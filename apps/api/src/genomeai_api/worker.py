"""Standalone workflow-run worker entrypoint (Phase 7.4).

Runs the application-level worker loop against Redis + PostgreSQL:

    WorkflowRunWorker
      → JobQueue (RedisJobQueue)
      → per-job SQLAlchemy session → WorkflowRepository
      → DAGExecutionEngine (+ PassthroughStepExecutor until real executors land)

Shutdown: SIGINT/SIGTERM stop claiming new jobs, let the current job
finish, close queue/session resources, then exit cleanly.
"""

from __future__ import annotations

import asyncio
import signal
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import timedelta

from genomeai_api.cache import create_redis, shutdown_redis
from genomeai_api.database import create_engine, create_session_factory, dispose_engine
from genomeai_api.repositories.workflow import WorkflowRepository
from genomeai_api.services.worker import WorkflowRunWorker
from genomeai_api.workflows.execution.engine import DAGExecutionEngine
from genomeai_api.workflows.execution.executor import PassthroughStepExecutor
from genomeai_api.workflows.redis_queue import DEFAULT_PREFIX, RedisJobQueue
from genomeai_api.workflows.retry import ExponentialBackoff, RetryPolicy

# Composition-root defaults for the standalone worker process: three
# attempts total with 1s → 2s → capped exponential backoff. Override by
# running workers in-process with an explicit RetryPolicy.
DEFAULT_RETRY_POLICY = RetryPolicy(
    max_attempts=3,
    backoff=ExponentialBackoff(
        initial=timedelta(seconds=1),
        multiplier=2.0,
        max_delay=timedelta(seconds=30),
    ),
)


async def main() -> int:
    from genomeai_config import load_settings
    from genomeai_logging import configure_logging, get_logger

    settings = load_settings()
    configure_logging(level=settings.log_level.value, json_format=settings.logging.json_format)
    logger = get_logger("genomeai.worker")

    db_engine = create_engine(settings.database)
    session_factory = create_session_factory(db_engine)
    assert session_factory is not None

    redis_client = create_redis(settings.redis)

    @asynccontextmanager
    async def store_factory() -> AsyncGenerator[WorkflowRepository, None]:
        async with session_factory() as session:
            yield WorkflowRepository(session)

    queue = RedisJobQueue(redis_client, prefix=DEFAULT_PREFIX)
    worker = WorkflowRunWorker(
        queue,
        store_factory,
        PassthroughStepExecutor(),
        worker_id="worker-1",
        logger=logger,
        engine_factory=lambda store: DAGExecutionEngine(store, PassthroughStepExecutor()),
        retry_policy=DEFAULT_RETRY_POLICY,
    )

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    try:
        await worker.run_forever(stop)
    finally:
        await shutdown_redis(redis_client)
        await dispose_engine(db_engine)
    return 0


def run() -> None:
    raise SystemExit(asyncio.run(main()))


if __name__ == "__main__":
    run()
