"""Lightweight ingestion-job foundation.

Tracks one ingestion attempt against a source with a small explicit state
machine (pending → running → succeeded/failed/cancelled). This is *not* a
workflow engine: no queues, workers, or scheduling live here — Phase 7 builds
those on top of this boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from genomeai_api.integration.errors import InvalidJobTransitionError
from genomeai_api.integration.types import JobState, can_transition


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass
class IngestionJob:
    """One ingestion run against one source."""

    source_id: str
    job_id: str = field(default_factory=lambda: str(uuid4()))
    state: JobState = JobState.PENDING
    started_at: datetime | None = None
    finished_at: datetime | None = None
    records_received: int = 0
    records_succeeded: int = 0
    records_failed: int = 0
    error_message: str | None = None
    error_detail: dict[str, object] | None = None

    def _move_to(self, next_state: JobState) -> None:
        if not can_transition(self.state, next_state):
            raise InvalidJobTransitionError(
                self.state.value,
                next_state.value,
            )
        self.state = next_state

    def start(self) -> None:
        self._move_to(JobState.RUNNING)
        if self.started_at is None:
            self.started_at = _utcnow()

    def succeed(self, *, received: int, succeeded: int) -> None:
        self._move_to(JobState.SUCCEEDED)
        self.records_received = received
        self.records_succeeded = succeeded
        self.records_failed = max(0, received - succeeded)
        self.finished_at = _utcnow()

    def fail(
        self,
        *,
        received: int,
        failed: int,
        error_message: str,
        error_detail: dict[str, object] | None = None,
    ) -> None:
        if not error_message.strip():
            raise ValueError("error_message must not be empty when failing a job")
        self._move_to(JobState.FAILED)
        self.records_received = received
        self.records_failed = failed
        self.records_succeeded = max(0, received - failed)
        self.error_message = error_message
        self.error_detail = error_detail
        self.finished_at = _utcnow()

    def cancel(self) -> None:
        self._move_to(JobState.CANCELLED)
        self.finished_at = _utcnow()
