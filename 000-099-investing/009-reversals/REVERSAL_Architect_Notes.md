# SENTINEL — Portfolio Alert System
## Architect Notes | Dec 2025

---

## TL;DR

Daily automated scan of 50+ AI infrastructure tickers. Email me when buy/sell triggers hit. Run on GitHub Actions (free), pull from Twelve Data API, send via SendGrid.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   ┌──────────┐     ┌──────────────┐     ┌──────────────┐       │
│   │  CRON    │────▶│   GitHub     │────▶│   Python     │       │
│   │ 4:30pm ET│     │   Actions    │     │   Script     │       │
│   └──────────┘     └──────────────┘     └──────────────┘       │
│                                                │                │
│                                                ▼                │
│                                        ┌──────────────┐        │
│                                        │  Twelve Data │        │
│                                        │     API      │        │
│                                        └──────────────┘        │
│                                                │                │
│         ┌──────────────┐                       ▼                │
│         │   GitHub     │◀──────────┬───────────────────┐       │
│         │   Cache      │           │                   │       │
│         │ (prev day)   │     ┌─────┴─────┐    ┌───────┴────┐  │
│         └──────────────┘     │  Compute   │    │  Trigger   │  │
│                              │  Bullish   │───▶│  Engine    │  │
│                              │  Score     │    │            │  │
│                              └───────────┘    └─────┬──────┘  │
│                                                      │         │
│                                                      ▼         │
│                              ┌──────────────┐  ┌──────────┐   │
│                              │   SendGrid   │─▶│  EMAIL   │   │
│                              └──────────────┘  └──────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Schema (from Twelve Data)

Pulling 29 metrics per ticker — here's what matters:

| Category | Metrics | Use |
|----------|---------|-----|
| **Price** | Price, Change%, VWAP | Current state |
| **Momentum** | RSI, MACD, MACD_Signal, MACD_Hist, Stoch_K, Stoch_D | Overbought/oversold |
| **Trend** | ADX, Trend, SMA_20, SMA_50, SMA_200 | Direction + MA stack |
| **Volatility** | BB_Upper, BB_Lower, ATR | Range + stops |
| **Volume** | OBV_Trend, Volume_Rel | Confirmation |
| **Range** | 52W_High, 52W_Low | Context |
| **Computed** | Bullish_Score (1-10), Divergence, Status | Our scoring |

---

## Bullish Score Calculation

Composite 1-10 score. Weights:

```
TREND DIRECTION     25%   STRONG_UP=10, UP=8, SIDEWAYS=5, DOWN=2
MA STACK            20%   20>50>200=10, Mixed=5, Bearish=2  
MACD HISTOGRAM      15%   Positive+expanding=10, Negative=2
RSI POSITION        15%   50-70=10, 30-50=6, extremes=4
OBV TREND           15%   UP=10, SIDEWAYS=5, DOWN=2
ADX STRENGTH        10%   >25=10, 20-25=7, <20=4
```

---

## Trigger Rules

### 🟢 BUY Triggers

| ID | Condition | Priority |
|----|-----------|----------|
| BUY-01 | `Score >= 7 AND Price > SMA_200` | HIGH |
| BUY-02 | `Score >= 8` (regardless of MA) | HIGH |
| BUY-03 | Price crosses ABOVE SMA_200 (was below yesterday) | MEDIUM |
| BUY-04 | Trend flips: DOWNTREND → UPTREND or STRONG_UPTREND | MEDIUM |
| BUY-05 | `Stoch_K < 20 AND Score >= 6` (oversold bounce) | LOW |
| BUY-06 | Price hits custom entry (ticker-specific, see watchlist) | HIGH |

### 🔴 SELL Triggers

| ID | Condition | Priority |
|----|-----------|----------|
| SELL-01 | `Score <= 4 AND Price < SMA_200` | HIGH |
| SELL-02 | `Score <= 3` (regardless of MA) | HIGH |
| SELL-03 | Price crosses BELOW SMA_200 (was above yesterday) | MEDIUM |
| SELL-04 | Trend flips: UPTREND → DOWNTREND | MEDIUM |
| SELL-05 | `OBV_Trend = DOWN AND Divergence = BEARISH` | LOW |

