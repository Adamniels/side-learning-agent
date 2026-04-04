# `graph/` — LangGraph workflow

Encodes the **fixed session-design pipeline**: normalize → analyze → candidate topics → choose topic → gather resources → generate session → validate → (optional) revise → return structured result.

## Files

| Module | Purpose |
|--------|---------|
| `state.py` | **`SessionDesignerState`** (`TypedDict`): JSON-friendly state keys (`user_context`, `learning_state`, `candidate_topics`, `draft_session`, `validation`, `revision_count`, …). |
| `deps.py` | **`GraphDeps`**: **`llm`**, **`resource_gatherer`**, **`model`**, **`max_revisions`** — injected into every node via **`functools.partial`**. |
| `nodes.py` | One function per node: **`normalize_input`**, **`analyze_learning_state`**, **`generate_candidate_topics`**, **`choose_best_topic`**, **`gather_resources`**, **`generate_session`**, **`validate_session`**, **`revise_session`**, **`return_result`**, plus **`route_after_validation`** for conditional edges. |
| `builder.py` | **`build_graph(deps)`** → compiled graph; **`run_session_design(deps, user_context)`** builds initial state and **`invoke`s** the graph. |

## Graph topology (summary)

Linear chain through **`generate_session`**, then **`validate_session`**. Conditional routing:

- If validation **`passed`** → **`return_result`**
- If not passed and **`revision_count < max_revisions`** → **`revise_session_if_needed`** → back to **`validate_session`**
- Otherwise → **`return_result`** (best effort + validation notes)

## How this folder connects

- **Upstream:** **`cli/main.py`** builds **`GraphDeps`** and calls **`run_session_design`**.
- **Domain:** nodes read/write **`domain`** models (via **`model_validate`** / **`model_dump`** on state slices).
- **Prompts:** **`prompts/templates.py`** supplies system/user strings.
- **Providers / resources:** nodes use **`deps.llm`** and **`deps.resource_gatherer`** only — no direct vendor SDKs here.

`__init__.py` re-exports **`GraphDeps`**, **`build_graph`**, **`run_session_design`** for convenience.
