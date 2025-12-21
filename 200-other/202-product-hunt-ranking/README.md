# Product Hunt Ranking Scraper

A robust Python tool for tracking and archiving Product Hunt's weekly top products to Google Sheets.

## Key Features
- **Automated Weekly Scraping**: Scrapes Product Hunt's weekly leaderboard for top 10 products
- **Rich Data Extraction**: Captures product name, description, upvotes, and URL
- **Google Sheets Integration**: Automatically appends results to a configured sheet
- **Historical Backfill**: One-time script to fetch past weeks of data
- **GitHub Actions**: Scheduled Sunday runs + manual triggers
- **Configurable**: Fully controlled via environment variables

## Output Format
| Date | Rank | Name | Description | Upvotes | URL |
|------|------|------|-------------|---------|-----|
| 2025-12-13 | 1 | Incredible | Deep Work AI Agents - powered by Agent MAX | 626 | https://... |
| 2025-12-13 | 2 | ClickUp 4.0 | All your work: tasks, docs, chat, and AI with 100% context | 608 | https://... |

## Project Structure
```
product_hunt_ranking/
├── src/
│   ├── main.py           # Entry point & Google Sheets integration
│   ├── config.py         # Settings (env vars)
│   ├── models.py         # Pydantic data models
│   └── utils/
│       └── parsing.py    # HTML scraping logic
├── backfill/
│   ├── main.py           # Historical data fetcher
│   └── config/
│       └── settings.py   # WEEKS_BACK = 10
├── tests/
├── .github/workflows/
│   ├── weekly_ph_rankings.yml  # Scheduled Sunday runs
│   ├── backfill.yml            # One-time historical fetch
│   └── ci.yml                  # Linting & tests
└── requirements.txt
```

## Quick Start

### Prerequisites
- Python 3.10+
- Google Service Account JSON key

### Installation
```bash
git clone https://github.com/alexbesp18/alex-bespalov-portfolio.git
cd alex-bespalov-portfolio/product_hunt_ranking
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Google Sheet ID and credentials path
```

### Usage
```bash
# Run weekly scraper
python -m src.main

# Run historical backfill (fetches last 10 weeks)
python -m backfill.main
```

### GitHub Actions
- **Weekly Product Hunt Rankings**: Runs every Sunday at 12 PM UTC
- **One-Time Historical Backfill**: Manual trigger for historical data

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `PH_GDRIVE_API_KEY_JSON` | Service Account JSON content or file path | (Required) |
| `PH_GSHEET_ID` | Google Spreadsheet ID (from URL) | (Required) |
| `GSHEET_NAME` | Spreadsheet name (fallback) | "Product Hunt Rankings" |
| `GSHEET_TAB` | Tab name to write to | "Weekly Top 10" |
| `LOG_LEVEL` | Logging verbosity | "INFO" |

## Technical Notes
- **Resiliency**: Uses `tenacity` for exponential backoff on network failures
- **Type Safety**: Fully typed with Pydantic models
- **Rate Limiting**: 2-second delay between requests during backfill
- **Upvote Extraction**: Takes the maximum number found (distinguishes from comment counts)

## License
MIT
