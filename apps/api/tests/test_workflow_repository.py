from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from genomeai_api.repositories.workflow import WorkflowRepository
from genomeai_api.schemas.workflow import (
    WorkflowCreate,
    WorkflowDependencySpec,
    WorkflowStepSpec,
    WorkflowUpdate,
)
from genomeai_api.workflows.models.step_run import StepRun
from genomeai_api.workflows.models.workflow import Workflow
from genomeai_api.workflows.models.workflow_run import WorkflowRun
from genomeai_api.workflows.types import RunState, WorkflowStatus
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repository(mock_session: AsyncMock) -> WorkflowRepository:
    return WorkflowRepository(mock_session)


def _single_result(value: object) -> MagicMock:
    result = MagicMock()
    result.scalars.return_value.first.return_value = value
    return result


def _cursor_result(value: object) -> MagicMock:
    """Mock for session.execute returning CursorResult (used by UPDATE...RETURNING)."""
    result = MagicMock()
    result.scalars.return_value.first.return_value = value
    return result


def _list_result(values: list[object]) -> MagicMock:
    result = MagicMock()
    result.scalars.return_value.all.return_value = values
    return result


def _create_payload() -> WorkflowCreate:
    return WorkflowCreate(
        name="RNA pipeline",
        description="test",
        steps=[
            WorkflowStepSpec(name="fetch", step_type="ingest", position=0),
            WorkflowStepSpec(
                name="normalize", step_type="transform", configuration={"strict": True}
            ),
            WorkflowStepSpec(name="store", step_type="persist", position=2),
        ],
        dependencies=[
            WorkflowDependencySpec(from_step="fetch", to_step="normalize"),
            WorkflowDependencySpec(from_step="normalize", to_step="store"),
        ],
    )


@pytest.mark.asyncio
async def test_create_persists_workflow_with_resolved_edges(
    repository: WorkflowRepository,
    mock_session: AsyncMock,
) -> None:
    added: list[Workflow] = []
    mock_session.add.side_effect = added.append

    async def _refetch(*args: object, **kwargs: object) -> MagicMock:
        assert added, "commit-time fetch must follow add"
        return _single_result(added[0])

    mock_session.execute.side_effect = _refetch

    result = await repository.create(_create_payload())

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    assert isinstance(result, Workflow)
    assert result.name == "RNA pipeline"
    assert [step.name for step in result.steps] == ["fetch", "normalize", "store"]
    assert result.steps[0].position == 0
    assert result.steps[1].configuration == {"strict": True}

    by_name = {step.name: step for step in result.steps}
    assert len(result.dependencies) == 2
    assert result.dependencies[0].from_step_id == by_name["fetch"].id
    assert result.dependencies[0].to_step_id == by_name["normalize"].id
    assert result.dependencies[1].to_step_id == by_name["store"].id


@pytest.mark.asyncio
async def test_create_generates_eager_step_uuids(
    repository: WorkflowRepository,
    mock_session: AsyncMock,
) -> None:
    added: list[Workflow] = []
    mock_session.add.side_effect = added.append
    mock_session.execute.side_effect = lambda *a, **kw: _single_result(added[0])

    await repository.create(_create_payload())

    for step in added[0].steps:
        assert isinstance(step.id, uuid.UUID)


@pytest.mark.asyncio
async def test_get_by_id_returns_found_workflow(
    repository: WorkflowRepository,
    mock_session: AsyncMock,
) -> None:
    workflow = Workflow(name="w")
    mock_session.execute.return_value = _single_result(workflow)

    found = await repository.get_by_id(workflow.id)

    assert found is workflow
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_missing(
    repository: WorkflowRepository,
    mock_session: AsyncMock,
) -> None:
    mock_session.execute.return_value = _single_result(None)

    assert await repository.get_by_id(uuid.uuid4()) is None


@pytest.mark.asyncio
async def test_list_returns_all_workflows(
    repository: WorkflowRepository,
    mock_session: AsyncMock,
) -> None:
    workflows = [Workflow(name="a"), Workflow(name="b")]
    mock_session.execute.return_value = _list_result(workflows)

    assert await repository.list() == workflows


