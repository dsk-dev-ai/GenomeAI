from __future__ import annotations

from fastapi.testclient import TestClient
from genomeai_api.main import app


def test_lifespan_startup_sets_state() -> None:
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    state = app.state.app_state
    assert state is not None
    assert state.settings.app.service_name == "genomeai"
    assert state.settings.app.version == "0.1.0"
    assert state.logger is not None


def test_root_after_lifespan() -> None:
    with TestClient(app) as client:
        resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_health_after_lifespan() -> None:
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_ready_after_lifespan() -> None:
    with TestClient(app) as client:
        resp = client.get("/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert "database" in body
    assert "redis" in body
    assert body["status"] in ("ok", "degraded")


def test_live_after_lifespan() -> None:
    with TestClient(app) as client:
        resp = client.get("/live")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
