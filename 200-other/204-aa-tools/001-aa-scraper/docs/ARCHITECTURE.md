# System Architecture

## Overview

The AA Points Arbitrage Monitor is an automated system for discovering high-yield loyalty point earning opportunities by monitoring three data sources and detecting "stacking" combinations where multiple earning channels overlap.

**Core Strategy:**
```
Portal (X mi/$) + SimplyMiles (bonus) + Credit Card (1 mi/$) = Combined Yield
Example: $5 Kindle purchase → 10 + 135 + 5 = 150 LPs = 30 LP/$
```

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES                                │
├─────────────────┬─────────────────┬─────────────────────────────────┤
│   SimplyMiles   │  AA eShopping   │      AAdvantage Hotels          │
│  (Card-linked)  │    (Portal)     │        (Bookings)               │
│   ~150 offers   │  ~1,300 rates   │    8 cities, 90 days            │
└────────┬────────┴────────┬────────┴──────────────┬──────────────────┘
         │                 │                       │
         ▼                 ▼                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         SCRAPERS (Async)                            │
├─────────────────┬─────────────────┬─────────────────────────────────┤
│ simplymiles_    │   portal.py     │         hotels.py               │
│ api.py (JSON)   │  (Cartera API)  │   (REST API + Matrix)           │
│ simplymiles.py  │                 │                                 │
│ (fallback)      │                 │                                 │
└────────┬────────┴────────┬────────┴──────────────┬──────────────────┘
         │                 │                       │
         └─────────────────┼───────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      SUPABASE DATABASE                              │
├─────────────────────────────────────────────────────────────────────┤
│  simplymiles_offers │ portal_rates │ hotel_deals │ hotel_yield_matrix│
│  stacked_opportunities │ alert_history │ scraper_health            │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      CORE PROCESSING                                │
├─────────────────┬─────────────────┬─────────────────────────────────┤
│  Stack Detector │     Scorer      │        Optimizer                │
│ (Fuzzy Match)   │  (Yield Calc)   │   (Budget Allocation)           │
└────────┬────────┴────────┬────────┴──────────────┬──────────────────┘
         │                 │                       │
         └─────────────────┼───────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ALERT SYSTEM                                   │
├─────────────────┬─────────────────┬─────────────────────────────────┤
│    Evaluator    │    Formatter    │         Sender                  │
│ (Thresholds)    │  (HTML/Text)    │    (Resend API)                 │
└─────────────────┴─────────────────┴─────────────────────────────────┘
```

---

## Component Breakdown

### 1. Scrapers (`scrapers/`)

| Scraper | Method | Source | Auth |
|---------|--------|--------|------|
| `simplymiles_api.py` | JSON API (preferred) | `simplymiles.com/get-pclo-and-rakuten-offers` | Cookie auth |
| `simplymiles.py` | Playwright DOM | HTML parsing | Browser session |
| `portal.py` | Cartera REST API | `api.cartera.com/content/v4/merchants/all` | None (public) |
| `hotels.py` | REST API | `aadvantagehotels.com/rest/` | None (public) |

**Key Implementation Details:**
- All scrapers are async (`asyncio` + `httpx`)
- Random delays (2-5s) between requests
- Retry logic with exponential backoff (max 3 attempts)
- Staleness thresholds: SimplyMiles 6h, Portal 12h, Hotels 24h

**Hotels API Flow:**
```
1. GET /rest/aadvantage-hotels/places?query={city}     → Agoda place ID
2. GET /rest/aadvantage-hotels/searchRequest?...       → Search UUID
3. GET /rest/aadvantage-hotels/search/{uuid}           → Poll for results
```

### 2. Database (`core/database.py`)

**Pattern:** Singleton with context manager for connections

**Core Tables:**
| Table | Purpose | Key Fields |
|-------|---------|------------|
| `simplymiles_offers` | Card-linked offers | merchant, miles, lp, min_spend, expires |
| `portal_rates` | Shopping portal | merchant, miles_per_dollar, is_bonus |
| `hotel_deals` | Available bookings | hotel, city, cost, miles, yield |
| `stacked_opportunities` | Matched deals | merchant, combined_yield, deal_score |
| `alert_history` | Sent alerts (deduplication) | deal_id, sent_at, deal_score |
| `scraper_health` | System monitoring | scraper, status, last_run, failures |

**Intelligence Tables:**
| Table | Purpose | Entries |
|-------|---------|---------|
| `hotel_yield_matrix` | Yield predictions by city/dow/duration/advance | 1,176 |
| `hotel_yield_history` | Historical yield tracking | Variable |
| `discovery_progress` | Session resume for long-running exploration | Variable |

### 3. Core Processing (`core/`)

#### Stack Detector (`core/stack_detector.py`)
```
SimplyMiles Offers ──┐
                     ├── Fuzzy Match (85%) ──► Stacked Opportunities
