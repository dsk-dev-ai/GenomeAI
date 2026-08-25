"""Workflow run worker (Phase 7.4).

Consumes queued workflow runs and hands each one to the EXISTING
DAGExecutionEngine. The worker contains no DAG planning logic and never
touches step states itself — it decides WHETHER a claimed run may
execute (still pending?), invokes the engine once, then releases the job.

Failure philosophy: jobs are never silently lost. Every claimed job ends
at exactly one of: completed (processed — executed or deliberately
skipped) or failed (recorded with a reason). A crash between claim and
release leaves the payload on the queue's processing list where later
recovery can find it (recovery policy intentionally deferred).

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
from typing import Protocol, runtime_checkable

from genomeai_api.workflows.errors import WorkflowStateTransitionError
from genomeai_api.workflows.execution.engine import DAGExecutionEngine, ExecutionRunStore
from genomeai_api.workflows.execution.executor import StepExecutor
from genomeai_api.workflows.models.workflow_run import WorkflowRun
from genomeai_api.workflows.queueing import JobQueue, WorkflowJob
from genomeai_api.workflows.types import RunState

# Persistence surface handed to the engine for exactly one job; produced
# per-job by the injected factory (the real composition root wraps one
# fresh SQLAlchemy session in an async context manager).
ExecutionStoreFactory = Callable[[], AbstractAsyncContextManager[ExecutionRunStore]]


@runtime_checkable
class SupportsExecuteRun(Protocol):
    """Structural engine surface the worker drives."""

    async def execute_run(self, run_id: uuid.UUID) -> WorkflowRun: ...


EngineFactory = Callable[[ExecutionRunStore], SupportsExecuteRun]

NO_JOB = "no_job"
EXECUTED = "executed"
SKIPPED_STATE = "skipped_state"
SKIPPED_RACE = "skipped_race"
MISSING_RUN = "missing_run"
EXECUTION_FAILED = "execution_failed"
WORKER_ERROR = "worker_error"


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
    ) -> None:
        self._queue = queue
        self._store_factory = store_factory
        self._worker_id = worker_id
        self._poll_interval = poll_interval
        self._logger = logger
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
            except Exception as exc:  # noqa: BLE001 - classify & record
                reason = str(exc) or type(exc).__name__
                try:
                    await store.transition_run(
                        job.workflow_run_id,
                        RunState.FAILED,
                        error_message=f"worker execution error: {reason}",
                    )
                except Exception:  # noqa: BLE001
                    self._log(
                        "error", "could not mark run %s failed", job.workflow_run_id
                    )
                await self._queue.fail(job, reason)
                return ProcessOutcome(
                    EXECUTION_FAILED, reason, job.job_id, job.workflow_run_id
                )

        await self._queue.complete(job)
        return ProcessOutcome(
            EXECUTED, str(finished.state), job.job_id, job.workflow_run_id
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
    "ProcessOutcome",
    "SKIPPED_RACE",
    "SKIPPED_STATE",
    "WORKER_ERROR",
    "WorkflowRunWorker",
]
