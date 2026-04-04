from __future__ import annotations

from dataclasses import dataclass

from session_designer.providers.base import LLMProvider
from session_designer.resources.gatherer import ResourceGatherer


@dataclass
class GraphDeps:
    llm: LLMProvider
    resource_gatherer: ResourceGatherer
    model: str
    max_revisions: int = 2
