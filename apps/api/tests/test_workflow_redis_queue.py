"""RedisJobQueue tests against a mocked redis.asyncio client.

Verifies the command choreography, the enqueue guard (no duplicate
messages), atomic claim semantics, and that Redis failures surface as
QueueUnavailableError instead of leaking raw exceptions.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from genomeai_api.workflows.errors import JobDecodeError, QueueUnavailableError
from genomeai_api.workflows.queueing import WorkflowJob, job_from_json, job_to_json
from genomeai_api.workflows.redis_queue import RedisJobQueue
from genomeai_api.workflows.types import JobState

PREFIX = "genomeai:workflow-runs"

pytestmark = pytest.mark.asyncio


def _queued_job(run_id: uuid.UUID | None = None) -> WorkflowJob:
    return WorkflowJob(
        job_id=uuid.uuid4(),
        workflow_run_id=run_id or uuid.uuid4(),
        queued_at=datetime(2026, 8, 25, 12, 0, tzinfo=UTC),
    )


def _running_job(queued: WorkflowJob) -> WorkflowJob:
    return WorkflowJob(
        job_id=queued.job_id,
        workflow_run_id=queued.workflow_run_id,
        queued_at=queued.queued_at,
        attempt=queued.attempt,
        state=JobState.RUNNING,
        claimed_at=queued.queued_at + timedelta(seconds=1),
    )


def _client() -> AsyncMock:
    client = AsyncMock()
    # redis.asyncio's pipeline() is synchronous; only execute() is awaited.
    pipeline = MagicMock()
    pipeline.execute = AsyncMock(return_value=[1, 1, 1])
    client.pipeline = MagicMock(return_value=pipeline)
    client.hsetnx.return_value = 1  # HSETNX wins by default
    client.lmove.return_value = None  # empty queue by default
    client.zrangebyscore.return_value = []  # no delayed jobs due by default
    client.zcard.return_value = 0
    # Lua EVAL for promotion: default to no due jobs (returns nil).
    client.eval = AsyncMock(return_value=None)
    return client


# --- enqueue ---------------------------------------------------------------


async def test_enqueue_pushes_payload_and_returns_queued_job() -> None:
    client = _client()
    queue = RedisJobQueue(client)
    run_id = uuid.uuid4()

    job = await queue.enqueue(run_id)

    assert job.state is JobState.QUEUED
    assert job.workflow_run_id == run_id
    raw = client.rpush.call_args.args[1]
    assert job_from_json(raw) == job
    client.hsetnx.assert_awaited_once_with(f"{PREFIX}:active", str(run_id), raw)
    client.rpush.assert_awaited_once_with(f"{PREFIX}:queued", raw)


async def test_enqueue_is_idempotent_when_guard_entry_exists() -> None:
    existing = _queued_job()
    client = _client()
    client.hsetnx.return_value = 0  # HSETNX loses: someone else won the guard
    client.hget.return_value = job_to_json(existing)
    queue = RedisJobQueue(client)

    job = await queue.enqueue(existing.workflow_run_id)

    assert job.job_id == existing.job_id
    client.rpush.assert_not_awaited()


async def test_enqueue_retries_when_guard_entry_vanishes_mid_flight() -> None:
    run_id = uuid.uuid4()
    client = _client()
    # Attempt 1: HSETNX wins, but the entry is gone by lookup time.
    # Attempt 2 (retry): HSETNX wins again and the push succeeds.
    client.hsetnx.side_effect = [1, 1]
    client.hget.side_effect = [None]

    queue = RedisJobQueue(client)
    job = await queue.enqueue(run_id)

    assert job.workflow_run_id == run_id
    assert client.rpush.await_count == 1


# --- claim -----------------------------------------------------------------


async def test_claim_moves_payload_atomically_and_marks_running() -> None:
    queued = _queued_job()
    client = _client()
    client.lmove.return_value = job_to_json(queued)
    queue = RedisJobQueue(client)

    job = await queue.claim("worker-7")

    assert job is not None
    assert job.state is JobState.RUNNING
    assert job.claimed_at is not None
    assert job.workflow_run_id == queued.workflow_run_id
    client.lmove.assert_awaited_once_with(
        f"{PREFIX}:queued", f"{PREFIX}:processing", "RIGHT", "LEFT"
    )
    claims_call = client.hset.call_args
    assert claims_call.args[0] == f"{PREFIX}:claims"
    # The claims hash stores the EXACT bytes moved to the processing list,
    # so the release LREM can match and remove them.
    assert claims_call.args[2] == job_to_json(queued)


async def test_claim_on_empty_queue_returns_none() -> None:
    queue = RedisJobQueue(_client())

    assert await queue.claim("worker-1") is None


async def test_malformed_claimed_payload_raises_decode_error() -> None:
    client = _client()
    client.lmove.return_value = "{not-json"
    queue = RedisJobQueue(client)

    with pytest.raises(JobDecodeError):
        await queue.claim("worker-1")


# --- complete / fail -------------------------------------------------------


async def test_complete_removes_processing_claim_and_active_entries() -> None:
    queued = _queued_job()
    running = _running_job(queued)
    client = _client()
    client.hget.return_value = job_to_json(running)
    queue = RedisJobQueue(client)

    await queue.complete(running)

    pipeline = client.pipeline.return_value
    lrem_args = pipeline.lrem.call_args.args
    assert lrem_args[0] == f"{PREFIX}:processing"
    pipeline.hdel.assert_any_call(f"{PREFIX}:claims", str(running.job_id))
    pipeline.hdel.assert_any_call(f"{PREFIX}:active", str(running.workflow_run_id))
    pipeline.execute.assert_awaited_once()


async def test_fail_releases_job_like_complete() -> None:
    queued = _queued_job()
    running = _running_job(queued)
    client = _client()
    client.hget.return_value = job_to_json(running)
    queue = RedisJobQueue(client)

    await queue.fail(running, "boom")

    pipeline = client.pipeline.return_value
    pipeline.execute.assert_awaited_once()
    pipeline.hdel.assert_any_call(f"{PREFIX}:claims", str(running.job_id))
    pipeline.hdel.assert_any_call(f"{PREFIX}:active", str(running.workflow_run_id))


# --- depth / failures ------------------------------------------------------


async def test_depth_reports_waiting_jobs() -> None:
    client = _client()
    client.llen.return_value = 3

    assert await RedisJobQueue(client).depth() == 3


@pytest.mark.parametrize(
    ("method", "command", "args"),
    [
        ("enqueue", "hsetnx", (uuid.uuid4(),)),
        ("claim", "lmove", ("w",)),
        ("depth", "llen", ()),
    ],
)
async def test_redis_failures_surface_as_unavailable(
    method: str, command: str, args: tuple
) -> None:
    client = _client()
    getattr(client, command).side_effect = ConnectionError("redis down")

    with pytest.raises(QueueUnavailableError):
        await getattr(RedisJobQueue(client), method)(*args)


async def test_release_failure_surfaces_as_unavailable() -> None:
    client = _client()
    client.hget.side_effect = ConnectionError("redis down")
    job = _queued_job()

    with pytest.raises(QueueUnavailableError):
        await RedisJobQueue(client).complete(job)


async def test_close_is_no_op_client_owned_by_composition_root() -> None:
    client = _client()

    await RedisJobQueue(client).close()

    client.aclose.assert_not_called()


async def test_full_cycle_removes_exact_bytes_from_processing_list() -> None:
    """Regression: release must LREM the same bytes that claim moved,
    otherwise payloads leak on the processing list forever."""
    run_id = uuid.uuid4()
    pushed: list[str] = {}
    claimed_stored: dict[str, str] = {}

    client = _client()

    async def rpush(key: str, value: str) -> int:
        pushed[key] = value
        return 1

    async def lmove(src: str, dst: str, src_dir: str, dst_dir: str):
        del src, dst, src_dir, dst_dir
        return pushed[f"{PREFIX}:queued"]

    async def hsetnx(key: str, field: str, value: str) -> int:
        del key
        pushed[field] = value  # active guard
        return 1

    async def hset(key: str, field: str, value: str) -> int:
        claimed_stored[field] = value
        return 1

    async def hget(key: str, field: str):
        del key
        return claimed_stored.get(field)

    client.rpush = rpush
    client.lmove = lmove
    client.hsetnx = hsetnx
    client.hset = MagicMock(side_effect=hset)
    client.hget = hget

    queue = RedisJobQueue(client)
    await queue.enqueue(run_id)
    job = await queue.claim("worker-1")
    assert job is not None

    await queue.complete(job)

    lrem_args = client.pipeline.return_value.lrem.call_args.args
    removed_bytes = lrem_args[2]
    assert removed_bytes == pushed[f"{PREFIX}:queued"]


# --- delayed enqueue (Phase 7.5) -----------------------------------------


async def test_delayed_enqueue_goes_to_zset_with_ready_score() -> None:
    moment = datetime(2026, 8, 25, 12, 0, tzinfo=UTC)
    client = _client()
    queue = RedisJobQueue(client, now=lambda: moment)

    job = await queue.enqueue(uuid.uuid4(), delay=timedelta(seconds=30))

    zadd_args = client.zadd.call_args
    assert zadd_args.args[0] == f"{PREFIX}:scheduled"
    member, score = next(iter(zadd_args.args[1].items()))
    assert job_from_json(member) == job
    assert score == (moment + timedelta(seconds=30)).timestamp()
    client.rpush.assert_not_awaited()


async def test_zero_delay_enqueues_immediately() -> None:
    client = _client()

    await RedisJobQueue(client).enqueue(uuid.uuid4(), delay=timedelta(0))

    client.zadd.assert_not_awaited()
    client.rpush.assert_awaited_once()


async def test_claim_promotes_due_scheduled_job() -> None:
    queued = _queued_job()
    raw = job_to_json(queued)
    client = _client()
    # Lua script returns the promoted member on the first call, then nil.
    client.eval = AsyncMock(side_effect=[b"ok", None])
    client.lmove.return_value = raw
    queue = RedisJobQueue(client)

    claimed = await queue.claim("worker-1")

    assert claimed is not None
    assert claimed.job_id == queued.job_id
    # eval is called with the Lua script and both keys.
    client.eval.assert_awaited()
    call_args = client.eval.call_args
    assert call_args.args[0] == RedisJobQueue._PROMOTE_LUA


async def test_claim_skips_member_lost_to_another_promoter() -> None:
    client = _client()
    # Lua script returns nil (member lost to ZREM gate or nothing due).
    client.eval = AsyncMock(return_value=None)
    client.lmove.return_value = None

    result = await RedisJobQueue(client).claim("worker-1")

    assert result is None


async def test_delayed_counts_scheduled_jobs() -> None:
    client = _client()
    client.zcard.return_value = 4

    assert await RedisJobQueue(client).delayed() == 4

# --- reschedule (Phase 7.5) --------------------------------------------------


@pytest.mark.asyncio
async def test_reschedule_atomically_releases_and_schedules_delayed_replacement() -> None:
    client = _client()
    # Reschedule issues 4 pipeline ops (LREM + HDEL + HSET active + ZADD);
    # mock must return one result per operation.
    client.pipeline.return_value.execute = AsyncMock(return_value=[1, 1, 1, 1])
    queue = RedisJobQueue(client)
    run_id = uuid.uuid4()
    job = await queue.enqueue(run_id)
    raw = job_to_json(job)
    client.lmove.return_value = raw  # claim retrieves the enqueued bytes

    claimed = await queue.claim("worker-1")
    assert claimed is not None

    replacement = await queue.reschedule(job=claimed, delay=timedelta(seconds=30))

    assert replacement.job_id != claimed.job_id
    assert replacement.workflow_run_id == run_id
    # Pipeline wrote a ZADD for the delayed replacement (functional
    # correctness of the scheduled heap is covered by InMemory tests).
    pipeline = client.pipeline.return_value
    pipeline.zadd.assert_called()
    pipeline.execute.assert_awaited_once()
