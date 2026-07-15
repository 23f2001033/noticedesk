from pydantic import BaseModel, Field


class Client(BaseModel):
    """clients/{client_id} -- docs/SPEC.md #3. Thin record; not a books system."""

    firm_id: str
    trade_name: str
    gstins: list[str] = Field(default_factory=list)
    contact: str | None = None
    notes: str | None = None
