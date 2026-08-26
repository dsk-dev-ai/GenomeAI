"""In-process DAG execution engine (Phases 7.2 + 7.6).

Executes one validated WorkflowRun as a deterministic DAG. Responsibilities:

- legality of every run/step state transition (via Phase 7.1 types)
- ready-step scheduling (via the planner)
- invoking the injected `StepExecutor` (sync executors run via asyncio.to_thread)
- recording outputs / failure reasons on StepRuns
- propagating failures and honouring cancellation checks
- parallel concurrent execution of independent steps (Phase 7.6)

When ``max_concurrency`` > 1, independent steps that are all ready
(satisfied dependencies) execute concurrently using structured
concurrency (``asyncio.TaskGroup``). The concurrency limit is enforced
by an ``asyncio.Semaphore``. When ``max_concurrency`` == 1 (the default)
behaviour is identical to the sequential Phase 7.2 model.

The engine does NOT distribute, retry, or schedule work beyond DAG
concurrency — no queues, no workers, no background execution. Persistence
goes through the same ``WorkflowRepository`` used by the service layer.
"""

from __future__ import annotations

import asyncio
import uuid
from collections import defaultdict
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Protocol

from genomeai_api.workflows.dag import validate_graph
from genomeai_api.workflows.errors import (
    WorkflowNotFoundError,
    WorkflowRunNotFoundError,
    WorkflowStateTransitionError,
    WorkflowValidationError,
)
from genomeai_api.workflows.execution.executor import (
    StepExecutionContext,
    StepExecutor,
)
from genomeai_api.workflows.execution.planner import (
    PlannedStep,
    all_succeeded,
    ready_steps,
)
from genomeai_api.workflows.models.workflow import Workflow
from genomeai_api.workflows.models.workflow_run import WorkflowRun
from genomeai_api.workflows.types import RunState, can_transition

if TYPE_CHECKING:
    from genomeai_api.workflows.models.workflow_step import WorkflowStep


class ExecutionRunStore(Protocol):
    """Persistence surface the engine needs (satisfied by WorkflowRepository)."""

    async def get_run(self, run_id: uuid.UUID) -> WorkflowRun | None: ...

    async def get_by_id(self, workflow_id: uuid.UUID) -> Workflow | None: ...

    async def transition_run(
        self,
        run_id: uuid.UUID,
        to_state: RunState,
        *,
        error_message: str | None = None,
    ) -> WorkflowRun | None: ...

    async def transition_step_run(
        self,
        step_run_id: uuid.UUID,
        to_state: RunState,
        *,
        output: dict[str, Any] | None = None,
        error_message: str | None = None,
    ) -> Any: ...


