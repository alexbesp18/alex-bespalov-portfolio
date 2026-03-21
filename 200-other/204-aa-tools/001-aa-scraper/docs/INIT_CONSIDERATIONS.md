# Init Considerations

Quick-start guide for new agents/developers working on the AA Points Arbitrage Monitor.

---

## Start Here (5 Minutes to Productive)

### 1. Read CLAUDE.md First
Located at project root (`/CLAUDE.md`). Contains all commands, APIs, and troubleshooting.

### 2. Understand the Goal
- **What:** Automated system to find high-yield AA loyalty point opportunities
- **Strategy:** Stack earning channels: Portal + SimplyMiles + Credit Card
- **User goal:** Reach Platinum (75K LPs) from Gold (40K) with $500/month budget

### 3. Check Current State
Read `docs/CHECKPOINT.md` for what's working, what's broken, and what's next.

---

## Database (Supabase)

**The project uses Supabase (cloud PostgreSQL) as the primary database.**

### Configuration
```bash
# .env settings
DB_MODE=supabase
SUPABASE_URL=https://rxsmmrmahnvaarwsngtb.supabase.co
SUPABASE_KEY=eyJ...  # service_role key
```

### Key Files
- `core/supabase_db.py` - All Supabase operations
- `core/database.py` - DB routing (`get_database()` returns SupabaseDatabase)

### Supabase Dashboard
Access at: https://supabase.com/dashboard/project/rxsmmrmahnvaarwsngtb

---

## Key Files (Mental Model)

```
┌─────────────────────────────────────────────────────────────┐
│                    CONFIGURATION                            │
│  config/settings.py  ← All thresholds, modifiers, keys      │
│  config/cities.py    ← Hotel city definitions               │
│  .env                ← Secrets (API keys, Supabase)         │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      SCRAPERS                               │
│  scrapers/simplymiles_api.py  ← Preferred (JSON API)        │
│  scrapers/simplymiles.py      ← Fallback (Playwright)       │
│  scrapers/portal.py           ← Cartera API                 │
│  scrapers/hotels.py           ← REST API + matrix           │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    CORE LOGIC                               │
│  core/supabase_db.py  ← Supabase operations (primary)       │
│  core/database.py     ← DB routing (get_database())         │
│  core/stack_detector.py ← Matches SM ↔ Portal               │
│  core/scorer.py       ← Yield calc + modifiers              │
│  core/optimizer.py    ← Budget allocation                   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      ALERTS                                 │
│  alerts/evaluator.py  ← Threshold checks, dedup             │
│  alerts/formatter.py  ← HTML/text email templates           │
│  alerts/sender.py     ← Resend API                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Common Gotchas

### Two SimplyMiles Scrapers?
- `simplymiles_api.py` - JSON API, faster, **use this one**
- `simplymiles.py` - Playwright DOM scraping, fallback only

### "Yield" vs "Score"?
- **Yield** = Raw LP/$ (total_miles / min_spend)
- **Score** = Yield × modifiers (urgency, commitment level, location)

### Hotel Matrix vs Hotel Deals?
- `hotel_yield_matrix` - 1,176 historical averages for predictions
- `hotel_deals` - Current availability from scraper

### Session Expired?
If SimplyMiles returns 0 offers or HTTP 419: See VPS section below for full recovery process.

### Supabase vs SQLite?
- **Supabase (primary):** DB_MODE=supabase - used by default
- **SQLite (fallback):** DB_MODE=sqlite - for local testing only

---

## VPS Access (Production)

The system runs on DigitalOcean VPS with 7 cron jobs.

### Access Details
```bash
# SSH
ssh root@REDACTED_VPS_IP

# VNC (for visual debugging)
Host: REDACTED_VPS_IP
Port: 5900
Password: REDACTED_VNC_PASS
```

### Key Paths on VPS
- Project: `/root/aa_scraper/`
- Logs: `/root/aa_scraper/logs/`
- Cookies: `/root/aa_scraper/simplymiles_cookies.json`

### SimplyMiles Session Recovery
When session expires (HTTP 419 error):
```bash
# 1. On Mac - re-authenticate
cd ~/Desktop/Projects/aa_scraper
source venv/bin/activate
python scripts/setup_auth.py
# Browser opens -> Log in to AA -> Press Enter

