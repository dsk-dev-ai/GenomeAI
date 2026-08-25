from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from genomeai_api.routes.schedules import _get_scheduler, router
from genomeai_api.schemas.schedule import (
    ScheduleResponse,
)
from genomeai_api.services.scheduler import EvaluationResult
from genomeai_api.services.scheduler import (
    SchedulerService as _SchedulerService,  # noqa: F401  (spec source)
)
from genomeai_api.workflows.errors import (
    ScheduleNotFoundError,
    ScheduleStateTransitionError,
    ScheduleValidationError,
    WorkflowNotFoundError,
)

ERROR_STATUS = {
    ScheduleNotFoundError: status.HTTP_404_NOT_FOUND,
    WorkflowNotFoundError: status.HTTP_404_NOT_FOUND,
    ScheduleStateTransitionError: status.HTTP_409_CONFLICT,
}


def _schedule_response(**overrides: object) -> ScheduleResponse:
    now = datetime.now(UTC)
    payload: dict[str, object] = {
        "id": uuid.uuid4(),
        "workflow_id": uuid.uuid4(),
        "schedule_type": "recurring",
        "expression": "0 9 * * *",
        "run_at": None,
        "timezone_name": "UTC",
        "state": "enabled",
        "next_run_at": datetime(2026, 8, 25, 9, 0, tzinfo=UTC),
        "last_run_at": None,
        "created_at": now,
        "updated_at": now,
    }
    payload.update(overrides)
    return ScheduleResponse.model_validate(payload)


@pytest.fixture
def mock_scheduler() -> AsyncMock:
    return AsyncMock(spec=_SchedulerService)


@pytest.fixture
def client(mock_scheduler: AsyncMock) -> TestClient:
    app = FastAPI()
    app.include_router(router)

    for exc_type, code in ERROR_STATUS.items():
        def _make_handler(code: int):
            async def handler(request: Request, exc: Exception) -> JSONResponse:
                return JSONResponse(status_code=code, content={"detail": str(exc)})
            return handler

        app.add_exception_handler(exc_type, _make_handler(code))

    async def _validation_handler(request: Request, exc: Exception) -> JSONResponse:
        assert isinstance(exc, ScheduleValidationError)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": str(exc), "issues": exc.issues},
        )

    app.add_exception_handler(ScheduleValidationError, _validation_handler)

    async def override() -> SchedulerServiceProtocol:
        return mock_scheduler  # type: ignore[return-value]

    app.dependency_overrides[_get_scheduler] = override
    return TestClient(app)


class SchedulerServiceProtocol:
    pass


VALID_RECURRING = {"schedule_type": "recurring", "expression": "0 9 * * *"}


def test_create_schedule_returns_201(
    client: TestClient,
    mock_scheduler: AsyncMock,
) -> None:
    workflow_id = uuid.uuid4()
    mock_scheduler.create_schedule.return_value = _schedule_response(
        workflow_id=workflow_id
    )

    response = client.post(f"/workflows/{workflow_id}/schedules", json=VALID_RECURRING)

    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["workflow_id"] == str(workflow_id)
    assert body["state"] == "enabled"
    assert body["next_run_at"] is not None