### 🟡 WATCH Triggers

| ID | Condition | Priority |
|----|-----------|----------|
| WATCH-01 | Price within 2% of SMA_200 | MEDIUM |
| WATCH-02 | Score changed +/- 2 from yesterday | LOW |
| WATCH-03 | `Volume_Rel >= 2.0x` (unusual volume) | LOW |
| WATCH-04 | Price within 3% of 52W_High | MEDIUM |

---

## Current Watchlist + Re-Entry Triggers

### EDGE AI Theme

| Ticker | Status | Score | Custom Entry Trigger |
|--------|--------|-------|---------------------|
| **QCOM** | BUY NOW | 8 | — |
| **AAPL** | BUY NOW | 8 | — |
| **SITM** | BUY NOW | 9 | — |
| ARM | WAIT | 6 | `Price <= 138` OR `Price > 153 (SMA50)` |
| PLTR | STARTER | 7 | — |
| DELL | STARTER | 7 | `Price <= 131 (SMA20)` |
| ENVX | SPECULATIVE | 7 | `Price > 10.20 (SMA50)` |
| AMBA | WAIT | 6 | `Price > 83 (SMA50)` |
| SOUN | WAIT | 6 | `Price > 15.44 (SMA50)` |
| CRWD | WAIT | 5 | `Price > 517 (SMA50)` |

### ORBITAL COMPUTE Theme

| Ticker | Status | Score | Custom Entry Trigger |
|--------|--------|-------|---------------------|
| **RKLB** | BUY NOW | 9 | — |
| **RTX** | BUY NOW | 8 | — |
| **LITE** | BUY NOW | 9 | — |
| **PL** | BUY NOW | 9 | — |
| **ASTS** | BUY NOW | 8 | — |
| LUNR | STARTER | 7 | — |
| AMD | WAIT | 5 | `Price > 224 (SMA20)` with volume |
| CACI | WAIT | 6 | `Price > 599 (SMA20)` bounce confirm |
| KTOS | WAIT | 6 | `Price > 82.73 (SMA50)` |
| RDW | AVOID | 6 | `Price > 10.92 (SMA200)` — long way off |
| HON | AVOID | 3 | Broken chart, skip |

### CRITICAL MINERALS Theme

| Ticker | Status | Score | Custom Entry Trigger |
|--------|--------|-------|---------------------|
| **GM** | BUY NOW | 9 | — |
| LMT | STARTER | 7 | — |
| UUUU | STARTER | 6 | `Price > 17.63 (SMA50)` for confirmation |
| USAR | STARTER | 7 | `Price > 20.40 (SMA50)` |
| TROX | STARTER | 7 | `Price > 4.91 (SMA200)` |
| MP | HOLD | 6 | Already own |
| CC | WAIT | 5 | `Price > 13.08 (SMA200)` |
| ABAT | SPECULATIVE | 7 | `Price > 4.93 (SMA50)` |
| METC | AVOID | 3 | Broken |
| NB | WAIT | 6 | `Price > 7.20 (SMA50)` |

### EXISTING PORTFOLIO — Watch for Deterioration

| Ticker | Score | Alert If... |
|--------|-------|-------------|
| CRWV | 3 | Already triggered SELL |
| ORCL | 4 | Already triggered SELL |
| VST | 4 | Already triggered SELL |
| TLN | 4 | Already triggered SELL |
| ANET | 6 | Score drops to 5 or below |
| COIN | 6 | Score drops to 5 or below |
| EQT | 6 | OBV continues DOWN |

---

## Repo Structure

