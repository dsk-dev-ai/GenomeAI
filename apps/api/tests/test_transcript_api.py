from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from genomeai_api.exceptions import DuplicateTranscriptError
from genomeai_api.routes.transcripts import _get_service, router
from genomeai_api.schemas.transcript import TranscriptCreate, TranscriptResponse
from genomeai_api.services.transcript import TranscriptService


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock(spec=TranscriptService)


@pytest.fixture
def test_app(mock_service: AsyncMock) -> FastAPI:
    app = FastAPI()
    app.include_router(router)

    @app.exception_handler(DuplicateTranscriptError)
    async def _handler(
        request: Request, exc: DuplicateTranscriptError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)},
        )

    async def override() -> TranscriptService:
        return mock_service

    app.dependency_overrides[_get_service] = override
    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


@pytest.fixture
def sample_transcript_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def sample_response(sample_transcript_id: uuid.UUID) -> dict[str, object]:
    now = datetime.now(UTC).isoformat()
    return {
        "id": str(sample_transcript_id),
        "transcript_id": "ENST00000269305",
        "transcript_name": "TP53-201",
        "transcript_type": "protein_coding",
        "chromosome": "17",
        "strand": "+",
        "start_position": 7661779,
        "end_position": 7687538,
        "length": 25759,
        "genome_id": None,
        "gene_id": None,
        "variant_id": None,
        "description": "TP53 transcript",
        "created_at": now,
        "updated_at": now,
    }


def test_create_transcript_201(
    client: TestClient,
    mock_service: AsyncMock,
    sample_response: dict[str, object],
) -> None:
    mock_service.create.return_value = TranscriptResponse(**sample_response)

    payload = {
        "transcript_id": "ENST00000269305",
        "transcript_name": "TP53-201",
        "chromosome": "17",
    }
    resp = client.post("/transcripts/", json=payload)

    assert resp.status_code == 201
    assert resp.json()["transcript_id"] == "ENST00000269305"
    mock_service.create.assert_awaited_once()
    call_arg = mock_service.create.call_args[0][0]
    assert isinstance(call_arg, TranscriptCreate)


def test_create_transcript_422_missing_fields(client: TestClient) -> None:
    resp = client.post("/transcripts/", json={})
    assert resp.status_code == 422


def test_create_transcript_422_transcript_id_too_long(
    client: TestClient,
) -> None:
    resp = client.post(
        "/transcripts/",
        json={
            "transcript_id": "T" * 51,
            "transcript_name": "TP53-201",
            "chromosome": "17",
        },
    )
    assert resp.status_code == 422


def test_create_transcript_422_chromosome_too_long(
    client: TestClient,
) -> None:
    resp = client.post(
        "/transcripts/",
        json={
            "transcript_id": "ENST00000269305",
            "transcript_name": "TP53-201",
            "chromosome": "C" * 11,
        },
    )
    assert resp.status_code == 422


def test_create_transcript_409_duplicate(
    client: TestClient,
    mock_service: AsyncMock,
) -> None:
    mock_service.create.side_effect = DuplicateTranscriptError()

    payload = {
        "transcript_id": "ENST00000269305",
        "transcript_name": "TP53-201",
        "chromosome": "17",
    }
    resp = client.post("/transcripts/", json=payload)

    assert resp.status_code == 409
    assert resp.json()["detail"] == "Transcript already exists"


def test_list_transcripts(
    client: TestClient,
    mock_service: AsyncMock,
    sample_response: dict[str, object],
) -> None:
    mock_service.list.return_value = [TranscriptResponse(**sample_response)]

    resp = client.get("/transcripts/")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["transcript_id"] == "ENST00000269305"


def test_list_transcripts_empty(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.list.return_value = []

    resp = client.get("/transcripts/")

    assert resp.status_code == 200
    assert resp.json() == []


def test_get_transcript_200(
    client: TestClient,
    mock_service: AsyncMock,
    sample_transcript_id: uuid.UUID,
    sample_response: dict[str, object],
) -> None:
    mock_service.get_by_id.return_value = TranscriptResponse(**sample_response)

    resp = client.get(f"/transcripts/{sample_transcript_id}")

    assert resp.status_code == 200
    assert resp.json()["id"] == str(sample_transcript_id)


def test_get_transcript_404(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.get_by_id.return_value = None

    resp = client.get(f"/transcripts/{uuid.uuid4()}")

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Transcript not found"


def test_get_transcript_422_invalid_uuid(client: TestClient) -> None:
    resp = client.get("/transcripts/not-a-uuid")
    assert resp.status_code == 422


def test_update_transcript_200(
    client: TestClient,
    mock_service: AsyncMock,
    sample_transcript_id: uuid.UUID,
    sample_response: dict[str, object],
) -> None:
    mock_service.update.return_value = TranscriptResponse(**sample_response)

    resp = client.patch(
        f"/transcripts/{sample_transcript_id}", json={"chromosome": "X"}
    )

    assert resp.status_code == 200
    assert resp.json()["id"] == str(sample_transcript_id)


def test_update_transcript_404(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.update.return_value = None

    resp = client.patch(f"/transcripts/{uuid.uuid4()}", json={"chromosome": "X"})

    assert resp.status_code == 404


def test_update_transcript_422_invalid_body(
    client: TestClient,
    sample_transcript_id: uuid.UUID,
) -> None:
    resp = client.patch(
        f"/transcripts/{sample_transcript_id}", json={"transcript_id": 123}
    )
    assert resp.status_code == 422


def test_update_transcript_422_transcript_id_too_long(
    client: TestClient,
    sample_transcript_id: uuid.UUID,
) -> None:
    resp = client.patch(
        f"/transcripts/{sample_transcript_id}",
        json={"transcript_id": "T" * 51},
    )
    assert resp.status_code == 422


def test_update_transcript_409_duplicate(
    client: TestClient,
    mock_service: AsyncMock,
    sample_transcript_id: uuid.UUID,
) -> None:
    mock_service.update.side_effect = DuplicateTranscriptError()

    resp = client.patch(
        f"/transcripts/{sample_transcript_id}",
        json={"transcript_id": "ENST00000420229"},
    )

    assert resp.status_code == 409
    assert resp.json()["detail"] == "Transcript already exists"


def test_delete_transcript_204(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.delete.return_value = True

    resp = client.delete(f"/transcripts/{uuid.uuid4()}")

    assert resp.status_code == 204


def test_delete_transcript_404(
    client: TestClient, mock_service: AsyncMock
) -> None:
    mock_service.delete.return_value = False

    resp = client.delete(f"/transcripts/{uuid.uuid4()}")

    assert resp.status_code == 404
