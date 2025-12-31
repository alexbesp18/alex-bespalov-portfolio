# Project Plan

## What We're Building (One Sentence)
An automated pipeline that scrapes Product Hunt's weekly top 10 products and archives them to Google Sheets for trend analysis.

## Short-Term Goals (This Week/Sprint)
1. [x] Weekly scraping operational via GitHub Actions
2. [x] Historical backfill capability (last 10 weeks)
3. [x] CI/CD pipeline with linting, type checking, and tests
4. [ ] Monitor first few automated runs for stability

## Mid-Term Goals (This Month)
1. [ ] Add Slack/email notifications on successful scrape
2. [ ] Implement error alerting for failed runs
3. [ ] Add more data points (comments count, maker info)

## Long-Term Vision (3-6 Months)
1. [ ] Build dashboard for visualizing trends over time
2. [ ] Expand to other Product Hunt leaderboards (daily, monthly)
3. [ ] Add API endpoint for programmatic access to data

## Non-Goals (Explicitly Out of Scope)
- Real-time scraping (weekly cadence is sufficient)
- User-facing web application (Google Sheets is the interface)
- Scraping individual product pages (leaderboard summary only)
- Authentication with Product Hunt API (HTML scraping works)

## Success Metrics
- Weekly data collection with 0 missed weeks
- < 5 minute total runtime per execution
- All top 10 products captured with accurate upvote counts
- Zero manual intervention required

## Current Implementation Status
- **Done**: Core scraping, Google Sheets integration, backfill, CI/CD, tests
- **In Progress**: Monitoring initial automated runs
- **Blocked**: None

## Dependencies and Requirements
### External
- Product Hunt website structure (HTML parsing dependent)
- Google Sheets API (service account required)
- GitHub Actions (for scheduled runs)

### Internal
- Python 3.10+
- BeautifulSoup4, gspread, pydantic, tenacity
