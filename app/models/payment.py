from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class PaymentKind(StrEnum):
    DRAFT_CREDIT = "draft_credit"
    SUBSCRIPTION = "subscription"
    SETUP = "setup"


class Payment(BaseModel):
    """payments/{id} -- docs/SPEC.md #3."""

    firm_id: str
    amount_inr: float
    usd_equiv: float | None = None
    razorpay_ref: str | None = None
    kind: PaymentKind
    period: str | None = None
    related_party: bool = False
    notes: str | None = None
    ts: datetime
