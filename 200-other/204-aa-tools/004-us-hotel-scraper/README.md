# US Hotel Scraper

Scrapes AA Advantage Hotels across ~380 US Metropolitan Statistical Areas and finds the best miles-per-dollar deals.

## Features

- **US-Wide Coverage**: Scrapes hotels from top 100 US MSAs (expandable to 380+)
- **Async Scraping**: 10 parallel city searches for fast data collection
- **Quality Scoring**: Star-adjusted yield scoring (4-5 star hotels get bonuses)
- **Web Dashboard**: Browse and filter deals with FastAPI + HTMX
- **CSV Export**: Export top deals for analysis

## Quick Start

```bash
# 1. Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Discover cities (one-time)
python scripts/discover_cities.py --limit 50

# 3. Run scraper
python scripts/run_scraper.py

# 4. Start web dashboard
python -m web.app
# Open http://localhost:8000
```

## Commands

```bash
# City Discovery
python scripts/discover_cities.py              # Discover all MSAs
python scripts/discover_cities.py --limit 50   # Top 50 only
python scripts/discover_cities.py --status     # Show discovery status

# Scraper
python scripts/run_scraper.py                  # Full scrape
python scripts/run_scraper.py --limit 10       # Quick test (10 cities)
python scripts/run_scraper.py --stats          # Show statistics only

# Export
python scripts/export_csv.py                   # Export all deals
python scripts/export_csv.py --min-yield 15    # High-yield only

# Web Dashboard
python -m web.app                              # Start server
uvicorn web.app:app --reload                   # With hot reload
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Web dashboard with top deals |
| `GET /city/{id}` | City-specific deals |
| `GET /api/deals` | JSON API for deals |
| `GET /api/cities` | List of cities |
| `GET /api/stats` | Database statistics |
| `GET /admin/status` | Scraper status page |

## Project Structure

```
us_hotel_scraper/
├── config/
│   └── settings.py          # Configuration
├── core/
│   ├── database.py          # SQLite layer
│   ├── http_client.py       # Async HTTP
│   ├── hotels_api.py        # API wrapper
│   ├── city_discovery.py    # MSA discovery
│   └── scorer.py            # Deal scoring
├── scrapers/
│   └── hotel_scraper.py     # Main scraper
├── web/
│   ├── app.py               # FastAPI app
│   └── templates/           # HTML templates
├── scripts/
│   ├── discover_cities.py   # City discovery
│   ├── run_scraper.py       # Run scraper
│   └── export_csv.py        # CSV export
└── data/
    └── hotels.db            # SQLite database
```

## How It Works

1. **City Discovery**: Queries the places API to get Agoda place IDs for US cities
2. **Hotel Search**: For each city, searches 10 date ranges (30 days ahead)
3. **Scoring**: Applies star-rating multipliers (5-star: +25%, 1-star: -30%)
4. **Storage**: Deduplicates and stores deals in SQLite
5. **Dashboard**: FastAPI serves a filterable web UI

## Performance

| Metric | Value |
|--------|-------|
| Cities | ~100 (default), 380+ available |
| Parallel requests | 10 concurrent |
| Full scrape time | ~30-45 minutes |
| Deals per scrape | ~50,000+ |

## Environment Variables

```bash
# Optional - see .env.example
MAX_CONCURRENT_CITIES=10
DAYS_AHEAD=30
DATABASE_PATH=data/hotels.db
WEB_PORT=8000
```

## Data Source

Hotels data from [aadvantagehotels.com](https://www.aadvantagehotels.com) (Agoda/RocketMiles backend).
