from __future__ import annotations

import uuid
from dataclasses import replace

from genomeai_api.workflows.execution.planner import (
    PlannedStep,
    all_succeeded,
    pending_steps,
    ready_steps,
)
from genomeai_api.workflows.types import RunState


def _step(
    name: str,
    position: int,
    state: RunState = RunState.PENDING,
    upstream: tuple[str, ...] = (),
) -> PlannedStep:
    return PlannedStep(
        step_run_id=uuid.uuid4(),
        name=name,
        position=position,
        state=state,
        upstream=upstream,
    )


def test_linear_chain_releases_one_step_at_a_time() -> None:
    steps = [
        _step("a", 0),
        _step("b", 1, upstream=("a",)),
        _step("c", 2, upstream=("b",)),
    ]

    ready = ready_steps(steps)

    assert [step.name for step in ready] == ["a"]


def test_independent_steps_are_all_ready_in_position_order() -> None:
    steps = [_step("c", 2), _step("a", 0), _step("b", 1)]

    ready = ready_steps(steps)

    assert [step.name for step in ready] == ["a", "b", "c"]


def test_branching_releases_all_ready_branches() -> None:
    #      b
    #    a<
    #      c
    #       > d
    steps = [
        _step("a", 0),
        _step("b", 1, upstream=("a",)),
        _step("c", 2, upstream=("a",)),
        _step("d", 3, upstream=("b", "c")),
    ]

    first = ready_steps(steps)
    assert [step.name for step in first] == ["a"]

    a_succeeded = [replace(steps[0], state=RunState.SUCCEEDED)]
    second = ready_steps(a_succeeded + steps[1:])
    assert [step.name for step in second] == ["b", "c"]

    b_succeeded = [*a_succeeded, replace(steps[1], state=RunState.SUCCEEDED)]
    third = ready_steps(b_succeeded + [steps[2], steps[3]])
    assert [step.name for step in third] == ["c"]

    c_succeeded = [*b_succeeded, replace(steps[2], state=RunState.SUCCEEDED)]
    fourth = ready_steps(c_succeeded + [steps[3]])
    assert [step.name for step in fourth] == ["d"]


def test_join_blocked_until_every_upstream_succeeds() -> None:
    steps = [
        _step("b", 0, state=RunState.SUCCEEDED),
        _step("c", 1, state=RunState.RUNNING),
        _step("d", 2, upstream=("b", "c")),
    ]

    assert ready_steps(steps) == []


def test_completed_steps_never_reappear() -> None:
    steps = [
        _step("a", 0, state=RunState.SUCCEEDED),
        _step("b", 1, state=RunState.FAILED),
        _step("c", 2, state=RunState.CANCELLED),
        _step("d", 3, state=RunState.RUNNING),
    ]

    assert ready_steps(steps) == []
    assert pending_steps(steps) == []


def test_ties_break_by_name_at_equal_position() -> None:
    steps = [_step("beta", 0), _step("alpha", 0)]

    ready = ready_steps(steps)

    assert [step.name for step in ready] == ["alpha", "beta"]


def test_pending_preserves_order() -> None:
    steps = [
        _step("z", 3),
        _step("a", 1, state=RunState.SUCCEEDED),
        _step("m", 0),
    ]

    assert [step.name for step in pending_steps(steps)] == ["m", "z"]


def test_all_succeeded_requires_at_least_one_step() -> None:
    assert not all_succeeded([])
    assert all_succeeded([_step("a", 0, state=RunState.SUCCEEDED)])
    assert not all_succeeded([_step("a", 0)])
