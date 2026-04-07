import pytest

from session_designer.domain.models import UserLearningContext
from session_designer.prompts.templates import TOPIC_SYSTEM
from session_designer.prompts.templates import topic_user_prompt


def test_user_interest_context_is_supported_and_serialized_in_prompt() -> None:
    ctx = UserLearningContext.model_validate(
        {
            "user_id": "user_demo_1",
            "interests": [
                {
                    "label": "Cybersecurity",
                    "weight": 0.9,
                    "context": "Practical API auth hardening and token security patterns.",
                }
            ],
        }
    )

    prompt = topic_user_prompt(ctx, analysis={})
    assert "Practical API auth hardening and token security patterns." in prompt


def test_user_interest_context_defaults_to_empty_for_legacy_payloads() -> None:
    ctx = UserLearningContext.model_validate(
        {
            "user_id": "user_demo_1",
            "interests": [{"label": "Cybersecurity", "weight": 0.9}],
        }
    )

    assert ctx.interests[0].context == ""


def test_user_learning_context_rejects_legacy_skill_levels_payload() -> None:
    with pytest.raises(ValueError):
        UserLearningContext.model_validate(
            {
                "user_id": "user_demo_1",
                "interests": [{"label": "Cybersecurity", "weight": 0.9}],
                "skill_levels": [{"topic": "Python", "level": "beginner"}],
            }
        )


def test_topic_prompt_rules_do_not_reference_skill_levels() -> None:
    assert "skill levels" not in TOPIC_SYSTEM.lower()
