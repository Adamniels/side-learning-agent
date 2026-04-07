from __future__ import annotations

from pydantic import BaseModel, Field


class SessionGoal(BaseModel):
    """Concrete, measurable goal for one session."""

    statement: str = Field(
        min_length=10,
        max_length=800,
        description="What the learner will achieve in this session.",
    )


class SessionContext(BaseModel):
    """Short motivating orientation — not deep tutoring."""

    text: str = Field(
        min_length=20,
        max_length=1200,
        description="Brief: what the topic is and why it matters to the learner.",
    )


class HandsOnExercise(BaseModel):
    """Single-session concrete exercise with a tangible output."""

    instructions: str = Field(
        min_length=40,
        max_length=4000,
        description="Step-by-step instructions the learner can follow.",
    )
    expected_output: str = Field(
        min_length=10,
        max_length=800,
        description="What artifact or observable result they should produce.",
    )
    time_estimate_minutes: int | None = Field(
        default=None,
        ge=15,
        le=180,
        description="Rough single-session bound; optional but encouraged.",
    )


class ExtensionSuggestion(BaseModel):
    """Natural next step after this session."""

    text: str = Field(
        min_length=15,
        max_length=1000,
        description="A follow-on session direction that builds on this one.",
    )


class DesignedSession(BaseModel):
    goal: SessionGoal
    context: SessionContext
    hands_on: HandsOnExercise
    extension: ExtensionSuggestion
    subject_areas: list[str] = Field(
        min_length=1,
        max_length=6,
        description=(
            "1-6 short classification labels describing the areas this session belongs to "
            "(e.g. api, python, auth, http)."
        ),
    )
