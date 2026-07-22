from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from genomeai_api.exceptions import DuplicateProteinError
from genomeai_api.models.protein import Protein
from genomeai_api.repositories.protein import ProteinRepository
from genomeai_api.schemas.protein import (
    ProteinCreate,
    ProteinResponse,
    ProteinUpdate,
)
from genomeai_api.services.protein import ProteinService


@pytest.fixture
def mock_repository() -> AsyncMock:
    return AsyncMock(spec=ProteinRepository)


@pytest.fixture
def service(mock_repository: AsyncMock) -> ProteinService:
    return ProteinService(mock_repository)


def _make_protein(**overrides: object) -> Protein:
    return Protein(
        protein_id=overrides.get("protein_id", "P04637"),
        protein_name=overrides.get("protein_name", "p53"),
        id=overrides.get("id", uuid.uuid4()),
        created_at=overrides.get("created_at", datetime.now(UTC)),
        updated_at=overrides.get("updated_at", datetime.now(UTC)),
    )


@pytest.mark.asyncio
async def test_create(service: ProteinService, mock_repository: AsyncMock) -> None:
    protein = _make_protein()
    mock_repository.create.return_value = protein

    data = ProteinCreate(
        protein_id="P04637",
        protein_name="p53",
    )
    result = await service.create(data)

    assert isinstance(result, ProteinResponse)
    assert result.protein_id == "P04637"
    mock_repository.create.assert_awaited_once_with(data)


@pytest.mark.asyncio
async def test_create_duplicate_protein(
    service: ProteinService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.create.side_effect = DuplicateProteinError()

    data = ProteinCreate(
        protein_id="P04637",
        protein_name="p53",
    )
    with pytest.raises(DuplicateProteinError):
        await service.create(data)


@pytest.mark.asyncio
async def test_get_by_id_found(
    service: ProteinService, mock_repository: AsyncMock
) -> None:
    protein = _make_protein()
    mock_repository.get_by_id.return_value = protein

    result = await service.get_by_id(protein.id)

    assert isinstance(result, ProteinResponse)
    assert result.id == protein.id
    mock_repository.get_by_id.assert_awaited_once_with(protein.id)


@pytest.mark.asyncio
async def test_get_by_id_not_found(
    service: ProteinService, mock_repository: AsyncMock
) -> None:
    protein_id = uuid.uuid4()
    mock_repository.get_by_id.return_value = None

    result = await service.get_by_id(protein_id)

    assert result is None


@pytest.mark.asyncio
async def test_list(service: ProteinService, mock_repository: AsyncMock) -> None:
    proteins = [_make_protein(), _make_protein()]
    mock_repository.list.return_value = proteins

    results = await service.list()

    assert len(results) == 2
    assert all(isinstance(r, ProteinResponse) for r in results)


@pytest.mark.asyncio
async def test_list_empty(service: ProteinService, mock_repository: AsyncMock) -> None:
    mock_repository.list.return_value = []

    results = await service.list()

    assert results == []


@pytest.mark.asyncio
async def test_update_found(
    service: ProteinService, mock_repository: AsyncMock
) -> None:
    protein = _make_protein()
    mock_repository.update.return_value = protein

    data = ProteinUpdate(protein_name="p53 (updated)")
    result = await service.update(protein.id, data)

    assert isinstance(result, ProteinResponse)
    mock_repository.update.assert_awaited_once_with(protein.id, data)


@pytest.mark.asyncio
async def test_update_not_found(
    service: ProteinService, mock_repository: AsyncMock
) -> None:
    protein_id = uuid.uuid4()
    mock_repository.update.return_value = None

    data = ProteinUpdate(protein_name="p53 (updated)")
    result = await service.update(protein_id, data)

    assert result is None


@pytest.mark.asyncio
async def test_update_duplicate_protein(
    service: ProteinService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.update.side_effect = DuplicateProteinError()

    protein_id = uuid.uuid4()
    data = ProteinUpdate(protein_id="P04638")
    with pytest.raises(DuplicateProteinError):
        await service.update(protein_id, data)


@pytest.mark.asyncio
async def test_delete_found(
    service: ProteinService, mock_repository: AsyncMock
) -> None:
    protein_id = uuid.uuid4()
    mock_repository.delete.return_value = True

    result = await service.delete(protein_id)

    assert result is True
    mock_repository.delete.assert_awaited_once_with(protein_id)


@pytest.mark.asyncio
async def test_delete_not_found(
    service: ProteinService, mock_repository: AsyncMock
) -> None:
    protein_id = uuid.uuid4()
    mock_repository.delete.return_value = False

    result = await service.delete(protein_id)

    assert result is False


@pytest.mark.asyncio
async def test_exists_true(
    service: ProteinService, mock_repository: AsyncMock
) -> None:
    protein_id = uuid.uuid4()
    mock_repository.exists.return_value = True

    result = await service.exists(protein_id)

    assert result is True
    mock_repository.exists.assert_awaited_once_with(protein_id)


@pytest.mark.asyncio
async def test_exists_false(
    service: ProteinService, mock_repository: AsyncMock
) -> None:
    protein_id = uuid.uuid4()
    mock_repository.exists.return_value = False

    result = await service.exists(protein_id)

    assert result is False
