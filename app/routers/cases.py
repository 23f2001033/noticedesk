from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.deps import get_current_firm, get_current_user
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
