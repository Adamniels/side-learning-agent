from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from session_designer.domain.llm_contracts import (
    CandidateTopicBatch,
    ChooseTopicOutput,
    LearningStateAnalysis,
    ResourceBatch,
    SessionRevision,
)
from session_designer.domain.output import (
    CandidateTopic,
    ChecklistItem,
    ResourceKind,
    SelectedTopic,
    SuggestedResource,
    ValidationResult,
)
from session_designer.domain.session_schema import (
    DesignedSession,
    ExtensionSuggestion,
    HandsOnExercise,
    SessionContext,
    SessionGoal,
)
from session_designer.providers.base import LLMProvider

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider:
    """Deterministic provider for tests / CI without API keys."""

    def generate_structured(
        self,
        *,
        model: str,
        system: str,
        user: str,
        response_model: type[T],
        temperature: float = 0.2,
    ) -> T:
        fn = _MOCK_RESPONSES.get(response_model)
        if fn is None:
            raise KeyError(f"No mock structured response for {response_model.__name__}")
        return fn(user)  # type: ignore[return-value]

    def generate_text(
        self,
        *,
        model: str,
        system: str,
        user: str,
        temperature: float = 0.3,
    ) -> str:
        return "mock-text"


def _analysis(_: str) -> LearningStateAnalysis:
    return LearningStateAnalysis(
        themes_covered=["Python tooling", "HTTP basics"],
        gaps_vs_interests=["Backend frameworks", "Databases"],
        repetition_risks=["Re-teaching pip/venv"],
        level_constraints="User is intermediate Python, beginner FastAPI/SQL.",
        avoid_next=["Another pure HTTP theory session"],
        summary="Ready for practical API + persistence bridge.",
    )


def _candidates(_: str) -> CandidateTopicBatch:
    return CandidateTopicBatch(
        topics=[
            CandidateTopic(
                id="c1",
                title="FastAPI dependency injection and settings",
                one_line_fit="Levels up structure before DB work.",
                difficulty_note="Matches beginner FastAPI, int. Python.",
                non_repetition_rationale="Not repeating venv or raw HTTP.",
            ),
            CandidateTopic(
                id="c2",
                title="SQLAlchemy models + Alembic migrations (minimal)",
                one_line_fit="Connects API to real persistence.",
                difficulty_note="Stretch on SQL; scoped to one table.",
                non_repetition_rationale="Different from unfinished CRUD tutorial chunk.",
            ),
            CandidateTopic(
                id="c3",
                title="Dockerfile for a small FastAPI app",
                one_line_fit="Aligns with DevOps interest; concrete artifact.",
                difficulty_note="Beginner Docker; uses known Python context.",
                non_repetition_rationale="New domain vs past sessions.",
            ),
        ]
    )


def _choose(_: str) -> ChooseTopicOutput:
    return ChooseTopicOutput(
        selected_topic=SelectedTopic(
            title="FastAPI dependency injection and settings",
            summary="Learn app configuration and DI patterns to structure a service.",
            difficulty_alignment="Fits beginner FastAPI with intermediate Python.",
            candidate_id="c1",
        ),
        why_chosen="Best immediate bridge to finishing the stalled CRUD API without jumping to DB complexity first.",
        comparison_notes="c2 is valuable next but needs routing patterns solid; c3 is parallel DevOps track.",
    )


def _resources(_: str) -> ResourceBatch:
    return ResourceBatch(
        resources=[
            SuggestedResource(
                kind=ResourceKind.official_docs,
                title="FastAPI docs — Dependencies",
                url="https://fastapi.tiangolo.com/tutorial/dependencies/",
                rationale="Official explanation of dependency injection.",
            ),
            SuggestedResource(
                kind=ResourceKind.tutorial,
                title="Pydantic settings management",
                url="https://docs.pydantic.dev/latest/concepts/pydantic_settings/",
                rationale="Common pattern for FastAPI configuration.",
            ),
        ]
    )


def _session(_: str) -> DesignedSession:
    return DesignedSession(
        goal=SessionGoal(
            statement="Implement a small FastAPI app that reads settings from environment and injects a config object into a route.",
        ),
        context=SessionContext(
            text="Dependency injection keeps FastAPI endpoints testable and makes configuration explicit. "
            "You will use it constantly once you add databases and auth.",
        ),
        hands_on=HandsOnExercise(
            instructions=(
                "1) Create a FastAPI app with a `Settings` class using `pydantic-settings` "
                "loading `APP_NAME` from env.\n"
                "2) Add a `get_settings` dependency that returns a cached settings instance.\n"
                "3) Expose `GET /health` returning JSON `{'app': settings.app_name}`.\n"
                "4) Run with uvicorn and verify with curl."
            ),
            expected_output="Running server; `curl localhost:8000/health` returns JSON with your app name.",
            time_estimate_minutes=60,
        ),
        extension=ExtensionSuggestion(
            text="Next session: add SQLAlchemy + a single `Item` model and persist rows via a FastAPI route.",
        ),
    )


def _validation(_: str) -> ValidationResult:
    return ValidationResult(
        passed=True,
        checklist=[
            ChecklistItem(name="goal_concrete", passed=True, detail="Clear deliverable."),
            ChecklistItem(name="hands_on_output", passed=True, detail="curl JSON output."),
        ],
        issues=[],
        suggested_fixes=[],
        overall_notes="Mock pass.",
    )


def _revision(_: str) -> SessionRevision:
    return SessionRevision(session=_session("").model_copy())


_MOCK_RESPONSES: dict[type[BaseModel], object] = {
    LearningStateAnalysis: _analysis,
    CandidateTopicBatch: _candidates,
    ChooseTopicOutput: _choose,
    ResourceBatch: _resources,
    DesignedSession: lambda _: _session(""),
    ValidationResult: _validation,
    SessionRevision: _revision,
}
