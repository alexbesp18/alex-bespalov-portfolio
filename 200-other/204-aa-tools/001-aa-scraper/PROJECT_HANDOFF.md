# AA Points Arbitrage Monitor - Complete Project Handoff

## Executive Summary

Build an automated system to monitor American Airlines loyalty point earning opportunities and alert Alex when exceptional deals arise. The core strategy is **minimal dollar commitment, maximum LP (Loyalty Points) yield**.

---

## User Context: Alex

- **Current AA Status:** Gold (40,000 LPs)
- **Target Status:** Platinum (75,000 LPs) = **35,000 LP gap to close**
- **Monthly Budget:** ~$500 (flexible for exceptional opportunities)
- **Credit Card:** AA Mastercard (mid-tier, $95/year) — earns 1 LP per $1 spent
- **Location:** Austin, TX (timezone: America/Chicago)
- **Email:** user@example.com, user@example.com
- **Resend Domain:** novaconsultpro.com (already verified and working)

---

## The Arbitrage Opportunity

### How AA Loyalty Points Work
- 1 LP = 1 mile earned (they're equivalent for status qualification)
- Status tiers: Gold (40K) → Platinum (75K) → Platinum Pro (125K) → Executive Platinum (200K)
- LPs can be earned from: flights, credit card spend, shopping portals, SimplyMiles, hotels

### The "Stack" Strategy (Highest Value)
Combine multiple earning channels on a single purchase:

```
LAYER 1: AAdvantage eShopping Portal
         Click through portal before purchase
         Earns: X miles per $1 (varies by merchant, typically 1-15 mi/$)

LAYER 2: SimplyMiles
         Activate offer, pay with linked Mastercard
         Earns: Flat bonus OR per-dollar rate
         
LAYER 3: Credit Card
         Pay with AA Mastercard
         Earns: 1 LP per $1

TOTAL YIELD = (Portal miles + SimplyMiles bonus + CC miles) / $ spent
```

### Example Stack (from research)
- Merchant: Viator
- Spend: $200
- Portal: 5 mi/$ = 1,000 miles
- SimplyMiles: 1,000 bonus miles
- CC: 200 miles
- **Total: 2,200 LPs on $200 = 11 LP/$**

### Hotel Arbitrage (Secondary)
- Book through aadvantagehotels.com
- Some hotels offer 5,000-10,000+ LPs per stay
- Example: $300 hotel → 10,000 LPs = 33 LP/$
- Constraint: Requires actual travel/stay

---

## Data Sources

### 1. SimplyMiles (simplymiles.com)
- **Alex's account:** 142 offers available (confirmed via screenshot)
- **Auth required:** Yes — uses AA credentials
- **Card linked:** AA Mastercard (already connected)
- **Offer types observed:**
  - Flat bonus: "135 miles + 135 LP on a purchase of $5 or more" (Kindle)
  - Per-dollar: "4 miles + 4 LP per $1 spent on any purchase" (Lyft)
  - Flat bonus: "1065 miles + 1065 LP on a purchase of $50 or more" (Stitch Fix)
  - Per-dollar: "13 miles + 13 LP per $1 spent on any purchase" (TurboTax)
- **Key fields to scrape:**
  - Merchant name
  - Offer type (flat vs per-dollar)
  - Miles/LP amount
  - Minimum spend (if flat bonus)
  - Expiration date
  - "EXPIRING SOON" flag
- **Scrape frequency:** Every 2 hours
- **Scrape method:** Playwright with persistent browser context (Option B chosen)

### 2. AAdvantage eShopping Portal (aadvantageeshopping.com)
- **Auth required:** No (public rates)
- **Content:** ~200+ merchants with miles/$ rates
- **Key fields to scrape:**
  - Merchant name
  - Current miles per dollar rate
  - Bonus indicator (elevated rates)
  - Category
- **Scrape frequency:** Every 4 hours
- **Scrape method:** HTTP requests or light browser scraping

### 3. AAdvantage Hotels (aadvantagehotels.com)
- **Auth required:** No (public search)
- **Target cities (Alex's frequently visited):**
  - Austin, TX (HIGH priority + local)
  - Dallas, TX
  - Houston, TX
  - Las Vegas, NV
  - New York, NY
  - Boston, MA
  - San Francisco, CA
  - Los Angeles, CA
- **Also:** Top 10 best deals nationwide (any city)
- **Key fields to scrape:**
  - Hotel name
  - City/State
  - Nightly rate
  - Base miles
  - Bonus miles
  - Total miles
  - Calculated yield (miles / cost)
- **Scrape frequency:** Every 6 hours
- **Scrape method:** HTTP/API discovery, fallback to browser

---

## Architecture Decisions

### Infrastructure
- **Hosting:** $6/month VPS (DigitalOcean or Vultr recommended)
- **OS:** Ubuntu 24.04
- **Runtime:** Python 3.11+
- **Browser automation:** Playwright
- **Database:** SQLite (single file, no external dependencies)
- **Email:** Resend API
- **Scheduling:** Cron jobs

### Why SQLite over Supabase
- Single user, single server — no need for hosted DB
- Zero network latency
- No credentials to manage
- Backup = copy one file
- Alex has Supabase but it's overkill for this use case

### SimplyMiles Authentication Strategy (Option B - Chosen)
```
INITIAL SETUP:
1. Playwright opens browser with persistent context
2. Alex logs into SimplyMiles manually (one time)
3. Playwright saves browser profile (cookies, localStorage, session)

RUNTIME (automated):
1. Playwright launches headless with saved profile
2. Navigate to SimplyMiles offers page
3. If logged in → scrape offers
4. If login page detected → email Alex "Re-auth needed"
5. After successful scrape → profile auto-updates with refreshed session

SESSION LIFESPAN: Estimated 7-30 days before re-auth needed
```

---

## Database Schema (SQLite)

```sql
-- SimplyMiles offers (scraped from Alex's account)
CREATE TABLE simplymiles_offers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    merchant_name TEXT NOT NULL,
    merchant_name_normalized TEXT NOT NULL,  -- lowercase, stripped
    offer_type TEXT NOT NULL,  -- 'flat_bonus' or 'per_dollar'
    miles_amount INTEGER NOT NULL,  -- flat bonus amount OR per-dollar rate
    lp_amount INTEGER NOT NULL,  -- usually equals miles_amount
    min_spend REAL,  -- NULL if per-dollar type
    expires_at TEXT,  -- ISO date
    expiring_soon BOOLEAN DEFAULT FALSE,
    scraped_at TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Portal merchant rates
CREATE TABLE portal_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    merchant_name TEXT NOT NULL,
    merchant_name_normalized TEXT NOT NULL,
    miles_per_dollar REAL NOT NULL,
    is_bonus_rate BOOLEAN DEFAULT FALSE,
    category TEXT,
    url TEXT,
    scraped_at TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Hotel deals
CREATE TABLE hotel_deals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hotel_name TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    check_in TEXT NOT NULL,
    check_out TEXT NOT NULL,
    nightly_rate REAL NOT NULL,
    base_miles INTEGER NOT NULL,
    bonus_miles INTEGER DEFAULT 0,
    total_miles INTEGER NOT NULL,
    total_cost REAL NOT NULL,
    yield_ratio REAL NOT NULL,  -- total_miles / total_cost
    deal_score REAL NOT NULL,  -- yield with modifiers applied
    url TEXT,
    scraped_at TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Computed stacked opportunities
CREATE TABLE stacked_opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    merchant_name TEXT NOT NULL,
    
    -- Portal layer
    portal_rate REAL NOT NULL,
    portal_miles INTEGER NOT NULL,
    
    -- SimplyMiles layer
    simplymiles_type TEXT NOT NULL,  -- 'flat_bonus' or 'per_dollar'
    simplymiles_miles INTEGER NOT NULL,
    simplymiles_min_spend REAL,
    simplymiles_expires TEXT,
    
    -- Credit card layer (1 LP/$)
    cc_miles INTEGER NOT NULL,
    
    -- Totals
    min_spend_required REAL NOT NULL,
    total_miles INTEGER NOT NULL,
    combined_yield REAL NOT NULL,  -- total_miles / min_spend
    deal_score REAL NOT NULL,  -- yield with modifiers
    
    computed_at TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Alert history (prevent duplicate alerts)
CREATE TABLE alert_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT NOT NULL,  -- 'immediate' or 'digest'
    deal_type TEXT NOT NULL,  -- 'stack', 'hotel', 'portal'
    deal_identifier TEXT NOT NULL,  -- merchant name or hotel+city
    deal_score REAL NOT NULL,
    sent_at TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_simply_merchant ON simplymiles_offers(merchant_name_normalized);
CREATE INDEX idx_portal_merchant ON portal_rates(merchant_name_normalized);
CREATE INDEX idx_hotels_city ON hotel_deals(city, state);
CREATE INDEX idx_stacked_score ON stacked_opportunities(deal_score DESC);
CREATE INDEX idx_alert_identifier ON alert_history(deal_identifier, sent_at);
```

---

## Scoring Algorithm

### Base Yield Calculation

**For Stacked Deals:**
```python
def calculate_stack_yield(portal_rate, simply_offer, spend_amount):
    """
    portal_rate: miles per dollar from eShopping portal
    simply_offer: dict with type, amount, min_spend
    spend_amount: how much we're spending
    """
    # Layer 1: Portal
    portal_miles = portal_rate * spend_amount
    
    # Layer 2: SimplyMiles
    if simply_offer['type'] == 'flat_bonus':
        simply_miles = simply_offer['amount']  # flat regardless of spend
    else:  # per_dollar
        simply_miles = simply_offer['amount'] * spend_amount
    
    # Layer 3: Credit Card (AA Mastercard = 1 LP/$)
    cc_miles = spend_amount * 1
    
    total_miles = portal_miles + simply_miles + cc_miles
    yield_ratio = total_miles / spend_amount
    
    return yield_ratio
```

**For Hotels:**
```python
def calculate_hotel_yield(total_miles, total_cost):
    return total_miles / total_cost
```

### Deal Score Modifiers

```python
def calculate_deal_score(base_yield, min_spend, has_expiration, is_austin=False):
    """
    Apply modifiers based on Alex's "minimal commitment" framework
    """
    score = base_yield
    
    # Low commitment bonus (prefer smaller spends)
    if min_spend < 50:
        score *= 1.4  # Very low commitment
    elif min_spend < 100:
        score *= 1.3
    elif min_spend < 200:
        score *= 1.1
    elif min_spend > 500:
        score *= 0.8  # Penalty for high commitment
    
    # Urgency bonus
    if has_expiration:  # Expiring within 48 hours
        score *= 1.2
    
    # Austin local bonus (for hotels)
    if is_austin:
        score *= 1.15
    
    return score
```

---

## Alert Thresholds (Configurable)

```python
THRESHOLDS = {
    # Stacked deals (Portal + SimplyMiles)
    'stack_immediate_alert': 15,  # LP/$ - send email NOW
    'stack_daily_digest': 10,     # LP/$ - include in daily summary
    
    # Hotel deals
    'hotel_immediate_alert': 25,  # LP/$
    'hotel_daily_digest': 15,     # LP/$
    
    # Portal-only (no SimplyMiles match)
    'portal_immediate_alert': 20,  # LP/$ (rare, but possible during promos)
    'portal_daily_digest': 10,     # LP/$
    
    # Cooldown to prevent duplicate alerts
    'alert_cooldown_hours': 24,
}
```

---

## Alert Format

### Immediate Alert Email
```
Subject: 🔥 AA Points Alert: 27 LP/$ deal found!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 STACKED OPPORTUNITY: Kindle
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💵 Minimum Spend: $5
✈️ Total Earnings: 135 LPs

Breakdown:
  • Portal: 2 mi/$ × $5 = 10 miles
  • SimplyMiles: 135 bonus miles
  • Credit Card: 5 miles

📈 YIELD: 27 LP/$
⏰ Expires: 12/31/2025

ACTION REQUIRED:
1. Click through eShopping portal first
2. Activate offer on SimplyMiles
3. Pay with your AA Mastercard

Portal Link: [link]
SimplyMiles: https://simplymiles.com
```

### Daily Digest Email
```
Subject: ✈️ AA Points Daily Digest - 12 opportunities found

Good morning Alex,

Here's today's summary of LP earning opportunities:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 TOP STACKED DEALS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 🔥 Kindle — 27 LP/$ (spend $5, earn 135 LPs) — Expires 12/31
2. ✅ Stitch Fix — 21.3 LP/$ (spend $50, earn 1,065 LPs) — Expires 12/31
3. ✅ TurboTax — 13 LP/$ (any spend) — Expires 04/18/2026
...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏨 TOP HOTEL DEALS (Your Cities)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Marriott Downtown, Las Vegas — 33 LP/$ ($300 → 10,000 LPs)
2. Hilton Austin — 28 LP/$ ($250 → 7,000 LPs)
...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌎 BEST DEALS NATIONWIDE (Top 10)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Hotel ABC, Miami — 45 LP/$ ($200 → 9,000 LPs)
...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Status Progress: Gold → Platinum
Current: ~40,000 LPs | Target: 75,000 LPs | Gap: 35,000 LPs

Happy earning!
```

---

## Resend Configuration

```python
RESEND_CONFIG = {
    'api_key': '${RESEND_API_KEY}',  # Store in environment variable
    'from_email': 'alerts@example.com',
    'to_emails': ['user@example.com', 'user@example.com'],
}
```

Alex already has Resend set up with novaconsultpro.com verified.

---

## Cron Schedule

```cron
# SimplyMiles scraper - every 2 hours
0 */2 * * * cd /opt/aa-monitor && python scrape_simplymiles.py >> /var/log/aa-monitor/simply.log 2>&1

# Portal scraper - every 4 hours
30 */4 * * * cd /opt/aa-monitor && python scrape_portal.py >> /var/log/aa-monitor/portal.log 2>&1

# Hotel scraper - every 6 hours
0 */6 * * * cd /opt/aa-monitor && python scrape_hotels.py >> /var/log/aa-monitor/hotels.log 2>&1

# Stack detection + immediate alerts - runs after each scraper
# (triggered at end of each scrape script)

# Daily digest - 8am Central
0 8 * * * cd /opt/aa-monitor && python send_digest.py >> /var/log/aa-monitor/digest.log 2>&1
```

---

## Project Structure

```
aa-monitor/
├── config/
│   ├── settings.py          # All configurable thresholds
│   └── cities.py             # Hotel city configurations
├── scrapers/
│   ├── simplymiles.py        # Playwright-based, authenticated
│   ├── portal.py             # HTTP-based, public
│   └── hotels.py             # HTTP/browser hybrid
├── core/
│   ├── database.py           # SQLite operations
│   ├── normalizer.py         # Merchant name normalization
│   ├── stack_detector.py     # Matching algorithm
│   └── scorer.py             # Deal scoring logic
├── alerts/
│   ├── evaluator.py          # Check thresholds, dedup
│   ├── formatter.py          # Email HTML/text generation
│   └── sender.py             # Resend integration
├── browser_data/             # Playwright persistent context (gitignored)
├── data/
│   └── aa_monitor.db         # SQLite database
├── logs/
├── scripts/
│   ├── setup_auth.py         # Initial SimplyMiles login
│   ├── run_all.py            # Manual full run
│   └── test_alerts.py        # Test email sending
├── requirements.txt
├── .env.example
└── README.md
```

---

## Implementation Phases

### Phase 1: SimplyMiles Scraper + Auth
- Set up Playwright with persistent browser context
- Create `setup_auth.py` for initial manual login
- Build scraper to extract all 142 offers
- Parse both offer types (flat bonus and per-dollar)
- Store in SQLite

### Phase 2: Portal Scraper
- Discover if API exists (check network tab)
- Build HTTP-based scraper or light Playwright
- Extract merchant names and rates
- Store in SQLite

### Phase 3: Stack Detection
- Implement merchant name normalization
- Match SimplyMiles offers ↔ Portal merchants
- Calculate combined yields for all matches
- Score deals with modifiers
- Store computed opportunities

### Phase 4: Alert System
- Integrate Resend
- Build immediate alert logic (threshold check + dedup)
- Build daily digest generator
- Test email formatting

### Phase 5: Hotel Scraper
- Analyze aadvantagehotels.com structure
- Build scraper for 8 priority cities
- Add nationwide "top 10" scan
- Integrate into alert system

### Phase 6: VPS Deployment
- Provision $6/mo VPS
- Install dependencies (Python, Playwright, Chromium)
- Set up cron jobs
- Configure logging
- Test full system

---

## Environment Variables

```bash
# .env
RESEND_API_KEY=re_xxxxxxxxxxxxx
ALERT_EMAIL_TO=user@example.com,user@example.com
ALERT_EMAIL_FROM=alerts@example.com
TZ=America/Chicago
```

---

## Key Technical Notes

### Merchant Name Normalization
SimplyMiles says "Kindle and Kindle Unlimited", portal might say "Amazon Kindle". Need fuzzy matching:

```python
def normalize_merchant(name: str) -> str:
    """Normalize for matching across platforms"""
    name = name.lower().strip()
    
    # Remove common suffixes
    for suffix in ['.com', '.net', '.org', ' inc', ' llc', ' corp']:
        name = name.replace(suffix, '')
    
    # Remove special characters
    name = re.sub(r'[^a-z0-9\s]', '', name)
    
    # Collapse whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name

# May also need alias mapping for known mismatches:
MERCHANT_ALIASES = {
    'kindle and kindle unlimited': 'amazon kindle',
    'amazoncom': 'amazon',
    # etc.
}
```

### SimplyMiles Session Detection
Check if logged in before scraping:

```python
async def is_logged_in(page) -> bool:
    """Check if SimplyMiles session is valid"""
    # Look for elements that only appear when logged in
    offers_count = await page.query_selector('text=OFFERS AVAILABLE')
    login_button = await page.query_selector('text=Log in')
    
    return offers_count is not None and login_button is None
```

### Rate Limiting / Anti-Detection
- Random delays between requests (2-5 seconds)
- Realistic user agent
- Don't scrape more frequently than necessary
- SimplyMiles is card-linked program — they expect real users, not bots

---

## Success Metrics

1. **System Health:** All scrapers complete successfully >95% of the time
2. **Alert Accuracy:** No false positives (bad yield calculations)
3. **Session Stability:** SimplyMiles auth lasts 7+ days between manual re-logins
4. **LP Efficiency:** Alex achieves 15+ LP/$ average on monitored purchases
5. **Status Progress:** Close the 35,000 LP gap within 3-4 months at $500/mo budget

---

## Questions for Claude Code to Resolve

1. What's the actual HTML structure of SimplyMiles offer cards? (Need to inspect)
2. Does eShopping portal have a hidden API? (Check network tab)
3. What's the aadvantagehotels.com search API structure?
4. How long does SimplyMiles session actually last?

---

## Commands to Get Started

```bash
# Clone/create project
mkdir aa-monitor && cd aa-monitor

# Set up Python environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install playwright httpx beautifulsoup4 resend python-dotenv

# Install Playwright browsers
playwright install chromium

# Create initial structure
mkdir -p config scrapers core alerts browser_data data logs scripts

# Initialize database
python -c "from core.database import init_db; init_db()"

# Run initial auth setup (opens browser for manual login)
python scripts/setup_auth.py

# Test scraper
python scrapers/simplymiles.py --test
```

---

## Final Notes

This is a personal automation tool for Alex to efficiently earn AA status. The "minimal commitment, maximum yield" framework means:

- Prefer deals with low minimum spend
- Prioritize stacked opportunities (multiple earning layers)
- Hotels only matter if Alex is actually traveling
- Don't alert for mediocre deals — only exceptional ones

The system should run quietly in the background and only interrupt Alex when there's something genuinely worth acting on.

---

*Document created: December 27, 2024*
*For continuation with Claude Code CLI*
