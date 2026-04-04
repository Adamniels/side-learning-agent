from __future__ import annotations

from typing import Any, TypedDict


class SessionDesignerState(TypedDict, total=False):
    """LangGraph state: JSON-friendly dicts for Pydantic round-trips."""

    user_context: dict[str, Any]
    normalization_notes: list[str]
    learning_state: dict[str, Any]
    candidate_topics: list[dict[str, Any]]
    selected_topic: dict[str, Any]
    why_chosen: str
    comparison_notes: str
    resources: list[dict[str, Any]]
    draft_session: dict[str, Any]
    validation: dict[str, Any]
    revision_count: int
    max_revisions: int
    model: str
    final_result: dict[str, Any]
    prototype_notes: list[str]
    stop_reason: str | None
