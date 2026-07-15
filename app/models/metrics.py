from pydantic import BaseModel


class MetricsDaily(BaseModel):
    """metrics_daily/{date} -- docs/SPEC.md #3. `date` mirrors the doc id (YYYY-MM-DD)."""

    date: str
    notices_ingested: int = 0
    summaries_generated: int = 0
    drafts_generated: int = 0
    drafts_exported: int = 0
    deadlines_tracked: int = 0
    reminders_sent: int = 0
    active_firms: int = 0
    revenue_inr: float = 0
    agent_runs_total: int = 0
    avg_summary_latency_ms: float | None = None
