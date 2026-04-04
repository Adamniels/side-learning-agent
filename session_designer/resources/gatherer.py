"""Resource gathering seam: prototype uses LLM suggestions; swap for web search later."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from session_designer.domain.llm_contracts import ResourceBatch
from session_designer.domain.models import UserLearningContext
from session_designer.domain.output import SelectedTopic, SuggestedResource
from session_designer.prompts import templates as T
from session_designer.providers.base import LLMProvider


@runtime_checkable
class ResourceGatherer(Protocol):
    def gather(
        self,
        *,
        topic: SelectedTopic,
        user_context: UserLearningContext,
        model: str,
    ) -> list[SuggestedResource]: ...


class LLMResourceGatherer:
    """
    Prototype implementation: proposes titles + URLs via the LLM.

    **URLs are not live-verified** (no search API). Production should add
    `WebSearchResourceGatherer` using Tavily/SerpAPI/etc. and dedupe against LLM hints.
    """

    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    def gather(
        self,
        *,
        topic: SelectedTopic,
        user_context: UserLearningContext,
        model: str,
    ) -> list[SuggestedResource]:
        user = T.resource_user_prompt(topic=topic, user_context=user_context)
        batch = self._llm.generate_structured(
            model=model,
            system=T.RESOURCE_SYSTEM,
            user=user,
            response_model=ResourceBatch,
            temperature=0.3,
        )
        return list(batch.resources)


class PlaceholderWebResourceGatherer:
    """
    Reserved for a search-backed implementation.

    Intended shape: run queries derived from `topic` + `user_context`, fetch snippets,
    rank official docs / tutorials / YouTube, return `list[SuggestedResource]`.
    """

    def gather(
        self,
        *,
        topic: SelectedTopic,
        user_context: UserLearningContext,
        model: str,
    ) -> list[SuggestedResource]:
        raise NotImplementedError("Wire a search API and ranking here.")
