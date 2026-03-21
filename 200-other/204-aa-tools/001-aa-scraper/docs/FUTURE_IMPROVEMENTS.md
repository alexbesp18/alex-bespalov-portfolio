# Future: Improvements to Existing Features

Enhancements, optimizations, additional tests, and refinements to current functionality.

---

## 1. Scraper Improvements

### SimplyMiles Scraper

#### Session Management
**Current:** Manual re-auth every 7-30 days
**Improvement:** Proactive session refresh

```python
# Check session validity before scraping
async def ensure_valid_session():
    """Refresh session if expired or expiring soon."""
    if is_session_expiring_soon():
        await refresh_session()
    elif is_session_expired():
        send_alert("SimplyMiles session expired - manual login required")
        raise SessionExpiredError()
```

#### Offer Categorization
**Current:** All offers treated equally
**Improvement:** Categorize by type for filtering

```python
OFFER_CATEGORIES = {
    "dining": ["doordash", "uber eats", "grubhub", "restaurant"],
    "travel": ["hotel", "flight", "rental car", "airbnb"],
    "shopping": ["amazon", "walmart", "target", "best buy"],
    "subscription": ["spotify", "netflix", "hulu", "kindle"],
    "gas": ["shell", "exxon", "chevron", "bp"],
}
```

#### Duplicate Detection
**Current:** Simple merchant name match
**Improvement:** Detect same offer with different wording

```python
def is_duplicate_offer(new_offer, existing_offers):
    """Check if offer is duplicate based on merchant + value + dates."""
    for existing in existing_offers:
        if (fuzzy_match(new_offer.merchant, existing.merchant) > 90 and
            new_offer.miles == existing.miles and
            abs((new_offer.expires - existing.expires).days) < 2):
            return True
    return False
```

### Portal Scraper

#### Rate Change Detection
**Current:** Store current rates only
**Improvement:** Track rate changes over time

```sql
-- New table
CREATE TABLE portal_rate_history (
    id INTEGER PRIMARY KEY,
    merchant_name TEXT,
    miles_per_dollar REAL,
    recorded_at TEXT,
    change_from_previous REAL
);

-- Query for rate increases
SELECT merchant_name, miles_per_dollar,
       miles_per_dollar - LAG(miles_per_dollar) OVER (
           PARTITION BY merchant_name ORDER BY recorded_at
       ) as change
FROM portal_rate_history
WHERE change > 0;
```

#### Elevated Rate Tracking
**Current:** Capture elevated rates
**Improvement:** Track elevation duration and predict end dates

```python
@dataclass
class ElevatedRate:
    merchant: str
    normal_rate: float
    elevated_rate: float
    first_seen: datetime
    still_active: bool

    @property
    def days_active(self) -> int:
        return (datetime.now() - self.first_seen).days
```

### Hotels Scraper

#### Parallel City Searching
**Current:** Sequential city searches
**Improvement:** Parallel searches with rate limiting

```python
import asyncio
from asyncio import Semaphore

async def scrape_all_cities(cities: list[City], max_concurrent: int = 3):
    semaphore = Semaphore(max_concurrent)

    async def scrape_with_limit(city):
        async with semaphore:
            return await scrape_city(city)

    results = await asyncio.gather(*[
        scrape_with_limit(city) for city in cities
    ])
    return results
```

#### Price History
**Current:** Current prices only
**Improvement:** Track price trends for specific hotels

```sql
CREATE TABLE hotel_price_history (
    id INTEGER PRIMARY KEY,
    hotel_name TEXT,
    city TEXT,
    check_in TEXT,
    price REAL,
    miles INTEGER,
    yield_ratio REAL,
    recorded_at TEXT
);

-- Find hotels with improving yields
SELECT hotel_name, city,
       AVG(yield_ratio) as avg_yield,
       MAX(yield_ratio) - MIN(yield_ratio) as yield_range
FROM hotel_price_history
WHERE recorded_at > datetime('now', '-7 days')
GROUP BY hotel_name, city
HAVING yield_range > 2;
```

---

## 2. Detection & Scoring Improvements

### Stack Detector

#### Confidence Scoring
**Current:** Binary match (yes/no at 85%)
**Improvement:** Return confidence score for UI display

```python
@dataclass
class StackMatch:
    simplymiles_offer: Offer
    portal_rate: Rate
    confidence: float  # 0.85-1.0
    match_method: str  # "exact", "alias", "fuzzy"

def detect_with_confidence(offers, rates):
    matches = []
    for offer in offers:
        best_match = None
        best_score = 0

        for rate in rates:
            score = calculate_match_score(offer.merchant, rate.merchant)
            if score > best_score and score >= 0.85:
                best_score = score
                best_match = rate

        if best_match:
            matches.append(StackMatch(
                simplymiles_offer=offer,
                portal_rate=best_match,
                confidence=best_score,
                match_method="fuzzy" if best_score < 0.95 else "exact"
            ))

    return matches
```

