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
4. `src/db/supabase_client.py` - Database persistence
5. `src/config.py` - Environment configuration

## Mental Model

```
Product Hunt HTML → BeautifulSoup → Pydantic Models → Grok AI → Supabase
```

This is a **data pipeline**, not a web app. It runs once per week via GitHub Actions:
1. Fetches HTML from Product Hunt leaderboard
2. Parses top 10 products with BeautifulSoup
3. Enriches with Grok AI (category, scores, insights)
4. Saves to Supabase with upsert strategy

**Graceful degradation**: If Grok is unavailable, raw products are saved without enrichment.

## Common Gotchas

### 1. Environment Variables (No Prefix!)
Variables no longer use `PH_` prefix:
```bash
SUPABASE_URL            # Not PH_SUPABASE_URL
SUPABASE_SERVICE_KEY    # Not PH_SUPABASE_SERVICE_KEY
GROK_API_KEY            # Optional - enables AI enrichment
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
| HTML parsing | `src/utils/parsing.py` |
| AI enrichment | `src/analysis/grok_analyzer.py` |
| AI prompts | `src/analysis/prompts.py` |
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

-- Check if week exists
SELECT EXISTS(
  SELECT 1 FROM product_hunt.products
  WHERE week_date = '2025-12-30'
);
```
