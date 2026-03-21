# Project Status

## Current Phase
- [x] Documentation (`/doclikealex`)
- [x] Implementation (`/continuelikealex`)
- [x] Cleanup (`/cleanuplikealex`)
- [x] Modularization (`/modularizelikealex`)
- [x] Deployment Planning (`/deploylikealex`)
- [x] VPS Deployment (REDACTED_VPS_IP) - LIVE
- [x] Session Stability Fix - IMPLEMENTED
- [x] QA Audit (`/qalikealex`) - PASS
- [x] Supabase Migration - COMPLETE (2026-01-03)

## Last Updated
2026-01-04 12:30 CST (GitHub repo created, httpx logging fix, schema fixes)

## GitHub Repository
**Private:** https://github.com/alexbesp18/aa-scraper

## Quick Links
- [Plan & Goals](./docs/PLAN.md)
- [Architecture](./docs/ARCHITECTURE.md)
- [Current Checkpoint](./docs/CHECKPOINT.md)
- [Init Guide](./docs/INIT_CONSIDERATIONS.md)
- [Future Roadmap](./docs/future_roadmap.md)
- [QA Report](./qa_report.md)

## Current Priority
**System fully operational on Supabase** - Cloud database, VPS deployed, full pipeline tested.

### Database Migration Complete
- **From:** SQLite (local file)
- **To:** Supabase (cloud PostgreSQL)
- **Benefits:** Web dashboard, accessible from anywhere, automatic backups

### Latest Pipeline Results (2026-01-04):
- SimplyMiles: 128 offers
- Portal: 1,318 merchants
- Hotels: 3,553 deals (8 cities)
- Stacked: 37 opportunities (3 above immediate threshold)
- Alerts: 24 deals sent in batch email

### When Session Expires (HTTP 419):
1. On Mac: `python scripts/setup_auth.py` -> log in -> Enter
2. Sync: `rsync -avz simplymiles_cookies.json root@REDACTED_VPS_IP:~/aa_scraper/`
3. Verify: `ssh root@REDACTED_VPS_IP "cd aa_scraper && source venv/bin/activate && python scrapers/simplymiles_api.py --test"`

## System Status

| Component | Status | Health |
|-----------|--------|--------|
| Supabase Database | Operational | Cloud PostgreSQL |
| SimplyMiles API Scraper | Operational | Session expires 7-30 days |
| Portal Scraper | Operational | Public API, no auth needed |
| Hotels Scraper | Operational | 8 cities, matrix-aware |
| Stack Detector | Operational | 85% fuzzy matching |
| Alert System | Operational | Resend email API |
| Hotel Yield Matrix | Complete | 1,176 combinations |
| Test Suite | Passing | 154 tests |

## Key Metrics (Supabase)

| Metric | Value |
|--------|-------|
| SimpleMiles offers | 128 |
| Portal rates | 1,318 |
| Stacked opportunities | 37 |
| Hotel deals | 3,553 |
| Hotel yield baselines | Active |

## Supabase Tables

| Table | Purpose |
|-------|---------|
| simplymiles_offers | Card-linked offers |
| portal_rates | Shopping portal rates |
| hotel_deals | Current hotel availability |
| stacked_opportunities | Matched SM + Portal combos |
| alert_history | Sent alerts (deduplication) |
| scraper_health | System monitoring |
| hotel_yield_matrix | 1,176 yield predictions |
| hotel_yield_history | Historical tracking |
| discovery_progress | Session resume |
| merchant_history | Rate tracking |
| deal_discoveries | First-seen tracking |
| hotel_yield_baselines | Per-hotel averages |

## Cron Schedule (VPS)

| Job | Frequency | Status |
|-----|-----------|--------|
| SimplyMiles | Every 10 min | Active |
| Portal | Every 4 hours | Active |
| Hotels | Every 6 hours | Active |
| Stack detection | Every 2h +15m | Active |
| Alert check | Every 2h +20m | Active |
| Daily digest | 8am CT | Active |
| Matrix verification | Sunday 3am | Active |

## LP Progress

| Status | LPs | Gap |
|--------|-----|-----|
| Current (Gold) | 40,000 | - |
| Target (Platinum) | 75,000 | 35,000 |

**Monthly budget:** $500 | **Target yield:** 15+ LP/$
