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
│  - Calls save_to_gsheet() to persist data                       │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Product Hunt    │  │  src/utils/      │  │  Google Sheets   │
│  Weekly Page     │  │  parsing.py      │  │  API             │
│  (HTML Source)   │  │  (BeautifulSoup) │  │  (gspread)       │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

## Component Breakdown

### `src/` - Core Application
| File | Responsibility |
|------|----------------|
| `main.py` | Entry point, URL construction, orchestration, Google Sheets integration |
| `config.py` | pydantic-settings configuration from environment variables |
| `models.py` | Pydantic `Product` model with validation |
| `utils/parsing.py` | BeautifulSoup HTML parsing, product extraction |

### `backfill/` - Historical Data
| File | Responsibility |
|------|----------------|
| `main.py` | Iterates through past weeks, reuses core functions |
| `config/settings.py` | `WEEKS_BACK = 10` constant |

### `tests/` - Test Suite
| File | Coverage |
|------|----------|
| `test_main.py` | Google Sheets integration, fetch_html retry |
| `test_parsing.py` | HTML parsing logic, edge cases |
| `test_config.py` | Configuration loading |
| `test_backfill.py` | Backfill logic |

## Data Flow

```
1. TRIGGER
   GitHub Actions cron (0 12 * * 0) OR manual dispatch

2. URL CONSTRUCTION
   get_current_week_url() → https://producthunt.com/leaderboard/weekly/2025/1

3. HTML FETCH
   fetch_html(url) with tenacity retry (3 attempts, exponential backoff)

4. PARSING
   parse_products(html, limit=10) → List[Product]
   - Find all <a href="/products/..."> links
   - Extract name, description from DOM traversal
   - Extract upvotes (max number in button elements)
   - Deduplicate by slug

5. PERSISTENCE
   save_to_gsheet(products) with retry
   - Append rows to "Weekly Top 10" tab
   - Sort by Date (desc), Rank (asc)
```

## Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Language | Python 3.10+ | Type hints, async-ready |
| HTML Parsing | BeautifulSoup4 | Robust, well-documented |
| Data Validation | Pydantic | Type safety, serialization |
| Configuration | pydantic-settings | .env support, validation |
| Retry Logic | tenacity | Configurable backoff |
| Sheets API | gspread | Pythonic Google Sheets |
| Testing | pytest | Standard, mocking support |
| Linting | ruff | Fast, comprehensive |
| Type Checking | mypy (strict) | Catch bugs early |

## Key Design Decisions

### 1. Upvote Extraction Strategy
**Decision**: Take `max()` of all numbers found in button elements
**Rationale**: Distinguishes upvotes from comment counts (upvotes > comments)

### 2. URL Structure
**Decision**: Use ISO week numbers for URL construction
**Rationale**: Product Hunt uses `/{year}/{week}` format, matches ISO standard

### 3. Deduplication
**Decision**: Track seen slugs in a set during parsing
**Rationale**: Same product may appear multiple times in DOM

### 4. Retry Logic
**Decision**: 3 attempts with exponential backoff (4s → 60s)
**Rationale**: Handle transient network failures gracefully

### 5. Environment Variable Prefix
**Decision**: Use `PH_` prefix for secrets (`PH_GSHEET_ID`, `PH_GDRIVE_API_KEY_JSON`)
**Rationale**: Avoid conflicts with other projects using Google Sheets

## Integration Points

### Product Hunt (Source)
- URL: `https://www.producthunt.com/leaderboard/weekly/{year}/{week}`
- Method: HTML scraping (no API key required)
- Rate limiting: 2-second delay between requests in backfill

### Google Sheets (Destination)
- Authentication: Service account JSON (via `PH_GDRIVE_API_KEY_JSON`)
- Sheet ID: `PH_GSHEET_ID`
- Tab: "Weekly Top 10"
- Format: Date, Rank, Name, Description, Upvotes, URL

## Failure Modes

| Failure | Detection | Handling |
|---------|-----------|----------|
| Network timeout | urllib exception | Retry with backoff (3x) |
| HTML structure change | Empty product list | Log warning, no data saved |
| Google Sheets API error | gspread exception | Retry with backoff (3x) |
| Invalid credentials | Auth exception | Log error, exit gracefully |
| Rate limiting | HTTP 429 | Exponential backoff |

## Scaling Considerations
- Current load: 1 request/week (minimal)
- Backfill: 10 requests with 2s delays (20s total)
- Google Sheets: 10 rows/week append (well within limits)
- No database required at current scale
