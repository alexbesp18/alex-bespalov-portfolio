# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Actions (Trigger)                     │
│                    Sundays 12 PM UTC / Manual                    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         src/main.py                              │
│                    (Orchestration Layer)                         │
│  - Constructs URL for current ISO week                          │
│  - Calls fetch_html() with retry logic                          │
│  - Calls parse_products() from utils/parsing.py                 │
│  - Calls PHGrokAnalyzer for AI enrichment                       │
│  - Calls PHSupabaseClient to persist data                       │
│  - Calls aggregate_category_trends() for analytics              │
│  - Calls get_solo_builder_pick() for entrepreneur insights      │
│  - Calls send_weekly_digest() for email delivery                │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────┬───────┼───────┬───────────────┬───────────────┐
        ▼               ▼       ▼       ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Product Hunt │ │ src/utils/   │ │ src/analysis/│ │ src/db/      │ │ src/notif/   │
│ Weekly Page  │ │ parsing.py   │ │ grok_analyzer│ │ supabase_cli │ │ email_digest │
│ (HTML)       │ │ (BeautifulSp)│ │ (Grok AI)    │ │ (Supabase)   │ │ (Resend)     │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
                                                          │
                                          ┌───────────────┼───────────────┐
                                          ▼               ▼               ▼
                                   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
                                   │  products    │ │weekly_insights│ │category_trends│
                                   │  table       │ │  table       │ │  table       │
                                   └──────────────┘ └──────────────┘ └──────────────┘
```

## Component Breakdown

### `src/` - Core Application
| File | Responsibility |
|------|----------------|
| `main.py` | Entry point, URL construction, orchestration, pipeline flow |
| `config.py` | pydantic-settings configuration from environment variables |
| `models.py` | Pydantic `Product` model with validation |
| `utils/http.py` | HTTP fetching with tenacity retry logic |
| `utils/parsing.py` | BeautifulSoup HTML parsing, product extraction |
| `analysis/grok_analyzer.py` | Grok AI client for categorization and insights |
| `analysis/prompts.py` | AI prompt templates (product, batch, weekly) |
| `analytics/aggregations.py` | Category trend aggregation, solo builder pick algorithm |
| `db/supabase_client.py` | Supabase integration with upsert logic |
| `db/models.py` | Database models (EnrichedProduct, PHWeeklyInsights) |
| `notifications/email_digest.py` | Weekly digest email formatting and delivery via Resend |

### `backfill/` - Historical Data
| File | Responsibility |
|------|----------------|
| `main.py` | Iterates through past weeks, reuses core `run_pipeline()` |
| `config/settings.py` | `WEEKS_BACK = 10` constant |

### `tests/` - Test Suite
| File | Coverage |
|------|----------|
| `test_main.py` | Pipeline orchestration, week calculation, fetch retry |
| `test_parsing.py` | HTML parsing logic, edge cases |
| `test_config.py` | Configuration loading |
| `test_db.py` | Database models, serialization |
| `test_backfill.py` | Backfill logic, year boundaries |
| `test_analysis.py` | Grok API calls, error handling |

## Data Flow

```
1. TRIGGER
   GitHub Actions cron (0 12 * * 0) OR manual dispatch

2. URL CONSTRUCTION
   get_current_week_info() → (url, week_number, year, week_date)
   URL: https://producthunt.com/leaderboard/weekly/{year}/{week}

3. DUPLICATE CHECK
   PHSupabaseClient.week_exists(week_date)
   → Skip if already scraped

4. HTML FETCH
   fetch_html(url) with tenacity retry (3 attempts, exponential backoff)

5. PARSING
   parse_products(html, limit=10) → List[Product]
   - Find all <a href="/products/..."> links
   - Extract name, description from DOM traversal
   - Extract upvotes (max number in button elements)
   - Deduplicate by slug

6. AI ENRICHMENT (optional, if GROK_API_KEY set)
   PHGrokAnalyzer.enrich_products_batch(products)
   - Single API call for all 10 products
   - Returns: category, subcategory, target_audience, tech_stack,
              pricing_model, innovation_score, market_fit_score,
              maker_info (solo_friendly, build_complexity, what_it_does, etc.)

7. PERSISTENCE
   PHSupabaseClient.save_products(enriched_products)
   - Upsert to product_hunt.products table
   - Conflict key: (week_date, rank)

8. INSIGHTS GENERATION (optional)
   PHGrokAnalyzer.generate_weekly_insights(products)
   PHSupabaseClient.save_insights(insights)
   - Weekly trends, sentiment, notable launches

9. CATEGORY ANALYTICS
   aggregate_category_trends(products, week_date, client)
   - Group products by category
   - Calculate avg upvotes, avg scores, top product
   - Save to product_hunt.category_trends table

10. SOLO BUILDER PICK
    get_solo_builder_pick(products)
    - Filter for solo_friendly=true AND build_complexity in [weekend, month]
    - Score by upvotes + innovation_score
    - Return best candidate for solo entrepreneurs

11. EMAIL DIGEST
    send_weekly_digest(products, insights, week_date, solo_pick)
    - Build HTML email with product rankings
    - Include weekly insights section
    - Include Solo Builder Pick section
    - Send via Resend API
