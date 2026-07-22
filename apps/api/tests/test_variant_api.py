from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from genomeai_api.exceptions import DuplicateVariantError
from genomeai_api.routes.variants import _get_service, router
from genomeai_api.schemas.variant import VariantCreate, VariantResponse
from genomeai_api.services.variant import VariantService


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock(spec=VariantService)


@pytest.fixture
def test_app(mock_service: AsyncMock) -> FastAPI:
    app = FastAPI()
    app.include_router(router)

    @app.exception_handler(DuplicateVariantError)
    async def _handler(request: Request, exc: DuplicateVariantError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)},
        )

    async def override() -> VariantService:
        return mock_service

    app.dependency_overrides[_get_service] = override
    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


@pytest.fixture
def sample_variant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def sample_response(sample_variant_id: uuid.UUID) -> dict[str, object]:
    now = datetime.now(UTC).isoformat()
    return {
        "id": str(sample_variant_id),
        "variant_id": "chr17_7674220_G_A",
        "chromosome": "17",
        "position": 7674220,
        "ref": "G",
        "alt": "A",
        "type": "snv",
        "quality": 999.5,
        "filter_status": "PASS",
        "genome_id": None,
        "gene_id": None,
        "description": "A somatic SNV",
        "created_at": now,
        "updated_at": now,
    }


def test_create_variant_201(
    client: TestClient,
    mock_service: AsyncMock,
    sample_response: dict[str, object],
) -> None:
    mock_service.create.return_value = VariantResponse(**sample_response)

    payload = {
        "variant_id": "chr17_7674220_G_A",
        "chromosome": "17",
        "position": 7674220,
        "ref": "G",
        "alt": "A",
    }
    resp = client.post("/variants/", json=payload)

    assert resp.status_code == 201
    assert resp.json()["variant_id"] == "chr17_7674220_G_A"
    mock_service.create.assert_awaited_once()
    call_arg = mock_service.create.call_args[0][0]
    assert isinstance(call_arg, VariantCreate)


def test_create_variant_422_missing_fields(client: TestClient) -> None:
    resp = client.post("/variants/", json={})
    assert resp.status_code == 422


def test_create_variant_422_variant_id_too_long(client: TestClient) -> None:
    resp = client.post(
        "/variants/",
        json={
            "variant_id": "V" * 256,
            "chromosome": "17",
            "position": 7674220,
            "ref": "G",
            "alt": "A",
        },
    )
    assert resp.status_code == 422


def test_create_variant_422_chromosome_too_long(client: TestClient) -> None:
    resp = client.post(
        "/variants/",
        json={
            "variant_id": "chr17_7674220_G_A",
            "chromosome": "C" * 11,
            "position": 7674220,
            "ref": "G",
            "alt": "A",
        },
    )
    assert resp.status_code == 422


def test_create_variant_409_duplicate(
    client: TestClient,
    mock_service: AsyncMock,
) -> None:
    mock_service.create.side_effect = DuplicateVariantError()

    payload = {
        "variant_id": "chr17_7674220_G_A",
        "chromosome": "17",
        "position": 7674220,
        "ref": "G",
        "alt": "A",
    }
    resp = client.post("/variants/", json=payload)

    assert resp.status_code == 409
    assert resp.json()["detail"] == "Variant already exists"


def test_list_variants(
    client: TestClient,
    mock_service: AsyncMock,
    sample_response: dict[str, object],
) -> None:
    mock_service.list.return_value = [VariantResponse(**sample_response)]

    resp = client.get("/variants/")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["variant_id"] == "chr17_7674220_G_A"


def test_list_variants_empty(client: TestClient, mock_service: AsyncMock) -> None:
    mock_service.list.return_value = []

    resp = client.get("/variants/")

    assert resp.status_code == 200
    assert resp.json() == []


def test_get_variant_200(
    client: TestClient,
    mock_service: AsyncMock,
    sample_variant_id: uuid.UUID,
    sample_response: dict[str, object],
) -> None:
    mock_service.get_by_id.return_value = VariantResponse(**sample_response)

    resp = client.get(f"/variants/{sample_variant_id}")

    assert resp.status_code == 200
    assert resp.json()["id"] == str(sample_variant_id)


def test_get_variant_404(client: TestClient, mock_service: AsyncMock) -> None:
    mock_service.get_by_id.return_value = None

    resp = client.get(f"/variants/{uuid.uuid4()}")

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Variant not found"


def test_get_variant_422_invalid_uuid(client: TestClient) -> None:
    resp = client.get("/variants/not-a-uuid")
    assert resp.status_code == 422


def test_update_variant_200(
    client: TestClient,
    mock_service: AsyncMock,
    sample_variant_id: uuid.UUID,
    sample_response: dict[str, object],
) -> None:
    mock_service.update.return_value = VariantResponse(**sample_response)

    resp = client.patch(f"/variants/{sample_variant_id}", json={"chromosome": "X"})

    assert resp.status_code == 200
    assert resp.json()["id"] == str(sample_variant_id)


def test_update_variant_404(client: TestClient, mock_service: AsyncMock) -> None:
    mock_service.update.return_value = None

    resp = client.patch(f"/variants/{uuid.uuid4()}", json={"chromosome": "X"})

    assert resp.status_code == 404


def test_update_variant_422_invalid_body(
    client: TestClient,
    sample_variant_id: uuid.UUID,
) -> None:
    resp = client.patch(f"/variants/{sample_variant_id}", json={"variant_id": 123})
    assert resp.status_code == 422


def test_update_variant_422_variant_id_too_long(
    client: TestClient,
    sample_variant_id: uuid.UUID,
) -> None:
    resp = client.patch(f"/variants/{sample_variant_id}", json={"variant_id": "V" * 256})
    assert resp.status_code == 422


def test_update_variant_409_duplicate(
    client: TestClient,
    mock_service: AsyncMock,
    sample_variant_id: uuid.UUID,
) -> None:
    mock_service.update.side_effect = DuplicateVariantError()

    resp = client.patch(
        f"/variants/{sample_variant_id}",
        json={"variant_id": "chr17_7674221_C_T"},
    )

    assert resp.status_code == 409
    assert resp.json()["detail"] == "Variant already exists"


def test_delete_variant_204(client: TestClient, mock_service: AsyncMock) -> None:
    mock_service.delete.return_value = True

    resp = client.delete(f"/variants/{uuid.uuid4()}")

    assert resp.status_code == 204


def test_delete_variant_404(client: TestClient, mock_service: AsyncMock) -> None:
    mock_service.delete.return_value = False

    resp = client.delete(f"/variants/{uuid.uuid4()}")

    assert resp.status_code == 404
