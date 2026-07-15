from app.config import get_settings
from app.models.agent_run import AgentRunStatus
from app.models.case import NoticeType
from app.models.extraction import Extraction
from app.prompts.extractor import EXTRACTOR_PROMPT_V1
from app.services.gemini import GeminiJsonParseError, generate_json
from app.services.logging_runs import log_agent_run


def extract_notice(
    *, notice_text: str, notice_type: NoticeType, case_id: str, firm_id: str
) -> Extraction:
    """docs/SPEC.md #5 step 4 -- FAST model, JSON schema.

    Falls back to an empty Extraction on a JSON-parse failure (docs/SPEC.md
    #14) so the caller can route the case to manual review rather than
    silently losing the notice.
    """
    settings = get_settings()
    prompt = EXTRACTOR_PROMPT_V1.format(notice_text=notice_text, notice_type=notice_type.value)

    try:
        result, usage = generate_json(
            model=settings.gemini_model_fast,
            prompt=prompt,
            response_schema=Extraction,
            temperature=0.0,
        )
        status = AgentRunStatus.OK
        decision = "extracted"
    except GeminiJsonParseError:
        result = Extraction()
        usage = {}
        status = AgentRunStatus.FALLBACK
        decision = "extraction_failed"

    log_agent_run(
        agent="extractor",
        trigger="notice_classified",
        firm_id=firm_id,
        case_id=case_id,
        decision=decision,
        model=settings.gemini_model_fast,
        status=status,
        **usage,
    )
    return result