@pytest.mark.asyncio
async def test_update_metadata_applies_only_provided_fields(
    repository: WorkflowRepository,
    mock_session: AsyncMock,
) -> None:
    now = datetime.now(UTC)
    workflow = Workflow(
        id=uuid.uuid4(),
        name="old",
        description="d",
        version="1.2.3",
        status="draft",
        created_at=now,
        updated_at=now,
    )
    mock_session.get.return_value = workflow
    mock_session.execute.return_value = _single_result(workflow)

    data = WorkflowUpdate(name="new")
    result = await repository.update_metadata(workflow.id, data)

    assert result is workflow
    assert workflow.name == "new"
    assert workflow.description == "d"  # untouched
    assert workflow.version == "1.2.3"  # untouched
    assert workflow.status == "draft"  # untouched default
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_metadata_accepts_typed_status(
    repository: WorkflowRepository,
    mock_session: AsyncMock,
) -> None:
    workflow = Workflow(id=uuid.uuid4(), name="w")
    mock_session.get.return_value = workflow
    mock_session.execute.return_value = _single_result(workflow)

    result = await repository.update_metadata(
        workflow.id, WorkflowUpdate(status=WorkflowStatus.ACTIVE)
    )

    assert result is workflow
    assert workflow.status == WorkflowStatus.ACTIVE
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_metadata_unknown_workflow_returns_none(
    repository: WorkflowRepository,
    mock_session: AsyncMock,
) -> None:
    mock_session.get.return_value = None

    assert await repository.update_metadata(uuid.uuid4(), WorkflowUpdate(name="x")) is None
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_create_run_initializes_pending_step_runs_in_order(
    repository: WorkflowRepository,
    mock_session: AsyncMock,
) -> None:
    added: list[WorkflowRun] = []
    mock_session.add.side_effect = added.append

    async def _refetch(*args: object, **kwargs: object) -> MagicMock:
        assert added, "commit-time fetch must follow add"
        return _single_result(added[0])

    mock_session.execute.side_effect = _refetch

    workflow_id = uuid.uuid4()
    order = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]
    run = await repository.create_run(workflow_id, order)

    mock_session.commit.assert_awaited_once()
    assert isinstance(run, WorkflowRun)
    assert run.workflow_id == workflow_id
    assert [step_run.step_id for step_run in run.step_runs] == order
    assert [step_run.position for step_run in run.step_runs] == [0, 1, 2]
    assert all(isinstance(sr, StepRun) for sr in run.step_runs)
    # The pending state is applied by the column default at flush time.
    state_col = StepRun.__table__.columns["state"]
    assert state_col.server_default.arg == "pending"


@pytest.mark.asyncio
async def test_get_run_returns_found_run(
    repository: WorkflowRepository,
    mock_session: AsyncMock,
) -> None:
    run = WorkflowRun(workflow_id=uuid.uuid4())
    mock_session.execute.return_value = _single_result(run)

    assert await repository.get_run(run.id) is run


@pytest.mark.asyncio
async def test_get_run_returns_none_when_missing(
    repository: WorkflowRepository,
    mock_session: AsyncMock,
) -> None:
    mock_session.execute.return_value = _single_result(None)

    assert await repository.get_run(uuid.uuid4()) is None


# --- Phase 7.5 retry / failure methods ------------------------------------------


def _failed_run(attempt_count: int = 1) -> WorkflowRun:
    run = WorkflowRun(workflow_id=uuid.uuid4())
    run.state = "failed"
    run.attempt_count = attempt_count
    return run


@pytest.mark.asyncio
async def test_record_run_failure_appends_history_and_sets_class(
    repository: WorkflowRepository,
    mock_session: AsyncMock,
) -> None:
    run = _failed_run()
    mock_session.get.return_value = run
    failed_at = datetime.now(UTC)

    result = await repository.record_run_failure(
        run.id,
        classification="transient",
        reason="flaky",
        failed_at=failed_at,
    )

    assert result is run
    assert run.failure_class == "transient"
    assert run.error_message == "flaky"
    assert run.failure_history is not None
    assert len(run.failure_history) == 1
    assert run.failure_history[0]["class"] == "transient"
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_record_run_failure_returns_none_for_missing_run(
    repository: WorkflowRepository,
    mock_session: AsyncMock,
) -> None:
    mock_session.get.return_value = None
    result = await repository.record_run_failure(
        uuid.uuid4(), classification="permanent", reason="gone", failed_at=datetime.now(UTC)
    )
    assert result is None


@pytest.mark.asyncio
async def test_schedule_run_retry_sets_next_retry_at(
    repository: WorkflowRepository,
    mock_session: AsyncMock,
) -> None:
    run = _failed_run()
    mock_session.get.return_value = run
    target = datetime.now(UTC) + timedelta(seconds=30)

    await repository.schedule_run_retry(run.id, next_retry_at=target)

    assert run.next_retry_at == target
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_reopen_run_for_retry_moves_to_pending_and_clears_retry_metadata(
    repository: WorkflowRepository,
    mock_session: AsyncMock,
) -> None:
    run = _failed_run()
    run.next_retry_at = datetime.now(UTC)
    run.started_at = datetime.now(UTC)
    # UPDATE...RETURNING returns the UPDATED row from the DB.
    updated_run = _failed_run()
    updated_run.id = run.id
    updated_run.state = "pending"
    updated_run.next_retry_at = None
    updated_run.started_at = None
    mock_session.execute.return_value = _cursor_result(updated_run)

    result = await repository.reopen_run_for_retry(run.id)

    assert result is updated_run
    assert result.state == "pending"
    assert result.next_retry_at is None
    assert result.started_at is None
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("state", ["pending", "running", "succeeded", "cancelled"])
async def test_reopen_run_for_retry_refuses_non_failed_states(
    state: str,
    repository: WorkflowRepository,
    mock_session: AsyncMock,
) -> None:
    mock_session.execute.return_value = _cursor_result(None)

    assert await repository.reopen_run_for_retry(uuid.uuid4()) is None
    mock_session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_transition_run_to_running_increments_attempt_count(
    repository: WorkflowRepository,
    mock_session: AsyncMock,
) -> None:
    run = _failed_run(attempt_count=1)
    mock_session.get.return_value = run

    await repository.transition_run(run.id, RunState.RUNNING)

    assert run.attempt_count == 2
    assert run.next_retry_at is None
    mock_session.commit.assert_awaited_once()


# Overwrite the last transition test to use proper RunState enum
