# vFinal - Optimized Stock Data Loader

A modular, caching-enabled rewrite of the stock data loader scripts.

## Key Features

- **Daily Caching**: API data cached locally; each ticker's API called at most once per day
- **Simple Logic**: If data for today exists, use cache; otherwise fetch fresh
- **Modular Architecture**: Single source of truth for each component
- **Row Replacement**: Updates existing sheet rows instead of just appending

## Quick Start

```bash
# Navigate to vFinal directory
cd vFinal

# Run all (technicals + transcripts) - RECOMMENDED
python run_all.py --verbose

# Run technicals only
python run_technicals.py --verbose

# Run transcripts only
python run_transcripts.py --verbose
```

## CLI Options

All scripts support these options:

| Option | Short | Description |
|--------|-------|-------------|
| `--verbose` | `-v` | Print detailed progress |
| `--dry-run` | `-n` | Fetch data but don't write to sheets |
| `--limit N` | `-l N` | Process at most N tickers |
| `--batch-size N` | `-b N` | Process N tickers then stop |
| `--clean` | | Overwrite all existing data |
| `--force-refresh` | | Ignore cache, fetch fresh data |
| `--clear-cache` | | Delete cache files older than 7 days |
| `--config PATH` | `-c PATH` | Use custom config file |

## File Structure

```
vFinal/
├── core/                      # Shared modules
│   ├── __init__.py           # Package exports
│   ├── config.py             # Configuration loader
│   ├── data_cache.py         # JSON caching layer
│   ├── technical_calculator.py  # Indicator math
│   ├── twelve_data_client.py # Twelve Data API + cache
│   ├── transcript_client.py  # defeatbeta API + cache
│   ├── grok_analyzer.py      # AI analysis
│   └── sheet_manager.py      # Google Sheets I/O
├── data/                      # Cache directory (auto-created)
│   ├── twelve_data/          # Cached time series
│   └── transcripts/          # Cached transcripts
├── run_all.py                # Combined entry point
├── run_technicals.py         # Technicals only
├── run_transcripts.py        # Transcripts only
├── config.json               # Configuration
└── requirements.txt          # Dependencies
```

## Caching Behavior

Cache files are stored with date stamps:
- `data/twelve_data/AAPL_2025-12-19.json`
- `data/transcripts/AAPL_2025-12-19.json`

**Cache Hit**: If today's file exists, use it (no API call)
**Cache Miss**: Fetch from API, save to cache

## Configuration

Edit `config.json` (same format as parent directory):

```json
{
  "google_sheets": {
    "credentials_file": "google_service_account.json",
    "spreadsheet_name": "Your Sheet Name",
    "main_tab": "Sheet1",
    "tech_data_tab": "Tech_Data",
    "transcripts_tab": "Transcripts"
  },
  "twelve_data": {
    "api_key": "YOUR_API_KEY",
    "rate_limit_sleep": 0.5
  },
  "grok": {
    "api_key": "YOUR_API_KEY",
    "model": "grok-4-1-fast-reasoning"
  }
}
```

## Compared to Original Scripts

| Metric | Original (6 scripts) | vFinal |
|--------|---------------------|--------|
| Total lines | ~5600 | ~1200 |
| Duplicated code | ~4500 lines | 0 |
| API calls (repeat run) | N (per ticker) | 0 (cached) |
| Time (cached run) | Minutes | Seconds |

## Workflow

1. **First run of the day**: Fetches all data, populates cache
2. **Subsequent runs same day**: Uses cache, skips API calls entirely
3. **Next day**: No cache for today, fetches fresh data for all tickers
4. **Force refresh**: Use `--force-refresh` to bypass cache any time