Portal Rates ────────┘
```
- Uses `rapidfuzz.fuzz.token_sort_ratio` at 85% threshold
- Applies merchant aliases from `config/settings.py` for known mismatches
- Calculates combined yield: `portal + simplymiles + cc_bonus (1 mi/$)`

#### Scorer (`core/scorer.py`)
```python
base_yield = total_miles / min_spend

Modifiers applied (multiplicative):
  +40% if min_spend < $50    (low commitment bonus)
  +30% if min_spend < $100
  +10% if min_spend < $200
  -20% if min_spend > $500   (high commitment penalty)
  +20% if expiring < 48h     (urgency bonus)
  +15% if Austin hotel       (local preference)

deal_score = base_yield × product(all_modifiers)
```

#### Optimizer (`core/optimizer.py`)
- **Strategy:** Greedy allocation by efficiency (score/spend)
- **Function:** `optimize_allocation(budget, opportunities)` → Optimal distribution
- **Function:** `identify_top_pick(opportunities)` → Best single deal with reasoning

### 4. Alert System (`alerts/`)

| Component | File | Responsibility |
|-----------|------|----------------|
| Evaluator | `evaluator.py` | Threshold checking, 24h cooldown, 20% improvement override |
| Formatter | `formatter.py` | HTML/text email templates, above-expectation badges |
| Sender | `sender.py` | Resend API integration, batched delivery |
| Health | `health.py` | Scraper failure tracking, alert after 3 consecutive failures |

**Alert Thresholds (from `config/settings.py`):**
| Deal Type | Immediate Alert | Daily Digest |
|-----------|-----------------|--------------|
| Stacked | ≥15 LP/$ | ≥10 LP/$ |
| Hotels | ≥25 LP/$ | ≥15 LP/$ |
| Portal-only | ≥20 LP/$ | ≥10 LP/$ |

---

## Data Flow Diagrams

### Daily Pipeline
```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   SCRAPE     │    │   DETECT     │    │   ALERT      │
│  (2-6 hours) │ ─► │  (after)     │ ─► │  (if needed) │
└──────────────┘    └──────────────┘    └──────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
  SimplyMiles        Match SM ↔ Portal    Check thresholds
  Portal             Calculate yields     Check cooldown
  Hotels             Apply modifiers      Format email
       │                   │              Send via Resend
       ▼                   ▼              Record history
    [Database]          [Database]
```

### Hotel Intelligence Flow
```
DISCOVERY (one-time)          VERIFICATION (weekly)        SMART SCRAPING (daily)
        │                            │                            │
        ▼                            ▼                            ▼
Explore 1,176 combos        Find stale entries          Query matrix for best
8 cities × 7 dow ×          Re-test yields              (dow, advance) combos
3 durations × 6 advance     Update stability            Prioritize searches
        │                            │                            │
        └────────────────────────────┴────────────────────────────┘
                                     │
                                     ▼
                           hotel_yield_matrix table
