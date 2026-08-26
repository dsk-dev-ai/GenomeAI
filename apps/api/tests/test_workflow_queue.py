"""Queue domain tests: job serialization, idempotency, exclusive claims."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from genomeai_api.workflows.errors import JobDecodeError
from genomeai_api.workflows.queueing import (
    JOB_SCHEMA_VERSION,
    InMemoryJobQueue,
    WorkflowJob,
    job_from_json,
    job_to_json,
)
from genomeai_api.workflows.types import JobState

pytestmark = pytest.mark.asyncio


def _job(**overrides: object) -> WorkflowJob:
    defaults: dict[str, object] = {
        "job_id": uuid.uuid4(),
        "workflow_run_id": uuid.uuid4(),
        "queued_at": datetime(2026, 8, 25, 12, 0, tzinfo=UTC),
    }
    defaults.update(overrides)
    return WorkflowJob(**defaults)  # type: ignore[arg-type]


# --- serialization ------------------------------------------------------


async def test_job_json_roundtrip_is_lossless() -> None:
    job = _job(attempt=2)

    decoded = job_from_json(job_to_json(job))

    assert decoded == job


async def test_job_json_is_deterministic() -> None:
    job = _job()

    assert job_to_json(job) == job_to_json(job)
    payload = json.loads(job_to_json(job))
    assert payload["schema"] == JOB_SCHEMA_VERSION
    # Sorted keys make byte-identical encodings across processes.
    assert list(json.loads(job_to_json(job))) == sorted(payload)


async def test_job_json_rejects_naive_queued_at() -> None:
    with pytest.raises(JobDecodeError):
        job_to_json(_job(queued_at=datetime(2026, 8, 25, 12, 0)))


@pytest.mark.parametrize(
    "raw",
    [
        "not json at all",
        "[1, 2, 3]",
        "{}",
        json.dumps({"job_id": "nope", "workflow_run_id": "also-nope"}),
        json.dumps({"state": "teleported"}),
    ],
)
async def test_malformed_payloads_are_rejected(raw: str) -> None:
    with pytest.raises(JobDecodeError):
        job_from_json(raw)


async def test_payload_missing_required_fields_is_rejected() -> None:
    incomplete = json.dumps({"job_id": str(uuid.uuid4())})

    # BaseError surfaces the generic message; the reason lives in `detail`.
    with pytest.raises(JobDecodeError) as excinfo:
        job_from_json(incomplete)

    assert "missing" in str(excinfo.value.detail)


# --- InMemoryJobQueue: enqueue / claim / release --------------------------


async def test_enqueue_creates_queued_job() -> None:
    queue = InMemoryJobQueue()
    run_id = uuid.uuid4()

    job = await queue.enqueue(run_id)

    assert job.workflow_run_id == run_id
    assert job.state is JobState.QUEUED
    assert await queue.depth() == 1


async def test_enqueue_is_idempotent_per_run() -> None:
    queue = InMemoryJobQueue()
    run_id = uuid.uuid4()

    first = await queue.enqueue(run_id)
    second = await queue.enqueue(run_id)

    assert second.job_id == first.job_id
    assert await queue.depth() == 1


async def test_claim_returns_fifo_and_marks_running() -> None:
    queue = InMemoryJobQueue()
    first = await queue.enqueue(uuid.uuid4())
    second = await queue.enqueue(uuid.uuid4())

    claimed_first = await queue.claim("worker-a")
    claimed_second = await queue.claim("worker-b")

    assert claimed_first is not None and claimed_second is not None
    assert [claimed_first.job_id, claimed_second.job_id] == [first.job_id, second.job_id]
    assert claimed_first.state is JobState.RUNNING
    assert claimed_first.claimed_at is not None
    del second


async def test_claim_on_empty_queue_returns_none() -> None:
    assert await InMemoryJobQueue().claim("worker-a") is None


async def test_two_workers_receive_different_jobs() -> None:
    queue = InMemoryJobQueue()
    for _ in range(3):
        await queue.enqueue(uuid.uuid4())
    seen: set[uuid.UUID] = set()

    for worker in ("w1", "w2", "w3"):
        job = await queue.claim(worker)
        assert job is not None
        assert job.job_id not in seen
        seen.add(job.job_id)


async def test_complete_releases_claim_and_allows_reenqueue() -> None:
    queue = InMemoryJobQueue()
    run_id = uuid.uuid4()
    job = await queue.enqueue(run_id)
    claimed = await queue.claim("worker-a")
    assert claimed is not None
    del job

    await queue.complete(claimed)

    requeued = await queue.enqueue(run_id)
    assert requeued.job_id != claimed.job_id
    assert requeued.state is JobState.QUEUED


async def test_fail_records_terminal_failed_state() -> None:
    queue = InMemoryJobQueue()
    job = await queue.enqueue(uuid.uuid4())
    claimed = await queue.claim("worker-a")
    assert claimed is not None

    await queue.fail(claimed, "boom")

    # The caller's frozen job object is untouched by design; release means
    # the claim is dropped and the run may be enqueued again.
    assert claimed.state is JobState.RUNNING
    assert await queue.depth() == 0
    requeued = await queue.enqueue(job.workflow_run_id)
    assert requeued.state is JobState.QUEUED


async def test_duplicate_delivery_never_yields_same_job_twice() -> None:
    queue = InMemoryJobQueue()
    run_id = uuid.uuid4()
    # Simulate duplicate messages by enqueueing two distinct runs; each
    # claim must hand out a DIFFERENT job even under repeated calls.
    await queue.enqueue(run_id)
    await queue.enqueue(uuid.uuid4())

    first = await queue.claim("w1")
    second = await queue.claim("w1")

    assert first is not None and second is not None
    assert first.job_id != second.job_id


async def test_close_is_idempotent() -> None:
    queue = InMemoryJobQueue()

    await queue.close()
    await queue.close()


# --- delayed enqueue (Phase 7.5) -----------------------------------------


class _ManualClock:
    def __init__(self) -> None:
        self.moment = datetime(2026, 8, 25, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.moment


async def test_delayed_job_is_not_claimable_before_ready() -> None:
    clock = _ManualClock()
    queue = InMemoryJobQueue(now=clock)
    await queue.enqueue(uuid.uuid4(), delay=timedelta(seconds=10))
    assert await queue.depth() == 0

    clock.moment = datetime(2026, 8, 25, 12, 0, 9, tzinfo=UTC)
    assert await queue.claim("w") is None
    assert await queue.delayed() == 1
    assert await queue.depth() == 0


async def test_delayed_job_becomes_claimable_at_ready_time() -> None:
    clock = _ManualClock()
    queue = InMemoryJobQueue(now=clock)
    job = await queue.enqueue(uuid.uuid4(), delay=timedelta(seconds=10))

    clock.moment = datetime(2026, 8, 25, 12, 0, 10, tzinfo=UTC)
    claimed = await queue.claim("w")

    assert claimed is not None and claimed.job_id == job.job_id
    assert await queue.delayed() == 0


async def test_due_delayed_jobs_are_promoted_in_enqueue_order() -> None:
    clock = _ManualClock()
    queue = InMemoryJobQueue(now=clock)
    first = await queue.enqueue(uuid.uuid4(), delay=timedelta(seconds=5))
    second = await queue.enqueue(uuid.uuid4(), delay=timedelta(seconds=9))

    clock.moment = datetime(2026, 8, 25, 12, 0, 30, tzinfo=UTC)
    got_first = await queue.claim("w")
    got_second = await queue.claim("w")

    assert [got_first.job_id, got_second.job_id] == [first.job_id, second.job_id]


async def test_zero_or_negative_delay_enqueues_immediately() -> None:
    queue = InMemoryJobQueue()

    await queue.enqueue(uuid.uuid4(), delay=timedelta(0))
    await queue.enqueue(uuid.uuid4(), delay=timedelta(seconds=-5))

    assert await queue.delayed() == 0
    assert await queue.depth() == 2


async def test_duplicate_enqueue_is_idempotent_across_delayed_and_immediate() -> None:
    clock = _ManualClock()
    queue = InMemoryJobQueue(now=clock)
    run_id = uuid.uuid4()
    delayed = await queue.enqueue(run_id, delay=timedelta(seconds=5))

    again = await queue.enqueue(run_id)

    assert again.job_id == delayed.job_id
    assert await queue.depth() == 0
    assert await queue.delayed() == 1

# --- reschedule (Phase 7.5) --------------------------------------------------


async def test_reschedule_releases_original_and_creates_delayed_replacement() -> None:
    queue = InMemoryJobQueue(now=lambda: datetime.now(UTC))
    run_id = uuid.uuid4()
    await queue.enqueue(run_id)
    claimed = await queue.claim("worker-1")
    assert claimed is not None

    replacement = await queue.reschedule(claimed, delay=timedelta(seconds=60))

    assert replacement.job_id != claimed.job_id
    assert replacement.workflow_run_id == run_id
    assert await queue.delayed() == 1
    assert await queue.depth() == 0
    # Original job is gone — can't be claimed again.
    assert await queue.claim("worker-1") is None


async def test_reschedule_with_zero_delay_puts_replacement_immediately() -> None:
    queue = InMemoryJobQueue(now=lambda: datetime.now(UTC))
    run_id = uuid.uuid4()
    await queue.enqueue(run_id)
    claimed = await queue.claim("worker-1")
    assert claimed is not None

    replacement = await queue.reschedule(claimed, delay=timedelta(0))

    assert await queue.depth() == 1
    assert await queue.delayed() == 0
    # Replacement is claimable right away.
    second_claim = await queue.claim("worker-2")
    assert second_claim is not None
    assert second_claim.job_id == replacement.job_id
