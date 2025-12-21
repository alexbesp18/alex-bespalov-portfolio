# Reversal Tracker

Mid-term reversal detection system that identifies potential trend reversals using multiple technical indicators and divergence analysis.

## Key Features

- **Multi-Indicator Scoring** — RSI, Stochastic, MACD, volume, divergence
- **Upside Reversal Detection** — Identifies oversold stocks showing reversal signals
- **Divergence Analysis** — Bullish/bearish divergence between price and momentum
- **Configurable Watchlists** — YAML-based ticker configuration
- **Daily Email Digest** — Ranked reversal candidates

## Scoring Components

| Component | Weight | What It Measures |
|-----------|--------|------------------|
| RSI | 20% | Oversold condition (< 30 = max points) |
| Stochastic K | 15% | Short-term oversold |
| Stochastic Crossover | 15% | K crossing above D |
| MACD Flip | 20% | Histogram turning positive |
| Volume Surge | 10% | Above-average volume |
| Divergence | 20% | Price low vs indicator low |

## Usage

```bash
# Dry run (no email)
python reversals.py --dry-run

# Full run with email
python reversals.py

# Send reminder of yesterday's signals
python reversals.py --reminder

# Archive an actioned signal
python reversals.py --archive NVDA
```

## Triggers

| Trigger | Condition |
|---------|-----------|
| `UPSIDE_REVERSAL` | Score ≥ 7.0, multiple indicators aligned |
| `MACD_FLIP` | Histogram crosses zero from below |
| `BULLISH_DIVERGENCE` | Price makes lower low, RSI makes higher low |

## Architecture

```
009-reversals/
├── reversals.py         # Main entry point
├── config/
│   ├── watchlist.yaml   # Ticker list
│   └── thresholds.yaml  # Score thresholds
├── src/
│   ├── fetcher.py       # Uses shared CacheAwareFetcher
│   ├── calculator.py    # Extends shared_core.TechnicalCalculator
│   ├── reversal_scorer.py   # Upside score calculation
│   └── triggers.py      # Trigger evaluation
└── tests/               # 8 unit tests
```

## Tech Stack

- Python 3.10+
- shared_core.CacheAwareFetcher
- shared_core.TechnicalCalculator
- pandas, numpy
- SendGrid (notifications)

## Running Tests

```bash
PYTHONPATH=../000-shared-core/src pytest tests/ -v
```

