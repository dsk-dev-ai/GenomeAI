from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from genomeai_api.exceptions import DuplicateGenomeAccessionError
from genomeai_api.models.genome import Genome
from genomeai_api.repositories.genome import GenomeRepository
from genomeai_api.schemas.genome import GenomeCreate, GenomeUpdate
from sqlalchemy.exc import IntegrityError
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
async def test_create_duplicate_accession(
    repository: GenomeRepository,
    mock_session: AsyncMock,
) -> None:
    mock_session.commit.side_effect = IntegrityError("test", "orig", "dup")

    data = GenomeCreate(
        accession="GCF_000001405.40",
        organism="Homo sapiens",
    )

    with pytest.raises(DuplicateGenomeAccessionError):
        await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


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
async def test_list_multiple(repository: GenomeRepository, mock_session: AsyncMock) -> None:
    genome1 = Genome(id=uuid.uuid4(), accession="GCF_000001405.40", organism="Homo sapiens")
    genome2 = Genome(id=uuid.uuid4(), accession="GCF_000002409.10", organism="Mus musculus")
    scalars_result = MagicMock()
    scalars_result.all.return_value = [genome1, genome2]
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_result
    mock_session.execute.return_value = result_mock

    results = await repository.list()

    assert len(results) == 2
    assert results[0] is genome1
    assert results[1] is genome2


@pytest.mark.asyncio
async def test_list_order_by_desc(repository: GenomeRepository, mock_session: AsyncMock) -> None:
    scalars_result = MagicMock()
    scalars_result.all.return_value = []
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_result
    mock_session.execute.return_value = result_mock

    await repository.list()

    stmt = mock_session.execute.call_args[0][0]
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "ORDER BY" in compiled.upper()
    assert "genomes.created_at" in compiled.lower()


@pytest.mark.asyncio
async def test_list_empty(repository: GenomeRepository, mock_session: AsyncMock) -> None:
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
async def test_update_not_found(
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
async def test_update_duplicate_accession(
    repository: GenomeRepository,
    mock_session: AsyncMock,
) -> None:
    genome_id = uuid.uuid4()
    existing = Genome(
        id=genome_id,
        accession="GCF_000001405.40",
        organism="Homo sapiens",
    )
    mock_session.get.return_value = existing
    mock_session.commit.side_effect = IntegrityError("test", "orig", "dup")

    data = GenomeUpdate(accession="GCF_000002409.10")
    with pytest.raises(DuplicateGenomeAccessionError):
        await repository.update(genome_id, data)

    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


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
async def test_delete_not_found(
    repository: GenomeRepository,
    mock_session: AsyncMock,
) -> None:
    genome_id = uuid.uuid4()
    mock_session.get.return_value = None

    result = await repository.delete(genome_id)

    assert result is False
    mock_session.delete.assert_not_called()
    mock_session.commit.assert_not_called()
