from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from genomeai_api.exceptions import DuplicateSampleError
from genomeai_api.routes.samples import _get_service, router
from genomeai_api.schemas.sample import SampleCreate, SampleResponse
from genomeai_api.services.sample import SampleService


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock(spec=SampleService)


@pytest.fixture
def test_app(mock_service: AsyncMock) -> FastAPI:
    app = FastAPI()
    app.include_router(router)

    @app.exception_handler(DuplicateSampleError)
    async def _handler(request: Request, exc: DuplicateSampleError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)},
        )

    async def override() -> SampleService:
        return mock_service

    app.dependency_overrides[_get_service] = override
    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


@pytest.fixture
def sample_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def sample_response(sample_id: uuid.UUID) -> dict[str, object]:
    now = datetime.now(UTC).isoformat()
    return {
        "id": str(sample_id),
        "sample_id": "SMP001",
        "sample_name": "Sample 1",
        "organism": "Homo sapiens",
        "tissue": "Brain",
        "cell_type": None,
        "disease": None,
        "phenotype": None,
        "sex": None,
        "age": None,
        "genome_id": None,
        "description": None,
        "created_at": now,
        "updated_at": now,
    }


def test_create_sample_201(
    client: TestClient,
    mock_service: AsyncMock,
    sample_response: dict[str, object],
) -> None:
    mock_service.create.return_value = SampleResponse(**sample_response)

    payload = {
        "sample_id": "SMP001",
        "sample_name": "Sample 1",
        "organism": "Homo sapiens",
        "tissue": "Brain",
    }
    resp = client.post("/samples/", json=payload)

    assert resp.status_code == 201
    assert resp.json()["sample_id"] == "SMP001"
    mock_service.create.assert_awaited_once()
    call_arg = mock_service.create.call_args[0][0]
    assert isinstance(call_arg, SampleCreate)


def test_create_sample_422_missing_fields(client: TestClient) -> None:
    resp = client.post("/samples/", json={})
    assert resp.status_code == 422


def test_create_sample_422_sample_id_too_long(client: TestClient) -> None:
    resp = client.post(
        "/samples/",
        json={
            "sample_id": "S" * 101,
            "sample_name": "Sample 1",
            "organism": "Homo sapiens",
        },
    )
    assert resp.status_code == 422


def test_create_sample_422_sample_name_too_long(client: TestClient) -> None:
    resp = client.post(
        "/samples/",
        json={
            "sample_id": "SMP001",
            "sample_name": "N" * 256,
            "organism": "Homo sapiens",
        },
    )
    assert resp.status_code == 422


def test_create_sample_422_organism_too_long(client: TestClient) -> None:
    resp = client.post(
        "/samples/",
        json={
            "sample_id": "SMP001",
            "sample_name": "Sample 1",
            "organism": "O" * 256,
        },
    )
    assert resp.status_code == 422


def test_create_sample_409_duplicate(
    client: TestClient,
    mock_service: AsyncMock,
) -> None:
    mock_service.create.side_effect = DuplicateSampleError()

    payload = {
        "sample_id": "SMP001",
        "sample_name": "Sample 1",
        "organism": "Homo sapiens",
    }
    resp = client.post("/samples/", json=payload)

    assert resp.status_code == 409
    assert resp.json()["detail"] == "Sample already exists"


def test_list_samples(
    client: TestClient,
    mock_service: AsyncMock,
    sample_response: dict[str, object],
) -> None:
    mock_service.list.return_value = [SampleResponse(**sample_response)]

    resp = client.get("/samples/")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["sample_id"] == "SMP001"


def test_list_samples_empty(client: TestClient, mock_service: AsyncMock) -> None:
    mock_service.list.return_value = []

    resp = client.get("/samples/")

    assert resp.status_code == 200
    assert resp.json() == []


def test_get_sample_200(
    client: TestClient,
    mock_service: AsyncMock,
    sample_id: uuid.UUID,
    sample_response: dict[str, object],
) -> None:
    mock_service.get_by_id.return_value = SampleResponse(**sample_response)

    resp = client.get(f"/samples/{sample_id}")

    assert resp.status_code == 200
    assert resp.json()["id"] == str(sample_id)


def test_get_sample_404(client: TestClient, mock_service: AsyncMock) -> None:
    mock_service.get_by_id.return_value = None

    resp = client.get(f"/samples/{uuid.uuid4()}")

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Sample not found"


def test_get_sample_422_invalid_uuid(client: TestClient) -> None:
    resp = client.get("/samples/not-a-uuid")
    assert resp.status_code == 422


def test_update_sample_200(
    client: TestClient,
    mock_service: AsyncMock,
    sample_id: uuid.UUID,
    sample_response: dict[str, object],
) -> None:
    mock_service.update.return_value = SampleResponse(**sample_response)

    resp = client.patch(f"/samples/{sample_id}", json={"organism": "Mus musculus"})

    assert resp.status_code == 200
    assert resp.json()["id"] == str(sample_id)


def test_update_sample_404(client: TestClient, mock_service: AsyncMock) -> None:
    mock_service.update.return_value = None

    resp = client.patch(f"/samples/{uuid.uuid4()}", json={"organism": "Mus musculus"})

    assert resp.status_code == 404


def test_update_sample_422_invalid_body(client: TestClient, sample_id: uuid.UUID) -> None:
    resp = client.patch(f"/samples/{sample_id}", json={"sample_id": 123})
    assert resp.status_code == 422


def test_update_sample_422_sample_id_too_long(
    client: TestClient,
    sample_id: uuid.UUID,
) -> None:
    resp = client.patch(f"/samples/{sample_id}", json={"sample_id": "S" * 101})
    assert resp.status_code == 422


def test_update_sample_409_duplicate(
    client: TestClient,
    mock_service: AsyncMock,
    sample_id: uuid.UUID,
) -> None:
    mock_service.update.side_effect = DuplicateSampleError()

    resp = client.patch(
        f"/samples/{sample_id}",
        json={"sample_id": "SMP002"},
    )

    assert resp.status_code == 409
    assert resp.json()["detail"] == "Sample already exists"


def test_delete_sample_204(client: TestClient, mock_service: AsyncMock) -> None:
    mock_service.delete.return_value = True

    resp = client.delete(f"/samples/{uuid.uuid4()}")

    assert resp.status_code == 204


def test_delete_sample_404(client: TestClient, mock_service: AsyncMock) -> None:
    mock_service.delete.return_value = False

    resp = client.delete(f"/samples/{uuid.uuid4()}")

    assert resp.status_code == 404
