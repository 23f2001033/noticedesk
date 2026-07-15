import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from app.agents.classifier import classify_notice
from app.agents.extractor import extract_notice
from app.models.case import NoticeType
from app.models.extraction import Extraction, FieldConfidenceLevel

# docs/SPEC.md #14 deploy gates.
MIN_FIELD_ACCURACY = 0.90
DUE_DATE_ONLY_FIELD = "due_date"


class GoldenSourceError(ValueError):
    """An evals/golden_notices/*.json file failed to parse or validate."""


@dataclass
class GoldenCase:
    id: str
    notice_type: NoticeType
    notice_text: str
    expected_extraction: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalCaseResult:
    id: str
    classifier_correct: bool
    fields_checked: int
    fields_correct: int
    due_date_ok: bool


@dataclass
class EvalSummary:
    results: list[EvalCaseResult]

    @property
    def total_fields_checked(self) -> int:
        return sum(r.fields_checked for r in self.results)

    @property
    def total_fields_correct(self) -> int:
        return sum(r.fields_correct for r in self.results)

    @property
    def field_accuracy(self) -> float | None:
        if self.total_fields_checked == 0:
            return None
        return self.total_fields_correct / self.total_fields_checked

    @property
    def due_date_pass_rate(self) -> float | None:
        if not self.results:
            return None
        return sum(1 for r in self.results if r.due_date_ok) / len(self.results)

    def passes_gates(self) -> bool:
        """docs/SPEC.md #14: >=90% field accuracy on found fields, 100% on
        due_date-or-flag behavior. An empty golden set trivially passes --
        there's nothing to fail yet (see evals/golden_notices/README.md)."""
        if not self.results:
            return True
        accuracy_ok = (self.field_accuracy or 1.0) >= MIN_FIELD_ACCURACY
        due_date_ok = self.due_date_pass_rate == 1.0
        return accuracy_ok and due_date_ok


def _values_match(actual: Any, expected: Any) -> bool:
    if isinstance(expected, str) and _looks_like_datetime(expected):
        expected = datetime.fromisoformat(expected)
    if isinstance(actual, datetime) and isinstance(expected, datetime):
        return actual.date() == expected.date()
    return actual == expected


def _looks_like_datetime(value: str) -> bool:
    try:
        datetime.fromisoformat(value)
        return True
    except ValueError:
        return False


def load_golden_case(path: Path) -> GoldenCase:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GoldenSourceError(f"{path}: invalid JSON ({exc})") from exc

    for required in ("id", "notice_type", "notice_text"):
        if required not in raw:
            raise GoldenSourceError(f"{path}: missing required field {required!r}")

    try:
        notice_type = NoticeType(raw["notice_type"])
    except ValueError as exc:
        raise GoldenSourceError(f"{path}: invalid notice_type {raw['notice_type']!r}") from exc

    return GoldenCase(
        id=raw["id"],
        notice_type=notice_type,
        notice_text=raw["notice_text"],
        expected_extraction=raw.get("expected_extraction", {}),
    )


def load_golden_cases(golden_dir: Path) -> list[GoldenCase]:
    return [load_golden_case(p) for p in sorted(golden_dir.glob("*.json"))]


def evaluate_case(case: GoldenCase) -> EvalCaseResult:
    classifier_result = classify_notice(
        notice_text=case.notice_text, case_id=f"eval-{case.id}", firm_id="eval"
    )
    extraction = extract_notice(
        notice_text=case.notice_text,
        notice_type=classifier_result.notice_type,
        case_id=f"eval-{case.id}",
        firm_id="eval",
    )

    fields_checked = 0
    fields_correct = 0
    for field_name, expected_value in case.expected_extraction.items():
        if field_name == DUE_DATE_ONLY_FIELD or expected_value is None:
            continue
        fields_checked += 1
        actual_value = getattr(extraction, field_name, None)
        if _values_match(actual_value, expected_value):
            fields_correct += 1

    due_date_ok = _check_due_date(extraction, case.expected_extraction.get("due_date"))

    return EvalCaseResult(
        id=case.id,
        classifier_correct=classifier_result.notice_type == case.notice_type,
        fields_checked=fields_checked,
        fields_correct=fields_correct,
        due_date_ok=due_date_ok,
    )


def _check_due_date(extraction: Extraction, expected_due_date: Any) -> bool:
    if expected_due_date is not None:
        return _values_match(extraction.due_date, expected_due_date)
    # The notice genuinely has no stated due date -- the extractor must flag
    # that (never silently guess), not the eval harness itself.
    return (
        extraction.due_date is None
        and extraction.field_confidence.get(DUE_DATE_ONLY_FIELD) == FieldConfidenceLevel.ABSENT
    )


def run_eval(golden_dir: Path) -> EvalSummary:
    cases = load_golden_cases(golden_dir)
    return EvalSummary(results=[evaluate_case(c) for c in cases])
