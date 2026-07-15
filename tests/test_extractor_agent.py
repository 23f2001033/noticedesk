from app.agents.extractor import extract_notice
from app.models.agent_run import AgentRunStatus
from app.models.case import NoticeType
from app.models.extraction import Extraction
from app.services.gemini import GeminiJsonParseError


def test_extract_notice_returns_parsed_result_and_logs_ok(monkeypatch) -> None:
    logged = {}
    expected = Extraction(gstin="27AAAAA0000A1Z5", legal_name="Test Traders")

    def fake_generate_json(*, model, prompt, response_schema, temperature):
        assert response_schema is Extraction
        return expected, {"tokens_in": 500, "tokens_out": 200, "latency_ms": 900}

    def fake_log_agent_run(**kwargs):
        logged.update(kwargs)

    monkeypatch.setattr("app.agents.extractor.generate_json", fake_generate_json)
    monkeypatch.setattr("app.agents.extractor.log_agent_run", fake_log_agent_run)

    result = extract_notice(
        notice_text="notice body",
        notice_type=NoticeType.ASMT_10,
        case_id="case-1",
        firm_id="firm-1",
    )

    assert result == expected
    assert logged["status"] == AgentRunStatus.OK
    assert logged["decision"] == "extracted"


def test_extract_notice_falls_back_on_parse_error(monkeypatch) -> None:
    logged = {}

    def fake_generate_json(**kwargs):
        raise GeminiJsonParseError("bad json")

    def fake_log_agent_run(**kwargs):
        logged.update(kwargs)

    monkeypatch.setattr("app.agents.extractor.generate_json", fake_generate_json)
    monkeypatch.setattr("app.agents.extractor.log_agent_run", fake_log_agent_run)

    result = extract_notice(
        notice_text="garbled",
        notice_type=NoticeType.DRC_01,
        case_id="case-1",
        firm_id="firm-1",
    )

    assert result == Extraction()
    assert logged["status"] == AgentRunStatus.FALLBACK
    assert logged["decision"] == "extraction_failed"
