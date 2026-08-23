from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from genomeai_api.integration.errors import (
    ConnectorNotFoundError,
    DataSourceNotFoundError,
    IntegrationConfigurationError,
    InvalidJobTransitionError,
    UnsafeSourceUrlError,
)
from genomeai_api.routes.integrations import _get_service, router
from genomeai_api.schemas.integration import (
    ConnectorHealthResponse,
    DataSourceResponse,
    IngestionJobResponse,
)
from genomeai_api.services.integration import IntegrationService

ERROR_STATUS = {
    DataSourceNotFoundError: status.HTTP_404_NOT_FOUND,
    ConnectorNotFoundError: status.HTTP_404_NOT_FOUND,
    UnsafeSourceUrlError: status.HTTP_400_BAD_REQUEST,
    IntegrationConfigurationError: status.HTTP_409_CONFLICT,
    InvalidJobTransitionError: status.HTTP_409_CONFLICT,
}


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock(spec=IntegrationService)


@pytest.fixture
def client(mock_service: AsyncMock) -> TestClient:
    app = FastAPI()
    app.include_router(router)

    for exc_type, code in ERROR_STATUS.items():
        def _make_handler(code: int):
            async def handler(request: Request, exc: Exception) -> JSONResponse:
                return JSONResponse(status_code=code, content={"detail": str(exc)})
            return handler

        app.add_exception_handler(exc_type, _make_handler(code))

    async def override() -> IntegrationService:
        return mock_service  # type: ignore[return-value]

    app.dependency_overrides[_get_service] = override
    return TestClient(app)


def _source_response(source_id: str = "genomeai-reference") -> DataSourceResponse:
    now = datetime.now(UTC)
    return DataSourceResponse(
        id=uuid.uuid4(),
        source_id=source_id,
        provider="GenomeAI",
        display_name="GenomeAI Reference Source",
        source_type="other",
        api_base_url="https://reference.internal",
        documentation_url=None,
        auth_mode="none",
        credential_ref=None,
        rate_limit={},
        license_info={"access": "reference-only"},
        access_mode="live",
        source_version="2026.08",
        last_synced_at=None,
        sync_status="idle",
        enabled=True,
        feature_flags={},
        created_at=now,
        updated_at=now,
    )


def _job_response(state: str = "pending") -> IngestionJobResponse:
    now = datetime.now(UTC)
    return IngestionJobResponse(
        id=uuid.uuid4(),
        source_id="genomeai-reference",
        state=state,  # type: ignore[arg-type]
        started_at=None if state == "pending" else now,
        finished_at=None,
        records_received=0,
        records_succeeded=0,
        records_failed=0,
        error_message=None,
        created_at=now,
    )


def test_list_sources(client: TestClient, mock_service: AsyncMock) -> None:
    mock_service.list_sources.return_value = [_source_response()]
    response = client.get("/integration/sources")
    assert response.status_code == 200
    body = response.json()
    assert body[0]["source_id"] == "genomeai-reference"
    assert body[0]["credential_ref"] is None


def test_register_source_returns_created(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.register_source.return_value = _source_response()
    payload = {
        "source_id": "genomeai-reference",
        "provider": "GenomeAI",
        "display_name": "Reference",
        "api_base_url": "https://reference.internal",
    }
    response = client.post("/integration/sources", json=payload)
    assert response.status_code == 201


def test_unknown_source_maps_to_404(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.get_source.side_effect = DataSourceNotFoundError("missing")
    response = client.get("/integration/sources/missing")
    assert response.status_code == 404


def test_unregistered_connector_maps_to_404(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.register_source.side_effect = ConnectorNotFoundError("x")
    response = client.post(
        "/integration/sources",
        json={
            "source_id": "x",
            "provider": "p",
            "display_name": "d",
            "api_base_url": "https://ok.example.com",
        },
    )
    assert response.status_code == 404


def test_health_endpoint_returns_connector_health(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.check_source_health.return_value = ConnectorHealthResponse(
        source_id="genomeai-reference",
        ok=True,
        checked_at=datetime.now(UTC),
        message="healthy",
        latency_ms=12,
    )
    response = client.get("/integration/sources/genomeai-reference/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["latency_ms"] == 12


def test_disabled_source_health_maps_to_409(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.check_source_health.side_effect = IntegrationConfigurationError("disabled")
    response = client.get("/integration/sources/genomeai-reference/health")
    assert response.status_code == 409


def test_create_and_drive_ingestion_job(
    client: TestClient, mock_service: AsyncMock
) -> None:
    job = _job_response("running")
    mock_service.create_job.return_value = _job_response("pending")
    mock_service.start_job.return_value = job

    created = client.post(
        "/integration/jobs", json={"source_id": "genomeai-reference"}
    )
    assert created.status_code == 201
    job_id = created.json()["id"]

    started = client.post(f"/integration/jobs/{job_id}/start")
    assert started.status_code == 200
    assert started.json()["state"] == "running"


def test_invalid_job_transition_maps_to_409(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.start_job.side_effect = InvalidJobTransitionError("succeeded", "running")
    response = client.post("/integration/jobs/00000000-0000-0000-0000-000000000000/start")
    assert response.status_code == 409


def test_connectors_listing_is_static_metadata(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.registered_connectors.return_value = [
        {"source_id": "genomeai-reference", "display_name": "GenomeAI Reference Source"}
    ]
    response = client.get("/integration/connectors")
    assert response.status_code == 200
    assert response.json()[0]["source_id"] == "genomeai-reference"
