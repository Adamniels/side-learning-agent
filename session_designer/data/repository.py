from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol, runtime_checkable
from uuid import UUID

from session_designer.domain.models import UserLearningContext


@runtime_checkable
class UserContextRepository(Protocol):
    """Read-only access to user learning context (replace with DB-backed impl later)."""

    def get_context(self, user_id: UUID) -> UserLearningContext: ...


class InMemoryUserContextRepository:
    def __init__(self, contexts: dict[UUID, UserLearningContext]) -> None:
        self._contexts = contexts

    def get_context(self, user_id: UUID) -> UserLearningContext:
        if user_id not in self._contexts:
            raise KeyError(f"No context for user_id={user_id!r}")
        return self._contexts[user_id]


class JsonFileUserContextRepository:
    """Loads a single fixed context file (prototype); production would query by user_id."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._data = json.loads(path.read_text(encoding="utf-8"))

    def get_context(self, user_id: UUID) -> UserLearningContext:
        raw = dict(self._data)
        fid = raw.get("user_id")
        if fid is not None and UUID(str(fid)) != user_id:
            raise KeyError(f"Fixture user_id {fid!r} does not match requested {user_id!r}")
        raw["user_id"] = str(user_id)
        return UserLearningContext.model_validate(raw)


def load_context_from_json(path: Path) -> UserLearningContext:
    """Convenience: parse a fixture without embedding user_id lookup semantics."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return UserLearningContext.model_validate(data)
