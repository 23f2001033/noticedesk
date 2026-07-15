from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class NoticeType(StrEnum):
    ASMT_10 = "ASMT-10"
    DRC_01A = "DRC-01A"
    DRC_01 = "DRC-01"
    OTHER = "other"


class CaseStatus(StrEnum):
    NEW = "new"
    IN_PREP = "in_prep"
    DRAFT_READY = "draft_ready"
    REPLY_FILED = "reply_filed"
    DROPPED = "dropped"
    ORDER_PASSED = "order_passed"
    APPEAL_WINDOW = "appeal_window"
    CLOSED = "closed"


class CaseSource(StrEnum):
    WEB = "web"
    WHATSAPP = "whatsapp"


class DocumentKind(StrEnum):
    NOTICE = "notice"
    EVIDENCE = "evidence"
    EXPORT = "export"


class Case(BaseModel):
    """cases/{case_id} -- docs/SPEC.md #3."""

    firm_id: str
    client_id: str
    notice_type: NoticeType
    fy_period: str | None = None
    sections_invoked: list[str] = Field(default_factory=list)
    demand_amount: float | None = None
    officer: str | None = None
    din: str | None = None
    notice_date: datetime | None = None
    due_date: datetime | None = None
    # Set whenever due_date wasn't found on the notice itself and had to be
    # computed from a statutory default (docs/SPEC.md #5: "never silently
    # guess a deadline") -- due_date_confirmed must stay False until a CA
    # reviews it, regardless of how confident the computed default is.
    due_date_source: Literal["extracted", "statutory_default"] | None = None
    due_date_confirmed: bool = False
    status: CaseStatus = CaseStatus.NEW
    appeal_due_date: datetime | None = None
    assigned_uid: str | None = None
    source: CaseSource = CaseSource.WEB
    created_at: datetime


class CaseDocument(BaseModel):
    """cases/{id}/documents/{doc_id} -- docs/SPEC.md #3."""

    kind: DocumentKind
    storage_ref: str
    ocr_used: bool = False
    pages: int | None = None
    uploaded_by: str
    ts: datetime