```

## Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Language | Python 3.10+ | Type hints, async-ready |
| HTML Parsing | BeautifulSoup4 | Robust, well-documented |
| Data Validation | Pydantic | Type safety, serialization |
| Configuration | pydantic-settings | .env support, validation |
| Retry Logic | tenacity | Configurable backoff |
| Database | Supabase | Structured data, SQL queries, RLS |
| AI Enrichment | Grok (xAI) | Fast, JSON mode support |
| HTTP Client | requests | Simple, reliable |
| Email Delivery | Resend | Simple API, good deliverability |
| Testing | pytest | Standard, mocking support |
| Linting | ruff | Fast, comprehensive |
| Type Checking | mypy (strict) | Catch bugs early |

## Key Design Decisions

### 1. Supabase over Google Sheets
**Decision**: Migrate from gspread/Google Sheets to Supabase
**Rationale**:
- Structured schema with proper data types
- SQL queries for analytics
- Better for AI enrichment (JSONB fields)
- No row limits or API quota issues
- Easier integration with future dashboards

### 2. Grok AI for Enrichment
**Decision**: Add optional Grok AI categorization
**Rationale**:
- Automatic product categorization
- Innovation/market-fit scoring
- Weekly trend insights
- Graceful fallback if unavailable
- Special fields for entrepreneurs (solo_friendly, build_complexity)

### 3. Batch Enrichment
**Decision**: Single API call for all 10 products
**Rationale**:
- More efficient (1 call vs 10)
- Lower latency and cost
- Consistent categorization across products

### 4. Upsert Strategy
**Decision**: Use Supabase upsert with `on_conflict="week_date,rank"`
**Rationale**:
- Handles re-runs gracefully
- No duplicate data
- Safe to retry on failure

### 5. Upvote Extraction Strategy
**Decision**: Take `max()` of all numbers found in button elements
**Rationale**: Distinguishes upvotes from comment counts (upvotes > comments)

### 6. URL Structure
**Decision**: Use ISO week numbers for URL construction
**Rationale**: Product Hunt uses `/{year}/{week}` format, matches ISO standard

### 7. Deduplication
**Decision**: Track seen slugs in a set during parsing
**Rationale**: Same product may appear multiple times in DOM

### 8. Email Digest with Solo Builder Pick
**Decision**: Add special section for entrepreneur-friendly products
**Rationale**:
- Target audience includes solo builders
- `what_it_does` field provides clearer descriptions than marketing copy
- Build complexity and monetization hints help with project inspiration

## Supabase Schema

**Project**: `rxsmmrmahnvaarwsngtb`
**Schema**: `product_hunt`

### `products` Table
```sql
CREATE TABLE product_hunt.products (
    week_date DATE NOT NULL,
    rank INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    year INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    upvotes INTEGER DEFAULT 0,
    url TEXT NOT NULL,
    category TEXT,
    subcategory TEXT,
    target_audience TEXT,
    tech_stack TEXT[],
    maker_info JSONB,           -- solo_friendly, build_complexity, what_it_does, etc.
    pricing_model TEXT,
    innovation_score FLOAT,
    market_fit_score FLOAT,
    analyzed_at TIMESTAMPTZ,
    PRIMARY KEY (week_date, rank)
);
```

### `weekly_insights` Table
```sql
CREATE TABLE product_hunt.weekly_insights (
    week_date DATE PRIMARY KEY,
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    top_trends TEXT[],
    notable_launches TEXT,
    category_breakdown JSONB,
    avg_upvotes FLOAT,
    sentiment TEXT,
    full_analysis JSONB
);
```

### `category_trends` Table
```sql
CREATE TABLE product_hunt.category_trends (
    week_date DATE NOT NULL,
    category TEXT NOT NULL,
    product_count INTEGER,
    avg_upvotes FLOAT,
    avg_innovation_score FLOAT,
    avg_market_fit_score FLOAT,
    top_product TEXT,
    top_product_upvotes INTEGER,
    PRIMARY KEY (week_date, category)
);
```

## Integration Points

### Product Hunt (Source)
- URL: `https://www.producthunt.com/leaderboard/weekly/{year}/{week}`
- Method: HTML scraping (no API key required)
- Rate limiting: 3-second delay between requests in backfill

### Grok AI (Enrichment)
- API: `https://api.x.ai/v1/chat/completions`
- Model: `grok-4-1-fast-reasoning`
- Auth: Bearer token (`GROK_API_KEY`)
- Response: JSON mode enabled

### Supabase (Storage)
- Project URL: `SUPABASE_URL`
- Auth: Service role key (`SUPABASE_SERVICE_KEY`)
- Schema: `product_hunt`
- Tables: `products`, `weekly_insights`, `category_trends`

### Resend (Email)
- API: `https://api.resend.com/emails`
- Auth: API key (`RESEND_API_KEY`)
- From: `EMAIL_FROM`
- To: `EMAIL_TO` (comma-separated)

### GitHub Actions (Orchestration)
- Weekly: Sundays 12 PM UTC
- CI: On push/PR to project directory
- Backfill: Manual trigger

## Failure Modes

| Failure | Detection | Handling |
|---------|-----------|----------|
| Network timeout | urllib exception | Retry with backoff (3x) |
| Empty product list | parse_products returns [] | Log warning, return False |
| Grok API error | HTTP 4xx/5xx | Save raw products without enrichment |
| Grok rate limit | HTTP 429 | Log warning, skip enrichment |
| Supabase error | Exception on upsert | Log error, raise (workflow fails) |
| Invalid credentials | Auth exception | Log error, exit gracefully |
| Duplicate week | week_exists() returns True | Skip if skip_if_exists=True |
| Resend API error | Exception on send | Log warning, continue (email optional) |

## Scaling Considerations

**Current scale is minimal:**
- 1 request/week to Product Hunt
- 1 Grok API call/week (batch mode)
- 10 rows/week to Supabase (+ 1 insight + N category trends)
- 1 email/week via Resend
- Backfill: 10 requests with 3s delays

**If scaling needed:**
- Supabase can handle millions of rows
- Grok batch mode already optimized
- Could add Redis cache for HTML during development
- Could parallelize backfill (currently sequential for rate limiting)
- Resend supports high volume without changes
