"""Workflow queue abstraction (Phase 7.4).

Defines WHAT a queued workflow-run job is and the boundary every queue
backend must satisfy. Nothing here knows about Redis, databases, or the
DAG engine — backends implement `JobQueue`; the worker and services
depend only on that protocol, keeping the implementation replaceable.

Idempotency contract (every backend MUST honour it):

- `enqueue` is idempotent per workflow-run: re-enqueueing a run that is
  still queued/claimed returns the SAME job instead of a second entry,
  so duplicate queue messages cannot exist at the source.
- `claim` hands each queued job to exactly one worker atomically.
- `complete`/`fail` release the claim; afterwards the run may be
  enqueued again.

Job state describes queue processing only — the WorkflowRun row stays
the source of truth for execution state.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol, runtime_checkable

from genomeai_api.workflows.errors import JobDecodeError
from genomeai_api.workflows.types import JobState

JOB_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class WorkflowJob:
    """One workflow-run waiting for (or processed by) a worker.

    Carries just enough identity to load the WorkflowRun — no workflow
    domain data is duplicated into the queue.
    """

    job_id: uuid.UUID
    workflow_run_id: uuid.UUID
    queued_at: datetime
    attempt: int = 1
    state: JobState = JobState.QUEUED
    claimed_at: datetime | None = None
    completed_at: datetime | None = None


def _require_utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise JobDecodeError(f"'{field}' must be timezone-aware")


def job_to_json(job: WorkflowJob) -> str:
    """Deterministic JSON encoding (sorted keys, UTC ISO-8601 instants)."""
    _require_utc(job.queued_at, "queued_at")
    if job.claimed_at is not None:
        _require_utc(job.claimed_at, "claimed_at")
    if job.completed_at is not None:
        _require_utc(job.completed_at, "completed_at")
    payload = {
        "schema": JOB_SCHEMA_VERSION,
        "job_id": str(job.job_id),
        "workflow_run_id": str(job.workflow_run_id),
        "queued_at": job.queued_at.isoformat(),
        "attempt": job.attempt,
        "state": job.state.value,
        "claimed_at": job.claimed_at.isoformat() if job.claimed_at else None,
        "completed_at": (
            job.completed_at.isoformat() if job.completed_at else None
        ),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def job_from_json(raw: str | bytes) -> WorkflowJob:
    """Decodes a payload produced by `job_to_json`, rejecting anything else."""
    try:
        payload: dict[str, object] = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise JobDecodeError(f"payload is not valid JSON: {exc}") from exc
    required = (
        "job_id",
        "workflow_run_id",
        "queued_at",
        "attempt",
        "state",
    )
    missing = [key for key in required if key not in payload]
    if missing:
        raise JobDecodeError(f"payload missing field(s): {', '.join(missing)}")
    job_id_raw = str(payload["job_id"])
    run_id_raw = str(payload["workflow_run_id"])
    queued_at_raw = str(payload["queued_at"])
    state_raw = str(payload["state"])
    try:
        attempt = int(str(payload["attempt"]))
        job_id = uuid.UUID(job_id_raw)
        run_id = uuid.UUID(run_id_raw)
        queued_at = datetime.fromisoformat(queued_at_raw)
    except ValueError as exc:
        raise JobDecodeError(f"payload field is invalid: {exc}") from exc
    _require_utc(queued_at, "queued_at")
    try:
        state = JobState(state_raw)
    except ValueError as exc:
        raise JobDecodeError(f"unknown job state: {state_raw}") from exc
    claimed_raw = payload.get("claimed_at")
    completed_raw = payload.get("completed_at")
    claimed_at: datetime | None
    completed_at: datetime | None
    try:
        claimed_at = (
            datetime.fromisoformat(str(claimed_raw)) if claimed_raw else None
        )
        completed_at = (
            datetime.fromisoformat(str(completed_raw)) if completed_raw else None
        )
    except ValueError as exc:
        raise JobDecodeError(f"payload timestamp is invalid: {exc}") from exc
    return WorkflowJob(
        job_id=job_id,
        workflow_run_id=run_id,
        queued_at=queued_at,
        attempt=attempt,
        state=state,
        claimed_at=claimed_at,
        completed_at=completed_at,
    )


@runtime_checkable
class JobQueue(Protocol):
    """Boundary between the application and any queue backend."""

    async def enqueue(self, workflow_run_id: uuid.UUID) -> WorkflowJob:
        """Queues one workflow run; idempotent while it is already queued."""
        ...

    async def claim(self, worker_id: str) -> WorkflowJob | None:
        """Atomically claims the next queued job for one worker."""
        ...

    async def complete(self, job: WorkflowJob) -> None:
        """Marks the job processed and releases its claim."""
        ...

    async def fail(self, job: WorkflowJob, reason: str) -> None:
        """Records why the job could not be processed and releases it."""
        ...

    async def depth(self) -> int:
        """Number of jobs currently waiting to be claimed."""
        ...

    async def close(self) -> None:
        """Releases backend resources (idempotent)."""
        ...


class InMemoryJobQueue:
    """Reference `JobQueue` used by tests and standalone tooling.

    Implements exactly the same idempotency contract as the Redis
    backend; not intended for multi-process deployments.
    """

    def __init__(self, *, now: Callable[[], datetime] | None = None) -> None:
        self._queued: list[WorkflowJob] = []
        self._by_run: dict[uuid.UUID, WorkflowJob] = {}
        self._claims: dict[uuid.UUID, WorkflowJob] = {}
        self._now: Callable[[], datetime] = now or (lambda: datetime.now(UTC))
        self._closed = False

    async def enqueue(self, workflow_run_id: uuid.UUID) -> WorkflowJob:
        existing = self._by_run.get(workflow_run_id)
        if existing is not None:
            return existing
        job = WorkflowJob(
            job_id=uuid.uuid4(),
            workflow_run_id=workflow_run_id,
            queued_at=self._now(),
        )
        self._queued.append(job)
        self._by_run[workflow_run_id] = job
        return job

    async def claim(self, worker_id: str) -> WorkflowJob | None:
        del worker_id  # claims are exclusive regardless of caller identity
        if not self._queued:
            return None
        job = self._queued.pop(0)
        claimed = WorkflowJob(
            job_id=job.job_id,
            workflow_run_id=job.workflow_run_id,
            queued_at=job.queued_at,
            attempt=job.attempt,
            state=JobState.RUNNING,
            claimed_at=self._now(),
        )
        # Keep the mapping so re-enqueue stays idempotent until released.
        self._by_run[job.workflow_run_id] = claimed
        self._claims[job.job_id] = claimed
        return claimed

    async def complete(self, job: WorkflowJob) -> None:
        finished = WorkflowJob(
            job_id=job.job_id,
            workflow_run_id=job.workflow_run_id,
            queued_at=job.queued_at,
            attempt=job.attempt,
            state=JobState.COMPLETED,
            claimed_at=job.claimed_at,
            completed_at=self._now(),
        )
        self._release(finished)

    async def fail(self, job: WorkflowJob, reason: str) -> None:
        del reason  # recorded by callers via logs/run state, not the job
        failed = WorkflowJob(
            job_id=job.job_id,
            workflow_run_id=job.workflow_run_id,
            queued_at=job.queued_at,
            attempt=job.attempt,
            state=JobState.FAILED,
            claimed_at=job.claimed_at,
            completed_at=self._now(),
        )
        self._release(failed)

    async def depth(self) -> int:
        return len(self._queued)

    async def close(self) -> None:
        self._closed = True

    def _release(self, finished: WorkflowJob) -> None:
        self._claims.pop(finished.job_id, None)
        current = self._by_run.get(finished.workflow_run_id)
        if current is not None and current.job_id == finished.job_id:
            del self._by_run[finished.workflow_run_id]


__all__ = [
    "InMemoryJobQueue",
    "JobQueue",
    "JOB_SCHEMA_VERSION",
    "WorkflowJob",
    "job_from_json",
    "job_to_json",
]
