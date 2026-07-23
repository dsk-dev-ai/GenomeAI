from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from genomeai_api.exceptions import DuplicateExperimentError
from genomeai_api.models.experiment import Experiment
from genomeai_api.repositories.experiment import ExperimentRepository
from genomeai_api.schemas.experiment import (
    ExperimentCreate,
    ExperimentResponse,
    ExperimentUpdate,
)
from genomeai_api.services.experiment import ExperimentService


@pytest.fixture
def mock_repository() -> AsyncMock:
    return AsyncMock(spec=ExperimentRepository)


@pytest.fixture
def service(mock_repository: AsyncMock) -> ExperimentService:
    return ExperimentService(mock_repository)


def _make_experiment(**overrides: object) -> Experiment:
    return Experiment(
        experiment_id=overrides.get("experiment_id", "EXP-001"),
        experiment_name=overrides.get("experiment_name", "RNA-seq"),
        id=overrides.get("id", uuid.uuid4()),
        created_at=overrides.get("created_at", datetime.now(UTC)),
        updated_at=overrides.get("updated_at", datetime.now(UTC)),
    )


@pytest.mark.asyncio
async def test_create(service: ExperimentService, mock_repository: AsyncMock) -> None:
    experiment = _make_experiment()
    mock_repository.create.return_value = experiment

    data = ExperimentCreate(
        experiment_id="EXP-001",
        experiment_name="RNA-seq",
    )
    result = await service.create(data)

    assert isinstance(result, ExperimentResponse)
    assert result.experiment_id == "EXP-001"
    mock_repository.create.assert_awaited_once_with(data)


@pytest.mark.asyncio
async def test_create_duplicate_experiment(
    service: ExperimentService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.create.side_effect = DuplicateExperimentError()

    data = ExperimentCreate(
        experiment_id="EXP-001",
        experiment_name="RNA-seq",
    )
    with pytest.raises(DuplicateExperimentError):
        await service.create(data)


@pytest.mark.asyncio
async def test_get_by_id_found(
    service: ExperimentService, mock_repository: AsyncMock
) -> None:
    experiment = _make_experiment()
    mock_repository.get_by_id.return_value = experiment

    result = await service.get_by_id(experiment.id)

    assert isinstance(result, ExperimentResponse)
    assert result.id == experiment.id
    mock_repository.get_by_id.assert_awaited_once_with(experiment.id)


@pytest.mark.asyncio
async def test_get_by_id_not_found(
    service: ExperimentService, mock_repository: AsyncMock
) -> None:
    experiment_id = uuid.uuid4()
    mock_repository.get_by_id.return_value = None

    result = await service.get_by_id(experiment_id)

    assert result is None


@pytest.mark.asyncio
async def test_list(service: ExperimentService, mock_repository: AsyncMock) -> None:
    experiments = [_make_experiment(), _make_experiment()]
    mock_repository.list.return_value = experiments

    results = await service.list()

    assert len(results) == 2
    assert all(isinstance(r, ExperimentResponse) for r in results)


@pytest.mark.asyncio
async def test_list_empty(service: ExperimentService, mock_repository: AsyncMock) -> None:
    mock_repository.list.return_value = []

    results = await service.list()

    assert results == []


@pytest.mark.asyncio
async def test_update_found(
    service: ExperimentService, mock_repository: AsyncMock
) -> None:
    experiment = _make_experiment()
    mock_repository.update.return_value = experiment

    data = ExperimentUpdate(experiment_name="WGS")
    result = await service.update(experiment.id, data)

    assert isinstance(result, ExperimentResponse)
    mock_repository.update.assert_awaited_once_with(experiment.id, data)


@pytest.mark.asyncio
async def test_update_not_found(
    service: ExperimentService, mock_repository: AsyncMock
) -> None:
    experiment_id = uuid.uuid4()
    mock_repository.update.return_value = None

    data = ExperimentUpdate(experiment_name="WGS")
    result = await service.update(experiment_id, data)

    assert result is None


@pytest.mark.asyncio
async def test_update_duplicate_experiment(
    service: ExperimentService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.update.side_effect = DuplicateExperimentError()

    experiment_id = uuid.uuid4()
    data = ExperimentUpdate(experiment_id="EXP-002")
    with pytest.raises(DuplicateExperimentError):
        await service.update(experiment_id, data)


@pytest.mark.asyncio
async def test_delete_found(
    service: ExperimentService, mock_repository: AsyncMock
) -> None:
    experiment_id = uuid.uuid4()
    mock_repository.delete.return_value = True

    result = await service.delete(experiment_id)

    assert result is True
    mock_repository.delete.assert_awaited_once_with(experiment_id)


@pytest.mark.asyncio
async def test_delete_not_found(
    service: ExperimentService, mock_repository: AsyncMock
) -> None:
    experiment_id = uuid.uuid4()
    mock_repository.delete.return_value = False

    result = await service.delete(experiment_id)

    assert result is False


@pytest.mark.asyncio
async def test_exists_true(
    service: ExperimentService, mock_repository: AsyncMock
) -> None:
    experiment_id = uuid.uuid4()
    mock_repository.exists.return_value = True

    result = await service.exists(experiment_id)

    assert result is True
    mock_repository.exists.assert_awaited_once_with(experiment_id)


@pytest.mark.asyncio
async def test_exists_false(
    service: ExperimentService, mock_repository: AsyncMock
) -> None:
    experiment_id = uuid.uuid4()
    mock_repository.exists.return_value = False

    result = await service.exists(experiment_id)

    assert result is False
