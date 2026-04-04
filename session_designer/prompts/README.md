# `prompts/` — prompt text for nodes

Holds **static prompt strings and small builders** so **`graph/nodes.py`** stays focused on orchestration and Pydantic I/O.

## Files

| Module | Purpose |
|--------|---------|
| `templates.py` | Constants like **`ANALYSIS_SYSTEM`**, **`TOPIC_SYSTEM`**, **`SESSION_SYSTEM`**, **`VALIDATION_SYSTEM`**, **`REVISION_SYSTEM`**, **`RESOURCE_SYSTEM`**, plus functions that format **`UserLearningContext`** and intermediate artifacts into user messages (**`analysis_user_prompt`**, **`topic_user_prompt`**, **`session_user_prompt`**, etc.). |

## How this folder connects

- **`graph/nodes.py`** imports the module as **`T`** and passes **`T.*_SYSTEM`** / **`T.*_user_prompt(...)`** into **`deps.llm.generate_structured`**.
- **`resources/gatherer.py`** uses **`RESOURCE_SYSTEM`** and **`resource_user_prompt`** for the resource step.

Tweaking behavior for experiments usually starts here or in **`graph/nodes`** (temperature/model), not in provider internals.
