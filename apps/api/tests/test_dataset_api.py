from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from genomeai_api.exceptions import DuplicateDatasetError
from genomeai_api.routes.datasets import _get_service, router
from genomeai_api.schemas.dataset import DatasetCreate, DatasetResponse
from genomeai_api.services.dataset import DatasetService


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock(spec=DatasetService)


@pytest.fixture
def test_app(mock_service: AsyncMock) -> FastAPI:
    app = FastAPI()
    app.include_router(router)

    @app.exception_handler(DuplicateDatasetError)
    async def _handler(
        request: Request, exc: DuplicateDatasetError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)},
        )

    async def override() -> DatasetService:
        return mock_service

    app.dependency_overrides[_get_service] = override
    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


@pytest.fixture
def sample_dataset_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def sample_response(sample_dataset_id: uuid.UUID) -> dict[str, object]:
    now = datetime.now(UTC).isoformat()
    return {
        "id": str(sample_dataset_id),
        "dataset_id": "DS-001",
        "dataset_name": "RNA-seq expression data",
        "dataset_type": "expression",
        "source": "TCGA",
        "organism": "Homo sapiens",
        "version": "v1.0",
        "description": "Expression data",
        "sample_count": 100,
        "file_count": 5,
        "size_bytes": 1073741824,
        "is_public": True,
        "genome_id": None,
        "experiment_id": None,
        "created_at": now,
        "updated_at": now,
    }


def test_create_dataset_201(
    client: TestClient,
    mock_service: AsyncMock,
    sample_response: dict[str, object],
) -> None:
    mock_service.create.return_value = DatasetResponse(**sample_response)

    payload = {
        "dataset_id": "DS-001",
        "dataset_name": "RNA-seq expression data",
    }
    resp = client.post("/datasets/", json=payload)

    assert resp.status_code == 201
    assert resp.json()["dataset_id"] == "DS-001"
    mock_service.create.assert_awaited_once()
    call_arg = mock_service.create.call_args[0][0]
    assert isinstance(call_arg, DatasetCreate)


def test_create_dataset_422_missing_fields(client: TestClient) -> None:
    resp = client.post("/datasets/", json={})
    assert resp.status_code == 422


def test_create_dataset_422_dataset_id_too_long(
    client: TestClient,
) -> None:
    resp = client.post(
        "/datasets/",
        json={
            "dataset_id": "D" * 101,
            "dataset_name": "RNA-seq data",
        },
    )
    assert resp.status_code == 422


def test_create_dataset_422_dataset_name_too_long(
    client: TestClient,
) -> None:
    resp = client.post(
        "/datasets/",
        json={
            "dataset_id": "DS-001",
            "dataset_name": "D" * 256,
        },
    )
    assert resp.status_code == 422


def test_create_dataset_409_duplicate(
    client: TestClient,
    mock_service: AsyncMock,
) -> None:
    mock_service.create.side_effect = DuplicateDatasetError()

    payload = {
        "dataset_id": "DS-001",
        "dataset_name": "RNA-seq expression data",
    }
    resp = client.post("/datasets/", json=payload)

    assert resp.status_code == 409
    assert resp.json()["detail"] == "Dataset already exists"


def test_list_datasets(
    client: TestClient,
    mock_service: AsyncMock,
    sample_response: dict[str, object],
) -> None:
    mock_service.list.return_value = [DatasetResponse(**sample_response)]

    resp = client.get("/datasets/")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["dataset_id"] == "DS-001"


def test_list_datasets_empty(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.list.return_value = []

    resp = client.get("/datasets/")

    assert resp.status_code == 200
    assert resp.json() == []


def test_get_dataset_200(
    client: TestClient,
    mock_service: AsyncMock,
    sample_dataset_id: uuid.UUID,
    sample_response: dict[str, object],
) -> None:
    mock_service.get_by_id.return_value = DatasetResponse(**sample_response)

    resp = client.get(f"/datasets/{sample_dataset_id}")

    assert resp.status_code == 200
    assert resp.json()["id"] == str(sample_dataset_id)


def test_get_dataset_404(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.get_by_id.return_value = None

    resp = client.get(f"/datasets/{uuid.uuid4()}")

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Dataset not found"


def test_get_dataset_422_invalid_uuid(client: TestClient) -> None:
    resp = client.get("/datasets/not-a-uuid")
    assert resp.status_code == 422


def test_update_dataset_200(
    client: TestClient,
    mock_service: AsyncMock,
    sample_dataset_id: uuid.UUID,
    sample_response: dict[str, object],
) -> None:
    mock_service.update.return_value = DatasetResponse(**sample_response)

    resp = client.patch(
        f"/datasets/{sample_dataset_id}", json={"dataset_name": "WGS data"}
    )

    assert resp.status_code == 200
    assert resp.json()["id"] == str(sample_dataset_id)


def test_update_dataset_404(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.update.return_value = None

    resp = client.patch(f"/datasets/{uuid.uuid4()}", json={"dataset_name": "WGS data"})

    assert resp.status_code == 404


def test_update_dataset_422_invalid_body(
    client: TestClient,
    sample_dataset_id: uuid.UUID,
) -> None:
    resp = client.patch(
        f"/datasets/{sample_dataset_id}", json={"dataset_id": 123}
    )
    assert resp.status_code == 422


def test_update_dataset_422_null_dataset_id(
    client: TestClient,
    sample_dataset_id: uuid.UUID,
) -> None:
    resp = client.patch(
        f"/datasets/{sample_dataset_id}",
        json={"dataset_id": None},
    )
    assert resp.status_code == 422


def test_update_dataset_422_null_dataset_name(
    client: TestClient,
    sample_dataset_id: uuid.UUID,
) -> None:
    resp = client.patch(
        f"/datasets/{sample_dataset_id}",
        json={"dataset_name": None},
    )
    assert resp.status_code == 422


def test_update_dataset_422_dataset_id_too_long(
    client: TestClient,
    sample_dataset_id: uuid.UUID,
) -> None:
    resp = client.patch(
        f"/datasets/{sample_dataset_id}",
        json={"dataset_id": "D" * 101},
    )
    assert resp.status_code == 422


def test_update_dataset_409_duplicate(
    client: TestClient,
    mock_service: AsyncMock,
    sample_dataset_id: uuid.UUID,
) -> None:
    mock_service.update.side_effect = DuplicateDatasetError()

    resp = client.patch(
        f"/datasets/{sample_dataset_id}",
        json={"dataset_id": "DS-002"},
    )

    assert resp.status_code == 409
    assert resp.json()["detail"] == "Dataset already exists"


def test_delete_dataset_204(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.delete.return_value = True

    resp = client.delete(f"/datasets/{uuid.uuid4()}")

    assert resp.status_code == 204


def test_delete_dataset_404(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.delete.return_value = False

    resp = client.delete(f"/datasets/{uuid.uuid4()}")

    assert resp.status_code == 404
