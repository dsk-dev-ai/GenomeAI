from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from genomeai_api.exceptions import DuplicateProjectError, InvalidForeignKeyError
from genomeai_api.models.project import Project
from genomeai_api.repositories.project import ProjectRepository
from genomeai_api.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)
from genomeai_api.services.project import ProjectService


@pytest.fixture
def mock_repository() -> AsyncMock:
    return AsyncMock(spec=ProjectRepository)


@pytest.fixture
def service(mock_repository: AsyncMock) -> ProjectService:
    return ProjectService(mock_repository)


def _make_project(**overrides: object) -> Project:
    return Project(
        project_id=overrides.get("project_id", "PRJ-001"),
        project_name=overrides.get("project_name", "Genome project"),
        id=overrides.get("id", uuid.uuid4()),
        created_at=overrides.get("created_at", datetime.now(UTC)),
        updated_at=overrides.get("updated_at", datetime.now(UTC)),
    )


@pytest.mark.asyncio
async def test_create(service: ProjectService, mock_repository: AsyncMock) -> None:
    project = _make_project()
    mock_repository.create.return_value = project

    data = ProjectCreate(
        project_id="PRJ-001",
        project_name="Genome project",
    )
    result = await service.create(data)

    assert isinstance(result, ProjectResponse)
    assert result.project_id == "PRJ-001"
    mock_repository.create.assert_awaited_once_with(data)


@pytest.mark.asyncio
async def test_create_duplicate_project(
    service: ProjectService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.create.side_effect = DuplicateProjectError()

    data = ProjectCreate(
        project_id="PRJ-001",
        project_name="Genome project",
    )
    with pytest.raises(DuplicateProjectError):
        await service.create(data)


@pytest.mark.asyncio
async def test_create_foreign_key_violation(
    service: ProjectService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.create.side_effect = InvalidForeignKeyError()

    data = ProjectCreate(
        project_id="PRJ-001",
        project_name="Genome project",
        genome_id=uuid.uuid4(),
    )
    with pytest.raises(InvalidForeignKeyError):
        await service.create(data)


@pytest.mark.asyncio
async def test_get_by_id_found(
    service: ProjectService, mock_repository: AsyncMock
) -> None:
    project = _make_project()
    mock_repository.get_by_id.return_value = project

    result = await service.get_by_id(project.id)

    assert isinstance(result, ProjectResponse)
    assert result.id == project.id
    mock_repository.get_by_id.assert_awaited_once_with(project.id)


@pytest.mark.asyncio
async def test_get_by_id_not_found(
    service: ProjectService, mock_repository: AsyncMock
) -> None:
    project_id = uuid.uuid4()
    mock_repository.get_by_id.return_value = None

    result = await service.get_by_id(project_id)

    assert result is None


@pytest.mark.asyncio
async def test_list(service: ProjectService, mock_repository: AsyncMock) -> None:
    projects = [_make_project(), _make_project()]
    mock_repository.list.return_value = projects

    results = await service.list()

    assert len(results) == 2
    assert all(isinstance(r, ProjectResponse) for r in results)


@pytest.mark.asyncio
async def test_list_empty(service: ProjectService, mock_repository: AsyncMock) -> None:
    mock_repository.list.return_value = []

    results = await service.list()

    assert results == []


@pytest.mark.asyncio
async def test_update_found(
    service: ProjectService, mock_repository: AsyncMock
) -> None:
    project = _make_project()
    mock_repository.update.return_value = project

    data = ProjectUpdate(project_name="Updated project")
    result = await service.update(project.id, data)

    assert isinstance(result, ProjectResponse)
    mock_repository.update.assert_awaited_once_with(project.id, data)


@pytest.mark.asyncio
async def test_update_not_found(
    service: ProjectService, mock_repository: AsyncMock
) -> None:
    project_id = uuid.uuid4()
    mock_repository.update.return_value = None

    data = ProjectUpdate(project_name="Updated project")
    result = await service.update(project_id, data)

    assert result is None


@pytest.mark.asyncio
async def test_update_duplicate_project(
    service: ProjectService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.update.side_effect = DuplicateProjectError()

    project_id = uuid.uuid4()
    data = ProjectUpdate(project_id="PRJ-002")
    with pytest.raises(DuplicateProjectError):
        await service.update(project_id, data)


@pytest.mark.asyncio
async def test_delete_found(
    service: ProjectService, mock_repository: AsyncMock
) -> None:
    project_id = uuid.uuid4()
    mock_repository.delete.return_value = True

    result = await service.delete(project_id)

    assert result is True
    mock_repository.delete.assert_awaited_once_with(project_id)


@pytest.mark.asyncio
async def test_delete_not_found(
    service: ProjectService, mock_repository: AsyncMock
) -> None:
    project_id = uuid.uuid4()
    mock_repository.delete.return_value = False

    result = await service.delete(project_id)

    assert result is False


@pytest.mark.asyncio
async def test_exists_true(
    service: ProjectService, mock_repository: AsyncMock
) -> None:
    project_id = uuid.uuid4()
    mock_repository.exists.return_value = True

    result = await service.exists(project_id)

    assert result is True
    mock_repository.exists.assert_awaited_once_with(project_id)


@pytest.mark.asyncio
async def test_exists_false(
    service: ProjectService, mock_repository: AsyncMock
) -> None:
    project_id = uuid.uuid4()
    mock_repository.exists.return_value = False

    result = await service.exists(project_id)

    assert result is False
