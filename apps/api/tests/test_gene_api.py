from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from genomeai_api.exceptions import DuplicateGeneError
from genomeai_api.routes.genes import _get_service, router
from genomeai_api.schemas.gene import GeneCreate, GeneResponse
from genomeai_api.services.gene import GeneService


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock(spec=GeneService)


@pytest.fixture
def test_app(mock_service: AsyncMock) -> FastAPI:
    app = FastAPI()
    app.include_router(router)

    @app.exception_handler(DuplicateGeneError)
    async def _handler(request: Request, exc: DuplicateGeneError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)},
        )

    async def override() -> GeneService:
        return mock_service

    app.dependency_overrides[_get_service] = override
    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


@pytest.fixture
def sample_gene_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def sample_response(sample_gene_id: uuid.UUID) -> dict[str, object]:
    now = datetime.now(UTC).isoformat()
    return {
        "id": str(sample_gene_id),
        "gene_id": "ENSG00000139618",
        "gene_name": "TP53",
        "chromosome": "17",
        "strand": "-",
        "start_position": 7661779,
        "end_position": 7687538,
        "biotype": "protein_coding",
        "description": "Tumor protein p53",
        "genome_id": None,
        "created_at": now,
        "updated_at": now,
    }


def test_create_gene_201(
    client: TestClient,
    mock_service: AsyncMock,
    sample_response: dict[str, object],
) -> None:
    mock_service.create.return_value = GeneResponse(**sample_response)

    payload = {
        "gene_id": "ENSG00000139618",
        "gene_name": "TP53",
        "chromosome": "17",
    }
    resp = client.post("/genes/", json=payload)

    assert resp.status_code == 201
    assert resp.json()["gene_id"] == "ENSG00000139618"
    mock_service.create.assert_awaited_once()
    call_arg = mock_service.create.call_args[0][0]
    assert isinstance(call_arg, GeneCreate)


def test_create_gene_422_missing_fields(client: TestClient) -> None:
    resp = client.post("/genes/", json={})
    assert resp.status_code == 422


def test_create_gene_422_gene_id_too_long(client: TestClient) -> None:
    resp = client.post(
        "/genes/",
        json={
            "gene_id": "E" * 51,
            "gene_name": "TP53",
            "chromosome": "17",
        },
    )
    assert resp.status_code == 422


def test_create_gene_422_gene_name_too_long(client: TestClient) -> None:
    resp = client.post(
        "/genes/",
        json={
            "gene_id": "ENSG00000139618",
            "gene_name": "N" * 256,
            "chromosome": "17",
        },
    )
    assert resp.status_code == 422


def test_create_gene_422_chromosome_too_long(client: TestClient) -> None:
    resp = client.post(
        "/genes/",
        json={
            "gene_id": "ENSG00000139618",
            "gene_name": "TP53",
            "chromosome": "C" * 11,
        },
    )
    assert resp.status_code == 422


def test_create_gene_409_duplicate(
    client: TestClient,
    mock_service: AsyncMock,
) -> None:
    mock_service.create.side_effect = DuplicateGeneError()

    payload = {
        "gene_id": "ENSG00000139618",
        "gene_name": "TP53",
        "chromosome": "17",
    }
    resp = client.post("/genes/", json=payload)

    assert resp.status_code == 409
    assert resp.json()["detail"] == "Gene already exists"


def test_list_genes(
    client: TestClient,
    mock_service: AsyncMock,
    sample_response: dict[str, object],
) -> None:
    mock_service.list.return_value = [GeneResponse(**sample_response)]

    resp = client.get("/genes/")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["gene_id"] == "ENSG00000139618"


def test_list_genes_empty(client: TestClient, mock_service: AsyncMock) -> None:
    mock_service.list.return_value = []

    resp = client.get("/genes/")

    assert resp.status_code == 200
    assert resp.json() == []


def test_get_gene_200(
    client: TestClient,
    mock_service: AsyncMock,
    sample_gene_id: uuid.UUID,
    sample_response: dict[str, object],
) -> None:
    mock_service.get_by_id.return_value = GeneResponse(**sample_response)

    resp = client.get(f"/genes/{sample_gene_id}")

    assert resp.status_code == 200
    assert resp.json()["id"] == str(sample_gene_id)


def test_get_gene_404(client: TestClient, mock_service: AsyncMock) -> None:
    mock_service.get_by_id.return_value = None

    resp = client.get(f"/genes/{uuid.uuid4()}")

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Gene not found"


def test_get_gene_422_invalid_uuid(client: TestClient) -> None:
    resp = client.get("/genes/not-a-uuid")
    assert resp.status_code == 422


def test_update_gene_200(
    client: TestClient,
    mock_service: AsyncMock,
    sample_gene_id: uuid.UUID,
    sample_response: dict[str, object],
) -> None:
    mock_service.update.return_value = GeneResponse(**sample_response)

    resp = client.patch(f"/genes/{sample_gene_id}", json={"gene_name": "BRCA1"})

    assert resp.status_code == 200
    assert resp.json()["id"] == str(sample_gene_id)


def test_update_gene_404(client: TestClient, mock_service: AsyncMock) -> None:
    mock_service.update.return_value = None

    resp = client.patch(f"/genes/{uuid.uuid4()}", json={"gene_name": "BRCA1"})

    assert resp.status_code == 404


def test_update_gene_422_invalid_body(client: TestClient, sample_gene_id: uuid.UUID) -> None:
    resp = client.patch(f"/genes/{sample_gene_id}", json={"gene_id": 123})
    assert resp.status_code == 422


def test_update_gene_422_gene_id_too_long(
    client: TestClient,
    sample_gene_id: uuid.UUID,
) -> None:
    resp = client.patch(f"/genes/{sample_gene_id}", json={"gene_id": "E" * 51})
    assert resp.status_code == 422


def test_update_gene_409_duplicate(
    client: TestClient,
    mock_service: AsyncMock,
    sample_gene_id: uuid.UUID,
) -> None:
    mock_service.update.side_effect = DuplicateGeneError()

    resp = client.patch(
        f"/genes/{sample_gene_id}",
        json={"gene_id": "ENSG00000141510"},
    )

    assert resp.status_code == 409
    assert resp.json()["detail"] == "Gene already exists"


def test_delete_gene_204(client: TestClient, mock_service: AsyncMock) -> None:
    mock_service.delete.return_value = True

    resp = client.delete(f"/genes/{uuid.uuid4()}")

    assert resp.status_code == 204


def test_delete_gene_404(client: TestClient, mock_service: AsyncMock) -> None:
    mock_service.delete.return_value = False

    resp = client.delete(f"/genes/{uuid.uuid4()}")

    assert resp.status_code == 404
