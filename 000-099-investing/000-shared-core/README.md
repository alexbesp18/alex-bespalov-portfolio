# Shared Core Library

Centralized library for common utilities used across the portfolio projects. Reduces code duplication and ensures consistent behavior.

## Features

- **Unified LLM Client**: Single interface for Claude, GPT, Grok, and Gemini
- **Auto-Retry Logic**: Tenacity-based retries with exponential backoff
- **System Messages**: Support for system prompts across all providers
- **Streaming**: Optional streaming for large outputs (Claude)

## Supported Providers

| Provider | Model Examples | Features |
|----------|---------------|----------|
| Claude (Anthropic) | sonnet-4.5, opus-4.1 | Extended thinking, streaming |
| GPT (OpenAI) | gpt-4, gpt-5 | Web search, reasoning effort |
| Grok (xAI) | grok-4, grok-4-fast | Fast inference |
| Gemini (Google) | gemini-2.5-pro | Web search, system instruction |

## Installation

```bash
cd 000-shared-core
pip install -r requirements.txt
```

## Usage

```python
from shared_core.llm import LLMClient

# Initialize
client = LLMClient(
    provider="claude",
    api_key="sk-...",
    provider_settings={
        "model": "sonnet-4.5",
        "max_tokens": 4096
    }
)

# Simple call
response = client.call_llm("Hello, world!")

# With system message
response = client.call_llm(
    prompt="Analyze this stock",
    system_message="You are a technical analysis expert."
)
```

## Integration

Projects using this library:
- `003-investment-agent`
- `006-ai-stock-analyzer`
- `008-ticker-analysis-sheets`

These projects add the shared core to their Python path:
```python
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parents[3] / "000-shared-core" / "src"))
from shared_core.llm import LLMClient
```

## Running Tests

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
pytest tests/ -v
```

## Project Structure

```
000-shared-core/
├── src/
│   └── shared_core/
│       ├── __init__.py
│       └── llm/
│           ├── __init__.py
│           └── client.py      # Unified LLM client
├── tests/
│   └── test_llm.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

## License

Private/Internal Use
