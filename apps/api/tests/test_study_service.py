from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from genomeai_api.exceptions import DuplicateStudyError, InvalidForeignKeyError
from genomeai_api.models.study import Study
from genomeai_api.repositories.study import StudyRepository
from genomeai_api.schemas.study import (
    StudyCreate,
    StudyResponse,
    StudyUpdate,
)
from genomeai_api.services.study import StudyService


@pytest.fixture
def mock_repository() -> AsyncMock:
    return AsyncMock(spec=StudyRepository)


@pytest.fixture
def service(mock_repository: AsyncMock) -> StudyService:
    return StudyService(mock_repository)


def _make_study(**overrides: object) -> Study:
    return Study(
        study_id=overrides.get("study_id", "STU-001"),
        study_name=overrides.get("study_name", "Cancer study"),
        id=overrides.get("id", uuid.uuid4()),
        created_at=overrides.get("created_at", datetime.now(UTC)),
        updated_at=overrides.get("updated_at", datetime.now(UTC)),
    )


@pytest.mark.asyncio
async def test_create(service: StudyService, mock_repository: AsyncMock) -> None:
    study = _make_study()
    mock_repository.create.return_value = study

    data = StudyCreate(
        study_id="STU-001",
        study_name="Cancer study",
    )
    result = await service.create(data)

    assert isinstance(result, StudyResponse)
    assert result.study_id == "STU-001"
    mock_repository.create.assert_awaited_once_with(data)


@pytest.mark.asyncio
async def test_create_duplicate_study(
    service: StudyService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.create.side_effect = DuplicateStudyError()

    data = StudyCreate(
        study_id="STU-001",
        study_name="Cancer study",
    )
    with pytest.raises(DuplicateStudyError):
        await service.create(data)


@pytest.mark.asyncio
async def test_create_foreign_key_violation(
    service: StudyService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.create.side_effect = InvalidForeignKeyError()

    data = StudyCreate(
        study_id="STU-001",
        study_name="Cancer study",
        genome_id=uuid.uuid4(),
    )
    with pytest.raises(InvalidForeignKeyError):
        await service.create(data)


@pytest.mark.asyncio
async def test_get_by_id_found(
    service: StudyService, mock_repository: AsyncMock
) -> None:
    study = _make_study()
    mock_repository.get_by_id.return_value = study

    result = await service.get_by_id(study.id)

    assert isinstance(result, StudyResponse)
    assert result.id == study.id
    mock_repository.get_by_id.assert_awaited_once_with(study.id)


@pytest.mark.asyncio
async def test_get_by_id_not_found(
    service: StudyService, mock_repository: AsyncMock
) -> None:
    study_id = uuid.uuid4()
    mock_repository.get_by_id.return_value = None

    result = await service.get_by_id(study_id)

    assert result is None


@pytest.mark.asyncio
async def test_list(service: StudyService, mock_repository: AsyncMock) -> None:
    studies = [_make_study(), _make_study()]
    mock_repository.list.return_value = studies

    results = await service.list()

    assert len(results) == 2
    assert all(isinstance(r, StudyResponse) for r in results)


@pytest.mark.asyncio
async def test_list_empty(service: StudyService, mock_repository: AsyncMock) -> None:
    mock_repository.list.return_value = []

    results = await service.list()

    assert results == []


@pytest.mark.asyncio
async def test_update_found(
    service: StudyService, mock_repository: AsyncMock
) -> None:
    study = _make_study()
    mock_repository.update.return_value = study

    data = StudyUpdate(study_name="Updated study")
    result = await service.update(study.id, data)

    assert isinstance(result, StudyResponse)
    mock_repository.update.assert_awaited_once_with(study.id, data)


@pytest.mark.asyncio
async def test_update_not_found(
    service: StudyService, mock_repository: AsyncMock
) -> None:
    study_id = uuid.uuid4()
    mock_repository.update.return_value = None

    data = StudyUpdate(study_name="Updated study")
    result = await service.update(study_id, data)

    assert result is None


@pytest.mark.asyncio
async def test_update_duplicate_study(
    service: StudyService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.update.side_effect = DuplicateStudyError()

    study_id = uuid.uuid4()
    data = StudyUpdate(study_id="STU-002")
    with pytest.raises(DuplicateStudyError):
        await service.update(study_id, data)


@pytest.mark.asyncio
async def test_delete_found(
    service: StudyService, mock_repository: AsyncMock
) -> None:
    study_id = uuid.uuid4()
    mock_repository.delete.return_value = True

    result = await service.delete(study_id)

    assert result is True
    mock_repository.delete.assert_awaited_once_with(study_id)


@pytest.mark.asyncio
async def test_delete_not_found(
    service: StudyService, mock_repository: AsyncMock
) -> None:
    study_id = uuid.uuid4()
    mock_repository.delete.return_value = False

    result = await service.delete(study_id)

    assert result is False


@pytest.mark.asyncio
async def test_exists_true(
    service: StudyService, mock_repository: AsyncMock
) -> None:
    study_id = uuid.uuid4()
    mock_repository.exists.return_value = True

    result = await service.exists(study_id)

    assert result is True
    mock_repository.exists.assert_awaited_once_with(study_id)


@pytest.mark.asyncio
async def test_exists_false(
    service: StudyService, mock_repository: AsyncMock
) -> None:
    study_id = uuid.uuid4()
    mock_repository.exists.return_value = False

    result = await service.exists(study_id)

    assert result is False
