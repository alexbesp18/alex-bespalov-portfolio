# Trading Alerts

Automated daily scanner for 80+ AI infrastructure and tech tickers with configurable buy/sell triggers based on technical indicators.

## Key Features

- **Daily Automated Scans** — GitHub Actions cron job runs after market close
- **Configurable Triggers** — Score-based, price-cross-MA, RSI extremes, volume spikes
- **Portfolio vs Watchlist** — Different alert types for owned positions vs watchlist
- **Cooldown System** — Prevents alert fatigue with configurable suppression periods
- **Email Notifications** — Resend integration with actionable links

## Architecture

```
008-alerts/
├── main.py              # Orchestrator
├── config/
│   ├── portfolio.json   # Current holdings
│   ├── watchlist.json   # Watch targets
│   └── actioned.json    # Suppressed alerts
├── src/
│   ├── fetch_prices.py  # Uses shared CacheAwareFetcher
│   ├── calculator.py    # Technical indicators (extends shared_core)
│   ├── compute_flags.py # Bullish score (0-10)
│   ├── evaluate_triggers.py  # Trigger logic
│   └── notifier.py      # Resend email
└── tests/               # 13 unit tests
```

## Triggers

| Trigger | Condition | Signal |
|---------|-----------|--------|
| `BUY_PULLBACK` | Score ≥ 8, RSI < 50, in uptrend | Enter on dip |
| `BUY_MORE_PULLBACK` | Owned, Score ≥ 8, RSI < 55 | Add to winner |
| `SELL_WARNING` | Score < 5, below SMA20 | Early exit signal |
| `MOMENTUM_BUY` | Score ≥ 9, volume spike | Strong momentum |

## Usage

```bash
# Dry run (no email sent)
python main.py --dry-run

# Full run with email
python main.py

# Suppress an alert for 30 days
python main.py --archive NVDA:BUY_PULLBACK
```

## Sample Output

```
[ALERTS] 3 BUY, 1 SELL — Dec 20

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 BUY SIGNALS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

▲ BUY MORE PULLBACK
ANET — Add to winner on healthy pullback
RSI: 54.8, Score: 9.0, Close: $131.12
[ACTIONED: I bought]
```

## Tech Stack

- Python 3.10+
- shared_core.CacheAwareFetcher (cache-first data fetching)
- Resend API (email)
- GitHub Actions (scheduling)
- tenacity (retry logic)

## Running Tests

```bash
PYTHONPATH=../000-shared-core/src pytest tests/ -v
```

