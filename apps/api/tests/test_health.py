from fastapi.testclient import TestClient
from genomeai_api.main import app


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


def test_ready() -> None:
    with TestClient(app) as client:
        resp = client.get("/ready")
    assert resp.status_code == 200


def test_live() -> None:
    with TestClient(app) as client:
        resp = client.get("/live")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
