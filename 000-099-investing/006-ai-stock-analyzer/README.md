# AI Stock Analyzer

> Multi-agent AI system that analyzes stocks using 4 LLM models (Claude, GPT, Grok, Gemini) for consensus-based technical analysis with 90% API cost reduction.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-ruff-orange.svg)](https://github.com/astral-sh/ruff)

## Key Features

- **4-Model AI Consensus** - Claude, GPT, Grok, and Gemini analyze independently, then arbitrate disagreements
- **90% API Cost Reduction** - Single data call per stock (1 credit vs 7+) with client-side indicator calculation  
- **20+ Technical Indicators** - RSI, MACD, Bollinger Bands, ATR, Stochastic, support/resistance levels
- **Automatic Retry Logic** - Tenacity-based retries with exponential backoff for LLM calls
- **Google Sheets Output** - Color-coded results with 22 columns of analysis data
- **Production-Ready** - Pydantic config, proper logging, modular architecture, test suite

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        AI Stock Analyzer                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│   Twelve Data API ──────► TechnicalCalculator                    │
│   (1 credit/stock)         (20+ indicators)                      │
│                                   │                               │
│                                   ▼                               │
│                    ┌──────────────────────────┐                  │
│                    │   Parallel AI Analysis    │                  │
│                    │  ┌──────┬──────┬───────┐ │                  │
│                    │  │Claude│ GPT  │ Grok  │ │                  │
│                    │  │      │      │       │ │                  │
│                    │  │Gemini│  +   │       │ │                  │
│                    │  └──────┴──────┴───────┘ │                  │
│                    └───────────┬──────────────┘                  │
│                                │                                  │
│                                ▼                                  │
│                    ┌──────────────────────────┐                  │
│                    │   Claude Arbitrator       │                  │
│                    │   (resolves disagreements)│                  │
│                    └───────────┬──────────────┘                  │
│                                │                                  │
│                                ▼                                  │
│                    ┌──────────────────────────┐                  │
│                    │   Google Sheets Output    │                  │
│                    │   (color-coded results)   │                  │
│                    └──────────────────────────┘                  │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Python 3.9+
- API Keys: Anthropic, OpenAI, Google AI, XAI, Twelve Data
- Google Cloud Service Account (for Sheets integration)

### Installation

```bash
# Clone the repository
git clone https://github.com/alexbesp18/ai-stock-analyzer
cd ai-stock-analyzer

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp config.json.example config.json
# Edit config.json with your API keys

# (Optional) Add Google service account for Sheets
# Place service-account.json in project root
```

### Usage

```bash
# Analyze specific tickers
python -m src.main AAPL MSFT NVDA

# Process tickers from Google Sheet
python -m src.main

# Verbose output for debugging
python -m src.main -v AAPL

# Using Makefile
make run TICKERS="AAPL MSFT"
```

## Example Output

```
╔══════════════════════════════════════════════════════════════════════╗
║          AI STOCK ANALYZER - MULTI-AGENT TECHNICAL ANALYSIS          ║
╚══════════════════════════════════════════════════════════════════════╝

[1/3] AAPL...
  Fetching market data for AAPL (1 credit only)
  Calculated indicators: RSI=52.3, MACD=1.234
  Running agent analyses in parallel
  Gemini result: score 7/10
  GPT result: score 7/10  
  Grok result: score 6/10
  Full agreement - averaging results
  
  Cost: $0.02 | Agreement: FULL_AGREEMENT
  Technical Score: 7/10
  Price: $185.42 | Entry: $182.50
```

## Project Structure

```
ai-stock-analyzer/
├── src/
│   ├── main.py              # CLI entry point
│   ├── config.py            # Pydantic settings
│   ├── analysis/
│   │   ├── calculator.py    # Technical indicators
│   │   └── analyzer.py      # Multi-agent orchestration
│   ├── fetcher/
│   │   └── twelve_data.py   # Market data API
│   ├── llm/
│   │   ├── client.py        # Unified LLM client with retry
│   │   └── prompts/
│   │       └── analysis.txt # Externalized prompts
│   └── sheets/
│       └── writer.py        # Google Sheets output
├── tests/
│   ├── test_calculator.py   # Indicator tests
│   └── test_config.py       # Config tests
├── config.json.example
├── requirements.txt
├── Makefile
└── pyproject.toml
```

## Configuration

Edit `config.json` to customize:

```json
{
  "api_keys": {
    "anthropic": "sk-ant-...",
    "openai": "sk-...",
    "google": "...",
    "xai": "...",
    "twelve_data": "..."
  },
  "claude_settings": {
    "enabled": true,
    "model": "sonnet-4.5",
    "use_extended_thinking": false
  },
  "gemini_settings": {
    "enabled": true,
    "model": "gemini-2.5-pro",
    "use_thinking": false
  },
  "global_settings": {
    "use_concurrent": true,
    "max_workers": 3
  }
}
```

## Technical Indicators

| Category | Indicators |
|----------|-----------|
| **Trend** | SMA (20/50/200), EMA, MACD |
| **Momentum** | RSI, Stochastic %K/%D, MACD Histogram |
| **Volatility** | ATR, Bollinger Bands |
| **Levels** | Support/Resistance (24 auto-detected) |

## Technical Notes

### Cost Optimization
Traditional approach requires 7+ API calls per stock:
- Quote, SMA20, SMA50, SMA200, RSI, MACD, ATR...

This system uses **1 API call** with all calculations done client-side:
- **Before**: $0.07+ per stock
- **After**: $0.01 per stock
- **Savings**: ~90%

### Multi-Agent Consensus
Running 3-4 models in parallel reduces:
- AI hallucination through cross-validation
- Single-model bias
- Confidence in conflicting signals

Claude acts as arbitrator when models disagree significantly (variance > 2.5).

### Retry Logic
All LLM calls use tenacity with:
- 3 retry attempts
- Exponential backoff (2-30 seconds)
- Automatic recovery from rate limits

## Development

```bash
# Run tests
make test

# Format code
make format

# Lint check
make lint

# Type check
make typecheck
```

## License

MIT License - see [LICENSE](LICENSE)

## Author

**Alex Bespalov**  
🐙 [GitHub](https://github.com/alexbesp18)

---

⭐ Star this repo if you find it useful!
