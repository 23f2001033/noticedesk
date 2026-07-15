from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Plan(StrEnum):
    FREE = "free"
    SOLO = "solo"
    FIRM = "firm"


class UserRole(StrEnum):
    PARTNER = "partner"
    STAFF = "staff"
    OPERATOR = "operator"


class Firm(BaseModel):
    """firms/{firm_id} -- docs/SPEC.md #3."""

    name: str
    city: str | None = None
    plan: Plan = Plan.FREE
    seats: int = 1
    letterhead_asset_ref: str | None = None
    wa_number: str | None = None
    member_emails: list[str] = Field(default_factory=list)
    razorpay_customer_ref: str | None = None
    created_at: datetime


class User(BaseModel):
    """users/{uid} -- docs/SPEC.md #3."""

    firm_id: str
    role: UserRole
    email: str
    phone: str | None = None
