from datetime import UTC, datetime

from app.models.agent_run import AgentRun, AgentRunStatus
from app.services.firestore import get_firestore_client

MAX_INPUT_DIGEST_CHARS = 300


def log_agent_run(
    *,
    agent: str,
    trigger: str,
    decision: str,
    model: str | None = None,
    firm_id: str | None = None,
    case_id: str | None = None,
    input_digest: str = "",
    reasoning_digest: str = "",
    output_digest: str = "",
    tokens_in: int | None = None,
    tokens_out: int | None = None,
    latency_ms: int | None = None,
    status: AgentRunStatus = AgentRunStatus.OK,
) -> AgentRun:
    """Write one agent_runs record (docs/SPEC.md #3, #9).

    Callers must not pass raw client documents or PII in input_digest --
    it is truncated here but not scrubbed; PII-minimization is the caller's
    responsibility per the non-negotiable constraints in CLAUDE.md.
    """
    run = AgentRun(
        agent=agent,
        firm_id=firm_id,
        case_id=case_id,
        trigger=trigger,
        input_digest=input_digest[:MAX_INPUT_DIGEST_CHARS],
        decision=decision,
        reasoning_digest=reasoning_digest,
        output_digest=output_digest,
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        latency_ms=latency_ms,
        status=status,
        ts=datetime.now(UTC),
    )
    db = get_firestore_client()
    db.collection("agent_runs").document().set(run.model_dump(mode="json"))
    return run
