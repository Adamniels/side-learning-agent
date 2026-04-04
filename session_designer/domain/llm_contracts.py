"""Pydantic models used as structured LLM outputs (internal to the graph)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from session_designer.domain.output import CandidateTopic, SelectedTopic, SuggestedResource
from session_designer.domain.session_schema import DesignedSession


class LearningStateAnalysis(BaseModel):
    themes_covered: list[str] = Field(default_factory=list, max_length=20)
    gaps_vs_interests: list[str] = Field(default_factory=list, max_length=20)
    repetition_risks: list[str] = Field(default_factory=list, max_length=20)
    level_constraints: str = Field(default="", max_length=1200)
    avoid_next: list[str] = Field(default_factory=list, max_length=15)
    summary: str = Field(default="", max_length=1500)


class CandidateTopicBatch(BaseModel):
    topics: list[CandidateTopic] = Field(min_length=3, max_length=5)


class ChooseTopicOutput(BaseModel):
    selected_topic: SelectedTopic
    why_chosen: str = Field(max_length=2000)
    comparison_notes: str = Field(max_length=2000)


class ResourceBatch(BaseModel):
    """LLM-proposed resources; URLs are not live-verified in the prototype."""

    resources: list[SuggestedResource] = Field(min_length=2, max_length=8)


class SessionRevision(BaseModel):
    """Full session replacement after failed validation."""

    session: DesignedSession
