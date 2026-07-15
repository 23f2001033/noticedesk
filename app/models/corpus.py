from enum import StrEnum

from pydantic import BaseModel, Field


class CorpusItemType(StrEnum):
    ACT_SECTION = "act_section"
    RULE = "rule"
    CIRCULAR = "circular"
    INSTRUCTION = "instruction"
    NOTIFICATION = "notification"
    CASE_LAW = "case_law"


class CorpusItem(BaseModel):
    """corpus/{item_id} -- docs/SPEC.md #3, #8.

    Immutable once reviewed; edits create a new version. Not retrievable by
    the drafter until `reviewed_by` is set by Aman or a CA advisor.
    """

    type: CorpusItemType
    citation_string: str
    source_url: str
    effective_dates: str | None = None
    verbatim_text: str
    summary: str | None = None
    issue_tags: list[str] = Field(default_factory=list)
    embedding: list[float] | None = None
    added_by: str
    reviewed_by: str | None = None
    version: int = 1


class CorpusChunk(BaseModel):
    """corpus_chunks/{chunk_id} -- docs/SPEC.md #3. Citations always resolve
    to the parent corpus item, never to a bare chunk."""

    corpus_item_id: str
    chunk_text: str
    embedding: list[float] | None = None
