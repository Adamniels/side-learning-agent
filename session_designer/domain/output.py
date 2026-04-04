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


class SessionDesignResult(BaseModel):
    """Strict app-facing result of the session design workflow."""

    selected_topic: SelectedTopic
    why_chosen: str = Field(max_length=2000)
    candidates_considered: list[CandidateTopic]
    goal: str = Field(description="Flattened goal statement for convenience.")
    context: str
    hands_on: str = Field(description="Flattened hands-on instructions.")
    hands_on_expected_output: str
    extension: str
    suggested_resources: list[SuggestedResource]
    validation: ValidationResult
    revision_count: int = Field(ge=0)
    normalization_notes: list[str] = Field(default_factory=list)
    prototype_notes: list[str] = Field(
        default_factory=list,
        description="e.g. LLM-suggested URLs are not live-verified in the prototype.",
    )

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
        prototype_notes: list[str] | None = None,
    ) -> SessionDesignResult:
        return cls(
            selected_topic=selected,
            why_chosen=why_chosen,
            candidates_considered=candidates,
            goal=session.goal.statement,
            context=session.context.text,
            hands_on=session.hands_on.instructions,
            hands_on_expected_output=session.hands_on.expected_output,
            extension=session.extension.text,
            suggested_resources=resources,
            validation=validation,
            revision_count=revision_count,
            normalization_notes=normalization_notes,
            prototype_notes=prototype_notes or [],
        )
