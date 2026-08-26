"""Workflow run worker (Phases 7.4 + 7.5).

Consumes queued workflow runs and hands each one to the EXISTING
DAGExecutionEngine. The worker contains no DAG planning logic and never
touches step states itself — it decides WHETHER a claimed run may
execute (still pending? retry due?), invokes the engine once, then
releases the job.

Failure philosophy (Phase 7.5): failures are CLASSIFIED (transient,
permanent, cancellation, invalid-workflow, infrastructure) and an
injected `RetryPolicy` — never the worker itself — decides whether to
retry. Retries re-enter through the SAME queue atomically
(`reschedule`), preserving per-run uniqueness. When the retry budget is
exhausted, or the failure class is non-retryable, the run stays FAILED
with its full failure metadata; that durable record is the final
failure ("dead letter") — nothing keeps requeueing.

Shutdown is cooperative: `run_forever` stops claiming as soon as the
injected `asyncio.Event` is set, finishes the current job first, closes
queue resources, and returns.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol, runtime_checkable

from genomeai_api.workflows.errors import WorkflowStateTransitionError
from genomeai_api.workflows.execution.engine import DAGExecutionEngine, ExecutionRunStore
from genomeai_api.workflows.execution.executor import StepExecutor
from genomeai_api.workflows.models.workflow_run import WorkflowRun
from genomeai_api.workflows.queueing import JobQueue, WorkflowJob
from genomeai_api.workflows.retry import (
    FailureClass,
    FailureObservation,
    RetryPolicy,
    classify_failure,
)
from genomeai_api.workflows.types import RunState

# Persistence surface handed to the engine for exactly one job; produced
# per-job by the injected factory (the real composition root wraps one
# fresh SQLAlchemy session in an async context manager).
ExecutionStoreFactory = Callable[[], AbstractAsyncContextManager["RetryAwareRunStore"]]


@runtime_checkable
class SupportsExecuteRun(Protocol):
    """Structural engine surface the worker drives."""

    async def execute_run(self, run_id: uuid.UUID) -> WorkflowRun: ...


class RetryAwareRunStore(ExecutionRunStore, Protocol):
    """Engine persistence surface PLUS Phase 7.5 retry bookkeeping.

    Satisfied structurally by `WorkflowRepository`; fakes implement the
    same three methods so tests stay honest about what the worker needs.
    """

    async def record_run_failure(
        self,
        run_id: uuid.UUID,
        *,
        classification: str,
        reason: str,
        failed_at: datetime,
    ) -> WorkflowRun | None: ...

    async def schedule_run_retry(
        self,
        run_id: uuid.UUID,
        *,
        next_retry_at: datetime,
    ) -> WorkflowRun | None: ...

    async def reopen_run_for_retry(self, run_id: uuid.UUID) -> WorkflowRun | None: ...


EngineFactory = Callable[[ExecutionRunStore], SupportsExecuteRun]

NO_JOB = "no_job"
EXECUTED = "executed"
SKIPPED_STATE = "skipped_state"
SKIPPED_RACE = "skipped_race"
MISSING_RUN = "missing_run"
EXECUTION_FAILED = "execution_failed"
WORKER_ERROR = "worker_error"
RETRY_SCHEDULED = "retry_scheduled"


@dataclass(frozen=True)
class ProcessOutcome:
    """Result of one claim/process cycle."""

    kind: str
    detail: str = ""
    job_id: uuid.UUID | None = None
    workflow_run_id: uuid.UUID | None = None

    @classmethod
    def no_job(cls) -> ProcessOutcome:
        return cls(kind=NO_JOB)


class WorkflowRunWorker:
    def __init__(
        self,
        queue: JobQueue,
        store_factory: ExecutionStoreFactory,
        executor: StepExecutor,
        *,
        worker_id: str = "worker-1",
        poll_interval: float = 0.5,
        logger: logging.Logger | None = None,
        engine_factory: EngineFactory | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self._queue = queue
        self._store_factory = store_factory
        self._worker_id = worker_id
        self._poll_interval = poll_interval
        self._logger = logger
        # Default policy = no automatic retries (Phase 7.4 behaviour).
        self._retry_policy = retry_policy or RetryPolicy(max_attempts=1)
        if engine_factory is not None:
            self._engine_factory = engine_factory
        else:
            self._engine_factory: EngineFactory = lambda store: DAGExecutionEngine(
                store, executor
            )

    async def process_next(self) -> ProcessOutcome:
        """Claims and processes at most one job."""
        job = await self._queue.claim(self._worker_id)
        if job is None:
            return ProcessOutcome.no_job()
        try:
            return await self._process_claimed(job)
        except WorkflowStateTransitionError as exc:
            # Defensive: any unclassified race retires the message without
            # duplicate execution; DB truth prevails.
            self._log("warning", "job %s raced run state: %s", job.job_id, exc)
            await self._release_completed(job)
            return ProcessOutcome(
                SKIPPED_RACE, str(exc), job.job_id, job.workflow_run_id
            )
        except Exception as exc:  # noqa: BLE001 - worker must survive anything
            self._log("exception", "unexpected error processing job %s", job.job_id)
            try:
                await self._queue.fail(job, f"unexpected worker error: {exc}")
            except Exception:  # noqa: BLE001
                self._log("error", "could not release job %s after error", job.job_id)
            return ProcessOutcome(
                WORKER_ERROR, str(exc), job.job_id, job.workflow_run_id
            )

    async def run_forever(self, stop: asyncio.Event | None = None) -> None:
        """Processes jobs until `stop` is set; graceful by construction."""
        stop = stop or asyncio.Event()
        self._log("info", "worker %s started", self._worker_id)
        try:
            while not stop.is_set():
                outcome = await self.process_next()
                if outcome.kind == NO_JOB:
                    try:
                        # Cancellation-safe idle sleep: stop.wait() wins the
                        # race against the timeout and wakes the loop at once.
                        await asyncio.wait_for(stop.wait(), timeout=self._poll_interval)
                    except TimeoutError:
                        pass
                elif outcome.kind in (EXECUTION_FAILED, WORKER_ERROR):
                    self._log(
                        "error",
                        "job %s ended in %s: %s",
                        outcome.job_id,
                        outcome.kind,
                        outcome.detail,
                    )
                elif outcome.kind in (SKIPPED_STATE, SKIPPED_RACE, MISSING_RUN):
                    self._log(
                        "warning",
                        "job %s skipped (%s): %s",
                        outcome.job_id,
                        outcome.kind,
                        outcome.detail,
                    )
        finally:
            await self._queue.close()
            self._log("info", "worker %s stopped", self._worker_id)

    async def _process_claimed(self, job: WorkflowJob) -> ProcessOutcome:
        async with self._store_factory() as store:
            run = await store.get_run(job.workflow_run_id)

            if run is None:
                await self._queue.fail(job, "workflow run does not exist")
                return ProcessOutcome(
                    MISSING_RUN, "run not found", job.job_id, job.workflow_run_id
                )

            current = RunState(run.state)
            if (
                current is RunState.FAILED
                and run.next_retry_at is not None
            ):
                # A retry delivery: the run failed earlier and a delayed
                # message brought it back.  Before doing anything else,
                # check the budget so an exhausted retry is retired
                # without reopening the run or touching the engine.
                attempts = run.attempt_count or 0
                if attempts >= self._retry_policy.max_attempts:
                    await self._queue.complete(job)
                    return ProcessOutcome(
                        SKIPPED_STATE,
                        f"retry exhausted ({attempts}/{self._retry_policy.max_attempts})",
                        job.job_id,
                        job.workflow_run_id,
                    )
                # Premature arrivals go straight back to the queue for
                # their remaining delay; only due retries are reopened.
                now = datetime.now(UTC)
                if run.next_retry_at > now:
                    remaining = run.next_retry_at - now
                    replacement = await self._queue.reschedule(
                        job, delay=remaining
                    )
                    return ProcessOutcome(
                        RETRY_SCHEDULED,
                        f"retry not due yet ({replacement.job_id})",
                        job.job_id,
                        job.workflow_run_id,
                    )
                reopened = await store.reopen_run_for_retry(job.workflow_run_id)
                if reopened is not None:
                    run = reopened
                    current = RunState.PENDING
                else:
                    # Lost the race against cancellation/manual action; the
                    # DB state wins and this message retires.
                    await self._queue.complete(job)
                    return ProcessOutcome(
                        SKIPPED_STATE,
                        "retry reopen refused (run no longer failed)",
                        job.job_id,
                        job.workflow_run_id,
                    )

            if current is not RunState.PENDING:
                # Cancelled / completed / running / failed runs must never be
                # re-executed because a queue message survived.
                await self._queue.complete(job)
                return ProcessOutcome(
                    SKIPPED_STATE,
                    f"run state is '{current.value}'",
                    job.job_id,
                    job.workflow_run_id,
                )

            engine = self._engine_factory(store)
            try:
                finished = await engine.execute_run(job.workflow_run_id)
            except WorkflowStateTransitionError as exc:
                # Another executor won the race; DB truth prevails and the
                # message is simply retired — no duplicate execution.
                await self._queue.complete(job)
                return ProcessOutcome(
                    SKIPPED_RACE, str(exc), job.job_id, job.workflow_run_id
                )
            except Exception as exc:  # noqa: BLE001 - classify & decide retry
                return await self._handle_execution_failure(job, store, run, exc)

        await self._queue.complete(job)
        return ProcessOutcome(
            EXECUTED, str(finished.state), job.job_id, job.workflow_run_id
        )

    async def _handle_execution_failure(
        self,
        job: WorkflowJob,
        store: RetryAwareRunStore,
        run: WorkflowRun,
        exc: Exception,
    ) -> ProcessOutcome:
        """Classifies one execution failure and applies the retry policy.

        Order of operations (crash-safety):
        1. Record the failure on the run (classification + history).
        2. Park the run in FAILED — except cancellations, which keep
           their own terminal state.
        3. Ask the POLICY — never the worker — whether to retry.
        4. If retrying: atomically reschedule through the SAME queue
           (`reschedule` releases + requeues in one step), then persist
           next_retry_at. If that metadata write fails the delayed job
           still exists, so only observability is lost.
        5. Otherwise: final failure. The FAILED run itself is the durable
           dead-letter record; the queue holds nothing further.
        """
        # Capture everything the exception carries: BaseError subclasses
        # keep their specifics on `.detail`, so a bare str() would lose it.
        reason = str(exc) or type(exc).__name__
        extra_detail = getattr(exc, "detail", None)
        if (
            isinstance(extra_detail, str)
            and extra_detail
            and extra_detail not in reason
        ):
            reason = f"{reason}: {extra_detail}"
        # Classification FIRST: a cancelled run must be recognized as such
        # before any state change erases that signal.
        classification = classify_failure(
            FailureObservation(exc, run_state=run.state)
        )
        try:
            recorded = await store.record_run_failure(
                job.workflow_run_id,
                classification=classification.value,
                reason=reason,
                failed_at=datetime.now(UTC),
            )
        except Exception:  # noqa: BLE001 - metadata loss must not stop flow
            self._log("error", "could not record failure for run %s", job.workflow_run_id)
            recorded = run

        # Every execution failure parks the run in FAILED (with retry
        # metadata attached) EXCEPT cancellations, which keep their own
        # terminal state — cancellation is never laundered into a failure.
        if classification is not FailureClass.CANCELLATION and run.state != (
            RunState.FAILED.value
        ):
            try:
                await store.transition_run(
                    job.workflow_run_id,
                    RunState.FAILED,
                    error_message=reason,
                )
            except Exception:  # noqa: BLE001 - state loss must not stop flow
                self._log(
                    "error", "could not fail run %s after execution error",
                    job.workflow_run_id,
                )

        # The attempt that just failed is included in attempt_count (the
        # engine increments it when starting an execution); floor at 1 so
        # policy math stays sane even if tracking metadata failed.
        attempts_made = max(recorded.attempt_count or 0, 1) if recorded else 1
        decision = self._retry_policy.decide(classification, attempts_made)
        if decision.retry:
            # Persist the retry intent BEFORE creating the queue job: if
            # the metadata write succeeds but reschedule crashes, the run
            # has next_retry_at set and a manual retry or re-evaluation
            # can recover.  If reschedule succeeds but this write fails,
            # the broadened pre-flight (state==FAILED) still reopens.
            next_retry_at = datetime.now(UTC) + decision.delay
            try:
                await store.schedule_run_retry(
                    job.workflow_run_id, next_retry_at=next_retry_at,
                )
            except Exception:  # noqa: BLE001
                self._log(
                    "error",
                    "could not persist next_retry_at for run %s",
                    job.workflow_run_id,
                )
            replacement = await self._queue.reschedule(job, delay=decision.delay)
            detail = (
                f"{classification.value}: {reason} → {decision.reason} "
                f"(job {replacement.job_id})"
            )
            self._log("warning", "job %s: %s", job.job_id, detail)
            return ProcessOutcome(
                RETRY_SCHEDULED, detail, job.job_id, job.workflow_run_id
            )

        final_reason = f"{classification.value}: {reason} ({decision.reason})"
        await self._queue.fail(job, final_reason)
        return ProcessOutcome(
            EXECUTION_FAILED, final_reason, job.job_id, job.workflow_run_id
        )

    async def _release_completed(self, job: WorkflowJob) -> None:
        try:
            await self._queue.complete(job)
        except Exception:  # noqa: BLE001
            self._log("error", "could not release job %s", job.job_id)

    def _log(self, level: str, message: str, *args: object) -> None:
        if self._logger is not None:
            getattr(self._logger, level)(message, *args)


__all__ = [
    "EXECUTED",
    "EXECUTION_FAILED",
    "MISSING_RUN",
    "NO_JOB",
    "RETRY_SCHEDULED",
    "ProcessOutcome",
    "SKIPPED_RACE",
    "SKIPPED_STATE",
    "WORKER_ERROR",
    "WorkflowRunWorker",
]
