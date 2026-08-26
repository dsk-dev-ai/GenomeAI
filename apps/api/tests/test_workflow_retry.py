"""Phase 7.5 domain tests: failure classification, backoff, retry policy.

These pin the deterministic core that the Worker consults — classification
must be pure and reproducible, backoff must never depend on wall-clock or
randomness, and the policy must encode the hard rules (cancellation never
retries, infrastructure never auto-retries, budget is respected).
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from genomeai_api.workflows.errors import (
    PermanentExecutionError,
    QueueUnavailableError,
    TransientExecutionError,
    WorkflowValidationError,
)
from genomeai_api.workflows.retry import (
    ExponentialBackoff,
    FailureClass,
    FailureObservation,
    FixedBackoff,
    RetryPolicy,
    classify_failure,
)

# --- failure classification ---------------------------------------------------


class _SomeUnknownError(Exception):
    pass


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (TransientExecutionError("timeout"), FailureClass.TRANSIENT),
        (PermanentExecutionError("bad shape"), FailureClass.PERMANENT),
        (QueueUnavailableError("redis down"), FailureClass.INFRASTRUCTURE),
        (WorkflowValidationError("no edges", ["missing edges"]), FailureClass.INVALID_WORKFLOW),
        (TimeoutError("step timed out"), FailureClass.TRANSIENT),
        (ConnectionError("peer reset"), FailureClass.TRANSIENT),
        (_SomeUnknownError("???"), FailureClass.PERMANENT),  # conservative default
    ],
)
def test_classification_by_exception_type(exc: Exception, expected: FailureClass) -> None:
    assert classify_failure(FailureObservation(exc)) is expected


def test_cancelled_run_state_overrides_any_exception() -> None:
    # Even a transient-looking exception during a cancelled run stays a
    # cancellation — cancellation NEVER becomes a retry.
    exc = TransientExecutionError("cancelled mid-flight")
    assert (
        classify_failure(FailureObservation(exc, run_state="cancelled"))
        is FailureClass.CANCELLATION
    )


def test_classification_is_deterministic() -> None:
    exc = TransientExecutionError("same input")
    first = classify_failure(FailureObservation(exc))
    for _ in range(5):
        assert classify_failure(FailureObservation(exc)) is first


# --- backoff -------------------------------------------------------------------


def test_fixed_backoff_returns_same_delay_every_time() -> None:
    policy = FixedBackoff(timedelta(seconds=7))
    for retry in range(1, 6):
        assert policy.delay_for(retry) == timedelta(seconds=7)


def test_exponential_backoff_grows_deterministically() -> None:
    policy = ExponentialBackoff(timedelta(seconds=1))
    assert policy.delay_for(1) == timedelta(seconds=1)
    assert policy.delay_for(2) == timedelta(seconds=2)
    assert policy.delay_for(3) == timedelta(seconds=4)
    assert policy.delay_for(4) == timedelta(seconds=8)


def test_exponential_backoff_caps_at_maximum_delay() -> None:
    policy = ExponentialBackoff(
        initial=timedelta(seconds=1),
        multiplier=2.0,
        max_delay=timedelta(seconds=5),
    )
    assert policy.delay_for(1) == timedelta(seconds=1)
    assert policy.delay_for(4) == timedelta(seconds=5)
    assert policy.delay_for(50) == timedelta(seconds=5)  # never exceeds cap


def test_backoffs_are_deterministic() -> None:
    exp = ExponentialBackoff(timedelta(seconds=2))
    assert [exp.delay_for(n) for n in range(1, 8)] == [
        exp.delay_for(n) for n in range(1, 8)
    ]


@pytest.mark.parametrize(
    "factory",
    [
        lambda: FixedBackoff(timedelta(seconds=-1)),
        lambda: ExponentialBackoff(initial=timedelta(seconds=-1)),
        lambda: ExponentialBackoff(multiplier=0.5),
        lambda: ExponentialBackoff(max_delay=timedelta(seconds=0)),
    ],
)
def test_invalid_backoff_configuration_is_rejected(factory: object) -> None:
    with pytest.raises(ValueError):
        factory()  # type: ignore[operator]


def test_backoff_rejects_non_positive_retry_number() -> None:
    with pytest.raises(ValueError):
        ExponentialBackoff().delay_for(0)


# --- retry policy ---------------------------------------------------------------


def _transient() -> FailureObservation:
    return FailureObservation(TransientExecutionError("flaky"))


def test_policy_with_zero_extra_retries_never_schedules() -> None:
    decision = RetryPolicy(max_attempts=1).decide(FailureClass.TRANSIENT, 1)
    assert decision.retry is False
    assert "exhausted" in decision.reason


def test_policy_allows_one_retry_then_exhausts() -> None:
    policy = RetryPolicy(max_attempts=2, backoff=FixedBackoff(timedelta(seconds=3)))
    first = policy.decide(FailureClass.TRANSIENT, attempts_made=1)
    assert first.retry is True
    assert first.delay == timedelta(seconds=3)
    second = policy.decide(FailureClass.TRANSIENT, attempts_made=2)
    assert second.retry is False


def test_policy_reports_remaining_budget_in_decision_reason() -> None:
    decision = RetryPolicy(max_attempts=4).decide(FailureClass.TRANSIENT, 2)
    assert decision.retry is True
    assert "attempt 3 of 4" in decision.reason


def test_permanent_failures_are_not_retryable_by_default() -> None:
    decision = RetryPolicy(max_attempts=5).decide(FailureClass.PERMANENT, 1)
    assert decision.retry is False


def test_cancellations_are_never_retried_even_with_custom_retryable_set() -> None:
    # Hard rule: no configuration can talk the policy into retrying a
    # cancelled run.
    policy = RetryPolicy(
        max_attempts=9,
        retryable=frozenset(FailureClass),  # everything "retryable"
    )
    assert policy.decide(FailureClass.CANCELLATION, 1).retry is False


def test_infrastructure_failures_are_not_auto_retried() -> None:
    decision = RetryPolicy(max_attempts=5).decide(FailureClass.INFRASTRUCTURE, 1)
    assert decision.retry is False


def test_invalid_workflow_failures_are_not_retryable_by_default() -> None:
    decision = RetryPolicy(max_attempts=5).decide(
        FailureClass.INVALID_WORKFLOW, 1
    )
    assert decision.retry is False


def test_custom_retryable_set_can_opt_other_classes_in() -> None:
    policy = RetryPolicy(
        max_attempts=3,
        retryable=frozenset({FailureClass.TRANSIENT, FailureClass.PERMANENT}),
    )
    assert policy.decide(FailureClass.PERMANENT, 1).retry is True
    assert policy.decide(FailureClass.INVALID_WORKFLOW, 1).retry is False


def test_policy_validates_max_attempts() -> None:
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=0)


def test_worker_default_policy_matches_phase_74_behaviour() -> None:
    """The worker's implicit default (max_attempts=1) disables retries."""

    # Constructed without an explicit policy the worker must behave like
    # Phase 7.4: any execution failure is final.
    default = RetryPolicy(max_attempts=1)
    assert default.decide(FailureClass.TRANSIENT, 1).retry is False
