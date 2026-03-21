# Module Catalog

Quick reference for all modules in the AA Points Monitor codebase.

---

## Core Modules (`core/`)

### database.py
**Purpose:** SQLite database operations (singleton pattern)

**Key Exports:**
- `get_database()` → Returns singleton `Database` instance
- `Database` class with methods for all CRUD operations

**Depends on:** `config.settings`

**Used by:** All scrapers, stack_detector, evaluator, health

**Example:**
```python
from core.database import get_database
db = get_database()
offers = db.get_active_simplymiles_offers()
```

---

### scorer.py
**Purpose:** Deal scoring with yield calculations and modifiers

**Key Exports:**
- `StackedDeal` - Dataclass for stacked deal calculations
- `calculate_deal_score(base_yield, min_spend, ...)` → Modified score
- `is_expiring_soon(expires_at, hours=48)` → Boolean
- `format_yield(yield_ratio)` → "X.XX LP/$"

**Depends on:** `config.settings`

**Used by:** stack_detector, hotels scraper, formatter

---

### stack_detector.py
**Purpose:** Match SimplyMiles offers with Portal merchants

**Key Exports:**
- `detect_stacked_opportunities(check_staleness=True, min_yield=0)` → List[Dict]
- `store_opportunities(opportunities)` → int (count stored)
- `run_detection(store_results=True)` → Dict (status report)

**Depends on:** `database`, `normalizer`, `scorer`, `settings`

**Used by:** run_all.py, cron jobs

---

### normalizer.py
**Purpose:** Merchant name normalization and fuzzy matching

**Key Exports:**
- `normalize_merchant(name)` → Normalized string
- `find_best_match(name, candidates, threshold=85)` → Optional[Tuple[str, int]]

**Depends on:** `config.settings` (for aliases)

**Used by:** All scrapers, stack_detector

---

### optimizer.py
**Purpose:** Budget allocation across deals

**Key Exports:**
- `TopPick` - Named tuple for best single deal
- `AllocationResult` - Named tuple for budget distribution
- `identify_top_pick(opportunities)` → TopPick
- `optimize_allocation(budget, opportunities)` → AllocationResult

**Depends on:** `config.settings`

**Used by:** alerts/evaluator, alerts/formatter

---

### hotel_scorer.py
**Purpose:** Hotel-specific yield calculations

**Key Exports:**
- `HotelDeal` - Dataclass for hotel deal calculations
- `calculate_hotel_yield(cost, miles)` → float
- `score_hotel_deal(...)` → float with modifiers

**Depends on:** `config.settings`

**Used by:** hotels scraper, hotel_discovery script

---

### verification.py
**Purpose:** Hotel yield matrix verification

**Key Exports:**
- `get_entries_needing_verification(limit)` → List[Dict]
- `get_matrix_health()` → Dict with coverage stats

**Depends on:** `database`

**Used by:** hotel_discovery script

---

### http_client.py (NEW)
**Purpose:** Reusable HTTP client with retry logic

**Key Exports:**
- `fetch_json(url, **options)` → Dict (async)
- `create_client(**options)` → AsyncContextManager
- `create_sync_client(**options)` → httpx.Client
- Constants: `DEFAULT_TIMEOUT`, `DEFAULT_HEADERS`

**Depends on:** `exceptions`

**Used by:** Can be adopted by scrapers for simpler HTTP

---

### exceptions.py (NEW)
**Purpose:** Custom exception hierarchy

**Key Exports:**
- `AAMonitorError` - Base exception
- Scraper: `ScraperError`, `SessionExpiredError`, `ParseError`, `NoDataError`
- HTTP: `HttpClientError`, `RetryableError`, `RateLimitError`, `AuthenticationError`
- Database: `DatabaseError`, `StaleDataError`
- Alerts: `AlertError`, `EmailDeliveryError`, `PushNotificationError`
- Config: `ConfigurationError`, `MissingEnvVarError`

**Depends on:** Nothing (leaf module)

**Used by:** http_client, can be adopted throughout codebase

---

## Alert Modules (`alerts/`)

### evaluator.py
**Purpose:** Determine which deals trigger alerts

**Key Exports:**
- `get_pending_immediate_alerts()` → Dict with stack/hotel lists
- `get_digest_deals()` → Dict with all deal types
- `record_alerts(deals, alert_type, deal_type)` → None
- `should_send_immediate_alert(deal, deal_type)` → Boolean

**Depends on:** `database`, `optimizer`, `settings`

**Used by:** check_alerts script, run_all

---

