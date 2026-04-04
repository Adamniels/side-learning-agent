# `resources/` — suggested learning resources

Topic-specific links (official docs, tutorials, videos) are produced through a small **gatherer** abstraction so you can later plug in real search (Tavily, SerpAPI, etc.) without changing topic or session nodes.

## Files

| Module | Purpose |
|--------|---------|
| `gatherer.py` | **`ResourceGatherer`** protocol: **`gather(topic, user_context, model) -> list[SuggestedResource]`**. **`LLMResourceGatherer`**: calls the shared **`LLMProvider`** with prompts from **`prompts/templates.py`** and parses **`ResourceBatch`**. **`PlaceholderWebResourceGatherer`**: documents the future search-backed implementation (not implemented). |

## How this folder connects

- **`graph/deps.py`** can carry a **`ResourceGatherer`** (CLI wires **`LLMResourceGatherer(llm)`**).
- **`graph/nodes.py`** **`gather_resources`** calls **`deps.resource_gatherer.gather`** after **`choose_best_topic`**.
- **`domain/output.py`** **`SuggestedResource`** is the shared shape for the final result and for LLM structured output.

**Prototype caveat:** URLs are **model-suggested**, not fetched or verified live; **`SessionDesignResult.prototype_notes`** and prompts state this explicitly.
