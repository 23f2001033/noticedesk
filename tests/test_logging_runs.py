from app.models.agent_run import AgentRunStatus
from app.services.logging_runs import MAX_INPUT_DIGEST_CHARS, log_agent_run


def test_log_agent_run_writes_to_agent_runs_collection(
    monkeypatch, fake_firestore_recorder
) -> None:
    monkeypatch.setattr(
        "app.services.logging_runs.get_firestore_client", lambda: fake_firestore_recorder
    )

    run = log_agent_run(
        agent="classifier",
        trigger="notice_uploaded",
        decision="ASMT-10",
        firm_id="firm-1",
        case_id="case-1",
    )

    assert run.status == AgentRunStatus.OK
    assert len(fake_firestore_recorder.writes) == 1
    collection, data = fake_firestore_recorder.writes[0]
    assert collection == "agent_runs"
    assert data["agent"] == "classifier"
    assert data["decision"] == "ASMT-10"
    assert data["firm_id"] == "firm-1"


def test_log_agent_run_truncates_input_digest(monkeypatch, fake_firestore_recorder) -> None:
    monkeypatch.setattr(
        "app.services.logging_runs.get_firestore_client", lambda: fake_firestore_recorder
    )

    run = log_agent_run(agent="extractor", trigger="t", decision="d", input_digest="x" * 500)

    assert len(run.input_digest) == MAX_INPUT_DIGEST_CHARS
    _, data = fake_firestore_recorder.writes[0]
    assert len(data["input_digest"]) == MAX_INPUT_DIGEST_CHARS
