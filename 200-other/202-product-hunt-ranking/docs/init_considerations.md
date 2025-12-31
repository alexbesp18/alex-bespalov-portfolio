# Init Considerations

## Quick Start for New Agents/Developers

### Start Here
1. Read `README.md` for project overview
2. Read `docs/architecture.md` for system design
3. Check `docs/checkpoint.md` for current state

### Key Files (in order of importance)
1. `src/main.py` - Entry point, understand the flow
2. `src/utils/parsing.py` - Core scraping logic
3. `src/config.py` - Environment configuration
4. `src/models.py` - Data structures

## Mental Model

```
Product Hunt HTML → BeautifulSoup Parser → Pydantic Models → Google Sheets
```

This is a **data pipeline**, not a web app. It runs once per week via GitHub Actions, fetches HTML, extracts structured data, and appends to a spreadsheet.

## Common Gotchas

### 1. Environment Variable Prefix
Variables use `PH_` prefix to avoid conflicts:
```bash
PH_GDRIVE_API_KEY_JSON  # Not GDRIVE_API_KEY_JSON
PH_GSHEET_ID            # Not GSHEET_ID
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

### 4. Service Account JSON
Can be provided as:
- Raw JSON string (for GitHub Actions secrets)
- File path (for local development)

### 5. Sheet Sorting
After appending rows, the sheet auto-sorts by Date (desc) then Rank (asc). Don't be surprised if new data appears at top.

## Key Decisions Already Made

**Do NOT re-litigate these:**

| Decision | Rationale | Date |
|----------|-----------|------|
| HTML scraping vs API | No API key needed, simpler | 2025-12 |
| Google Sheets vs database | User prefers spreadsheet interface | 2025-12 |
| Weekly vs daily scraping | Weekly leaderboard is the focus | 2025-12 |
| pydantic-settings | Type-safe config with .env support | 2025-12 |
| tenacity for retries | Standard, configurable | 2025-12 |

## Questions to Ask Before Making Changes

1. **Does this change affect the parsing logic?**
   - Test with real HTML first
   - Product Hunt may have changed their structure

2. **Does this change require new secrets?**
   - Update GitHub Actions secrets
   - Update `.env.example`

3. **Does this change affect the output format?**
   - Existing data in Google Sheets may need migration
   - Check if headers need updating

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
```

## File Locations

| What | Where |
|------|-------|
| Main entry point | `src/main.py` |
| HTML parsing | `src/utils/parsing.py` |
| Configuration | `src/config.py` |
| Backfill script | `backfill/main.py` |
| GitHub workflows | `/.github/workflows/202_ph_ranking_*.yml` |
| Tests | `tests/test_*.py` |
