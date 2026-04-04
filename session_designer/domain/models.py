from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class SkillLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class UserInterest(BaseModel):
    label: str = Field(min_length=1, max_length=200)
    weight: float = Field(ge=0.0, le=1.0, default=0.5)


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

    user_id: str = Field(min_length=1, max_length=128)
    interests: list[UserInterest] = Field(default_factory=list)
    skill_levels: list[tuple[str, SkillLevel]] = Field(
        default_factory=list,
        description="Topic name and self-reported level",
    )
    completed_sessions: list[PastSession] = Field(default_factory=list)
    uncompleted_sessions: list[PastSession] = Field(default_factory=list)

    @field_validator("skill_levels", mode="before")
    @classmethod
    def coerce_skill_levels(
        cls, v: list[tuple[str, str]] | list[dict[str, str]] | None
    ) -> list[tuple[str, SkillLevel]]:
        if not v:
            return []
        out: list[tuple[str, SkillLevel]] = []
        for item in v:
            if isinstance(item, dict):
                topic = item.get("topic", "").strip()
                level_raw = item.get("level", "beginner")
            else:
                topic, level_raw = item[0].strip(), item[1]
            if not topic:
                continue
            out.append((topic, SkillLevel(str(level_raw).lower())))
        return out
