from __future__ import annotations

from fastapi.testclient import TestClient
from genomeai_api.main import app


def test_cors_preflight_allows_frontend_origin() -> None:
    with TestClient(app) as client:
        resp = client.options(
            "/api/v1/genes/analyze",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
    assert resp.status_code == 200
    allow_origin = resp.headers.get("access-control-allow-origin")
    assert allow_origin == "http://localhost:3000"
    allowed_methods = resp.headers.get("access-control-allow-methods", "")
    assert "POST" in allowed_methods
    assert "content-type" in resp.headers.get(
        "access-control-allow-headers", ""
    )


def test_cors_response_headers_on_actual_request() -> None:
    with TestClient(app) as client:
        resp = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"