# 2. Sync cookies to VPS
rsync -avz simplymiles_cookies.json root@REDACTED_VPS_IP:~/aa_scraper/

# 3. Verify
ssh root@REDACTED_VPS_IP "cd aa_scraper && source venv/bin/activate && python scrapers/simplymiles_api.py --test"
```

### VPS Commands
```bash
# Full pipeline
cd /root/aa_scraper && source venv/bin/activate && python scripts/run_all.py

# Check logs
tail -f logs/simplymiles.log

# Test session health
python scripts/session_keepalive.py --test

# View cron jobs
crontab -l
```

---

## Decisions Already Made (Don't Re-Litigate)

| Decision | Why |
|----------|-----|
| Supabase not SQLite | Cloud access, web dashboard, no file sync needed |
| 85% fuzzy threshold | Balance between precision and recall for merchant matching |
| Greedy optimizer | Simple, fast, good-enough for personal use |
| Resend for email | Reliable, good DX, reasonable pricing |
| No automated purchasing | ToS risk, keep it advisory only |
| Hotels separate from stacking | Different architecture (no merchant match, star-rating scoring) |

---

## Questions to Ask Before Changes

1. **Is this in scope?** Check `docs/PLAN.md` for Non-Goals
2. **Does it exist already?** Search codebase before building
3. **Is it tested?** Run `pytest -x -q` before and after
4. **Is it simple?** This is a personal tool, don't over-engineer

---

## Quick Health Check

```bash
source venv/bin/activate
pytest -x -q                                                    # Should pass (154 tests)
python -c "from core.database import get_database; print(type(get_database()).__name__)"  # Should print SupabaseDatabase
python -c "from config.settings import get_settings; print('OK')" # Should print OK
```

---

## Related Commands

| Task | Command |
|------|---------|
| Continue building | `/continuelikealex` |
| Run QA audit | `/qalikealex` |
| Plan deployment | `/deploylikealex` |
| Clean up code | `/cleanuplikealex` |
| Debug issues | `/debuglikealex` |

---

## Documentation Map

| Doc | Purpose |
|-----|---------|
| `CLAUDE.md` | Commands, APIs, troubleshooting (read first!) |
| `docs/PLAN.md` | Goals, milestones, non-goals |
| `docs/ARCHITECTURE.md` | System design, data flow |
| `docs/CHECKPOINT.md` | Current state, metrics, next actions |
| `docs/future_roadmap.md` | What's planned for later |
| `docs/patterns.md` | Established patterns to follow |
| `docs/modules.md` | Module catalog and dependencies |
| `docs/discovery_notes.md` | CSS selectors, HTML structure |

---

## How to Add a New Feature

### Adding a New Data Source

1. **Create scraper in `scrapers/`**
   ```python
   # scrapers/new_source.py
   from core.database import get_database
   from core.normalizer import normalize_merchant

   async def scrape_new_source():
       db = get_database()
       # ... fetch and parse data
       db.insert_new_source(data)
   ```

2. **Add database methods in `core/supabase_db.py`**
   - `insert_new_source(...)` - Store scraped data
   - `get_latest_new_source()` - Retrieve for processing
   - `clear_new_source()` - Clean old data (with verification!)

3. **Add Supabase table** via migration or dashboard

4. **Add tests in `tests/test_new_source.py`**

5. **Update `scripts/run_all.py`** to include new scraper

### Adding a New Alert Type

1. **Add threshold in `config/settings.py`**
2. **Add evaluation logic in `alerts/evaluator.py`**
3. **Add formatting in `alerts/formatter.py`**
4. **Update `format_daily_digest()` to include new type**

### Patterns to Follow

See `docs/patterns.md` for established patterns:
- Singleton pattern (database, settings)
- Async scraping pattern
- Error handling pattern
- Scoring pattern
- Alert deduplication pattern

### Modules to Reuse

See `docs/modules.md` for module catalog:
- `core/http_client.py` - HTTP with retry logic
- `core/exceptions.py` - Custom exception hierarchy
- `core/normalizer.py` - Merchant name matching
- `core/scorer.py` - Yield calculations

---

*Last updated: 2026-01-03*
