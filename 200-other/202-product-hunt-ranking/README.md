# Product Hunt Ranking Scraper

[![Weekly Scraper](https://github.com/alexbesp18/alex-bespalov-portfolio/actions/workflows/202_ph_ranking_weekly.yml/badge.svg)](https://github.com/alexbesp18/alex-bespalov-portfolio/actions/workflows/202_ph_ranking_weekly.yml)
[![CI](https://github.com/alexbesp18/alex-bespalov-portfolio/actions/workflows/202_ph_ranking_ci.yml/badge.svg)](https://github.com/alexbesp18/alex-bespalov-portfolio/actions/workflows/202_ph_ranking_ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Automated pipeline that scrapes Product Hunt's weekly top 10 products, enriches them with Grok AI categorization, and stores results in Supabase.

## Key Features

- **Automated Weekly Scraping**: Scrapes Product Hunt's weekly leaderboard (Sundays 12 PM UTC)
- **AI Enrichment**: Grok AI categorizes products (category, scores, insights)
- **Supabase Storage**: Structured data with SQL queries and upsert strategy
- **Weekly Digest Email**: Sends formatted digest with insights via Resend
- **Historical Backfill**: One-time script to fetch past weeks

## Architecture

```
Product Hunt HTML
        ↓
   fetch_html() [tenacity retry]
        ↓
   parse_products() [BeautifulSoup]
        ↓
   PHGrokAnalyzer.enrich_products_batch() [optional]
        ↓
   PHSupabaseClient.save_products()
        ↓
   send_weekly_digest() [optional]
```

## Quick Start

### Prerequisites
- Python 3.10+
- Supabase project
- Grok API key (optional, for AI enrichment)
- Resend API key (optional, for email digest)

### Installation
```bash
git clone https://github.com/alexbesp18/alex-bespalov-portfolio.git
cd alex-bespalov-portfolio/200-other/202-product-hunt-ranking
pip install -r requirements.txt
```

### Environment Variables
```bash
# Required
export SUPABASE_URL='https://your-project.supabase.co'
export SUPABASE_SERVICE_KEY='your-service-role-key'

# Optional - AI enrichment
export GROK_API_KEY='your-xai-key'

# Optional - Email digest
export RESEND_API_KEY='your-resend-key'
export EMAIL_FROM='digest@yourdomain.com'
export EMAIL_TO='you@example.com'
```

### Usage
```bash
# Run weekly scraper (current week)
python -m src.main

# Run historical backfill (last 10 weeks)
python -m backfill.main
```

## Project Structure
```
202-product-hunt-ranking/
├── src/
│   ├── main.py              # Pipeline orchestration
│   ├── config.py            # Settings (pydantic-settings)
│   ├── models.py            # Product model
│   ├── utils/parsing.py     # HTML scraping
│   ├── analysis/            # Grok AI enrichment
│   ├── db/                  # Supabase integration
│   └── notifications/       # Email digest
├── backfill/                # Historical data fetcher
├── tests/                   # Test suite
└── docs/                    # Architecture & plans
```

## Supabase Schema

Schema: `product_hunt`

| Table | Primary Key | Purpose |
|-------|-------------|---------|
| `products` | `(week_date, rank)` | Weekly rankings with AI enrichment |
| `weekly_insights` | `week_date` | AI-generated trends and analysis |
| `category_trends` | `(week_date, category)` | Aggregated stats by category |

## Technical Notes

- **Retry Logic**: `tenacity` with 3 attempts, exponential backoff
- **Upsert Strategy**: Safe re-runs via `on_conflict="week_date,rank"`
- **Graceful Fallback**: Saves raw products if Grok unavailable
- **Rate Limiting**: 3-second delay between requests during backfill
- **Upvote Extraction**: Takes `max()` of numbers (distinguishes from comments)

## License

MIT
