"""Error hierarchy for the Workflow Foundation.

All workflow errors derive from a single `WorkflowError` base so callers can
catch one type. Validation errors carry their full deterministic issue list —
never raw payloads or credentials.
"""

from __future__ import annotations

import uuid

from genomeai_shared import BaseError


class WorkflowError(BaseError):
    """Base for every Workflow Foundation error."""

    error_code: str = "workflow.error"


class WorkflowNotFoundError(WorkflowError):
    error_code = "workflow.not-found"

    def __init__(self, workflow_id: uuid.UUID) -> None:
        super().__init__(
            message=f"Workflow '{workflow_id}' does not exist",
            detail="No workflow is registered under this identifier.",
        )


class WorkflowRunNotFoundError(WorkflowError):
    error_code = "workflow.run-not-found"

    def __init__(self, run_id: uuid.UUID) -> None:
        super().__init__(
            message=f"Workflow run '{run_id}' does not exist",
            detail="No workflow run is registered under this identifier.",
        )


class WorkflowStateTransitionError(WorkflowError):
    error_code = "workflow.invalid-transition"

    def __init__(self, current: str, next_state: str) -> None:
        super().__init__(
            message=f"Cannot transition workflow state from '{current}' to '{next_state}'",
            detail="The workflow run state machine does not allow this transition.",
        )


class WorkflowValidationError(WorkflowError):
    """The submitted workflow definition is not a valid DAG."""

    error_code = "workflow.validation-error"

    def __init__(self, summary: str, issues: list[str]) -> None:
        self.issues = issues
        detail = "; ".join(issues) if issues else None
        super().__init__(
            message=summary,
            detail=detail,
        )


class ScheduleNotFoundError(WorkflowError):
    error_code = "workflow.schedule-not-found"

    def __init__(self, schedule_id: uuid.UUID) -> None:
        super().__init__(
            message=f"Workflow schedule '{schedule_id}' does not exist",
            detail="No workflow schedule is registered under this identifier.",
        )


class ScheduleValidationError(WorkflowError):
    """The submitted schedule configuration is invalid."""

    error_code = "workflow.schedule-validation-error"

    def __init__(self, summary: str, issues: list[str]) -> None:
        self.issues = issues
        detail = "; ".join(issues) if issues else None
        super().__init__(message=summary, detail=detail)


class ScheduleStateTransitionError(WorkflowError):
    error_code = "workflow.schedule-invalid-transition"

    def __init__(self, current: str, next_state: str) -> None:
        super().__init__(
            message=f"Cannot transition schedule state from '{current}' to '{next_state}'",
            detail="The schedule lifecycle does not allow this transition.",
        )


__all__ = [
    "ScheduleNotFoundError",
    "ScheduleStateTransitionError",
    "ScheduleValidationError",
    "WorkflowError",
    "WorkflowNotFoundError",
    "WorkflowRunNotFoundError",
    "WorkflowStateTransitionError",
    "WorkflowValidationError",
]
