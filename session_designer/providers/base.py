from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@runtime_checkable
class LLMProvider(Protocol):
    """Swap implementations (Anthropic, OpenAI, local, mock) without changing graph nodes."""

    def generate_structured(
        self,
        *,
        model: str,
        system: str,
        user: str,
        response_model: type[T],
        temperature: float = 0.2,
    ) -> T: ...

    def generate_text(
        self,
        *,
        model: str,
        system: str,
        user: str,
        temperature: float = 0.3,
    ) -> str: ...
