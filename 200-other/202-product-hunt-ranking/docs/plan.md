# Project Plan

## What We're Building (One Sentence)
An automated pipeline that scrapes Product Hunt's weekly top 10 products, enriches them with Grok AI categorization, stores results in Supabase, and sends weekly digest emails with insights for entrepreneurs.

## Short-Term Goals (This Week/Sprint)
1. [x] Weekly scraping operational via GitHub Actions
2. [x] Historical backfill capability (last 10 weeks)
3. [x] CI/CD pipeline with linting, type checking, and tests
4. [x] Migrate from Google Sheets to Supabase
5. [x] Add Grok AI enrichment (category, scores, insights)
6. [x] Weekly digest email with Solo Builder Pick
7. [ ] Monitor automated runs for stability (first few weeks)

## Mid-Term Goals (This Month)
1. [x] Add failure notifications (GitHub Actions workflow failure)
2. [x] Add weekly digest email with AI insights
3. [ ] Build query interface for Supabase data (Streamlit dashboard)
4. [ ] Extract comment count from HTML

## Long-Term Vision (3-6 Months)
1. [ ] Build dashboard for visualizing trends over time
2. [ ] Expand to other Product Hunt leaderboards (daily, monthly)
3. [ ] Add API endpoint for programmatic access to data
4. [ ] Cross-reference with other sources (HN, Reddit)

## Non-Goals (Explicitly Out of Scope)
- Real-time scraping (weekly cadence is sufficient)
- User-facing web application (Supabase is the interface)
- Scraping individual product pages (leaderboard summary only)
- Authentication with Product Hunt API (HTML scraping works)
- Google Sheets integration (migrated to Supabase)

## Success Metrics
- Weekly data collection with 0 missed weeks
- < 2 minute total runtime per execution
- All top 10 products captured with accurate upvote counts
- AI enrichment success rate > 90%
- Zero manual intervention required
- Email digest delivered every Sunday

## Current Implementation Status
- **Done**: Core scraping, Supabase integration, Grok AI enrichment, backfill, CI/CD, tests, email digest, category trends, solo builder pick
- **In Progress**: Monitoring initial automated runs
- **Blocked**: None

## Dependencies and Requirements

### External Services
| Service | Purpose | Auth | Status |
|---------|---------|------|--------|
| Product Hunt | HTML source | None (public) | ✅ Active |
| Grok AI (xAI) | Product categorization | `GROK_API_KEY` | ✅ Active |
| Supabase | Data storage | `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` | ✅ Active |
| Resend | Email delivery | `RESEND_API_KEY` | ✅ Active |
| GitHub Actions | Orchestration | Built-in | ✅ Active |

### Python Dependencies
- Python 3.10+
- beautifulsoup4, supabase, pydantic, tenacity, requests, resend

## Data Flow
```
Product Hunt HTML
        ↓
   fetch_html() [tenacity retry, 3 attempts]
        ↓
   parse_products() [BeautifulSoup, limit=10]
        ↓
   List[Product]
        ↓
   PHGrokAnalyzer.enrich_products_batch() [optional, batch mode]
        ↓
   List[EnrichedProduct]
        ↓
   PHSupabaseClient.save_products() [upsert on week_date,rank]
        ↓
   PHGrokAnalyzer.generate_weekly_insights()
        ↓
   PHSupabaseClient.save_insights()
        ↓
   aggregate_category_trends() [save to category_trends table]
        ↓
   get_solo_builder_pick() [identify best product for solo builders]
        ↓
   send_weekly_digest() [Resend email with HTML template]
```

## Key Supabase Tables
| Table | Purpose | Primary Key |
|-------|---------|-------------|
| `products` | Weekly rankings with AI enrichment | `(week_date, rank)` |
| `weekly_insights` | AI-generated trends and analysis | `week_date` |
| `category_trends` | Aggregated stats by category | `(week_date, category)` |
