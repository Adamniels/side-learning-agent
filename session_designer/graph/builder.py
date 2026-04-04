from __future__ import annotations

from functools import partial

from langgraph.graph import END, StateGraph

from session_designer.domain.models import UserLearningContext
from session_designer.domain.output import SessionDesignResult
from session_designer.graph.deps import GraphDeps
from session_designer.graph.nodes import (
    analyze_learning_state,
    choose_best_topic,
    gather_resources,
    generate_candidate_topics,
    generate_session,
    normalize_input,
    return_result,
    revise_session,
    route_after_validation,
    validate_session,
)
from session_designer.graph.state import SessionDesignerState


def build_graph(deps: GraphDeps):
    g = StateGraph(SessionDesignerState)

    g.add_node("normalize_input", partial(normalize_input, deps=deps))
    g.add_node("analyze_learning_state", partial(analyze_learning_state, deps=deps))
    g.add_node("generate_candidate_topics", partial(generate_candidate_topics, deps=deps))
    g.add_node("choose_best_topic", partial(choose_best_topic, deps=deps))
    g.add_node("gather_resources", partial(gather_resources, deps=deps))
    g.add_node("generate_session", partial(generate_session, deps=deps))
    g.add_node("validate_session", partial(validate_session, deps=deps))
    g.add_node("revise_session_if_needed", partial(revise_session, deps=deps))
    g.add_node("return_result", partial(return_result, deps=deps))

    g.set_entry_point("normalize_input")
    g.add_edge("normalize_input", "analyze_learning_state")
    g.add_edge("analyze_learning_state", "generate_candidate_topics")
    g.add_edge("generate_candidate_topics", "choose_best_topic")
    g.add_edge("choose_best_topic", "gather_resources")
    g.add_edge("gather_resources", "generate_session")
    g.add_edge("generate_session", "validate_session")

    g.add_conditional_edges(
        "validate_session",
        route_after_validation,
        {
            "return_result": "return_result",
            "revise_session": "revise_session_if_needed",
        },
    )
    g.add_edge("revise_session_if_needed", "validate_session")
    g.add_edge("return_result", END)

    return g.compile()


def run_session_design(
    deps: GraphDeps,
    user_context: UserLearningContext,
) -> SessionDesignResult:
    graph = build_graph(deps)
    initial: SessionDesignerState = {
        "user_context": user_context.model_dump(mode="json"),
        "revision_count": 0,
        "max_revisions": deps.max_revisions,
        "model": deps.model,
        "normalization_notes": [],
        "prototype_notes": [],
    }
    out = graph.invoke(initial)
    fr = out.get("final_result")
    if not fr:
        raise RuntimeError("Graph finished without final_result")
    return SessionDesignResult.model_validate(fr)
