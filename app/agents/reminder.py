from dataclasses import dataclass
from datetime import datetime

from app.models.agent_run import AgentRunStatus
from app.models.case import Case, CaseStatus
from app.services.deadlines import IST, REMINDER_OFFSETS_DAYS
from app.services.firestore import get_firestore_client
from app.services.logging_runs import log_agent_run
from app.services.wa_client import send_whatsapp_message

# A reminder no longer makes sense once the CA has moved past needing one.
SKIP_STATUSES = frozenset(
    {
        CaseStatus.REPLY_FILED,
        CaseStatus.DROPPED,
        CaseStatus.ORDER_PASSED,
        CaseStatus.APPEAL_WINDOW,
        CaseStatus.CLOSED,
    }
)


@dataclass
class ReminderDecision:
    case_id: str
    firm_id: str
    offset_days: int
    action: str  # "sent" | "skipped"
    reason: str


def decide_reminders_for_cases(
    cases: list[tuple[str, Case]], as_of: datetime
) -> list[ReminderDecision]:
    """docs/SPEC.md #9 reminder agent: per deadline, decide send/skip.

    Pure decision logic, kept separate from the Firestore fetch and the
    WhatsApp send so it's cheaply unit-testable.
    """
    decisions = []
    for case_id, case in cases:
        if case.due_date is None:
            continue

        due_local = case.due_date.astimezone(IST).date()
        as_of_local = as_of.astimezone(IST).date()
        days_until_due = (due_local - as_of_local).days
        if days_until_due not in REMINDER_OFFSETS_DAYS:
            continue

        if case.status in SKIP_STATUSES:
            decisions.append(
                ReminderDecision(
                    case_id=case_id,
                    firm_id=case.firm_id,
                    offset_days=days_until_due,
                    action="skipped",
                    reason=f"case status is {case.status.value}, reminder no longer applies",
                )
            )
            continue

        decisions.append(
            ReminderDecision(
                case_id=case_id,
                firm_id=case.firm_id,
                offset_days=days_until_due,
                action="sent",
                reason=f"T-{days_until_due} reminder due",
            )
        )
    return decisions


def run_reminder_check(*, as_of: datetime | None = None) -> list[ReminderDecision]:
    """Scheduler-driven entry point (intended for a Cloud Scheduler ->
    POST /tasks/reminders task, not yet wired -- needs OIDC audience config
    that depends on a live GCP project, see PROGRESS.md).

    Fetches all cases, decides who needs a T-7/T-3/T-1 reminder today, sends
    via WhatsApp to the firm's registered number, and logs every decision.
    """
    as_of = as_of or datetime.now(tz=IST)
    db = get_firestore_client()

    cases = [(doc.id, Case(**doc.to_dict())) for doc in db.collection("cases").stream()]
    decisions = decide_reminders_for_cases(cases, as_of)

    for decision in decisions:
        status = AgentRunStatus.OK
        if decision.action == "sent":
            firm_doc = db.collection("firms").document(decision.firm_id).get()
            wa_number = (firm_doc.to_dict() or {}).get("wa_number") if firm_doc.exists else None
            if wa_number:
                send_whatsapp_message(
                    to=wa_number,
                    body=f"NoticeDesk reminder: case {decision.case_id} is due in "
                    f"{decision.offset_days} day(s).",
                )
            else:
                status = AgentRunStatus.FALLBACK
                decision.reason += " (no wa_number on file, message not sent)"

        log_agent_run(
            agent="reminder",
            trigger="scheduled_check",
            firm_id=decision.firm_id,
            case_id=decision.case_id,
            decision=decision.action,
            reasoning_digest=decision.reason,
            status=status,
        )

    return decisions
