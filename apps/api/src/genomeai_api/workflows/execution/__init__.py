"""DAG Execution Engine (Phases 7.2 + 7.6).

Deterministic, in-process execution of one WorkflowRun at a time. Supports
sequential (max_concurrency=1, default) and parallel (max_concurrency>1)
execution of independent DAG steps. NOT a distributed engine: no queues,
workers, schedulers, retries, or cross-run parallelism — those are deferred
to later Phase 7 milestones.
"""

from genomeai_api.workflows.execution.engine import DAGExecutionEngine
from genomeai_api.workflows.execution.executor import (
    PassthroughStepExecutor,
    StepExecutionContext,
    StepExecutionResult,
    StepExecutor,
)
from genomeai_api.workflows.execution.planner import (
    PlannedStep,
    all_succeeded,
    pending_steps,
    ready_steps,
)

__all__ = [
    "DAGExecutionEngine",
    "PassthroughStepExecutor",
    "PlannedStep",
    "StepExecutionContext",
    "StepExecutionResult",
    "StepExecutor",
    "all_succeeded",
    "pending_steps",
    "ready_steps",
]
