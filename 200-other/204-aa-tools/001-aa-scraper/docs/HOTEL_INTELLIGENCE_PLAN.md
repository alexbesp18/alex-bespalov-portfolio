# Hotel Intelligence System - Architecture Plan

## The Insight

The hotel yield permutation space is **finite and small enough to exhaustively explore**:

```
Cities (8) × Days of Week (7) × Durations (3) × Advance Windows (7) = 1,176 combinations
```

At ~2-3 seconds per API call, full exploration takes **~45-60 minutes**.

Instead of sampling and guessing, we can **know** the yield patterns with certainty.

---

## Phase 1: Discovery Engine (Standalone Script)

### `scripts/hotel_discovery.py`

A standalone script that exhaustively explores the permutation space.

**Permutation Dimensions:**

| Dimension | Values | Count |
|-----------|--------|-------|
| Cities | Austin, Dallas, Houston, Vegas, NYC, Boston, SF, LA | 8 |
| Day of Week | Mon, Tue, Wed, Thu, Fri, Sat, Sun | 7 |
| Duration | 1, 2, 3 nights | 3 |
| Advance Days | 7, 14, 21, 30, 45, 60, 90 | 7 |

**Total: 1,176 unique combinations**

### Discovery Algorithm

```python
def run_discovery(max_runtime_minutes: int = 60):
    """
    Exhaustively explore hotel yield space.

    For each (city, dow, duration, advance_days):
        1. Find the next date matching that dow/advance_days
        2. Search hotels for that (check_in, check_out)
        3. Record: min/max/avg/median yield, deal count, top hotels
        4. Save to hotel_yield_matrix table
    """

    combinations = generate_all_combinations()
    shuffle(combinations)  # Randomize to get broad coverage if interrupted

    for city, dow, duration, advance_days in combinations:
        check_in = find_next_date(dow, advance_days)
        check_out = check_in + timedelta(days=duration)

        hotels = search_hotels(city, check_in, check_out)

        record_yield_matrix(
            city=city,
            day_of_week=dow,
            duration=duration,
            advance_days=advance_days,
            stats=calculate_stats(hotels),
            top_hotel=hotels[0] if hotels else None,
            discovered_at=now()
        )
```

### Output: Yield Matrix Table

```sql
CREATE TABLE hotel_yield_matrix (
    id INTEGER PRIMARY KEY,
    city TEXT NOT NULL,
    day_of_week INTEGER NOT NULL,  -- 0=Mon, 6=Sun
    duration INTEGER NOT NULL,      -- 1, 2, 3 nights
    advance_days INTEGER NOT NULL,  -- 7, 14, 21, 30, 45, 60, 90

    -- Stats from discovery
    avg_yield REAL,
    max_yield REAL,
    min_yield REAL,
    median_yield REAL,
    deal_count INTEGER,

    -- Best hotel found
    top_hotel_name TEXT,
    top_hotel_yield REAL,
    top_hotel_cost REAL,
    top_hotel_miles INTEGER,

    -- Metadata
    discovered_at TEXT,
    last_verified_at TEXT,
    verification_count INTEGER DEFAULT 1,
    yield_stability REAL,  -- Std dev across verifications

    UNIQUE(city, day_of_week, duration, advance_days)
);
```

---

## Phase 2: Weekly Verification Job

### `scripts/hotel_verify.py`

A weekly job that:
1. Re-runs a sample of the matrix (e.g., 200 random combinations)
2. Compares new yields to historical data
3. Updates stability scores
4. Flags significant changes

**Verification Logic:**

```python
def verify_matrix(sample_size: int = 200):
    """
    Weekly verification of yield matrix accuracy.
    """
    # Get combinations ordered by oldest verification
    stale_combinations = db.get_stale_matrix_entries(limit=sample_size)

    for entry in stale_combinations:
        new_stats = search_and_calculate(entry)

        # Compare to historical
        drift = abs(new_stats.avg_yield - entry.avg_yield) / entry.avg_yield

        db.update_matrix_entry(
            entry.id,
            new_stats=new_stats,
            verified_at=now(),
            yield_stability=calculate_stability(entry, new_stats)
        )

        if drift > 0.25:  # 25% drift
            flag_for_review(entry, drift)
```

### Stability Scoring

Track how consistent yields are over time:

```python
yield_stability = std_dev(historical_yields) / mean(historical_yields)

# Low stability = yields vary a lot (volatile)
# High stability = yields are predictable
```

---

## Phase 3: Smart Scraper (Daily Job)

### Updated `scrapers/hotels.py`

