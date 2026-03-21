# Project Plan

## What We're Building (One Sentence)
Automated system to maximize American Airlines loyalty point earnings through intelligent stacking of Portal + SimplyMiles + Credit Card earning channels, targeting 15+ LP/$ yield on everyday purchases.

## Short-Term Goals (This Week/Sprint)
1. [x] Set up cron scheduling for automated scraper runs - **DONE (VPS)**
2. [x] Add push notifications (Pushover/ntfy) for immediate alerts - **DONE**
3. [x] Migrate from SQLite to Supabase - **DONE (2026-01-03)**
4. [x] Add missing database indexes for query optimization - **DONE**
5. [x] Session stability fix (keep-alive, validation, quick re-auth) - **DONE**
6. [ ] Monitor production alerts, tune thresholds

## Mid-Term Goals (This Month)
1. [ ] Build FastAPI backend for data access
2. [ ] Create HTMX dashboard for visual deal browsing
3. [ ] Implement rate change tracking for portal merchants
4. [ ] Add session auto-refresh detection for SimplyMiles

## Long-Term Vision (3-6 Months)
1. [ ] Reach Platinum status (75,000 LPs from current 40,000)
2. [x] Deploy to VPS for always-on operation - **DONE (REDACTED_VPS_IP)**
3. [ ] Build browser extension for live deal info while shopping
4. [ ] Consider multi-program support (United, Delta, etc.)

## Non-Goals (Explicitly Out of Scope)
- **Automated purchasing** - Too risky, potential ToS violation
- **Multi-user SaaS** - Personal tool, keeping it simple
- **Native mobile app** - Web/email sufficient for now
- **ML-based predictions** - Current matrix approach works well enough
- **Social features** - Solo project, no community needs

## Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Blended yield on purchases | >15 LP/$ | TBD (tracking starts with production) |
| Hotel booking yield | >20 LP/$ | 10.13 LP/$ average |
| Time to Platinum | <6 months | In progress |
| Alert false positive rate | <5% | TBD |
| System uptime | >99% | Operational on VPS |

## Current Implementation Status

### Complete
- SimplyMiles scraper (API + Playwright fallback)
- Portal scraper (Cartera API, ~1,300 merchants)
- Hotels scraper (8 cities, REST API)
- Stack detector (fuzzy matching at 85%)
- Scoring engine with modifiers
- Budget optimizer (greedy allocation)
- Hotel yield matrix (1,176 combinations explored)
- Email alerts (immediate + daily digest)
- Health monitoring system
- Test suite (154 tests passing)
- **Supabase migration (cloud PostgreSQL)**

### In Progress
- Monitoring production alerts

### Blocked
- Nothing currently blocked

### Recently Completed (2026-01-03)
- Supabase migration (SQLite -> cloud PostgreSQL)
- Fixed Supabase delete patterns (gte('id', 0) with verification)
- Fixed timezone handling in get_latest_scrape_time()
- Fixed optional parameter in get_city_star_tier_average()
- Added retry decorators to staleness methods
- Full A-Z pipeline test on VPS with Supabase

## Dependencies and Requirements

### External Services
- **Supabase** - Cloud PostgreSQL database (primary)
- **Resend API** - Email delivery (API key required)
- **SimplyMiles** - Requires AA credentials for session
- **Cartera API** - Public, no auth needed
- **AAdvantage Hotels** - Public API

### Python Dependencies
- playwright (browser automation)
- httpx (async HTTP)
- rapidfuzz (fuzzy matching)
- resend (email)
- supabase (database client)
- pytest (testing)

### Environment
- Python 3.13+
- macOS/Linux (Playwright support)
- Supabase project with service_role key

## Phase Timeline

```
Phase 1: Foundation     COMPLETE (2024-12)
Phase 2: Intelligence   COMPLETE (2024-12-28)
Phase 3: Alerts         COMPLETE (2024-12-29)
Phase 4: Production     COMPLETE (2026-01-01) - VPS deployed
Phase 5: Supabase       COMPLETE (2026-01-03) - Cloud database
Phase 6: Dashboard      PLANNED (future)
```

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Website structure changes | Scrapers break | CSS selector discovery workflow in `docs/DISCOVERY_INSTRUCTIONS.md` |
| API rate limiting | Blocked requests | Random delays (2-5s), respectful scraping |
| SimplyMiles session expires | Missing offers | Email alert on expiration, manual re-auth workflow |
| Data staleness | Bad recommendations | Staleness thresholds (6h/12h/24h), health monitoring |
| Over-alerting | Alert fatigue | 24h cooldown, 20% improvement threshold |
| Supabase outage | No data access | Service has 99.9% SLA, local SQLite fallback available |

---

*This file is the single source of truth for project goals. Used by `/continuelikealex` as its "north star".*

*Last updated: 2026-01-03*
