from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from genomeai_api.exceptions import DuplicateStudyError, InvalidForeignKeyError
from genomeai_api.models.study import Study
from genomeai_api.repositories.study import StudyRepository
from genomeai_api.schemas.study import StudyCreate, StudyUpdate
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repository(mock_session: AsyncMock) -> StudyRepository:
    return StudyRepository(mock_session)


@pytest.mark.asyncio
async def test_create_study(
    repository: StudyRepository, mock_session: AsyncMock
) -> None:
    data = StudyCreate(
        study_id="STU-001",
        study_name="Cancer study",
    )
    result = await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
    assert isinstance(result, Study)
    assert result.study_id == "STU-001"


@pytest.mark.asyncio
async def test_create_duplicate_study(
    repository: StudyRepository,
    mock_session: AsyncMock,
) -> None:
    orig = MagicMock()
    orig.sqlstate = "23505"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = StudyCreate(
        study_id="STU-001",
        study_name="Cancer study",
    )

    with pytest.raises(DuplicateStudyError):
        await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_create_foreign_key_violation(
    repository: StudyRepository,
    mock_session: AsyncMock,
) -> None:
    orig = MagicMock()
    orig.sqlstate = "23503"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = StudyCreate(
        study_id="STU-001",
        study_name="Cancer study",
        genome_id=uuid.uuid4(),
    )

    with pytest.raises(InvalidForeignKeyError):
        await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_create_non_duplicate_integrity_error(
    repository: StudyRepository,
    mock_session: AsyncMock,
) -> None:
    orig = MagicMock()
    orig.sqlstate = "99999"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = StudyCreate(
        study_id="STU-001",
        study_name="Cancer study",
    )

    with pytest.raises(IntegrityError):
        await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_get_by_id_found(
    repository: StudyRepository, mock_session: AsyncMock
) -> None:
    study_id = uuid.uuid4()
    expected = Study(
        id=study_id,
        study_id="STU-001",
        study_name="Cancer study",
    )
    mock_session.get.return_value = expected

    result = await repository.get_by_id(study_id)

    mock_session.get.assert_awaited_once_with(Study, study_id)
    assert result is expected


@pytest.mark.asyncio
async def test_get_by_id_not_found(
    repository: StudyRepository,
    mock_session: AsyncMock,
) -> None:
    study_id = uuid.uuid4()
    mock_session.get.return_value = None

    result = await repository.get_by_id(study_id)

    assert result is None


@pytest.mark.asyncio
async def test_list_multiple(
    repository: StudyRepository, mock_session: AsyncMock
) -> None:
    s1 = Study(
        id=uuid.uuid4(),
        study_id="STU-001",
        study_name="Cancer study",
    )
    s2 = Study(
        id=uuid.uuid4(),
        study_id="STU-002",
        study_name="Healthy study",
    )
    scalars_result = MagicMock()
    scalars_result.all.return_value = [s1, s2]
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_result
    mock_session.execute.return_value = result_mock

    results = await repository.list()

    assert len(results) == 2
    assert results[0] is s1
    assert results[1] is s2


@pytest.mark.asyncio
async def test_list_order_by_desc(
    repository: StudyRepository,
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
    assert "studies.created_at" in compiled.lower()
    assert "DESC" in compiled.upper()


@pytest.mark.asyncio
async def test_list_empty(
    repository: StudyRepository, mock_session: AsyncMock
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
    repository: StudyRepository, mock_session: AsyncMock
) -> None:
    study_id = uuid.uuid4()
    existing = Study(
        id=study_id,
        study_id="STU-001",
        study_name="Cancer study",
    )
    mock_session.get.return_value = existing

    data = StudyUpdate(study_name="Updated study")
    result = await repository.update(study_id, data)

    mock_session.get.assert_awaited_once_with(Study, study_id)
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
    assert result is not None
    assert result is existing
    assert existing.study_name == "Updated study"


@pytest.mark.asyncio
async def test_update_not_found(
    repository: StudyRepository,
    mock_session: AsyncMock,
) -> None:
    study_id = uuid.uuid4()
    mock_session.get.return_value = None

    data = StudyUpdate(study_name="Updated study")
    result = await repository.update(study_id, data)

    assert result is None
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_update_duplicate_study(
    repository: StudyRepository,
    mock_session: AsyncMock,
) -> None:
    study_id = uuid.uuid4()
    existing = Study(
        id=study_id,
        study_id="STU-001",
        study_name="Cancer study",
    )
    mock_session.get.return_value = existing
    orig = MagicMock()
    orig.sqlstate = "23505"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = StudyUpdate(study_id="STU-002")
    with pytest.raises(DuplicateStudyError):
        await repository.update(study_id, data)

    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_update_foreign_key_violation(
    repository: StudyRepository,
    mock_session: AsyncMock,
) -> None:
    study_id = uuid.uuid4()
    existing = Study(
        id=study_id,
        study_id="STU-001",
        study_name="Cancer study",
    )
    mock_session.get.return_value = existing
    orig = MagicMock()
    orig.sqlstate = "23503"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = StudyUpdate(genome_id=uuid.uuid4())
    with pytest.raises(InvalidForeignKeyError):
        await repository.update(study_id, data)

    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_delete_found(
    repository: StudyRepository, mock_session: AsyncMock
) -> None:
    study_id = uuid.uuid4()
    existing = Study(
        id=study_id,
        study_id="STU-001",
        study_name="Cancer study",
    )
    mock_session.get.return_value = existing

    result = await repository.delete(study_id)

    assert result is True
    mock_session.delete.assert_awaited_once_with(existing)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_not_found(
    repository: StudyRepository,
    mock_session: AsyncMock,
) -> None:
    study_id = uuid.uuid4()
    mock_session.get.return_value = None

    result = await repository.delete(study_id)

    assert result is False
    mock_session.delete.assert_not_called()
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_exists_true(
    repository: StudyRepository, mock_session: AsyncMock
) -> None:
    study_id = uuid.uuid4()
    scalar_result = MagicMock()
    scalar_result.one_or_none.return_value = study_id
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalar_result
    mock_session.execute.return_value = result_mock

    result = await repository.exists(study_id)

    assert result is True


@pytest.mark.asyncio
async def test_exists_false(
    repository: StudyRepository, mock_session: AsyncMock
) -> None:
    study_id = uuid.uuid4()
    scalar_result = MagicMock()
    scalar_result.one_or_none.return_value = None
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalar_result
    mock_session.execute.return_value = result_mock

    result = await repository.exists(study_id)

    assert result is False
