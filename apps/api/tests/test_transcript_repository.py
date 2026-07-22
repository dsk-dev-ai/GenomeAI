from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from genomeai_api.exceptions import DuplicateTranscriptError
from genomeai_api.models.transcript import Transcript
from genomeai_api.repositories.transcript import TranscriptRepository
from genomeai_api.schemas.transcript import TranscriptCreate, TranscriptUpdate
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repository(mock_session: AsyncMock) -> TranscriptRepository:
    return TranscriptRepository(mock_session)


@pytest.mark.asyncio
async def test_create_transcript(
    repository: TranscriptRepository, mock_session: AsyncMock
) -> None:
    data = TranscriptCreate(
        transcript_id="ENST00000269305",
        transcript_name="TP53-201",
        chromosome="17",
    )
    result = await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
    assert isinstance(result, Transcript)
    assert result.transcript_id == "ENST00000269305"


@pytest.mark.asyncio
async def test_create_duplicate_transcript(
    repository: TranscriptRepository,
    mock_session: AsyncMock,
) -> None:
    orig = MagicMock()
    orig.sqlstate = "23505"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = TranscriptCreate(
        transcript_id="ENST00000269305",
        transcript_name="TP53-201",
        chromosome="17",
    )

    with pytest.raises(DuplicateTranscriptError):
        await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_create_non_duplicate_integrity_error(
    repository: TranscriptRepository,
    mock_session: AsyncMock,
) -> None:
    orig = MagicMock()
    orig.sqlstate = "99999"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = TranscriptCreate(
        transcript_id="ENST00000269305",
        transcript_name="TP53-201",
        chromosome="17",
    )

    with pytest.raises(IntegrityError):
        await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_get_by_id_found(
    repository: TranscriptRepository, mock_session: AsyncMock
) -> None:
    transcript_id = uuid.uuid4()
    expected = Transcript(
        id=transcript_id,
        transcript_id="ENST00000269305",
        transcript_name="TP53-201",
        chromosome="17",
    )
    mock_session.get.return_value = expected

    result = await repository.get_by_id(transcript_id)

    mock_session.get.assert_awaited_once_with(Transcript, transcript_id)
    assert result is expected


@pytest.mark.asyncio
async def test_get_by_id_not_found(
    repository: TranscriptRepository,
    mock_session: AsyncMock,
) -> None:
    transcript_id = uuid.uuid4()
    mock_session.get.return_value = None

    result = await repository.get_by_id(transcript_id)

    assert result is None


@pytest.mark.asyncio
async def test_list_multiple(
    repository: TranscriptRepository, mock_session: AsyncMock
) -> None:
    t1 = Transcript(
        id=uuid.uuid4(),
        transcript_id="ENST00000269305",
        transcript_name="TP53-201",
        chromosome="17",
    )
    t2 = Transcript(
        id=uuid.uuid4(),
        transcript_id="ENST00000420229",
        transcript_name="TP53-202",
        chromosome="17",
    )
    scalars_result = MagicMock()
    scalars_result.all.return_value = [t1, t2]
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_result
    mock_session.execute.return_value = result_mock

    results = await repository.list()

    assert len(results) == 2
    assert results[0] is t1
    assert results[1] is t2


@pytest.mark.asyncio
async def test_list_order_by_desc(
    repository: TranscriptRepository,
    mock_session: AsyncMock,
) -> None:
    scalars_result = MagicMock()
    scalars_result.all.return_value = []
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_result
    mock_session.execute.return_value = result_mock

    await repository.list()

    stmt = mock_session.execute.call_args[0][0]
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "ORDER BY" in compiled.upper()
    assert "transcripts.created_at" in compiled.lower()
    assert "DESC" in compiled.upper()


@pytest.mark.asyncio
async def test_list_empty(
    repository: TranscriptRepository, mock_session: AsyncMock
) -> None:
    scalars_result = MagicMock()
    scalars_result.all.return_value = []
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_result
    mock_session.execute.return_value = result_mock

    results = await repository.list()

    assert results == []


@pytest.mark.asyncio
async def test_update_found(
    repository: TranscriptRepository, mock_session: AsyncMock
) -> None:
    transcript_id = uuid.uuid4()
    existing = Transcript(
        id=transcript_id,
        transcript_id="ENST00000269305",
        transcript_name="TP53-201",
        chromosome="17",
    )
    mock_session.get.return_value = existing

    data = TranscriptUpdate(chromosome="X")
    result = await repository.update(transcript_id, data)

    mock_session.get.assert_awaited_once_with(Transcript, transcript_id)
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
    assert result is not None
    assert result is existing
    assert existing.chromosome == "X"


@pytest.mark.asyncio
async def test_update_not_found(
    repository: TranscriptRepository,
    mock_session: AsyncMock,
) -> None:
    transcript_id = uuid.uuid4()
    mock_session.get.return_value = None

    data = TranscriptUpdate(chromosome="X")
    result = await repository.update(transcript_id, data)

    assert result is None
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_update_duplicate_transcript(
    repository: TranscriptRepository,
    mock_session: AsyncMock,
) -> None:
    transcript_id = uuid.uuid4()
    existing = Transcript(
        id=transcript_id,
        transcript_id="ENST00000269305",
        transcript_name="TP53-201",
        chromosome="17",
    )
    mock_session.get.return_value = existing
    orig = MagicMock()
    orig.sqlstate = "23505"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = TranscriptUpdate(transcript_id="ENST00000420229")
    with pytest.raises(DuplicateTranscriptError):
        await repository.update(transcript_id, data)

    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_delete_found(
    repository: TranscriptRepository, mock_session: AsyncMock
) -> None:
    transcript_id = uuid.uuid4()
    existing = Transcript(
        id=transcript_id,
        transcript_id="ENST00000269305",
        transcript_name="TP53-201",
        chromosome="17",
    )
    mock_session.get.return_value = existing

    result = await repository.delete(transcript_id)

    assert result is True
    mock_session.delete.assert_called_once_with(existing)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_not_found(
    repository: TranscriptRepository,
    mock_session: AsyncMock,
) -> None:
    transcript_id = uuid.uuid4()
    mock_session.get.return_value = None

    result = await repository.delete(transcript_id)

    assert result is False
    mock_session.delete.assert_not_called()
    mock_session.commit.assert_not_called()
