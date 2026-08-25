"""Scheduling domain: clocks, schedule specs, and occurrence calculation.

Phase 7.3 determines WHEN runs should start — nothing here executes
workflows or touches infrastructure. Recurring schedules use standard
5-field cron expressions evaluated by `croniter`; parsing/validation is
isolated behind the `OccurrenceCalculator` abstraction so the expression
language can be swapped without touching the scheduler service.

All arithmetic uses timezone-aware datetimes; naive values are rejected.
Occurrence times are computed in the schedule's own timezone and
normalized to UTC at the boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from zoneinfo import ZoneInfo

from croniter import croniter

from genomeai_api.workflows.types import ScheduleType

DEFAULT_TIMEZONE = "UTC"


class Clock(Protocol):
    """Injectable time source so core logic never reads the system clock."""

    def now(self) -> datetime:
        """Current time as a timezone-aware UTC datetime."""
        ...


class SystemClock:
    """Production clock."""

    def now(self) -> datetime:
        return datetime.now(UTC)


@dataclass(frozen=True)
class ScheduleSpec:
    """Validated-shape description of when a schedule fires."""

    schedule_type: ScheduleType
    expression: str | None = None
    run_at: datetime | None = None
    timezone_name: str = DEFAULT_TIMEZONE


class OccurrenceCalculator(Protocol):
    """Pure occurrence math for a schedule specification."""

    def validate(self, spec: ScheduleSpec) -> list[str]:
        """All deterministic issues with the spec (empty when valid)."""
        ...

    def next_occurrence(self, spec: ScheduleSpec, *, after: datetime) -> datetime | None:
        """First occurrence strictly after `after`, or None when exhausted."""
        ...


class CronOccurrenceCalculator:
    """Standard cron evaluation via croniter, resolved in a named timezone."""

    def validate(self, spec: ScheduleSpec) -> list[str]:
        issues: list[str] = []
        if spec.schedule_type == ScheduleType.ONCE:
            if spec.run_at is None:
                issues.append("missing_run_at: one-time schedules require run_at")
            elif spec.run_at.tzinfo is None or spec.run_at.utcoffset() is None:
                issues.append("naive_run_at: run_at must be timezone-aware")
            if spec.expression is not None:
                issues.append("unexpected_expression: one-time schedules take no expression")
        else:
            if not spec.expression:
                issues.append("missing_expression: recurring schedules require a cron expression")
            elif not self._valid_cron(spec.expression):
                issues.append(
                    f"invalid_expression: '{spec.expression}' is not a valid cron expression"
                )
            if spec.run_at is not None:
                issues.append("unexpected_run_at: recurring schedules take no run_at")
        issues.extend(self._timezone_issues(spec.timezone_name))
        return issues

    def next_occurrence(self, spec: ScheduleSpec, *, after: datetime) -> datetime | None:
        if spec.schedule_type == ScheduleType.ONCE:
            if spec.run_at is None or not spec.run_at > after:
                return None
            return spec.run_at.astimezone(UTC)
        assert spec.expression is not None  # validated before evaluation
        local_after = after.astimezone(ZoneInfo(spec.timezone_name))
        iterator = croniter(spec.expression, local_after)
        return iterator.get_next(datetime).astimezone(UTC)

    def _valid_cron(self, expression: str) -> bool:
        try:
            croniter(expression)
        except (ValueError, KeyError):
            return False
        return True

    def _timezone_issues(self, timezone_name: str) -> list[str]:
        try:
            ZoneInfo(timezone_name)
        except (ValueError, KeyError):
            return [f"invalid_timezone: '{timezone_name}' is not a known IANA timezone"]
        return []


__all__ = [
    "DEFAULT_TIMEZONE",
    "Clock",
    "CronOccurrenceCalculator",
    "OccurrenceCalculator",
    "ScheduleSpec",
    "SystemClock",
]
