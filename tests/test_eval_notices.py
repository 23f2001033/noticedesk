import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.agents.classifier import ClassifierResult
from app.models.case import NoticeType
from app.models.extraction import Extraction, FieldConfidenceLevel
from app.services.eval_notices import (
    EvalCaseResult,
    EvalSummary,
    GoldenCase,
    GoldenSourceError,
    evaluate_case,
    load_golden_case,
    load_golden_cases,
    run_eval,
)

# NOTE: "notice_text" / expected values below are obviously fictional test
# fixtures, not real notices -- see evals/golden_notices/README.md.
FIXTURE_JSON = {
    "id": "golden-fixture-1",
    "notice_type": "ASMT-10",
    "notice_text": "Fixture notice text for testing only.",
    "expected_extraction": {"gstin": "00TESTGSTIN0Z0", "due_date": "2026-08-01"},
}


def _write_fixture(tmp_path: Path, data: dict, name: str = "golden-fixture-1.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_load_golden_case_valid(tmp_path: Path) -> None:
    path = _write_fixture(tmp_path, FIXTURE_JSON)

    case = load_golden_case(path)

    assert case.id == "golden-fixture-1"
    assert case.notice_type == NoticeType.ASMT_10
    assert case.expected_extraction["gstin"] == "00TESTGSTIN0Z0"


def test_load_golden_case_missing_field(tmp_path: Path) -> None:
    path = _write_fixture(tmp_path, {"id": "x", "notice_type": "ASMT-10"}, name="bad.json")

    with pytest.raises(GoldenSourceError):
        load_golden_case(path)


def test_load_golden_case_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(GoldenSourceError):
        load_golden_case(path)


def test_load_golden_case_invalid_notice_type(tmp_path: Path) -> None:
    path = _write_fixture(
        tmp_path,
        {"id": "x", "notice_type": "NOT-REAL", "notice_text": "t"},
        name="bad.json",
    )

    with pytest.raises(GoldenSourceError):
        load_golden_case(path)


def test_load_golden_cases_reads_all_sorted(tmp_path: Path) -> None:
    _write_fixture(tmp_path, {**FIXTURE_JSON, "id": "b"}, name="b.json")
    _write_fixture(tmp_path, {**FIXTURE_JSON, "id": "a"}, name="a.json")

    cases = load_golden_cases(tmp_path)

    assert [c.id for c in cases] == ["a", "b"]


def _golden_case(expected_extraction: dict) -> GoldenCase:
    return GoldenCase(
        id="case-1",
        notice_type=NoticeType.ASMT_10,
        notice_text="fixture notice text",
        expected_extraction=expected_extraction,
    )


def test_evaluate_case_all_fields_correct(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.eval_notices.classify_notice",
        lambda **kwargs: ClassifierResult(notice_type=NoticeType.ASMT_10, confidence=0.9),
    )
    due = datetime(2026, 8, 1, tzinfo=UTC)
    monkeypatch.setattr(
        "app.services.eval_notices.extract_notice",
        lambda **kwargs: Extraction(gstin="00TESTGSTIN0Z0", due_date=due),
    )

    result = evaluate_case(_golden_case({"gstin": "00TESTGSTIN0Z0", "due_date": "2026-08-01"}))

    assert result.classifier_correct is True
    assert result.fields_checked == 1  # due_date is scored separately, not as a generic field
    assert result.fields_correct == 1
    assert result.due_date_ok is True


def test_evaluate_case_wrong_field(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.eval_notices.classify_notice",
        lambda **kwargs: ClassifierResult(notice_type=NoticeType.ASMT_10, confidence=0.9),
    )
    monkeypatch.setattr(
        "app.services.eval_notices.extract_notice",
        lambda **kwargs: Extraction(gstin="WRONG-GSTIN"),
    )

    result = evaluate_case(_golden_case({"gstin": "00TESTGSTIN0Z0"}))

    assert result.fields_checked == 1
    assert result.fields_correct == 0


def test_evaluate_case_classifier_mismatch(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.eval_notices.classify_notice",
        lambda **kwargs: ClassifierResult(notice_type=NoticeType.DRC_01, confidence=0.9),
    )
    monkeypatch.setattr("app.services.eval_notices.extract_notice", lambda **kwargs: Extraction())

    result = evaluate_case(_golden_case({}))

    assert result.classifier_correct is False


def test_evaluate_case_due_date_correctly_flagged_absent(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.eval_notices.classify_notice",
        lambda **kwargs: ClassifierResult(notice_type=NoticeType.ASMT_10, confidence=0.9),
    )
    monkeypatch.setattr(
        "app.services.eval_notices.extract_notice",
        lambda **kwargs: Extraction(
            due_date=None, field_confidence={"due_date": FieldConfidenceLevel.ABSENT}
        ),
    )

    result = evaluate_case(_golden_case({}))  # no due_date expected -> notice states none

    assert result.due_date_ok is True


def test_evaluate_case_due_date_silently_guessed_fails(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.eval_notices.classify_notice",
        lambda **kwargs: ClassifierResult(notice_type=NoticeType.ASMT_10, confidence=0.9),
    )
    monkeypatch.setattr(
        "app.services.eval_notices.extract_notice",
        lambda **kwargs: Extraction(due_date=datetime(2026, 9, 1, tzinfo=UTC)),
    )

    result = evaluate_case(_golden_case({}))  # notice states no due_date, but model guessed one

    assert result.due_date_ok is False


def test_run_eval_with_no_golden_notices_is_empty(tmp_path: Path) -> None:
    summary = run_eval(tmp_path)

    assert summary.results == []
    assert summary.field_accuracy is None
    assert summary.passes_gates() is True


def test_eval_summary_passes_gates_above_threshold() -> None:

    summary = EvalSummary(
        results=[
            EvalCaseResult(
                id="a",
                classifier_correct=True,
                fields_checked=10,
                fields_correct=9,
                due_date_ok=True,
            ),
        ]
    )

    assert summary.field_accuracy == pytest.approx(0.9)
    assert summary.passes_gates() is True


def test_eval_summary_fails_gate_below_accuracy_threshold() -> None:

    summary = EvalSummary(
        results=[
            EvalCaseResult(
                id="a",
                classifier_correct=True,
                fields_checked=10,
                fields_correct=8,
                due_date_ok=True,
            ),
        ]
    )

    assert summary.passes_gates() is False


def test_eval_summary_fails_gate_on_any_due_date_miss() -> None:

    summary = EvalSummary(
        results=[
            EvalCaseResult(
                id="a",
                classifier_correct=True,
                fields_checked=10,
                fields_correct=10,
                due_date_ok=True,
            ),
            EvalCaseResult(
                id="b",
                classifier_correct=True,
                fields_checked=10,
                fields_correct=10,
                due_date_ok=False,
            ),
        ]
    )

    assert summary.field_accuracy == 1.0
    assert summary.passes_gates() is False
