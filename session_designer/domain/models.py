from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserInterest(BaseModel):
    label: str = Field(min_length=1, max_length=200)
    weight: float = Field(ge=0.0, le=1.0, default=0.5)
    context: str = Field(default="", max_length=1000)


class PastSession(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    summary: str = Field(default="", max_length=2000)
    topics: list[str] = Field(default_factory=list)
    completed_at: date | None = None
    last_touched_at: date | None = None

    @field_validator("topics", mode="before")
    @classmethod
    def strip_topics(cls, v: list[str] | None) -> list[str]:
        if not v:
            return []
        return [t.strip() for t in v if t and str(t).strip()]


class UserLearningContext(BaseModel):
    """Read-only aggregate passed into the graph (canonical data lives elsewhere)."""

    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    interests: list[UserInterest] = Field(default_factory=list)
    completed_sessions: list[PastSession] = Field(default_factory=list)
    uncompleted_sessions: list[PastSession] = Field(default_factory=list)
