from __future__ import annotations

from fastapi.testclient import TestClient
from genomeai_api.main import app


def test_lifespan_startup_sets_state() -> None:
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    assert app.state.settings is not None
    assert app.state.logger is not None
    assert app.state.settings.app.service_name == "genomeai"
    assert app.state.settings.app.version == "0.1.0"


def test_health_after_lifespan() -> None:
    with TestClient(app) as client:
        resp_root = client.get("/")
        resp_health = client.get("/health")
        resp_ready = client.get("/ready")
        resp_live = client.get("/live")
    assert resp_root.status_code == 200
    assert resp_root.json() == {"status": "ok"}
    assert resp_health.status_code == 200
    assert resp_health.json() == {"status": "ok"}
    assert resp_ready.status_code == 200
    assert resp_ready.json() == {"status": "ok"}
    assert resp_live.status_code == 200
    assert resp_live.json() == {"status": "ok"}
