"""Workflow domain.

Phase 7.1: definitions, DAG validation, execution-state models, persistence,
minimal admin API. Phase 7.2: deterministic sequential in-process DAG
execution. No scheduler, queue, worker, or parallel engine exists here.
"""

from genomeai_api.workflows.dag import GraphIssue, topological_order, validate_graph
from genomeai_api.workflows.errors import (
    WorkflowError,
    WorkflowNotFoundError,
    WorkflowRunNotFoundError,
    WorkflowStateTransitionError,
    WorkflowValidationError,
)
from genomeai_api.workflows.execution.engine import DAGExecutionEngine
from genomeai_api.workflows.execution.executor import (
    PassthroughStepExecutor,
    StepExecutionContext,
    StepExecutionResult,
    StepExecutor,
)
from genomeai_api.workflows.types import (
    RUN_STATE_TRANSITIONS,
    RunState,
    WorkflowStatus,
    can_transition,
    is_terminal,
)

__all__ = [
    "DAGExecutionEngine",
    "PassthroughStepExecutor",
    "RUN_STATE_TRANSITIONS",
    "GraphIssue",
    "RunState",
    "StepExecutionContext",
    "StepExecutionResult",
    "StepExecutor",
    "WorkflowError",
    "WorkflowNotFoundError",
    "WorkflowRunNotFoundError",
    "WorkflowStateTransitionError",
    "WorkflowStatus",
    "WorkflowValidationError",
    "can_transition",
    "is_terminal",
    "topological_order",
    "validate_graph",
]