```

---

## Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Language | Python 3.13 | Async support, rich ecosystem |
| HTTP Client | httpx | Async, modern, type hints |
| Browser Automation | Playwright | Reliable, headless support |
| Fuzzy Matching | rapidfuzz | Fast, accurate, Levenshtein |
| Database | Supabase (PostgreSQL) | Cloud-hosted, web dashboard, real-time |
| Email | Resend API | Reliable, good DX, reasonable pricing |
| Testing | pytest + pytest-asyncio | Standard, async support |

---

## Key Design Decisions

| Decision | Choice | Alternative Considered | Rationale |
|----------|--------|------------------------|-----------|
| Database | Supabase | SQLite | Web dashboard, accessible from anywhere, automatic backups |
| Scrapers | Async | Threaded | Better I/O handling, cleaner code |
| Matching | Fuzzy 85% | Exact only | Merchant names vary between sources |
| Optimizer | Greedy | Linear programming | Simple, fast, good-enough |
| DB Pattern | Singleton | Connection pool | CLI usage, not web server |

---

## Failure Modes & Handling

| Failure | Detection | Recovery |
|---------|-----------|----------|
| SimplyMiles session expired | 401/403 response | Email alert, manual re-auth |
| API rate limited | 429 response | Exponential backoff, retry |
| Network timeout | httpx.TimeoutError | Retry up to 3 times |
| Stale data | Staleness check in health | Alert in digest, re-scrape |
| Scraper consecutive failures | `scraper_health` table | Alert after 3 failures |

---

## Integration Points

| External Service | Purpose | Auth Method |
|------------------|---------|-------------|
| SimplyMiles API | Card-linked offers | Cookie from browser session |
| Cartera API | Portal rates | Public (no auth) |
| AAdvantage Hotels API | Hotel deals | Public (no auth) |
| Resend API | Email delivery | API key in `.env` |

---

## VPS Deployment

**Status:** OPERATIONAL at REDACTED_VPS_IP (DigitalOcean $6/mo droplet)

### Deployment Architecture
```
┌─────────────────────────────────────────────────────────────────────┐
│                      VPS (REDACTED_VPS_IP)                             │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Cron Jobs (7)                            │    │
│  │  • SimplyMiles (10min) • Alert check (2h +20m)              │    │
│  │  • Portal (4h)         • Daily digest (8am CT)              │    │
│  │  • Hotels (6h)         • Matrix verification (Sun 3am)      │    │
│  │  • Stack detection (2h +15m)                                │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              │                                      │
│                              ▼                                      │
│  ┌───────────────────┐    ┌───────────────────┐                    │
│  │   Python venv     │    │   Supabase        │                    │
│  │   /root/venv/     │    │   (cloud DB)      │                    │
│  └───────────────────┘    └───────────────────┘                    │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                   logs/ (per-job)                           │    │
│  │  simplymiles.log, portal.log, hotels.log, keepalive.log...  │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ Cookies sync
                              │ (rsync from Mac)
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Mac (Development)                              │
│  • Browser-based re-auth (Playwright)                               │
│  • Cookie extraction → simplymiles_cookies.json                     │
│  • rsync to VPS when session expires                                │
└─────────────────────────────────────────────────────────────────────┘
```

### Access
- **SSH:** `ssh root@REDACTED_VPS_IP`
- **VNC:** REDACTED_VPS_IP:5900 (password: REDACTED_VNC_PASS)
- **Logs:** `/root/aa_scraper/logs/`

### Session Management
SimplyMiles requires browser cookies that expire every 7-30 days. The session stability system includes:

| Component | Purpose |
|-----------|---------|
| `scripts/session_keepalive.py` | Refreshes session every 6 hours (cron) |
| `scripts/quick_reauth.py` | Streamlined re-authentication |
| Pre-run validation | Fails fast on expired session (HTTP 419) |
| Proactive alerts | Warning email at 5 days session age |

---

## Scaling Considerations

**Current:** VPS deployment, Supabase (cloud PostgreSQL), cron-based execution

**If scaling needed:**
1. **Multiple users:** Add user model, multi-tenant schema
2. **Higher frequency:** Add rate limiting awareness, distributed queue
3. **More data sources:** Plugin architecture for new scrapers
4. **High availability:** Container orchestration, database replication

---

*Last updated: 2026-01-03 (Supabase migration)*
