from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from genomeai_api.repositories.workflow import WorkflowRepository
from genomeai_api.schemas.workflow import (
    WorkflowCreate,
    WorkflowDependencySpec,
    WorkflowResponse,
    WorkflowStepSpec,
    WorkflowUpdate,
)
from genomeai_api.services.workflow import WorkflowService
from genomeai_api.workflows.errors import (
    QueueUnavailableError,
    WorkflowNotFoundError,
    WorkflowRunNotFoundError,
    WorkflowStateTransitionError,
    WorkflowValidationError,
)
from genomeai_api.workflows.models.step_run import StepRun
from genomeai_api.workflows.models.workflow import Workflow
from genomeai_api.workflows.models.workflow_dependency import WorkflowDependency
from genomeai_api.workflows.models.workflow_run import WorkflowRun
from genomeai_api.workflows.models.workflow_step import WorkflowStep
from genomeai_api.workflows.queueing import InMemoryJobQueue


@pytest.fixture
def mock_repository() -> AsyncMock:
    return AsyncMock(spec=WorkflowRepository)


@pytest.fixture
def service(mock_repository: AsyncMock) -> WorkflowService:
    return WorkflowService(mock_repository)


def _valid_payload(
    steps: list[WorkflowStepSpec] | None = None,
    dependencies: list[WorkflowDependencySpec] | None = None,
) -> WorkflowCreate:
    return WorkflowCreate(
        name="pipeline",
        steps=steps
        or [
            WorkflowStepSpec(name="A", step_type="t"),
            WorkflowStepSpec(name="B", step_type="t"),
            WorkflowStepSpec(name="C", step_type="t"),
        ],
        dependencies=dependencies
        if dependencies is not None
        else [
            WorkflowDependencySpec(from_step="A", to_step="B"),
            WorkflowDependencySpec(from_step="B", to_step="C"),
        ],
    )


def _workflow_row(
    names: tuple[str, ...] = ("A", "B"),
    edges: tuple[tuple[str, str], ...] = (("A", "B"),),
) -> Workflow:
    now = datetime.now(UTC)
    wf = Workflow(
        id=uuid.uuid4(),
        name="pipeline",
        version="0.1.0",
        status="draft",
        created_at=now,
        updated_at=now,
    )
    by_name: dict[str, WorkflowStep] = {}
    for name in names:
        step = WorkflowStep(
            id=uuid.uuid4(),
            workflow_id=wf.id,
            name=name,
            step_type="t",
            configuration={},
            position=len(by_name),
            created_at=now,
            updated_at=now,
        )
        by_name[name] = step
        wf.steps.append(step)
    for source, target in edges:
        wf.dependencies.append(
            WorkflowDependency(
                id=uuid.uuid4(),
                workflow_id=wf.id,
                from_step_id=by_name[source].id,
                to_step_id=by_name[target].id,
                created_at=now,
            )
        )
    return wf


@pytest.mark.asyncio
async def test_create_workflow_validates_before_persisting(
    service: WorkflowService,
    mock_repository: AsyncMock,
) -> None:
    payload = _valid_payload()
    mock_repository.create.return_value = _workflow_row()

    result = await service.create_workflow(payload)

    assert isinstance(result, WorkflowResponse)
    mock_repository.create.assert_awaited_once_with(payload)


@pytest.mark.asyncio
async def test_create_rejects_cycle_without_touching_repository(
    service: WorkflowService,
    mock_repository: AsyncMock,
) -> None:
    payload = _valid_payload(
        dependencies=[
            WorkflowDependencySpec(from_step="A", to_step="B"),
            WorkflowDependencySpec(from_step="B", to_step="A"),
        ]
    )

    with pytest.raises(WorkflowValidationError) as exc_info:
        await service.create_workflow(payload)

    assert any("cycle" in issue for issue in exc_info.value.issues)
    mock_repository.create.assert_not_called()


@pytest.mark.asyncio
async def test_create_rejects_self_dependency(service: WorkflowService) -> None:
    payload = _valid_payload(
        dependencies=[WorkflowDependencySpec(from_step="A", to_step="A")]
    )
    with pytest.raises(WorkflowValidationError) as exc_info:
        await service.create_workflow(payload)
    assert any("self-dependency" in issue for issue in exc_info.value.issues)


@pytest.mark.asyncio
async def test_create_rejects_missing_reference(service: WorkflowService) -> None:
    payload = _valid_payload(
        dependencies=[WorkflowDependencySpec(from_step="A", to_step="ghost")]
    )
    with pytest.raises(WorkflowValidationError) as exc_info:
        await service.create_workflow(payload)
    assert any("missing-step" in issue for issue in exc_info.value.issues)


@pytest.mark.asyncio
async def test_create_rejects_duplicate_steps(service: WorkflowService) -> None:
    payload = _valid_payload(
        steps=[WorkflowStepSpec(name="A", step_type="t"), WorkflowStepSpec(name="A", step_type="t")]
    )
    with pytest.raises(WorkflowValidationError) as exc_info:
        await service.create_workflow(payload)
    assert any("duplicate-step" in issue for issue in exc_info.value.issues)


@pytest.mark.asyncio
async def test_get_workflow_raises_typed_error_when_missing(
    service: WorkflowService,
    mock_repository: AsyncMock,
) -> None:
    missing = uuid.uuid4()
    mock_repository.get_by_id.return_value = None

    with pytest.raises(WorkflowNotFoundError):
        await service.get_workflow(missing)

    mock_repository.get_by_id.assert_awaited_once_with(missing)


