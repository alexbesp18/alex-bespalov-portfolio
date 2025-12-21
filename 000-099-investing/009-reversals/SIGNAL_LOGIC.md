# Reversal Tracker — Signal Logic Reference

A comprehensive guide to all technical indicators and trigger logic used in the reversal detection system.

---

## Table of Contents
1. [Technical Indicators](#technical-indicators)
2. [Upside Reversal Score](#upside-reversal-score)
3. [Downside Reversal Score](#downside-reversal-score)
4. [Trigger Rules](#trigger-rules)
5. [Cooldown System](#cooldown-system)

---

## Technical Indicators

### Trend Indicators
| Indicator | Calculation | Purpose |
|-----------|-------------|---------|
| **SMA 20** | 20-day simple moving average | Short-term trend |
| **SMA 50** | 50-day simple moving average | Medium-term trend |
| **SMA 200** | 200-day simple moving average | Long-term trend |

### Momentum Indicators
| Indicator | Calculation | Interpretation |
|-----------|-------------|----------------|
| **RSI (14)** | 14-period Relative Strength Index | <30 = oversold, >70 = overbought |
| **MACD** | 12/26/9 EMA crossover | Line, Signal, Histogram |
| **MACD Histogram** | MACD Line - Signal Line | Positive = bullish momentum |
| **Stochastic %K/%D** | 14-period with 3-period smoothing | <20 = oversold, >80 = overbought |
| **Williams %R** | 14-period | <-80 = oversold, >-20 = overbought |
| **ROC** | 14-period Rate of Change | Extreme negative = mean reversion candidate |

### Volatility Indicators
| Indicator | Calculation | Purpose |
|-----------|-------------|---------|
| **Bollinger Bands** | 20-period SMA ± 2 std dev | Volatility squeeze/expansion |
| **BB Width** | (Upper - Lower) / Middle * 100 | Volatility measurement |
| **ATR** | 14-period Average True Range | Stop-loss sizing, volatility |

### Volume Indicators
| Indicator | Calculation | Purpose |
|-----------|-------------|---------|
| **OBV** | Cumulative volume flow | Accumulation/distribution |
| **Volume Ratio** | Current volume / 20-day avg | Spike detection (>2x = significant) |

---

## Upside Reversal Score

**Purpose:** Detect potential bottoms and bounce opportunities.

**Score Range:** 1-10 (higher = stronger upside reversal signal)

### Weighting

| Factor | Weight | 10 Points | 7 Points | 5 Points | 2 Points |
|--------|--------|-----------|----------|----------|----------|
| **RSI Position** | 25% | RSI <25 | RSI 25-35 | RSI 35-50 | RSI >50 |
| **Stochastic** | 20% | %K <20 + bullish cross | %K <20 | %K 20-30 | %K >50 |
| **MACD Histogram** | 15% | Neg→Pos flip | — | Narrowing negative | Widening negative |
| **Price vs SMA200** | 15% | Just crossed above | Above | Within 3% below | >10% below |
| **Volume Spike** | 10% | >2x avg on UP day | — | 1.5x avg | Normal |
| **Divergence** | 10% | RSI or OBV bullish div | — | — | None detected |
| **Consecutive Reds** | 5% | 5+ red days | — | 3-4 red days | <3 red days |

### Divergence Detection

**Bullish Divergence:** Price makes lower low, but RSI/OBV makes higher low.
- Lookback: 14 days
- Indicates: Selling pressure exhausted, potential bounce

---

## Downside Reversal Score

**Purpose:** Detect potential tops and pullback risk.

**Score Range:** 1-10 (higher = stronger downside reversal signal)

### Weighting

| Factor | Weight | 10 Points | 7 Points | 5 Points | 2 Points |
|--------|--------|-----------|----------|----------|----------|
| **RSI Position** | 25% | RSI >75 | RSI 65-75 | RSI 50-65 | RSI <50 |
| **Stochastic** | 20% | %K >80 + bearish cross | %K >80 | %K 70-80 | %K <50 |
| **MACD Histogram** | 15% | Pos→Neg flip | — | Narrowing positive | Widening positive |
| **Price vs SMA200** | 15% | Just crossed below | >20% above (extended) | 10-20% above | Below |
| **Volume Spike** | 10% | >2x avg on DOWN day | — | 1.5x avg | Normal |
| **Divergence** | 10% | RSI or OBV bearish div | — | — | None detected |
| **Consecutive Greens** | 5% | 5+ green days | — | 3-4 green days | <3 green days |

### Divergence Detection

**Bearish Divergence:** Price makes higher high, but RSI/OBV makes lower high.
- Lookback: 14 days
- Indicates: Buying pressure exhausted, distribution underway

---

## Trigger Rules

### High Priority Triggers

| ID | Type | Condition | Action | Cooldown |
|----|------|-----------|--------|----------|
| `upside_reversal_score` | Reversal | Score ≥ 7 | BUY | 7 days |
| `downside_reversal_score` | Reversal | Score ≥ 7 | SELL | 7 days |
| `golden_cross` | MA Cross | SMA50 crosses above SMA200 | BUY | 30 days |
| `death_cross` | MA Cross | SMA50 crosses below SMA200 | SELL | 30 days |
| `price_crosses_above_ma` | Trend | Price crosses above SMA200 | BUY | 14 days |
| `price_crosses_below_ma` | Trend | Price crosses below SMA200 | SELL | 14 days |

### Medium Priority Triggers

| ID | Type | Condition | Action | Cooldown |
|----|------|-----------|--------|----------|
| `rsi_bounce_oversold` | Momentum | RSI crosses above 30 from below | BUY | 5 days |
| `rsi_drop_overbought` | Momentum | RSI crosses below 70 from above | SELL | 5 days |
| `stoch_bullish_cross` | Momentum | %K crosses above %D while both <20 | BUY | 5 days |
| `stoch_bearish_cross` | Momentum | %K crosses below %D while both >80 | SELL | 5 days |

### Watch Triggers

| ID | Type | Condition | Action | Cooldown |
|----|------|-----------|--------|----------|
| `macd_histogram_flip_positive` | Momentum | Histogram turns positive | WATCH | 3 days |
| `macd_histogram_flip_negative` | Momentum | Histogram turns negative | WATCH | 3 days |

---

## Cooldown System

Cooldowns prevent alert fatigue by suppressing repeated triggers.

### How It Works
1. When a trigger fires, it's recorded with a timestamp
2. If the same trigger fires again within the cooldown period, it's suppressed
3. Cooldown resets after expiration

### Recommended Cooldowns

| Trigger Category | Cooldown | Rationale |
|------------------|----------|-----------|
| **Reversal Scores** | 7 days | Allow recovery/continuation time |
| **Golden/Death Cross** | 30 days | Rare events, don't spam |
| **SMA200 Crosses** | 14 days | Moderate frequency |
| **RSI Bounces/Drops** | 5 days | Can oscillate frequently |
| **MACD Flips** | 3 days | Early warning, frequent |

---

## Signal Priority Hierarchy

When multiple signals fire, they're categorized:

1. **🟢 UPSIDE REVERSAL** — High conviction buy signals
2. **🔴 DOWNSIDE REVERSAL** — High conviction sell signals  
3. **BUY** — Standard buy triggers
4. **SELL** — Standard sell triggers
5. **WATCH** — Early warning, no immediate action

---

## Customization

### Adding Ticker-Specific Triggers

In `config/watchlist.json`, override defaults per ticker:

```json
{
  "symbol": "NVDA",
  "theme": "AI/GPU",
  "triggers": [
    {"type": "price_below", "value": 120, "action": "BUY", "note": "Key support"},
    {"type": "rsi_oversold", "threshold": 25, "action": "BUY"}
  ]
}
```

### Adjusting Default Thresholds

Modify `default_triggers` in `watchlist.json`:

```json
{
  "type": "upside_reversal_score",
  "threshold": 8,  // Stricter than default 7
  "action": "BUY",
  "cooldown_days": 10
}
```

---

## Future Enhancements

- [ ] Multi-timeframe confluence (weekly + daily alignment)
- [ ] Sector rotation signals
- [ ] Earnings date proximity filter
- [ ] Volume profile analysis
- [ ] Support/resistance level detection
