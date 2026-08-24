"""DAGExecutionEngine tests against an in-memory fake store.

No database involved: the fake store implements the same persistence
surface as WorkflowRepository so transition legality and ordering can be
asserted deterministically.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest
from genomeai_api.workflows.errors import (
    WorkflowRunNotFoundError,
    WorkflowStateTransitionError,
    WorkflowValidationError,
)
from genomeai_api.workflows.execution.engine import DAGExecutionEngine
from genomeai_api.workflows.execution.executor import (
    StepExecutionContext,
    StepExecutionResult,
    StepExecutor,
)
from genomeai_api.workflows.models.step_run import StepRun
from genomeai_api.workflows.models.workflow import Workflow
from genomeai_api.workflows.models.workflow_dependency import WorkflowDependency
from genomeai_api.workflows.models.workflow_run import WorkflowRun
from genomeai_api.workflows.models.workflow_step import WorkflowStep
from genomeai_api.workflows.types import RunState


class FakeStore:
    """Minimal in-memory stand-in for WorkflowRepository."""

    def __init__(self, workflow: Workflow | None, run: WorkflowRun | None) -> None:
        self._workflow = workflow
        self._run = run

    async def get_run(self, run_id: uuid.UUID) -> WorkflowRun | None:
        if self._run is None or self._run.id != run_id:
            return None
        return self._run

    async def get_by_id(self, workflow_id: uuid.UUID) -> Workflow | None:
        if self._workflow is None or self._workflow.id != workflow_id:
            return None
        return self._workflow

    async def transition_run(
        self,
        run_id: uuid.UUID,
        to_state: RunState,
        *,
        error_message: str | None = None,
    ) -> WorkflowRun | None:
        assert self._run is not None and self._run.id == run_id
        now = datetime.now(UTC)
        self._run.state = to_state.value
        if to_state == RunState.RUNNING:
            self._run.started_at = now
        if to_state in (RunState.SUCCEEDED, RunState.FAILED, RunState.CANCELLED):
            self._run.finished_at = now
        if error_message is not None or to_state == RunState.SUCCEEDED:
            self._run.error_message = error_message
        return self._run

    async def transition_step_run(
        self,
        step_run_id: uuid.UUID,
        to_state: RunState,
        *,
        output: dict[str, Any] | None = None,
        error_message: str | None = None,
    ) -> StepRun | None:
        assert self._run is not None
        for step_run in self._run.step_runs:
            if step_run.id != step_run_id:
                continue
            now = datetime.now(UTC)
            step_run.state = to_state.value
            if to_state == RunState.RUNNING:
                step_run.started_at = now
            if to_state in (RunState.SUCCEEDED, RunState.FAILED, RunState.CANCELLED):
                step_run.finished_at = now
            if output is not None:
                step_run.output = output
            if error_message is not None:
                step_run.error_message = error_message
            return step_run
        return None


class RecordingExecutor(StepExecutor):
    FAIL_KEY = "fail"

    def __init__(self) -> None:
        self.calls: list[tuple[str, frozenset[str]]] = []

    def execute(self, step: WorkflowStep, context: StepExecutionContext) -> StepExecutionResult:
        self.calls.append((step.name, frozenset(context.upstream_outputs)))
        configuration = step.configuration or {}
        if self.FAIL_KEY in configuration:
            return StepExecutionResult.failure(str(configuration[self.FAIL_KEY]))
        merged: dict[str, Any] = {}
        for upstream in sorted(context.upstream_outputs):
            merged.update(context.upstream_outputs[upstream])
        merged.update(configuration)
        return StepExecutionResult.ok(merged)


class ExplodingOnCallExecutor(RecordingExecutor):
    """Raises instead of returning a failed result on the Nth call."""

    def __init__(self, explode_on_call: int) -> None:
        super().__init__()
        self._explode_on_call = explode_on_call

    def execute(self, step: WorkflowStep, context: StepExecutionContext) -> StepExecutionResult:
        if len(self.calls) + 1 == self._explode_on_call:
            raise RuntimeError("disk on fire")
        return super().execute(step, context)


def _workflow(
    steps: tuple[str, ...],
    edges: tuple[tuple[str, str], ...] = (),
) -> Workflow:
    workflow_id = uuid.uuid4()
    ids = {name: uuid.uuid4() for name in steps}
    workflow = Workflow(
        id=workflow_id,
        name="pipeline",
        description=None,
        version="0.1.0",
        status="draft",
    )
    workflow.steps = [
        WorkflowStep(
            id=ids[name],
            workflow_id=workflow_id,
            name=name,
            step_type="noop",
            configuration={},
            position=index,
        )
        for index, name in enumerate(steps)
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


def _run(workflow: Workflow, state: RunState = RunState.PENDING) -> WorkflowRun:
    run_id = uuid.uuid4()
    return WorkflowRun(
        id=run_id,
        workflow_id=workflow.id,
        state=state.value,
        created_at=datetime.now(UTC),
        step_runs=[
            StepRun(
                id=uuid.uuid4(),
                run_id=run_id,
                step_id=step.id,
                state="pending",
                position=step.position,
            )
            for step in sorted(workflow.steps, key=lambda s: s.position)
        ],
    )


def _engine(
    store: FakeStore,
    executor: StepExecutor,
    should_cancel: Callable[[], bool] | None = None,
) -> DAGExecutionEngine:
    return DAGExecutionEngine(store, executor, should_cancel)


@pytest.mark.asyncio
async def test_single_step_run_succeeds_end_to_end() -> None:
    workflow = _workflow(("only",))
    run = _run(workflow)
    store = FakeStore(workflow, run)
    executor = RecordingExecutor()

    result = await _engine(store, executor).execute_run(run.id)

    assert result.state == RunState.SUCCEEDED.value
    assert result.started_at is not None
    assert result.finished_at is not None
    assert result.error_message is None
    step_run = result.step_runs[0]
    assert step_run.state == "succeeded"
    assert step_run.output == {}
    assert step_run.started_at is not None
    assert step_run.finished_at is not None


@pytest.mark.asyncio
async def test_linear_steps_execute_in_position_order() -> None:
    workflow = _workflow(("fetch", "align", "report"), (("fetch", "align"), ("align", "report")))
    run = _run(workflow)
    store = FakeStore(workflow, run)
    executor = RecordingExecutor()

    result = await _engine(store, executor).execute_run(run.id)

    assert result.state == RunState.SUCCEEDED.value
    assert [name for name, _ in executor.calls] == ["fetch", "align", "report"]


@pytest.mark.asyncio
async def test_diamond_join_waits_for_all_branches() -> None:
    workflow = _workflow(
        ("a", "b", "c", "d"),
        (("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")),
    )
    run = _run(workflow)
    store = FakeStore(workflow, run)
    executor = RecordingExecutor()

    result = await _engine(store, executor).execute_run(run.id)

    assert result.state == RunState.SUCCEEDED.value
    executed = [name for name, _ in executor.calls]
    assert executed[0] == "a"
    assert set(executed[1:3]) == {"b", "c"}
    assert executed[-1] == "d"


@pytest.mark.asyncio
async def test_downstream_receives_direct_upstream_output() -> None:
    workflow = _workflow(
        ("a", "b", "c", "d"),
        (("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")),
    )
    run = _run(workflow)
    store = FakeStore(workflow, run)
    executor = RecordingExecutor()

    await _engine(store, executor).execute_run(run.id)

    by_name = dict(executor.calls)
    assert by_name["a"] == frozenset()
    assert by_name["b"] == frozenset({"a"})
    assert by_name["d"] == frozenset({"b", "c"})


@pytest.mark.asyncio
async def test_failure_blocks_dependents_and_preserves_reason() -> None:
    workflow = _workflow(("a", "b", "c"), (("a", "b"), ("b", "c")))
    run = _run(workflow)
    workflow.steps[1].configuration = {RecordingExecutor.FAIL_KEY: "aligner crashed"}
    store = FakeStore(workflow, run)
    executor = RecordingExecutor()

    result = await _engine(store, executor).execute_run(run.id)

    assert result.state == RunState.FAILED.value
    assert result.error_message == "Step 'b' failed: aligner crashed"
    assert result.finished_at is not None
    states = {step_run.position: step_run.state for step_run in result.step_runs}
    assert states == {
        0: "succeeded",
        1: "failed",
        2: "cancelled",
    }
    failed_step = next(sr for sr in result.step_runs if sr.position == 1)
    assert failed_step.error_message == "aligner crashed"


@pytest.mark.asyncio
async def test_failure_stops_further_scheduling() -> None:
    workflow = _workflow(("a", "b", "c"))
    run = _run(workflow)
    workflow.steps[0].configuration = {RecordingExecutor.FAIL_KEY: "nope"}
    store = FakeStore(workflow, run)
    executor = RecordingExecutor()

    result = await _engine(store, executor).execute_run(run.id)

    assert len(executor.calls) == 1
    assert result.state == RunState.FAILED.value
    states = {sr.position: sr.state for sr in result.step_runs}
    assert states == {0: "failed", 1: "cancelled", 2: "cancelled"}


@pytest.mark.asyncio
async def test_cancel_before_start_leaves_nothing_executed() -> None:
    workflow = _workflow(("a", "b"))
    run = _run(workflow)
    store = FakeStore(workflow, run)
    executor = RecordingExecutor()

    result = await _engine(store, executor, lambda: True).execute_run(run.id)

    assert result.state == RunState.CANCELLED.value
    assert executor.calls == []
    assert all(sr.state == "cancelled" for sr in result.step_runs)


@pytest.mark.asyncio
async def test_cancel_mid_run_preserves_completed_steps() -> None:
    workflow = _workflow(("a", "b", "c"))
    run = _run(workflow)
    store = FakeStore(workflow, run)
    executor = RecordingExecutor()

    def cancel_after_first() -> bool:
        return len(executor.calls) >= 1

    result = await _engine(store, executor, cancel_after_first).execute_run(run.id)

    assert result.state == RunState.CANCELLED.value
    states = {sr.position: sr.state for sr in result.step_runs}
    assert states == {0: "succeeded", 1: "cancelled", 2: "cancelled"}
    assert [name for name, _ in executor.calls] == ["a"]


@pytest.mark.asyncio
async def test_executing_non_pending_run_is_rejected_and_persists_nothing() -> None:
    workflow = _workflow(("a",))
    run = _run(workflow, state=RunState.SUCCEEDED)
    before = (run.state, run.started_at, run.finished_at)
    store = FakeStore(workflow, run)
    executor = RecordingExecutor()

    with pytest.raises(WorkflowStateTransitionError):
        await _engine(store, executor).execute_run(run.id)

    assert (run.state, run.started_at, run.finished_at) == before
    assert executor.calls == []


@pytest.mark.asyncio
async def test_unknown_run_raises_not_found() -> None:
    store = FakeStore(None, None)
    executor = RecordingExecutor()

    with pytest.raises(WorkflowRunNotFoundError):
        await _engine(store, executor).execute_run(uuid.uuid4())


@pytest.mark.asyncio
async def test_broken_graph_rejected_before_any_transition() -> None:
    workflow = _workflow(("a", "b"), (("a", "b"), ("b", "a")))
    run = _run(workflow)
    store = FakeStore(workflow, run)
    executor = RecordingExecutor()

    with pytest.raises(WorkflowValidationError):
        await _engine(store, executor).execute_run(run.id)

    assert run.state == "pending"
    assert all(step_run.state == "pending" for step_run in run.step_runs)
    assert executor.calls == []


@pytest.mark.asyncio
async def test_executor_exception_on_first_step_fails_the_run() -> None:
    workflow = _workflow(("a",))
    run = _run(workflow)
    store = FakeStore(workflow, run)
    executor = ExplodingOnCallExecutor(explode_on_call=1)

    result = await _engine(store, executor).execute_run(run.id)

    assert result.state == RunState.FAILED.value
    assert result.error_message == "Step 'a' failed: disk on fire"
    assert result.finished_at is not None
    step_run = result.step_runs[0]
    assert step_run.state == "failed"
    assert step_run.error_message == "disk on fire"


@pytest.mark.asyncio
async def test_executor_exception_mid_run_blocks_dependents() -> None:
    workflow = _workflow(("a", "b", "c"), (("a", "b"), ("b", "c")))
    run = _run(workflow)
    store = FakeStore(workflow, run)
    executor = ExplodingOnCallExecutor(explode_on_call=2)

    result = await _engine(store, executor).execute_run(run.id)

    assert [name for name, _ in executor.calls] == ["a"]
    states = {sr.position: sr.state for sr in result.step_runs}
    assert states == {0: "succeeded", 1: "failed", 2: "cancelled"}
    failed_step = next(sr for sr in result.step_runs if sr.position == 1)
    assert failed_step.error_message == "disk on fire"
    assert result.error_message == "Step 'b' failed: disk on fire"

    with pytest.raises(WorkflowStateTransitionError):
        await _engine(store, RecordingExecutor()).execute_run(run.id)
