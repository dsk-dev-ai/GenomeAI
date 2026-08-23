from __future__ import annotations

import pytest
from genomeai_api.integration.errors import InvalidJobTransitionError
from genomeai_api.integration.jobs import IngestionJob
from genomeai_api.integration.types import JobState


def test_new_job_starts_pending_with_id() -> None:
    job = IngestionJob(source_id="genomeai-reference")
    assert job.state is JobState.PENDING
    assert job.started_at is None
    assert job.records_received == 0


def test_successful_lifecycle() -> None:
    job = IngestionJob(source_id="s")
    job.start()
    assert job.state is JobState.RUNNING
    assert job.started_at is not None

    job.succeed(received=10, succeeded=8)
    assert job.state is JobState.SUCCEEDED
    assert job.records_failed == 2
    assert job.finished_at is not None


def test_failed_lifecycle_requires_message() -> None:
    job = IngestionJob(source_id="s")
    job.start()
    with pytest.raises(ValueError, match="error_message"):
        job.fail(received=3, failed=3, error_message="   ")

    job.fail(
        received=3,
        failed=3,
        error_message="source unreachable",
        error_detail={"status": 503},
    )
    assert job.state is JobState.FAILED
    assert job.error_detail == {"status": 503}


def test_cancelled_from_pending_and_running() -> None:
    pending = IngestionJob(source_id="s")
    pending.cancel()
    assert pending.state is JobState.CANCELLED

    running = IngestionJob(source_id="s")
    running.start()
    running.cancel()
    assert running.state is JobState.CANCELLED


@pytest.mark.parametrize(
    ("state", "next_state"),
    [
        (JobState.SUCCEEDED, JobState.RUNNING),
        (JobState.FAILED, JobState.RUNNING),
        (JobState.CANCELLED, JobState.RUNNING),
        (JobState.PENDING, JobState.FAILED),
    ],
)
def test_invalid_transitions_raise(state: JobState, next_state: JobState) -> None:
    job = IngestionJob(source_id="s", state=state)
    with pytest.raises(InvalidJobTransitionError):
        job._move_to(next_state)
