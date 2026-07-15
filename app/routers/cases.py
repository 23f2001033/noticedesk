from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.deps import get_current_firm, get_current_user
from app.models.case import CaseStatus
from app.services.board import list_cases_for_firm
from app.services.case_pipeline import ingest_notice

router = APIRouter(prefix="/api/cases", tags=["cases"])


@router.post("")
async def create_case(
    client_id: str = Form(...),
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    firm: dict = Depends(get_current_firm),
) -> dict:
    file_bytes = await file.read()
    case = ingest_notice(
        firm_id=firm["firm_id"],
        client_id=client_id,
        uploaded_by=user["uid"],
        file_bytes=file_bytes,
        filename=file.filename or "notice",
        content_type=file.content_type or "application/pdf",
    )
    return case.model_dump(mode="json")


@router.get("")
def get_cases(
    status: CaseStatus | None = None,
    firm: dict = Depends(get_current_firm),
) -> list[dict]:
    """docs/SPEC.md #11 board / #12 GET /api/cases?filters -- firm-scoped, urgency-annotated."""
    return list_cases_for_firm(firm_id=firm["firm_id"], status=status)
