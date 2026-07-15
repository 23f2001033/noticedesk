from datetime import datetime, timedelta

import pytest

from app.models.case import NoticeType
from app.services.deadlines import (
    IST,
    NoStatutoryDefaultError,
    compute_reminder_schedule,
    compute_statutory_default_due_date,
    is_overdue,
    is_quiet_hours,
    next_available_send_time,
)


def test_statutory_default_asmt10_is_30_days() -> None:
    notice_date = datetime(2026, 7, 1, tzinfo=IST)

    due_date = compute_statutory_default_due_date(NoticeType.ASMT_10, notice_date)

    assert due_date == notice_date + timedelta(days=30)


def test_statutory_default_raises_for_unmapped_notice_type() -> None:
    notice_date = datetime(2026, 7, 1, tzinfo=IST)

    with pytest.raises(NoStatutoryDefaultError):
        compute_statutory_default_due_date(NoticeType.OTHER, notice_date)


@pytest.mark.parametrize(
    ("hour", "minute", "expected"),
    [
        (21, 0, True),  # quiet hours start, inclusive
        (23, 30, True),
        (0, 0, True),
        (8, 59, True),
        (9, 0, False),  # quiet hours end, exclusive
        (12, 0, False),
        (20, 59, False),
    ],
)
def test_is_quiet_hours_boundaries(hour: int, minute: int, expected: bool) -> None:
    moment = datetime(2026, 7, 10, hour, minute, tzinfo=IST)

    assert is_quiet_hours(moment) is expected


def test_next_available_send_time_pushes_late_night_to_next_morning() -> None:
    moment = datetime(2026, 7, 10, 22, 0, tzinfo=IST)

    result = next_available_send_time(moment)

    assert result == datetime(2026, 7, 11, 9, 0, tzinfo=IST)


def test_next_available_send_time_pushes_early_morning_to_same_morning() -> None:
    moment = datetime(2026, 7, 10, 3, 0, tzinfo=IST)

    result = next_available_send_time(moment)

    assert result == datetime(2026, 7, 10, 9, 0, tzinfo=IST)


def test_next_available_send_time_noop_during_open_hours() -> None:
    moment = datetime(2026, 7, 10, 14, 0, tzinfo=IST)

    assert next_available_send_time(moment) == moment


def test_compute_reminder_schedule_returns_three_offsets_outside_quiet_hours() -> None:
    due_date = datetime(2026, 7, 20, 23, 59, tzinfo=IST)

    schedule = compute_reminder_schedule(due_date)

    assert len(schedule) == 3
    assert [d.date() for d in schedule] == [
        datetime(2026, 7, 13).date(),
        datetime(2026, 7, 17).date(),
        datetime(2026, 7, 19).date(),
    ]
    assert all(not is_quiet_hours(d) for d in schedule)


def test_is_overdue() -> None:
    due_date = datetime(2026, 7, 1, tzinfo=IST)

    assert is_overdue(due_date, as_of=datetime(2026, 7, 2, tzinfo=IST)) is True
    assert is_overdue(due_date, as_of=datetime(2026, 6, 30, tzinfo=IST)) is False
