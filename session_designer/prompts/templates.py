from __future__ import annotations

import json
from typing import Any

from session_designer.domain.models import UserLearningContext
from session_designer.domain.output import CandidateTopic, SelectedTopic
from session_designer.domain.session_schema import DesignedSession


def _ctx_json(ctx: UserLearningContext) -> str:
    return json.dumps(ctx.model_dump(mode="json"), indent=2)


ANALYSIS_SYSTEM = """You are a learning path analyst for a session DESIGNER (not a tutor).
Infer themes already covered, gaps vs stated interests, repetition risks, and level constraints.
Output structured JSON matching the schema. Be concise."""


def analysis_user_prompt(ctx: UserLearningContext) -> str:
    return f"User learning context:\n{_ctx_json(ctx)}"


TOPIC_SYSTEM = """You propose 3 to 5 candidate NEXT session topics for a learner.
Rules:
- Must align with interests and self-reported skill levels.
- Avoid repeating completed session themes unless clearly deeper/next step.
- Each topic must be concrete enough for one session with a hands-on artifact.
- Broad enough they can research further afterward.
- Assign each candidate a short stable `id` like c1, c2, ...
Output structured candidates only."""


def topic_user_prompt(ctx: UserLearningContext, analysis: dict[str, Any]) -> str:
    return (
        f"Context:\n{_ctx_json(ctx)}\n\n"
        f"Prior analysis (JSON):\n{json.dumps(analysis, indent=2)}"
    )


CHOOSE_SYSTEM = """You compare candidate topics and pick the single best NEXT session.
Explain why it wins vs the others for progression, level fit, and non-repetition.
Output structured JSON matching the schema."""


def choose_user_prompt(
    ctx: UserLearningContext,
    analysis: dict[str, Any],
    candidates: list[CandidateTopic],
) -> str:
    cjson = [c.model_dump(mode="json") for c in candidates]
    return (
        f"User context:\n{_ctx_json(ctx)}\n\n"
        f"Analysis:\n{json.dumps(analysis, indent=2)}\n\n"
        f"Candidates:\n{json.dumps(cjson, indent=2)}"
    )


RESOURCE_SYSTEM = """You suggest 3 to 6 high-quality learning resources.
Preference order: (1) official documentation, (2) reputable tutorials, (3) strong YouTube, (4) other only if needed.
Avoid random low-quality blogs.
**Prototype limitation**: propose plausible URLs you know or strongly believe exist; they are NOT verified live.
Use `kind` one of: official_docs, tutorial, video, other.
Output structured JSON only."""


def resource_user_prompt(*, topic: SelectedTopic, user_context: UserLearningContext) -> str:
    return (
        f"Selected topic:\n{topic.model_dump_json(indent=2)}\n\n"
        f"User context:\n{_ctx_json(user_context)}"
    )


SESSION_SYSTEM = """You design ONE learning session for self-study (not live tutoring).
Sections ONLY: goal, context, hands-on, extension, subject_areas. NO reflection section.
- Goal: concrete, achievable in one sitting.
- Context: SHORT motivating orientation (what/why), not deep explanation.
- Hands-on: step-by-step, produces a tangible output; scoped to one session; not vague.
- Extension: natural deeper follow-on session idea.
- Subject areas: return 1 to 6 short lowercase classification labels for where this session belongs
  (examples: api, python, http, auth, fastapi). Avoid duplicates.
Use the suggested resources as hints; do not paste long excerpts.
Output structured JSON matching DesignedSession schema."""


def session_user_prompt(
    *,
    ctx: UserLearningContext,
    analysis: dict[str, Any],
    selected: SelectedTopic,
    why_chosen: str,
    resources: list[dict[str, Any]],
) -> str:
    return (
        f"User context:\n{_ctx_json(ctx)}\n\n"
        f"Analysis:\n{json.dumps(analysis, indent=2)}\n\n"
        f"Selected topic:\n{selected.model_dump_json(indent=2)}\n\n"
        f"Why chosen:\n{why_chosen}\n\n"
        f"Resources (hint list):\n{json.dumps(resources, indent=2)}"
    )


VALIDATION_SYSTEM = """You validate a designed learning session from a session designer agent.
Check:
- Topic is a sensible next step for this user (level, interests, history).
- Goal is concrete.
- Context is short and useful, not overly deep.
- Hands-on is concrete, realistic for one session, produces an actual output/deliverable.
- Extension naturally builds on the session.
- Overall coherence; not too shallow, too broad, or too ambitious for one session.
Return structured checklist with passed flags, issues, suggested_fixes, and overall passed boolean."""


def validation_user_prompt(
    *,
    ctx: UserLearningContext,
    selected: SelectedTopic,
    session: DesignedSession,
) -> str:
    return (
        f"User context:\n{_ctx_json(ctx)}\n\n"
        f"Selected topic:\n{selected.model_dump_json(indent=2)}\n\n"
        f"Designed session:\n{session.model_dump_json(indent=2)}"
    )


REVISION_SYSTEM = """You revise a designed session to address validation issues.
Regenerate a full improved DesignedSession (goal, context, hands_on, extension).
Keep the same selected topic intent; fix concreteness, length, and exercise scope.
Output structured JSON: SessionRevision with field `session` only."""


def revision_user_prompt(
    *,
    ctx: UserLearningContext,
    selected: SelectedTopic,
    session: DesignedSession,
    validation_issues: list[str],
    suggested_fixes: list[str],
) -> str:
    return (
        f"User context:\n{_ctx_json(ctx)}\n\n"
        f"Selected topic:\n{selected.model_dump_json(indent=2)}\n\n"
        f"Current session:\n{session.model_dump_json(indent=2)}\n\n"
        f"Issues:\n{json.dumps(validation_issues, indent=2)}\n\n"
        f"Suggested fixes:\n{json.dumps(suggested_fixes, indent=2)}"
    )