class DAGExecutionEngine:
    """Deterministic executor for one workflow run.

    When ``max_concurrency`` is 1 (the default), steps execute one at a
    time in topological-position order — identical to the Phase 7.2
    sequential model.  When ``max_concurrency`` > 1, independent ready
    steps execute concurrently using structured concurrency with an
    ``asyncio.Semaphore`` enforcing the limit.
    """

    def __init__(
        self,
        repository: ExecutionRunStore,
        executor: StepExecutor,
        should_cancel: Callable[[], bool] | None = None,
        *,
        max_concurrency: int = 1,
    ) -> None:
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be >= 1")
        self._repository = repository
        self._executor = executor
        self._should_cancel = should_cancel or (lambda: False)
        self._max_concurrency = max_concurrency

    # -- public entry ---------------------------------------------------

    async def execute_run(self, run_id: uuid.UUID) -> WorkflowRun:
        """Executes a PENDING run to a terminal state and returns it."""
        run = await self._repository.get_run(run_id)
        if run is None:
            raise WorkflowRunNotFoundError(run_id)

        current = RunState(run.state)
        if self._should_cancel():
            return await self._cancel_from(current, run)

        if not can_transition(current, RunState.RUNNING):
            raise WorkflowStateTransitionError(current.value, RunState.RUNNING.value)

        workflow = await self._repository.get_by_id(run.workflow_id)
        if workflow is None:
            raise WorkflowNotFoundError(run.workflow_id)

        names, name_edges, upstream_of, step_by_name = _graph_of(workflow)
        issues = validate_graph(names, name_edges)
        if issues:
            raise WorkflowValidationError(
                summary=(
                    f"Workflow '{workflow.name}' cannot be executed "
                    f"({len(issues)} issue{'s' if len(issues) != 1 else ''})"
                ),
                issues=[f"{issue.code}: {issue.message}" for issue in issues],
            )

        run = await self._require_transition_run(run.id, current, RunState.RUNNING)

        states: dict[uuid.UUID, RunState] = {
            step_run.id: RunState(step_run.state) for step_run in run.step_runs
        }
        outputs: dict[str, dict[str, Any]] = {}
        name_of_step = {step.id: step.name for step in workflow.steps}
        name_of_step_run = {
            step_run.id: name_of_step[step_run.step_id] for step_run in run.step_runs
        }
        planned: list[PlannedStep] = []

        semaphore = asyncio.Semaphore(self._max_concurrency)
        cancel_event = asyncio.Event()
        failure_step_name: str | None = None
        failure_reason: str | None = None

        while True:
            planned = [
                PlannedStep(
                    step_run_id=step_run.id,
                    name=name_of_step_run[step_run.id],
                    position=step_run.position,
                    state=states[step_run.id],
                    upstream=tuple(sorted(upstream_of[name_of_step_run[step_run.id]])),
                )
                for step_run in sorted(run.step_runs, key=lambda sr: sr.position)
            ]

            if self._should_cancel() or cancel_event.is_set():
                if failure_reason is None:
                    await self._sweep_pending(run, states)
                    run = await self._require_transition_run(
                        run.id, RunState.RUNNING, RunState.CANCELLED
                    )
                    return run
                break

            ready = ready_steps(planned)
            if not ready:
                break

            async def _run_step(
                target: PlannedStep,
            ) -> None:
                nonlocal failure_step_name, failure_reason
                async with semaphore:
                    if cancel_event.is_set() or self._should_cancel():
                        return
                    await self._repository.transition_step_run(
                        target.step_run_id, RunState.RUNNING
                    )
                    states[target.step_run_id] = RunState.RUNNING

                    context = StepExecutionContext(
                        run_id=run.id,  # type: ignore[union-attr]
                        workflow_id=workflow.id,
                        workflow_name=workflow.name,
                        upstream_outputs={
                            upstream: outputs.get(upstream, {})
                            for upstream in target.upstream
                        },
                    )
                    try:
                        result = await asyncio.to_thread(
                            self._executor.execute,
                            step_by_name[target.name],
                            context,
                        )
                    except Exception as exc:
                        if not cancel_event.is_set():
                            failure_step_name = target.name
                            failure_reason = str(exc) or type(exc).__name__
                            cancel_event.set()
                        return

                    if result.succeeded:
                        await self._repository.transition_step_run(
                            target.step_run_id,
                            RunState.SUCCEEDED,
                            output=result.output,
                        )
                        states[target.step_run_id] = RunState.SUCCEEDED
                        outputs[target.name] = result.output or {}
                    else:
                        if not cancel_event.is_set():
                            failure_step_name = target.name
                            failure_reason = result.error_message or "unknown error"
                            cancel_event.set()

            async with asyncio.TaskGroup() as tg:
                for target in ready:
                    tg.create_task(_run_step(target))

        if failure_reason is not None and failure_step_name is not None:
            await self._repository.transition_step_run(
                next(
                    sr.id
                    for sr in run.step_runs
                    if name_of_step_run[sr.id] == failure_step_name
                ),
                RunState.FAILED,
                error_message=failure_reason,
            )
            await self._sweep_pending(run, states)
            return await self._require_transition_run(
                run.id,
                RunState.RUNNING,
                RunState.FAILED,
                error_message=f"Step '{failure_step_name}' failed: {failure_reason}",
            )

        if all_succeeded(planned):
            run = await self._require_transition_run(
                run.id, RunState.RUNNING, RunState.SUCCEEDED
            )
        return run

    async def _cancel_from(self, current: RunState, run: WorkflowRun) -> WorkflowRun:
        """Cancels before execution started (run still PENDING)."""
        if not can_transition(current, RunState.CANCELLED):
            raise WorkflowStateTransitionError(current.value, RunState.CANCELLED.value)
        for step_run in run.step_runs:
            if RunState(step_run.state) == RunState.PENDING:
                await self._repository.transition_step_run(
                    step_run.id, RunState.CANCELLED
                )
        return await self._require_transition_run(
            run.id, current, RunState.CANCELLED
        )

    async def _sweep_pending(
        self,
        run: WorkflowRun,
        states: dict[uuid.UUID, RunState],
    ) -> None:
        """Cancels every never-executed step so no pendings dangle."""
        for step_run in sorted(run.step_runs, key=lambda sr: sr.position):
            if states[step_run.id] == RunState.PENDING:
                await self._repository.transition_step_run(
                    step_run.id, RunState.CANCELLED
                )

    async def _require_transition_run(
        self,
        run_id: uuid.UUID,
        current: RunState,
        to_state: RunState,
        *,
        error_message: str | None = None,
    ) -> WorkflowRun:
        if not can_transition(current, to_state):
            raise WorkflowStateTransitionError(current.value, to_state.value)
        updated = await self._repository.transition_run(
            run_id, to_state, error_message=error_message
        )
        assert updated is not None  # engine loaded this run at entry
        return updated


def _graph_of(
    workflow: Workflow,
) -> tuple[
    list[str],
    list[tuple[str, str]],
    dict[str, set[str]],
    dict[str, WorkflowStep],
]:
    """Name/edge projections of a stored workflow plus upstream index."""
    steps = sorted(workflow.steps, key=lambda step: step.position)
    id_to_name = {step.id: step.name for step in steps}
    names = [step.name for step in steps]
    name_edges = [
        (id_to_name[dep.from_step_id], id_to_name[dep.to_step_id])
        for dep in workflow.dependencies
    ]
    upstream_of: dict[str, set[str]] = defaultdict(set)
    for source, target in name_edges:
        upstream_of[target].add(source)
    step_by_name = {step.name: step for step in steps}
    return names, name_edges, upstream_of, step_by_name


__all__ = ["DAGExecutionEngine", "ExecutionRunStore"]
