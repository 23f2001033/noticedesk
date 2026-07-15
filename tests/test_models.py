from datetime import UTC, datetime

from app.models.case import Case, CaseSource, CaseStatus, NoticeType


def test_notice_type_values_match_spec_strings() -> None:
    assert NoticeType.ASMT_10.value == "ASMT-10"
    assert NoticeType.DRC_01A.value == "DRC-01A"
    assert NoticeType.DRC_01.value == "DRC-01"
    assert NoticeType.OTHER.value == "other"


def test_case_defaults_never_silently_confirm_a_computed_due_date() -> None:
    case = Case(
        firm_id="firm-1",
        client_id="client-1",
        notice_type=NoticeType.ASMT_10,
        created_at=datetime.now(UTC),
    )

    assert case.due_date_confirmed is False
    assert case.status == CaseStatus.NEW
    assert case.source == CaseSource.WEB
