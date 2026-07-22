from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from genomeai_api.exceptions import DuplicateProteinError
from genomeai_api.routes.proteins import _get_service, router
from genomeai_api.schemas.protein import ProteinCreate, ProteinResponse
from genomeai_api.services.protein import ProteinService


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock(spec=ProteinService)


@pytest.fixture
def test_app(mock_service: AsyncMock) -> FastAPI:
    app = FastAPI()
    app.include_router(router)

    @app.exception_handler(DuplicateProteinError)
    async def _handler(
        request: Request, exc: DuplicateProteinError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)},
        )

    async def override() -> ProteinService:
        return mock_service

    app.dependency_overrides[_get_service] = override
    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


@pytest.fixture
def sample_protein_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def sample_response(sample_protein_id: uuid.UUID) -> dict[str, object]:
    now = datetime.now(UTC).isoformat()
    return {
        "id": str(sample_protein_id),
        "protein_id": "P04637",
        "protein_name": "Cellular tumor antigen p53",
        "symbol": "TP53",
        "accession": "P04637",
        "sequence": "MEEPQSDPSVEPPLSQETFSDLWKLLPENNVLSPLPSQAM",
        "length": 393,
        "molecular_weight": 43653.0,
        "organism": "Homo sapiens",
        "function": "Tumor suppressor",
        "gene_id": None,
        "transcript_id": None,
        "genome_id": None,
        "description": "TP53 tumor suppressor",
        "created_at": now,
        "updated_at": now,
    }


def test_create_protein_201(
    client: TestClient,
    mock_service: AsyncMock,
    sample_response: dict[str, object],
) -> None:
    mock_service.create.return_value = ProteinResponse(**sample_response)

    payload = {
        "protein_id": "P04637",
        "protein_name": "Cellular tumor antigen p53",
    }
    resp = client.post("/proteins/", json=payload)

    assert resp.status_code == 201
    assert resp.json()["protein_id"] == "P04637"
    mock_service.create.assert_awaited_once()
    call_arg = mock_service.create.call_args[0][0]
    assert isinstance(call_arg, ProteinCreate)


def test_create_protein_422_missing_fields(client: TestClient) -> None:
    resp = client.post("/proteins/", json={})
    assert resp.status_code == 422


def test_create_protein_422_protein_id_too_long(
    client: TestClient,
) -> None:
    resp = client.post(
        "/proteins/",
        json={
            "protein_id": "P" * 51,
            "protein_name": "p53",
        },
    )
    assert resp.status_code == 422


def test_create_protein_422_protein_name_too_long(
    client: TestClient,
) -> None:
    resp = client.post(
        "/proteins/",
        json={
            "protein_id": "P04637",
            "protein_name": "P" * 256,
        },
    )
    assert resp.status_code == 422


def test_create_protein_409_duplicate(
    client: TestClient,
    mock_service: AsyncMock,
) -> None:
    mock_service.create.side_effect = DuplicateProteinError()

    payload = {
        "protein_id": "P04637",
        "protein_name": "Cellular tumor antigen p53",
    }
    resp = client.post("/proteins/", json=payload)

    assert resp.status_code == 409
    assert resp.json()["detail"] == "Protein already exists"


def test_list_proteins(
    client: TestClient,
    mock_service: AsyncMock,
    sample_response: dict[str, object],
) -> None:
    mock_service.list.return_value = [ProteinResponse(**sample_response)]

    resp = client.get("/proteins/")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["protein_id"] == "P04637"


def test_list_proteins_empty(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.list.return_value = []

    resp = client.get("/proteins/")

    assert resp.status_code == 200
    assert resp.json() == []


def test_get_protein_200(
    client: TestClient,
    mock_service: AsyncMock,
    sample_protein_id: uuid.UUID,
    sample_response: dict[str, object],
) -> None:
    mock_service.get_by_id.return_value = ProteinResponse(**sample_response)

    resp = client.get(f"/proteins/{sample_protein_id}")

    assert resp.status_code == 200
    assert resp.json()["id"] == str(sample_protein_id)


def test_get_protein_404(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.get_by_id.return_value = None

    resp = client.get(f"/proteins/{uuid.uuid4()}")

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Protein not found"


def test_get_protein_422_invalid_uuid(client: TestClient) -> None:
    resp = client.get("/proteins/not-a-uuid")
    assert resp.status_code == 422


def test_update_protein_200(
    client: TestClient,
    mock_service: AsyncMock,
    sample_protein_id: uuid.UUID,
    sample_response: dict[str, object],
) -> None:
    mock_service.update.return_value = ProteinResponse(**sample_response)

    resp = client.patch(
        f"/proteins/{sample_protein_id}", json={"protein_name": "p53 (updated)"}
    )

    assert resp.status_code == 200
    assert resp.json()["id"] == str(sample_protein_id)


def test_update_protein_404(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.update.return_value = None

    resp = client.patch(
        f"/proteins/{uuid.uuid4()}", json={"protein_name": "p53 (updated)"}
    )

    assert resp.status_code == 404


def test_update_protein_422_invalid_body(
    client: TestClient,
    sample_protein_id: uuid.UUID,
) -> None:
    resp = client.patch(
        f"/proteins/{sample_protein_id}", json={"protein_id": 123}
    )
    assert resp.status_code == 422


def test_update_protein_422_null_protein_id(
    client: TestClient,
    sample_protein_id: uuid.UUID,
) -> None:
    resp = client.patch(
        f"/proteins/{sample_protein_id}",
        json={"protein_id": None},
    )
    assert resp.status_code == 422


def test_update_protein_422_null_protein_name(
    client: TestClient,
    sample_protein_id: uuid.UUID,
) -> None:
    resp = client.patch(
        f"/proteins/{sample_protein_id}",
        json={"protein_name": None},
    )
    assert resp.status_code == 422


def test_update_protein_422_protein_id_too_long(
    client: TestClient,
    sample_protein_id: uuid.UUID,
) -> None:
    resp = client.patch(
        f"/proteins/{sample_protein_id}",
        json={"protein_id": "P" * 51},
    )
    assert resp.status_code == 422


def test_update_protein_409_duplicate(
    client: TestClient,
    mock_service: AsyncMock,
    sample_protein_id: uuid.UUID,
) -> None:
    mock_service.update.side_effect = DuplicateProteinError()

    resp = client.patch(
        f"/proteins/{sample_protein_id}",
        json={"protein_id": "P04638"},
    )

    assert resp.status_code == 409
    assert resp.json()["detail"] == "Protein already exists"


def test_delete_protein_204(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.delete.return_value = True

    resp = client.delete(f"/proteins/{uuid.uuid4()}")

    assert resp.status_code == 204


def test_delete_protein_404(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.delete.return_value = False

    resp = client.delete(f"/proteins/{uuid.uuid4()}")

    assert resp.status_code == 404