#### Alias Learning
**Current:** Manual alias configuration
**Improvement:** Suggest aliases from near-matches

```python
def find_potential_aliases(unmatched_offers, rates, threshold=0.75):
    """Find offers that almost match a portal rate."""
    suggestions = []

    for offer in unmatched_offers:
        for rate in rates:
            score = fuzzy_match(offer.merchant, rate.merchant)
            if threshold <= score < 0.85:
                suggestions.append({
                    "simplymiles": offer.merchant,
                    "portal": rate.merchant,
                    "score": score,
                    "suggested_alias": f'"{offer.merchant.lower()}": "{rate.merchant.lower()}"'
                })

    return sorted(suggestions, key=lambda x: x["score"], reverse=True)
```

### Scorer

#### Dynamic Thresholds
**Current:** Fixed thresholds in config
**Improvement:** Adjust based on recent deal quality

```python
def calculate_dynamic_threshold(deal_type: str, lookback_days: int = 14):
    """Set threshold at 75th percentile of recent deals."""
    db = get_database()
    recent_scores = db.get_recent_scores(deal_type, lookback_days)

    if len(recent_scores) < 10:
        return get_settings().thresholds.get_default(deal_type)

    return np.percentile(recent_scores, 75)
```

#### Time-Decay Scoring
**Current:** Urgency bonus only for <48h
**Improvement:** Graduated decay curve

```python
def calculate_time_modifier(expires_at: datetime) -> float:
    """Graduated urgency modifier based on time remaining."""
    if not expires_at:
        return 1.0

    hours_remaining = (expires_at - datetime.now()).total_seconds() / 3600

    if hours_remaining < 0:
        return 0.5  # Expired penalty
    elif hours_remaining < 24:
        return 1.3  # Urgent
    elif hours_remaining < 48:
        return 1.2  # Soon
    elif hours_remaining < 72:
        return 1.1  # This week
    else:
        return 1.0  # Normal
```

#### Category Bonuses
**Current:** Only Austin hotel bonus
**Improvement:** Category-based preferences

```python
USER_PREFERENCES = {
    "preferred_categories": ["dining", "travel"],
    "preferred_merchants": ["amazon", "uber eats"],
    "avoid_categories": ["gambling"],
    "local_cities": ["Austin", "Dallas"],
}

def apply_preference_modifiers(deal, preferences):
    modifier = 1.0

    if deal.category in preferences["preferred_categories"]:
        modifier *= 1.15
    if deal.merchant in preferences["preferred_merchants"]:
        modifier *= 1.10
    if deal.category in preferences["avoid_categories"]:
        modifier *= 0.5
    if deal.city in preferences["local_cities"]:
        modifier *= 1.15

    return modifier
```

---

## 3. Alert System Improvements

### Evaluator

#### Smart Batching
**Current:** Immediate alerts sent individually
**Improvement:** Batch alerts within time window

```python
class AlertBatcher:
    def __init__(self, window_minutes: int = 15):
        self.window = timedelta(minutes=window_minutes)
        self.pending = []
        self.window_start = None

    def add_alert(self, deal):
        now = datetime.now()

        if not self.window_start:
            self.window_start = now

        self.pending.append(deal)

        if now - self.window_start >= self.window:
            return self.flush()
        return None

    def flush(self):
        alerts = self.pending
        self.pending = []
        self.window_start = None
        return alerts
```

#### Alert Fatigue Prevention
**Current:** 24h cooldown per deal
**Improvement:** Adaptive cooldown based on user engagement

```python
def calculate_adaptive_cooldown(deal_type: str) -> timedelta:
    """Increase cooldown if alerts aren't being acted on."""
    db = get_database()

    recent_alerts = db.get_recent_alerts(deal_type, days=7)
    acted_on = db.get_alerts_with_action(deal_type, days=7)

    if len(recent_alerts) == 0:
        return timedelta(hours=24)

    action_rate = len(acted_on) / len(recent_alerts)

    if action_rate < 0.1:  # <10% action rate
        return timedelta(hours=72)  # Back off
    elif action_rate > 0.5:  # >50% action rate
        return timedelta(hours=12)  # More aggressive
    else:
        return timedelta(hours=24)  # Default
```

### Formatter

#### Personalized Digest
**Current:** Same format for all digests
**Improvement:** Learn preferred sections

