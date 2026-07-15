from pydantic import BaseModel, Field

from app.config import get_settings
from app.models.agent_run import AgentRunStatus
from app.models.case import NoticeType
from app.prompts.classifier import CLASSIFIER_PROMPT_V1
from app.services.gemini import GeminiJsonParseError, generate_json
from app.services.logging_runs import log_agent_run


class ClassifierResult(BaseModel):
    notice_type: NoticeType
    confidence: float = Field(ge=0.0, le=1.0)


def classify_notice(*, notice_text: str, case_id: str, firm_id: str) -> ClassifierResult:
    """docs/SPEC.md #5 step 3 -- FAST model, temp 0, JSON schema.

    Falls back to notice_type=other, confidence=0.0 on a JSON-parse failure
    (docs/SPEC.md #14) rather than raising -- the case still gets tracked,
    just without drafting support, and the fallback is logged.
    """
    settings = get_settings()
    prompt = CLASSIFIER_PROMPT_V1.format(notice_text=notice_text)

    try:
        result, usage = generate_json(
            model=settings.gemini_model_fast,
            prompt=prompt,
            response_schema=ClassifierResult,
            temperature=0.0,
        )
        status = AgentRunStatus.OK
    except GeminiJsonParseError:
        result = ClassifierResult(notice_type=NoticeType.OTHER, confidence=0.0)
        usage = {}
        status = AgentRunStatus.FALLBACK

    log_agent_run(
        agent="classifier",
        trigger="notice_uploaded",
        firm_id=firm_id,
        case_id=case_id,
        decision=result.notice_type.value,
        model=settings.gemini_model_fast,
        status=status,
        **usage,
    )
    return result
