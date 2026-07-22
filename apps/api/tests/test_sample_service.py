from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from genomeai_api.exceptions import DuplicateSampleError
from genomeai_api.models.sample import Sample
from genomeai_api.repositories.sample import SampleRepository
from genomeai_api.schemas.sample import SampleCreate, SampleResponse, SampleUpdate
from genomeai_api.services.sample import SampleService


@pytest.fixture
def mock_repository() -> AsyncMock:
    return AsyncMock(spec=SampleRepository)


@pytest.fixture
def service(mock_repository: AsyncMock) -> SampleService:
    return SampleService(mock_repository)


def _make_sample(**overrides: object) -> Sample:
    return Sample(
        sample_id=overrides.get("sample_id", "SMP001"),
        sample_name=overrides.get("sample_name", "Sample 1"),
        organism=overrides.get("organism", "Homo sapiens"),
        id=overrides.get("id", uuid.uuid4()),
        created_at=overrides.get("created_at", datetime.now(UTC)),
        updated_at=overrides.get("updated_at", datetime.now(UTC)),
    )


@pytest.mark.asyncio
async def test_create(service: SampleService, mock_repository: AsyncMock) -> None:
    sample = _make_sample()
    mock_repository.create.return_value = sample

    data = SampleCreate(sample_id="SMP001", sample_name="Sample 1", organism="Homo sapiens")
    result = await service.create(data)

    assert isinstance(result, SampleResponse)
    assert result.sample_id == "SMP001"
    mock_repository.create.assert_awaited_once_with(data)


@pytest.mark.asyncio
async def test_create_duplicate_sample(
    service: SampleService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.create.side_effect = DuplicateSampleError()

    data = SampleCreate(sample_id="SMP001", sample_name="Sample 1", organism="Homo sapiens")
    with pytest.raises(DuplicateSampleError):
        await service.create(data)


@pytest.mark.asyncio
async def test_get_by_id_found(service: SampleService, mock_repository: AsyncMock) -> None:
    sample = _make_sample()
    mock_repository.get_by_id.return_value = sample

    result = await service.get_by_id(sample.id)

    assert isinstance(result, SampleResponse)
    assert result.id == sample.id
    mock_repository.get_by_id.assert_awaited_once_with(sample.id)


@pytest.mark.asyncio
async def test_get_by_id_not_found(service: SampleService, mock_repository: AsyncMock) -> None:
    sample_id = uuid.uuid4()
    mock_repository.get_by_id.return_value = None

    result = await service.get_by_id(sample_id)

    assert result is None


@pytest.mark.asyncio
async def test_list(service: SampleService, mock_repository: AsyncMock) -> None:
    samples = [_make_sample(), _make_sample()]
    mock_repository.list.return_value = samples

    results = await service.list()

    assert len(results) == 2
    assert all(isinstance(r, SampleResponse) for r in results)


@pytest.mark.asyncio
async def test_list_empty(service: SampleService, mock_repository: AsyncMock) -> None:
    mock_repository.list.return_value = []

    results = await service.list()

    assert results == []


@pytest.mark.asyncio
async def test_update_found(service: SampleService, mock_repository: AsyncMock) -> None:
    sample = _make_sample()
    mock_repository.update.return_value = sample

    data = SampleUpdate(organism="Mus musculus")
    result = await service.update(sample.id, data)

    assert isinstance(result, SampleResponse)
    mock_repository.update.assert_awaited_once_with(sample.id, data)


@pytest.mark.asyncio
async def test_update_not_found(service: SampleService, mock_repository: AsyncMock) -> None:
    sample_id = uuid.uuid4()
    mock_repository.update.return_value = None

    data = SampleUpdate(organism="Mus musculus")
    result = await service.update(sample_id, data)

    assert result is None


@pytest.mark.asyncio
async def test_update_duplicate_sample(
    service: SampleService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.update.side_effect = DuplicateSampleError()

    sample_id = uuid.uuid4()
    data = SampleUpdate(sample_id="SMP002")
    with pytest.raises(DuplicateSampleError):
        await service.update(sample_id, data)


@pytest.mark.asyncio
async def test_delete_found(service: SampleService, mock_repository: AsyncMock) -> None:
    sample_id = uuid.uuid4()
    mock_repository.delete.return_value = True

    result = await service.delete(sample_id)

    assert result is True
    mock_repository.delete.assert_awaited_once_with(sample_id)


@pytest.mark.asyncio
async def test_delete_not_found(service: SampleService, mock_repository: AsyncMock) -> None:
    sample_id = uuid.uuid4()
    mock_repository.delete.return_value = False

    result = await service.delete(sample_id)

    assert result is False
