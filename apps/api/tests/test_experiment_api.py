from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from genomeai_api.exceptions import DuplicateExperimentError
from genomeai_api.routes.experiments import _get_service, router
from genomeai_api.schemas.experiment import ExperimentCreate, ExperimentResponse
from genomeai_api.services.experiment import ExperimentService


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock(spec=ExperimentService)


@pytest.fixture
def test_app(mock_service: AsyncMock) -> FastAPI:
    app = FastAPI()
    app.include_router(router)

    @app.exception_handler(DuplicateExperimentError)
    async def _handler(
        request: Request, exc: DuplicateExperimentError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)},
        )

    async def override() -> ExperimentService:
        return mock_service

    app.dependency_overrides[_get_service] = override
    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


@pytest.fixture
def sample_experiment_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def sample_response(sample_experiment_id: uuid.UUID) -> dict[str, object]:
    now = datetime.now(UTC).isoformat()
    return {
        "id": str(sample_experiment_id),
        "experiment_id": "EXP-001",
        "experiment_name": "RNA-seq of tumor samples",
        "experiment_type": "RNA-seq",
        "platform": "Illumina NovaSeq",
        "technology": "paired-end",
        "status": "completed",
        "organism": "Homo sapiens",
        "laboratory": "Genomics Lab",
        "researcher": "Dr. Smith",
        "sample_id": None,
        "genome_id": None,
        "description": "RNA-seq experiment",
        "created_at": now,
        "updated_at": now,
    }


def test_create_experiment_201(
    client: TestClient,
    mock_service: AsyncMock,
    sample_response: dict[str, object],
) -> None:
    mock_service.create.return_value = ExperimentResponse(**sample_response)

    payload = {
        "experiment_id": "EXP-001",
        "experiment_name": "RNA-seq of tumor samples",
    }
    resp = client.post("/experiments/", json=payload)

    assert resp.status_code == 201
    assert resp.json()["experiment_id"] == "EXP-001"
    mock_service.create.assert_awaited_once()
    call_arg = mock_service.create.call_args[0][0]
    assert isinstance(call_arg, ExperimentCreate)


def test_create_experiment_422_missing_fields(client: TestClient) -> None:
    resp = client.post("/experiments/", json={})
    assert resp.status_code == 422


def test_create_experiment_422_experiment_id_too_long(
    client: TestClient,
) -> None:
    resp = client.post(
        "/experiments/",
        json={
            "experiment_id": "E" * 101,
            "experiment_name": "RNA-seq",
        },
    )
    assert resp.status_code == 422


def test_create_experiment_422_experiment_name_too_long(
    client: TestClient,
) -> None:
    resp = client.post(
        "/experiments/",
        json={
            "experiment_id": "EXP-001",
            "experiment_name": "E" * 256,
        },
    )
    assert resp.status_code == 422


def test_create_experiment_409_duplicate(
    client: TestClient,
    mock_service: AsyncMock,
) -> None:
    mock_service.create.side_effect = DuplicateExperimentError()

    payload = {
        "experiment_id": "EXP-001",
        "experiment_name": "RNA-seq of tumor samples",
    }
    resp = client.post("/experiments/", json=payload)

    assert resp.status_code == 409
    assert resp.json()["detail"] == "Experiment already exists"


def test_list_experiments(
    client: TestClient,
    mock_service: AsyncMock,
    sample_response: dict[str, object],
) -> None:
    mock_service.list.return_value = [ExperimentResponse(**sample_response)]

    resp = client.get("/experiments/")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["experiment_id"] == "EXP-001"


def test_list_experiments_empty(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.list.return_value = []

    resp = client.get("/experiments/")

    assert resp.status_code == 200
    assert resp.json() == []


def test_get_experiment_200(
    client: TestClient,
    mock_service: AsyncMock,
    sample_experiment_id: uuid.UUID,
    sample_response: dict[str, object],
) -> None:
    mock_service.get_by_id.return_value = ExperimentResponse(**sample_response)

    resp = client.get(f"/experiments/{sample_experiment_id}")

    assert resp.status_code == 200
    assert resp.json()["id"] == str(sample_experiment_id)


def test_get_experiment_404(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.get_by_id.return_value = None

    resp = client.get(f"/experiments/{uuid.uuid4()}")

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Experiment not found"


def test_get_experiment_422_invalid_uuid(client: TestClient) -> None:
    resp = client.get("/experiments/not-a-uuid")
    assert resp.status_code == 422


def test_update_experiment_200(
    client: TestClient,
    mock_service: AsyncMock,
    sample_experiment_id: uuid.UUID,
    sample_response: dict[str, object],
) -> None:
    mock_service.update.return_value = ExperimentResponse(**sample_response)

    resp = client.patch(
        f"/experiments/{sample_experiment_id}", json={"experiment_name": "WGS"}
    )

    assert resp.status_code == 200
    assert resp.json()["id"] == str(sample_experiment_id)


def test_update_experiment_404(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.update.return_value = None

    resp = client.patch(
        f"/experiments/{uuid.uuid4()}", json={"experiment_name": "WGS"}
    )

    assert resp.status_code == 404


def test_update_experiment_422_invalid_body(
    client: TestClient,
    sample_experiment_id: uuid.UUID,
) -> None:
    resp = client.patch(
        f"/experiments/{sample_experiment_id}", json={"experiment_id": 123}
    )
    assert resp.status_code == 422


def test_update_experiment_422_null_experiment_id(
    client: TestClient,
    sample_experiment_id: uuid.UUID,
) -> None:
    resp = client.patch(
        f"/experiments/{sample_experiment_id}",
        json={"experiment_id": None},
    )
    assert resp.status_code == 422


def test_update_experiment_422_null_experiment_name(
    client: TestClient,
    sample_experiment_id: uuid.UUID,
) -> None:
    resp = client.patch(
        f"/experiments/{sample_experiment_id}",
        json={"experiment_name": None},
    )
    assert resp.status_code == 422


def test_update_experiment_422_experiment_id_too_long(
    client: TestClient,
    sample_experiment_id: uuid.UUID,
) -> None:
    resp = client.patch(
        f"/experiments/{sample_experiment_id}",
        json={"experiment_id": "E" * 101},
    )
    assert resp.status_code == 422


def test_update_experiment_409_duplicate(
    client: TestClient,
    mock_service: AsyncMock,
    sample_experiment_id: uuid.UUID,
) -> None:
    mock_service.update.side_effect = DuplicateExperimentError()

    resp = client.patch(
        f"/experiments/{sample_experiment_id}",
        json={"experiment_id": "EXP-002"},
    )

    assert resp.status_code == 409
    assert resp.json()["detail"] == "Experiment already exists"


def test_delete_experiment_204(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.delete.return_value = True

    resp = client.delete(f"/experiments/{uuid.uuid4()}")

    assert resp.status_code == 204


def test_delete_experiment_404(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.delete.return_value = False

    resp = client.delete(f"/experiments/{uuid.uuid4()}")

    assert resp.status_code == 404
