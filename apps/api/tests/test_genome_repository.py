from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from genomeai_api.models.genome import Genome
from genomeai_api.repositories.genome import GenomeRepository
from genomeai_api.schemas.genome import GenomeCreate, GenomeUpdate
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repository(mock_session: AsyncMock) -> GenomeRepository:
    return GenomeRepository(mock_session)


@pytest.mark.asyncio
async def test_create_genome(repository: GenomeRepository, mock_session: AsyncMock) -> None:
    data = GenomeCreate(
        accession="GCF_000001405.40",
        organism="Homo sapiens",
    )
    result = await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
    assert isinstance(result, Genome)
    assert result.accession == "GCF_000001405.40"


@pytest.mark.asyncio
async def test_get_by_id_found(repository: GenomeRepository, mock_session: AsyncMock) -> None:
    genome_id = uuid.uuid4()
    expected = Genome(
        id=genome_id,
        accession="GCF_000001405.40",
        organism="Homo sapiens",
    )
    mock_session.get.return_value = expected

    result = await repository.get_by_id(genome_id)

    mock_session.get.assert_awaited_once_with(Genome, genome_id)
    assert result is expected


@pytest.mark.asyncio
async def test_get_by_id_not_found(repository: GenomeRepository, mock_session: AsyncMock) -> None:
    genome_id = uuid.uuid4()
    mock_session.get.return_value = None

    result = await repository.get_by_id(genome_id)

    assert result is None


@pytest.mark.asyncio
async def test_list_genomes(repository: GenomeRepository, mock_session: AsyncMock) -> None:
    genome = Genome(id=uuid.uuid4(), accession="GCF_000001405.40", organism="Homo sapiens")
    scalars_result = MagicMock()
    scalars_result.all.return_value = [genome]
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_result
    mock_session.execute.return_value = result_mock

    results = await repository.list()

    mock_session.execute.assert_awaited_once()
    assert results == [genome]


@pytest.mark.asyncio
async def test_list_genomes_empty(repository: GenomeRepository, mock_session: AsyncMock) -> None:
    scalars_result = MagicMock()
    scalars_result.all.return_value = []
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_result
    mock_session.execute.return_value = result_mock

    results = await repository.list()

    assert results == []


@pytest.mark.asyncio
async def test_update_genome_found(repository: GenomeRepository, mock_session: AsyncMock) -> None:
    genome_id = uuid.uuid4()
    existing = Genome(
        id=genome_id,
        accession="GCF_000001405.40",
        organism="Homo sapiens",
    )
    mock_session.get.return_value = existing

    data = GenomeUpdate(organism="Mus musculus")
    result = await repository.update(genome_id, data)

    mock_session.get.assert_awaited_once_with(Genome, genome_id)
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
    assert result is not None
    assert result is existing
    assert existing.organism == "Mus musculus"


@pytest.mark.asyncio
async def test_update_genome_not_found(
    repository: GenomeRepository,
    mock_session: AsyncMock,
) -> None:
    genome_id = uuid.uuid4()
    mock_session.get.return_value = None

    data = GenomeUpdate(organism="Mus musculus")
    result = await repository.update(genome_id, data)

    assert result is None
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_delete_genome_found(repository: GenomeRepository, mock_session: AsyncMock) -> None:
    genome_id = uuid.uuid4()
    existing = Genome(
        id=genome_id,
        accession="GCF_000001405.40",
        organism="Homo sapiens",
    )
    mock_session.get.return_value = existing

    result = await repository.delete(genome_id)

    assert result is True
    mock_session.delete.assert_called_once_with(existing)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_genome_not_found(
    repository: GenomeRepository,
    mock_session: AsyncMock,
) -> None:
    genome_id = uuid.uuid4()
    mock_session.get.return_value = None

    result = await repository.delete(genome_id)

    assert result is False
    mock_session.delete.assert_not_called()
    mock_session.commit.assert_not_called()