@pytest.mark.asyncio
async def test_list_workflows_maps_all_rows(
    service: WorkflowService,
    mock_repository: AsyncMock,
) -> None:
    rows = [_workflow_row(), _workflow_row(names=("X",), edges=())]
    mock_repository.list.return_value = rows

    results = await service.list_workflows()

    assert [r.name for r in results] == ["pipeline", "pipeline"]
    assert len(results[0].steps) == 2
    assert len(results[0].dependencies) == 1


@pytest.mark.asyncio
async def test_update_workflow_returns_none_when_missing(
    service: WorkflowService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.update_metadata.return_value = None

    assert await service.update_workflow(uuid.uuid4(), WorkflowUpdate(name="n")) is None


@pytest.mark.asyncio
async def test_create_run_initializes_one_pending_step_run_per_step(
    service: WorkflowService,
    mock_repository: AsyncMock,
) -> None:
    # Stored order is C,B,A but edges force A → B → C at run time.
    workflow = _workflow_row(names=("C", "B", "A"), edges=(("A", "B"), ("B", "C")))
    id_by_name = {step.name: step.id for step in workflow.steps}
    captured: dict[str, object] = {}

    async def _create_run(workflow_id: uuid.UUID, ordered_ids: list[uuid.UUID]):
        captured["workflow_id"] = workflow_id
        captured["ordered"] = ordered_ids
        run = WorkflowRun(
            id=uuid.uuid4(),
            workflow_id=workflow_id,
            state="pending",
            created_at=datetime.now(UTC),
        )
        for position, step_id in enumerate(ordered_ids):
            run.step_runs.append(
                StepRun(
                    id=uuid.uuid4(),
                    run_id=run.id,
                    step_id=step_id,
                    state="pending",
                    position=position,
                )
            )
        return run

    mock_repository.get_by_id.return_value = workflow
    mock_repository.create_run.side_effect = _create_run

    response = await service.create_run(workflow.id)

    assert captured["ordered"] == [id_by_name["A"], id_by_name["B"], id_by_name["C"]]
    assert response.state == "pending"
    assert [sr.state for sr in response.step_runs] == ["pending", "pending", "pending"]
    assert [sr.position for sr in response.step_runs] == [0, 1, 2]
    assert len(response.step_runs) == len(workflow.steps)


@pytest.mark.asyncio
async def test_create_run_unknown_workflow_raises(
    service: WorkflowService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.get_by_id.return_value = None

    with pytest.raises(WorkflowNotFoundError):
        await service.create_run(uuid.uuid4())

    mock_repository.create_run.assert_not_called()


@pytest.mark.asyncio
async def test_get_run_raises_typed_error_when_missing(
    service: WorkflowService,
    mock_repository: AsyncMock,
) -> None:
    missing = uuid.uuid4()
    mock_repository.get_run.return_value = None

    with pytest.raises(WorkflowRunNotFoundError):
        await service.get_run(missing)

    mock_repository.get_run.assert_awaited_once_with(missing)


def _run_row(state: str = "pending") -> WorkflowRun:
    return WorkflowRun(
        id=uuid.uuid4(),
        workflow_id=uuid.uuid4(),
        state=state,
        created_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_queue_run_enqueues_pending_run_and_returns_job() -> None:
    run = _run_row()
    queue = InMemoryJobQueue()
    mock_repository = AsyncMock(spec=WorkflowRepository)
    mock_repository.get_run.return_value = run
    service = WorkflowService(mock_repository, queue=queue)

    result = await service.queue_run(run.id)

    assert result.run.id == run.id
    assert result.job_id is not None
    assert await queue.depth() == 1
    mock_repository.transition_run.assert_not_called()


@pytest.mark.asyncio
async def test_queue_run_is_idempotent_for_repeated_requests() -> None:
    run = _run_row()
    queue = InMemoryJobQueue()
    mock_repository = AsyncMock(spec=WorkflowRepository)
    mock_repository.get_run.return_value = run
    service = WorkflowService(mock_repository, queue=queue)

    first = await service.queue_run(run.id)
    second = await service.queue_run(run.id)

    assert second.job_id == first.job_id
    assert await queue.depth() == 1


@pytest.mark.asyncio
async def test_queue_run_missing_run_raises_not_found(
    mock_repository: AsyncMock,
) -> None:
    mock_repository.get_run.return_value = None
    service = WorkflowService(mock_repository, queue=InMemoryJobQueue())

    with pytest.raises(WorkflowRunNotFoundError):
        await service.queue_run(uuid.uuid4())


@pytest.mark.asyncio
@pytest.mark.parametrize("state", ["cancelled", "succeeded", "failed", "running"])
async def test_queue_run_rejects_non_pending_runs_without_enqueueing(
    state: str,
) -> None:
    run = _run_row(state)
    queue = InMemoryJobQueue()
    mock_repository = AsyncMock(spec=WorkflowRepository)
    mock_repository.get_run.return_value = run
    service = WorkflowService(mock_repository, queue=queue)

    with pytest.raises(WorkflowStateTransitionError, match="queued"):
        await service.queue_run(run.id)

    assert await queue.depth() == 0


@pytest.mark.asyncio
async def test_queue_run_without_queue_configured_raises_unavailable(
    mock_repository: AsyncMock,
) -> None:
    mock_repository.get_run.return_value = _run_row()
    service = WorkflowService(mock_repository)

    with pytest.raises(QueueUnavailableError):
        await service.queue_run(uuid.uuid4())


@pytest.mark.asyncio
async def test_service_remains_constructible_without_queue(
    mock_repository: AsyncMock,
) -> None:
    # Phase 7.2 direct execution must keep working untouched.
    service = WorkflowService(mock_repository)
    assert service is not None
