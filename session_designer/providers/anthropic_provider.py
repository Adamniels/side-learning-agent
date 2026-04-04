from __future__ import annotations

import json
import os
from typing import TypeVar

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, ValidationError

from session_designer.providers.base import LLMProvider

T = TypeVar("T", bound=BaseModel)


class AnthropicLLMProvider:
    """Anthropic via LangChain ChatAnthropic with structured output + JSON fallback."""

    def __init__(self, *, api_key: str | None = None, default_model: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._default_model = default_model or os.environ.get(
            "ANTHROPIC_MODEL", "claude-sonnet-4-20250514"
        )
        if not self._api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for AnthropicLLMProvider")

    def _chat(self, model: str, temperature: float = 0.2) -> ChatAnthropic:
        return ChatAnthropic(
            model=model,
            api_key=self._api_key,
            temperature=temperature,
            max_tokens=4096,
        )

    def generate_structured(
        self,
        *,
        model: str,
        system: str,
        user: str,
        response_model: type[T],
        temperature: float = 0.2,
    ) -> T:
        m = model or self._default_model
        chat = self._chat(m, temperature).with_structured_output(response_model)
        messages = [SystemMessage(content=system), HumanMessage(content=user)]
        try:
            out = chat.invoke(messages)
            if isinstance(out, response_model):
                return out
            if isinstance(out, dict):
                return response_model.model_validate(out)
        except (ValidationError, ValueError, TypeError):
            pass
        return self._fallback_json(m, system, user, response_model, temperature)

    def _fallback_json(
        self,
        model: str,
        system: str,
        user: str,
        response_model: type[T],
        temperature: float,
    ) -> T:
        sys2 = (
            system
            + "\n\nRespond with a single JSON object only, no markdown, "
            + f"matching this schema name: {response_model.__name__}. "
            + "Keys must match the model fields exactly."
        )
        chat = self._chat(model, temperature)
        messages = [SystemMessage(content=sys2), HumanMessage(content=user)]
        text = str(chat.invoke(messages).content)
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        try:
            data = json.loads(text)
            return response_model.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as e:
            raise ValueError(f"Structured output fallback failed: {e}") from e

    def generate_text(
        self,
        *,
        model: str,
        system: str,
        user: str,
        temperature: float = 0.3,
    ) -> str:
        m = model or self._default_model
        chat = self._chat(m, temperature)
        messages = [SystemMessage(content=system), HumanMessage(content=user)]
        return str(chat.invoke(messages).content)
