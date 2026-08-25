"""Redis-backed `JobQueue` (Phase 7.4).

The ONLY application module allowed to know Redis is the queue backend;
everything else depends on the `JobQueue` protocol from
`workflows.queueing`, keeping the implementation replaceable.

Layout (all keys under a configurable prefix):

- ``{prefix}:queued``     LIST of queued job payloads
- ``{prefix}:processing`` LIST of claimed payloads awaiting release
- ``{prefix}:active``     HASH workflow_run_id -> queued payload (guards
                          duplicate enqueues and powers idempotent returns)

Idempotency contract (same semantics as `InMemoryJobQueue`):

- enqueue: ``HSETNX`` on the active hash is the guard — exactly one
  enqueuer wins per run; losers receive the existing job, so duplicate
  messages cannot exist at the source. Re-enqueue is possible again
  once a job is released.
- claim:   atomic ``LMOVE queued -> processing``, so two workers can
  never receive the same payload. The claimed (running-state) payload is
  recorded in the claims hash so release removes exactly those bytes.
- complete/fail: one transactional pipeline removes the payload from the
  processing list and clears both hashes.

Connection failures surface as `QueueUnavailableError`; malformed stored
payloads as `JobDecodeError`. Jobs are never silently dropped: a crash
between claim and release leaves the payload on the processing list,
where a later recovery phase can find it (intentionally deferred).
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any, TypeVar

from genomeai_api.workflows.errors import JobDecodeError, QueueUnavailableError
from genomeai_api.workflows.queueing import (
    WorkflowJob,
    job_from_json,
    job_to_json,
)
from genomeai_api.workflows.types import JobState

DEFAULT_PREFIX = "genomeai:workflow-runs"

T = TypeVar("T")


class RedisJobQueue:
    """JobQueue over redis.asyncio."""

    def __init__(self, client: Any, *, prefix: str = DEFAULT_PREFIX) -> None:
        self._client = client
        self._prefix = prefix

    @property
    def _queued_key(self) -> str:
        return f"{self._prefix}:queued"

    @property
    def _processing_key(self) -> str:
        return f"{self._prefix}:processing"

    @property
    def _active_key(self) -> str:
        return f"{self._prefix}:active"

    @property
    def _claims_key(self) -> str:
        return f"{self._prefix}:claims"

    async def enqueue(self, workflow_run_id: uuid.UUID) -> WorkflowJob:
        """Queues a run; idempotent while a job for it is still active."""
        candidate = WorkflowJob(
            job_id=uuid.uuid4(),
            workflow_run_id=workflow_run_id,
            queued_at=datetime.now(UTC),
        )
        raw = job_to_json(candidate)

        created = await self._guard(
            lambda: self._client.hsetnx(
                self._active_key, str(workflow_run_id), raw
            ),
            "enqueue guard",
        )
        if not created:
            stored = await self._guard(
                lambda: self._client.hget(self._active_key, str(workflow_run_id)),
                "enqueue lookup",
            )
            if stored:
                return self._decode(stored)
            # Guard entry vanished between HSETNX and HGET (released by a
            # worker in that window); retrying re-runs the whole guard.
            return await self.enqueue(workflow_run_id)

        await self._guard(
            lambda: self._client.rpush(self._queued_key, raw), "enqueue push"
        )
        return candidate

    async def claim(self, worker_id: str) -> WorkflowJob | None:
        del worker_id  # claims are exclusive regardless of caller identity
        raw = await self._guard(
            lambda: self._client.lmove(
                self._queued_key, self._processing_key, "RIGHT", "LEFT"
            ),
            "claim",
        )
        if raw is None:
            return None
        queued_job = self._decode(raw)
        claimed = WorkflowJob(
            job_id=queued_job.job_id,
            workflow_run_id=queued_job.workflow_run_id,
            queued_at=queued_job.queued_at,
            attempt=queued_job.attempt,
            state=JobState.RUNNING,
            claimed_at=datetime.now(UTC),
        )
        # The claims hash must remember the EXACT bytes sitting on the
        # processing list (the queued-form payload), otherwise the release
        # LREM can never match and payloads would leak on that list.
        claimed_raw = self._as_text(raw)
        await self._guard(
            lambda: self._client.hset(self._claims_key, str(claimed.job_id), claimed_raw),
            "claim record",
        )
        return claimed

    async def complete(self, job: WorkflowJob) -> None:
        finished = WorkflowJob(
            job_id=job.job_id,
            workflow_run_id=job.workflow_run_id,
            queued_at=job.queued_at,
            attempt=job.attempt,
            state=JobState.COMPLETED,
            claimed_at=job.claimed_at,
            completed_at=datetime.now(UTC),
        )
        await self._release(finished)

    async def fail(self, job: WorkflowJob, reason: str) -> None:
        del reason  # failure detail lives in run state/logs, not the queue
        failed = WorkflowJob(
            job_id=job.job_id,
            workflow_run_id=job.workflow_run_id,
            queued_at=job.queued_at,
            attempt=job.attempt,
            state=JobState.FAILED,
            claimed_at=job.claimed_at,
            completed_at=datetime.now(UTC),
        )
        await self._release(failed)

    async def depth(self) -> int:
        return int(
            await self._guard(lambda: self._client.llen(self._queued_key), "depth")
        )

    async def close(self) -> None:
        # Client ownership stays with the composition root (shared pool);
        # closing here would break other users of the connection.
        return None

    async def _release(self, finished: WorkflowJob) -> None:
        recorded = await self._guard(
            lambda: self._client.hget(self._claims_key, str(finished.job_id)),
            "release lookup",
        )
        claimed_raw = (
            self._as_text(recorded)
            if recorded is not None
            else job_to_json(finished)
        )

        async def _atomic() -> None:
            pipeline = self._client.pipeline(transaction=True)
            pipeline.lrem(self._processing_key, 0, claimed_raw)
            pipeline.hdel(self._claims_key, str(finished.job_id))
            pipeline.hdel(self._active_key, str(finished.workflow_run_id))
            await pipeline.execute()

        await self._guard(_atomic, "release")

    @staticmethod
    def _as_text(raw: Any) -> str:
        return raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)

    @classmethod
    def _decode(cls, raw: Any) -> WorkflowJob:
        try:
            return job_from_json(cls._as_text(raw))
        except JobDecodeError:
            raise
        except Exception as exc:  # defensive: unexpected payload shapes
            raise JobDecodeError(f"unreadable job payload: {exc}") from exc

    @staticmethod
    async def _guard(
        operation: Callable[[], Awaitable[T]], action: str
    ) -> T:
        try:
            return await operation()
        except JobDecodeError:
            raise
        except Exception as exc:
            raise QueueUnavailableError(f"queue {action} failed: {exc}") from exc


__all__ = ["DEFAULT_PREFIX", "RedisJobQueue"]
