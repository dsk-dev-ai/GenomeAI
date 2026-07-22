from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from genomeai_api.exceptions import DuplicateGeneError
from genomeai_api.models.gene import Gene
from genomeai_api.repositories.gene import GeneRepository
from genomeai_api.schemas.gene import GeneCreate, GeneUpdate
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repository(mock_session: AsyncMock) -> GeneRepository:
    return GeneRepository(mock_session)


@pytest.mark.asyncio
async def test_create_gene(repository: GeneRepository, mock_session: AsyncMock) -> None:
    data = GeneCreate(
        gene_id="ENSG00000139618",
        gene_name="TP53",
        chromosome="17",
    )
    result = await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
    assert isinstance(result, Gene)
    assert result.gene_id == "ENSG00000139618"


@pytest.mark.asyncio
async def test_create_duplicate_gene(
    repository: GeneRepository,
    mock_session: AsyncMock,
) -> None:
    orig = MagicMock()
    orig.sqlstate = "23505"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = GeneCreate(
        gene_id="ENSG00000139618",
        gene_name="TP53",
        chromosome="17",
    )

    with pytest.raises(DuplicateGeneError):
        await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_get_by_id_found(repository: GeneRepository, mock_session: AsyncMock) -> None:
    gene_id = uuid.uuid4()
    expected = Gene(
        id=gene_id,
        gene_id="ENSG00000139618",
        gene_name="TP53",
        chromosome="17",
    )
    mock_session.get.return_value = expected

    result = await repository.get_by_id(gene_id)

    mock_session.get.assert_awaited_once_with(Gene, gene_id)
    assert result is expected


@pytest.mark.asyncio
async def test_get_by_id_not_found(repository: GeneRepository, mock_session: AsyncMock) -> None:
    gene_id = uuid.uuid4()
    mock_session.get.return_value = None

    result = await repository.get_by_id(gene_id)

    assert result is None


@pytest.mark.asyncio
async def test_list_multiple(repository: GeneRepository, mock_session: AsyncMock) -> None:
    gene1 = Gene(id=uuid.uuid4(), gene_id="ENSG00000139618", gene_name="TP53", chromosome="17")
    gene2 = Gene(id=uuid.uuid4(), gene_id="ENSG00000141510", gene_name="BRCA1", chromosome="17")
    scalars_result = MagicMock()
    scalars_result.all.return_value = [gene1, gene2]
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_result
    mock_session.execute.return_value = result_mock

    results = await repository.list()

    assert len(results) == 2
    assert results[0] is gene1
    assert results[1] is gene2


@pytest.mark.asyncio
async def test_list_order_by_desc(repository: GeneRepository, mock_session: AsyncMock) -> None:
    scalars_result = MagicMock()
    scalars_result.all.return_value = []
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_result
    mock_session.execute.return_value = result_mock

    await repository.list()

    stmt = mock_session.execute.call_args[0][0]
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "ORDER BY" in compiled.upper()
    assert "genes.created_at" in compiled.lower()


@pytest.mark.asyncio
async def test_list_empty(repository: GeneRepository, mock_session: AsyncMock) -> None:
    scalars_result = MagicMock()
    scalars_result.all.return_value = []
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_result
    mock_session.execute.return_value = result_mock

    results = await repository.list()

    assert results == []


@pytest.mark.asyncio
async def test_update_found(repository: GeneRepository, mock_session: AsyncMock) -> None:
    gene_id = uuid.uuid4()
    existing = Gene(
        id=gene_id,
        gene_id="ENSG00000139618",
        gene_name="TP53",
        chromosome="17",
    )
    mock_session.get.return_value = existing

    data = GeneUpdate(gene_name="BRCA1")
    result = await repository.update(gene_id, data)

    mock_session.get.assert_awaited_once_with(Gene, gene_id)
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
    assert result is not None
    assert result is existing
    assert existing.gene_name == "BRCA1"


@pytest.mark.asyncio
async def test_update_not_found(
    repository: GeneRepository,
    mock_session: AsyncMock,
) -> None:
    gene_id = uuid.uuid4()
    mock_session.get.return_value = None

    data = GeneUpdate(gene_name="BRCA1")
    result = await repository.update(gene_id, data)

    assert result is None
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_update_duplicate_gene(
    repository: GeneRepository,
    mock_session: AsyncMock,
) -> None:
    gene_id = uuid.uuid4()
    existing = Gene(
        id=gene_id,
        gene_id="ENSG00000139618",
        gene_name="TP53",
        chromosome="17",
    )
    mock_session.get.return_value = existing
    orig = MagicMock()
    orig.sqlstate = "23505"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = GeneUpdate(gene_id="ENSG00000141510")
    with pytest.raises(DuplicateGeneError):
        await repository.update(gene_id, data)

    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_delete_found(repository: GeneRepository, mock_session: AsyncMock) -> None:
    gene_id = uuid.uuid4()
    existing = Gene(
        id=gene_id,
        gene_id="ENSG00000139618",
        gene_name="TP53",
        chromosome="17",
    )
    mock_session.get.return_value = existing

    result = await repository.delete(gene_id)

    assert result is True
    mock_session.delete.assert_called_once_with(existing)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_not_found(
    repository: GeneRepository,
    mock_session: AsyncMock,
) -> None:
    gene_id = uuid.uuid4()
    mock_session.get.return_value = None

    result = await repository.delete(gene_id)

    assert result is False
    mock_session.delete.assert_not_called()
    mock_session.commit.assert_not_called()
