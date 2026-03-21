# AA Points Arbitrage Monitor - Project Checkpoint

## Quick Context for Claude Code

**Project:** Automated system to monitor American Airlines loyalty point earning opportunities and alert when exceptional deals arise.

**Goal:** Help Alex close a 35,000 LP gap (Gold 40K → Platinum 75K) with minimal dollar commitment.

**Strategy:** Stack multiple earning channels on purchases:
```
Portal (X mi/$) + SimplyMiles (bonus) + Credit Card (1 mi/$) = Combined Yield
Example: $5 Kindle → 10 + 135 + 5 = 150 LPs = 30 LP/$
```

---

## Current Status

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 0: Discovery | ⏳ PENDING | Need to inspect actual site HTML/APIs |
| Phase 1: Foundation | ✅ Complete | Settings, database, structure |
| Phase 2: Core Utils | ✅ Complete | Normalizer, scorer, tests |
| Phase 3: SimplyMiles | ✅ Complete | Scraper ready (needs selectors) |
| Phase 4: Portal | ✅ Complete | Scraper ready (needs selectors) |
| Phase 5: Stack Detection | ✅ Complete | Matching and scoring |
| Phase 6: Alerts | ✅ Complete | Resend integration |
| Phase 7: Hotels | ✅ Complete | Scraper ready (needs API) |
| Phase 8: Orchestration | ✅ Complete | run_all, send_digest, tests |

**All 80 tests passing.**

---

## Project Structure

```
aa_scraper/
├── config/
│   ├── settings.py          # Thresholds, API config (AlertThresholds, ScraperConfig, etc.)
│   └── cities.py             # 8 priority cities for hotels
├── core/
│   ├── database.py           # SQLite with staleness detection
│   ├── normalizer.py         # rapidfuzz matching (85% threshold)
│   ├── scorer.py             # Yield calculation + deal scoring
│   └── stack_detector.py     # Match SimplyMiles ↔ Portal
├── scrapers/
│   ├── simplymiles.py        # Playwright with persistent auth
│   ├── portal.py             # HTTP-based (fallback to Playwright)
│   └── hotels.py             # HTTP/API for 8 cities, 90 days
├── alerts/
│   ├── sender.py             # Resend API integration
│   ├── evaluator.py          # Threshold checking, deduplication
│   ├── formatter.py          # Email HTML/text templates
│   └── health.py             # Scraper health monitoring
├── scripts/
│   ├── setup_auth.py         # Manual SimplyMiles login
│   ├── run_all.py            # Full pipeline: scrape → detect → alert
│   ├── send_digest.py        # Daily digest at 8am CT
│   └── test_alerts.py        # Test email delivery
├── tests/                    # 80 tests (pytest)
├── docs/
│   ├── discovery_notes.md    # Template for site inspection
│   └── DISCOVERY_INSTRUCTIONS.md  # Claude Code + Extension workflow
├── browser_data/             # Playwright session (gitignored)
├── data/                     # SQLite database
└── logs/                     # Log files
```

---

## Key Configuration

### Alert Thresholds (`config/settings.py`)

| Deal Type | Immediate Alert | Daily Digest |
|-----------|-----------------|--------------|
| Stacked | ≥15 LP/$ | ≥10 LP/$ |
| Hotels | ≥25 LP/$ | ≥15 LP/$ |
| Portal only | ≥20 LP/$ | ≥10 LP/$ |

### Scoring Modifiers

- **Low commitment:** +40% for <$50, +30% for <$100, +10% for <$200
- **High commitment:** -20% for >$500
- **Urgency:** +20% for expiring within 48 hours
- **Austin local:** +15% for Austin hotels

### Fuzzy Matching

- Threshold: 85% similarity (rapidfuzz token_sort_ratio)
- Aliases defined in `settings.py` for known mismatches

---

## Data Sources

### 1. SimplyMiles (Authenticated)
- URL: https://www.simplymiles.com
- Auth: Playwright persistent context, manual login via `setup_auth.py`
- Session: ~7-30 days before re-auth needed
- Offers: ~142 card-linked offers

### 2. eShopping Portal (Public)
- URL: https://www.aadvantageeshopping.com
- Auth: None required
- Merchants: ~200+ with miles/$ rates

### 3. AAdvantage Hotels (Public)
- URL: https://www.aadvantagehotels.com
- Auth: None required
- Cities: Austin, Dallas, Houston, Las Vegas, NYC, Boston, SF, LA
- Date range: 90 days ahead, weekend-heavy

---

## Database Schema (SQLite)

