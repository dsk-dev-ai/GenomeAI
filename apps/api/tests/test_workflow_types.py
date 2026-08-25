from __future__ import annotations

import pytest
from genomeai_api.workflows.types import (
    JOB_STATE_TRANSITIONS,
    RUN_STATE_TRANSITIONS,
    JobState,
    RunState,
    WorkflowStatus,
    can_transition,
    can_transition_job,
    is_terminal,
)


def test_run_state_values() -> None:
    assert {state.value for state in RunState} == {
        "pending",
        "running",
        "succeeded",
        "failed",
        "cancelled",
    }


def test_workflow_status_values() -> None:
    assert {status.value for status in WorkflowStatus} == {
        "draft",
        "active",
        "archived",
    }


def test_pending_can_start_or_cancel() -> None:
    assert can_transition(RunState.PENDING, RunState.RUNNING)
    assert can_transition(RunState.PENDING, RunState.CANCELLED)
    assert not can_transition(RunState.PENDING, RunState.SUCCEEDED)
    assert not can_transition(RunState.PENDING, RunState.FAILED)


def test_running_can_finish_any_way() -> None:
    assert can_transition(RunState.RUNNING, RunState.SUCCEEDED)
    assert can_transition(RunState.RUNNING, RunState.FAILED)
    assert can_transition(RunState.RUNNING, RunState.CANCELLED)
    assert not can_transition(RunState.RUNNING, RunState.PENDING)


@pytest.mark.parametrize("terminal", list(RunState)[2:])
def test_terminal_states_transition_nowhere(terminal: RunState) -> None:
    for next_state in RunState:
        assert not can_transition(terminal, next_state)


def test_is_terminal_flags_exactly_the_final_states() -> None:
    assert is_terminal(RunState.SUCCEEDED)
    assert is_terminal(RunState.FAILED)
    assert is_terminal(RunState.CANCELLED)
    assert not is_terminal(RunState.PENDING)
    assert not is_terminal(RunState.RUNNING)


def test_transition_table_covers_all_states_and_terminals_are_empty() -> None:
    assert set(RUN_STATE_TRANSITIONS) == set(RunState)
    for state, targets in RUN_STATE_TRANSITIONS.items():
        if is_terminal(state):
            assert targets == frozenset()
        else:
            assert targets


# --- Phase 7.4: job state vocabulary ------------------------------------


def test_job_state_values() -> None:
    assert {state.value for state in JobState} == {
        "queued",
        "running",
        "completed",
        "failed",
    }


def test_queued_job_can_only_start() -> None:
    assert can_transition_job(JobState.QUEUED, JobState.RUNNING)
    for terminal in (JobState.COMPLETED, JobState.FAILED):
        assert not can_transition_job(JobState.QUEUED, terminal)


def test_running_job_must_finish() -> None:
    assert can_transition_job(JobState.RUNNING, JobState.COMPLETED)
    assert can_transition_job(JobState.RUNNING, JobState.FAILED)
    assert not can_transition_job(JobState.RUNNING, JobState.QUEUED)


def test_finished_jobs_never_move_again() -> None:
    for terminal in (JobState.COMPLETED, JobState.FAILED):
        for next_state in JobState:
            assert not can_transition_job(terminal, next_state)


def test_job_transition_table_covers_all_states_and_terminals_are_empty() -> None:
    assert set(JOB_STATE_TRANSITIONS) == set(JobState)
    for state, targets in JOB_STATE_TRANSITIONS.items():
        if state in (JobState.COMPLETED, JobState.FAILED):
            assert targets == frozenset()
        else:
            assert targets
