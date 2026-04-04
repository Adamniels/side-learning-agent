from __future__ import annotations

from typing import Any

from session_designer.domain.llm_contracts import (
    CandidateTopicBatch,
    ChooseTopicOutput,
    LearningStateAnalysis,
    SessionRevision,
)
from session_designer.domain.models import UserLearningContext
from session_designer.domain.output import (
    CandidateTopic,
    SessionDesignResult,
    SelectedTopic,
    SuggestedResource,
    ValidationResult,
)
from session_designer.domain.session_schema import DesignedSession
from session_designer.graph.deps import GraphDeps
from session_designer.graph.state import SessionDesignerState
from session_designer.prompts import templates as T


def _ctx(state: SessionDesignerState) -> UserLearningContext:
    return UserLearningContext.model_validate(state["user_context"])


def normalize_input(state: SessionDesignerState, deps: GraphDeps) -> dict[str, Any]:
    _ = deps
    ctx = UserLearningContext.model_validate(state["user_context"])
    notes: list[str] = []
    max_interests = 15
    if len(ctx.interests) > max_interests:
        ctx = ctx.model_copy(
            update={
                "interests": sorted(ctx.interests, key=lambda x: -x.weight)[:max_interests]
            }
        )
        notes.append(f"Clamped interests to top {max_interests} by weight.")
    max_sessions = 25
    if len(ctx.completed_sessions) > max_sessions:
        ctx = ctx.model_copy(
            update={"completed_sessions": ctx.completed_sessions[-max_sessions:]}
        )
        notes.append(f"Kept last {max_sessions} completed sessions.")
    if len(ctx.uncompleted_sessions) > max_sessions:
        ctx = ctx.model_copy(
            update={"uncompleted_sessions": ctx.uncompleted_sessions[-max_sessions:]}
        )
        notes.append(f"Kept last {max_sessions} uncompleted sessions.")

    def _dedupe(sessions: list[Any]) -> tuple[list[Any], bool]:
        seen: set[str] = set()
        out: list[Any] = []
        for s in sessions:
            k = s.title.casefold().strip()
            if k in seen:
                continue
            seen.add(k)
            out.append(s)
        return out, len(out) != len(sessions)

    comp, d1 = _dedupe(ctx.completed_sessions)
    unco, d2 = _dedupe(ctx.uncompleted_sessions)
    if d1 or d2:
        notes.append("Deduped sessions by title (case-insensitive).")
    ctx = ctx.model_copy(update={"completed_sessions": comp, "uncompleted_sessions": unco})

    prior = list(state.get("normalization_notes") or [])
    return {
        "user_context": ctx.model_dump(mode="json"),
        "normalization_notes": prior + notes,
    }


def analyze_learning_state(state: SessionDesignerState, deps: GraphDeps) -> dict[str, Any]:
    ctx = _ctx(state)
    analysis = deps.llm.generate_structured(
        model=state["model"],
        system=T.ANALYSIS_SYSTEM,
        user=T.analysis_user_prompt(ctx),
        response_model=LearningStateAnalysis,
        temperature=0.2,
    )
    return {"learning_state": analysis.model_dump(mode="json")}


def generate_candidate_topics(state: SessionDesignerState, deps: GraphDeps) -> dict[str, Any]:
    ctx = _ctx(state)
    ls = state.get("learning_state") or {}
    batch = deps.llm.generate_structured(
        model=state["model"],
        system=T.TOPIC_SYSTEM,
        user=T.topic_user_prompt(ctx, ls),
        response_model=CandidateTopicBatch,
        temperature=0.4,
    )
    topics = batch.topics
    if len(topics) < 3:
        raise ValueError("Expected at least 3 candidate topics from the model.")
    if len(topics) > 5:
        topics = topics[:5]
    return {"candidate_topics": [t.model_dump(mode="json") for t in topics]}


def choose_best_topic(state: SessionDesignerState, deps: GraphDeps) -> dict[str, Any]:
    ctx = _ctx(state)
    ls = state.get("learning_state") or {}
    raw_c = state.get("candidate_topics") or []
    cand_objs = [CandidateTopic.model_validate(x) for x in raw_c]
    out = deps.llm.generate_structured(
        model=state["model"],
        system=T.CHOOSE_SYSTEM,
        user=T.choose_user_prompt(ctx, ls, cand_objs),
        response_model=ChooseTopicOutput,
        temperature=0.2,
    )
    return {
        "selected_topic": out.selected_topic.model_dump(mode="json"),
        "why_chosen": out.why_chosen,
        "comparison_notes": out.comparison_notes,
    }


