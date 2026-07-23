from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from genomeai_api.exceptions import DuplicateProjectError
from genomeai_api.routes.projects import _get_service, router
from genomeai_api.schemas.project import ProjectCreate, ProjectResponse
from genomeai_api.services.project import ProjectService


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock(spec=ProjectService)


@pytest.fixture
def test_app(mock_service: AsyncMock) -> FastAPI:
    app = FastAPI()
    app.include_router(router)

    @app.exception_handler(DuplicateProjectError)
    async def _handler(
        request: Request, exc: DuplicateProjectError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)},
        )

    async def override() -> ProjectService:
        return mock_service

    app.dependency_overrides[_get_service] = override
    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


@pytest.fixture
def sample_project_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def sample_response(sample_project_id: uuid.UUID) -> dict[str, object]:
    now = datetime.now(UTC).isoformat()
    return {
        "id": str(sample_project_id),
        "project_id": "PRJ-001",
        "project_name": "Genome sequencing project",
        "title": "1000 Genomes Project",
        "description": "Large-scale genome sequencing",
        "organization": "Wellcome Trust",
        "owner": "Dr. Stevens",
        "principal_investigator": "Dr. Collins",
        "status": "active",
        "start_date": None,
        "end_date": None,
        "genome_id": None,
        "study_id": None,
        "created_at": now,
        "updated_at": now,
    }


def test_create_project_201(
    client: TestClient,
    mock_service: AsyncMock,
    sample_response: dict[str, object],
) -> None:
    mock_service.create.return_value = ProjectResponse(**sample_response)

    payload = {
        "project_id": "PRJ-001",
        "project_name": "Genome sequencing project",
    }
    resp = client.post("/projects/", json=payload)

    assert resp.status_code == 201
    assert resp.json()["project_id"] == "PRJ-001"
    mock_service.create.assert_awaited_once()
    call_arg = mock_service.create.call_args[0][0]
    assert isinstance(call_arg, ProjectCreate)


def test_create_project_422_missing_fields(client: TestClient) -> None:
    resp = client.post("/projects/", json={})
    assert resp.status_code == 422


def test_create_project_422_project_id_too_long(
    client: TestClient,
) -> None:
    resp = client.post(
        "/projects/",
        json={
            "project_id": "P" * 101,
            "project_name": "Genome project",
        },
    )
    assert resp.status_code == 422


def test_create_project_422_project_name_too_long(
    client: TestClient,
) -> None:
    resp = client.post(
        "/projects/",
        json={
            "project_id": "PRJ-001",
            "project_name": "P" * 256,
        },
    )
    assert resp.status_code == 422


def test_create_project_409_duplicate(
    client: TestClient,
    mock_service: AsyncMock,
) -> None:
    mock_service.create.side_effect = DuplicateProjectError()

    payload = {
        "project_id": "PRJ-001",
        "project_name": "Genome sequencing project",
    }
    resp = client.post("/projects/", json=payload)

    assert resp.status_code == 409
    assert resp.json()["detail"] == "Project already exists"


def test_list_projects(
    client: TestClient,
    mock_service: AsyncMock,
    sample_response: dict[str, object],
) -> None:
    mock_service.list.return_value = [ProjectResponse(**sample_response)]

    resp = client.get("/projects/")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["project_id"] == "PRJ-001"


def test_list_projects_empty(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.list.return_value = []

    resp = client.get("/projects/")

    assert resp.status_code == 200
    assert resp.json() == []


def test_get_project_200(
    client: TestClient,
    mock_service: AsyncMock,
    sample_project_id: uuid.UUID,
    sample_response: dict[str, object],
) -> None:
    mock_service.get_by_id.return_value = ProjectResponse(**sample_response)

    resp = client.get(f"/projects/{sample_project_id}")

    assert resp.status_code == 200
    assert resp.json()["id"] == str(sample_project_id)


def test_get_project_404(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.get_by_id.return_value = None

    resp = client.get(f"/projects/{uuid.uuid4()}")

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Project not found"


def test_get_project_422_invalid_uuid(client: TestClient) -> None:
    resp = client.get("/projects/not-a-uuid")
    assert resp.status_code == 422


def test_update_project_200(
    client: TestClient,
    mock_service: AsyncMock,
    sample_project_id: uuid.UUID,
    sample_response: dict[str, object],
) -> None:
    mock_service.update.return_value = ProjectResponse(**sample_response)

    resp = client.patch(
        f"/projects/{sample_project_id}", json={"project_name": "Updated project"}
    )

    assert resp.status_code == 200
    assert resp.json()["id"] == str(sample_project_id)


def test_update_project_404(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.update.return_value = None

    resp = client.patch(f"/projects/{uuid.uuid4()}", json={"project_name": "Updated project"})

    assert resp.status_code == 404


def test_update_project_422_invalid_body(
    client: TestClient,
    sample_project_id: uuid.UUID,
) -> None:
    resp = client.patch(
        f"/projects/{sample_project_id}", json={"project_id": 123}
    )
    assert resp.status_code == 422


def test_update_project_422_null_project_id(
    client: TestClient,
    sample_project_id: uuid.UUID,
) -> None:
    resp = client.patch(
        f"/projects/{sample_project_id}",
        json={"project_id": None},
    )
    assert resp.status_code == 422


def test_update_project_422_null_project_name(
    client: TestClient,
    sample_project_id: uuid.UUID,
) -> None:
    resp = client.patch(
        f"/projects/{sample_project_id}",
        json={"project_name": None},
    )
    assert resp.status_code == 422


def test_update_project_422_project_id_too_long(
    client: TestClient,
    sample_project_id: uuid.UUID,
) -> None:
    resp = client.patch(
        f"/projects/{sample_project_id}",
        json={"project_id": "P" * 101},
    )
    assert resp.status_code == 422


def test_update_project_409_duplicate(
    client: TestClient,
    mock_service: AsyncMock,
    sample_project_id: uuid.UUID,
) -> None:
    mock_service.update.side_effect = DuplicateProjectError()

    resp = client.patch(
        f"/projects/{sample_project_id}",
        json={"project_id": "PRJ-002"},
    )

    assert resp.status_code == 409
    assert resp.json()["detail"] == "Project already exists"


def test_delete_project_204(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.delete.return_value = True

    resp = client.delete(f"/projects/{uuid.uuid4()}")

    assert resp.status_code == 204


def test_delete_project_404(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.delete.return_value = False

    resp = client.delete(f"/projects/{uuid.uuid4()}")

    assert resp.status_code == 404
