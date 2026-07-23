from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from genomeai_api.exceptions import DuplicateExperimentError
from genomeai_api.models.experiment import Experiment
from genomeai_api.repositories.experiment import ExperimentRepository
from genomeai_api.schemas.experiment import ExperimentCreate, ExperimentUpdate
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repository(mock_session: AsyncMock) -> ExperimentRepository:
    return ExperimentRepository(mock_session)


@pytest.mark.asyncio
async def test_create_experiment(
    repository: ExperimentRepository, mock_session: AsyncMock
) -> None:
    data = ExperimentCreate(
        experiment_id="EXP-001",
        experiment_name="RNA-seq",
    )
    result = await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
    assert isinstance(result, Experiment)
    assert result.experiment_id == "EXP-001"


@pytest.mark.asyncio
async def test_create_duplicate_experiment(
    repository: ExperimentRepository,
    mock_session: AsyncMock,
) -> None:
    orig = MagicMock()
    orig.sqlstate = "23505"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = ExperimentCreate(
        experiment_id="EXP-001",
        experiment_name="RNA-seq",
    )

    with pytest.raises(DuplicateExperimentError):
        await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_create_non_duplicate_integrity_error(
    repository: ExperimentRepository,
    mock_session: AsyncMock,
) -> None:
    orig = MagicMock()
    orig.sqlstate = "99999"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = ExperimentCreate(
        experiment_id="EXP-001",
        experiment_name="RNA-seq",
    )

    with pytest.raises(IntegrityError):
        await repository.create(data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_get_by_id_found(
    repository: ExperimentRepository, mock_session: AsyncMock
) -> None:
    experiment_id = uuid.uuid4()
    expected = Experiment(
        id=experiment_id,
        experiment_id="EXP-001",
        experiment_name="RNA-seq",
    )
    mock_session.get.return_value = expected

    result = await repository.get_by_id(experiment_id)

    mock_session.get.assert_awaited_once_with(Experiment, experiment_id)
    assert result is expected


@pytest.mark.asyncio
async def test_get_by_id_not_found(
    repository: ExperimentRepository,
    mock_session: AsyncMock,
) -> None:
    experiment_id = uuid.uuid4()
    mock_session.get.return_value = None

    result = await repository.get_by_id(experiment_id)

    assert result is None


@pytest.mark.asyncio
async def test_list_multiple(
    repository: ExperimentRepository, mock_session: AsyncMock
) -> None:
    e1 = Experiment(
        id=uuid.uuid4(),
        experiment_id="EXP-001",
        experiment_name="RNA-seq",
    )
    e2 = Experiment(
        id=uuid.uuid4(),
        experiment_id="EXP-002",
        experiment_name="WGS",
    )
    scalars_result = MagicMock()
    scalars_result.all.return_value = [e1, e2]
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_result
    mock_session.execute.return_value = result_mock

    results = await repository.list()

    assert len(results) == 2
    assert results[0] is e1
    assert results[1] is e2


@pytest.mark.asyncio
async def test_list_order_by_desc(
    repository: ExperimentRepository,
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
    assert "experiments.created_at" in compiled.lower()
    assert "DESC" in compiled.upper()


@pytest.mark.asyncio
async def test_list_empty(
    repository: ExperimentRepository, mock_session: AsyncMock
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
    repository: ExperimentRepository, mock_session: AsyncMock
) -> None:
    experiment_id = uuid.uuid4()
    existing = Experiment(
        id=experiment_id,
        experiment_id="EXP-001",
        experiment_name="RNA-seq",
    )
    mock_session.get.return_value = existing

    data = ExperimentUpdate(experiment_name="WGS")
    result = await repository.update(experiment_id, data)

    mock_session.get.assert_awaited_once_with(Experiment, experiment_id)
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
    assert result is not None
    assert result is existing
    assert existing.experiment_name == "WGS"


@pytest.mark.asyncio
async def test_update_not_found(
    repository: ExperimentRepository,
    mock_session: AsyncMock,
) -> None:
    experiment_id = uuid.uuid4()
    mock_session.get.return_value = None

    data = ExperimentUpdate(experiment_name="WGS")
    result = await repository.update(experiment_id, data)

    assert result is None
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_update_duplicate_experiment(
    repository: ExperimentRepository,
    mock_session: AsyncMock,
) -> None:
    experiment_id = uuid.uuid4()
    existing = Experiment(
        id=experiment_id,
        experiment_id="EXP-001",
        experiment_name="RNA-seq",
    )
    mock_session.get.return_value = existing
    orig = MagicMock()
    orig.sqlstate = "23505"
    mock_session.commit.side_effect = IntegrityError("test", "orig", orig)

    data = ExperimentUpdate(experiment_id="EXP-002")
    with pytest.raises(DuplicateExperimentError):
        await repository.update(experiment_id, data)

    mock_session.rollback.assert_awaited_once()
    mock_session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_delete_found(
    repository: ExperimentRepository, mock_session: AsyncMock
) -> None:
    experiment_id = uuid.uuid4()
    existing = Experiment(
        id=experiment_id,
        experiment_id="EXP-001",
        experiment_name="RNA-seq",
    )
    mock_session.get.return_value = existing

    result = await repository.delete(experiment_id)

    assert result is True
    mock_session.delete.assert_called_once_with(existing)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_not_found(
    repository: ExperimentRepository,
    mock_session: AsyncMock,
) -> None:
    experiment_id = uuid.uuid4()
    mock_session.get.return_value = None

    result = await repository.delete(experiment_id)

    assert result is False
    mock_session.delete.assert_not_called()
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_exists_true(
    repository: ExperimentRepository, mock_session: AsyncMock
) -> None:
    experiment_id = uuid.uuid4()
    scalar_result = MagicMock()
    scalar_result.one_or_none.return_value = experiment_id
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalar_result
    mock_session.execute.return_value = result_mock

    result = await repository.exists(experiment_id)

    assert result is True


@pytest.mark.asyncio
async def test_exists_false(
    repository: ExperimentRepository, mock_session: AsyncMock
) -> None:
    experiment_id = uuid.uuid4()
    scalar_result = MagicMock()
    scalar_result.one_or_none.return_value = None
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalar_result
    mock_session.execute.return_value = result_mock

    result = await repository.exists(experiment_id)

    assert result is False
