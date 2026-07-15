from app.agents.classifier import ClassifierResult, classify_notice
from app.models.agent_run import AgentRunStatus
from app.models.case import NoticeType
from app.services.gemini import GeminiJsonParseError


def test_classify_notice_returns_parsed_result_and_logs_ok(monkeypatch) -> None:
    logged = {}

    def fake_generate_json(*, model, prompt, response_schema, temperature):
        assert response_schema is ClassifierResult
        return (
            ClassifierResult(notice_type=NoticeType.ASMT_10, confidence=0.92),
            {"tokens_in": 100, "tokens_out": 20, "latency_ms": 450},
        )

    def fake_log_agent_run(**kwargs):
        logged.update(kwargs)

    monkeypatch.setattr("app.agents.classifier.generate_json", fake_generate_json)
    monkeypatch.setattr("app.agents.classifier.log_agent_run", fake_log_agent_run)

    result = classify_notice(notice_text="some notice", case_id="case-1", firm_id="firm-1")

    assert result.notice_type == NoticeType.ASMT_10
    assert result.confidence == 0.92
    assert logged["status"] == AgentRunStatus.OK
    assert logged["decision"] == "ASMT-10"
    assert logged["tokens_in"] == 100


def test_classify_notice_falls_back_on_parse_error(monkeypatch) -> None:
    logged = {}

    def fake_generate_json(**kwargs):
        raise GeminiJsonParseError("bad json")

    def fake_log_agent_run(**kwargs):
        logged.update(kwargs)

    monkeypatch.setattr("app.agents.classifier.generate_json", fake_generate_json)
    monkeypatch.setattr("app.agents.classifier.log_agent_run", fake_log_agent_run)

    result = classify_notice(notice_text="garbled", case_id="case-1", firm_id="firm-1")

    assert result.notice_type == NoticeType.OTHER
    assert result.confidence == 0.0
    assert logged["status"] == AgentRunStatus.FALLBACK
    assert logged["decision"] == "other"
