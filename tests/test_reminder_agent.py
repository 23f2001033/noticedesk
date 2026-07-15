from datetime import UTC, datetime

from app.agents.reminder import decide_reminders_for_cases, run_reminder_check
from app.models.agent_run import AgentRunStatus
from app.models.case import Case, CaseStatus, NoticeType
from app.services.deadlines import IST


def _case(status: CaseStatus = CaseStatus.NEW, due_date: datetime | None = None) -> Case:
    return Case(
        firm_id="firm-1",
        client_id="client-1",
        notice_type=NoticeType.ASMT_10,
        status=status,
        due_date=due_date,
        created_at=datetime.now(UTC),
    )


def test_decide_reminders_sends_on_matching_offset() -> None:
    as_of = datetime(2026, 7, 20, tzinfo=IST)
    due = datetime(2026, 7, 27, tzinfo=IST)  # T-7

    decisions = decide_reminders_for_cases([("case-1", _case(due_date=due))], as_of)

    assert len(decisions) == 1
    assert decisions[0].action == "sent"
    assert decisions[0].offset_days == 7


def test_decide_reminders_skips_non_matching_offset() -> None:
    as_of = datetime(2026, 7, 20, tzinfo=IST)
    due = datetime(2026, 8, 5, tzinfo=IST)  # not T-7/T-3/T-1

    decisions = decide_reminders_for_cases([("case-1", _case(due_date=due))], as_of)

    assert decisions == []


def test_decide_reminders_skips_when_case_already_filed() -> None:
    as_of = datetime(2026, 7, 20, tzinfo=IST)
    due = datetime(2026, 7, 23, tzinfo=IST)  # T-3

    decisions = decide_reminders_for_cases(
        [("case-1", _case(status=CaseStatus.REPLY_FILED, due_date=due))], as_of
    )

    assert len(decisions) == 1
    assert decisions[0].action == "skipped"
    assert "reply_filed" in decisions[0].reason


def test_decide_reminders_ignores_cases_without_due_date() -> None:
    as_of = datetime(2026, 7, 20, tzinfo=IST)

    assert decide_reminders_for_cases([("case-1", _case(due_date=None))], as_of) == []


class _FakeCaseDoc:
    def __init__(self, doc_id: str, data: dict) -> None:
        self.id = doc_id
        self._data = data

    def to_dict(self) -> dict:
        return self._data


class _FakeCasesCollection:
    def __init__(self, docs: list[_FakeCaseDoc]) -> None:
        self._docs = docs

    def stream(self):
        return iter(self._docs)


class _FakeFirmDocRef:
    def __init__(self, exists: bool, data: dict | None) -> None:
        self.exists = exists
        self._data = data

    def get(self) -> "_FakeFirmDocRef":
        return self

    def to_dict(self) -> dict | None:
        return self._data


class _FakeFirmsCollection:
    def __init__(self, firms: dict[str, dict]) -> None:
        self._firms = firms

    def document(self, firm_id: str) -> _FakeFirmDocRef:
        data = self._firms.get(firm_id)
        return _FakeFirmDocRef(exists=data is not None, data=data)


class _FakeReminderDB:
    def __init__(self, case_docs: list[_FakeCaseDoc], firms: dict[str, dict]) -> None:
        self._cases = _FakeCasesCollection(case_docs)
        self._firms = _FakeFirmsCollection(firms)

    def collection(self, name: str):
        if name == "cases":
            return self._cases
        if name == "firms":
            return self._firms
        raise ValueError(name)


def test_run_reminder_check_sends_and_logs(monkeypatch) -> None:
    as_of = datetime(2026, 7, 20, tzinfo=IST)
    due = datetime(2026, 7, 21, tzinfo=IST)  # T-1
    case_data = _case(due_date=due).model_dump(mode="json")
    fake_db = _FakeReminderDB(
        case_docs=[_FakeCaseDoc("case-1", case_data)],
        firms={"firm-1": {"wa_number": "+911234567890"}},
    )
    monkeypatch.setattr("app.agents.reminder.get_firestore_client", lambda: fake_db)

    sent = {}

    def fake_send(*, to: str, body: str) -> str:
        sent["to"] = to
        sent["body"] = body
        return "wamid.123"

    monkeypatch.setattr("app.agents.reminder.send_whatsapp_message", fake_send)

    logged = []
    monkeypatch.setattr("app.agents.reminder.log_agent_run", lambda **kwargs: logged.append(kwargs))

    decisions = run_reminder_check(as_of=as_of)

    assert len(decisions) == 1
    assert decisions[0].action == "sent"
    assert sent["to"] == "+911234567890"
    assert "case-1" in sent["body"]
    assert logged[0]["decision"] == "sent"
    assert logged[0]["status"] == AgentRunStatus.OK


def test_run_reminder_check_falls_back_when_no_wa_number(monkeypatch) -> None:
    as_of = datetime(2026, 7, 20, tzinfo=IST)
    due = datetime(2026, 7, 21, tzinfo=IST)
    case_data = _case(due_date=due).model_dump(mode="json")
    fake_db = _FakeReminderDB(case_docs=[_FakeCaseDoc("case-1", case_data)], firms={"firm-1": {}})
    monkeypatch.setattr("app.agents.reminder.get_firestore_client", lambda: fake_db)

    def fail_if_called(**kwargs):
        raise AssertionError("should not send WhatsApp message without a wa_number")

    monkeypatch.setattr("app.agents.reminder.send_whatsapp_message", fail_if_called)

    logged = []
    monkeypatch.setattr("app.agents.reminder.log_agent_run", lambda **kwargs: logged.append(kwargs))

    run_reminder_check(as_of=as_of)

    assert logged[0]["status"] == AgentRunStatus.FALLBACK
