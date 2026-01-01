# Established Patterns

## HTTP Fetching with Retry

We use `src/utils/http.fetch_html()` for web scraping with automatic retry.

**Location:** `src/utils/http.py`

**Example:**
```python
from src.utils.http import fetch_html

# Basic usage - defaults to browser User-Agent, 20s timeout
html = fetch_html("https://example.com/page")

# Custom headers
html = fetch_html(
    "https://example.com/api",
    headers={"Accept": "application/json"},
    timeout=30
)
```

**When to use:**
- Scraping any web page
- Future multi-platform scrapers (HN, Reddit, etc.)
- Any HTTP GET with retry needs

**Features:**
- 3 retry attempts with exponential backoff
- Browser User-Agent by default
- Configurable timeout and headers

---

## AI Enrichment (Grok)

We use `PHGrokAnalyzer` for AI-powered product analysis.

**Location:** `src/analysis/grok_analyzer.py`

**Example:**
```python
from src.analysis import PHGrokAnalyzer

analyzer = PHGrokAnalyzer(api_key=settings.xai_api_key)

# Batch enrichment (preferred - 1 API call)
enriched = analyzer.enrich_products_batch(
    products=products,
    week_date=week_date,
    week_number=week,
    year=year
)

# Weekly insights
insights = analyzer.generate_weekly_insights(
    products=enriched,
    week_date=week_date,
    week_number=week,
    year=year
)
```

**When to use:**
- Categorizing products
- Scoring innovation/market fit
- Generating weekly trends

---

## Database Operations (Supabase)

We use `PHSupabaseClient` for all database operations.

**Location:** `src/db/supabase_client.py`

**Example:**
```python
from src.db import PHSupabaseClient

db = PHSupabaseClient(url, key)

# Check if data exists
if db.week_exists(week_date):
    return  # Skip duplicate

# Save products (upsert)
saved = db.save_products(enriched_products)

# Save insights
db.save_insights(insights)
```

**When to use:**
- Any Supabase read/write
- Schema: `product_hunt`

---

## Data Models (Pydantic)

All data structures use Pydantic models.

**Locations:**
- `src/models.py` - Raw scraped data (`Product`)
- `src/db/models.py` - Database models (`EnrichedProduct`, `PHWeeklyInsights`)

**Example:**
```python
from src.models import Product
from src.db.models import EnrichedProduct

# Raw product (from scraping)
product = Product(
    rank=1,
    name="Cool App",
    url="https://...",
    description="...",
    upvotes=500
)

# Enriched product (from AI + metadata)
enriched = EnrichedProduct(
    week_date=date.today(),
    week_number=1,
    year=2025,
    **product.model_dump(),
    category="AI",
    innovation_score=8.5
)

# Convert to DB format
data = enriched.to_db_dict()
```

---

## Configuration (pydantic-settings)

All config is loaded from environment via `src/config.settings`.

**Example:**
```python
from src.config import settings

# Access settings
url = settings.supabase_url
key = settings.supabase_key
model = settings.grok_model  # Default: "grok-4-1-fast-reasoning"
```

**Environment variables:**
- `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` - Database
- `GROK_API_KEY` - AI enrichment
- `RESEND_API_KEY`, `EMAIL_FROM`, `EMAIL_TO` - Notifications

---

## Email Notifications

We use Resend for email delivery.

**Location:** `src/notifications/email_digest.py`

**Example:**
```python
from src.notifications import send_weekly_digest

success = send_weekly_digest(
    products=enriched,
    insights=insights,
    week_date=week_date,
    solo_pick=solo_pick
)
```

---

## Analytics Aggregation

Category trends and special picks.

**Location:** `src/analytics/aggregations.py`

**Example:**
```python
from src.analytics.aggregations import aggregate_category_trends, get_solo_builder_pick

# Save category stats to Supabase
trends = aggregate_category_trends(enriched, week_date, db.client)

# Find best product for solo builders
pick = get_solo_builder_pick(enriched)
```

---

## Module Composition

The main pipeline composes all modules:

```
fetch_html() → parse_products() → PHGrokAnalyzer → PHSupabaseClient → send_weekly_digest()
                                        ↓
                              aggregate_category_trends()
```

Each module can be used independently or composed differently for new features.