### formatter.py
**Purpose:** HTML and text email formatting

**Key Exports:**
- `format_immediate_alert(deal, deal_type)` → Dict[subject, html, text]
- `format_batch_alert(deals, deal_type)` → Dict[subject, html, text]
- `format_daily_digest(...)` → Dict[subject, html, text]

**Depends on:** `database`, `optimizer`, `scorer`, `settings`

**Used by:** sender, check_alerts, send_digest

---

### sender.py
**Purpose:** Email delivery via Resend API

**Key Exports:**
- `send_immediate_alert(subject, html, text)` → Boolean
- `send_daily_digest(subject, html, text)` → Boolean
- `send_health_alert(scraper_name, failure_count, last_error)` → Boolean

**Depends on:** `config.settings`

**Used by:** check_alerts, send_digest, health

---

### push.py
**Purpose:** Push notifications via ntfy.sh/Pushover

**Key Exports:**
- `send_push(title, message, priority=0, tags=None)` → Boolean
- `push_hot_deal(merchant, yield_ratio, min_spend, total_miles)` → Boolean
- `push_hotel_deal(hotel, city, yield_ratio, total_cost, total_miles)` → Boolean
- `push_system_alert(title, message)` → Boolean

**Depends on:** Nothing (reads from env vars)

**Used by:** check_alerts

---

### health.py
**Purpose:** Scraper health monitoring

**Key Exports:**
- `HealthMonitor` class
- `check_and_alert()` → Dict (convenience function)

**Depends on:** `database`, `sender`, `settings`

**Used by:** Can be called from cron

---

## Scraper Modules (`scrapers/`)

### simplymiles_api.py
**Purpose:** Fetch SimplyMiles offers via JSON API (preferred)

**Key Exports:**
- `fetch_offers_via_api()` → List[Dict] (async)
- `run_scraper()` → Dict (status report)

**Depends on:** `database`, `normalizer`, `settings`

**Auth:** Requires cookies from browser session

---

### simplymiles.py
**Purpose:** Fetch SimplyMiles offers via Playwright (fallback)

**Key Exports:**
- `scrape_offers()` → List[Dict] (async)
- `run_scraper()` → Dict (status report)

**Depends on:** `database`, `normalizer`, `settings`

**Auth:** Uses Playwright persistent context

---

### portal.py
**Purpose:** Fetch AA eShopping portal rates

**Key Exports:**
- `scrape_via_cartera_api()` → List[Dict] (async)
- `run_scraper()` → Dict (status report)

**Depends on:** `database`, `normalizer`, `settings`

**Auth:** None (public API)

---

### hotels.py
**Purpose:** Fetch AAdvantage Hotels deals

**Key Exports:**
- `search_hotels(city, check_in, nights)` → List[Dict]
- `run_scraper()` → Dict (status report)

**Depends on:** `database`, `scorer`, `cities`, `settings`

**Auth:** None (public API)

---

## Config Modules (`config/`)

### settings.py
**Purpose:** Application configuration with defaults

**Key Exports:**
- `get_settings()` → Settings singleton
- `Settings` dataclass with nested config
- `Thresholds`, `MatchingConfig`, `ScoringConfig` nested classes

**Depends on:** Nothing (leaf module)

---

### cities.py
**Purpose:** Priority city definitions for hotel searches

**Key Exports:**
- `City` named tuple
- `PRIORITY_CITIES` list
- `get_search_dates(advance_days, num_dates)` → List[Tuple[date, date]]

**Depends on:** Nothing (leaf module)

---

## Scripts (`scripts/`)

| Script | Purpose |
|--------|---------|
| `run_all.py` | Full pipeline orchestrator |
| `send_digest.py` | Send daily digest email |
| `check_alerts.py` | Check and send immediate alerts |
| `setup_cron.py` | Install/remove cron jobs |
| `setup_auth.py` | Browser session setup for SimplyMiles |
| `test_alerts.py` | Test email sending |
| `hotel_discovery.py` | Explore hotel yield matrix |
| `analyze_hotels.py` | Generate hotel analysis report |

---

## Dependency Graph

```
config/
   ↑
core/exceptions (leaf)
   ↑
core/http_client
   ↑
core/normalizer, scorer, hotel_scorer
   ↑
core/database (uses settings)
   ↑
core/stack_detector, optimizer, verification
   ↑
alerts/evaluator, formatter, sender, push, health
   ↑
scrapers/simplymiles*, portal, hotels
   ↑
scripts/run_all, check_alerts, send_digest, etc.
```

---

*Last updated: 2024-12-29*
