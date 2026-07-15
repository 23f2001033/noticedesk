from enum import StrEnum

from pydantic import BaseModel


class KBGapStatus(StrEnum):
    OPEN = "open"
    CORPUS_ADDED = "corpus_added"
    REJECTED = "rejected"


class KBGap(BaseModel):
    """kb_gaps/{id} -- docs/SPEC.md #3. Feeds the weekly corpus curation queue."""

    point: str
    case_id: str
    issue_tag: str | None = None
    status: KBGapStatus = KBGapStatus.OPEN
