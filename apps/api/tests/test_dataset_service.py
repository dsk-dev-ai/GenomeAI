from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from genomeai_api.exceptions import DuplicateDatasetError, InvalidForeignKeyError
from genomeai_api.models.dataset import Dataset
from genomeai_api.repositories.dataset import DatasetRepository
from genomeai_api.schemas.dataset import (
    DatasetCreate,
    DatasetResponse,
    DatasetUpdate,
)
from genomeai_api.services.dataset import DatasetService


@pytest.fixture
def mock_repository() -> AsyncMock:
    return AsyncMock(spec=DatasetRepository)


@pytest.fixture
def service(mock_repository: AsyncMock) -> DatasetService:
    return DatasetService(mock_repository)


def _make_dataset(**overrides: object) -> Dataset:
    return Dataset(
        dataset_id=overrides.get("dataset_id", "DS-001"),
        dataset_name=overrides.get("dataset_name", "RNA-seq data"),
        id=overrides.get("id", uuid.uuid4()),
        created_at=overrides.get("created_at", datetime.now(UTC)),
        updated_at=overrides.get("updated_at", datetime.now(UTC)),
    )


@pytest.mark.asyncio
async def test_create(service: DatasetService, mock_repository: AsyncMock) -> None:
    dataset = _make_dataset()
    mock_repository.create.return_value = dataset

    data = DatasetCreate(
        dataset_id="DS-001",
        dataset_name="RNA-seq data",
    )
    result = await service.create(data)

    assert isinstance(result, DatasetResponse)
    assert result.dataset_id == "DS-001"
    mock_repository.create.assert_awaited_once_with(data)


@pytest.mark.asyncio
async def test_create_duplicate_dataset(
    service: DatasetService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.create.side_effect = DuplicateDatasetError()

    data = DatasetCreate(
        dataset_id="DS-001",
        dataset_name="RNA-seq data",
    )
    with pytest.raises(DuplicateDatasetError):
        await service.create(data)


@pytest.mark.asyncio
async def test_create_foreign_key_violation(
    service: DatasetService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.create.side_effect = InvalidForeignKeyError()

    data = DatasetCreate(
        dataset_id="DS-001",
        dataset_name="RNA-seq data",
        genome_id=uuid.uuid4(),
    )
    with pytest.raises(InvalidForeignKeyError):
        await service.create(data)


@pytest.mark.asyncio
async def test_get_by_id_found(
    service: DatasetService, mock_repository: AsyncMock
) -> None:
    dataset = _make_dataset()
    mock_repository.get_by_id.return_value = dataset

    result = await service.get_by_id(dataset.id)

    assert isinstance(result, DatasetResponse)
    assert result.id == dataset.id
    mock_repository.get_by_id.assert_awaited_once_with(dataset.id)


@pytest.mark.asyncio
async def test_get_by_id_not_found(
    service: DatasetService, mock_repository: AsyncMock
) -> None:
    dataset_id = uuid.uuid4()
    mock_repository.get_by_id.return_value = None

    result = await service.get_by_id(dataset_id)

    assert result is None


@pytest.mark.asyncio
async def test_list(service: DatasetService, mock_repository: AsyncMock) -> None:
    datasets = [_make_dataset(), _make_dataset()]
    mock_repository.list.return_value = datasets

    results = await service.list()

    assert len(results) == 2
    assert all(isinstance(r, DatasetResponse) for r in results)


@pytest.mark.asyncio
async def test_list_empty(service: DatasetService, mock_repository: AsyncMock) -> None:
    mock_repository.list.return_value = []

    results = await service.list()

    assert results == []


@pytest.mark.asyncio
async def test_update_found(
    service: DatasetService, mock_repository: AsyncMock
) -> None:
    dataset = _make_dataset()
    mock_repository.update.return_value = dataset

    data = DatasetUpdate(dataset_name="WGS data")
    result = await service.update(dataset.id, data)

    assert isinstance(result, DatasetResponse)
    mock_repository.update.assert_awaited_once_with(dataset.id, data)


@pytest.mark.asyncio
async def test_update_not_found(
    service: DatasetService, mock_repository: AsyncMock
) -> None:
    dataset_id = uuid.uuid4()
    mock_repository.update.return_value = None

    data = DatasetUpdate(dataset_name="WGS data")
    result = await service.update(dataset_id, data)

    assert result is None


@pytest.mark.asyncio
async def test_update_duplicate_dataset(
    service: DatasetService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.update.side_effect = DuplicateDatasetError()

    dataset_id = uuid.uuid4()
    data = DatasetUpdate(dataset_id="DS-002")
    with pytest.raises(DuplicateDatasetError):
        await service.update(dataset_id, data)


@pytest.mark.asyncio
async def test_delete_found(
    service: DatasetService, mock_repository: AsyncMock
) -> None:
    dataset_id = uuid.uuid4()
    mock_repository.delete.return_value = True

    result = await service.delete(dataset_id)

    assert result is True
    mock_repository.delete.assert_awaited_once_with(dataset_id)


@pytest.mark.asyncio
async def test_delete_not_found(
    service: DatasetService, mock_repository: AsyncMock
) -> None:
    dataset_id = uuid.uuid4()
    mock_repository.delete.return_value = False

    result = await service.delete(dataset_id)

    assert result is False


@pytest.mark.asyncio
async def test_exists_true(
    service: DatasetService, mock_repository: AsyncMock
) -> None:
    dataset_id = uuid.uuid4()
    mock_repository.exists.return_value = True

    result = await service.exists(dataset_id)

    assert result is True
    mock_repository.exists.assert_awaited_once_with(dataset_id)


@pytest.mark.asyncio
async def test_exists_false(
    service: DatasetService, mock_repository: AsyncMock
) -> None:
    dataset_id = uuid.uuid4()
    mock_repository.exists.return_value = False

    result = await service.exists(dataset_id)

    assert result is False
