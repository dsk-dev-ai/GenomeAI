from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from genomeai_api.routes.workflows import _get_engine, _get_service, router
from genomeai_api.schemas.workflow import (
    StepRunResponse,
    WorkflowDependencyResponse,
    WorkflowResponse,
    WorkflowRunResponse,
    WorkflowStepResponse,
)
from genomeai_api.services.workflow import WorkflowService
from genomeai_api.workflows.errors import (
    WorkflowNotFoundError,
    WorkflowRunNotFoundError,
    WorkflowStateTransitionError,
    WorkflowValidationError,
)
from genomeai_api.workflows.execution.engine import DAGExecutionEngine

ERROR_STATUS = {
    WorkflowNotFoundError: status.HTTP_404_NOT_FOUND,
    WorkflowRunNotFoundError: status.HTTP_404_NOT_FOUND,
    WorkflowStateTransitionError: status.HTTP_409_CONFLICT,
}


def _workflow_response(
    step_names: tuple[str, ...] = ("A", "B"),
    edges: tuple[tuple[str, str], ...] = (("A", "B"),),
) -> WorkflowResponse:
    now = datetime.now(UTC)
    workflow_id = uuid.uuid4()
    ids = {name: uuid.uuid4() for name in step_names}
    return WorkflowResponse(
        id=workflow_id,
        name="pipeline",
        description=None,
        version="0.1.0",
        status="draft",
        created_at=now,
        updated_at=now,
        steps=[
            WorkflowStepResponse(
                id=ids[name],
                name=name,
                step_type="noop",
                configuration={},
                position=i,
            )
            for i, name in enumerate(step_names)
        ],
        dependencies=[
            WorkflowDependencyResponse(
                id=uuid.uuid4(),
                from_step_id=ids[source],
                to_step_id=ids[target],
            )
            for source, target in edges
        ],
    )


def _run_response(step_count: int = 2) -> WorkflowRunResponse:
    now = datetime.now(UTC)
    run_id = uuid.uuid4()
    return WorkflowRunResponse(
        id=run_id,
        workflow_id=uuid.uuid4(),
        state="pending",
        started_at=None,
        finished_at=None,
        error_message=None,
        created_at=now,
        step_runs=[
            StepRunResponse(
                id=uuid.uuid4(),
                run_id=run_id,
                step_id=uuid.uuid4(),
                state="pending",
                position=i,
                started_at=None,
                finished_at=None,
                output=None,
                error_message=None,
            )
            for i in range(step_count)
        ],
    )


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock(spec=WorkflowService)


@pytest.fixture
def mock_engine() -> AsyncMock:
    return AsyncMock(spec=DAGExecutionEngine)


@pytest.fixture
def client(mock_service: AsyncMock, mock_engine: AsyncMock) -> TestClient:
    app = FastAPI()
    app.include_router(router)

    for exc_type, code in ERROR_STATUS.items():
        def _make_handler(code: int):
            async def handler(request: Request, exc: Exception) -> JSONResponse:
                return JSONResponse(status_code=code, content={"detail": str(exc)})
            return handler

        app.add_exception_handler(exc_type, _make_handler(code))

    async def _validation_handler(request: Request, exc: Exception) -> JSONResponse:
        assert isinstance(exc, WorkflowValidationError)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": str(exc), "issues": exc.issues},
        )

    app.add_exception_handler(WorkflowValidationError, _validation_handler)

    async def override() -> WorkflowService:
        return mock_service  # type: ignore[return-value]

    app.dependency_overrides[_get_service] = override

    async def override_engine() -> DAGExecutionEngine:
        return mock_engine  # type: ignore[return-value]

    app.dependency_overrides[_get_engine] = override_engine
    return TestClient(app)


VALID_BODY = {
    "name": "RNA pipeline",
    "steps": [
        {"name": "fetch", "step_type": "ingest"},
        {"name": "align", "step_type": "compute"},
    ],
    "dependencies": [{"from_step": "fetch", "to_step": "align"}],
}

CYCLE_BODY = {
    "name": "broken",
    "steps": [
        {"name": "A", "step_type": "t"},
        {"name": "B", "step_type": "t"},
    ],
    "dependencies": [
        {"from_step": "A", "to_step": "B"},
        {"from_step": "B", "to_step": "A"},
    ],
}


def test_create_workflow_returns_201(client: TestClient, mock_service: AsyncMock) -> None:
    mock_service.create_workflow.return_value = _workflow_response()

    response = client.post("/workflows", json=VALID_BODY)

    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["name"] == "pipeline"
    assert [step["name"] for step in body["steps"]] == ["A", "B"]
    assert body["steps"][0]["configuration"] == {}
    assert body["dependencies"][0]["to_step_id"]


def test_create_workflow_rejects_malformed_dag_with_issue_list(
    client: TestClient,
    mock_service: AsyncMock,
) -> None:
    issues = ["cycle: Dependency cycle detected involving steps: A, B"]
    mock_service.create_workflow.side_effect = WorkflowValidationError(
        summary="Workflow 'broken' is not a valid DAG (1 issue)", issues=issues
    )

    response = client.post("/workflows", json=CYCLE_BODY)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    body = response.json()
    assert "not a valid DAG" in body["detail"]
    assert "cycle" in body["issues"][0]


