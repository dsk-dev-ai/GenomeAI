from __future__ import annotations

import uuid

from genomeai_api.workflows.execution.executor import (
    PassthroughStepExecutor,
    StepExecutionContext,
    StepExecutionResult,
)
from genomeai_api.workflows.models.workflow_step import WorkflowStep


def _step(configuration: dict | None = None) -> WorkflowStep:
    return WorkflowStep(
        id=uuid.uuid4(),
        workflow_id=uuid.uuid4(),
        name="transform",
        step_type="passthrough",
        configuration=configuration or {},
    )


def _context(upstream: dict[str, dict] | None = None) -> StepExecutionContext:
    return StepExecutionContext(
        run_id=uuid.uuid4(),
        workflow_id=uuid.uuid4(),
        workflow_name="pipeline",
        upstream_outputs=upstream or {},
    )


def test_result_factories() -> None:
    ok = StepExecutionResult.ok({"value": 1})
    assert ok.succeeded and ok.output == {"value": 1} and ok.error_message is None

    failed = StepExecutionResult.failure("boom")
    assert not failed.succeeded and failed.error_message == "boom" and failed.output is None


def test_passthrough_success_merges_configuration_over_upstream() -> None:
    context = _context({"fetch": {"rows": 10, "source": "ref"}})
    step = _step({"rows": 99, "format": "json"})

    result = PassthroughStepExecutor().execute(step, context)

    assert result.succeeded
    assert result.output == {"rows": 99, "source": "ref", "format": "json"}


def test_passthrough_is_deterministic() -> None:
    context = _context({"a": {"x": 1}})
    step = _step({"y": 2})
    executor = PassthroughStepExecutor()

    first = executor.execute(step, context)
    second = executor.execute(step, context)

    assert first == second


def test_passthrough_with_no_inputs_yields_configuration_only() -> None:
    result = PassthroughStepExecutor().execute(_step({"k": "v"}), _context())

    assert result.succeeded
    assert result.output == {"k": "v"}


def test_passthrough_fails_deterministically_on_trigger() -> None:
    step = _step({PassthroughStepExecutor.FAILURE_TRIGGER_KEY: "upstream unavailable"})

    result = PassthroughStepExecutor().execute(step, _context())

    assert not result.succeeded
    assert result.error_message == "upstream unavailable"
    assert result.output is None
