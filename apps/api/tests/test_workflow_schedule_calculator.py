from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from genomeai_api.workflows.scheduling import (
    CronOccurrenceCalculator,
    ScheduleSpec,
    SystemClock,
)


@pytest.fixture
def calculator() -> CronOccurrenceCalculator:
    return CronOccurrenceCalculator()


def _once(run_at: datetime, timezone_name: str = "UTC") -> ScheduleSpec:
    return ScheduleSpec(schedule_type="once", run_at=run_at, timezone_name=timezone_name)


def _recurring(expression: str, timezone_name: str = "UTC") -> ScheduleSpec:
    return ScheduleSpec(
        schedule_type="recurring", expression=expression, timezone_name=timezone_name
    )


# --- validation -------------------------------------------------------


def test_valid_one_time_spec_has_no_issues(calculator: CronOccurrenceCalculator) -> None:
    spec = _once(datetime(2026, 9, 1, 8, 0, tzinfo=UTC))

    assert calculator.validate(spec) == []


def test_valid_recurring_spec_has_no_issues(calculator: CronOccurrenceCalculator) -> None:
    assert calculator.validate(_recurring("0 9 * * *")) == []


def test_one_time_requires_run_at(calculator: CronOccurrenceCalculator) -> None:
    issues = calculator.validate(
        ScheduleSpec(schedule_type="once", timezone_name="UTC")
    )

    assert any(issue.startswith("missing_run_at") for issue in issues)


def test_one_time_rejects_naive_run_at(calculator: CronOccurrenceCalculator) -> None:
    issues = calculator.validate(_once(datetime(2026, 9, 1, 8, 0)))

    assert any(issue.startswith("naive_run_at") for issue in issues)


def test_one_time_rejects_expression(calculator: CronOccurrenceCalculator) -> None:
    issues = calculator.validate(
        ScheduleSpec(
            schedule_type="once",
            run_at=datetime(2026, 9, 1, 8, 0, tzinfo=UTC),
            expression="0 9 * * *",
        )
    )

    assert any(issue.startswith("unexpected_expression") for issue in issues)


def test_recurring_requires_expression(calculator: CronOccurrenceCalculator) -> None:
    issues = calculator.validate(ScheduleSpec(schedule_type="recurring"))

    assert any(issue.startswith("missing_expression") for issue in issues)


def test_recurring_rejects_invalid_cron(calculator: CronOccurrenceCalculator) -> None:
    issues = calculator.validate(_recurring("not a cron"))

    assert any(issue.startswith("invalid_expression") for issue in issues)
    assert any("'not a cron'" in issue for issue in issues)


def test_recurring_rejects_run_at(calculator: CronOccurrenceCalculator) -> None:
    issues = calculator.validate(
        ScheduleSpec(
            schedule_type="recurring",
            expression="0 9 * * *",
            run_at=datetime(2026, 9, 1, 8, 0, tzinfo=UTC),
        )
    )

    assert any(issue.startswith("unexpected_run_at") for issue in issues)


def test_unknown_timezone_is_reported(calculator: CronOccurrenceCalculator) -> None:
    issues = calculator.validate(_recurring("0 9 * * *", "Mars/Olympus_Mons"))

    assert any(issue.startswith("invalid_timezone") for issue in issues)


def test_valid_timezone_names_pass(calculator: CronOccurrenceCalculator) -> None:
    assert calculator.validate(_recurring("0 9 * * *", "Europe/Berlin")) == []
    assert calculator.validate(_recurring("0 9 * * *", "America/New_York")) == []


# --- occurrence calculation -------------------------------------------


def test_once_returns_absolute_time_until_passed(
    calculator: CronOccurrenceCalculator,
) -> None:
    run_at = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)

    nxt = calculator.next_occurrence(_once(run_at), after=datetime(2026, 8, 24, tzinfo=UTC))

    assert nxt == run_at
    assert calculator.next_occurrence(
        _once(run_at), after=datetime(2026, 9, 2, tzinfo=UTC)
    ) is None


def test_once_boundary_exact_match_is_exhausted(
    calculator: CronOccurrenceCalculator,
) -> None:
    run_at = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)

    # Strictly-after semantics: an occurrence exactly at `after` is gone.
    assert (
        calculator.next_occurrence(_once(run_at), after=run_at) is None
    )


def test_recurring_next_in_utc(calculator: CronOccurrenceCalculator) -> None:
    after = datetime(2026, 8, 24, 10, 30, tzinfo=UTC)

    nxt = calculator.next_occurrence(_recurring("30 12 * * *"), after=after)

    assert nxt == datetime(2026, 8, 24, 12, 30, tzinfo=UTC)


def test_recurring_multiple_occurrences_advance(
    calculator: CronOccurrenceCalculator,
) -> None:
    spec = _recurring("*/15 * * * *")
    cursor = datetime(2026, 8, 24, 10, 0, tzinfo=UTC)

    occurrences = []
    for _ in range(4):
        cursor = calculator.next_occurrence(spec, after=cursor)
        assert cursor is not None
        occurrences.append(cursor)

    assert [o.minute for o in occurrences] == [15, 30, 45, 0]
    assert occurrences[3].hour == 11


def test_recurring_respects_timezone_offset(calculator: CronOccurrenceCalculator) -> None:
    # 09:00 in Kathmandu (+05:45) is 03:15 UTC.
    spec = _recurring("0 9 * * *", "Asia/Kathmandu")

    nxt = calculator.next_occurrence(spec, after=datetime(2026, 8, 24, 0, 0, tzinfo=UTC))

    assert nxt == datetime(2026, 8, 24, 3, 15, tzinfo=UTC)


def test_recurring_handles_dst_spring_forward(
    calculator: CronOccurrenceCalculator,
) -> None:
    # America/New_York springs forward on 2026-03-08 (02:00 -> 03:00 local).
    spec = _recurring("0 9 * * *", "America/New_York")
    before = datetime(2026, 3, 7, 9, 0, tzinfo=ZoneInfo("America/New_York"))

    nxt = calculator.next_occurrence(spec, after=before)
    assert nxt is not None
    assert nxt.astimezone(ZoneInfo("America/New_York")) == datetime(
        2026, 3, 8, 9, 0, tzinfo=ZoneInfo("America/New_York")
    )
    # Winter offset -05:00, day after spring-forward -04:00 at the same
    # wall-clock hour — the UTC instant shifted accordingly.
    local = nxt.astimezone(ZoneInfo("America/New_York"))
    assert local.utcoffset() == timedelta(hours=-4)


def test_recurring_daily_boundary_rolls_to_next_day(
    calculator: CronOccurrenceCalculator,
) -> None:
    spec = _recurring("0 0 * * *")
    exactly_midnight = datetime(2026, 8, 24, 0, 0, tzinfo=UTC)

    nxt = calculator.next_occurrence(spec, after=exactly_midnight)

    assert nxt == datetime(2026, 8, 25, 0, 0, tzinfo=UTC)


def test_system_clock_returns_utc() -> None:
    now = SystemClock().now()

    assert now.tzinfo is not None
    assert now.utcoffset() == UTC.utcoffset(now)
