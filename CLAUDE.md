# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a portfolio of 21+ production-ready projects across three categories:
- **000-099:** Investment & Portfolio Tools (Python-based)
- **100-199:** Bitcoin Mining Calculators (React/JavaScript)
- **200-299:** AI & Automation Tools (Python)

## Common Commands

### Python Projects (000-099, 200-299)

All Python projects use consistent Makefile patterns:

```bash
make install      # pip install -r requirements.txt
make test         # pytest tests/ -v
make test-cov     # pytest with coverage (50% minimum required)
make lint         # ruff check src/ tests/
make format       # ruff format + ruff fix
make typecheck    # mypy src/ --ignore-missing-imports
make clean        # Remove __pycache__, .pytest_cache
```

To run a single test:
```bash
pytest tests/test_file.py::test_function -v
```

### React Projects (100-199)

```bash
npm install       # Install dependencies
npm start         # Development server (localhost:3000)
npm run build     # Production build
npm test          # Run Jest tests
```

### Shared Libraries

**Python (000-shared-core):**
```bash
cd 000-099-investing/000-shared-core
pip install -e ".[dev]"
PYTHONPATH=src pytest tests/
```

**JavaScript (100-shared-core):**
```bash
cd 100-199-bitcoin-mining/100-shared-core
npm run build     # babel src --out-dir dist
npm run verify    # Verify exports
```

## Architecture

### Data Flow (Investment Tools)

```
Twelve Data API → 007-ticker-analysis (cache producer)
                        ↓
                  Cache (parquet + JSON)
                        ↓
        ┌───────────────┼───────────────┐
        ↓               ↓               ↓
   008-alerts     009-reversals    010-oversold
        ↓
   006-ai-stock-analyzer (4-LLM ensemble)
```

The `007-ticker-analysis` project populates the cache. Consumer projects (008, 009, 010, 006) read from cache for instant execution (<2 seconds).

### Shared Libraries

**000-shared-core (Python):** Central library with:
- `market_data/` - Twelve Data API clients, caching, 15+ technical indicators
- `llm/` - Multi-provider client (Claude, GPT, Grok, Gemini) with retry logic
- `integrations/` - Google Sheets, Supabase connectors
- `backtest/` - Signal backtesting engine
- `divergence/` - RSI/MACD divergence detection

**100-shared-core (JavaScript):** NPM package with:
- `calculations/` - Mining profitability, projections, taxes, risk
- `constants/` - Bitcoin halvings, electricity rates, MACRS depreciation
- `data/` - Miner database (31 models)
- `formatters/` - Currency, numbers, dates
- `hooks/` - React state management hooks

## Code Quality Standards

### Python
- **Linter:** ruff (E, F, W rules, line length 100)
- **Types:** mypy with strict optional checking
- **Tests:** pytest with 50% coverage minimum (core modules 85%+)
- **Python version:** 3.10+

### JavaScript
- **Tests:** Jest with 80% coverage threshold
- **Format:** Prettier (printWidth: 100)
- **Build:** react-scripts / Babel

## Project Conventions

- Projects are numbered: 000-010 (investing), 100-106 (mining), 200-204 (other)
- Shared libraries are always #X0 (000, 100)
- Modular service-based architecture—break logic into separate files
- No file should exceed 200 lines; break into helper functions
- Each service should have a `if __name__ == "__main__":` block for independent testing
- If a solution fails twice, revert to last clean commit and rethink the approach

## Key Configuration Files

- `pyproject.toml` - Python project metadata, tool configs (ruff, mypy, pytest)
- `package.json` - Node.js dependencies and scripts
- `config/*.json` - Optional ticker/watchlist configurations per project

## CI/CD Workflows

Located in `.github/workflows/`:
- `000_shared-core-ci.yml` - Lint, typecheck, test across Python 3.10-3.12
- `000_backtest.yml` - Run reversal/oversold signal backtests (manual)
- `000_cache-refresh.yml` - Refresh ticker cache via Twelve Data API
- `202_ph_ranking_*.yml` - Product Hunt ranking scraper (weekly)
- `204_podcast_intel.yml` - Automated podcast analysis pipeline
