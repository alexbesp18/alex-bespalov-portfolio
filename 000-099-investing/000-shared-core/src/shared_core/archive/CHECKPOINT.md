# Supabase Archival System - Architecture & Decisions

**Last Updated:** 2024-12-27
**Status:** Production-ready

---

## Overview

The archival system stores daily technical indicators in Supabase for historical analysis, backtesting, and pattern recognition.

### Storage Tiers
```
Tier 1 (Hot):    0-7 days   → Raw JSON cache (007-ticker-analysis)
Tier 2 (Daily):  7-90 days  → Full daily snapshots in Supabase
Tier 3 (Monthly): 90+ days  → Compressed monthly aggregates
```

---

## Tables

### `daily_indicators`
Primary key: `(date, symbol)`

| Column | Type | Populated By | Notes |
|--------|------|--------------|-------|
| date | date | All scanners | YYYY-MM-DD |
| symbol | varchar | All scanners | Ticker symbol |
| close | numeric | All scanners | Closing price |
| rsi | numeric | 008, 010 | Relative Strength Index |
| stoch_k | numeric | 010 | Stochastic %K |
| stoch_d | numeric | 010 | Stochastic %D |
| williams_r | numeric | 010 | Williams %R |
| roc | numeric | 010 | Rate of Change |
| macd | numeric | 008, 010 | MACD line |
| macd_signal | numeric | 008, 010 | MACD signal |
| macd_hist | numeric | 008, 010 | MACD histogram |
| adx | numeric | 010 | Average Directional Index |
| sma_20 | numeric | 008, 010 | 20-day SMA |
| sma_50 | numeric | 008, 010 | 50-day SMA |
| sma_200 | numeric | 008, 010 | 200-day SMA |
| bb_upper | numeric | 010 | Bollinger upper band |
| bb_lower | numeric | 010 | Bollinger lower band |
| bb_position | numeric | 010 | Position within bands (0-1) |
| atr | numeric | 010 | Average True Range |
| volume | bigint | 008, 010 | Trading volume |
| volume_ratio | numeric | 008 | Volume vs average |
| obv | bigint | 010 | On-Balance Volume |
| bullish_score | numeric | 008-alerts | Bullish signal score |
| reversal_score | numeric | 009-reversals | Reversal signal score |
| oversold_score | numeric | 010-oversold | Oversold signal score |
| created_at | timestamptz | Supabase | Auto-generated |

### `monthly_aggregates`
Primary key: `(month, symbol)`

| Column | Type | Description |
|--------|------|-------------|
| month | date | First day of month (YYYY-MM-01) |
| symbol | varchar | Ticker symbol |
| open_price | numeric | First close of month |
| close_price | numeric | Last close of month |
| high_price | numeric | Highest close |
| low_price | numeric | Lowest close |
| monthly_return | numeric | % return for month |
| avg_rsi | numeric | Average RSI |
| min_rsi | numeric | Minimum RSI |
| max_rsi | numeric | Maximum RSI |
| days_oversold | int | Days with RSI < 30 |
| days_overbought | int | Days with RSI > 70 |
| avg_bullish_score | numeric | Average bullish score |
| avg_reversal_score | numeric | Average reversal score |
| avg_oversold_score | numeric | Average oversold score |
| buy_signals | int | Count of BUY actions |
| sell_signals | int | Count of SELL actions |

---

## Key Architectural Decisions

### 1. Sparse Dictionary Pattern

**Problem:** Multiple scanners (008, 009, 010) write to the same `daily_indicators` row. If scanner A writes `bullish_score=7.5` and scanner B later upserts with `bullish_score=NULL`, the original value gets overwritten.

**Solution:** `to_dict()` only includes non-None fields:
```python
def to_dict(self) -> Dict[str, Any]:
    result = {"date": self.date, "symbol": self.symbol}
    fields = [("rsi", self.rsi), ("bullish_score", self.bullish_score), ...]
    for key, value in fields:
        if value is not None:
            result[key] = value
    return result
```

**Result:** Each scanner only updates its own fields, preserving data from other scanners.

### 2. inf/nan Sanitization

**Problem:** Python float values like `inf`, `-inf`, and `NaN` are not JSON-compliant and cause `ValueError: Out of range float values are not JSON compliant`.

**Solution:** `_sanitize_float()` replaces these with `None`:
```python
def _sanitize_float(value):
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
    return value
```

### 3. Upsert with Conflict Resolution

Uses Supabase upsert with `on_conflict="date,symbol"` to:
- Insert new records
- Update existing records on re-runs
- Batch operations (500 records per batch) to avoid payload limits

### 4. Monthly Aggregation (90-day retention)

**Trigger:** Data older than 90 days is eligible for compression.

**Process:**
1. `get_months_to_aggregate()` finds months with daily data > 90 days old
2. `aggregate_month()` creates `MonthlyAggregate` per symbol
3. `cleanup_old_daily()` deletes compressed daily records

**Calculations:**
- `monthly_return` = ((close - open) / open) * 100
- `days_oversold` = count where RSI < 30
- `days_overbought` = count where RSI > 70
- `buy_signals` = count where action contains "BUY"
- `sell_signals` = count where action contains "SELL"

---

## Scanner Data Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   008-alerts    │     │  009-reversals  │     │  010-oversold   │
│                 │     │                 │     │                 │
│ bullish_score   │     │ reversal_score  │     │ oversold_score  │
│ rsi, macd, sma  │     │ upside_rev_score│     │ All indicators  │
│ volume_ratio    │     │                 │     │ bb, atr, adx    │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │ archive_daily_indicators│
                    │   score_type param:     │
                    │   "bullish"/"reversal"/ │
                    │   "oversold"            │
                    └────────────┬───────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │   daily_indicators     │
                    │   (Supabase table)     │
                    │   Upsert on date,symbol│
                    └────────────────────────┘
```

---

## Removed Fields

| Field | Date | Reason |
|-------|------|--------|
| `reversal_score_downside` | 2026-01-14 | User only cares about upside (BUY) signals |
| `reversal_conviction_downside` | 2026-01-14 | User only cares about upside (BUY) signals |
| `bullish_reason` | 2024-12-27 | Grok AI analysis not in use |
| `tech_summary` | 2024-12-27 | Grok AI analysis not in use |
| `action` | 2024-12-27 | Never populated by any scanner |

---

## Environment Variables

```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...  # Service role key (bypasses RLS)
```

---

## Future Considerations

1. **Action Field:** If scanners need to track BUY/SELL actions, add `action` back to `IndicatorSnapshot` and update scanners to pass it.

2. **Grok Analysis:** If AI analysis is re-enabled, add `bullish_reason` and `tech_summary` columns back to Supabase and `IndicatorSnapshot`.

3. **Monthly Aggregation Cron:** Consider adding a scheduled job to run `run_monthly_aggregation()` weekly/monthly.

4. **Backfill:** To populate historical data, run scanners with historical dates.

---

## Debugging Checklist

If data isn't appearing in Supabase:

1. Check env vars are set: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`
2. Check workflow step has env vars in `env:` block
3. Look for "Archived X indicator snapshots" in logs
4. Check for inf/nan errors in logs
5. Verify table schema matches `IndicatorSnapshot` fields