Instead of generating dates blindly, consult the yield matrix:

```python
def get_smart_search_targets(budget_searches: int = 80):
    """
    Use yield matrix to pick the best searches to run today.

    Strategy:
    1. Always include top 20 highest-yield combinations
    2. Include 20 Austin-specific combinations (local priority)
    3. Include 20 "volatile" combinations (might have changed)
    4. Include 20 random for exploration
    """

    targets = []

    # Top performers
    targets += db.get_top_yield_combinations(limit=20)

    # Austin priority
    targets += db.get_top_yield_combinations(city='Austin', limit=20)

    # Volatile (low stability, might have improved)
    targets += db.get_volatile_combinations(limit=20)

    # Random exploration
    targets += db.get_random_combinations(limit=20)

    return deduplicate(targets)
```

---

## Phase 4: Analytics Dashboard (Future)

Query the matrix to answer questions:

```sql
-- Best day of week for Austin?
SELECT day_of_week, AVG(avg_yield) as yield
FROM hotel_yield_matrix
WHERE city = 'Austin'
GROUP BY day_of_week
ORDER BY yield DESC;

-- Best advance booking window?
SELECT advance_days, AVG(max_yield) as best_yield
FROM hotel_yield_matrix
GROUP BY advance_days
ORDER BY best_yield DESC;

-- 1-night vs 2-night vs 3-night comparison?
SELECT duration, city, AVG(avg_yield) as yield
FROM hotel_yield_matrix
GROUP BY duration, city
ORDER BY city, duration;

-- Most volatile markets (yields change frequently)?
SELECT city, AVG(yield_stability) as stability
FROM hotel_yield_matrix
GROUP BY city
ORDER BY stability DESC;
```

---

## Implementation Priority

### Week 1: Discovery Engine
| Task | Est. Time |
|------|-----------|
| Create `hotel_yield_matrix` table | 30 min |
| Build `scripts/hotel_discovery.py` | 2 hours |
| Add progress tracking & resume capability | 1 hour |
| Run initial discovery (~1 hour runtime) | 1 hour |

### Week 2: Verification & Smart Scraper
| Task | Est. Time |
|------|-----------|
| Build `scripts/hotel_verify.py` | 1 hour |
| Update `scrapers/hotels.py` to use matrix | 1 hour |
| Add stability scoring | 30 min |
| Set up weekly cron for verification | 15 min |

### Week 3: Reporting & Alerts
| Task | Est. Time |
|------|-----------|
| Add matrix insights to daily digest | 1 hour |
| Build "best booking windows" report | 1 hour |
| Alert on significant yield changes | 30 min |

---

## Expected Insights

After running discovery, we'll know things like:

```
AUSTIN YIELD PATTERNS:
- Best day: Saturday (avg 28 LP/$)
- Best duration: 2 nights (avg 26 LP/$)
- Best advance: 14 days (avg 30 LP/$)
- Sweet spot: Sat, 2 nights, 14 days ahead = 32 LP/$

VEGAS YIELD PATTERNS:
- Best day: Thursday (avg 25 LP/$)
- Worst day: Saturday (avg 18 LP/$) - high demand = low yield
- Best advance: 30+ days (avg 27 LP/$)

OVERALL INSIGHTS:
- Weekdays generally beat weekends (lower demand)
- 2-night stays have better yields than 1-night
- 14-30 days advance is the sweet spot
- Austin has most consistent yields (stability: 0.92)
```

---

## Questions to Resolve

1. **API Rate Limits**: Can we sustain 1,176 calls in an hour? (~20/min)
   - Current: 0.3-0.8s delay = ~2 calls/sec = 120/min (should be fine)

2. **Data Freshness**: How often do hotel yields actually change?
   - Weekly verification will answer this empirically

3. **Seasonal Patterns**: Should we track month/season as a dimension?
   - Start simple, add if we see monthly patterns in data

4. **Multi-City Trips**: Should we optimize for trip sequences?
   - Future enhancement after base system works

---

## Files to Create

```
scripts/
  hotel_discovery.py      # Full permutation exploration
  hotel_verify.py         # Weekly verification job
  hotel_analytics.py      # Query and report on matrix

core/
  database.py             # Add yield_matrix table + queries

config/
  cities.py               # Already exists, may need tweaks
```

---

## Success Metrics

After 1 month:
- [ ] Full yield matrix populated (1,176 entries)
- [ ] Each entry verified at least 2x
- [ ] Daily scraper using matrix intelligence
- [ ] Digest includes "best booking window" insights
- [ ] 20%+ improvement in average yield of reported deals
