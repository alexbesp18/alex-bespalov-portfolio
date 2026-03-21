# Established Patterns

This document describes the patterns used throughout the AA Points Monitor codebase.
Follow these patterns when adding new features.

---

## Singleton Pattern (Database & Settings)

We use singletons for resources that should be shared across the application.

### Database Access
```python
from core.database import get_database

db = get_database()  # Returns singleton instance
offers = db.get_active_simplymiles_offers()
```

**When to use:** Always use `get_database()` instead of creating `Database()` directly.

### Settings Access
```python
from config.settings import get_settings

settings = get_settings()  # Returns singleton instance
threshold = settings.thresholds.stack_immediate_alert
```

**When to use:** Always use `get_settings()` for configuration values.

---

## Async Scraping Pattern

All scrapers use async/await for I/O operations.

### Basic Structure
```python
import asyncio
import httpx
from core.database import get_database

async def scrape_something():
    db = get_database()

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        data = response.json()

    # Process and store
    db.insert_something(data)
    return results

def run_scraper():
    return asyncio.run(scrape_something())
```

### With Retry Logic (New Pattern)
```python
from core.http_client import fetch_json

async def scrape_something():
    data = await fetch_json(
        url,
        max_retries=3,
        retry_delay=2.0,
    )
    return data
```

**When to use:** Use `fetch_json()` for simple JSON APIs. Use raw `httpx.AsyncClient` when you need more control (cookies, complex auth).

---

## Error Handling Pattern

Use the custom exception hierarchy from `core/exceptions.py`.

### Scraper Errors
```python
from core.exceptions import (
    ScraperError,
    SessionExpiredError,
    ParseError,
    NoDataError,
)

async def scrape_offers():
    try:
        response = await client.get(url)
        if response.status_code == 401:
            raise SessionExpiredError("simplymiles")
        if not response.json().get('offers'):
            raise NoDataError("simplymiles")
    except Exception as e:
        raise ParseError("simplymiles", str(e))
```

### HTTP Errors
```python
from core.exceptions import (
    HttpClientError,
    RateLimitError,
    AuthenticationError,
)

try:
    data = await fetch_json(url)
except RateLimitError as e:
    logger.warning(f"Rate limited, retry after {e.retry_after}s")
except AuthenticationError:
    logger.error("Session expired, need re-authentication")
except HttpClientError as e:
    logger.error(f"HTTP error: {e}")
```

**When to use:** Always catch specific exceptions before general ones. Log errors with context.

---

## Data Normalization Pattern

Normalize merchant names for matching across data sources.

```python
from core.normalizer import normalize_merchant, find_best_match

# Normalize a merchant name
normalized = normalize_merchant("Kindle and Kindle Unlimited")
# Returns: "amazon kindle" (using alias mapping)

# Find best match with fuzzy matching
portal_merchants = ["amazon", "uber eats", "best buy"]
match = find_best_match(
    normalized,
    portal_merchants,
    threshold=85  # Default from settings
)
# Returns: ("amazon", 92) or None if no match
```

**When to use:** Always normalize before storing or matching merchant names.

---

## Scoring Pattern

All deals use a consistent scoring formula.

### Basic Yield
```python
base_yield = total_miles / min_spend
```

### With Modifiers
```python
from core.scorer import calculate_deal_score, StackedDeal

stacked = StackedDeal(
    merchant_name="Amazon",
    portal_rate=10.0,  # mi/$
    simplymiles_type="flat_bonus",
    simplymiles_amount=135,
    simplymiles_min_spend=5.0,
    simplymiles_expires="2025-01-15T00:00:00"
)

# Automatically applies:
# - Low commitment bonus (+40% for <$50)
# - Urgency bonus (+20% if expiring <48h)
# - etc.
```

**When to use:** Always use `StackedDeal` or `calculate_deal_score()` for scoring. Never calculate manually.

---

## Alert Deduplication Pattern

Prevent alert spam with cooldown periods.

```python
from core.database import get_database

db = get_database()

# Check if recently alerted
if db.was_recently_alerted(
    deal_id=merchant_name,
    deal_type="stack",
    cooldown_hours=24
):
    return  # Skip this alert

# Only override cooldown if significant improvement
if was_recently_alerted and improvement < 0.20:  # 20% threshold
    return  # Skip unless 20% better than last alert
```

**When to use:** Always check before sending immediate alerts. Digest alerts don't need deduplication.

---

## Health Monitoring Pattern

Track scraper health for alerting.

```python
from core.database import get_database

db = get_database()

# Record successful run
db.record_scraper_run(
    scraper_name="simplymiles",
    status="success",
    records_found=len(offers),
    duration_seconds=elapsed
)

# Record failure
db.record_scraper_run(
    scraper_name="simplymiles",
    status="failure",
    error_message=str(error)
)

# Check health
failures = db.get_consecutive_failures("simplymiles")
if failures >= 3:
    send_health_alert()
```

**When to use:** Record every scraper run, whether success or failure.

---

## Testing Pattern

Use pytest with async support.

### Basic Test
```python
import pytest
from core.scorer import calculate_deal_score

def test_deal_score_calculation():
    score = calculate_deal_score(base_yield=20.0, min_spend=50)
    assert score == pytest.approx(28.0)  # 20 * 1.4 (low commitment bonus)
```

### Async Test
```python
import pytest

@pytest.mark.asyncio
async def test_fetch_offers():
    offers = await fetch_offers()
    assert len(offers) > 0
```

### Fixture Pattern
```python
@pytest.fixture
def sample_offer():
    return {
        'merchant_name': 'Test Merchant',
        'miles_amount': 100,
        'min_spend': 10.0,
    }

def test_with_fixture(sample_offer):
    assert sample_offer['miles_amount'] == 100
```

**When to use:** Tests go in `tests/`. Use `pytest.approx()` for float comparisons. Use fixtures for shared test data.

---

## Logging Pattern

Use module-level loggers with consistent formatting.

```python
import logging

logger = logging.getLogger(__name__)

def some_function():
    logger.info(f"Processing {count} items")
    logger.debug(f"Details: {data}")
    logger.warning(f"Unusual condition: {condition}")
    logger.error(f"Failed to process: {error}")
```

**Log Levels:**
- `DEBUG`: Detailed info for debugging
- `INFO`: Normal operation milestones
- `WARNING`: Unusual but recoverable conditions
- `ERROR`: Failures that need attention

**When to use:** Use `logging.getLogger(__name__)` at module level. Never use `print()` in production code.

---

## Adding New Features

When adding a new scraper or data source:

1. **Create scraper in `scrapers/`**
   - Follow async pattern
   - Use `httpx` for HTTP
   - Record health status

2. **Add database methods in `core/database.py`**
   - Follow existing `insert_X`, `get_X`, `clear_X` pattern
   - Add appropriate indexes

3. **Add normalization in `core/normalizer.py`** (if needed)
   - Add merchant aliases
   - Test matching accuracy

4. **Add scoring in `core/scorer.py`** (if needed)
   - Create deal type class if complex
   - Follow modifier pattern

5. **Add alert formatting in `alerts/formatter.py`** (if needed)
   - Follow HTML + text dual format
   - Use consistent styling

6. **Add tests in `tests/`**
   - Unit tests for scoring
   - Integration tests for data flow

---

*Last updated: 2024-12-29*
