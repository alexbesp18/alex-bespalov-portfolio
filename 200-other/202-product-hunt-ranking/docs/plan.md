# Project Plan

## What We're Building (One Sentence)
An automated pipeline that scrapes Product Hunt's weekly top 10 products, enriches them with Grok AI categorization, and stores results in Supabase for trend analysis.

## Short-Term Goals (This Week/Sprint)
1. [x] Weekly scraping operational via GitHub Actions
2. [x] Historical backfill capability (last 10 weeks)
3. [x] CI/CD pipeline with linting, type checking, and tests
4. [x] Migrate from Google Sheets to Supabase
5. [x] Add Grok AI enrichment (category, scores, insights)
6. [ ] Monitor automated runs for stability

## Mid-Term Goals (This Month)
1. [x] Add failure notifications (Slack/email on workflow failure)
2. [ ] Build query interface for Supabase data
3. [x] Add weekly digest email with AI insights

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

## Current Implementation Status
- **Done**: Core scraping, Supabase integration, Grok AI enrichment, backfill, CI/CD, tests
- **In Progress**: Monitoring initial automated runs
- **Blocked**: None

## Dependencies and Requirements

### External Services
| Service | Purpose | Auth |
|---------|---------|------|
| Product Hunt | HTML source | None (public) |
| Grok AI (xAI) | Product categorization | `GROK_API_KEY` |
| Supabase | Data storage | `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` |
| GitHub Actions | Orchestration | Built-in |

### Internal
- Python 3.10+
- BeautifulSoup4, supabase, pydantic, tenacity, requests

## Data Flow
```
Product Hunt HTML
        ↓
   fetch_html() [tenacity retry]
        ↓
   parse_products() [BeautifulSoup]
        ↓
   List[Product]
        ↓
   PHGrokAnalyzer.enrich_products_batch() [optional]
        ↓
   List[EnrichedProduct]
        ↓
   PHSupabaseClient.save_products()
        ↓
   product_hunt.products table
```
