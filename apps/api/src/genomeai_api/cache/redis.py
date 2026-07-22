from __future__ import annotations

from fastapi import Request
from genomeai_config import RedisSettings
from redis.asyncio import ConnectionPool, Redis

from genomeai_api.state import AppState


def create_redis(settings: RedisSettings) -> Redis:
    pool = ConnectionPool.from_url(settings.url, max_connections=20)
    return Redis.from_pool(pool)


async def shutdown_redis(client: Redis | None) -> None:
    if client is None:
        return
    await client.aclose()


async def verify_redis(client: Redis) -> bool:
    try:
        return await client.ping()
    except Exception:
        return False


def get_redis(request: Request) -> Redis:
    state: AppState = request.app.state.app_state
    if state.redis is None:
        raise RuntimeError("redis not initialized")
    return state.redis
