from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from genomeai_api.exceptions import DuplicateProjectError, InvalidForeignKeyError
from genomeai_api.models.project import Project
from genomeai_api.repositories.project import ProjectRepository
from genomeai_api.schemas.project import ProjectCreate, ProjectUpdate
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repository(mock_session: AsyncMock) -> ProjectRepository:
    return ProjectRepository(mock_session)


@pytest.mark.asyncio
async def test_create_project(
    repository: ProjectRepository, mock_session: AsyncMock
) -> None:
    data = ProjectCreate(
        project_id="PRJ-001",
        project_name="Genome project",
    )
    result = await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
    assert isinstance(result, Project)
    assert result.project_id == "PRJ-001"


@pytest.mark.asyncio
async def test_create_duplicate_project(
    repository: ProjectRepository,
    mock_session: AsyncMock,
) -> None:
    orig = MagicMock()
    orig.sqlstate = "23505"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = ProjectCreate(
        project_id="PRJ-001",
        project_name="Genome project",
    )

    with pytest.raises(DuplicateProjectError):
        await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_create_foreign_key_violation(
    repository: ProjectRepository,
    mock_session: AsyncMock,
) -> None:
    orig = MagicMock()
    orig.sqlstate = "23503"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = ProjectCreate(
        project_id="PRJ-001",
        project_name="Genome project",
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
    repository: ProjectRepository,
    mock_session: AsyncMock,
) -> None:
    orig = MagicMock()
    orig.sqlstate = "99999"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = ProjectCreate(
        project_id="PRJ-001",
        project_name="Genome project",
    )

    with pytest.raises(IntegrityError):
        await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_get_by_id_found(
    repository: ProjectRepository, mock_session: AsyncMock
) -> None:
    project_id = uuid.uuid4()
    expected = Project(
        id=project_id,
        project_id="PRJ-001",
        project_name="Genome project",
    )
    mock_session.get.return_value = expected

    result = await repository.get_by_id(project_id)

    mock_session.get.assert_awaited_once_with(Project, project_id)
    assert result is expected


@pytest.mark.asyncio
async def test_get_by_id_not_found(
    repository: ProjectRepository,
    mock_session: AsyncMock,
) -> None:
    project_id = uuid.uuid4()
    mock_session.get.return_value = None

    result = await repository.get_by_id(project_id)

    assert result is None


@pytest.mark.asyncio
async def test_list_multiple(
    repository: ProjectRepository, mock_session: AsyncMock
) -> None:
    p1 = Project(
        id=uuid.uuid4(),
        project_id="PRJ-001",
        project_name="Genome project",
    )
    p2 = Project(
        id=uuid.uuid4(),
        project_id="PRJ-002",
        project_name="RNA project",
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
    repository: ProjectRepository,
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
    assert "projects.created_at" in compiled.lower()
    assert "DESC" in compiled.upper()


@pytest.mark.asyncio
async def test_list_empty(
    repository: ProjectRepository, mock_session: AsyncMock
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
    repository: ProjectRepository, mock_session: AsyncMock
) -> None:
    project_id = uuid.uuid4()
    existing = Project(
        id=project_id,
        project_id="PRJ-001",
        project_name="Genome project",
    )
    mock_session.get.return_value = existing

    data = ProjectUpdate(project_name="Updated project")
    result = await repository.update(project_id, data)

    mock_session.get.assert_awaited_once_with(Project, project_id)
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
    assert result is not None
    assert result is existing
    assert existing.project_name == "Updated project"


@pytest.mark.asyncio
async def test_update_not_found(
    repository: ProjectRepository,
    mock_session: AsyncMock,
) -> None:
    project_id = uuid.uuid4()
    mock_session.get.return_value = None

    data = ProjectUpdate(project_name="Updated project")
    result = await repository.update(project_id, data)

    assert result is None
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_update_duplicate_project(
    repository: ProjectRepository,
    mock_session: AsyncMock,
) -> None:
    project_id = uuid.uuid4()
    existing = Project(
        id=project_id,
        project_id="PRJ-001",
        project_name="Genome project",
    )
    mock_session.get.return_value = existing
    orig = MagicMock()
    orig.sqlstate = "23505"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = ProjectUpdate(project_id="PRJ-002")
    with pytest.raises(DuplicateProjectError):
        await repository.update(project_id, data)

    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_update_foreign_key_violation(
    repository: ProjectRepository,
    mock_session: AsyncMock,
) -> None:
    project_id = uuid.uuid4()
    existing = Project(
        id=project_id,
        project_id="PRJ-001",
        project_name="Genome project",
    )
    mock_session.get.return_value = existing
    orig = MagicMock()
    orig.sqlstate = "23503"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = ProjectUpdate(genome_id=uuid.uuid4())
    with pytest.raises(InvalidForeignKeyError):
        await repository.update(project_id, data)

    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_delete_found(
    repository: ProjectRepository, mock_session: AsyncMock
) -> None:
    project_id = uuid.uuid4()
    existing = Project(
        id=project_id,
        project_id="PRJ-001",
        project_name="Genome project",
    )
    mock_session.get.return_value = existing

    result = await repository.delete(project_id)

    assert result is True
    mock_session.delete.assert_awaited_once_with(existing)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_not_found(
    repository: ProjectRepository,
    mock_session: AsyncMock,
) -> None:
    project_id = uuid.uuid4()
    mock_session.get.return_value = None

    result = await repository.delete(project_id)

    assert result is False
    mock_session.delete.assert_not_called()
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_exists_true(
    repository: ProjectRepository, mock_session: AsyncMock
) -> None:
    project_id = uuid.uuid4()
    scalar_result = MagicMock()
    scalar_result.one_or_none.return_value = project_id
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalar_result
    mock_session.execute.return_value = result_mock

    result = await repository.exists(project_id)

    assert result is True


@pytest.mark.asyncio
async def test_exists_false(
    repository: ProjectRepository, mock_session: AsyncMock
) -> None:
    project_id = uuid.uuid4()
    scalar_result = MagicMock()
    scalar_result.one_or_none.return_value = None
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalar_result
    mock_session.execute.return_value = result_mock

    result = await repository.exists(project_id)

    assert result is False
