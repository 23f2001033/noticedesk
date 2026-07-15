from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class AgentRunStatus(StrEnum):
    OK = "ok"
    ERROR = "error"
    FALLBACK = "fallback"


class AgentRun(BaseModel):
    """agent_runs/{run_id} -- docs/SPEC.md #3, #9. Every agent action logs one
    of these: hackathon evidence and the audit trail for professional users."""

    agent: str
    firm_id: str | None = None
    case_id: str | None = None
    trigger: str
    input_digest: str = ""
    decision: str
    reasoning_digest: str = ""
    output_digest: str = ""
    model: str | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    latency_ms: int | None = None
    status: AgentRunStatus = AgentRunStatus.OK
    ts: datetime
