from pathlib import Path
from uuid import UUID

import pytest

from session_designer.data.repository import JsonFileUserContextRepository


def test_json_file_repository_returns_context_for_matching_uuid(tmp_path: Path) -> None:
    user_id = UUID("0f5db95f-566c-42f8-af4f-5662134f04d8")
    fixture = tmp_path / "context.json"
    fixture.write_text(
        """
{
  "user_id": "0f5db95f-566c-42f8-af4f-5662134f04d8",
  "interests": [{"label": "Cybersecurity", "weight": 0.9}],
  "completed_sessions": [],
  "uncompleted_sessions": []
}
""".strip(),
        encoding="utf-8",
    )

    repository = JsonFileUserContextRepository(fixture)
    context = repository.get_context(user_id)

    assert context.user_id == user_id


def test_json_file_repository_rejects_mismatched_uuid(tmp_path: Path) -> None:
    fixture = tmp_path / "context.json"
    fixture.write_text(
        """
{
  "user_id": "0f5db95f-566c-42f8-af4f-5662134f04d8",
  "interests": [{"label": "Cybersecurity", "weight": 0.9}],
  "completed_sessions": [],
  "uncompleted_sessions": []
}
""".strip(),
        encoding="utf-8",
    )

    repository = JsonFileUserContextRepository(fixture)
    different_user_id = UUID("d2f5d9d5-b4f0-47cf-8502-ded0186d4603")

    with pytest.raises(KeyError):
        repository.get_context(different_user_id)
