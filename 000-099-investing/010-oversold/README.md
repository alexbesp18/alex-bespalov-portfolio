# Oversold Screener

A local CLI tool that ranks stocks by **oversold score** (1-10) across flexible watchlists.

## Features

- **Weighted Scoring**: 6 technical indicators with configurable weights
- **Flexible Watchlists**: Scan single, multiple, or all watchlists
- **Multiple Output Formats**: Table, JSON, CSV
- **Production Quality**: Type hints, Google-style docstrings, 22+ unit tests

## Installation

```bash
# Clone and setup
cd 011_oversold
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your TWELVE_DATA_API_KEY
```

## Usage

```bash
# Single watchlist
python oversold.py --watchlist ai

# Multiple watchlists
python oversold.py --watchlist ai,portfolio

# All watchlists
python oversold.py --all

# Limit results & output format
python oversold.py --all --top 5 --output json
python oversold.py --watchlist ai --output csv
```

## Sample Output

```
════════════════════════════════════════════════════════════════════════
                          TOP 10 MOST OVERSOLD                          
════════════════════════════════════════════════════════════════════════
 Rank │ Ticker │ Score  │  RSI  │ Will%R │ Stoch │  Price   
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1   │  ARM   │  5.7   │ 35.4  │ -87.6  │ 12.4  │$  121.10
  2   │  AVGO  │  4.6   │ 35.2  │ -92.2  │  7.8  │$  341.30
  3   │  INTC  │  3.3   │ 54.0  │ -85.0  │ 15.0  │$   37.31
════════════════════════════════════════════════════════════════════════
```

## Scoring Logic

| Indicator | Weight | Oversold Signal |
|-----------|--------|-----------------|
| RSI | 30% | <30 |
| Williams %R | 20% | <-80 |
| Stochastic %K | 15% | <20 |
| Bollinger Position | 15% | Below lower band |
| SMA200 Distance | 10% | Below 200-day MA |
| Consecutive Red Days | 10% | 3+ down days |

## Project Structure

```
011_oversold/
├── oversold.py              # Main CLI entry point
├── src/
│   ├── __init__.py          # Package exports
│   ├── models.py            # Dataclasses (TickerResult, Watchlist, etc.)
│   ├── oversold_scorer.py   # Weighted scoring logic
│   ├── calculator.py        # Technical indicator calculations
│   └── fetcher.py           # TwelveData API client
├── config/
│   └── watchlists/          # Watchlist JSON files
├── tests/
│   └── test_oversold_scorer.py  # 22 unit tests
├── requirements.txt
└── README.md
```

## Adding Watchlists

Create JSON files in `config/watchlists/`:

```json
{
  "name": "My Watchlist",
  "tickers": ["AAPL", "MSFT", "GOOGL"]
}
```

## Running Tests

```bash
python -m pytest tests/ -v
```

## License

MIT
