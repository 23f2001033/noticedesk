from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.models.case import NoticeType

IST = ZoneInfo("Asia/Kolkata")

# Statutory default reply windows, in days from notice_date, used only when
# the extractor could not find an explicit due_date on the notice itself.
#
# PROVISIONAL -- ASMT-10's 30-day window (Rule 99(1) r/w Section 61) is the
# one entry here verified with reasonable confidence; DRC-01A and DRC-01 are
# placeholders pending sign-off from Aman or a CA advisor. Per docs/SPEC.md
# #5 ("never silently guess a deadline"), any case using one of these values
# must carry due_date_source="statutory_default" and due_date_confirmed=False
# on the Case record (see app/models/case.py) -- the UI must always surface
# these for CA confirmation rather than presenting them as final.
STATUTORY_DEFAULT_REPLY_DAYS: dict[NoticeType, int] = {
    NoticeType.ASMT_10: 30,
    NoticeType.DRC_01A: 15,
    NoticeType.DRC_01: 30,
}

REMINDER_OFFSETS_DAYS: tuple[int, ...] = (7, 3, 1)
DEFAULT_REMINDER_SEND_TIME = time(9, 30)
QUIET_HOURS_START = time(21, 0)
QUIET_HOURS_END = time(9, 0)


class NoStatutoryDefaultError(ValueError):
    """No statutory default reply window is configured for this notice type."""


def compute_statutory_default_due_date(notice_type: NoticeType, notice_date: datetime) -> datetime:
    days = STATUTORY_DEFAULT_REPLY_DAYS.get(notice_type)
    if days is None:
        raise NoStatutoryDefaultError(
            f"No statutory default reply window configured for {notice_type!r}; "
            "due date must be set manually by the CA."
        )
    return notice_date + timedelta(days=days)


def is_quiet_hours(moment: datetime) -> bool:
    """Quiet hours are 21:00-09:00 IST (docs/SPEC.md #5)."""
    local_time = moment.astimezone(IST).time()
    return local_time >= QUIET_HOURS_START or local_time < QUIET_HOURS_END


def next_available_send_time(moment: datetime) -> datetime:
    """Push a moment that falls in quiet hours to the next 09:00 IST; otherwise no-op."""
    if not is_quiet_hours(moment):
        return moment

    local = moment.astimezone(IST)
    if local.time() >= QUIET_HOURS_START:
        next_open_date: date = local.date() + timedelta(days=1)
    else:
        next_open_date = local.date()
    send_at_ist = datetime.combine(next_open_date, QUIET_HOURS_END, tzinfo=IST)
    return send_at_ist.astimezone(moment.tzinfo or IST)


def compute_reminder_schedule(due_date: datetime) -> list[datetime]:
    """T-7/T-3/T-1 reminder send times, each nudged out of quiet hours if needed."""
    due_local = due_date.astimezone(IST)
    schedule = []
    for offset in REMINDER_OFFSETS_DAYS:
        candidate_date = due_local.date() - timedelta(days=offset)
        candidate = datetime.combine(candidate_date, DEFAULT_REMINDER_SEND_TIME, tzinfo=IST)
        schedule.append(next_available_send_time(candidate))
    return schedule


def is_overdue(due_date: datetime, as_of: datetime | None = None) -> bool:
    as_of = as_of or datetime.now(tz=IST)
    return as_of > due_date