```python
def generate_personalized_digest(user_preferences):
    sections = []

    # Always include top pick
    sections.append(format_top_pick())

    # Order remaining sections by user preference
    section_order = user_preferences.get("digest_sections", [
        "expiring", "stacked", "hotels", "portal_only"
    ])

    for section in section_order:
        if section == "expiring" and user_preferences.get("show_expiring", True):
            sections.append(format_expiring_section())
        elif section == "stacked":
            sections.append(format_stacked_section())
        # ... etc

    return combine_sections(sections)
```

#### Rich Email Previews
**Current:** Basic subject line
**Improvement:** Optimized preview text

```python
def generate_email_preview(deals):
    """Generate preview text optimized for email clients."""
    top_deal = deals[0]

    # Most email clients show ~100 chars of preview
    preview = f"{top_deal.merchant}: {top_deal.score:.0f} LP/$ "
    preview += f"(${top_deal.min_spend:.0f} → {top_deal.total_miles:,} LPs)"

    if len(deals) > 1:
        preview += f" + {len(deals)-1} more deals"

    return preview[:100]
```

---

## 4. Database Improvements

### Query Optimization

#### Add Missing Indexes
```sql
-- Frequently filtered columns
CREATE INDEX IF NOT EXISTS idx_offers_expires ON simplymiles_offers(expires_at);
CREATE INDEX IF NOT EXISTS idx_deals_city_date ON hotel_deals(city, check_in);
CREATE INDEX IF NOT EXISTS idx_matrix_city_dow ON hotel_yield_matrix(city, day_of_week);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_stacked_score_yield
    ON stacked_opportunities(deal_score DESC, combined_yield DESC);
```

#### Query Result Caching
```python
from functools import lru_cache
from datetime import datetime

class CachedDatabase:
    def __init__(self, db, cache_ttl_seconds=300):
        self.db = db
        self.ttl = cache_ttl_seconds
        self._cache = {}
        self._cache_times = {}

    def get_stacked_opportunities(self, min_yield=5.0):
        cache_key = f"stacked_{min_yield}"

        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        result = self.db.get_stacked_opportunities(min_yield)
        self._cache[cache_key] = result
        self._cache_times[cache_key] = datetime.now()

        return result

    def _is_cache_valid(self, key):
        if key not in self._cache_times:
            return False
        age = (datetime.now() - self._cache_times[key]).seconds
        return age < self.ttl
```

### Data Retention

#### Automatic Cleanup
```python
def cleanup_old_data(days_to_keep: int = 30):
    """Remove old data to keep database size manageable."""
    db = get_database()
    cutoff = (datetime.now() - timedelta(days=days_to_keep)).isoformat()

    with db.get_connection() as conn:
        # Clean old hotel deals (keep matrix)
        conn.execute("DELETE FROM hotel_deals WHERE scraped_at < ?", (cutoff,))

        # Clean old yield history
        conn.execute("DELETE FROM hotel_yield_history WHERE scraped_at < ?", (cutoff,))

        # Clean old alert history (keep 90 days)
        cutoff_90 = (datetime.now() - timedelta(days=90)).isoformat()
        conn.execute("DELETE FROM alert_history WHERE sent_at < ?", (cutoff_90,))

        # Vacuum to reclaim space
        conn.execute("VACUUM")
```

---

## 5. Testing Improvements

### Unit Test Coverage

#### Current Gaps
```bash
# Check coverage
pytest --cov=core --cov=alerts --cov=scrapers --cov-report=html

# Target: 90% coverage on core modules
```

#### Tests to Add
```python
# tests/test_stack_detector.py - expand
class TestFuzzyMatching:
    def test_exact_match(self):
        """Exact merchant names should match at 100%."""

    def test_case_insensitive(self):
        """Matching should ignore case."""

    def test_alias_application(self):
        """Configured aliases should be applied."""

    def test_near_threshold(self):
        """84% match should not match, 85% should."""

# tests/test_hotels.py - new
class TestAdaptiveDates:
    def test_uses_matrix_data(self):
        """Should prioritize high-yield combinations."""

    def test_fallback_without_matrix(self):
        """Should use default dates if no matrix data."""

# tests/test_alerts.py - expand
class TestDeduplication:
    def test_cooldown_respected(self):
        """Same deal shouldn't alert within cooldown."""

    def test_improvement_triggers_alert(self):
        """20%+ improvement should bypass cooldown."""
```

### Integration Tests

#### End-to-End Pipeline Test
```python
# tests/test_integration.py
@pytest.mark.integration
async def test_full_pipeline():
    """Test complete scrape → detect → alert flow."""
    # 1. Run scrapers with mock data
    # 2. Verify database populated
    # 3. Run stack detection
    # 4. Verify opportunities created
    # 5. Run evaluator
    # 6. Verify alerts would be sent
```

