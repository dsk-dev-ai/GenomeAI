"""Scheduler service (Phase 7.3).

Answers exactly one question: *which enabled schedules are due to create
WorkflowRuns?* The scheduler creates pending runs through the existing
repository and advances schedule bookkeeping — it never executes steps.
Execution stays with the DAGExecutionEngine; there is no background
worker, queue, or distributed coordination anywhere in this module.

Determinism: all time comes from an injected `Clock`; occurrence math
from an injected `OccurrenceCalculator`; evaluation order from persisted
rows. Idempotency: each created run records `(schedule_id, scheduled_for)`
and a partial unique index makes duplicate creation of the same occurrence
impossible — repeated evaluations simply skip already-handled occurrences.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from genomeai_api.repositories.schedule import ScheduleRepository
from genomeai_api.repositories.workflow import WorkflowRepository
from genomeai_api.schemas.schedule import ScheduleCreate, ScheduleResponse, ScheduleUpdate
from genomeai_api.services.workflow import ordered_step_ids
from genomeai_api.workflows.errors import (
    ScheduleNotFoundError,
    ScheduleStateTransitionError,
    ScheduleValidationError,
    WorkflowNotFoundError,
)
from genomeai_api.workflows.models.workflow_schedule import WorkflowSchedule
from genomeai_api.workflows.queueing import JobQueue
from genomeai_api.workflows.scheduling import (
    Clock,
    CronOccurrenceCalculator,
    OccurrenceCalculator,
    ScheduleSpec,
    SystemClock,
)
from genomeai_api.workflows.types import (
    ScheduleState,
    ScheduleType,
    can_transition_schedule,
)


@dataclass(frozen=True)
class EvaluationResult:
    """Outcome of one deterministic due-run detection pass."""

    evaluated_at: datetime
    created_run_ids: list[uuid.UUID] = field(default_factory=list)
    skipped_duplicates: int = 0


def spec_from_row(schedule: WorkflowSchedule) -> ScheduleSpec:
    return ScheduleSpec(
        schedule_type=ScheduleType(schedule.schedule_type),
        expression=schedule.expression,
        run_at=schedule.run_at,
        timezone_name=schedule.timezone_name,
    )


class SchedulerService:
    """Scheduling only: due detection, run creation, lifecycle bookkeeping."""

    def __init__(
        self,
        schedules: ScheduleRepository,
        workflows: WorkflowRepository,
        calculator: OccurrenceCalculator | None = None,
        clock: Clock | None = None,
        queue: JobQueue | None = None,
    ) -> None:
        self._schedules = schedules
        self._workflows = workflows
        self._calculator = calculator or CronOccurrenceCalculator()
        self._clock = clock or SystemClock()
        self._queue = queue

    async def create_schedule(
        self, workflow_id: uuid.UUID, data: ScheduleCreate
    ) -> ScheduleResponse:
        workflow = await self._workflows.get_by_id(workflow_id)
        if workflow is None:
            raise WorkflowNotFoundError(workflow_id)

        spec = self._spec(data.schedule_type, data.run_at, data.expression, data.timezone_name)
        self._validate(spec)

        now = self._clock.now()
        schedule = WorkflowSchedule(
            workflow_id=workflow_id,
            schedule_type=data.schedule_type.value,
            expression=spec.expression,
            run_at=spec.run_at,
            timezone_name=spec.timezone_name,
            next_run_at=self._next_run_at(spec, now),
        )
        created = await self._schedules.create(schedule)
        return ScheduleResponse.model_validate(created)

    async def get_schedule(self, schedule_id: uuid.UUID) -> ScheduleResponse:
        schedule = await self._require(schedule_id)
        return ScheduleResponse.model_validate(schedule)

    async def list_schedules(
        self, workflow_id: uuid.UUID | None = None
    ) -> list[ScheduleResponse]:
        rows = await self._schedules.list(workflow_id)
        return [ScheduleResponse.model_validate(row) for row in rows]

    async def update_schedule(
        self, schedule_id: uuid.UUID, data: ScheduleUpdate
    ) -> ScheduleResponse:
        schedule = await self._require(schedule_id)

        merged_run_at = data.run_at if data.run_at is not None else schedule.run_at
        merged_expression = (
            data.expression if data.expression is not None else schedule.expression
        )
        merged_timezone = (
            data.timezone_name if data.timezone_name is not None else schedule.timezone_name
        )
        spec = self._spec(
            ScheduleType(schedule.schedule_type),
            merged_run_at,
            merged_expression,
            merged_timezone,
        )
        self._validate(spec)

        updated = await self._schedules.update_fields(schedule_id, data)
        assert updated is not None  # loaded above

        if updated.state == ScheduleState.ENABLED.value:
            await self._schedules.reschedule(
                schedule_id,
                next_run_at=self._next_run_at(spec, self._clock.now()),
            )
        return ScheduleResponse.model_validate(await self._require(schedule_id))

    async def enable_schedule(self, schedule_id: uuid.UUID) -> ScheduleResponse:
        return await self._set_state(schedule_id, ScheduleState.ENABLED)

    async def disable_schedule(self, schedule_id: uuid.UUID) -> ScheduleResponse:
        return await self._set_state(schedule_id, ScheduleState.DISABLED)

    async def delete_schedule(self, schedule_id: uuid.UUID) -> bool:
        await self._require(schedule_id)
        return await self._schedules.delete(schedule_id)

    async def evaluate_due(self, now: datetime | None = None) -> EvaluationResult:
        """Creates runs for every due enabled schedule; idempotent per occurrence."""
        at = now if now is not None else self._clock.now()
        if at.tzinfo is None or at.utcoffset() is None:
            raise ValueError("evaluate_due requires a timezone-aware timestamp")

        created_run_ids: list[uuid.UUID] = []
        skipped_duplicates = 0

        for schedule in await self._schedules.list_enabled():
            if schedule.next_run_at is None or schedule.next_run_at > at:
                continue
            occurrence = schedule.next_run_at
            workflow = await self._workflows.get_by_id(schedule.workflow_id)
            if workflow is None:  # defensive; FK cascade prevents this
                continue

            run = await self._workflows.create_scheduled_run(
                workflow.id,
                ordered_step_ids(workflow),
                schedule_id=schedule.id,
                scheduled_for=occurrence,
            )
            if run is None:
                skipped_duplicates += 1
                continue

            created_run_ids.append(run.id)
            spec = spec_from_row(schedule)
            if spec.schedule_type == ScheduleType.ONCE:
                await self._schedules.record_occurrence(
                    schedule.id,
                    last_run_at=at,
                    next_run_at=None,
                    state=ScheduleState.COMPLETED.value,
                )
            else:
                await self._schedules.record_occurrence(
                    schedule.id,
                    last_run_at=at,
                    next_run_at=self._calculator.next_occurrence(spec, after=at),
                    state=ScheduleState.ENABLED.value,
                )

            # Phase 7.4: hand the fresh run to the queue AFTER bookkeeping —
            # a queue outage can then never strand schedule state. The run
            # itself stays PENDING in the DB (never lost); the worker will
            # execute it via DAGExecutionEngine. The scheduler still does
            # NOT execute anything itself.
            if self._queue is not None:
                await self._queue.enqueue(run.id)

        return EvaluationResult(
            evaluated_at=at,
            created_run_ids=created_run_ids,
            skipped_duplicates=skipped_duplicates,
        )

    async def _set_state(
        self, schedule_id: uuid.UUID, target: ScheduleState
    ) -> ScheduleResponse:
        schedule = await self._require(schedule_id)
        current = ScheduleState(schedule.state)
        if not can_transition_schedule(current, target):
            raise ScheduleStateTransitionError(current.value, target.value)

        if target == ScheduleState.ENABLED:
            # Re-arm relative to now so enabling never fires stale occurrences.
            next_run_at = self._calculator.next_occurrence(
                spec_from_row(schedule), after=self._clock.now()
            )
            await self._schedules.reschedule(schedule_id, next_run_at=next_run_at)
        # Disabling freezes the schedule as-is; its next_run_at is kept so
        # re-enabling can be inspected before the next evaluation.
        await self._schedules.set_state(schedule_id, target.value)
        return ScheduleResponse.model_validate(await self._require(schedule_id))

    async def _require(self, schedule_id: uuid.UUID) -> WorkflowSchedule:
        schedule = await self._schedules.get_by_id(schedule_id)
        if schedule is None:
            raise ScheduleNotFoundError(schedule_id)
        return schedule

    def _next_run_at(self, spec: ScheduleSpec, now: datetime) -> datetime | None:
        """Initial/re-armed next occurrence for a validated spec.

        One-time schedules keep their absolute run_at — a time already in
        the past is still due exactly once. Recurring schedules compute
        strictly after `now`, so stale occurrences never fire on arming.
        """
        if spec.schedule_type == ScheduleType.ONCE:
            return spec.run_at
        return self._calculator.next_occurrence(spec, after=now)

    @staticmethod
    def _spec(
        schedule_type: ScheduleType,
        run_at: datetime | None,
        expression: str | None,
        timezone_name: str,
    ) -> ScheduleSpec:
        return ScheduleSpec(
            schedule_type=schedule_type,
            expression=expression,
            run_at=run_at,
            timezone_name=timezone_name,
        )

    def _validate(self, spec: ScheduleSpec) -> None:
        issues = self._calculator.validate(spec)
        if issues:
            raise ScheduleValidationError(
                summary=(
                    f"Schedule configuration is invalid "
                    f"({len(issues)} issue{'s' if len(issues) != 1 else ''})"
                ),
                issues=issues,
            )


__all__ = ["EvaluationResult", "SchedulerService", "spec_from_row"]
