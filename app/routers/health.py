from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "service": "noticedesk", "version": "0.1.0"}
