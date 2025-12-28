# Reversal Tracker — Signal Logic Reference (v3)

A comprehensive guide to all technical indicators and trigger logic used in the reversal detection system.

**v3 Changes:**
- Removed short-term indicators (Stochastic, Williams %R, Consecutive Days)
- Focus on Mid-term (weeks) and Long-term (months) signals only
- Harsher volume gate (0.5x penalty for low volume)
- Harsher ADX penalty (0.5x for ADX > 40)
- Added Conviction Levels (HIGH/MEDIUM/LOW)
- Tightened RSI thresholds (< 25 for max score)

---

## Table of Contents
1. [Technical Indicators](#technical-indicators)
2. [Upside Reversal Score](#upside-reversal-score)
3. [Downside Reversal Score](#downside-reversal-score)
4. [Conviction Levels](#conviction-levels)
5. [Trigger Rules](#trigger-rules)
6. [Multipliers](#multipliers)

---

## Technical Indicators

### Mid-Term Indicators (Weeks)
| Indicator | Calculation | Purpose |
|-----------|-------------|---------|
| **SMA 50** | 50-day simple moving average | Mid-term trend |
| **MACD Line** | 12/26 EMA difference | Mid-term momentum |
| **MACD Signal** | 9-period EMA of MACD Line | Signal crossovers |
| **MACD Histogram** | MACD Line - Signal Line | Momentum direction |

### Long-Term Indicators (Months)
| Indicator | Calculation | Purpose |
|-----------|-------------|---------|
| **SMA 200** | 200-day simple moving average | Long-term trend |
| **Golden Cross** | SMA50 crosses above SMA200 | Major bullish signal |
| **Death Cross** | SMA50 crosses below SMA200 | Major bearish signal |

### Context Indicators
| Indicator | Calculation | Purpose |
|-----------|-------------|---------|
| **RSI (14)** | 14-period Relative Strength Index | Momentum context |
| **ADX** | Average Directional Index | Trend strength |
| **Volume Ratio** | Current volume / 20-day avg | Confirmation |
| **OBV** | Cumulative volume flow | Divergence detection |

---

## Upside Reversal Score

**Purpose:** Detect potential bottoms and bounce opportunities.

**Score Range:** 1-10 (higher = stronger upside reversal signal)

### Weighting (v3 — Mid/Long Term Focus)

| Factor | Weight | 10 Points | 7 Points | 4 Points | 1 Point |
|--------|--------|-----------|----------|----------|---------|
| **RSI** | 15% | RSI < 25 | RSI < 30 | RSI < 35 | RSI >= 35 |
| **MACD Crossover** | 15% | Fresh bullish cross | Above signal | Narrowing | Below signal |
| **MACD Histogram** | 10% | Neg→Pos flip | Positive | Narrowing neg | Widening neg |
| **Price vs SMA50** | 15% | Crossed above | Above | Within 3% below | Well below |
| **Price vs SMA200** | 20% | Crossed above | Above | Within 5% below | Well below |
| **Volume Spike** | 15% | >= 2.0x avg | >= 1.5x | >= 1.2x | < 1.0x |
| **Divergence** | 10% | RSI+OBV bullish | RSI bullish | — | None |

### Key Differences from v2
- Removed: Stochastic (too short-term)
- Removed: Williams %R (redundant with RSI)
- Removed: Consecutive Red Days (noise)
- Added: MACD Line Crossover (mid-term signal)
- Added: Price vs SMA50 (mid-term trend)
- Increased: Volume weight (10% → 15%)
- Increased: SMA200 weight (15% → 20%)

---

## Downside Reversal Score

**Purpose:** Detect potential tops and pullback risk.

**Score Range:** 1-10 (higher = stronger downside reversal signal)

### Weighting (v3 — Mid/Long Term Focus)

| Factor | Weight | 10 Points | 7 Points | 4 Points | 1 Point |
|--------|--------|-----------|----------|----------|---------|
| **RSI** | 15% | RSI > 75 | RSI > 70 | RSI > 65 | RSI <= 65 |
| **MACD Crossover** | 15% | Fresh bearish cross | Below signal | Narrowing | Above signal |
| **MACD Histogram** | 10% | Pos→Neg flip | Negative | Narrowing pos | Widening pos |
| **Price vs SMA50** | 15% | Crossed below | > 15% above | > 5% above | Near/below |
| **Price vs SMA200** | 20% | Crossed below | > 20% above | > 10% above | Near/below |
| **Volume Spike** | 15% | >= 2.0x avg | >= 1.5x | >= 1.2x | < 1.0x |
| **Divergence** | 10% | RSI+OBV bearish | RSI bearish | — | None |

---

## Conviction Levels

**NEW in v3:** Signals are classified by conviction level for actionability.

| Level | Requirements | Action |
|-------|--------------|--------|
| **HIGH** | Score >= 8.0 AND Volume >= 1.2x AND ADX < 35 | **BUY/SELL NOW** |
| **MEDIUM** | Score >= 7.0 AND Volume >= 1.0x | Developing — watch closely |
| **LOW** | Score >= 6.0 | Not actionable |
| **NONE** | Below thresholds | Ignore |

### Alert Behavior
- **Default mode:** Only HIGH conviction signals generate alerts
- **Developing mode:** Show MEDIUM+ for manual review
- HIGH conviction = actionable immediately
- MEDIUM conviction = something is brewing, check manually

---

## Multipliers

### Volume Multiplier (HARSH)

Volume confirmation is critical. Low volume reversals are traps.

| Volume Ratio | Multiplier | Effect |
|--------------|------------|--------|
| >= 2.0x avg | 1.2x | +20% bonus (strong confirmation) |
| >= 1.5x avg | 1.1x | +10% bonus (good volume) |
| >= 1.0x avg | 1.0x | Neutral |
| >= 0.8x avg | 0.7x | -30% penalty (weak) |
| < 0.8x avg | 0.5x | -50% penalty (halve score) |

### ADX Multiplier (HARSH)

Don't fight strong trends. Mean reversion works best in ranging markets.

| ADX Value | Multiplier | Interpretation |
|-----------|------------|----------------|
| ADX < 20 | 1.15x | Range-bound = mean reversion boost |
| ADX 20-30 | 1.0x | Moderate trend = neutral |
| ADX 30-40 | 0.7x | Strong trend = -30% penalty |
| ADX > 40 | 0.5x | Very strong trend = -50% penalty |

---

## Trigger Rules

### HIGH Conviction Signals (Actionable)

| ID | Condition | Action | Cooldown |
|----|-----------|--------|----------|
| `UPSIDE_REVERSAL_HIGH` | Score >= 8, Volume >= 1.2x, ADX < 35 | BUY NOW | 7 days |
| `DOWNSIDE_REVERSAL_HIGH` | Score >= 8, Volume >= 1.2x, ADX < 35 | SELL NOW | 7 days |

### Event-Based Triggers

| ID | Condition | Action | Cooldown |
|----|-----------|--------|----------|
| `BUY_REVERSAL` | Crosses above SMA200, Score >= 8, Volume >= 1.2x | BUY | 0 days |
| `BUY_OVERSOLD_BOUNCE` | RSI crosses above 30, Above SMA50, Score >= 7 | BUY | 0 days |
| `SELL_WARNING` | Crosses below SMA200, Score <= 5 | SELL | 0 days |

### Pattern Triggers

| ID | Condition | Action | Cooldown |
|----|-----------|--------|----------|
| `GOLDEN_CROSS` | SMA50 crosses above SMA200 | BUY | 30 days |
| `DEATH_CROSS` | SMA50 crosses below SMA200 | SELL | 30 days |

---

## Divergence Detection

**Lookback:** 20 days (increased from 14 for mid-term focus)

**Bullish Divergence:** Price makes lower low, RSI/OBV makes higher low.
- Indicates selling pressure exhausted
- Confluence bonus if both RSI and OBV show divergence (1.5x)

**Bearish Divergence:** Price makes higher high, RSI/OBV makes lower high.
- Indicates buying pressure exhausted
- Confluence bonus if both RSI and OBV show divergence (1.5x)

---

## Score Calculation Example

**AAPL Upside Reversal Check:**

```
Components:
  RSI (28)           → 7.0/10  × 15% = 1.05
  MACD Crossover     → 10.0/10 × 15% = 1.50  (fresh bullish cross)
  MACD Histogram     → 10.0/10 × 10% = 1.00  (just flipped positive)
  Price vs SMA50     → 7.0/10  × 15% = 1.05  (above SMA50)
  Price vs SMA200    → 10.0/10 × 20% = 2.00  (just crossed above)
  Volume (1.8x)      → 7.0/10  × 15% = 1.05
  Divergence         → 7.5/10  × 10% = 0.75  (bullish RSI divergence)
                                       -----
  Raw Score:                           8.40

Multipliers:
  Volume (1.8x avg)  → 1.1x
  ADX (22)           → 1.0x

Final Score: 8.40 × 1.1 × 1.0 = 9.24/10

Conviction: HIGH (Score >= 8.0, Volume >= 1.2x, ADX < 35)
Action: BUY NOW
```

---

## Historical Data

- **Data source:** Twelve Data API
- **Default lookback:** 1000 days (~4 years)
- **API credits:** 1 credit per ticker regardless of lookback
- **Backtest capability:** Full support for 3+ year backtesting
