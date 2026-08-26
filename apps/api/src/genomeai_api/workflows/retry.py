"""Retry policy, failure classification, and backoff (Phase 7.5).

Pure domain logic — no I/O, no clock reads, fully deterministic and
testable. The worker ASKS this module whether a failure may be retried
and how long to wait; retry behaviour is never hard-coded there.

Failure classes separate WHAT went wrong from WHETHER to retry:

- ``transient``        temporary conditions (timeouts, connection loss)
- ``permanent``        deterministic failures that will not change
- ``cancellation``     the run was cancelled — NEVER auto-retried
- ``invalid_workflow`` bad definition/configuration — non-retryable by
                       default because retrying cannot fix the input
- ``infrastructure``   queue/backend problems — not execution failures;
                       never attributed to the run itself

Classification is driven by exception types plus the observed run state,
so the same input always yields the same class.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from enum import StrEnum
from typing import Protocol

from genomeai_api.workflows.errors import (
    JobDecodeError,
    PermanentExecutionError,
    QueueUnavailableError,
    TransientExecutionError,
    WorkflowValidationError,
)


class FailureClass(StrEnum):
    """Deterministic category of one workflow-run failure."""

    TRANSIENT = "transient"
    PERMANENT = "permanent"
    CANCELLATION = "cancellation"
    INVALID_WORKFLOW = "invalid_workflow"
    INFRASTRUCTURE = "infrastructure"


# Exceptions whose TYPE alone determines the class. Anything unmapped is
# classified PERMANENT (conservative default: unknown failures must not
# loop forever). Run-state evidence can override via classify_failure().
_EXCEPTION_CLASSES: tuple[tuple[type[BaseException], FailureClass], ...] = (
    # Infrastructure first: backend outages are not run failures.
    (QueueUnavailableError, FailureClass.INFRASTRUCTURE),
    (JobDecodeError, FailureClass.INFRASTRUCTURE),
    # Explicit executor markers.
    (TransientExecutionError, FailureClass.TRANSIENT),
    (PermanentExecutionError, FailureClass.PERMANENT),
    # Bad definition/configuration surfaced during execution.
    (WorkflowValidationError, FailureClass.INVALID_WORKFLOW),
    # Common transient OS/network conditions.
    (TimeoutError, FailureClass.TRANSIENT),
    (ConnectionError, FailureClass.TRANSIENT),
)


@dataclass(frozen=True)
class FailureObservation:
    """Everything known about ONE failure, before any retry decision."""

    exception: BaseException
    run_state: str | None = None  # observed state AFTER the failure attempt


def _classify_exception(exc: BaseException) -> FailureClass | None:
    for exc_type, failure_class in _EXCEPTION_CLASSES:
        if isinstance(exc, exc_type):
            return failure_class
    return None


def classify_failure(observation: FailureObservation) -> FailureClass:
    """Deterministically maps one failure observation to a class.

    Order of precedence:
    1. The run was cancelled → CANCELLATION regardless of the exception
       (a cancelled run must never look like a retryable failure).
    2. Exception type mapping (see _EXCEPTION_CLASSES).
    3. Unknown exceptions → PERMANENT (conservative default).
    """
    if observation.run_state == "cancelled":
        return FailureClass.CANCELLATION
    mapped = _classify_exception(observation.exception)
    return mapped or FailureClass.PERMANENT


# --- backoff -------------------------------------------------------------


class Backoff(Protocol):
    """Deterministic delay strategy for the Nth retry (N starts at 1)."""

    def delay_for(self, retry_number: int) -> timedelta: ...


@dataclass(frozen=True)
class FixedBackoff:
    """Same delay for every retry."""

    delay: timedelta = field(default_factory=lambda: timedelta(seconds=1))

    def __post_init__(self) -> None:
        if self.delay < timedelta(0):
            raise ValueError("backoff delay must be >= 0")

    def delay_for(self, retry_number: int) -> timedelta:
        del retry_number
        return self.delay


@dataclass(frozen=True)
class ExponentialBackoff:
    """initial * multiplier^(retry-1), capped at max_delay.

    No jitter: identical inputs yield identical delays so tests and
    operators can predict exactly when a retry fires.
    """

    initial: timedelta = field(default_factory=lambda: timedelta(seconds=1))
    multiplier: float = 2.0
    max_delay: timedelta = field(default_factory=lambda: timedelta(minutes=1))

    def __post_init__(self) -> None:
        if self.initial < timedelta(0):
            raise ValueError("backoff initial must be >= 0")
        if self.multiplier < 1.0:
            raise ValueError("backoff multiplier must be >= 1.0")
        if self.max_delay < self.initial:
            raise ValueError("backoff max_delay must be >= initial")

    def delay_for(self, retry_number: int) -> timedelta:
        if retry_number < 1:
            raise ValueError("retry_number starts at 1")
        # Compare in float space FIRST: constructing a timedelta from an
        # enormous exponent overflows before min() could clamp it.
        delay_seconds = self.initial.total_seconds() * (
            self.multiplier ** (retry_number - 1)
        )
        if delay_seconds > self.max_delay.total_seconds():
            return self.max_delay
        return timedelta(seconds=delay_seconds)


# --- policy ----------------------------------------------------------------


@dataclass(frozen=True)
class RetryDecision:
    """Outcome of evaluating the policy for one failed attempt."""

    retry: bool
    reason: str
    delay: timedelta = field(default_factory=timedelta)

    @classmethod
    def no_retry(cls, reason: str) -> RetryDecision:
        return cls(retry=False, reason=reason)


@dataclass(frozen=True)
class RetryPolicy:
    """Whether and when failures may be retried.

    ``max_attempts`` counts EXECUTION attempts in total (not retries):
    1 disables retries, 2 allows exactly one retry, and so on. Only
    classifications listed in ``retryable`` are ever retried; attempts is
    compared against the run's persisted attempt count, so duplicate
    messages or crashes can never exceed the budget.
    """

    max_attempts: int = 1
    retryable: frozenset[FailureClass] = frozenset({FailureClass.TRANSIENT})
    backoff: Backoff = field(default_factory=ExponentialBackoff)

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")

    def decide(
        self, classification: FailureClass, attempts_made: int
    ) -> RetryDecision:
        """Decides retry eligibility after ``attempts_made`` executions."""
        if classification is FailureClass.CANCELLATION:
            return RetryDecision.no_retry("cancelled runs are never retried")
        if classification is FailureClass.INFRASTRUCTURE:
            return RetryDecision.no_retry(
                "infrastructure failures are not retried automatically"
            )
        if classification not in self.retryable:
            return RetryDecision.no_retry(
                f"failure class '{classification.value}' is not retryable"
            )
        if attempts_made >= self.max_attempts:
            return RetryDecision.no_retry(
                f"retry budget exhausted ({attempts_made}/{self.max_attempts} attempts)"
            )
        next_attempt = attempts_made + 1
        return RetryDecision(
            retry=True,
            reason=f"attempt {next_attempt} of {self.max_attempts} scheduled",
            # Backoff counts RETRIES (1st retry, 2nd retry, ...), not
            # total attempts: after one failed execution we are about to
            # schedule retry #1.
            delay=self.backoff.delay_for(attempts_made),
        )


__all__ = [
    "Backoff",
    "ExponentialBackoff",
    "FailureClass",
    "FailureObservation",
    "FixedBackoff",
    "RetryDecision",
    "RetryPolicy",
    "classify_failure",
]
