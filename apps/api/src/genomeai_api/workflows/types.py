"""Shared typed vocabulary for the Workflow domain.

Values are stored as their lowercase string values in PostgreSQL. Execution
states are shared by `WorkflowRun` and `StepRun` (identical lifecycle).
Schedule states govern the Phase 7.3 scheduler lifecycle.
"""

from __future__ import annotations

from enum import StrEnum


class WorkflowStatus(StrEnum):
    """Lifecycle of a workflow *definition* (not its executions)."""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class RunState(StrEnum):
    """Execution state of one workflow run or one step run.

    Phase 7.1 only creates runs in the PENDING state; transitions exist so the
    state model is complete and testable, not because anything executes yet.
    """

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Allowed run-state transitions. Terminal states transition nowhere.
RUN_STATE_TRANSITIONS: dict[RunState, frozenset[RunState]] = {
    RunState.PENDING: frozenset({RunState.RUNNING, RunState.CANCELLED}),
    RunState.RUNNING: frozenset({RunState.SUCCEEDED, RunState.FAILED, RunState.CANCELLED}),
    RunState.SUCCEEDED: frozenset(),
    RunState.FAILED: frozenset(),
    RunState.CANCELLED: frozenset(),
}


def can_transition(current: RunState, next_state: RunState) -> bool:
    """Whether a run/step may move from `current` to `next_state`."""
    return next_state in RUN_STATE_TRANSITIONS.get(current, frozenset())


def is_terminal(state: RunState) -> bool:
    """Whether a run/step state has no outgoing transitions."""
    return len(RUN_STATE_TRANSITIONS.get(state, frozenset())) == 0


class ScheduleType(StrEnum):
    """How a schedule produces occurrences."""

    ONCE = "once"
    RECURRING = "recurring"


class ScheduleState(StrEnum):
    """Lifecycle of one schedule.

    One-time schedules complete themselves after their single occurrence;
    recurring schedules stay enabled until disabled explicitly. Disabled
    schedules never create runs; completed is terminal.
    """

    ENABLED = "enabled"
    DISABLED = "disabled"
    COMPLETED = "completed"


SCHEDULE_STATE_TRANSITIONS: dict[ScheduleState, frozenset[ScheduleState]] = {
    ScheduleState.ENABLED: frozenset({ScheduleState.DISABLED, ScheduleState.COMPLETED}),
    ScheduleState.DISABLED: frozenset({ScheduleState.ENABLED}),
    ScheduleState.COMPLETED: frozenset(),
}


def can_transition_schedule(current: ScheduleState, next_state: ScheduleState) -> bool:
    """Whether a schedule may move from `current` to `next_state`."""
    return next_state in SCHEDULE_STATE_TRANSITIONS.get(current, frozenset())


class JobState(StrEnum):
    """Lifecycle of one queued workflow-run job (Phase 7.4).

    Job state describes QUEUE processing, not workflow execution — the
    WorkflowRun row remains the sole source of truth for execution state.
    """

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


JOB_STATE_TRANSITIONS: dict[JobState, frozenset[JobState]] = {
    JobState.QUEUED: frozenset({JobState.RUNNING}),
    JobState.RUNNING: frozenset({JobState.COMPLETED, JobState.FAILED}),
    JobState.COMPLETED: frozenset(),
    JobState.FAILED: frozenset(),
}


def can_transition_job(current: JobState, next_state: JobState) -> bool:
    """Whether a queue job may move from `current` to `next_state`."""
    return next_state in JOB_STATE_TRANSITIONS.get(current, frozenset())


__all__ = [
    "JOB_STATE_TRANSITIONS",
    "RUN_STATE_TRANSITIONS",
    "SCHEDULE_STATE_TRANSITIONS",
    "JobState",
    "RunState",
    "ScheduleState",
    "ScheduleType",
    "WorkflowStatus",
    "can_transition",
    "can_transition_job",
    "can_transition_schedule",
    "is_terminal",
]
