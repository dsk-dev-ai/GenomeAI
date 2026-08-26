"""WorkflowRunWorker tests against in-memory fakes.

Pins the worker boundary: it only DECIDES whether a claimed run may
execute (or re-execute after a due retry) and delegates to the injected
engine — never planning or step states of its own. Phase 7.5 pins the
failure flow: classify → record → ask the injected RetryPolicy → either
atomically reschedule through the same queue or final-fail. Also pins
graceful shutdown behaviour.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import pytest
from genomeai_api.services.worker import (
    EXECUTED,
    EXECUTION_FAILED,
    MISSING_RUN,
    NO_JOB,
    RETRY_SCHEDULED,
    SKIPPED_RACE,
    SKIPPED_STATE,
    WORKER_ERROR,
    ProcessOutcome,
    WorkflowRunWorker,
)
from genomeai_api.workflows.errors import (
    TransientExecutionError,
    WorkflowStateTransitionError,
)
from genomeai_api.workflows.execution.executor import (
    StepExecutionContext,
    StepExecutionResult,
    StepExecutor,
)
from genomeai_api.workflows.models.workflow_run import WorkflowRun
from genomeai_api.workflows.queueing import InMemoryJobQueue
from genomeai_api.workflows.retry import ExponentialBackoff, FixedBackoff, RetryPolicy
from genomeai_api.workflows.types import RunState

pytestmark = pytest.mark.asyncio


@dataclass
class FakeStore:
    """RetryAwareRunStore subset with scripted run lookups."""

    runs: dict[uuid.UUID, WorkflowRun] = field(default_factory=dict)
    transitions: list[tuple[uuid.UUID, str]] = field(default_factory=list)

    async def get_run(self, run_id: uuid.UUID) -> WorkflowRun | None:
        return self.runs.get(run_id)

    async def get_by_id(self, workflow_id: uuid.UUID) -> object | None:
        del workflow_id
        return {"name": "pipeline"}

    async def transition_run(
        self,
        run_id: uuid.UUID,
        to_state: RunState,
        *,
        error_message: str | None = None,
    ) -> WorkflowRun:
        self.transitions.append((run_id, to_state.value))
        run = self.runs[run_id]
        run.state = to_state.value  # type: ignore[union-attr]
        if to_state is RunState.RUNNING:
            assert run is not None  # type narrowing for fakes
            run.attempt_count = (run.attempt_count or 0) + 1  # type: ignore[union-attr]
        elif error_message is not None and run is not None:
            run.error_message = error_message
        return run  # type: ignore[return-value]

    async def record_run_failure(
        self,
        run_id: uuid.UUID,
        *,
        classification: str,
        reason: str,
        failed_at: datetime,
    ) -> WorkflowRun | None:
        run = self.runs.get(run_id)
        if run is None:
            return None
        history = list(run.failure_history) if run.failure_history else []
        history.append(
            {
                "attempt": max(run.attempt_count or 0, 1),
                "class": classification,
                "reason": reason,
                "failed_at": failed_at.isoformat(),
            }
        )
        run.failure_history = history
        run.failure_class = classification
        run.error_message = reason
        return run

    async def schedule_run_retry(
        self, run_id: uuid.UUID, *, next_retry_at: datetime
    ) -> WorkflowRun | None:
        run = self.runs.get(run_id)
        if run is None:
            return None
        run.next_retry_at = next_retry_at
        return run

    async def reopen_run_for_retry(self, run_id: uuid.UUID) -> WorkflowRun | None:
        run = self.runs.get(run_id)
        if run is None or run.state != RunState.FAILED.value:
            return None
        run.state = RunState.PENDING.value
        run.next_retry_at = None
        return run

    async def transition_step_run(self, *args: object, **kwargs: object) -> None:
        raise AssertionError("worker must not touch step runs directly")


def _run(state: str = "pending") -> WorkflowRun:
    run = WorkflowRun(workflow_id=uuid.uuid4())
    run.id = uuid.uuid4()
    run.state = state
    return run


@dataclass
class ScriptedEngine:
    """Stands in for DAGExecutionEngine; records execute_run calls.

    Mirrors the real engine contract: starting an execution moves the run
    to RUNNING (which bumps attempt_count via the store), then the
    scripted outcome plays out.
    """

    store: FakeStore
    outcome: str = "succeed"
    calls: list[uuid.UUID] = field(default_factory=list)

    async def execute_run(self, run_id: uuid.UUID) -> WorkflowRun:
        self.calls.append(run_id)
        run = self.store.runs.get(run_id)
        if run is None:
            raise AssertionError("engine invoked without a run")
        await self.store.transition_run(run_id, RunState.RUNNING)
        if self.outcome == "succeed":
            run.state = RunState.SUCCEEDED.value
            return run
        if self.outcome == "transient":
            raise TransientExecutionError("flaky dependency")
        if self.outcome == "permanent":
            from genomeai_api.workflows.errors import PermanentExecutionError

            raise PermanentExecutionError("bad input shape")
        if self.outcome == "cancel":
            run.state = RunState.CANCELLED.value
            raise TransientExecutionError("cancelled mid-flight")
        if self.outcome == "race":
            raise WorkflowStateTransitionError("running", "running")
        if self.outcome == "explode":
            raise RuntimeError("engine blew up")
        raise AssertionError(f"unknown outcome {self.outcome}")


def _worker(
    queue: InMemoryJobQueue,
    store: FakeStore,
    engine_outcome: str = "succeed",
    retry_policy: RetryPolicy | None = None,
) -> tuple[WorkflowRunWorker, ScriptedEngine]:
    engine = ScriptedEngine(store, outcome=engine_outcome)

    @contextlib.asynccontextmanager
    async def store_factory():
        yield store

    def engine_factory(_store: FakeStore) -> ScriptedEngine:
        return engine

    worker = WorkflowRunWorker(
        queue,
        store_factory,  # type: ignore[arg-type]
        _NoopExecutor(),
        logger=logging.getLogger("test"),
        engine_factory=engine_factory,  # type: ignore[arg-type]
        retry_policy=retry_policy,
    )
    return worker, engine


class _NoopExecutor(StepExecutor):
    def execute(
        self, step: object, context: StepExecutionContext
    ) -> StepExecutionResult:
        raise AssertionError("executor must be driven by the engine, not the worker")


# --- happy path -------------------------------------------------------------


async def test_successful_claim_executes_engine_once_and_completes_job() -> None:
    queue = InMemoryJobQueue()
    store = FakeStore()
    run = _run()
    store.runs[run.id] = run
    await queue.enqueue(run.id)
    worker, engine = _worker(queue, store)

    outcome = await worker.process_next()

    assert outcome.kind == EXECUTED
    assert outcome.detail == "succeeded"
    assert engine.calls == [run.id]
    assert run.state == "succeeded"
    assert await queue.depth() == 0


async def test_empty_queue_yields_no_job() -> None:
    worker, _engine = _worker(InMemoryJobQueue(), FakeStore())

    assert (await worker.process_next()).kind == NO_JOB


# --- guarded skips -----------------------------------------------------------


async def test_missing_run_is_failed_not_lost() -> None:
    queue = InMemoryJobQueue()
    await queue.enqueue(uuid.uuid4())  # no such run anywhere
    worker, _engine = _worker(queue, FakeStore())

    outcome = await worker.process_next()

    assert outcome.kind == MISSING_RUN
    assert await queue.depth() == 0


@pytest.mark.parametrize("state", ["cancelled", "succeeded", "failed", "running"])
async def test_non_pending_runs_are_skipped_without_execution(state: str) -> None:
    queue = InMemoryJobQueue()
    store = FakeStore()
    run = _run(state)
    store.runs[run.id] = run
    await queue.enqueue(run.id)
    worker, engine = _worker(queue, store)

    outcome = await worker.process_next()

    assert outcome.kind == SKIPPED_STATE
    assert state in outcome.detail
    assert engine.calls == []  # cancelled/completed runs NEVER re-execute


async def test_concurrent_race_is_retired_without_duplicate_execution() -> None:
    queue = InMemoryJobQueue()
    store = FakeStore()
    run = _run()
    store.runs[run.id] = run
    await queue.enqueue(run.id)
    worker, engine = _worker(queue, store, engine_outcome="race")

    outcome = await worker.process_next()

    assert outcome.kind == SKIPPED_RACE
    assert len(engine.calls) == 1  # attempted exactly once, then retired


# --- failure handling ---------------------------------------------------------


async def test_unexpected_engine_exception_fails_run_and_job() -> None:
    queue = InMemoryJobQueue()
    store = FakeStore()
    run = _run()
    store.runs[run.id] = run
    await queue.enqueue(run.id)
    worker, _engine = _worker(queue, store, engine_outcome="explode")

    outcome = await worker.process_next()

    assert outcome.kind == EXECUTION_FAILED
    assert "engine blew up" in outcome.detail
    # The engine started the attempt (RUNNING) and the worker parked the
    # run in FAILED so it is not stranded in a running state.
    assert store.transitions == [(run.id, "running"), (run.id, "failed")]
    # Failure metadata is preserved even without retries.
    assert run.failure_class == "permanent"  # RuntimeError → conservative default
    assert run.failure_history is not None and len(run.failure_history) == 1
    assert await queue.depth() == 0


# --- automatic retry flow (Phase 7.5) -----------------------------------------


def _transient_policy(max_attempts: int) -> RetryPolicy:
    return RetryPolicy(
        max_attempts=max_attempts,
        backoff=FixedBackoff(timedelta(seconds=60)),
    )


async def test_transient_failure_with_budget_reschedules_through_queue() -> None:
    queue = InMemoryJobQueue()
    store = FakeStore()
    run = _run()
    store.runs[run.id] = run
    await queue.enqueue(run.id)
    worker, _engine = _worker(
        queue, store, engine_outcome="transient", retry_policy=_transient_policy(3)
    )

    outcome = await worker.process_next()

    assert outcome.kind == RETRY_SCHEDULED
    assert "flaky dependency" in outcome.detail
    # Run is FAILED (resting state between attempts) with retry metadata.
    assert run.state == RunState.FAILED.value
    assert run.attempt_count == 1
    assert run.next_retry_at is not None
    assert run.failure_class == "transient"
    assert len(run.failure_history or []) == 1
    # The retry re-entered the SAME queue as a delayed replacement.
    assert await queue.depth() == 0
    assert await queue.delayed() == 1


async def test_successful_retry_completes_the_run() -> None:
    queue = InMemoryJobQueue(now=lambda: datetime.now(UTC))
    store = FakeStore()
    run = _run(state="failed")  # resting after attempt 1
    run.attempt_count = 1
    run.next_retry_at = datetime.now(UTC) - timedelta(seconds=1)  # due now
    store.runs[run.id] = run
    await queue.enqueue(run.id)
    worker, engine = _worker(
        queue,
        store,
        engine_outcome="succeed",  # second time it works
        retry_policy=_transient_policy(3),
    )

    outcome = await worker.process_next()

    assert outcome.kind == EXECUTED
    assert engine.calls == [run.id]
    assert run.state == RunState.SUCCEEDED.value
    assert run.attempt_count == 2  # tracked across the retry boundary
    assert run.next_retry_at is None  # cleared once executing again
    assert await queue.delayed() == 0
    assert await queue.depth() == 0


async def test_early_retry_delivery_is_rescheduled_not_executed() -> None:
    queue = InMemoryJobQueue(now=lambda: datetime.now(UTC))
    store = FakeStore()
    run = _run(state="failed")
    run.attempt_count = 1
    run.next_retry_at = datetime.now(UTC) + timedelta(minutes=5)  # NOT due yet
    store.runs[run.id] = run
    await queue.enqueue(run.id)
    worker, engine = _worker(queue, store, retry_policy=_transient_policy(3))

    outcome = await worker.process_next()

    assert outcome.kind == RETRY_SCHEDULED
    assert "not due yet" in outcome.detail
    assert engine.calls == []  # never executed early
    assert await queue.delayed() == 1  # put back for its real time slot


async def test_retry_exhaustion_causes_final_failure_without_requeue() -> None:
    queue = InMemoryJobQueue(now=lambda: datetime.now(UTC))
    store = FakeStore()
    run = _run(state="failed")
    run.attempt_count = 2  # already burned both allowed attempts
    run.next_retry_at = datetime.now(UTC) - timedelta(seconds=1)  # attempt due
    run.failure_history = [
        {"attempt": 1, "class": "transient", "reason": "first", "failed_at": "t1"},
        {"attempt": 2, "class": "transient", "reason": "second", "failed_at": "t2"},
    ]
    store.runs[run.id] = run
    await queue.enqueue(run.id)
    worker, engine = _worker(
        queue, store, engine_outcome="transient", retry_policy=_transient_policy(2)
    )

    outcome = await worker.process_next()

    # Pre-flight catches the exhausted retry BEFORE reaching the engine.
    assert outcome.kind == SKIPPED_STATE
    assert "exhausted" in outcome.detail
    assert engine.calls == []  # engine never called — budget already spent
    # History unchanged — no new attempt was made.
    assert run.failure_history is not None and len(run.failure_history) == 2
    assert run.state == RunState.FAILED.value
    assert await queue.delayed() == 0
    assert await queue.depth() == 0


async def test_permanent_failure_never_retries_even_with_budget() -> None:
    queue = InMemoryJobQueue()
    store = FakeStore()
    run = _run()
    store.runs[run.id] = run
    await queue.enqueue(run.id)
    worker, _engine = _worker(
        queue,
        store,
        engine_outcome="permanent",
        retry_policy=_transient_policy(5),  # generous budget...
    )

    outcome = await worker.process_next()

    assert outcome.kind == EXECUTION_FAILED
    assert "permanent" in outcome.detail
    assert run.failure_class == "permanent"
    assert await queue.delayed() == 0  # ...but permanent failures don't retry


async def test_cancelled_run_is_never_auto_retried() -> None:
    queue = InMemoryJobQueue()
    store = FakeStore()
    run = _run()
    store.runs[run.id] = run
    await queue.enqueue(run.id)
    worker, _engine = _worker(
        queue,
        store,
        engine_outcome="cancel",  # cancelled mid-flight, transient exception raised
        retry_policy=_transient_policy(3),
    )

    outcome = await worker.process_next()

    assert outcome.kind == EXECUTION_FAILED
    assert run.state == RunState.CANCELLED.value  # NOT laundered into failed
    assert run.failure_class == "cancellation"
    assert await queue.delayed() == 0  # cancellation NEVER auto-retries


async def test_exponential_backoff_delay_is_applied_to_replacement_job() -> None:
    queue = InMemoryJobQueue(now=lambda: datetime.now(UTC))
    store = FakeStore()
    run = _run()
    store.runs[run.id] = run
    await queue.enqueue(run.id)
    policy = RetryPolicy(
        max_attempts=2,
        backoff=ExponentialBackoff(timedelta(seconds=30)),
    )
    worker, _engine = _worker(
        queue, store, engine_outcome="transient", retry_policy=policy
    )

    outcome = await worker.process_next()

    assert outcome.kind == RETRY_SCHEDULED
    assert run.next_retry_at is not None
    remaining = (run.next_retry_at - datetime.now(UTC)).total_seconds()
    assert 29 <= remaining <= 31  # first retry delay ≈ initial backoff


async def test_worker_survives_arbitrary_processing_crash_and_releases_job() -> None:
    queue = InMemoryJobQueue()

    @contextlib.asynccontextmanager
    async def bad_factory():
        raise RuntimeError("session factory exploded")
        yield None  # pragma: no cover

    await queue.enqueue(uuid.uuid4())
    worker = WorkflowRunWorker(
        queue,
        bad_factory,  # type: ignore[arg-type]
        _NoopExecutor(),
        logger=logging.getLogger("test"),
    )

    outcome = await worker.process_next()

    assert outcome.kind == WORKER_ERROR
    assert await queue.depth() == 0  # job released, not lost


# --- graceful shutdown ----------------------------------------------------------


async def test_shutdown_before_start_processes_nothing_and_closes_queue() -> None:
    queue = InMemoryJobQueue()
    worker, _engine = _worker(queue, FakeStore())
    stop = asyncio.Event()
    stop.set()

    await worker.run_forever(stop)

    assert queue._closed is True


async def test_shutdown_wakes_idle_loop_promptly() -> None:
    queue = InMemoryJobQueue()
    worker, _engine = _worker(queue, FakeStore())
    stop = asyncio.Event()

    async def request_stop() -> None:
        await asyncio.sleep(0.05)
        stop.set()

    await asyncio.wait_for(
        asyncio.gather(worker.run_forever(stop), request_stop()), timeout=2.0
    )


async def test_current_job_finishes_before_shutdown_returns() -> None:
    queue = InMemoryJobQueue()
    store = FakeStore()
    run = _run()
    store.runs[run.id] = run
    await queue.enqueue(run.id)
    worker, engine = _worker(queue, store)

    # Claim first, then request shutdown: the in-flight job must still be
    # processed to a terminal outcome before run_forever can return.
    claimed = await queue.claim("worker-1")
    assert claimed is not None
    stop = asyncio.Event()
    stop.set()

    result = await worker._process_claimed(claimed)  # noqa: SLF001 - pinning guarantee

    assert result.kind == EXECUTED
    assert engine.calls == [run.id]
    assert await queue.depth() == 0


async def test_process_outcome_no_job_factory() -> None:
    assert ProcessOutcome.no_job().kind == NO_JOB
