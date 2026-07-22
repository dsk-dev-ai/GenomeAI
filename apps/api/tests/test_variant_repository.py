from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from genomeai_api.exceptions import DuplicateVariantError
from genomeai_api.models.variant import Variant
from genomeai_api.repositories.variant import VariantRepository
from genomeai_api.schemas.variant import VariantCreate, VariantUpdate
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repository(mock_session: AsyncMock) -> VariantRepository:
    return VariantRepository(mock_session)


@pytest.mark.asyncio
async def test_create_variant(repository: VariantRepository, mock_session: AsyncMock) -> None:
    data = VariantCreate(
        variant_id="chr17_7674220_G_A",
        chromosome="17",
        position=7674220,
        ref="G",
        alt="A",
    )
    result = await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
    assert isinstance(result, Variant)
    assert result.variant_id == "chr17_7674220_G_A"


@pytest.mark.asyncio
async def test_create_duplicate_variant(
    repository: VariantRepository,
    mock_session: AsyncMock,
) -> None:
    orig = MagicMock()
    orig.sqlstate = "23505"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = VariantCreate(
        variant_id="chr17_7674220_G_A",
        chromosome="17",
        position=7674220,
        ref="G",
        alt="A",
    )

    with pytest.raises(DuplicateVariantError):
        await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_create_non_duplicate_integrity_error(
    repository: VariantRepository,
    mock_session: AsyncMock,
) -> None:
    orig = MagicMock()
    orig.sqlstate = "99999"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = VariantCreate(
        variant_id="chr17_7674220_G_A",
        chromosome="17",
        position=7674220,
        ref="G",
        alt="A",
    )

    with pytest.raises(IntegrityError):
        await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_get_by_id_found(repository: VariantRepository, mock_session: AsyncMock) -> None:
    variant_id = uuid.uuid4()
    expected = Variant(
        id=variant_id,
        variant_id="chr17_7674220_G_A",
        chromosome="17",
        position=7674220,
        ref="G",
        alt="A",
    )
    mock_session.get.return_value = expected

    result = await repository.get_by_id(variant_id)

    mock_session.get.assert_awaited_once_with(Variant, variant_id)
    assert result is expected


@pytest.mark.asyncio
async def test_get_by_id_not_found(
    repository: VariantRepository,
    mock_session: AsyncMock,
) -> None:
    variant_id = uuid.uuid4()
    mock_session.get.return_value = None

    result = await repository.get_by_id(variant_id)

    assert result is None


@pytest.mark.asyncio
async def test_list_multiple(repository: VariantRepository, mock_session: AsyncMock) -> None:
    variant1 = Variant(
        id=uuid.uuid4(),
        variant_id="chr17_7674220_G_A",
        chromosome="17",
        position=7674220,
        ref="G",
        alt="A",
    )
    variant2 = Variant(
        id=uuid.uuid4(),
        variant_id="chr17_7674221_C_T",
        chromosome="17",
        position=7674221,
        ref="C",
        alt="T",
    )
    scalars_result = MagicMock()
    scalars_result.all.return_value = [variant1, variant2]
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_result
    mock_session.execute.return_value = result_mock

    results = await repository.list()

    assert len(results) == 2
    assert results[0] is variant1
    assert results[1] is variant2


@pytest.mark.asyncio
async def test_list_order_by_desc(
    repository: VariantRepository,
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
    assert "variants.created_at" in compiled.lower()
    assert "DESC" in compiled.upper()


@pytest.mark.asyncio
async def test_list_empty(repository: VariantRepository, mock_session: AsyncMock) -> None:
    scalars_result = MagicMock()
    scalars_result.all.return_value = []
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_result
    mock_session.execute.return_value = result_mock

    results = await repository.list()

    assert results == []


@pytest.mark.asyncio
async def test_update_found(repository: VariantRepository, mock_session: AsyncMock) -> None:
    variant_id = uuid.uuid4()
    existing = Variant(
        id=variant_id,
        variant_id="chr17_7674220_G_A",
        chromosome="17",
        position=7674220,
        ref="G",
        alt="A",
    )
    mock_session.get.return_value = existing

    data = VariantUpdate(chromosome="X")
    result = await repository.update(variant_id, data)

    mock_session.get.assert_awaited_once_with(Variant, variant_id)
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
    assert result is not None
    assert result is existing
    assert existing.chromosome == "X"


@pytest.mark.asyncio
async def test_update_not_found(
    repository: VariantRepository,
    mock_session: AsyncMock,
) -> None:
    variant_id = uuid.uuid4()
    mock_session.get.return_value = None

    data = VariantUpdate(chromosome="X")
    result = await repository.update(variant_id, data)

    assert result is None
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_update_duplicate_variant(
    repository: VariantRepository,
    mock_session: AsyncMock,
) -> None:
    variant_id = uuid.uuid4()
    existing = Variant(
        id=variant_id,
        variant_id="chr17_7674220_G_A",
        chromosome="17",
        position=7674220,
        ref="G",
        alt="A",
    )
    mock_session.get.return_value = existing
    orig = MagicMock()
    orig.sqlstate = "23505"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = VariantUpdate(variant_id="chr17_7674221_C_T")
    with pytest.raises(DuplicateVariantError):
        await repository.update(variant_id, data)

    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_delete_found(repository: VariantRepository, mock_session: AsyncMock) -> None:
    variant_id = uuid.uuid4()
    existing = Variant(
        id=variant_id,
        variant_id="chr17_7674220_G_A",
        chromosome="17",
        position=7674220,
        ref="G",
        alt="A",
    )
    mock_session.get.return_value = existing

    result = await repository.delete(variant_id)

    assert result is True
    mock_session.delete.assert_called_once_with(existing)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_not_found(
    repository: VariantRepository,
    mock_session: AsyncMock,
) -> None:
    variant_id = uuid.uuid4()
    mock_session.get.return_value = None

    result = await repository.delete(variant_id)

    assert result is False
    mock_session.delete.assert_not_called()
    mock_session.commit.assert_not_called()
