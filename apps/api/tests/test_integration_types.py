from __future__ import annotations

import pytest
from genomeai_api.integration.types import (
    JOB_STATE_TRANSITIONS,
    AccessMode,
    EntityType,
    JobState,
    SourceType,
    SyncStatus,
    can_transition,
)


@pytest.mark.parametrize(
    ("enum_cls", "value"),
    [
        (SourceType, "genome"),
        (SourceType, "chemical"),
        (AccessMode, "bulk"),
        (EntityType, "publication"),
        (SyncStatus, "failed"),
    ],
)
def test_enum_values_are_stable_strings(enum_cls: type, value: str) -> None:
    assert enum_cls(value).value == value


def test_str_members_compare_as_their_values() -> None:
    assert SourceType.GENOME == "genome"
    assert JobState.RUNNING == "running"


def test_terminal_states_have_no_outgoing_transitions() -> None:
    for terminal in (JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED):
        assert JOB_STATE_TRANSITIONS[terminal] == frozenset()


def test_pending_can_start_or_cancel() -> None:
    assert can_transition(JobState.PENDING, JobState.RUNNING)
    assert can_transition(JobState.PENDING, JobState.CANCELLED)
    assert not can_transition(JobState.PENDING, JobState.SUCCEEDED)


def test_running_can_finish_any_way() -> None:
    assert can_transition(JobState.RUNNING, JobState.SUCCEEDED)
    assert can_transition(JobState.RUNNING, JobState.FAILED)
    assert can_transition(JobState.RUNNING, JobState.CANCELLED)
    assert not can_transition(JobState.RUNNING, JobState.PENDING)
