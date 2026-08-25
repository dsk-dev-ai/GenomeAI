"""SchedulerService tests against in-memory fakes with a fixed clock.

The service must never execute steps — these tests also pin that
boundary: only run creation happens here.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import pytest
from genomeai_api.repositories.schedule import ScheduleUpdate
from genomeai_api.schemas.schedule import ScheduleCreate
from genomeai_api.services.scheduler import SchedulerService
from genomeai_api.workflows.errors import (
    ScheduleNotFoundError,
    ScheduleStateTransitionError,
    ScheduleValidationError,
    WorkflowNotFoundError,
)
from genomeai_api.workflows.models.step_run import StepRun
from genomeai_api.workflows.models.workflow import Workflow
from genomeai_api.workflows.models.workflow_dependency import WorkflowDependency
from genomeai_api.workflows.models.workflow_run import WorkflowRun
from genomeai_api.workflows.models.workflow_schedule import WorkflowSchedule
from genomeai_api.workflows.models.workflow_step import WorkflowStep
from genomeai_api.workflows.queueing import InMemoryJobQueue


@dataclass
class FakeClock:
    moment: datetime = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self.moment


@dataclass
class FakeScheduleRepository:
    rows: dict[uuid.UUID, WorkflowSchedule] = field(default_factory=dict)

    async def create(self, schedule: WorkflowSchedule) -> WorkflowSchedule:
        # Emulate flush-time server/python defaults the real DB applies.
        if schedule.id is None:
            schedule.id = uuid.uuid4()
        if schedule.state is None:
            schedule.state = "enabled"
        if schedule.timezone_name is None:
            schedule.timezone_name = "UTC"
        now = datetime.now(UTC)
        if schedule.created_at is None:
            schedule.created_at = now
        if schedule.updated_at is None:
            schedule.updated_at = now
        self.rows[schedule.id] = schedule
        return schedule

    async def get_by_id(self, schedule_id: uuid.UUID) -> WorkflowSchedule | None:
        return self.rows.get(schedule_id)

    async def list(self, workflow_id: uuid.UUID | None = None) -> list[WorkflowSchedule]:
        return [
            row
            for row in self.rows.values()
            if workflow_id is None or row.workflow_id == workflow_id
        ]

    async def list_enabled(self) -> list[WorkflowSchedule]:
        return [row for row in self.rows.values() if row.state == "enabled"]

    async def update_fields(
        self, schedule_id: uuid.UUID, data: ScheduleUpdate
    ) -> WorkflowSchedule | None:
        row = self.rows.get(schedule_id)
        if row is None:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(row, key, value)
        return row

    async def reschedule(
        self, schedule_id: uuid.UUID, *, next_run_at: datetime | None
    ) -> None:
        self.rows[schedule_id].next_run_at = next_run_at

    async def set_state(self, schedule_id: uuid.UUID, state: str) -> None:
        self.rows[schedule_id].state = state

    async def record_occurrence(
        self,
        schedule_id: uuid.UUID,
        *,
        last_run_at: datetime,
        next_run_at: datetime | None,
        state: str,
    ) -> None:
        row = self.rows[schedule_id]
        row.last_run_at = last_run_at
        row.next_run_at = next_run_at
        row.state = state

    async def delete(self, schedule_id: uuid.UUID) -> bool:
        return self.rows.pop(schedule_id, None) is not None


@dataclass
class FakeWorkflowRepository:
    workflows: dict[uuid.UUID, Workflow] = field(default_factory=dict)
    created_runs: list[WorkflowRun] = field(default_factory=list)
    duplicate_occurrences: set[tuple[uuid.UUID, datetime]] = field(default_factory=set)

    async def get_by_id(self, workflow_id: uuid.UUID) -> Workflow | None:
        return self.workflows.get(workflow_id)

    async def create_scheduled_run(
        self,
        workflow_id: uuid.UUID,
        ordered_step_ids: list[uuid.UUID],
        *,
        schedule_id: uuid.UUID,
        scheduled_for: datetime,
    ) -> WorkflowRun | None:
        key = (schedule_id, scheduled_for)
        if key in self.duplicate_occurrences:
            return None
        self.duplicate_occurrences.add(key)
        run_id = uuid.uuid4()
        run = WorkflowRun(
            id=run_id,
            workflow_id=workflow_id,
            schedule_id=schedule_id,
            scheduled_for=scheduled_for,
            state="pending",
            created_at=datetime.now(UTC),
            step_runs=[
                StepRun(
                    id=uuid.uuid4(),
                    run_id=run_id,
                    step_id=step_id,
                    state="pending",
                    position=position,
                )
                for position, step_id in enumerate(ordered_step_ids)
            ],
        )
        self.created_runs.append(run)
        return run


def _workflow(*steps: str, edges: tuple[tuple[str, str], ...] = ()) -> Workflow:
    workflow_id = uuid.uuid4()
    ids = {name: uuid.uuid4() for name in steps}
    workflow = Workflow(
        id=workflow_id, name="pipeline", version="0.1.0", status="draft"
    )
    workflow.steps = [
        WorkflowStep(
            id=ids[name],
            workflow_id=workflow_id,
            name=name,
            step_type="noop",
            position=position,
        )
        for position, name in enumerate(steps)
    ]
    workflow.dependencies = [
        WorkflowDependency(
            id=uuid.uuid4(),
            workflow_id=workflow_id,
            from_step_id=ids[source],
            to_step_id=ids[target],
        )
        for source, target in edges
    ]
    return workflow


def _service(
    schedules: FakeScheduleRepository | None = None,
    workflows: FakeWorkflowRepository | None = None,
    clock: FakeClock | None = None,
    queue: InMemoryJobQueue | None = None,
) -> tuple[SchedulerService, FakeScheduleRepository, FakeWorkflowRepository, FakeClock]:
    schedules = schedules or FakeScheduleRepository()
    workflows = workflows or FakeWorkflowRepository()
    clock = clock or FakeClock()
    service = SchedulerService(schedules, workflows, clock=clock, queue=queue)  # type: ignore[arg-type]
    return service, schedules, workflows, clock


async def _create_schedule(
    service: SchedulerService,
    workflow: Workflow,
    **payload: Any,
) -> uuid.UUID:
    response = await service.create_schedule(workflow.id, ScheduleCreate(**payload))
    return response.id


# --- creation & validation ---------------------------------------------


@pytest.mark.asyncio
async def test_create_one_time_schedule_computes_next_run() -> None:
    service, _schedules, workflows, _clock = _service()
    workflow = _workflow("a")
    workflows.workflows[workflow.id] = workflow
    run_at = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)

    response = await service.create_schedule(
        workflow.id, ScheduleCreate(schedule_type="once", run_at=run_at)
    )

    assert response.state == "enabled"
    assert response.schedule_type == "once"
    assert response.next_run_at == run_at
    assert response.last_run_at is None
    assert response.timezone_name == "UTC"


@pytest.mark.asyncio
async def test_create_recurring_schedule_computes_first_occurrence() -> None:
    service, _schedules, workflows, clock = _service()
    clock.moment = datetime(2026, 8, 24, 10, 30, tzinfo=UTC)
    workflow = _workflow("a")
    workflows.workflows[workflow.id] = workflow

    response = await service.create_schedule(
        workflow.id,
        ScheduleCreate(schedule_type="recurring", expression="30 12 * * *"),
    )

    assert response.expression == "30 12 * * *"
    assert response.next_run_at == datetime(2026, 8, 24, 12, 30, tzinfo=UTC)


@pytest.mark.asyncio
async def test_create_schedule_for_missing_workflow_raises() -> None:
    service, _schedules, _workflows, _clock = _service()
    missing = uuid.uuid4()

    with pytest.raises(WorkflowNotFoundError):
        await service.create_schedule(
            missing, ScheduleCreate(schedule_type="once", run_at=_aware())
        )


def _aware() -> datetime:
    return datetime(2026, 9, 1, 8, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_create_invalid_cron_raises_validation_error() -> None:
    service, _schedules, workflows, _clock = _service()
    workflow = _workflow("a")
    workflows.workflows[workflow.id] = workflow

    with pytest.raises(ScheduleValidationError) as exc_info:
        await service.create_schedule(
            workflow.id,
            ScheduleCreate(schedule_type="recurring", expression="banana"),
        )
    assert any(issue.startswith("invalid_expression") for issue in exc_info.value.issues)


@pytest.mark.asyncio
async def test_create_invalid_timezone_raises_validation_error() -> None:
    service, _schedules, workflows, _clock = _service()
    workflow = _workflow("a")
    workflows.workflows[workflow.id] = workflow

    with pytest.raises(ScheduleValidationError):
        await service.create_schedule(
            workflow.id,
            ScheduleCreate(schedule_type="once", run_at=_aware(), timezone_name="Nowhere/Nothing"),
        )


@pytest.mark.asyncio
async def test_get_unknown_schedule_raises() -> None:
    service, _schedules, _workflows, _clock = _service()

    with pytest.raises(ScheduleNotFoundError):
        await service.get_schedule(uuid.uuid4())


# --- due detection ------------------------------------------------------


@pytest.mark.asyncio
async def test_not_due_schedule_creates_nothing() -> None:
    service, _schedules, workflows, clock = _service()
    workflow = _workflow("a")
    workflows.workflows[workflow.id] = workflow
    future = datetime(2026, 12, 1, tzinfo=UTC)
    schedule_id = await _create_schedule(
        service, workflow, schedule_type="once", run_at=future
    )

    result = await service.evaluate_due()

    assert result.created_run_ids == []
    assert result.skipped_duplicates == 0
    assert (await service.get_schedule(schedule_id)).state == "enabled"


@pytest.mark.asyncio
async def test_due_schedule_creates_pending_run() -> None:
    service, _schedules, workflows, clock = _service()
    workflow = _workflow("a", "b", "c", edges=(("a", "b"), ("b", "c")))
    workflows.workflows[workflow.id] = workflow
    past = datetime(2026, 8, 24, 6, 0, tzinfo=UTC)
    schedule_id = await _create_schedule(
        service, workflow, schedule_type="once", run_at=past
    )

    result = await service.evaluate_due()

    assert len(result.created_run_ids) == 1
    run = workflows.created_runs[0]
    assert run.workflow_id == workflow.id
    assert run.state == "pending"
    assert run.schedule_id == schedule_id
    assert run.scheduled_for == past
    # Existing execution model preserved: one pending StepRun per step in
    # topological order; the scheduler did NOT advance any states.
    assert [sr.position for sr in run.step_runs] == [0, 1, 2]
    assert all(sr.state == "pending" for sr in run.step_runs)


@pytest.mark.asyncio
async def test_exact_boundary_is_due() -> None:
    service, _schedules, workflows, clock = _service()
    clock.moment = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)
    workflow = _workflow("a")
    workflows.workflows[workflow.id] = workflow
    await _create_schedule(
        service, workflow, schedule_type="once", run_at=clock.moment
    )

    result = await service.evaluate_due(now=clock.moment)

    assert len(result.created_run_ids) == 1


@pytest.mark.asyncio
async def test_disabled_schedule_never_fires() -> None:
    service, _schedules, workflows, clock = _service()
    workflow = _workflow("a")
    workflows.workflows[workflow.id] = workflow
    schedule_id = await _create_schedule(
        service, workflow, schedule_type="once", run_at=datetime(2026, 8, 1, tzinfo=UTC)
    )
    await service.disable_schedule(schedule_id)

    result = await service.evaluate_due()

    assert result.created_run_ids == []
    assert [row for row in _schedules.rows.values()][0].state == "disabled"


@pytest.mark.asyncio
async def test_completed_one_time_schedule_never_fires_again() -> None:
    service, _schedules, workflows, clock = _service()
    workflow = _workflow("a")
    workflows.workflows[workflow.id] = workflow
    schedule_id = await _create_schedule(
        service, workflow, schedule_type="once", run_at=datetime(2026, 8, 1, tzinfo=UTC)
    )

    first = await service.evaluate_due()
    second = await service.evaluate_due()

    assert len(first.created_run_ids) == 1
    assert second.created_run_ids == []
    completed = await service.get_schedule(schedule_id)
    assert completed.state == "completed"
    assert completed.next_run_at is None
    assert completed.last_run_at == datetime(2026, 8, 24, 12, 0, tzinfo=UTC)


# --- recurring ----------------------------------------------------------


@pytest.mark.asyncio
async def test_recurring_advances_to_next_occurrence_and_stays_enabled() -> None:
    service, _schedules, workflows, clock = _service()
    clock.moment = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)  # created before the hour
    workflow = _workflow("a")
    workflows.workflows[workflow.id] = workflow
    schedule_id = await _create_schedule(
        service, workflow, schedule_type="recurring", expression="30 12 * * *"
    )

    fire_at = datetime(2026, 8, 24, 12, 30, tzinfo=UTC)
    first = await service.evaluate_due(now=fire_at)

    assert len(first.created_run_ids) == 1
    row = await service.get_schedule(schedule_id)
    assert row.state == "enabled"  # recurring stays enabled
    assert row.last_run_at == fire_at
    assert row.next_run_at == datetime(2026, 8, 25, 12, 30, tzinfo=UTC)


@pytest.mark.asyncio
async def test_recurring_produces_multiple_runs_across_days() -> None:
    service, _schedules, workflows, clock = _service()
    clock.moment = datetime(2026, 8, 24, 8, 30, tzinfo=UTC)
    workflow = _workflow("a")
    workflows.workflows[workflow.id] = workflow
    await _create_schedule(service, workflow, schedule_type="recurring", expression="0 9 * * *")

    day1 = await service.evaluate_due(now=datetime(2026, 8, 24, 9, 0, tzinfo=UTC))
    day2 = await service.evaluate_due(now=datetime(2026, 8, 25, 9, 0, tzinfo=UTC))
    day3 = await service.evaluate_due(now=datetime(2026, 8, 26, 9, 0, tzinfo=UTC))

    assert [len(day.created_run_ids) for day in (day1, day2, day3)] == [1, 1, 1]
    scheduled_for = sorted(run.scheduled_for for run in workflows.created_runs)
    assert scheduled_for == [
        datetime(2026, 8, 24, 9, 0, tzinfo=UTC),
        datetime(2026, 8, 25, 9, 0, tzinfo=UTC),
        datetime(2026, 8, 26, 9, 0, tzinfo=UTC),
    ]


@pytest.mark.asyncio
async def test_lagging_evaluation_does_not_fire_twice_per_pass() -> None:
    """Evaluating late still yields exactly one run per elapsed occurrence."""
    service, _schedules, workflows, _clock = _service()
    workflow = _workflow("a")
    workflows.workflows[workflow.id] = workflow
    # Hourly job; evaluation lags two hours behind.
    await _create_schedule(service, workflow, schedule_type="recurring", expression="0 * * * *")

    result = await service.evaluate_due(now=datetime(2026, 8, 24, 14, 0, tzinfo=UTC))

    assert len(result.created_run_ids) == 1
    row = await service.get_schedule(list(_schedules.rows)[0])
    assert row.next_run_at == datetime(2026, 8, 24, 15, 0, tzinfo=UTC)


# --- idempotency --------------------------------------------------------


@pytest.mark.asyncio
async def test_duplicate_occurrence_is_skipped_not_duplicated() -> None:
    service, schedules, workflows, _clock = _service()
    workflow = _workflow("a")
    workflows.workflows[workflow.id] = workflow
    schedule_id = await _create_schedule(
        service, workflow, schedule_type="once", run_at=datetime(2026, 8, 1, tzinfo=UTC)
    )
    # Simulate the DB unique constraint having already seen this occurrence.
    row = schedules.rows[schedule_id]
    workflows.duplicate_occurrences.add((schedule_id, row.next_run_at))

    result = await service.evaluate_due()

    assert result.created_run_ids == []
    assert result.skipped_duplicates == 1
    assert workflows.created_runs == []


@pytest.mark.asyncio
async def test_repeated_evaluation_of_same_time_creates_single_run() -> None:
    service, _schedules, workflows, clock = _service()
    clock.moment = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)
    workflow = _workflow("a")
    workflows.workflows[workflow.id] = workflow
    past = datetime(2026, 8, 24, 11, 0, tzinfo=UTC)
    await _create_schedule(service, workflow, schedule_type="once", run_at=past)

    at_boundary = datetime(2026, 8, 24, 11, 0, tzinfo=UTC)
    first = await service.evaluate_due(now=at_boundary)
    again_same_moment = await service.evaluate_due(now=at_boundary)

    assert len(first.created_run_ids) == 1
    assert again_same_moment.created_run_ids == []


@pytest.mark.asyncio
async def test_evaluate_due_rejects_naive_timestamp() -> None:
    service, _schedules, _workflows, _clock = _service()

    with pytest.raises(ValueError, match="timezone-aware"):
        await service.evaluate_due(now=datetime(2026, 8, 24, 12, 0))


# --- lifecycle ----------------------------------------------------------


@pytest.mark.asyncio
async def test_enable_disable_roundtrip() -> None:
    service, _schedules, workflows, clock = _service()
    clock.moment = datetime(2026, 8, 24, 10, 0, tzinfo=UTC)
    workflow = _workflow("a")
    workflows.workflows[workflow.id] = workflow
    schedule_id = await _create_schedule(
        service, workflow, schedule_type="recurring", expression="0 22 * * *"
    )

    disabled = await service.disable_schedule(schedule_id)
    assert disabled.state == "disabled"

    enabled = await service.enable_schedule(schedule_id)
    assert enabled.state == "enabled"
    # Re-armed relative to `now`, never firing stale occurrences.
    assert enabled.next_run_at == datetime(2026, 8, 24, 22, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_enabling_completed_schedule_is_rejected() -> None:
    service, _schedules, workflows, _clock = _service()
    workflow = _workflow("a")
    workflows.workflows[workflow.id] = workflow
    schedule_id = await _create_schedule(
        service, workflow, schedule_type="once", run_at=datetime(2026, 8, 1, tzinfo=UTC)
    )
    await service.evaluate_due()
    assert (await service.get_schedule(schedule_id)).state == "completed"

    with pytest.raises(ScheduleStateTransitionError):
        await service.enable_schedule(schedule_id)


@pytest.mark.asyncio
async def test_disabling_missing_schedule_raises() -> None:
    service, _schedules, _workflows, _clock = _service()

    with pytest.raises(ScheduleNotFoundError):
        await service.disable_schedule(uuid.uuid4())


# --- update & delete ----------------------------------------------------


@pytest.mark.asyncio
async def test_update_recomputes_next_run_for_enabled_schedule() -> None:
    service, _schedules, workflows, clock = _service()
    clock.moment = datetime(2026, 8, 24, 10, 0, tzinfo=UTC)
    workflow = _workflow("a")
    workflows.workflows[workflow.id] = workflow
    schedule_id = await _create_schedule(
        service, workflow, schedule_type="recurring", expression="0 23 * * *"
    )

    updated = await service.update_schedule(
        schedule_id, ScheduleUpdate(expression="15 6 * * *")
    )

    assert updated.expression == "15 6 * * *"
    assert updated.next_run_at == datetime(2026, 8, 25, 6, 15, tzinfo=UTC)
    assert updated.last_run_at is None  # reschedule never fabricates runs


@pytest.mark.asyncio
async def test_update_with_invalid_expression_is_rejected() -> None:
    service, _schedules, workflows, _clock = _service()
    workflow = _workflow("a")
    workflows.workflows[workflow.id] = workflow
    schedule_id = await _create_schedule(
        service, workflow, schedule_type="recurring", expression="0 23 * * *"
    )

    with pytest.raises(ScheduleValidationError):
        await service.update_schedule(
            schedule_id, ScheduleUpdate(expression="@#$%")
        )


@pytest.mark.asyncio
async def test_delete_removes_schedule() -> None:
    service, schedules, workflows, _clock = _service()
    workflow = _workflow("a")
    workflows.workflows[workflow.id] = workflow
    schedule_id = await _create_schedule(
        service, workflow, schedule_type="once", run_at=_aware()
    )

    assert await service.delete_schedule(schedule_id) is True
    assert schedules.rows == {}


# --- scheduler → queue integration (Phase 7.4) --------------------------


@pytest.mark.asyncio
async def test_due_run_is_enqueued_after_creation() -> None:
    queue = InMemoryJobQueue()
    service, _schedules, workflows, clock = _service(queue=queue)
    workflow = _workflow("a")
    workflows.workflows[workflow.id] = workflow
    past = datetime(2026, 8, 24, 6, 0, tzinfo=UTC)
    schedule_id = await _create_schedule(
        service, workflow, schedule_type="once", run_at=past
    )

    result = await service.evaluate_due(now=clock.moment)

    assert len(result.created_run_ids) == 1
    assert await queue.depth() == 1
    job = await queue.claim("probe-worker")
    assert job is not None
    assert job.workflow_run_id == result.created_run_ids[0]
    # Bookkeeping happened before enqueue: occurrence recorded, run pending.
    run = workflows.created_runs[0]
    assert run.state == "pending"
    assert run.schedule_id == schedule_id


@pytest.mark.asyncio
async def test_skipped_duplicate_schedules_enqueue_nothing() -> None:
    queue = InMemoryJobQueue()
    service, schedules, workflows, clock = _service(queue=queue)
    workflow = _workflow("a")
    workflows.workflows[workflow.id] = workflow
    clock.moment = datetime(2026, 8, 24, 11, 58, tzinfo=UTC)  # created before boundary
    schedule_id = await _create_schedule(
        service, workflow, schedule_type="recurring", expression="*/5 * * * *"
    )
    # Advance past the first cron boundary so the schedule actually fires.
    clock.moment = datetime(2026, 8, 24, 12, 3, tzinfo=UTC)

    first = await service.evaluate_due(now=clock.moment)
    assert len(first.created_run_ids) == 1
    assert await queue.depth() == 1

    # A repeated notification for the SAME occurrence must not enqueue twice:
    # simulate the DB unique constraint rejecting the next boundary on
    # re-evaluation.
    row = schedules.rows[schedule_id]
    workflows.duplicate_occurrences.add((schedule_id, row.next_run_at))
    clock.moment = datetime(2026, 8, 24, 12, 6, tzinfo=UTC)

    second = await service.evaluate_due(now=clock.moment)

    assert second.created_run_ids == []
    assert second.skipped_duplicates == 1
    assert await queue.depth() == 1  # unchanged


@pytest.mark.asyncio
async def test_scheduler_without_queue_still_creates_runs(
    mock_queue_absent_guard: None = None,
) -> None:
    del mock_queue_absent_guard
    service, _schedules, workflows, _clock = _service()
    workflow = _workflow("a")
    workflows.workflows[workflow.id] = workflow
    await _create_schedule(
        service, workflow, schedule_type="once", run_at=datetime(2026, 8, 24, 6, tzinfo=UTC)
    )

    result = await service.evaluate_due()

    assert len(result.created_run_ids) == 1
