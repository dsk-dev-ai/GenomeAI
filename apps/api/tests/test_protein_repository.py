from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from genomeai_api.exceptions import DuplicateProteinError
from genomeai_api.models.protein import Protein
from genomeai_api.repositories.protein import ProteinRepository
from genomeai_api.schemas.protein import ProteinCreate, ProteinUpdate
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repository(mock_session: AsyncMock) -> ProteinRepository:
    return ProteinRepository(mock_session)


@pytest.mark.asyncio
async def test_create_protein(
    repository: ProteinRepository, mock_session: AsyncMock
) -> None:
    data = ProteinCreate(
        protein_id="P04637",
        protein_name="p53",
    )
    result = await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
    assert isinstance(result, Protein)
    assert result.protein_id == "P04637"


@pytest.mark.asyncio
async def test_create_duplicate_protein(
    repository: ProteinRepository,
    mock_session: AsyncMock,
) -> None:
    orig = MagicMock()
    orig.sqlstate = "23505"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = ProteinCreate(
        protein_id="P04637",
        protein_name="p53",
    )

    with pytest.raises(DuplicateProteinError):
        await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_create_non_duplicate_integrity_error(
    repository: ProteinRepository,
    mock_session: AsyncMock,
) -> None:
    orig = MagicMock()
    orig.sqlstate = "99999"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = ProteinCreate(
        protein_id="P04637",
        protein_name="p53",
    )

    with pytest.raises(IntegrityError):
        await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_get_by_id_found(
    repository: ProteinRepository, mock_session: AsyncMock
) -> None:
    protein_id = uuid.uuid4()
    expected = Protein(
        id=protein_id,
        protein_id="P04637",
        protein_name="p53",
    )
    mock_session.get.return_value = expected

    result = await repository.get_by_id(protein_id)

    mock_session.get.assert_awaited_once_with(Protein, protein_id)
    assert result is expected


@pytest.mark.asyncio
async def test_get_by_id_not_found(
    repository: ProteinRepository,
    mock_session: AsyncMock,
) -> None:
    protein_id = uuid.uuid4()
    mock_session.get.return_value = None

    result = await repository.get_by_id(protein_id)

    assert result is None


@pytest.mark.asyncio
async def test_list_multiple(
    repository: ProteinRepository, mock_session: AsyncMock
) -> None:
    p1 = Protein(
        id=uuid.uuid4(),
        protein_id="P04637",
        protein_name="p53",
    )
    p2 = Protein(
        id=uuid.uuid4(),
        protein_id="P04638",
        protein_name="p63",
    )
    scalars_result = MagicMock()
    scalars_result.all.return_value = [p1, p2]
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_result
    mock_session.execute.return_value = result_mock

    results = await repository.list()

    assert len(results) == 2
    assert results[0] is p1
    assert results[1] is p2


@pytest.mark.asyncio
async def test_list_order_by_desc(
    repository: ProteinRepository,
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
    assert "proteins.created_at" in compiled.lower()
    assert "DESC" in compiled.upper()


@pytest.mark.asyncio
async def test_list_empty(
    repository: ProteinRepository, mock_session: AsyncMock
) -> None:
    scalars_result = MagicMock()
    scalars_result.all.return_value = []
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_result
    mock_session.execute.return_value = result_mock

    results = await repository.list()

    assert results == []


@pytest.mark.asyncio
async def test_update_found(
    repository: ProteinRepository, mock_session: AsyncMock
) -> None:
    protein_id = uuid.uuid4()
    existing = Protein(
        id=protein_id,
        protein_id="P04637",
        protein_name="p53",
    )
    mock_session.get.return_value = existing

    data = ProteinUpdate(protein_name="p53 (updated)")
    result = await repository.update(protein_id, data)

    mock_session.get.assert_awaited_once_with(Protein, protein_id)
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
    assert result is not None
    assert result is existing
    assert existing.protein_name == "p53 (updated)"


@pytest.mark.asyncio
async def test_update_not_found(
    repository: ProteinRepository,
    mock_session: AsyncMock,
) -> None:
    protein_id = uuid.uuid4()
    mock_session.get.return_value = None

    data = ProteinUpdate(protein_name="p53 (updated)")
    result = await repository.update(protein_id, data)

    assert result is None
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_update_duplicate_protein(
    repository: ProteinRepository,
    mock_session: AsyncMock,
) -> None:
    protein_id = uuid.uuid4()
    existing = Protein(
        id=protein_id,
        protein_id="P04637",
        protein_name="p53",
    )
    mock_session.get.return_value = existing
    orig = MagicMock()
    orig.sqlstate = "23505"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = ProteinUpdate(protein_id="P04638")
    with pytest.raises(DuplicateProteinError):
        await repository.update(protein_id, data)

    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_delete_found(
    repository: ProteinRepository, mock_session: AsyncMock
) -> None:
    protein_id = uuid.uuid4()
    existing = Protein(
        id=protein_id,
        protein_id="P04637",
        protein_name="p53",
    )
    mock_session.get.return_value = existing

    result = await repository.delete(protein_id)

    assert result is True
    mock_session.delete.assert_called_once_with(existing)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_not_found(
    repository: ProteinRepository,
    mock_session: AsyncMock,
) -> None:
    protein_id = uuid.uuid4()
    mock_session.get.return_value = None

    result = await repository.delete(protein_id)

    assert result is False
    mock_session.delete.assert_not_called()
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_exists_true(
    repository: ProteinRepository, mock_session: AsyncMock
) -> None:
    protein_id = uuid.uuid4()
    scalar_result = MagicMock()
    scalar_result.one_or_none.return_value = protein_id
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalar_result
    mock_session.execute.return_value = result_mock

    result = await repository.exists(protein_id)

    assert result is True


@pytest.mark.asyncio
async def test_exists_false(
    repository: ProteinRepository, mock_session: AsyncMock
) -> None:
    protein_id = uuid.uuid4()
    scalar_result = MagicMock()
    scalar_result.one_or_none.return_value = None
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalar_result
    mock_session.execute.return_value = result_mock

    result = await repository.exists(protein_id)

    assert result is False
