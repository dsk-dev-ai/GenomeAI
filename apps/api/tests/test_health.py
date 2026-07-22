from __future__ import annotations

from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from genomeai_api.main import app
from genomeai_api.state import AppState


def test_root() -> None:
    with TestClient(app) as client:
        resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_health() -> None:
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_ready_strengthened() -> None:
    with TestClient(app) as client:
        resp = client.get("/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"database", "redis", "status"}
    assert body["status"] in ("ok", "degraded")
    assert body["database"] in ("ok", "error", "not_configured")
    assert body["redis"] in ("ok", "error", "not_configured")


def test_live() -> None:
    with TestClient(app) as client:
        resp = client.get("/live")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.parametrize(
    ("db_setup", "redis_setup", "expected_db", "expected_redis", "expected_status"),
    [
        ("healthy", "healthy", "ok", "ok", "ok"),
        ("healthy", "failure", "ok", "error", "degraded"),
        ("healthy", "none", "ok", "not_configured", "ok"),
        ("failure", "healthy", "error", "ok", "degraded"),
        ("none", "healthy", "not_configured", "ok", "ok"),
        ("failure", "failure", "error", "error", "degraded"),
        ("none", "none", "not_configured", "not_configured", "ok"),
    ],
)
def test_ready_scenarios(
    db_setup: str,
    redis_setup: str,
    expected_db: str,
    expected_redis: str,
    expected_status: str,
) -> None:
    with TestClient(app) as client:
        state = cast(AppState, app.state.app_state)
        if db_setup == "healthy":
            mock_engine = MagicMock()
            mock_engine.dispose = AsyncMock()
            mock_conn = AsyncMock()
            acm = AsyncMock()
            acm.return_value = mock_conn
            mock_engine.connect.return_value = acm
            state.db_engine = mock_engine
        elif db_setup == "failure":
            mock_engine = MagicMock()
            mock_engine.dispose = AsyncMock()
            mock_engine.connect.side_effect = Exception("db error")
            state.db_engine = mock_engine
        elif db_setup == "none":
            state.db_engine = None
        if redis_setup == "healthy":
            mock_redis = AsyncMock()
            mock_redis.ping.return_value = True
            state.redis = mock_redis
        elif redis_setup == "failure":
            mock_redis = AsyncMock()
            mock_redis.ping.side_effect = Exception("redis error")
            state.redis = mock_redis
        elif redis_setup == "none":
            state.redis = None
        resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.json() == {
        "database": expected_db,
        "redis": expected_redis,
        "status": expected_status,
    }
