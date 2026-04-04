# `cli/` — terminal entry point

Typer application exposed as the **`session-designer`** console script (see **`pyproject.toml`** **`[project.scripts]`**).

## Files

| Module | Purpose |
|--------|---------|
| `main.py` | Commands: **`version`**, **`run`**. **`run`**: loads **`.env`** (walks up from **`--fixture`** path), parses JSON → **`UserLearningContext`**, builds **`GraphDeps`** (**`MockLLMProvider`** or **`AnthropicLLMProvider`** + **`LLMResourceGatherer`**), calls **`run_session_design`**. Output: **`--format preview`** (default) uses Rich via **`preview.py`**; **`--format json`** / **`--compact`** emit JSON. Catches **`anthropic.APIError`** and missing-key **`ValueError`** for readable errors. |
| `preview.py` | **`print_session_preview`**: Rich panels, tables, and rules approximating an in-app session summary (not identical to a web UI, but closer than raw JSON). |

## How this folder connects

- **`data.repository.load_context_from_json`** — fixture loading.
- **`graph.builder.run_session_design`** + **`graph.deps.GraphDeps`** — runs the workflow.
- **`providers.*`** — which LLM implementation is used.
- **`resources.gatherer.LLMResourceGatherer`** — bundled with the same LLM as the rest of the graph.

A future HTTP API would likely call **`run_session_design`** with the same **`GraphDeps`** factory rather than reimplementing the graph.
