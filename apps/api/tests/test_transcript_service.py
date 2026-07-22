from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from genomeai_api.exceptions import DuplicateTranscriptError
from genomeai_api.models.transcript import Transcript
from genomeai_api.repositories.transcript import TranscriptRepository
from genomeai_api.schemas.transcript import (
    TranscriptCreate,
    TranscriptResponse,
    TranscriptUpdate,
)
from genomeai_api.services.transcript import TranscriptService


@pytest.fixture
def mock_repository() -> AsyncMock:
    return AsyncMock(spec=TranscriptRepository)


@pytest.fixture
def service(mock_repository: AsyncMock) -> TranscriptService:
    return TranscriptService(mock_repository)


def _make_transcript(**overrides: object) -> Transcript:
    return Transcript(
        transcript_id=overrides.get("transcript_id", "ENST00000269305"),
        transcript_name=overrides.get("transcript_name", "TP53-201"),
        chromosome=overrides.get("chromosome", "17"),
        id=overrides.get("id", uuid.uuid4()),
        created_at=overrides.get("created_at", datetime.now(UTC)),
        updated_at=overrides.get("updated_at", datetime.now(UTC)),
    )


@pytest.mark.asyncio
async def test_create(service: TranscriptService, mock_repository: AsyncMock) -> None:
    transcript = _make_transcript()
    mock_repository.create.return_value = transcript

    data = TranscriptCreate(
        transcript_id="ENST00000269305",
        transcript_name="TP53-201",
        chromosome="17",
    )
    result = await service.create(data)

    assert isinstance(result, TranscriptResponse)
    assert result.transcript_id == "ENST00000269305"
    mock_repository.create.assert_awaited_once_with(data)


@pytest.mark.asyncio
async def test_create_duplicate_transcript(
    service: TranscriptService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.create.side_effect = DuplicateTranscriptError()

    data = TranscriptCreate(
        transcript_id="ENST00000269305",
        transcript_name="TP53-201",
        chromosome="17",
    )
    with pytest.raises(DuplicateTranscriptError):
        await service.create(data)


@pytest.mark.asyncio
async def test_get_by_id_found(
    service: TranscriptService, mock_repository: AsyncMock
) -> None:
    transcript = _make_transcript()
    mock_repository.get_by_id.return_value = transcript

    result = await service.get_by_id(transcript.id)

    assert isinstance(result, TranscriptResponse)
    assert result.id == transcript.id
    mock_repository.get_by_id.assert_awaited_once_with(transcript.id)


@pytest.mark.asyncio
async def test_get_by_id_not_found(
    service: TranscriptService, mock_repository: AsyncMock
) -> None:
    transcript_id = uuid.uuid4()
    mock_repository.get_by_id.return_value = None

    result = await service.get_by_id(transcript_id)

    assert result is None


@pytest.mark.asyncio
async def test_list(service: TranscriptService, mock_repository: AsyncMock) -> None:
    transcripts = [_make_transcript(), _make_transcript()]
    mock_repository.list.return_value = transcripts

    results = await service.list()

    assert len(results) == 2
    assert all(isinstance(r, TranscriptResponse) for r in results)


@pytest.mark.asyncio
async def test_list_empty(service: TranscriptService, mock_repository: AsyncMock) -> None:
    mock_repository.list.return_value = []

    results = await service.list()

    assert results == []


@pytest.mark.asyncio
async def test_update_found(
    service: TranscriptService, mock_repository: AsyncMock
) -> None:
    transcript = _make_transcript()
    mock_repository.update.return_value = transcript

    data = TranscriptUpdate(chromosome="X")
    result = await service.update(transcript.id, data)

    assert isinstance(result, TranscriptResponse)
    mock_repository.update.assert_awaited_once_with(transcript.id, data)


@pytest.mark.asyncio
async def test_update_not_found(
    service: TranscriptService, mock_repository: AsyncMock
) -> None:
    transcript_id = uuid.uuid4()
    mock_repository.update.return_value = None

    data = TranscriptUpdate(chromosome="X")
    result = await service.update(transcript_id, data)

    assert result is None


@pytest.mark.asyncio
async def test_update_duplicate_transcript(
    service: TranscriptService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.update.side_effect = DuplicateTranscriptError()

    transcript_id = uuid.uuid4()
    data = TranscriptUpdate(transcript_id="ENST00000420229")
    with pytest.raises(DuplicateTranscriptError):
        await service.update(transcript_id, data)


@pytest.mark.asyncio
async def test_delete_found(
    service: TranscriptService, mock_repository: AsyncMock
) -> None:
    transcript_id = uuid.uuid4()
    mock_repository.delete.return_value = True

    result = await service.delete(transcript_id)

    assert result is True
    mock_repository.delete.assert_awaited_once_with(transcript_id)


@pytest.mark.asyncio
async def test_delete_not_found(
    service: TranscriptService, mock_repository: AsyncMock
) -> None:
    transcript_id = uuid.uuid4()
    mock_repository.delete.return_value = False

    result = await service.delete(transcript_id)

    assert result is False
