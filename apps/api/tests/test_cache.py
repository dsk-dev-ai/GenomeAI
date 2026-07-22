from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from genomeai_api.cache import create_redis, shutdown_redis, verify_redis
from genomeai_config import RedisSettings


def test_create_redis() -> None:
    settings = RedisSettings(host="localhost", port=6379, db=0)
    with (
        patch("redis.asyncio.ConnectionPool.from_url") as mock_pool,
        patch("redis.asyncio.Redis.from_pool") as mock_from_pool,
    ):
        mock_pool.return_value = "pool"
        _ = create_redis(settings)
        mock_pool.assert_called_once_with(settings.url, max_connections=20)
        mock_from_pool.assert_called_once_with("pool")


@pytest.mark.asyncio
async def test_verify_redis_true() -> None:
    client = AsyncMock()
    client.ping.return_value = True
    result = await verify_redis(client)
    assert result is True


@pytest.mark.asyncio
async def test_verify_redis_false() -> None:
    client = AsyncMock()
    client.ping.side_effect = Exception("connection failed")
    result = await verify_redis(client)
    assert result is False


@pytest.mark.asyncio
async def test_shutdown_redis_none() -> None:
    await shutdown_redis(None)


@pytest.mark.asyncio
async def test_shutdown_redis() -> None:
    client = AsyncMock()
    await shutdown_redis(client)
    client.aclose.assert_awaited_once()