```
sentinel/
├── .github/workflows/
│   └── daily-scan.yml          # Cron trigger
├── src/
│   ├── fetcher.py              # Twelve Data client
│   ├── calculator.py           # Bullish Score
│   ├── triggers.py             # Eval logic
│   └── notifier.py             # SendGrid
├── config/
│   ├── watchlist.yaml          # Tickers + custom triggers
│   └── holdings.yaml           # Current positions (for SELL alerts)
├── data/
│   └── cache.json              # Yesterday's data
├── templates/
│   └── email.html
├── sentinel.py                 # Main
└── requirements.txt
```

---

## Config Format

```yaml
# watchlist.yaml
tickers:
  - symbol: ARM
    theme: Edge AI
    tier: 1
    triggers:
      - type: price_below
        value: 138
        action: BUY
        note: "SMA20/200 support cluster"
      - type: price_above
        value: 153
        action: BUY
        note: "SMA50 breakout"
        
  - symbol: QCOM
    theme: Edge AI
    tier: 1
    triggers: []  # Use default rules only
    
  - symbol: AMD
    theme: Orbital
    tier: 1
    triggers:
      - type: price_above
        value: 224
        action: BUY
        requires_volume: true
        note: "Reclaim SMA20"
```

---

## GitHub Actions Workflow

```yaml
name: SENTINEL Daily Scan

on:
  schedule:
    - cron: '30 21 * * 1-5'  # 4:30 PM ET weekdays
  workflow_dispatch:          # Manual trigger

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Install deps
        run: pip install requests tenacity sendgrid pyyaml
        
      - name: Run scan
        run: python sentinel.py
        env:
          TWELVE_DATA_API_KEY: ${{ secrets.TWELVE_DATA_API_KEY }}
          SENDGRID_API_KEY: ${{ secrets.SENDGRID_API_KEY }}
          NOTIFICATION_EMAIL: ${{ secrets.NOTIFICATION_EMAIL }}
          
      - name: Cache today's data
        uses: actions/cache@v3
        with:
          path: data/cache.json
          key: sentinel-${{ github.run_id }}
```

---

## Email Output Format

```
Subject: [SENTINEL] 3 BUY, 1 SELL — Dec 13

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 BUY SIGNALS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

QCOM (Edge AI) — Score 8 → 8 | $176.03
  ✓ Above 200MA ($157.66)
  ✓ MACD bullish, ADX 29

RKLB (Orbital) — Score 8 → 9 | $61.49  
  ✓ Breakout, ADX 41, Vol 1.3x
  ⚠ Overbought RSI 84

ARM (Edge AI) — CUSTOM TRIGGER | $138.50
  ✓ Hit entry zone ($138)
  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 SELL SIGNALS  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CRWV — Score 7 → 3 | $78.59
  ✗ Below all MAs
  ✗ OBV DOWN, Downtrend
  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟡 WATCH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AMD — Score 5 | $221.56
  → 1.0% below SMA20 ($223.88)
  → Approaching re-entry zone
```

---

## Cost

| Service | Cost | Notes |
|---------|------|-------|
| GitHub Actions | $0 | 2000 min/mo free, need ~150 |
| Twelve Data | $0 | 800 calls/day free tier |
| SendGrid | $0 | 100 emails/day free |
| **Total** | **$0** | |

---

## Implementation Order

1. **Day 1-2**: Fetcher + Score calculator + basic email
2. **Day 3-4**: Trigger engine + cache for delta detection  
3. **Day 5**: Custom trigger YAML parsing
4. **Day 6-7**: Testing with full watchlist, edge cases

---

## Notes for Build

- Rate limit Twelve Data carefully — batch where possible
- Cache previous day in GitHub Actions cache (not artifact)
- SendGrid free tier resets daily, 1-2 emails plenty
- Test with `workflow_dispatch` before relying on cron
- Log everything to Actions console for debugging
- Consider adding Slack webhook as v1.1 enhancement

---

## Questions for Alex

1. Want intraday alerts (more complex) or EOD only?
2. Any tickers need EXCLUDE from general rules?
3. Preferred email format — digest vs individual alerts?
4. Add portfolio value tracking or keep pure technicals?
