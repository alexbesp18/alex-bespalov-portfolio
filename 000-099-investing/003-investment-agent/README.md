# Investment Agent

An AI-powered investment analysis agent that processes podcast transcripts and earnings reports through a sophisticated 3-step LLM pipeline to extract investment themes, identify publicly traded companies, and filter for high-conviction picks with recent positive catalysts.

## Key Features

- **Multi-Provider LLM Support**: Seamlessly switch between Claude (Anthropic), GPT (OpenAI), Grok (xAI), and Gemini (Google) with unified interface
- **3-Step Analysis Pipeline**: Extract themes → Identify companies → Filter for catalysts
- **Structured Output Parsing**: Pydantic models ensure reliable, type-safe data extraction
- **Retry Logic & Error Handling**: Automatic retry with exponential backoff for production reliability
- **Streaming Support**: Real-time streaming for large model outputs
- **Advanced Features**: Extended thinking budgets (Claude), web search integration (OpenAI/Gemini), reasoning effort control
- **Production-Ready**: Comprehensive logging, type hints, configuration management, and test suite

## Architecture

The agent follows a modular architecture with clear separation of concerns:

```
Input Transcript → [Step 1: Theme Extraction] → Themes
                                          ↓
                    [Step 2: Company Identification] → Companies
                                          ↓
                    [Step 3: Catalyst Filtering] → Investment Opportunities
                                          ↓
                                    Output Report
```

**Components:**
- **Agent** (`src/agent/`): Orchestrates the 3-step pipeline
- **LLM Client** (`src/llm/`): Unified interface with retry logic and multi-provider support
- **Prompts** (`src/llm/prompts/`): Externalized, versioned prompt templates
- **Parsing** (`src/utils/parsing.py`): Structured output parsing with Pydantic models
- **Config** (`src/config.py`): Environment-based configuration with pydantic-settings

## Quick Start

### Prerequisites

