# Session designer (LangGraph prototype)

Learning session **designer** agent: picks a next topic from user context, drafts goal / context / hands-on / extension, validates, and optionally revises.

## Code layout (per-folder docs)

- **Package overview and subfolder index:** [session_designer/README.md](session_designer/README.md)
- **Sample JSON fixtures:** [examples/README.md](examples/README.md)

Each major directory under `session_designer/` also has its own `README.md` (domain, data, providers, resources, graph, prompts, cli).

## Prerequisites

- **Python 3.11+** (see `requires-python` in `pyproject.toml`)

## Install (create a venv first)

Do **not** install into the system Python. Create and use a virtual environment, then install in dependency order:

```bash
cd /path/to/create-session-agent

# 1. Create the venv (use a 3.11+ interpreter)
python3.11 -m venv .venv
# If `python3` is already 3.11 or newer on your machine:
#   python3 -m venv .venv

# 2. Activate it
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows

# 3. Upgrade pip (recommended for editable installs)
python -m pip install --upgrade pip

# 4. Install this package in editable mode
pip install -e ".[dev]"
```

Copy `.env.example` to `.env` in the project root and set `ANTHROPIC_API_KEY` when not using `--mock`. The CLI loads `.env` by walking up from the `--fixture` path, so it still finds the project `.env` when you pass `examples/sample_context.json`.

## HTTP API (FastAPI, async jobs)

Used by the .NET backend: accepts **`POST /v1/design-jobs`** (returns **202** immediately), runs `run_session_design` in a background task, then POSTs results to the `callbackUrl` with header **`X-Session-Designer-Secret`**.

```bash
# After pip install -e ".[dev]" in a venv:
export SESSION_DESIGNER_SHARED_SECRET="same-as-dotnet-SessionDesigner__SharedSecret"
# Optional: no Anthropic key required
export SESSION_DESIGNER_USE_MOCK=true

uvicorn session_designer.api.main:app --host 0.0.0.0 --port 8010
```

Health: **`GET /health`**.

## Run

```bash
# Package version
session-designer version

# Deterministic mock (no API key)
session-designer run --fixture examples/sample_context.json --mock

# Anthropic (requires .env with ANTHROPIC_API_KEY)
session-designer run --fixture examples/sample_context.json
```

Optional flags:

- **`--format preview`** (default): Rich “app-like” layout in the terminal (topic hero, session cards, resources, validation).
- **`--format json`**: indented JSON for scripts and piping.
- **`--compact`** or **`--format compact`**: single-line JSON.
- **`--max-revisions N`** (default 2).

Equivalent module invocation:

`python -m session_designer.cli run --fixture examples/sample_context.json --mock`

If Anthropic returns errors about **credit balance** or **billing**, that is account-side (org, API key, or prepaid credits). Use `--mock` to exercise the graph without the API.

## Output

Structured JSON matching **`SessionDesignResult`** in [`session_designer/domain/output.py`](session_designer/domain/output.py). Top-level fields include:

| Field | Role |
|--------|------|
| `session_payload` | Persistence-ready session data (`title`, `summary`, `difficulty_alignment`, `goal`, `context`, `hands_on`, `hands_on_expected_output`, `extension`, `subject_areas`, optional `estimated_duration_in_minutes`) |
| `designer_metadata` | Designer-owned generation metadata (`why_chosen`, `candidates_considered`, `validation`, `revision_count`, notes) |
| `suggested_resources` | Kind, title, url, rationale (LLM-suggested in prototype; not live-verified) |
