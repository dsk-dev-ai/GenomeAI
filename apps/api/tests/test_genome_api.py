from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from genomeai_api.exceptions import DuplicateGenomeAccessionError
from genomeai_api.routes.genomes import _get_service, router
from genomeai_api.schemas.genome import GenomeCreate, GenomeResponse
from genomeai_api.services.genome import GenomeService


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock(spec=GenomeService)


@pytest.fixture
def test_app(mock_service: AsyncMock) -> FastAPI:
    app = FastAPI()
    app.include_router(router)

    @app.exception_handler(DuplicateGenomeAccessionError)
    async def _handler(request: Request, exc: DuplicateGenomeAccessionError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)},
        )

    async def override() -> GenomeService:
        return mock_service

    app.dependency_overrides[_get_service] = override
    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


@pytest.fixture
def sample_genome_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def sample_response(sample_genome_id: uuid.UUID) -> dict[str, object]:
    now = datetime.now(UTC).isoformat()
    return {
        "id": str(sample_genome_id),
        "accession": "GCF_000001405.40",
        "organism": "Homo sapiens",
        "assembly": "GRCh38.p14",
        "source": "NCBI",
        "description": "Human reference genome",
        "created_at": now,
        "updated_at": now,
    }


def test_create_genome_201(
    client: TestClient,
    mock_service: AsyncMock,
    sample_response: dict[str, object],
) -> None:
    mock_service.create.return_value = GenomeResponse(**sample_response)

    payload = {
        "accession": "GCF_000001405.40",
        "organism": "Homo sapiens",
        "assembly": "GRCh38.p14",
        "source": "NCBI",
        "description": "Human reference genome",
    }
    resp = client.post("/genomes/", json=payload)

    assert resp.status_code == 201
    assert resp.json()["accession"] == "GCF_000001405.40"
    mock_service.create.assert_awaited_once()
    call_arg = mock_service.create.call_args[0][0]
    assert isinstance(call_arg, GenomeCreate)


def test_create_genome_422_missing_fields(client: TestClient) -> None:
    resp = client.post("/genomes/", json={})
    assert resp.status_code == 422


def test_create_genome_422_accession_too_long(client: TestClient) -> None:
    resp = client.post(
        "/genomes/",
        json={
            "accession": "A" * 51,
            "organism": "Homo sapiens",
        },
    )
    assert resp.status_code == 422


def test_create_genome_422_organism_too_long(client: TestClient) -> None:
    resp = client.post(
        "/genomes/",
        json={
            "accession": "GCF_000001405.40",
            "organism": "O" * 256,
        },
    )
    assert resp.status_code == 422


def test_create_genome_409_duplicate(
    client: TestClient,
    mock_service: AsyncMock,
) -> None:
    mock_service.create.side_effect = DuplicateGenomeAccessionError()

    payload = {
        "accession": "GCF_000001405.40",
        "organism": "Homo sapiens",
    }
    resp = client.post("/genomes/", json=payload)

    assert resp.status_code == 409
    assert resp.json()["detail"] == "Genome accession already exists"


def test_list_genomes(
    client: TestClient,
    mock_service: AsyncMock,
    sample_response: dict[str, object],
) -> None:
    mock_service.list.return_value = [GenomeResponse(**sample_response)]

    resp = client.get("/genomes/")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["accession"] == "GCF_000001405.40"


def test_list_genomes_empty(client: TestClient, mock_service: AsyncMock) -> None:
    mock_service.list.return_value = []

    resp = client.get("/genomes/")

    assert resp.status_code == 200
    assert resp.json() == []


def test_get_genome_200(
    client: TestClient,
    mock_service: AsyncMock,
    sample_genome_id: uuid.UUID,
    sample_response: dict[str, object],
) -> None:
    mock_service.get_by_id.return_value = GenomeResponse(**sample_response)

    resp = client.get(f"/genomes/{sample_genome_id}")

    assert resp.status_code == 200
    assert resp.json()["id"] == str(sample_genome_id)


def test_get_genome_404(client: TestClient, mock_service: AsyncMock) -> None:
    mock_service.get_by_id.return_value = None

    resp = client.get(f"/genomes/{uuid.uuid4()}")

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Genome not found"


def test_get_genome_422_invalid_uuid(client: TestClient) -> None:
    resp = client.get("/genomes/not-a-uuid")
    assert resp.status_code == 422


def test_update_genome_200(
    client: TestClient,
    mock_service: AsyncMock,
    sample_genome_id: uuid.UUID,
    sample_response: dict[str, object],
) -> None:
    mock_service.update.return_value = GenomeResponse(**sample_response)

    resp = client.patch(f"/genomes/{sample_genome_id}", json={"organism": "Mus musculus"})

    assert resp.status_code == 200
    assert resp.json()["id"] == str(sample_genome_id)


def test_update_genome_404(client: TestClient, mock_service: AsyncMock) -> None:
    mock_service.update.return_value = None

    resp = client.patch(f"/genomes/{uuid.uuid4()}", json={"organism": "Mus musculus"})

    assert resp.status_code == 404


def test_update_genome_422_invalid_body(client: TestClient, sample_genome_id: uuid.UUID) -> None:
    resp = client.patch(f"/genomes/{sample_genome_id}", json={"accession": 123})
    assert resp.status_code == 422


def test_update_genome_422_accession_too_long(
    client: TestClient,
    sample_genome_id: uuid.UUID,
) -> None:
    resp = client.patch(f"/genomes/{sample_genome_id}", json={"accession": "A" * 51})
    assert resp.status_code == 422


def test_update_genome_409_duplicate(
    client: TestClient,
    mock_service: AsyncMock,
    sample_genome_id: uuid.UUID,
) -> None:
    mock_service.update.side_effect = DuplicateGenomeAccessionError()

    resp = client.patch(
        f"/genomes/{sample_genome_id}",
        json={"accession": "GCF_000002409.10"},
    )

    assert resp.status_code == 409
    assert resp.json()["detail"] == "Genome accession already exists"


def test_delete_genome_204(client: TestClient, mock_service: AsyncMock) -> None:
    mock_service.delete.return_value = True

    resp = client.delete(f"/genomes/{uuid.uuid4()}")

    assert resp.status_code == 204


def test_delete_genome_404(client: TestClient, mock_service: AsyncMock) -> None:
    mock_service.delete.return_value = False

    resp = client.delete(f"/genomes/{uuid.uuid4()}")

    assert resp.status_code == 404
