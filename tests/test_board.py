from datetime import UTC, datetime

from app.models.case import Case, CaseStatus, NoticeType
from app.services.board import Urgency, compute_urgency, list_cases_for_firm
from app.services.deadlines import IST


def _case(**overrides) -> Case:
    defaults = {
        "firm_id": "firm-1",
        "client_id": "client-1",
        "notice_type": NoticeType.ASMT_10,
        "status": CaseStatus.NEW,
        "created_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    return Case(**defaults)


def test_compute_urgency_no_deadline() -> None:
    assert compute_urgency(None) == Urgency.NO_DEADLINE


def test_compute_urgency_overdue() -> None:
    as_of = datetime(2026, 7, 20, tzinfo=IST)
    due = datetime(2026, 7, 15, tzinfo=IST)
    assert compute_urgency(due, as_of=as_of) == Urgency.OVERDUE


def test_compute_urgency_due_soon_3d() -> None:
    as_of = datetime(2026, 7, 20, tzinfo=IST)
    due = datetime(2026, 7, 22, tzinfo=IST)
    assert compute_urgency(due, as_of=as_of) == Urgency.DUE_SOON_3D


def test_compute_urgency_due_soon_7d() -> None:
    as_of = datetime(2026, 7, 20, tzinfo=IST)
    due = datetime(2026, 7, 26, tzinfo=IST)
    assert compute_urgency(due, as_of=as_of) == Urgency.DUE_SOON_7D


def test_compute_urgency_on_track() -> None:
    as_of = datetime(2026, 7, 20, tzinfo=IST)
    due = datetime(2026, 8, 10, tzinfo=IST)
    assert compute_urgency(due, as_of=as_of) == Urgency.ON_TRACK


class _FakeQueryDoc:
    def __init__(self, doc_id: str, data: dict) -> None:
        self.id = doc_id
        self._data = data

    def to_dict(self) -> dict:
        return self._data


class _FakeQuery:
    def __init__(self, docs: list[_FakeQueryDoc]) -> None:
        self._docs = docs

    def where(self, field: str, op: str, value) -> "_FakeQuery":
        filtered = [d for d in self._docs if d._data.get(field) == value]
        return _FakeQuery(filtered)

    def stream(self):
        return iter(self._docs)


class _FakeFirestoreQueryClient:
    def __init__(self, case_docs: dict[str, dict]) -> None:
        self._docs = [_FakeQueryDoc(doc_id, data) for doc_id, data in case_docs.items()]

    def collection(self, name: str) -> _FakeQuery:
        return _FakeQuery(self._docs)


def test_list_cases_for_firm_filters_by_firm_and_annotates_urgency(monkeypatch) -> None:
    matching = _case(due_date=datetime(2026, 7, 21, tzinfo=UTC)).model_dump(mode="json")
    other_firm = _case(firm_id="firm-2").model_dump(mode="json")

    fake_client = _FakeFirestoreQueryClient({"case-1": matching, "case-2": other_firm})
    monkeypatch.setattr("app.services.board.get_firestore_client", lambda: fake_client)

    results = list_cases_for_firm(firm_id="firm-1")

    assert len(results) == 1
    assert results[0]["id"] == "case-1"
    assert results[0]["firm_id"] == "firm-1"
    assert "urgency" in results[0]


def test_list_cases_for_firm_filters_by_status(monkeypatch) -> None:
    new_case = _case().model_dump(mode="json")
    filed_case = _case(status=CaseStatus.REPLY_FILED).model_dump(mode="json")

    fake_client = _FakeFirestoreQueryClient({"case-1": new_case, "case-2": filed_case})
    monkeypatch.setattr("app.services.board.get_firestore_client", lambda: fake_client)

    results = list_cases_for_firm(firm_id="firm-1", status=CaseStatus.REPLY_FILED)

    assert len(results) == 1
    assert results[0]["id"] == "case-2"
