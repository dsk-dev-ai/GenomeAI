"""WorkflowRunWorker tests against in-memory fakes.

Pins the worker boundary: it only DECIDES whether a claimed run may
execute and delegates to the injected engine — never planning or step
states of its own. Also pins graceful shutdown behaviour.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import uuid
from dataclasses import dataclass, field

import pytest
from genomeai_api.services.worker import (
    EXECUTED,
    EXECUTION_FAILED,
    MISSING_RUN,
    NO_JOB,
    SKIPPED_RACE,
    SKIPPED_STATE,
    WORKER_ERROR,
    ProcessOutcome,
    WorkflowRunWorker,
)
from genomeai_api.workflows.errors import WorkflowStateTransitionError
from genomeai_api.workflows.execution.executor import (
    StepExecutionContext,
    StepExecutionResult,
    StepExecutor,
)
from genomeai_api.workflows.models.workflow_run import WorkflowRun
from genomeai_api.workflows.queueing import InMemoryJobQueue
from genomeai_api.workflows.types import RunState

pytestmark = pytest.mark.asyncio


@dataclass
class FakeStore:
    """ExecutionRunStore subset with scripted run lookups."""

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
        return run  # type: ignore[return-value]

    async def transition_step_run(self, *args: object, **kwargs: object) -> None:
        raise AssertionError("worker must not touch step runs directly")


def _run(state: str = "pending") -> WorkflowRun:
    run = WorkflowRun(workflow_id=uuid.uuid4())
    run.id = uuid.uuid4()
    run.state = state
    return run


@dataclass
class ScriptedEngine:
    """Stands in for DAGExecutionEngine; records execute_run calls."""

    store: FakeStore
    outcome: str = "succeed"
    calls: list[uuid.UUID] = field(default_factory=list)

    async def execute_run(self, run_id: uuid.UUID) -> WorkflowRun:
        self.calls.append(run_id)
        if self.outcome == "succeed":
            self.store.runs[run_id].state = RunState.SUCCEEDED.value  # type: ignore[union-attr]
            return self.store.runs[run_id]  # type: ignore[return-value]
        if self.outcome == "race":
            raise WorkflowStateTransitionError("running", "running")
        if self.outcome == "explode":
            raise RuntimeError("engine blew up")
        raise AssertionError(f"unknown outcome {self.outcome}")


def _worker(
    queue: InMemoryJobQueue,
    store: FakeStore,
    engine_outcome: str = "succeed",
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
    # The worker recorded the failure on the RUN so it is not stranded.
    assert store.transitions == [(run.id, "failed")]
    assert await queue.depth() == 0


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
