"""Step execution abstraction for the DAG execution engine.

A `StepExecutor` runs ONE workflow step and returns a deterministic
`StepExecutionResult`. Executors are pure domain objects: no FastAPI, no
database, no scheduling — those belong to the engine. Phase 7.2 ships a
minimal deterministic executor (`PassthroughStepExecutor`) suitable for
tests; real biological executors arrive in later milestones.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from genomeai_api.workflows.models.workflow_step import WorkflowStep


@dataclass(frozen=True)
class StepExecutionContext:
    """Everything an executor may know about one step invocation.

    `upstream_outputs` maps DIRECT predecessor step names to their recorded
    outputs; steps only see data from steps they explicitly depend on.
    """

    run_id: uuid.UUID
    workflow_id: uuid.UUID
    workflow_name: str
    upstream_outputs: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass(frozen=True)
class StepExecutionResult:
    """Outcome of executing exactly one step."""

    succeeded: bool
    output: dict[str, Any] | None = None
    error_message: str | None = None

    @classmethod
    def ok(cls, output: dict[str, Any] | None = None) -> StepExecutionResult:
        return cls(succeeded=True, output=output)

    @classmethod
    def failure(cls, error_message: str) -> StepExecutionResult:
        return cls(succeeded=False, error_message=error_message)


class StepExecutor(ABC):
    """Executes a single workflow step.

    Implementations MUST be deterministic for identical inputs and MUST NOT
    schedule other steps, touch the database, or mutate the step row — the
    engine owns orchestration and persistence.
    """

    @abstractmethod
    def execute(
        self, step: WorkflowStep, context: StepExecutionContext
    ) -> StepExecutionResult:
        """Runs `step` and reports its outcome."""


class PassthroughStepExecutor(StepExecutor):
    """Deterministic reference executor.

    On success it emits the step's configuration merged over its upstream
    outputs — upstreams applied in name order (later names win conflicts),
    configuration wins last — making data-flow visible in tests. A step
    fails deterministically when its configuration contains the key
    `"fail_with_message"`.
    """

    FAILURE_TRIGGER_KEY = "fail_with_message"

    def execute(
        self, step: WorkflowStep, context: StepExecutionContext
    ) -> StepExecutionResult:
        trigger = step.configuration.get(self.FAILURE_TRIGGER_KEY)
        if isinstance(trigger, str):
            return StepExecutionResult.failure(trigger)

        output: dict[str, Any] = {}
        for name in sorted(context.upstream_outputs):
            output.update(context.upstream_outputs[name])
        output.update(step.configuration)
        return StepExecutionResult.ok(output)


__all__ = [
    "PassthroughStepExecutor",
    "StepExecutionContext",
    "StepExecutionResult",
    "StepExecutor",
]
