from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from genomeai_api.exceptions import DuplicateVariantError
from genomeai_api.models.variant import Variant
from genomeai_api.repositories.variant import VariantRepository
from genomeai_api.schemas.variant import VariantCreate, VariantResponse, VariantUpdate
from genomeai_api.services.variant import VariantService


@pytest.fixture
def mock_repository() -> AsyncMock:
    return AsyncMock(spec=VariantRepository)


@pytest.fixture
def service(mock_repository: AsyncMock) -> VariantService:
    return VariantService(mock_repository)


def _make_variant(**overrides: object) -> Variant:
    return Variant(
        variant_id=overrides.get("variant_id", "chr17_7674220_G_A"),
        chromosome=overrides.get("chromosome", "17"),
        position=overrides.get("position", 7674220),
        ref=overrides.get("ref", "G"),
        alt=overrides.get("alt", "A"),
        id=overrides.get("id", uuid.uuid4()),
        created_at=overrides.get("created_at", datetime.now(UTC)),
        updated_at=overrides.get("updated_at", datetime.now(UTC)),
    )


@pytest.mark.asyncio
async def test_create(service: VariantService, mock_repository: AsyncMock) -> None:
    variant = _make_variant()
    mock_repository.create.return_value = variant

    data = VariantCreate(
        variant_id="chr17_7674220_G_A",
        chromosome="17",
        position=7674220,
        ref="G",
        alt="A",
    )
    result = await service.create(data)

    assert isinstance(result, VariantResponse)
    assert result.variant_id == "chr17_7674220_G_A"
    mock_repository.create.assert_awaited_once_with(data)


@pytest.mark.asyncio
async def test_create_duplicate_variant(
    service: VariantService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.create.side_effect = DuplicateVariantError()

    data = VariantCreate(
        variant_id="chr17_7674220_G_A",
        chromosome="17",
        position=7674220,
        ref="G",
        alt="A",
    )
    with pytest.raises(DuplicateVariantError):
        await service.create(data)


@pytest.mark.asyncio
async def test_get_by_id_found(service: VariantService, mock_repository: AsyncMock) -> None:
    variant = _make_variant()
    mock_repository.get_by_id.return_value = variant

    result = await service.get_by_id(variant.id)

    assert isinstance(result, VariantResponse)
    assert result.id == variant.id
    mock_repository.get_by_id.assert_awaited_once_with(variant.id)


@pytest.mark.asyncio
async def test_get_by_id_not_found(service: VariantService, mock_repository: AsyncMock) -> None:
    variant_id = uuid.uuid4()
    mock_repository.get_by_id.return_value = None

    result = await service.get_by_id(variant_id)

    assert result is None


@pytest.mark.asyncio
async def test_list(service: VariantService, mock_repository: AsyncMock) -> None:
    variants = [_make_variant(), _make_variant()]
    mock_repository.list.return_value = variants

    results = await service.list()

    assert len(results) == 2
    assert all(isinstance(r, VariantResponse) for r in results)


@pytest.mark.asyncio
async def test_list_empty(service: VariantService, mock_repository: AsyncMock) -> None:
    mock_repository.list.return_value = []

    results = await service.list()

    assert results == []


@pytest.mark.asyncio
async def test_update_found(service: VariantService, mock_repository: AsyncMock) -> None:
    variant = _make_variant()
    mock_repository.update.return_value = variant

    data = VariantUpdate(chromosome="X")
    result = await service.update(variant.id, data)

    assert isinstance(result, VariantResponse)
    mock_repository.update.assert_awaited_once_with(variant.id, data)


@pytest.mark.asyncio
async def test_update_not_found(service: VariantService, mock_repository: AsyncMock) -> None:
    variant_id = uuid.uuid4()
    mock_repository.update.return_value = None

    data = VariantUpdate(chromosome="X")
    result = await service.update(variant_id, data)

    assert result is None


@pytest.mark.asyncio
async def test_update_duplicate_variant(
    service: VariantService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.update.side_effect = DuplicateVariantError()

    variant_id = uuid.uuid4()
    data = VariantUpdate(variant_id="chr17_7674221_C_T")
    with pytest.raises(DuplicateVariantError):
        await service.update(variant_id, data)


@pytest.mark.asyncio
async def test_delete_found(service: VariantService, mock_repository: AsyncMock) -> None:
    variant_id = uuid.uuid4()
    mock_repository.delete.return_value = True

    result = await service.delete(variant_id)

    assert result is True
    mock_repository.delete.assert_awaited_once_with(variant_id)


@pytest.mark.asyncio
async def test_delete_not_found(service: VariantService, mock_repository: AsyncMock) -> None:
    variant_id = uuid.uuid4()
    mock_repository.delete.return_value = False

    result = await service.delete(variant_id)

    assert result is False