```sql
simplymiles_offers     -- Scraped offers with expiration
portal_rates           -- Merchant miles/$ rates
hotel_deals            -- Hotel deals with yield calculations
stacked_opportunities  -- Computed stacks (SimplyMiles + Portal + CC)
alert_history          -- Deduplication tracking
scraper_health         -- Success/failure tracking
```

---

## Running the System

```bash
# Activate environment
cd /Users/alexbespalov/Desktop/Projects/aa_scraper
source venv/bin/activate

# One-time: Set up SimplyMiles auth
python scripts/setup_auth.py

# Full pipeline
python scripts/run_all.py

# Individual scrapers
python scrapers/simplymiles.py --test
python scrapers/portal.py --test
python scrapers/hotels.py --test

# Test emails
python scripts/test_alerts.py
python scripts/test_alerts.py --digest

# Daily digest preview
python scripts/send_digest.py --preview

# Run tests
pytest tests/ -v
```

---

## What Needs Discovery (Phase 0)

The scrapers have **placeholder CSS selectors** that need to be updated after inspecting the actual websites:

### SimplyMiles (`scrapers/simplymiles.py`)

```python
# Line ~180 - placeholder selectors
offer_selectors = [
    '[class*="offer-card"]',
    '[class*="OfferCard"]',
    # ... need actual selectors
]
```

**Need to find:**
- Offer card container
- Merchant name element
- Miles/LP amount element
- Min spend element
- Expiration element
- "Expiring Soon" badge

### Portal (`scrapers/portal.py`)

```python
# Line ~130 - placeholder selectors
card_selectors = [
    '.store-card',
    '.merchant-card',
    # ... need actual selectors
]
```

**Need to find:**
- API endpoint (preferred) OR HTML selectors
- Merchant name, miles rate, bonus indicator

### Hotels (`scrapers/hotels.py`)

```python
# Line ~90 - placeholder API endpoints
api_endpoints = [
    f"{HOTELS_BASE_URL}/api/search",
    # ... need actual endpoint
]
```

**Need to find:**
- Search API endpoint and parameters
- Response format

---

## Environment Variables

```bash
# Required in .env file:
RESEND_API_KEY=re_xxxxxxxxxxxxx
ALERT_EMAIL_TO=user@example.com,user@example.com
ALERT_EMAIL_FROM=alerts@example.com
TZ=America/Chicago
```

---

## Alex's Info

- **Email:** user@example.com, user@example.com
- **Location:** Austin, TX (America/Chicago timezone)
- **AA Status:** Gold (40K LPs), targeting Platinum (75K)
- **Budget:** ~$500/month
- **Credit Card:** AA Mastercard (1 LP/$)
- **Resend Domain:** novaconsultpro.com (verified)

---

## Key Files to Know

| File | Purpose |
|------|---------|
| `config/settings.py` | All thresholds and configuration |
| `core/database.py` | SQLite CRUD + staleness detection |
| `core/normalizer.py` | Merchant name matching (rapidfuzz) |
| `core/scorer.py` | Yield + deal score calculation |
| `core/stack_detector.py` | Match SimplyMiles ↔ Portal |
| `scrapers/simplymiles.py` | Main scraper to update |
| `scripts/run_all.py` | Full pipeline orchestration |

---

## Immediate Next Steps

1. **Use Claude Chrome Extension** to inspect the three websites
2. **Update CSS selectors** in scraper files based on findings
3. **Test scrapers** with `--test` flag
4. **Configure .env** with Resend API key
5. **Run full pipeline** with `python scripts/run_all.py`

See `docs/DISCOVERY_INSTRUCTIONS.md` for detailed inspection workflow.

---

## Cron Schedule (For VPS Deployment)

```cron
# SimplyMiles - every 2 hours
0 */2 * * * cd /opt/aa-monitor && python scrapers/simplymiles.py

# Portal - every 4 hours  
30 */4 * * * cd /opt/aa-monitor && python scrapers/portal.py

# Hotels - every 6 hours
0 */6 * * * cd /opt/aa-monitor && python scrapers/hotels.py

# Daily digest - 8am Central
0 8 * * * cd /opt/aa-monitor && python scripts/send_digest.py
```

---

## Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| SimplyMiles shows login | Run `setup_auth.py` again |
| No offers found | Update CSS selectors in scraper |
| Email not sending | Check RESEND_API_KEY in .env |
| Import errors | Activate venv: `source venv/bin/activate` |
| Database errors | Delete `data/aa_monitor.db` and rerun |

---

*Last updated: December 27, 2024*
*80 tests passing | Ready for Phase 0 discovery*

