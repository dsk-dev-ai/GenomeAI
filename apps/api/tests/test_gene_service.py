from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from genomeai_api.exceptions import DuplicateGeneError
from genomeai_api.models.gene import Gene
from genomeai_api.repositories.gene import GeneRepository
from genomeai_api.schemas.gene import GeneCreate, GeneResponse, GeneUpdate
from genomeai_api.services.gene import GeneService


@pytest.fixture
def mock_repository() -> AsyncMock:
    return AsyncMock(spec=GeneRepository)


@pytest.fixture
def service(mock_repository: AsyncMock) -> GeneService:
    return GeneService(mock_repository)


def _make_gene(**overrides: object) -> Gene:
    return Gene(
        gene_id=overrides.get("gene_id", "ENSG00000139618"),
        gene_name=overrides.get("gene_name", "TP53"),
        chromosome=overrides.get("chromosome", "17"),
        id=overrides.get("id", uuid.uuid4()),
        created_at=overrides.get("created_at", datetime.now(UTC)),
        updated_at=overrides.get("updated_at", datetime.now(UTC)),
    )


@pytest.mark.asyncio
async def test_create(service: GeneService, mock_repository: AsyncMock) -> None:
    gene = _make_gene()
    mock_repository.create.return_value = gene

    data = GeneCreate(gene_id="ENSG00000139618", gene_name="TP53", chromosome="17")
    result = await service.create(data)

    assert isinstance(result, GeneResponse)
    assert result.gene_id == "ENSG00000139618"
    mock_repository.create.assert_awaited_once_with(data)


@pytest.mark.asyncio
async def test_create_duplicate_gene(
    service: GeneService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.create.side_effect = DuplicateGeneError()

    data = GeneCreate(gene_id="ENSG00000139618", gene_name="TP53", chromosome="17")
    with pytest.raises(DuplicateGeneError):
        await service.create(data)


@pytest.mark.asyncio
async def test_get_by_id_found(service: GeneService, mock_repository: AsyncMock) -> None:
    gene = _make_gene()
    mock_repository.get_by_id.return_value = gene

    result = await service.get_by_id(gene.id)

    assert isinstance(result, GeneResponse)
    assert result.id == gene.id
    mock_repository.get_by_id.assert_awaited_once_with(gene.id)


@pytest.mark.asyncio
async def test_get_by_id_not_found(service: GeneService, mock_repository: AsyncMock) -> None:
    gene_id = uuid.uuid4()
    mock_repository.get_by_id.return_value = None

    result = await service.get_by_id(gene_id)

    assert result is None


@pytest.mark.asyncio
async def test_list(service: GeneService, mock_repository: AsyncMock) -> None:
    genes = [_make_gene(), _make_gene()]
    mock_repository.list.return_value = genes

    results = await service.list()

    assert len(results) == 2
    assert all(isinstance(r, GeneResponse) for r in results)


@pytest.mark.asyncio
async def test_list_empty(service: GeneService, mock_repository: AsyncMock) -> None:
    mock_repository.list.return_value = []

    results = await service.list()

    assert results == []


@pytest.mark.asyncio
async def test_update_found(service: GeneService, mock_repository: AsyncMock) -> None:
    gene = _make_gene()
    mock_repository.update.return_value = gene

    data = GeneUpdate(gene_name="BRCA1")
    result = await service.update(gene.id, data)

    assert isinstance(result, GeneResponse)
    mock_repository.update.assert_awaited_once_with(gene.id, data)


@pytest.mark.asyncio
async def test_update_not_found(service: GeneService, mock_repository: AsyncMock) -> None:
    gene_id = uuid.uuid4()
    mock_repository.update.return_value = None

    data = GeneUpdate(gene_name="BRCA1")
    result = await service.update(gene_id, data)

    assert result is None


@pytest.mark.asyncio
async def test_update_duplicate_gene(
    service: GeneService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.update.side_effect = DuplicateGeneError()

    gene_id = uuid.uuid4()
    data = GeneUpdate(gene_id="ENSG00000141510")
    with pytest.raises(DuplicateGeneError):
        await service.update(gene_id, data)


@pytest.mark.asyncio
async def test_delete_found(service: GeneService, mock_repository: AsyncMock) -> None:
    gene_id = uuid.uuid4()
    mock_repository.delete.return_value = True

    result = await service.delete(gene_id)

    assert result is True
    mock_repository.delete.assert_awaited_once_with(gene_id)


@pytest.mark.asyncio
async def test_delete_not_found(service: GeneService, mock_repository: AsyncMock) -> None:
    gene_id = uuid.uuid4()
    mock_repository.delete.return_value = False

    result = await service.delete(gene_id)

    assert result is False
