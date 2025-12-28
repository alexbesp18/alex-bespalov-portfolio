# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Structure

```
000-099-investing/     Python investment tools (shared library: 000)
100-199-bitcoin-mining/ React calculators (shared library: 100)
200-other/             Python automation tools
```

## Commands

### Python with Makefile (003, 004, 006, 202)

```bash
make install && make test && make lint
make format          # Auto-fix with ruff
```

### Python without Makefile (007, 008, 009, 010)

```bash
pip install -r requirements.txt
python main.py --dry-run           # 008-alerts
python reversals.py --dry-run      # 009-reversals
python oversold.py --all           # 010-oversold
python run_all.py                  # 007-ticker-analysis (cache producer)
pytest tests/ -v
```

### 000-shared-core (Python library)

```bash
cd 000-099-investing/000-shared-core
pip install -e ".[dev]"
PYTHONPATH=src pytest tests/ --ignore=tests/test_live_api.py -v
ruff check src/ --select=E,F,W,I
mypy src/shared_core --ignore-missing-imports
```

### React Apps (101-105)

```bash
npm install && npm start           # Dev server on :3000
npm run build && npm test
```

### 100-shared-core (JS library)

```bash
cd 100-199-bitcoin-mining/100-shared-core
npm run build                      # Babel transpile
npm test && npm run verify
```

## Architecture

### Data Pipeline (Investment Tools)

```
Twelve Data API
      ↓
007-ticker-analysis ──→ Cache (parquet)
      ↓
┌─────┴─────┬─────────────┐
↓           ↓             ↓
008-alerts  009-reversals 010-oversold
            ↓
    006-ai-stock-analyzer (4-LLM ensemble)
```

Cache enables <2s execution for consumer projects.

### 000-shared-core Modules

| Module | Purpose |
|--------|---------|
| `market_data/` | Twelve Data client, `TechnicalCalculator` (15+ indicators), `CacheAwareFetcher` |
| `llm/` | Multi-provider client (Claude, GPT, Grok, Gemini) with tenacity retry |
| `scoring/` | Multi-horizon analysis, weighted scoring, conviction models |
| `triggers/` | Alert conditions, evaluation engine, cooldown management |
| `backtest/` | Signal backtesting engine with forward-looking validation |
| `divergence/` | RSI/MACD divergence detection via swing points |
| `integrations/` | Google Sheets (`gspread`), Supabase |
| `notifications/` | Resend email client, HTML formatters |
| `state/` | Alert state management, archiving, digests |

### 100-shared-core Modules

| Module | Purpose |
|--------|---------|
| `calculations/` | Mining profitability, projections, taxes, risk, options |
| `constants/` | Bitcoin halvings, electricity rates, MACRS depreciation |
| `data/` | Miner database (31 models), power database, scenarios |
| `formatters/` | Currency, numbers, dates |
| `storage/` | localStorage with compression and migration |
| `validation/` | Input validation for numbers and miner specs |
| `hooks/` | `useLocalStorage`, `useMiningCalculations`, `useScenarios` |
| `export/` | CSV, JSON, Excel export utilities |

## Code Standards

| Aspect | Python | JavaScript |
|--------|--------|------------|
| Linter | ruff (E,F,W,I rules) | ESLint via react-scripts |
| Types | mypy (gradual typing) | — |
| Tests | pytest, 50% min coverage | Jest, 70-80% thresholds |
| Format | ruff format (100 char) | Prettier (100 char) |
| Version | 3.10+ | React 19, Node 18+ |

## Conventions

- Shared libraries are project #X0 (000-shared-core, 100-shared-core)
- Files should not exceed 200 lines—break into helpers
- Services should have `if __name__ == "__main__":` for standalone testing
- If a fix fails twice, revert and rethink the approach

## CI/CD Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `000_shared-core-ci.yml` | Push/PR | Lint, typecheck, test (Python 3.10-3.12 matrix) |
| `000_backtest.yml` | Manual | Run backtests on reversal/oversold signals |
| `000_cache-refresh.yml` | Scheduled | Refresh Twelve Data cache |
| `202_ph_ranking_*.yml` | Weekly | Product Hunt scraper |
| `204_podcast_intel.yml` | Scheduled | Podcast analysis pipeline |
