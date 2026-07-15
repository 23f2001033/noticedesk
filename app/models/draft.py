from pydantic import BaseModel, Field


class DraftSection(BaseModel):
    heading: str
    body: str
    citation_ids: list[str] = Field(default_factory=list)


class Draft(BaseModel):
    """cases/{id}/drafts/{draft_id} -- docs/SPEC.md #3."""

    version: int
    sections: list[DraftSection] = Field(default_factory=list)
    unsupported_points: list[str] = Field(default_factory=list)
    created_by_run: str | None = None
    editor_state: str | None = None
    exported_refs: list[str] = Field(default_factory=list)
