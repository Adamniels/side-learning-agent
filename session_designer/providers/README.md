# `providers/` — LLM abstraction

Model calls are isolated behind **`LLMProvider`** so you can swap Anthropic, OpenAI, local servers, or mocks without rewriting graph nodes.

## Files

| Module | Purpose |
|--------|---------|
| `base.py` | **`LLMProvider`** protocol: **`generate_structured`** (Pydantic output) and **`generate_text`**. |
| `anthropic_provider.py` | **`AnthropicLLMProvider`**: LangChain **`ChatAnthropic`** + **`with_structured_output`**, with JSON fallback parsing. Env: **`ANTHROPIC_API_KEY`**, **`ANTHROPIC_MODEL`**. |
| `mock_provider.py` | **`MockLLMProvider`**: deterministic structured responses for CI/demo without API keys. |

## How this folder connects

- **`graph/deps.py`** **`GraphDeps`** holds an **`LLMProvider`** instance.
- **`graph/nodes.py`** only calls **`deps.llm.generate_structured`** / text (if used).
- **`cli/main.py`** constructs **`AnthropicLLMProvider`** or **`MockLLMProvider`** and passes it into **`GraphDeps`**.
- **`resources/gatherer.py`** **`LLMResourceGatherer`** also uses the same **`LLMProvider`** for resource suggestions.

To add another vendor, implement **`LLMProvider`** in a new module and select it in the CLI or a future factory.
