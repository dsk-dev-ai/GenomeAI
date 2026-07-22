from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from genomeai_api.exceptions import DuplicateSampleError
from genomeai_api.models.sample import Sample
from genomeai_api.repositories.sample import SampleRepository
from genomeai_api.schemas.sample import SampleCreate, SampleUpdate
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repository(mock_session: AsyncMock) -> SampleRepository:
    return SampleRepository(mock_session)


@pytest.mark.asyncio
async def test_create_sample(repository: SampleRepository, mock_session: AsyncMock) -> None:
    data = SampleCreate(
        sample_id="SMP001",
        sample_name="Sample 1",
        organism="Homo sapiens",
    )
    result = await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
    assert isinstance(result, Sample)
    assert result.sample_id == "SMP001"


@pytest.mark.asyncio
async def test_create_duplicate_sample(
    repository: SampleRepository,
    mock_session: AsyncMock,
) -> None:
    orig = MagicMock()
    orig.sqlstate = "23505"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = SampleCreate(
        sample_id="SMP001",
        sample_name="Sample 1",
        organism="Homo sapiens",
    )

    with pytest.raises(DuplicateSampleError):
        await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_get_by_id_found(repository: SampleRepository, mock_session: AsyncMock) -> None:
    sample_id = uuid.uuid4()
    expected = Sample(
        id=sample_id,
        sample_id="SMP001",
        sample_name="Sample 1",
        organism="Homo sapiens",
    )
    mock_session.get.return_value = expected

    result = await repository.get_by_id(sample_id)

    mock_session.get.assert_awaited_once_with(Sample, sample_id)
    assert result is expected


@pytest.mark.asyncio
async def test_get_by_id_not_found(repository: SampleRepository, mock_session: AsyncMock) -> None:
    sample_id = uuid.uuid4()
    mock_session.get.return_value = None

    result = await repository.get_by_id(sample_id)

    assert result is None


@pytest.mark.asyncio
async def test_list_multiple(repository: SampleRepository, mock_session: AsyncMock) -> None:
    sample1 = Sample(
        id=uuid.uuid4(),
        sample_id="SMP001",
        sample_name="Sample 1",
        organism="Homo sapiens",
    )
    sample2 = Sample(
        id=uuid.uuid4(),
        sample_id="SMP002",
        sample_name="Sample 2",
        organism="Mus musculus",
    )
    scalars_result = MagicMock()
    scalars_result.all.return_value = [sample1, sample2]
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_result
    mock_session.execute.return_value = result_mock

    results = await repository.list()

    assert len(results) == 2
    assert results[0] is sample1
    assert results[1] is sample2


@pytest.mark.asyncio
async def test_list_order_by_desc(repository: SampleRepository, mock_session: AsyncMock) -> None:
    scalars_result = MagicMock()
    scalars_result.all.return_value = []
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_result
    mock_session.execute.return_value = result_mock

    await repository.list()

    stmt = mock_session.execute.call_args[0][0]
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "ORDER BY" in compiled.upper()
    assert "samples.created_at" in compiled.lower()


@pytest.mark.asyncio
async def test_list_empty(repository: SampleRepository, mock_session: AsyncMock) -> None:
    scalars_result = MagicMock()
    scalars_result.all.return_value = []
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_result
    mock_session.execute.return_value = result_mock

    results = await repository.list()

    assert results == []


@pytest.mark.asyncio
async def test_update_found(repository: SampleRepository, mock_session: AsyncMock) -> None:
    sample_id = uuid.uuid4()
    existing = Sample(
        id=sample_id,
        sample_id="SMP001",
        sample_name="Sample 1",
        organism="Homo sapiens",
    )
    mock_session.get.return_value = existing

    data = SampleUpdate(organism="Mus musculus")
    result = await repository.update(sample_id, data)

    mock_session.get.assert_awaited_once_with(Sample, sample_id)
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
    assert result is not None
    assert result is existing
    assert existing.organism == "Mus musculus"


@pytest.mark.asyncio
async def test_update_not_found(
    repository: SampleRepository,
    mock_session: AsyncMock,
) -> None:
    sample_id = uuid.uuid4()
    mock_session.get.return_value = None

    data = SampleUpdate(organism="Mus musculus")
    result = await repository.update(sample_id, data)

    assert result is None
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_update_duplicate_sample(
    repository: SampleRepository,
    mock_session: AsyncMock,
) -> None:
    sample_id = uuid.uuid4()
    existing = Sample(
        id=sample_id,
        sample_id="SMP001",
        sample_name="Sample 1",
        organism="Homo sapiens",
    )
    mock_session.get.return_value = existing
    orig = MagicMock()
    orig.sqlstate = "23505"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = SampleUpdate(sample_id="SMP002")
    with pytest.raises(DuplicateSampleError):
        await repository.update(sample_id, data)

    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_delete_found(repository: SampleRepository, mock_session: AsyncMock) -> None:
    sample_id = uuid.uuid4()
    existing = Sample(
        id=sample_id,
        sample_id="SMP001",
        sample_name="Sample 1",
        organism="Homo sapiens",
    )
    mock_session.get.return_value = existing

    result = await repository.delete(sample_id)

    assert result is True
    mock_session.delete.assert_called_once_with(existing)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_not_found(
    repository: SampleRepository,
    mock_session: AsyncMock,
) -> None:
    sample_id = uuid.uuid4()
    mock_session.get.return_value = None

    result = await repository.delete(sample_id)

    assert result is False
    mock_session.delete.assert_not_called()
    mock_session.commit.assert_not_called()
