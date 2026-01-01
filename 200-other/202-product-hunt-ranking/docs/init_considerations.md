# Init Considerations

## Quick Start for New Agents/Developers

### Start Here
1. Read `README.md` for project overview
2. Read `docs/architecture.md` for system design
3. Check `docs/checkpoint.md` for current state
4. Review `CLAUDE.md` for commands and module reference

### Key Files (in order of importance)
1. `src/main.py` - Entry point, `run_pipeline()` orchestrates everything
2. `src/utils/parsing.py` - Core HTML scraping logic
3. `src/analysis/grok_analyzer.py` - AI enrichment layer
4. `src/analytics/aggregations.py` - Category trends + Solo Builder Pick
5. `src/notifications/email_digest.py` - Weekly digest email
6. `src/db/supabase_client.py` - Database persistence
7. `src/config.py` - Environment configuration

## Mental Model

```
Product Hunt HTML → BeautifulSoup → Pydantic Models → Grok AI → Supabase → Email
```

This is a **data pipeline**, not a web app. It runs once per week via GitHub Actions:
1. Fetches HTML from Product Hunt leaderboard
2. Parses top 10 products with BeautifulSoup
3. Enriches with Grok AI (category, scores, insights, entrepreneur data)
4. Saves to Supabase with upsert strategy (3 tables)
5. Aggregates category trends
6. Identifies Solo Builder Pick
7. Sends weekly digest email via Resend

**Graceful degradation**: If Grok is unavailable, raw products are saved without enrichment. If Resend fails, pipeline still succeeds.

## Common Gotchas

### 1. Environment Variables (No Prefix!)
Variables no longer use `PH_` prefix:
```bash
SUPABASE_URL            # Not PH_SUPABASE_URL
SUPABASE_SERVICE_KEY    # Not PH_SUPABASE_SERVICE_KEY
GROK_API_KEY            # Optional - enables AI enrichment
RESEND_API_KEY          # Optional - enables email digest
EMAIL_FROM              # Sender email address
EMAIL_TO                # Comma-separated recipients
```

### 2. ISO Week Numbers
Product Hunt URLs use ISO week format. Week 1 can start in late December:
```python
# Correct: Use isocalendar()
week = today.isocalendar()[1]
# Wrong: week = today.strftime('%W')
```

### 3. Upvote vs Comment Count
Both appear as numbers in buttons. The code takes `max()` because upvotes > comments:
```python
# src/utils/parsing.py:93-94
if all_numbers:
    upvotes = max(all_numbers)
```

### 4. Grok API Response Format
Grok returns JSON in markdown code blocks. The analyzer strips them:
```python
# src/analysis/grok_analyzer.py:98-104
if content.startswith("```"):
    lines = content.split("\n")
    # Strip first and last lines
```

### 5. Upsert Behavior
Re-runs are safe! Supabase upserts on `(week_date, rank)`:
```python
# src/db/supabase_client.py:60-63
result = self.client.schema("product_hunt").table("products").upsert(
    rows, on_conflict="week_date,rank"
)
```

### 6. Batch vs Single Enrichment
Batch mode (default) is more efficient:
- `enrich_products_batch()` - 1 API call for 10 products
- `categorize_product()` - 1 API call per product (10x slower)

### 7. Solo Builder Pick Logic
Located in `src/analytics/aggregations.py:80-117`:
- Filters for `solo_friendly=true` AND `build_complexity in [weekend, month]`
- Scores by `upvotes + innovation_score * 20`
- Falls back to highest upvoted buildable product

### 8. Email Digest Uses what_it_does
The email shows `maker_info.what_it_does` instead of the marketing description:
```python
# src/notifications/email_digest.py:30-33
if product.maker_info and product.maker_info.get("what_it_does"):
    description = product.maker_info["what_it_does"]
```

## Key Decisions Already Made

**Do NOT re-litigate these:**

| Decision | Rationale | Date |
|----------|-----------|------|
| HTML scraping vs API | No API key needed, simpler | 2025-12 |
| Supabase vs Google Sheets | Structured data, SQL queries, JSONB for AI | 2025-12 |
| Grok vs other LLMs | Fast, JSON mode, good for categorization | 2025-12 |
| Weekly vs daily scraping | Weekly leaderboard is the focus | 2025-12 |
| pydantic-settings | Type-safe config with .env support | 2025-12 |
| tenacity for retries | Standard, configurable | 2025-12 |
| Batch enrichment | 1 API call vs 10, more efficient | 2025-12 |
| Resend for email | Simple API, used in other portfolio projects | 2025-12 |
| Solo Builder Pick | Target audience includes entrepreneurs | 2025-12 |

## Questions to Ask Before Making Changes

1. **Does this change affect the parsing logic?**
   - Test with real HTML first
   - Product Hunt may have changed their structure

2. **Does this change require new secrets?**
   - Update GitHub Actions secrets
   - Update `.env.example`

3. **Does this change affect the database schema?**
   - Supabase migrations needed
   - Consider backwards compatibility

4. **Does this change the AI enrichment?**
   - Update prompts in `src/analysis/prompts.py`
   - Test with real Grok API

5. **Does this change the email format?**
   - Test HTML rendering in email clients
   - Consider mobile responsiveness

## Related Commands to Run

```bash
# After making changes:
pytest                    # Run tests
ruff check src/ tests/    # Lint
mypy src/                 # Type check

# For documentation updates:
/doclikealex              # Regenerate docs

# For quality audit:
/qalikealex               # Full QA sweep

# For deployment planning:
/deploylikealex           # Deployment checklist
```

## File Locations

| What | Where |
|------|-------|
| Main entry point | `src/main.py` |
| HTTP fetching | `src/utils/http.py` |
| HTML parsing | `src/utils/parsing.py` |
| AI enrichment | `src/analysis/grok_analyzer.py` |
| AI prompts | `src/analysis/prompts.py` |
| Category analytics | `src/analytics/aggregations.py` |
| Email digest | `src/notifications/email_digest.py` |
| Database client | `src/db/supabase_client.py` |
| Database models | `src/db/models.py` |
| Configuration | `src/config.py` |
| Backfill script | `backfill/main.py` |
| Tests | `tests/test_*.py` |

## Supabase Quick Reference

**Project**: `rxsmmrmahnvaarwsngtb`
**Schema**: `product_hunt`

```sql
-- Query recent products
SELECT * FROM product_hunt.products
WHERE week_date >= '2025-01-01'
ORDER BY week_date DESC, rank ASC;

-- Query weekly insights
SELECT * FROM product_hunt.weekly_insights
ORDER BY week_date DESC
LIMIT 5;

-- Query category trends
SELECT * FROM product_hunt.category_trends
WHERE week_date >= '2025-01-01'
ORDER BY week_date DESC, avg_upvotes DESC;

-- Check if week exists
SELECT EXISTS(
  SELECT 1 FROM product_hunt.products
  WHERE week_date = '2025-12-30'
);

-- Find solo-friendly products
SELECT name, upvotes, maker_info->>'build_complexity' as complexity
FROM product_hunt.products
WHERE (maker_info->>'solo_friendly')::boolean = true
ORDER BY week_date DESC, upvotes DESC;
```

## maker_info JSONB Structure

The `maker_info` field in the products table contains:
```json
{
  "solo_friendly": true,
  "build_complexity": "weekend",
  "what_it_does": "Plain English description",
  "problem_solved": "Core problem addressed",
  "monetization": "freemium with pro tier"
}
```
