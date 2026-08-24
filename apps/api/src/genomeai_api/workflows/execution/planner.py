"""Deterministic ready-step resolution for DAG execution.

Pure functions only — the planner decides WHICH step may run next given the
current step-run states and the dependency edges. It never executes, never
persists, and always returns candidates in the same order (persisted
`position`, then name as a stable tie-break).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from genomeai_api.workflows.types import RunState


@dataclass(frozen=True)
class PlannedStep:
    """One step of a run as seen by the planner."""

    step_run_id: uuid.UUID
    name: str
    position: int
    state: RunState
    upstream: tuple[str, ...]  # direct predecessor step names


def ready_steps(steps: list[PlannedStep]) -> list[PlannedStep]:
    """Steps eligible for execution right now.

    A step is ready when its own run is still PENDING and every direct
    predecessor has SUCCEEDED. Steps that are RUNNING/terminal are never
    returned; steps whose predecessors have not all succeeded stay blocked.
    """
    by_name = {step.name: step for step in steps}
    ready = [
        step
        for step in steps
        if step.state == RunState.PENDING
        and all(by_name[upstream].state == RunState.SUCCEEDED for upstream in step.upstream)
    ]
    return sorted(ready, key=lambda step: (step.position, step.name))


def pending_steps(steps: list[PlannedStep]) -> list[PlannedStep]:
    """All not-yet-executed steps, in deterministic order."""
    return sorted(
        (step for step in steps if step.state == RunState.PENDING),
        key=lambda step: (step.position, step.name),
    )


def all_succeeded(steps: list[PlannedStep]) -> bool:
    return bool(steps) and all(step.state == RunState.SUCCEEDED for step in steps)


__all__ = ["PlannedStep", "all_succeeded", "pending_steps", "ready_steps"]
