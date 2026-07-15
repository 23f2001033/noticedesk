from datetime import UTC, datetime

from app.agents.classifier import classify_notice
from app.agents.extractor import extract_notice
from app.models.case import Case, CaseDocument, CaseSource, CaseStatus, DocumentKind
from app.services.deadlines import NoStatutoryDefaultError, compute_statutory_default_due_date
from app.services.firestore import get_firestore_client
from app.services.ocr import route_ocr
from app.services.storage import upload_document


def ingest_notice(
    *,
    firm_id: str,
    client_id: str,
    uploaded_by: str,
    file_bytes: bytes,
    filename: str,
    content_type: str,
) -> Case:
    """docs/SPEC.md #5 steps 1-6: intake -> OCR routing -> classify -> extract
    -> deadline -> persist. Summary-card rendering and reminder scheduling
    happen downstream of the returned Case (deadline board write, reminder
    agent -- not yet built, see PROGRESS.md)."""
    db = get_firestore_client()
    case_ref = db.collection("cases").document()
    case_id = case_ref.id

    storage_ref = upload_document(
        file_bytes=file_bytes,
        destination_path=f"{firm_id}/{case_id}/{filename}",
        content_type=content_type,
    )
    ocr_result = route_ocr(file_bytes=file_bytes, mime_type=content_type)

    classifier_result = classify_notice(
        notice_text=ocr_result.text, case_id=case_id, firm_id=firm_id
    )
    extraction = extract_notice(
        notice_text=ocr_result.text,
        notice_type=classifier_result.notice_type,
        case_id=case_id,
        firm_id=firm_id,
    )

    due_date = extraction.due_date
    due_date_source: str | None = "extracted" if due_date is not None else None
    if due_date is None and extraction.notice_date is not None:
        try:
            due_date = compute_statutory_default_due_date(
                classifier_result.notice_type, extraction.notice_date
            )
            due_date_source = "statutory_default"
        except NoStatutoryDefaultError:
            due_date_source = None

    now = datetime.now(UTC)
    case = Case(
        firm_id=firm_id,
        client_id=client_id,
        notice_type=classifier_result.notice_type,
        fy_period=extraction.fy_period,
        sections_invoked=extraction.sections_invoked,
        demand_amount=extraction.total_demand,
        officer=extraction.officer,
        din=extraction.din,
        notice_date=extraction.notice_date,
        due_date=due_date,
        due_date_source=due_date_source,
        due_date_confirmed=False,
        status=CaseStatus.NEW,
        source=CaseSource.WEB,
        created_at=now,
    )
    case_ref.set(case.model_dump(mode="json"))

    document = CaseDocument(
        kind=DocumentKind.NOTICE,
        storage_ref=storage_ref,
        ocr_used=ocr_result.ocr_used,
        pages=ocr_result.pages,
        uploaded_by=uploaded_by,
        ts=now,
    )
    case_ref.collection("documents").document().set(document.model_dump(mode="json"))
    case_ref.collection("extraction").document("current").set(extraction.model_dump(mode="json"))

    return case
