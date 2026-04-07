# `examples/` — sample inputs

JSON fixtures for manual and automated runs of the session designer.

## Files

| File | Purpose |
|------|---------|
| `sample_context.json` | Example **`UserLearningContext`**: `user_id`, `interests`, `completed_sessions`, `uncompleted_sessions`. Used by **`session-designer run --fixture examples/sample_context.json`**. |

## Schema

The JSON shape matches **`UserLearningContext`** in **`session_designer/domain/models.py`** (Pydantic will coerce dates and reject unknown fields). `user_id` must be a valid UUID string.

## How this folder connects

- **`cli/main.py`** passes the path to **`load_context_from_json`**.
- The graph does **not** read this folder directly; only the CLI (or tests) do.

Add more fixtures here to try different personas or histories without code changes.
