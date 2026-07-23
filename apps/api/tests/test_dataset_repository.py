from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from genomeai_api.exceptions import DuplicateDatasetError, InvalidForeignKeyError
from genomeai_api.models.dataset import Dataset
from genomeai_api.repositories.dataset import DatasetRepository
from genomeai_api.schemas.dataset import DatasetCreate, DatasetUpdate
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repository(mock_session: AsyncMock) -> DatasetRepository:
    return DatasetRepository(mock_session)


@pytest.mark.asyncio
async def test_create_dataset(
    repository: DatasetRepository, mock_session: AsyncMock
) -> None:
    data = DatasetCreate(
        dataset_id="DS-001",
        dataset_name="RNA-seq data",
    )
    result = await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
    assert isinstance(result, Dataset)
    assert result.dataset_id == "DS-001"


@pytest.mark.asyncio
async def test_create_duplicate_dataset(
    repository: DatasetRepository,
    mock_session: AsyncMock,
) -> None:
    orig = MagicMock()
    orig.sqlstate = "23505"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = DatasetCreate(
        dataset_id="DS-001",
        dataset_name="RNA-seq data",
    )

    with pytest.raises(DuplicateDatasetError):
        await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_create_foreign_key_violation(
    repository: DatasetRepository,
    mock_session: AsyncMock,
) -> None:
    orig = MagicMock()
    orig.sqlstate = "23503"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = DatasetCreate(
        dataset_id="DS-001",
        dataset_name="RNA-seq data",
        genome_id=uuid.uuid4(),
    )

    with pytest.raises(InvalidForeignKeyError):
        await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_create_non_duplicate_integrity_error(
    repository: DatasetRepository,
    mock_session: AsyncMock,
) -> None:
    orig = MagicMock()
    orig.sqlstate = "99999"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = DatasetCreate(
        dataset_id="DS-001",
        dataset_name="RNA-seq data",
    )

    with pytest.raises(IntegrityError):
        await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_get_by_id_found(
    repository: DatasetRepository, mock_session: AsyncMock
) -> None:
    dataset_id = uuid.uuid4()
    expected = Dataset(
        id=dataset_id,
        dataset_id="DS-001",
        dataset_name="RNA-seq data",
    )
    mock_session.get.return_value = expected

    result = await repository.get_by_id(dataset_id)

    mock_session.get.assert_awaited_once_with(Dataset, dataset_id)
    assert result is expected


@pytest.mark.asyncio
async def test_get_by_id_not_found(
    repository: DatasetRepository,
    mock_session: AsyncMock,
) -> None:
    dataset_id = uuid.uuid4()
    mock_session.get.return_value = None

    result = await repository.get_by_id(dataset_id)

    assert result is None


@pytest.mark.asyncio
async def test_list_multiple(
    repository: DatasetRepository, mock_session: AsyncMock
) -> None:
    d1 = Dataset(
        id=uuid.uuid4(),
        dataset_id="DS-001",
        dataset_name="RNA-seq data",
    )
    d2 = Dataset(
        id=uuid.uuid4(),
        dataset_id="DS-002",
        dataset_name="WGS data",
    )
    scalars_result = MagicMock()
    scalars_result.all.return_value = [d1, d2]
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_result
    mock_session.execute.return_value = result_mock

    results = await repository.list()

    assert len(results) == 2
    assert results[0] is d1
    assert results[1] is d2


@pytest.mark.asyncio
async def test_list_order_by_desc(
    repository: DatasetRepository,
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
    assert "datasets.created_at" in compiled.lower()
    assert "DESC" in compiled.upper()


@pytest.mark.asyncio
async def test_list_empty(
    repository: DatasetRepository, mock_session: AsyncMock
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
    repository: DatasetRepository, mock_session: AsyncMock
) -> None:
    dataset_id = uuid.uuid4()
    existing = Dataset(
        id=dataset_id,
        dataset_id="DS-001",
        dataset_name="RNA-seq data",
    )
    mock_session.get.return_value = existing

    data = DatasetUpdate(dataset_name="WGS data")
    result = await repository.update(dataset_id, data)

    mock_session.get.assert_awaited_once_with(Dataset, dataset_id)
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
    assert result is not None
    assert result is existing
    assert existing.dataset_name == "WGS data"


@pytest.mark.asyncio
async def test_update_not_found(
    repository: DatasetRepository,
    mock_session: AsyncMock,
) -> None:
    dataset_id = uuid.uuid4()
    mock_session.get.return_value = None

    data = DatasetUpdate(dataset_name="WGS data")
    result = await repository.update(dataset_id, data)

    assert result is None
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_update_duplicate_dataset(
    repository: DatasetRepository,
    mock_session: AsyncMock,
) -> None:
    dataset_id = uuid.uuid4()
    existing = Dataset(
        id=dataset_id,
        dataset_id="DS-001",
        dataset_name="RNA-seq data",
    )
    mock_session.get.return_value = existing
    orig = MagicMock()
    orig.sqlstate = "23505"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = DatasetUpdate(dataset_id="DS-002")
    with pytest.raises(DuplicateDatasetError):
        await repository.update(dataset_id, data)

    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_update_foreign_key_violation(
    repository: DatasetRepository,
    mock_session: AsyncMock,
) -> None:
    dataset_id = uuid.uuid4()
    existing = Dataset(
        id=dataset_id,
        dataset_id="DS-001",
        dataset_name="RNA-seq data",
    )
    mock_session.get.return_value = existing
    orig = MagicMock()
    orig.sqlstate = "23503"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = DatasetUpdate(genome_id=uuid.uuid4())
    with pytest.raises(InvalidForeignKeyError):
        await repository.update(dataset_id, data)

    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_delete_found(
    repository: DatasetRepository, mock_session: AsyncMock
) -> None:
    dataset_id = uuid.uuid4()
    existing = Dataset(
        id=dataset_id,
        dataset_id="DS-001",
        dataset_name="RNA-seq data",
    )
    mock_session.get.return_value = existing

    result = await repository.delete(dataset_id)

    assert result is True
    mock_session.delete.assert_awaited_once_with(existing)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_not_found(
    repository: DatasetRepository,
    mock_session: AsyncMock,
) -> None:
    dataset_id = uuid.uuid4()
    mock_session.get.return_value = None

    result = await repository.delete(dataset_id)

    assert result is False
    mock_session.delete.assert_not_called()
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_exists_true(
    repository: DatasetRepository, mock_session: AsyncMock
) -> None:
    dataset_id = uuid.uuid4()
    scalar_result = MagicMock()
    scalar_result.one_or_none.return_value = dataset_id
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalar_result
    mock_session.execute.return_value = result_mock

    result = await repository.exists(dataset_id)

    assert result is True


@pytest.mark.asyncio
async def test_exists_false(
    repository: DatasetRepository, mock_session: AsyncMock
) -> None:
    dataset_id = uuid.uuid4()
    scalar_result = MagicMock()
    scalar_result.one_or_none.return_value = None
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalar_result
    mock_session.execute.return_value = result_mock

    result = await repository.exists(dataset_id)

    assert result is False
