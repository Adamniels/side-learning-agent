from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator

from session_designer.domain.session_schema import DesignedSession


class ResourceKind(str, Enum):
    official_docs = "official_docs"
    tutorial = "tutorial"
    video = "video"
    other = "other"


class CandidateTopic(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=3, max_length=200)
    one_line_fit: str = Field(max_length=400)
    difficulty_note: str = Field(max_length=400)
    non_repetition_rationale: str = Field(max_length=600)


class SelectedTopic(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    summary: str = Field(max_length=800)
    difficulty_alignment: str = Field(
        max_length=600,
        description="How this matches the user's self-reported level and gaps.",
    )
    candidate_id: str | None = Field(
        default=None,
        description="Which candidate this corresponds to, if applicable.",
    )


class SuggestedResource(BaseModel):
    kind: ResourceKind
    title: str = Field(min_length=2, max_length=300)
    # String URL: LLM outputs are not guaranteed to satisfy HttpUrl; normalize lightly.
    url: str = Field(min_length=8, max_length=2000)
    rationale: str = Field(max_length=500)

    @field_validator("url")
    @classmethod
    def ensure_scheme(cls, v: str) -> str:
        s = v.strip()
        if not s.startswith(("http://", "https://")):
            return f"https://{s}"
        return s


class ChecklistItem(BaseModel):
    name: str
    passed: bool
    detail: str = Field(default="", max_length=500)


class ValidationResult(BaseModel):
    passed: bool
    checklist: list[ChecklistItem] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    suggested_fixes: list[str] = Field(default_factory=list)
    overall_notes: str = Field(default="", max_length=1500)


class SessionPayload(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    summary: str = Field(max_length=800)
    difficulty_alignment: str = Field(max_length=600)
    goal: str = Field(description="Flattened goal statement for persistence.")
    context: str
    hands_on: str = Field(description="Flattened hands-on instructions for persistence.")
    hands_on_expected_output: str
    extension: str
    subject_areas: list[str] = Field(default_factory=list)
    estimated_duration_in_minutes: int | None = Field(default=None, ge=15, le=180)


class DesignerMetadata(BaseModel):
    selected_candidate_id: str | None = None
    why_chosen: str = Field(max_length=2000)
    candidates_considered: list[CandidateTopic]
    validation: ValidationResult
    revision_count: int = Field(ge=0)
    normalization_notes: list[str] = Field(default_factory=list)
    prototype_notes: list[str] = Field(default_factory=list)
    comparison_notes: str | None = Field(default=None, max_length=2000)


class SessionDesignResult(BaseModel):
    """Output contract split into persistence payload and designer metadata."""

    session_payload: SessionPayload
    designer_metadata: DesignerMetadata
    suggested_resources: list[SuggestedResource]

    @classmethod
    def from_pipeline(
        cls,
        *,
        selected: SelectedTopic,
        why_chosen: str,
        candidates: list[CandidateTopic],
        session: DesignedSession,
        resources: list[SuggestedResource],
        validation: ValidationResult,
        revision_count: int,
        normalization_notes: list[str],
        comparison_notes: str = "",
        prototype_notes: list[str] | None = None,
    ) -> SessionDesignResult:
        payload = SessionPayload(
            title=selected.title,
            summary=selected.summary,
            difficulty_alignment=selected.difficulty_alignment,
            goal=session.goal.statement,
            context=session.context.text,
            hands_on=session.hands_on.instructions,
            hands_on_expected_output=session.hands_on.expected_output,
            extension=session.extension.text,
            subject_areas=list(session.subject_areas),
            estimated_duration_in_minutes=session.hands_on.time_estimate_minutes,
        )
        metadata = DesignerMetadata(
            selected_candidate_id=selected.candidate_id,
            why_chosen=why_chosen,
            candidates_considered=candidates,
            validation=validation,
            revision_count=revision_count,
            normalization_notes=normalization_notes,
            prototype_notes=prototype_notes or [],
            comparison_notes=comparison_notes or None,
        )
        return cls(
            session_payload=payload,
            designer_metadata=metadata,
            suggested_resources=resources,
        )
