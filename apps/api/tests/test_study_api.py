from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from genomeai_api.exceptions import DuplicateStudyError
from genomeai_api.routes.studies import _get_service, router
from genomeai_api.schemas.study import StudyCreate, StudyResponse
from genomeai_api.services.study import StudyService


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock(spec=StudyService)


@pytest.fixture
def test_app(mock_service: AsyncMock) -> FastAPI:
    app = FastAPI()
    app.include_router(router)

    @app.exception_handler(DuplicateStudyError)
    async def _handler(
        request: Request, exc: DuplicateStudyError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)},
        )

    async def override() -> StudyService:
        return mock_service

    app.dependency_overrides[_get_service] = override
    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


@pytest.fixture
def sample_study_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def sample_response(sample_study_id: uuid.UUID) -> dict[str, object]:
    now = datetime.now(UTC).isoformat()
    return {
        "id": str(sample_study_id),
        "study_id": "STU-001",
        "study_name": "Cancer genome atlas study",
        "study_type": "cohort",
        "title": "The Cancer Genome Atlas",
        "description": "Comprehensive genomic analysis",
        "organism": "Homo sapiens",
        "institution": "TCGA Consortium",
        "principal_investigator": "Dr. Collins",
        "publication": "Nature 2023",
        "doi": "10.1038/example",
        "start_date": None,
        "end_date": None,
        "status": "completed",
        "genome_id": None,
        "dataset_id": None,
        "created_at": now,
        "updated_at": now,
    }


def test_create_study_201(
    client: TestClient,
    mock_service: AsyncMock,
    sample_response: dict[str, object],
) -> None:
    mock_service.create.return_value = StudyResponse(**sample_response)

    payload = {
        "study_id": "STU-001",
        "study_name": "Cancer genome atlas study",
    }
    resp = client.post("/studies/", json=payload)

    assert resp.status_code == 201
    assert resp.json()["study_id"] == "STU-001"
    mock_service.create.assert_awaited_once()
    call_arg = mock_service.create.call_args[0][0]
    assert isinstance(call_arg, StudyCreate)


def test_create_study_422_missing_fields(client: TestClient) -> None:
    resp = client.post("/studies/", json={})
    assert resp.status_code == 422


def test_create_study_422_study_id_too_long(
    client: TestClient,
) -> None:
    resp = client.post(
        "/studies/",
        json={
            "study_id": "S" * 101,
            "study_name": "Cancer study",
        },
    )
    assert resp.status_code == 422


def test_create_study_422_study_name_too_long(
    client: TestClient,
) -> None:
    resp = client.post(
        "/studies/",
        json={
            "study_id": "STU-001",
            "study_name": "S" * 256,
        },
    )
    assert resp.status_code == 422


def test_create_study_409_duplicate(
    client: TestClient,
    mock_service: AsyncMock,
) -> None:
    mock_service.create.side_effect = DuplicateStudyError()

    payload = {
        "study_id": "STU-001",
        "study_name": "Cancer genome atlas study",
    }
    resp = client.post("/studies/", json=payload)

    assert resp.status_code == 409
    assert resp.json()["detail"] == "Study already exists"


def test_list_studies(
    client: TestClient,
    mock_service: AsyncMock,
    sample_response: dict[str, object],
) -> None:
    mock_service.list.return_value = [StudyResponse(**sample_response)]

    resp = client.get("/studies/")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["study_id"] == "STU-001"


def test_list_studies_empty(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.list.return_value = []

    resp = client.get("/studies/")

    assert resp.status_code == 200
    assert resp.json() == []


def test_get_study_200(
    client: TestClient,
    mock_service: AsyncMock,
    sample_study_id: uuid.UUID,
    sample_response: dict[str, object],
) -> None:
    mock_service.get_by_id.return_value = StudyResponse(**sample_response)

    resp = client.get(f"/studies/{sample_study_id}")

    assert resp.status_code == 200
    assert resp.json()["id"] == str(sample_study_id)


def test_get_study_404(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.get_by_id.return_value = None

    resp = client.get(f"/studies/{uuid.uuid4()}")

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Study not found"


def test_get_study_422_invalid_uuid(client: TestClient) -> None:
    resp = client.get("/studies/not-a-uuid")
    assert resp.status_code == 422


def test_update_study_200(
    client: TestClient,
    mock_service: AsyncMock,
    sample_study_id: uuid.UUID,
    sample_response: dict[str, object],
) -> None:
    mock_service.update.return_value = StudyResponse(**sample_response)

    resp = client.patch(
        f"/studies/{sample_study_id}", json={"study_name": "Updated study"}
    )

    assert resp.status_code == 200
    assert resp.json()["id"] == str(sample_study_id)


def test_update_study_404(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.update.return_value = None

    resp = client.patch(f"/studies/{uuid.uuid4()}", json={"study_name": "Updated study"})

    assert resp.status_code == 404


def test_update_study_422_invalid_body(
    client: TestClient,
    sample_study_id: uuid.UUID,
) -> None:
    resp = client.patch(
        f"/studies/{sample_study_id}", json={"study_id": 123}
    )
    assert resp.status_code == 422


def test_update_study_422_null_study_id(
    client: TestClient,
    sample_study_id: uuid.UUID,
) -> None:
    resp = client.patch(
        f"/studies/{sample_study_id}",
        json={"study_id": None},
    )
    assert resp.status_code == 422


def test_update_study_422_null_study_name(
    client: TestClient,
    sample_study_id: uuid.UUID,
) -> None:
    resp = client.patch(
        f"/studies/{sample_study_id}",
        json={"study_name": None},
    )
    assert resp.status_code == 422


def test_update_study_422_study_id_too_long(
    client: TestClient,
    sample_study_id: uuid.UUID,
) -> None:
    resp = client.patch(
        f"/studies/{sample_study_id}",
        json={"study_id": "S" * 101},
    )
    assert resp.status_code == 422


def test_update_study_409_duplicate(
    client: TestClient,
    mock_service: AsyncMock,
    sample_study_id: uuid.UUID,
) -> None:
    mock_service.update.side_effect = DuplicateStudyError()

    resp = client.patch(
        f"/studies/{sample_study_id}",
        json={"study_id": "STU-002"},
    )

    assert resp.status_code == 409
    assert resp.json()["detail"] == "Study already exists"


def test_delete_study_204(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.delete.return_value = True

    resp = client.delete(f"/studies/{uuid.uuid4()}")

    assert resp.status_code == 204


def test_delete_study_404(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.delete.return_value = False

    resp = client.delete(f"/studies/{uuid.uuid4()}")

    assert resp.status_code == 404
