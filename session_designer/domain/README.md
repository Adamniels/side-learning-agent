# `domain/` — models and schemas

This folder holds **Pydantic v2** types: the language of the app (inputs, intermediate structured LLM outputs, and the final API-shaped result).

## Files

| Module | Purpose |
|--------|---------|
| `models.py` | **`UserLearningContext`**: UUID `user_id`, interests, completed/uncompleted **`PastSession`** rows. This is what the graph treats as read-only input (canonical data lives outside the agent). |
| `session_schema.py` | **`DesignedSession`**: nested **`SessionGoal`**, **`SessionContext`**, **`HandsOnExercise`**, **`ExtensionSuggestion`** — the four sections only (no reflection). |
| `output.py` | **`SessionDesignResult`** (final payload), **`CandidateTopic`**, **`SelectedTopic`**, **`SuggestedResource`**, **`ValidationResult`**, enums like **`ResourceKind`**. |
| `llm_contracts.py` | Pydantic types used **only as structured LLM outputs** (e.g. **`LearningStateAnalysis`**, **`CandidateTopicBatch`**, **`ChooseTopicOutput`**, **`ResourceBatch`**, **`SessionRevision`**). |

## How this folder connects

- **`data/`** and **`cli/`** validate or build **`UserLearningContext`** from JSON using these models.
- **`graph/nodes.py`** converts graph state dicts ↔ domain models, and calls **`LLMProvider.generate_structured(..., response_model=...)`** with types from `llm_contracts.py` or `output.py` / `session_schema.py`.
- **`graph/nodes.py`** **`return_result`** builds **`SessionDesignResult`** for the CLI to print.

Keeping contracts here keeps **validation rules** in one place and avoids the graph or providers owning business shapes.