- Python 3.10+
- API keys for at least one LLM provider:
  - [Anthropic Claude](https://console.anthropic.com/)
  - [OpenAI](https://platform.openai.com/api-keys)
  - [xAI Grok](https://console.x.ai/)
  - [Google Gemini](https://makersuite.google.com/app/apikey)

### Installation

```bash
# Clone the repository
git clone https://github.com/alexbesp18/investment-agent
cd investment-agent

# Install dependencies
pip install -r requirements.txt
# or use Makefile
make install

# Setup environment
cp .env.example .env
# Edit .env and add your API keys
```

### Usage

1. **Place your transcript file** in the `input/` directory:
   ```bash
   echo "Your transcript content here" > input/transcript.txt
   ```

2. **Run the agent**:
   ```bash
   python -m src.main
   # or use Makefile
   make run
   ```

3. **Select your LLM provider** when prompted (interactive selection)

4. **Find results** in the `output/` directory with timestamped analysis reports

### CLI Options

```bash
python -m src.main --help

Options:
  --input PATH      Input folder path (default: input/)
  --output PATH     Output folder path (default: output/)
  --log-level LEVEL Logging level: DEBUG, INFO, WARNING, ERROR
  --log-file PATH   Optional log file path
```

## Example Output

```
🚀 Investment Analysis Agent Starting...
============================================================

🤖 SELECT YOUR LLM PROVIDER
============================================================
1. Claude (sonnet-4.5)
2. OpenAI (gpt-4)
3. Grok (grok-4)
4. Gemini (gemini-2.5-pro)

Select provider (1-4): 1
✅ Selected: Claude - sonnet-4.5

📄 Reading: transcript.txt

🔍 STEP 1: Extracting investment themes...
✅ Themes extracted

🏢 STEP 2: Finding publicly traded companies...
✅ Companies identified

📊 STEP 3: Filtering for recent earnings catalysts...
✅ Filtered to high conviction picks

💾 Full analysis saved to: output/analysis_20250115_143022.txt

============================================================
🎯 TOP INVESTMENT OPPORTUNITIES
============================================================

📌 NVDA
   Cap Size: Large
   💡 AI chip demand exceeding supply with multi-quarter backlog

📌 VRT
   Cap Size: Mid
   💡 AI-driven thermal management demand outpacing capacity
```

## Project Structure

```
investment-agent/
├── README.md
├── requirements.txt          # Pinned dependencies
├── .env.example             # Environment template
├── .gitignore               # Comprehensive ignore rules
├── Makefile                 # Common commands
├── AUDIT_REPORT.md          # Initial audit findings
│
├── src/
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   ├── config.py            # Configuration management
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   └── investment_agent.py  # Main agent logic
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py        # Unified LLM client with retry
│   │   └── prompts/
│   │       ├── theme_extraction.txt
│   │       ├── company_identification.txt
│   │       └── catalyst_filtering.txt
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logging.py        # Logging configuration
│       └── parsing.py        # Structured output parsing
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures
│   ├── test_config.py       # Config tests
│   ├── test_parsing.py      # Parsing tests
│   ├── test_llm_client.py   # LLM client tests
│   └── test_agent.py        # Integration tests
│
└── data/
    └── samples/             # Sample transcripts
```

## Configuration

Configuration is managed through environment variables (`.env` file). Key settings:

### API Keys (Required)
```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
XAI_API_KEY=xai-...
GOOGLE_API_KEY=...
```

### Provider Settings
Each provider can be enabled/disabled and configured independently:

```bash
# Claude
CLAUDE_ENABLED=true
CLAUDE_MODEL=sonnet-4.5
CLAUDE_USE_EXTENDED_THINKING=true
CLAUDE_THINKING_BUDGET_TOKENS=32000
CLAUDE_MAX_TOKENS=64000

# OpenAI
OPENAI_ENABLED=true
OPENAI_MODEL=gpt-4
OPENAI_REASONING_EFFORT=high
OPENAI_WEB_SEARCH_ENABLED=false

# ... (see .env.example for full configuration)
```

### Logging
```bash
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
# LOG_FILE=logs/agent.log  # Optional file logging
```

## Technical Notes

### Multi-Provider Abstraction
The `LLMClient` class provides a unified interface across providers, handling:
- Provider-specific API differences (Anthropic Messages API vs OpenAI Responses API vs Gemini)
- Model name mapping (config-friendly names → API model strings)
- Streaming support for large outputs
- Provider-specific features (thinking budgets, web search, reasoning effort)

### Retry Logic
All LLM calls are wrapped with `tenacity` retry decorator:
- **3 attempts** maximum
- **Exponential backoff**: 4s → 8s → 16s (capped at 60s)
- **Automatic retry** on transient failures (network errors, rate limits)

### Structured Output Parsing
- Prompts request JSON output with defined schemas
- Pydantic models (`Theme`, `Company`, `InvestmentOpportunity`) validate responses
- Fallback parsing handles markdown code blocks and mixed-format responses
- Type-safe data extraction prevents runtime errors

### Prompt Engineering
- Prompts are externalized to `src/llm/prompts/` for versioning and easy iteration
- Each prompt includes JSON schema specification for structured output
- Prompts are designed to work across all providers while leveraging provider-specific capabilities (web search, thinking)

### Error Handling
- Comprehensive error handling at each layer
- Logging at appropriate levels (DEBUG for details, ERROR for failures)
- User-friendly error messages for common issues (missing API keys, file not found)
- Graceful degradation (fallback parsing if structured output fails)

## Development

### Running Tests
```bash
make test
# or
pytest tests/ -v
```

### Code Quality
```bash
# Lint
make lint

# Format
make format

# Clean cache
make clean
```

### Adding a New Provider
1. Add API key to `Settings` in `src/config.py`
2. Implement provider-specific logic in `LLMClient._call_<provider>()`
3. Add model mappings in `_get_model_mapping()`
4. Update `.env.example` with provider settings

## License

MIT

## Author

Built for portfolio demonstration of production-ready AI/ML engineering practices.
