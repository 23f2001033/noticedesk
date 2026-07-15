from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class FieldConfidenceLevel(StrEnum):
    FOUND = "found"
    INFERRED = "inferred"
    ABSENT = "absent"


class DiscrepancyRow(BaseModel):
    issue_description: str
    tax_period: str | None = None
    amount: float | None = None
    tax_head: str | None = None
    source_of_mismatch: str | None = None


class Extraction(BaseModel):
    """cases/{id}/extraction -- docs/SPEC.md #3, #5. Extractor agent output."""

    gstin: str | None = None
    legal_name: str | None = None
    fy_period: str | None = None
    notice_no: str | None = None
    din: str | None = None
    notice_date: datetime | None = None
    due_date: datetime | None = None
    officer: str | None = None
    sections_invoked: list[str] = Field(default_factory=list)
    total_demand: float | None = None
    discrepancy_table: list[DiscrepancyRow] = Field(default_factory=list)
    field_confidence: dict[str, FieldConfidenceLevel] = Field(default_factory=dict)