def test_create_schedule_for_missing_workflow_returns_404(
    client: TestClient,
    mock_scheduler: AsyncMock,
) -> None:
    missing = uuid.uuid4()
    mock_scheduler.create_schedule.side_effect = WorkflowNotFoundError(missing)

    response = client.post(f"/workflows/{missing}/schedules", json=VALID_RECURRING)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_unmatched_path_is_not_swallowed_by_scheduler_routes(
    client: TestClient,
    mock_scheduler: AsyncMock,
) -> None:
    mock_scheduler.create_schedule.side_effect = ScheduleValidationError(
        summary="Schedule configuration is invalid (2 issues)",
        issues=[
            "invalid_expression: 'nope' is not a valid cron expression",
            "invalid_timezone: 'Mars/Base' is not a known IANA timezone",
        ],
    )

    response = client.post(
        f"/workflows/{uuid.uuid4()}",
        json={"schedule_type": "recurring", "expression": "nope", "timezone_name": "Mars/Base"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND  # wrong path -> no match


def test_create_invalid_expression_on_correct_path_is_422(
    client: TestClient,
    mock_scheduler: AsyncMock,
) -> None:
    mock_scheduler.create_schedule.side_effect = ScheduleValidationError(
        summary="Schedule configuration is invalid (1 issue)",
        issues=["invalid_expression: 'banana' is not a valid cron expression"],
    )

    response = client.post(f"/workflows/{uuid.uuid4()}/schedules", json=VALID_RECURRING)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    issues = response.json()["issues"]
    assert any(issue.startswith("invalid_expression") for issue in issues)


def test_create_rejects_unknown_schedule_type(client: TestClient) -> None:
    response = client.post(
        f"/workflows/{uuid.uuid4()}/schedules",
        json={"schedule_type": "sometimes", "expression": "0 9 * * *"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_get_schedule_returns_payload(
    client: TestClient,
    mock_scheduler: AsyncMock,
) -> None:
    schedule_id = uuid.uuid4()
    mock_scheduler.get_schedule.return_value = _schedule_response(id=schedule_id)

    response = client.get(f"/workflows/schedules/{schedule_id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(schedule_id)


def test_get_missing_schedule_returns_404(
    client: TestClient,
    mock_scheduler: AsyncMock,
) -> None:
    missing = uuid.uuid4()
    mock_scheduler.get_schedule.side_effect = ScheduleNotFoundError(missing)

    response = client.get(f"/workflows/schedules/{missing}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_list_schedules_supports_workflow_filter(
    client: TestClient,
    mock_scheduler: AsyncMock,
) -> None:
    workflow_id = uuid.uuid4()
    mock_scheduler.list_schedules.return_value = [
        _schedule_response(workflow_id=workflow_id)
    ]

    response = client.get("/workflows/schedules", params={"workflow_id": str(workflow_id)})

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    mock_scheduler.list_schedules.assert_awaited_once_with(workflow_id)


def test_update_schedule_returns_updated(
    client: TestClient,
    mock_scheduler: AsyncMock,
) -> None:
    schedule_id = uuid.uuid4()
    mock_scheduler.update_schedule.return_value = _schedule_response(
        id=schedule_id, expression="15 6 * * *"
    )

    response = client.patch(
        f"/workflows/schedules/{schedule_id}", json={"expression": "15 6 * * *"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["expression"] == "15 6 * * *"


def test_enable_and_disable_return_state(
    client: TestClient,
    mock_scheduler: AsyncMock,
) -> None:
    schedule_id = uuid.uuid4()
    mock_scheduler.enable_schedule.return_value = _schedule_response(
        id=schedule_id, state="enabled"
    )
    mock_scheduler.disable_schedule.return_value = _schedule_response(
        id=schedule_id, state="disabled"
    )

    enabled = client.post(f"/workflows/schedules/{schedule_id}/enable")
    disabled = client.post(f"/workflows/schedules/{schedule_id}/disable")

    assert enabled.json()["state"] == "enabled"
    assert disabled.json()["state"] == "disabled"


def test_enabling_completed_schedule_returns_409(
    client: TestClient,
    mock_scheduler: AsyncMock,
) -> None:
    schedule_id = uuid.uuid4()
    mock_scheduler.enable_schedule.side_effect = ScheduleStateTransitionError(
        "completed", "enabled"
    )

    response = client.post(f"/workflows/schedules/{schedule_id}/enable")

    assert response.status_code == status.HTTP_409_CONFLICT


def test_delete_schedule_returns_204_then_404(
    client: TestClient,
    mock_scheduler: AsyncMock,
) -> None:
    schedule_id = uuid.uuid4()
    mock_scheduler.delete_schedule.return_value = True

    deleted = client.delete(f"/workflows/schedules/{schedule_id}")
    assert deleted.status_code == status.HTTP_204_NO_CONTENT

    mock_scheduler.delete_schedule.return_value = False
    missing = client.delete(f"/workflows/schedules/{uuid.uuid4()}")
    assert missing.status_code == status.HTTP_404_NOT_FOUND


def test_evaluate_returns_created_run_ids(
    client: TestClient,
    mock_scheduler: AsyncMock,
) -> None:
    run_ids = [uuid.uuid4(), uuid.uuid4()]
    mock_scheduler.evaluate_due.return_value = EvaluationResult(
        evaluated_at=datetime(2026, 8, 24, 12, 0, tzinfo=UTC),
        created_run_ids=run_ids,
        skipped_duplicates=1,
    )

    response = client.post("/workflows/schedules/evaluate")

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["created_runs"] == [str(r) for r in run_ids]
    assert body["skipped_duplicates"] == 1