def gather_resources(state: SessionDesignerState, deps: GraphDeps) -> dict[str, Any]:
    ctx = _ctx(state)
    sel = SelectedTopic.model_validate(state["selected_topic"])
    resources = deps.resource_gatherer.gather(topic=sel, user_context=ctx, model=state["model"])
    return {"resources": [r.model_dump(mode="json") for r in resources]}


def generate_session(state: SessionDesignerState, deps: GraphDeps) -> dict[str, Any]:
    ctx = _ctx(state)
    ls = state.get("learning_state") or {}
    sel = SelectedTopic.model_validate(state["selected_topic"])
    why = state.get("why_chosen") or ""
    res = state.get("resources") or []
    session = deps.llm.generate_structured(
        model=state["model"],
        system=T.SESSION_SYSTEM,
        user=T.session_user_prompt(
            ctx=ctx, analysis=ls, selected=sel, why_chosen=why, resources=res
        ),
        response_model=DesignedSession,
        temperature=0.35,
    )
    return {"draft_session": session.model_dump(mode="json")}


def validate_session(state: SessionDesignerState, deps: GraphDeps) -> dict[str, Any]:
    ctx = _ctx(state)
    sel = SelectedTopic.model_validate(state["selected_topic"])
    draft = DesignedSession.model_validate(state["draft_session"])
    vr = deps.llm.generate_structured(
        model=state["model"],
        system=T.VALIDATION_SYSTEM,
        user=T.validation_user_prompt(ctx=ctx, selected=sel, session=draft),
        response_model=ValidationResult,
        temperature=0.1,
    )
    return {"validation": vr.model_dump(mode="json")}


def revise_session(state: SessionDesignerState, deps: GraphDeps) -> dict[str, Any]:
    ctx = _ctx(state)
    sel = SelectedTopic.model_validate(state["selected_topic"])
    draft = DesignedSession.model_validate(state["draft_session"])
    vr = ValidationResult.model_validate(state["validation"])
    rev = deps.llm.generate_structured(
        model=state["model"],
        system=T.REVISION_SYSTEM,
        user=T.revision_user_prompt(
            ctx=ctx,
            selected=sel,
            session=draft,
            validation_issues=vr.issues,
            suggested_fixes=vr.suggested_fixes,
        ),
        response_model=SessionRevision,
        temperature=0.25,
    )
    n = int(state.get("revision_count") or 0) + 1
    return {"draft_session": rev.session.model_dump(mode="json"), "revision_count": n}


def return_result(state: SessionDesignerState, deps: GraphDeps) -> dict[str, Any]:
    _ = deps
    selected = SelectedTopic.model_validate(state["selected_topic"])
    candidates = [CandidateTopic.model_validate(x) for x in (state.get("candidate_topics") or [])]
    session = DesignedSession.model_validate(state["draft_session"])
    resources = [SuggestedResource.model_validate(x) for x in (state.get("resources") or [])]
    validation = ValidationResult.model_validate(state["validation"])
    proto = list(state.get("prototype_notes") or [])
    proto.append(
        "Resource URLs were model-suggested in this prototype and were not verified live on the web."
    )
    notes = list(state.get("normalization_notes") or [])

    # Light programmatic nudges (non-blocking): annotate if context is long
    if len(session.context.text) > 1100:
        validation = validation.model_copy(
            update={
                "overall_notes": (
                    validation.overall_notes + " Programmatic note: context is near max length."
                ).strip(),
            }
        )

    result = SessionDesignResult.from_pipeline(
        selected=selected,
        why_chosen=state.get("why_chosen") or "",
        candidates=candidates,
        session=session,
        resources=resources,
        validation=validation,
        revision_count=int(state.get("revision_count") or 0),
        normalization_notes=notes,
        prototype_notes=proto,
    )
    stop = state.get("stop_reason")
    if stop:
        result = result.model_copy(
            update={
                "prototype_notes": result.prototype_notes + [f"stop_reason={stop}"],
            }
        )
    return {"final_result": result.model_dump(mode="json")}


def route_after_validation(state: SessionDesignerState) -> str:
    vr = ValidationResult.model_validate(state["validation"])
    rev_count = int(state.get("revision_count") or 0)
    max_r = int(state.get("max_revisions") or 0)
    if vr.passed:
        return "return_result"
    if rev_count < max_r:
        return "revise_session"
    return "return_result"
