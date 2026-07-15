from datetime import datetime
from enum import StrEnum

from app.models.case import Case, CaseStatus
from app.services.deadlines import IST
from app.services.firestore import get_firestore_client


class Urgency(StrEnum):
    OVERDUE = "overdue"
    DUE_SOON_3D = "due_soon_3d"
    DUE_SOON_7D = "due_soon_7d"
    ON_TRACK = "on_track"
    NO_DEADLINE = "no_deadline"


def compute_urgency(due_date: datetime | None, as_of: datetime | None = None) -> Urgency:
    """docs/SPEC.md #11: deadline urgency badges (overdue/<=3d/<=7d)."""
    if due_date is None:
        return Urgency.NO_DEADLINE

    as_of = as_of or datetime.now(tz=IST)
    days_left = (due_date.astimezone(IST).date() - as_of.astimezone(IST).date()).days

    if days_left < 0:
        return Urgency.OVERDUE
    if days_left <= 3:
        return Urgency.DUE_SOON_3D
    if days_left <= 7:
        return Urgency.DUE_SOON_7D
    return Urgency.ON_TRACK


def list_cases_for_firm(*, firm_id: str, status: CaseStatus | None = None) -> list[dict]:
    """docs/SPEC.md #12: GET /api/cases?filters -- firm-scoped, urgency-annotated."""
    db = get_firestore_client()
    query = db.collection("cases").where("firm_id", "==", firm_id)
    if status is not None:
        query = query.where("status", "==", status.value)

    results = []
    for doc in query.stream():
        case = Case(**doc.to_dict())
        results.append(
            {
                "id": doc.id,
                **case.model_dump(mode="json"),
                "urgency": compute_urgency(case.due_date),
            }
        )
    return results
