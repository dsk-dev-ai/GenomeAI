"""Parallel DAG execution tests (Phase 7.6).

Tests that the DAGExecutionEngine correctly executes independent steps
concurrently when max_concurrency > 1, respects concurrency limits,
and handles failures/cancellation correctly in parallel mode.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest
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


class TimingExecutor(StepExecutor):
    """Executor that records start/end times to detect concurrency.

    Each step sleeps for `step_delay` seconds so that concurrent steps
    overlap in time.  The `concurrency_watermark` property reports the
    maximum number of steps observed running simultaneously.
    """

    FAILURE_KEY = "fail"

    def __init__(self, step_delay: float = 0.05) -> None:
        self._step_delay = step_delay
        self._running = 0
        self.concurrency_watermark = 0
        self.execution_order: list[str] = []
        self._lock = asyncio.Lock()

    async def _record_start(self) -> None:
        async with self._lock:
            self._running += 1
            if self._running > self.concurrency_watermark:
                self.concurrency_watermark = self._running

    async def _record_end(self) -> None:
        async with self._lock:
            self._running -= 1

    def execute(
        self, step: WorkflowStep, context: StepExecutionContext
    ) -> StepExecutionResult:
        import time

        # Track concurrency — CPython GIL makes plain int ops atomic
        self._running += 1
        if self._running > self.concurrency_watermark:
            self.concurrency_watermark = self._running

        time.sleep(self._step_delay)

        self.execution_order.append(step.name)

        self._running -= 1

        configuration = step.configuration or {}
        if self.FAILURE_KEY in configuration:
            return StepExecutionResult.failure(str(configuration[self.FAILURE_KEY]))

        output: dict[str, Any] = {}
        for name in sorted(context.upstream_outputs):
            output.update(context.upstream_outputs[name])
        output.update(configuration)
        return StepExecutionResult.ok(output)


class SlowExecutor(StepExecutor):
    """Executor that sleeps synchronously for a configurable duration.

    Used to verify that asyncio.to_thread correctly offloads sync work.
    """

    def __init__(self, delay: float = 0.05) -> None:
        self._delay = delay
        self.execution_order: list[str] = []

    def execute(
        self, step: WorkflowStep, context: StepExecutionContext
    ) -> StepExecutionResult:
        import time

        time.sleep(self._delay)
        self.execution_order.append(step.name)
        configuration = step.configuration or {}
        if "fail" in configuration:
            return StepExecutionResult.failure(str(configuration["fail"]))
        return StepExecutionResult.ok(configuration)


class RecordingExecutor(StepExecutor):
    """Simple executor that records calls, no sleep."""

    FAIL_KEY = "fail"

    def __init__(self) -> None:
        self.calls: list[tuple[str, frozenset[str]]] = []

    def execute(
        self, step: WorkflowStep, context: StepExecutionContext
    ) -> StepExecutionResult:
        self.calls.append((step.name, frozenset(context.upstream_outputs)))
        configuration = step.configuration or {}
        if self.FAIL_KEY in configuration:
            return StepExecutionResult.failure(str(configuration[self.FAIL_KEY]))
        merged: dict[str, Any] = {}
        for upstream in sorted(context.upstream_outputs):
            merged.update(context.upstream_outputs[upstream])
        merged.update(configuration)
        return StepExecutionResult.ok(merged)


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
    *,
    max_concurrency: int = 1,
) -> DAGExecutionEngine:
    return DAGExecutionEngine(store, executor, should_cancel, max_concurrency=max_concurrency)


# ---------------------------------------------------------------------------
# Concurrency verification tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_independent_steps_run_concurrently() -> None:
    """Three independent steps with max_concurrency=3 should overlap."""
    workflow = _workflow(("a", "b", "c"))
    run = _run(workflow)
    store = FakeStore(workflow, run)
    executor = TimingExecutor(step_delay=0.05)

    result = await _engine(store, executor, max_concurrency=3).execute_run(run.id)

    assert result.state == RunState.SUCCEEDED.value
    # With delay=50ms and 3 concurrent tasks, watermark should be > 1
    assert executor.concurrency_watermark > 1
    assert len(executor.execution_order) == 3


@pytest.mark.asyncio
async def test_concurrency_limit_enforced() -> None:
    """max_concurrency=2 with 3 independent steps: at most 2 overlap."""
    workflow = _workflow(("a", "b", "c"))
    run = _run(workflow)
    store = FakeStore(workflow, run)
    executor = TimingExecutor(step_delay=0.05)

    result = await _engine(store, executor, max_concurrency=2).execute_run(run.id)

    assert result.state == RunState.SUCCEEDED.value
    assert executor.concurrency_watermark <= 2
    assert len(executor.execution_order) == 3


@pytest.mark.asyncio
async def test_max_concurrency_one_matches_sequential() -> None:
    """max_concurrency=1: no concurrency, same as Phase 7.2."""
    workflow = _workflow(("a", "b", "c"))
    run = _run(workflow)
    store = FakeStore(workflow, run)
    executor = TimingExecutor(step_delay=0.02)

    result = await _engine(store, executor, max_concurrency=1).execute_run(run.id)

    assert result.state == RunState.SUCCEEDED.value
    assert executor.concurrency_watermark == 1
    # Sequential order preserved
    assert executor.execution_order == ["a", "b", "c"]


@pytest.mark.asyncio
async def test_diamond_dag_parallel_branches() -> None:
    """Diamond: a → (b, c) → d. b and c should run concurrently."""
    workflow = _workflow(
        ("a", "b", "c", "d"),
        (("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")),
    )
    run = _run(workflow)
    store = FakeStore(workflow, run)
    executor = TimingExecutor(step_delay=0.05)

    result = await _engine(store, executor, max_concurrency=4).execute_run(run.id)

    assert result.state == RunState.SUCCEEDED.value
    assert executor.execution_order[0] == "a"
    assert executor.execution_order[-1] == "d"
    assert set(executor.execution_order[1:3]) == {"b", "c"}
    # b and c should have overlapped
    assert executor.concurrency_watermark >= 2


@pytest.mark.asyncio
async def test_wide_fan_out_respects_concurrency() -> None:
    """6 independent steps with max_concurrency=2: at most 2 overlap."""
    workflow = _workflow(("a", "b", "c", "d", "e", "f"))
    run = _run(workflow)
    store = FakeStore(workflow, run)
    executor = TimingExecutor(step_delay=0.03)

    result = await _engine(store, executor, max_concurrency=2).execute_run(run.id)

    assert result.state == RunState.SUCCEEDED.value
    assert executor.concurrency_watermark <= 2
    assert len(executor.execution_order) == 6


@pytest.mark.asyncio
async def test_complex_mixed_dag() -> None:
    """Mixed DAG: sequential a→b, parallel b→(c,d), then c→e, d→e."""
    workflow = _workflow(
        ("a", "b", "c", "d", "e"),
        (("a", "b"), ("b", "c"), ("b", "d"), ("c", "e"), ("d", "e")),
    )
    run = _run(workflow)
    store = FakeStore(workflow, run)
    executor = TimingExecutor(step_delay=0.05)

    result = await _engine(store, executor, max_concurrency=4).execute_run(run.id)

    assert result.state == RunState.SUCCEEDED.value
    order = executor.execution_order
    assert order[0] == "a"
    assert order[1] == "b"
    assert order[-1] == "e"
    assert set(order[2:4]) == {"c", "d"}
    assert executor.concurrency_watermark >= 2


# ---------------------------------------------------------------------------
# Failure handling in parallel mode
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_parallel_failure_cancels_dependents() -> None:
    """Failure in one step cancels steps that depend on it."""
    workflow = _workflow(
        ("a", "b", "c"),
        (("a", "b"), ("b", "c")),  # a→b→c
    )
    run = _run(workflow)
    workflow.steps[1].configuration = {RecordingExecutor.FAIL_KEY: "boom"}
    store = FakeStore(workflow, run)
    executor = RecordingExecutor()

    result = await _engine(store, executor, max_concurrency=1).execute_run(run.id)

    assert result.state == RunState.FAILED.value
    assert result.error_message == "Step 'b' failed: boom"
    states = {sr.position: sr.state for sr in result.step_runs}
    assert states[0] == "succeeded"  # a completed
    assert states[1] == "failed"  # b failed
    assert states[2] == "cancelled"  # c depends on b, cancelled


@pytest.mark.asyncio
async def test_parallel_independent_step_not_cancelled_by_later_failure() -> None:
    """Independent step that completes before failure keeps its success."""
    workflow = _workflow(
        ("a", "b", "c"),
        (("a", "b"),),  # a→b, c independent
    )
    run = _run(workflow)
    workflow.steps[1].configuration = {RecordingExecutor.FAIL_KEY: "boom"}
    store = FakeStore(workflow, run)
    executor = RecordingExecutor()

    # max_concurrency=2: wave 1 runs a and c concurrently; wave 2 runs b
    result = await _engine(store, executor, max_concurrency=2).execute_run(run.id)

    assert result.state == RunState.FAILED.value
    states = {sr.position: sr.state for sr in result.step_runs}
    assert states[0] == "succeeded"  # a succeeded in wave 1
    assert states[1] == "failed"  # b failed in wave 2
    assert states[2] == "succeeded"  # c succeeded in wave 1 (independent of b)


@pytest.mark.asyncio
async def test_parallel_failure_blocks_further_waves() -> None:
    """Failure in wave 1 prevents wave 2 from starting."""
    workflow = _workflow(
        ("a", "b", "c", "d"),
        (("a", "c"), ("b", "c"), ("c", "d")),
    )
    run = _run(workflow)
    # Make step "b" fail — it's in wave 1 alongside "a"
    workflow.steps[1].configuration = {RecordingExecutor.FAIL_KEY: "crash"}
    store = FakeStore(workflow, run)
    executor = RecordingExecutor()

    result = await _engine(store, executor, max_concurrency=2).execute_run(run.id)

    assert result.state == RunState.FAILED.value
    states = {sr.position: sr.state for sr in result.step_runs}
    # a succeeded (independent of b), b failed, c and d cancelled
    assert states[0] == "succeeded"
    assert states[1] == "failed"
    assert states[2] == "cancelled"
    assert states[3] == "cancelled"


@pytest.mark.asyncio
async def test_executor_exception_in_parallel_fails_run() -> None:
    """Exception in a concurrent step fails the run."""
    workflow = _workflow(("a", "b", "c"))
    run = _run(workflow)
    store = FakeStore(workflow, run)

    call_count = 0

    class ExplodingExecutor(StepExecutor):
        def execute(
            self, step: WorkflowStep, context: StepExecutionContext
        ) -> StepExecutionResult:
            nonlocal call_count
            call_count += 1
            if step.name == "b":
                raise RuntimeError("thread explosion")
            return StepExecutionResult.ok()

    executor = ExplodingExecutor()
    result = await _engine(store, executor, max_concurrency=3).execute_run(run.id)

    assert result.state == RunState.FAILED.value
    assert "thread explosion" in (result.error_message or "")


@pytest.mark.asyncio
async def test_two_parallel_failures_first_wins() -> None:
    """If two concurrent steps fail, the first one recorded wins."""
    workflow = _workflow(("a", "b", "c"))
    run = _run(workflow)
    # Make both a and b fail
    workflow.steps[0].configuration = {RecordingExecutor.FAIL_KEY: "fail_a"}
    workflow.steps[1].configuration = {RecordingExecutor.FAIL_KEY: "fail_b"}
    store = FakeStore(workflow, run)
    executor = RecordingExecutor()

    result = await _engine(store, executor, max_concurrency=2).execute_run(run.id)

    assert result.state == RunState.FAILED.value
    # Exactly one failure is recorded
    assert result.error_message is not None
    assert "failed:" in result.error_message


# ---------------------------------------------------------------------------
# Cancellation in parallel mode
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cancel_before_start_parallel() -> None:
    """Cancellation before any step starts."""
    workflow = _workflow(("a", "b", "c"))
    run = _run(workflow)
    store = FakeStore(workflow, run)
    executor = RecordingExecutor()

    result = await _engine(store, executor, lambda: True, max_concurrency=3).execute_run(run.id)

    assert result.state == RunState.CANCELLED.value
    assert executor.calls == []
    assert all(sr.state == "cancelled" for sr in result.step_runs)


@pytest.mark.asyncio
async def test_cancel_during_parallel_execution() -> None:
    """Cancellation during parallel execution: completed steps preserved."""
    workflow = _workflow(("a", "b", "c"))
    run = _run(workflow)
    store = FakeStore(workflow, run)
    executor = RecordingExecutor()

    def cancel_after_first() -> bool:
        return len(executor.calls) >= 1

    result = await _engine(store, executor, cancel_after_first, max_concurrency=1).execute_run(
        run.id
    )

    assert result.state == RunState.CANCELLED.value
    # At least step "a" completed
    assert len(executor.calls) >= 1
    states = {sr.position: sr.state for sr in result.step_runs}
    assert states[0] == "succeeded"
    for pos in range(1, 3):
        assert states[pos] == "cancelled"


@pytest.mark.asyncio
async def test_cancel_stops_new_steps_from_starting() -> None:
    """With max_concurrency=2, cancel prevents the second wave."""
    workflow = _workflow(
        ("a", "b", "c", "d"),
        (("a", "c"), ("b", "c"), ("c", "d")),
    )
    run = _run(workflow)
    store = FakeStore(workflow, run)
    executor = RecordingExecutor()

    # Cancel after first wave (a, b) completes
    def cancel_after_wave1() -> bool:
        return len(executor.calls) >= 2

    result = await _engine(
        store, executor, cancel_after_wave1, max_concurrency=2
    ).execute_run(run.id)

    assert result.state == RunState.CANCELLED.value
    executed_names = {name for name, _ in executor.calls}
    assert "a" in executed_names or "b" in executed_names
    # c and d should not have executed (cancelled)
    assert "c" not in executed_names
    assert "d" not in executed_names


# ---------------------------------------------------------------------------
# Regression: sequential behaviour preserved
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sequential_linear_order_preserved() -> None:
    """Linear chain: steps execute in strict order."""
    workflow = _workflow(("a", "b", "c"), (("a", "b"), ("b", "c")))
    run = _run(workflow)
    store = FakeStore(workflow, run)
    executor = RecordingExecutor()

    result = await _engine(store, executor, max_concurrency=4).execute_run(run.id)

    assert result.state == RunState.SUCCEEDED.value
    assert [name for name, _ in executor.calls] == ["a", "b", "c"]


@pytest.mark.asyncio
async def test_downstream_receives_correct_outputs_parallel() -> None:
    """In parallel mode, downstream steps receive correct upstream outputs."""
    workflow = _workflow(
        ("a", "b", "c", "d"),
        (("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")),
    )
    run = _run(workflow)
    store = FakeStore(workflow, run)
    executor = RecordingExecutor()

    await _engine(store, executor, max_concurrency=4).execute_run(run.id)

    by_name = dict(executor.calls)
    assert by_name["a"] == frozenset()
    assert by_name["b"] == frozenset({"a"})
    assert by_name["d"] == frozenset({"b", "c"})


@pytest.mark.asyncio
async def test_invalid_max_concurrency_rejected() -> None:
    """max_concurrency < 1 raises ValueError."""
    workflow = _workflow(("a",))
    run = _run(workflow)
    store = FakeStore(workflow, run)
    executor = RecordingExecutor()

    with pytest.raises(ValueError, match="max_concurrency"):
        DAGExecutionEngine(store, executor, max_concurrency=0)


@pytest.mark.asyncio
async def test_single_step_max_concurrency_100() -> None:
    """Single step with high max_concurrency works identically."""
    workflow = _workflow(("only",))
    run = _run(workflow)
    store = FakeStore(workflow, run)
    executor = RecordingExecutor()

    result = await _engine(store, executor, max_concurrency=100).execute_run(run.id)

    assert result.state == RunState.SUCCEEDED.value
    assert len(executor.calls) == 1
    assert executor.calls[0][0] == "only"