#### Scraper Contract Tests
```python
@pytest.mark.integration
async def test_simplymiles_api_contract():
    """Verify SimplyMiles API returns expected structure."""
    # This catches if the API changes
    result = await fetch_simplymiles_offers()

    assert "offers" in result
    assert len(result["offers"]) > 0

    offer = result["offers"][0]
    assert "merchant" in offer
    assert "miles" in offer or "lp" in offer
```

### Load Testing

#### Stress Test Database
```python
def test_database_under_load():
    """Ensure DB handles realistic data volumes."""
    db = get_database()

    # Insert 10,000 hotel deals
    for i in range(10000):
        db.insert_hotel_deal(...)

    # Query should still be fast
    start = time.time()
    deals = db.get_top_hotel_deals(limit=100)
    elapsed = time.time() - start

    assert elapsed < 0.5  # Should complete in <500ms
```

---

## 6. Code Quality Improvements

### Type Hints
```python
# Before
def get_best_deals(min_yield, limit):
    ...

# After
def get_best_deals(
    min_yield: float = 10.0,
    limit: int = 50
) -> list[dict[str, Any]]:
    ...
```

### Dataclasses for Domain Objects
```python
# Before: Dict everywhere
deal = {"merchant": "Amazon", "score": 15.5, ...}

# After: Typed dataclasses
@dataclass
class StackedDeal:
    merchant_name: str
    portal_rate: float
    simplymiles_type: Literal["flat_bonus", "per_dollar"]
    simplymiles_amount: int
    min_spend: float
    total_miles: int
    base_yield: float
    deal_score: float
    expires_at: Optional[datetime] = None
```

### Error Handling
```python
# Define specific exceptions
class ScraperError(Exception):
    """Base exception for scraper errors."""

class SessionExpiredError(ScraperError):
    """Authentication session has expired."""

class RateLimitError(ScraperError):
    """Rate limit hit, need to back off."""

class ParseError(ScraperError):
    """Failed to parse response data."""

# Use in scrapers
async def scrape_simplymiles():
    try:
        response = await fetch_offers()
    except httpx.TimeoutError:
        raise ScraperError("Timeout fetching offers")

    if response.status_code == 401:
        raise SessionExpiredError("Session expired")
    elif response.status_code == 429:
        raise RateLimitError("Rate limited")

    try:
        return parse_offers(response.json())
    except (KeyError, ValueError) as e:
        raise ParseError(f"Failed to parse: {e}")
```

---

## 7. Documentation Improvements

### Inline Documentation
```python
def calculate_deal_score(
    base_yield: float,
    min_spend: float,
    expires_at: Optional[datetime] = None,
    is_austin: bool = False
) -> float:
    """
    Calculate final deal score with modifiers applied.

    The score represents the adjusted value of a deal, accounting for:
    - Commitment level (lower spend = higher score)
    - Urgency (expiring soon = higher score)
    - Location preference (Austin = bonus)

    Args:
        base_yield: Raw LP/$ yield (total_miles / min_spend)
        min_spend: Minimum purchase required in dollars
        expires_at: When the offer expires (optional)
        is_austin: Whether this is an Austin-local deal

    Returns:
        Adjusted score as float. Higher is better.
        Typical range: 5-50 LP/$

    Examples:
        >>> calculate_deal_score(10.0, 25.0)  # Low spend
        14.0  # 10 * 1.4 (low commitment bonus)

        >>> calculate_deal_score(10.0, 25.0, datetime.now() + timedelta(hours=24))
        16.8  # 10 * 1.4 * 1.2 (urgency bonus)
    """
```

### Architecture Decision Records
```markdown
# docs/adr/001-sqlite-over-postgres.md

## Context
Need to choose a database for storing deal data.

## Decision
Use SQLite instead of PostgreSQL.

## Rationale
- Single user application
- No concurrent write requirements
- Simpler deployment (no DB server)
- Easy backup (single file)
- Good enough performance for our scale

## Consequences
- Cannot easily add multi-user support
- No remote DB access without extra tooling
- Limited to ~1GB practical size
```

---

## Priority Matrix

| Improvement | Effort | Impact | Priority |
|-------------|--------|--------|----------|
| Add missing indexes | Low | High | 1 |
| Type hints throughout | Medium | Medium | 2 |
| Expand test coverage | Medium | High | 3 |
| Rate change tracking | Low | Medium | 4 |
| Smart alert batching | Low | Medium | 5 |
| Session auto-refresh | Medium | High | 6 |
| Parallel hotel scraping | Medium | Medium | 7 |
| Dynamic thresholds | Medium | Medium | 8 |

---

*Last updated: 2024-12-29*
