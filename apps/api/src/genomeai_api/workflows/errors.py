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


class QueueUnavailableError(WorkflowError):
    """The workflow queue backend is not reachable or not configured."""

    error_code = "workflow.queue-unavailable"

    def __init__(self, reason: str) -> None:
        super().__init__(
            message="Workflow queue is unavailable",
            detail=reason,
        )


class JobDecodeError(WorkflowError):
    """A queued job payload cannot be decoded deterministically."""

    error_code = "workflow.job-decode-error"

    def __init__(self, reason: str) -> None:
        super().__init__(
            message="Queued job payload is malformed",
            detail=reason,
        )


class TransientExecutionError(WorkflowError):
    """A step execution failed in a way that is expected to be temporary.

    Executors raise this to opt a failure into automatic retry (the
    classifier also maps timeouts/connection errors here). The retry
    POLICY still decides whether any retries remain.
    """

    error_code = "workflow.transient-execution-error"

    def __init__(self, reason: str) -> None:
        super().__init__(message="Transient workflow execution failure", detail=reason)


class PermanentExecutionError(WorkflowError):
    """A step execution failed in a way that will not change on retry.

    Executors raise this for deterministic failures (bad input data,
    unsupported step configuration). The classifier maps it to the
    permanent class, which default policies never retry.
    """

    error_code = "workflow.permanent-execution-error"

    def __init__(self, reason: str) -> None:
        super().__init__(message="Permanent workflow execution failure", detail=reason)


__all__ = [
    "JobDecodeError",
    "PermanentExecutionError",
    "QueueUnavailableError",
    "ScheduleNotFoundError",
    "ScheduleStateTransitionError",
    "ScheduleValidationError",
    "TransientExecutionError",
    "WorkflowError",
    "WorkflowNotFoundError",
    "WorkflowRunNotFoundError",
    "WorkflowStateTransitionError",
    "WorkflowValidationError",
]
