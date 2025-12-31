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
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┬───────────────┐
                ▼               ▼               ▼               ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Product Hunt    │  │  src/utils/      │  │  src/analysis/   │  │  src/db/         │
│  Weekly Page     │  │  parsing.py      │  │  grok_analyzer   │  │  supabase_client │
│  (HTML Source)   │  │  (BeautifulSoup) │  │  (Grok AI)       │  │  (Supabase)      │
└──────────────────┘  └──────────────────┘  └──────────────────┘  └──────────────────┘
```

## Component Breakdown

### `src/` - Core Application
| File | Responsibility |
|------|----------------|
| `main.py` | Entry point, URL construction, orchestration, pipeline flow |
| `config.py` | pydantic-settings configuration from environment variables |
| `models.py` | Pydantic `Product` model with validation |
| `utils/parsing.py` | BeautifulSoup HTML parsing, product extraction |
| `analysis/grok_analyzer.py` | Grok AI client for categorization and insights |
| `analysis/prompts.py` | AI prompt templates (product, batch, weekly) |
| `db/supabase_client.py` | Supabase integration with upsert logic |
| `db/models.py` | Database models (EnrichedProduct, PHWeeklyInsights) |

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
              pricing_model, innovation_score, market_fit_score

7. PERSISTENCE
   PHSupabaseClient.save_products(enriched_products)
   - Upsert to product_hunt.products table
   - Conflict key: (week_date, rank)

8. INSIGHTS GENERATION (optional)
   PHGrokAnalyzer.generate_weekly_insights(products)
   PHSupabaseClient.save_insights(insights)
   - Weekly trends, sentiment, notable launches
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
    maker_info JSONB,
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
- Tables: `products`, `weekly_insights`

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

## Scaling Considerations

**Current scale is minimal:**
- 1 request/week to Product Hunt
- 1 Grok API call/week (batch mode)
- 10 rows/week to Supabase
- Backfill: 10 requests with 3s delays

**If scaling needed:**
- Supabase can handle millions of rows
- Grok batch mode already optimized
- Could add Redis cache for HTML during development
- Could parallelize backfill (currently sequential for rate limiting)