def test_create_workflow_rejects_payload_without_steps(
    client: TestClient,
    mock_service: AsyncMock,
) -> None:
    response = client.post("/workflows", json={"name": "empty", "steps": []})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    mock_service.create_workflow.assert_not_called()


def test_create_workflow_rejects_self_dependency_shape(
    client: TestClient,
    mock_service: AsyncMock,
) -> None:
    mock_service.create_workflow.side_effect = WorkflowValidationError(
        summary="invalid", issues=["self-dependency: Step 'A' cannot depend on itself"]
    )

    response = client.post(
        "/workflows",
        json={
            "name": "selfy",
            "steps": [{"name": "A", "step_type": "t"}],
            "dependencies": [{"from_step": "A", "to_step": "A"}],
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_list_workflows(client: TestClient, mock_service: AsyncMock) -> None:
    mock_service.list_workflows.return_value = [_workflow_response()]

    response = client.get("/workflows")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


def test_get_workflow_returns_definition(
    client: TestClient,
    mock_service: AsyncMock,
) -> None:
    mock_service.get_workflow.return_value = _workflow_response()

    response = client.get(f"/workflows/{uuid.uuid4()}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["version"] == "0.1.0"


def test_get_missing_workflow_returns_404(
    client: TestClient,
    mock_service: AsyncMock,
) -> None:
    missing = uuid.uuid4()
    mock_service.get_workflow.side_effect = WorkflowNotFoundError(missing)

    response = client.get(f"/workflows/{missing}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_workflow_rejects_unknown_status(
    client: TestClient,
    mock_service: AsyncMock,
) -> None:
    response = client.patch(f"/workflows/{uuid.uuid4()}", json={"status": "invalid"})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    mock_service.update_workflow.assert_not_called()


def test_update_workflow_metadata(
    client: TestClient,
    mock_service: AsyncMock,
) -> None:
    updated = _workflow_response().model_copy(update={"status": "active"})
    mock_service.update_workflow.return_value = updated

    response = client.patch(f"/workflows/{uuid.uuid4()}", json={"status": "active"})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "active"


def test_update_unknown_workflow_returns_404(
    client: TestClient,
    mock_service: AsyncMock,
) -> None:
    mock_service.update_workflow.return_value = None

    response = client.patch(f"/workflows/{uuid.uuid4()}", json={"name": "x"})

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_run_returns_pending_run(
    client: TestClient,
    mock_service: AsyncMock,
) -> None:
    mock_service.create_run.return_value = _run_response()

    response = client.post(f"/workflows/{uuid.uuid4()}/runs")

    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["state"] == "pending"
    assert all(sr["state"] == "pending" for sr in body["step_runs"])
    assert [sr["position"] for sr in body["step_runs"]] == [0, 1]
    assert len(body["step_runs"]) == 2


def test_create_run_for_unknown_workflow_returns_404(
    client: TestClient,
    mock_service: AsyncMock,
) -> None:
    missing = uuid.uuid4()
    mock_service.create_run.side_effect = WorkflowNotFoundError(missing)

    response = client.post(f"/workflows/{missing}/runs")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_run_returns_state(
    client: TestClient,
    mock_service: AsyncMock,
) -> None:
    mock_service.get_run.return_value = _run_response()

    response = client.get(f"/workflows/runs/{uuid.uuid4()}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["state"] == "pending"


def test_get_missing_run_returns_404(
    client: TestClient,
    mock_service: AsyncMock,
) -> None:
    missing = uuid.uuid4()
    mock_service.get_run.side_effect = WorkflowRunNotFoundError(missing)

    response = client.get(f"/workflows/runs/{missing}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def _succeeded_run_response() -> WorkflowRunResponse:
    now = datetime.now(UTC)
    run_id = uuid.uuid4()
    step_id = uuid.uuid4()
    return WorkflowRunResponse(
        id=run_id,
        workflow_id=uuid.uuid4(),
        state="succeeded",
        started_at=now,
        finished_at=now,
        error_message=None,
        created_at=now,
        step_runs=[
            StepRunResponse(
                id=uuid.uuid4(),
                run_id=run_id,
                step_id=step_id,
                state="succeeded",
                position=0,
                started_at=now,
                finished_at=now,
                output={"rows": 3},
                error_message=None,
            )
        ],
    )


def test_execute_run_returns_terminal_run(
    client: TestClient,
    mock_engine: AsyncMock,
) -> None:
    mock_engine.execute_run.return_value = _succeeded_run_response()

    response = client.post(f"/workflows/runs/{uuid.uuid4()}/execute")

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["state"] == "succeeded"
    assert body["step_runs"][0]["state"] == "succeeded"
    assert body["step_runs"][0]["output"] == {"rows": 3}
    mock_engine.execute_run.assert_awaited_once()


def test_execute_missing_run_returns_404(
    client: TestClient,
    mock_engine: AsyncMock,
) -> None:
    missing = uuid.uuid4()
    mock_engine.execute_run.side_effect = WorkflowRunNotFoundError(missing)

    response = client.post(f"/workflows/runs/{missing}/execute")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_execute_non_pending_run_returns_409(
    client: TestClient,
    mock_engine: AsyncMock,
) -> None:
    run_id = uuid.uuid4()
    mock_engine.execute_run.side_effect = WorkflowStateTransitionError("succeeded", "running")

    response = client.post(f"/workflows/runs/{run_id}/execute")

    assert response.status_code == status.HTTP_409_CONFLICT
