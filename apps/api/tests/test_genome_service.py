from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from genomeai_api.models.genome import Genome
from genomeai_api.repositories.genome import GenomeRepository
from genomeai_api.schemas.genome import GenomeCreate, GenomeResponse, GenomeUpdate
from genomeai_api.services.genome import GenomeService


@pytest.fixture
def mock_repository() -> AsyncMock:
    return AsyncMock(spec=GenomeRepository)


@pytest.fixture
def service(mock_repository: AsyncMock) -> GenomeService:
    return GenomeService(mock_repository)


def _make_genome(**overrides: object) -> Genome:
    return Genome(
        accession=overrides.get("accession", "GCF_000001405.40"),
        organism=overrides.get("organism", "Homo sapiens"),
        id=overrides.get("id", uuid.uuid4()),
        created_at=overrides.get("created_at", datetime.now(UTC)),
        updated_at=overrides.get("updated_at", datetime.now(UTC)),
    )


@pytest.mark.asyncio
async def test_create(service: GenomeService, mock_repository: AsyncMock) -> None:
    genome = _make_genome()
    mock_repository.create.return_value = genome

    data = GenomeCreate(accession="GCF_000001405.40", organism="Homo sapiens")
    result = await service.create(data)

    assert isinstance(result, GenomeResponse)
    assert result.accession == "GCF_000001405.40"
    mock_repository.create.assert_awaited_once_with(data)


@pytest.mark.asyncio
async def test_get_by_id_found(service: GenomeService, mock_repository: AsyncMock) -> None:
    genome = _make_genome()
    mock_repository.get_by_id.return_value = genome

    result = await service.get_by_id(genome.id)

    assert isinstance(result, GenomeResponse)
    assert result.id == genome.id
    mock_repository.get_by_id.assert_awaited_once_with(genome.id)


@pytest.mark.asyncio
async def test_get_by_id_not_found(service: GenomeService, mock_repository: AsyncMock) -> None:
    genome_id = uuid.uuid4()
    mock_repository.get_by_id.return_value = None

    result = await service.get_by_id(genome_id)

    assert result is None


@pytest.mark.asyncio
async def test_list(service: GenomeService, mock_repository: AsyncMock) -> None:
    genomes = [_make_genome(), _make_genome()]
    mock_repository.list.return_value = genomes

    results = await service.list()

    assert len(results) == 2
    assert all(isinstance(r, GenomeResponse) for r in results)


@pytest.mark.asyncio
async def test_list_empty(service: GenomeService, mock_repository: AsyncMock) -> None:
    mock_repository.list.return_value = []

    results = await service.list()

    assert results == []


@pytest.mark.asyncio
async def test_update_found(service: GenomeService, mock_repository: AsyncMock) -> None:
    genome = _make_genome()
    mock_repository.update.return_value = genome

    data = GenomeUpdate(organism="Mus musculus")
    result = await service.update(genome.id, data)

    assert isinstance(result, GenomeResponse)
    mock_repository.update.assert_awaited_once_with(genome.id, data)


@pytest.mark.asyncio
async def test_update_not_found(service: GenomeService, mock_repository: AsyncMock) -> None:
    genome_id = uuid.uuid4()
    mock_repository.update.return_value = None

    data = GenomeUpdate(organism="Mus musculus")
    result = await service.update(genome_id, data)

    assert result is None


@pytest.mark.asyncio
async def test_delete_found(service: GenomeService, mock_repository: AsyncMock) -> None:
    genome_id = uuid.uuid4()
    mock_repository.delete.return_value = True

    result = await service.delete(genome_id)

    assert result is True
    mock_repository.delete.assert_awaited_once_with(genome_id)


@pytest.mark.asyncio
async def test_delete_not_found(service: GenomeService, mock_repository: AsyncMock) -> None:
    genome_id = uuid.uuid4()
    mock_repository.delete.return_value = False

    result = await service.delete(genome_id)

    assert result is False
