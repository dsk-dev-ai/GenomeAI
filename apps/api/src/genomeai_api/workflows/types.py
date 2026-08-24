"""Shared typed vocabulary for the Workflow Foundation.

Values are stored as their lowercase string values in PostgreSQL. Execution
states are shared by `WorkflowRun` and `StepRun` (identical lifecycle).
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


__all__ = [
    "RUN_STATE_TRANSITIONS",
    "RunState",
    "WorkflowStatus",
    "can_transition",
    "is_terminal",
]
