# `data/` — read-only user context access

This folder defines how the agent **reads** learner context without owning canonical storage. The real product database remains the source of truth; this layer is a **replaceable adapter**.

## Files

| Module | Purpose |
|--------|---------|
| `repository.py` | **`UserContextRepository`** protocol: `get_context(user_id)` where `user_id` is a UUID. Implementations: **`InMemoryUserContextRepository`** (dict of contexts), **`JsonFileUserContextRepository`** (prototype: one JSON file; strict user_id match), **`load_context_from_json(path)`** (parse fixture → **`UserLearningContext`**). |

## How this folder connects

- **`cli/main.py`** uses **`load_context_from_json`** for `--fixture path/to.json` (simplest prototype path).
- Production: swap in a class that loads from your DB/API via **`UserContextRepository`**, still returning **`UserLearningContext`** from **`domain/models.py`**.

The **graph** never imports SQL or HTTP directly; it only sees **`UserLearningContext`** already materialized in LangGraph state (`user_context` dict).
