# `session_designer` package

Python package for the **session designer** prototype: a fixed LangGraph workflow that reads learner context, proposes and ranks topics, gathers resource hints, drafts a session (goal, context, hands-on, extension), validates it, and optionally revises.

## How it fits the whole project

- **`cli/`** — Entry point (`session-designer` console script loads fixture, wires deps, invokes the graph).
- **`domain/`** — Pydantic types: user context, session sections, final `SessionDesignResult`, and LLM structured-output contracts.
- **`data/`** — Read-only **repository** boundary for loading `UserLearningContext` (JSON fixture today; DB later).
- **`providers/`** — **LLM abstraction** (`LLMProvider`): Anthropic implementation + mock for offline runs.
- **`resources/`** — **Resource gathering** abstraction (prototype: LLM-suggested links; seam for real web search).
- **`graph/`** — LangGraph **state**, **nodes**, and **graph builder** (`build_graph`, `run_session_design`).
- **`prompts/`** — System/user prompt strings used by graph nodes (keeps nodes thin).

Data flows: **CLI** → load context (via `data` helpers) → **GraphDeps** (`providers` + `resources`) → **graph** nodes → **domain** models in/out → final JSON from **`SessionDesignResult`**.

## Subfolder docs

| Folder | README |
|--------|--------|
| Domain models & schemas | [domain/README.md](domain/README.md) |
| User context loading | [data/README.md](data/README.md) |
| Model providers | [providers/README.md](providers/README.md) |
| Resource gathering | [resources/README.md](resources/README.md) |
| LangGraph workflow | [graph/README.md](graph/README.md) |
| Prompt templates | [prompts/README.md](prompts/README.md) |
| Terminal CLI | [cli/README.md](cli/README.md) |

Project install and run instructions stay in the repository root [README.md](../README.md).
