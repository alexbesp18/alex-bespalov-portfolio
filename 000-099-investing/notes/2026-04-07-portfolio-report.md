# Portfolio Analysis Report — April 7, 2026

---

## 1. QA Validation Log

| Check | Result | Notes |
|-------|--------|-------|
| Equity position count (Holdings) | **28 tickers** | Confirmed across Images 2, 3, 4 |
| Equity position count (P&L) | **28 tickers** | Confirmed across Images 6, 7 — matches holdings |
| Options position count (Holdings) | **22 positions** | Confirmed across Images 4 (top), 5 |
| Options position count (P&L) | **22 positions** | Confirmed across Images 7 (top), 8 — matches holdings |
| Ticker reconciliation (Equities) | ✅ PASS | All 28 tickers match 1:1 between holdings and P&L views |
| Ticker reconciliation (Options) | ✅ PASS | All 22 option lines match 1:1 between holdings and P&L views |
| Margin data | ✅ PASS | Image 1 — all fields legible |
| $K abbreviation flag | ⚠️ NOTE | 15 equity positions displayed in "$X.XXK" format (nearest ~$10); 8 options positions in "$X.XXK" format. Exact cents unavailable for those entries. |
| Minor MV discrepancy (Image 2 vs 3) | ⚠️ NOTE | Images 2 and 3 overlap on MPWR–AAOI; slight price drift between captures (e.g., AVGO $969.12 vs $967.70). **Image 2 values used as primary** for this report since it is the more complete screenshot. |

---

## 2. Account & Margin Summary

| Metric | Value |
|--------|-------|
| Cash | $0.00 |
| Margin Total (Borrowing Limit) | $21,000.00 |
| Margin Used (Debt) | $18,102.42 |
| Buying Power | $2,897.58 |
| Margin Buffer | $15,029.51 (26.15%) |

### Leverage & Drawdown Analysis

> ⚠️ **All leverage ratios use equity as the denominator** per prior correction.

| Derived Metric | Value | Calculation |
|----------------|-------|-------------|
| Est. Total Portfolio Market Value | ~$75,480 | Sum of all equity + options MV (see §3) |
| Est. Portfolio Equity | ~$57,380 | Portfolio MV − Margin Debt |
| Margin-to-Equity Ratio | ~31.6% | $18,102 / $57,380 |
| Est. Drawdown to Margin Call (25% maint.) | ~$51,340 (~89.5% of equity) | Portfolio must fall to ~$24,137 MV to trigger call |

**Assessment:** Margin utilization is moderate. The ~89.5% equity drawdown cushion before a margin call is healthy, but $0 cash and full margin deployment leave no dry powder for new opportunities or margin buffer expansion in a sharp selloff.

---

## 3. Estimated Portfolio Totals

| Category | Est. Market Value | Est. Net Unrealized P&L |
|----------|-------------------|-------------------------|
| Equities (28 positions) | ~$44,040 | ~+$2,727 |
| Options (22 positions) | ~$31,470 | ~+$1,028 |
| **Portfolio Total** | **~$75,510** | **~+$3,755** |

> Note: Totals are approximate due to $K-abbreviated display values. Summed figures may differ from Robinhood's internal totals by ±$50.

---

## 4. House Money Positions — Do Not Touch

### Tier 1: Confirmed House Money (Prior Partial Trims Executed)

| Position | Current MV | Unrealized P&L | Status |
|----------|-----------|-----------------|--------|
| **AAOI** — 7.37 shares (equity) | $835.62 | +$275.85 (+49.22%) | 🔒 Do not disturb |
| **INTC $40 Call** — 12/17/2027, 1 buy | $2.26K | +$1,315.00 (+139.15%) | 🔒 Do not disturb |

**Rationale:** Both positions have been previously trimmed to recoup cost basis. Remaining shares/contracts represent pure upside with zero capital at risk. Thesis must fundamentally break before any further action.

### Tier 2: House Money Candidates (High Unrealized Gain — Trim Candidates)

| Position | Unrealized P&L | % Gain | Notes |
|----------|----------------|--------|-------|
| CIEN — 2.27 shares | +$468.09 | +91.04% | Optical networking thesis — consider partial trim |
| POWL — 4.23 shares | +$263.10 | +48.07% | Electrical infrastructure — approaching house money |
| MOD — 4.84 shares | +$271.47 | +36.14% | Electrical infrastructure — approaching house money |
| MU $700/$900 Calls (12/17/2027) | +$508.00 | +35.03% | LEAPS spread — strong gain |
| EQT $60 Call (1/21/2028) | +$706.00 | +31.38% | Energy/nat gas LEAPS — strong gain |
| TER — 3.77 shares | +$275.93 | +30.60% | Semi test equipment — approaching house money |

---

## 5. Full Equity Holdings

| # | Ticker | Shares | Market Value | Unrealized $ | Unrealized % | Sector |
|---|--------|--------|-------------|-------------|-------------|--------|
| 1 | ASML | 4.29 | $5.52K | -$297.55 | -5.12% | Semi Equipment |
| 2 | MU | 14.54 | $5.37K | -$53.33 | -0.98% | Semiconductors (Memory) |
| 3 | BE | 26.95 | $3.56K | -$157.87 | -4.25% | Clean Energy / Fuel Cells |
| 4 | NVDA | 13.75 | $2.40K | -$80.66 | -3.25% | Semiconductors (AI/GPU) |
| 5 | COHR | 8.06 | $2.04K | +$39.42 | +1.98% | Optical / Photonics |
| 6 | LITE | 2.40 | $1.92K | +$387.14 | +25.31% | Optical / Photonics |
| 7 | TSM | 4.78 | $1.62K | -$68.96 | -4.09% | Semiconductor Foundry |
| 8 | KLAC | 0.881218 | $1.34K | +$198.03 | +17.26% | Semi Equipment |
| 9 | AMAT | 3.72 | $1.30K | +$234.88 | +22.03% | Semi Equipment |
| 10 | LRCX | 5.63 | $1.23K | +$161.68 | +15.11% | Semi Equipment |
| 11 | GLW | 8.33 | $1.21K | +$212.92 | +21.34% | Optical / Specialty Glass |
| 12 | EWY | 9.54 | $1.19K | -$12.55 | -1.05% | South Korea ETF |
| 13 | VRT | 4.59 | $1.19K | +$237.95 | +25.11% | Power Infrastructure |
| 14 | TER | 3.77 | $1.18K | +$275.93 | +30.60% | Semi Test Equipment |
| 15 | FN | 2.07 | $1.16K | +$89.51 | +8.35% | Optical / Networking |
| 16 | MPWR | 0.963671 | $1.12K | +$76.98 | +7.36% | Semiconductors (Power) |
| 17 | APH | 8.61 | $1.08K | -$100.78 | -8.50% | Connectors / Networking |
| 18 | MTSI | 4.59 | $1.07K | +$53.29 | +5.26% | Semiconductors (RF/Optical) |
| 19 | MOD | 4.84 | $1.02K | +$271.47 | +36.14% | Electrical Infrastructure |
| 20 | CIEN | 2.27 | $982.09 | +$468.09 | +91.04% | Optical Networking |
| 21 | AVGO | 2.99 | $969.12 | -$31.53 | -3.15% | Semiconductors (Networking) |
| 22 | AMKR | 20.34 | $946.75 | +$54.28 | +6.08% | Semiconductor Packaging |
| 23 | SIMO | 7.24 | $837.93 | -$15.91 | -1.86% | Semiconductors (Storage) |
| 24 | AAOI | 7.37 | $835.62 | +$275.85 | +49.22% | Optical / Fiber 🔒 |
| 25 | POWL | 4.23 | $810.28 | +$263.10 | +48.07% | Electrical Equipment |
| 26 | GEV | 0.848845 | $756.94 | +$144.06 | +23.49% | Power / Energy |
| 27 | ETN | 1.95 | $708.24 | +$9.54 | +1.37% | Power Management |
| 28 | PWR | 1.21 | $673.88 | +$92.08 | +15.83% | Power Infrastructure |

---

## 6. Full Options Holdings

| # | Position | Expiry | Contracts / Type | Market Value | Unrealized $ | Unrealized % | Strategy Label |
|---|----------|--------|-----------------|-------------|-------------|-------------|---------------|
| 1 | VIX 30/40 Calls | 4/15 (AM) | 1 Debit Spread | $78.00 | -$32.00 | -29.63% | ⚠️ Volatility Hedge |
| 2 | VIX 25/35 Calls | 6/17 (AM) | 3 Debit Spreads | $468.00 | +$3.00 | +0.65% | Volatility Hedge |
| 3 | IBIT $40 Put | 6/18 | 1 buy | $398.00 | -$197.00 | -33.11% | ⚠️ Crypto Hedge |
| 4 | IGV $80 Put | 6/18 | 2 buys | $960.00 | -$220.00 | -18.64% | Sector Hedge (Tech/Software) |
| 5 | QQQ $550 Put | 6/18 | 1 buy | $1.43K | +$137.00 | +10.62% | Market Hedge |
| 6 | VIX 25/35 Calls | 9/16 (AM) | 1 Debit Spread | $160.00 | +$10.00 | +6.67% | Volatility Hedge |
| 7 | VIX 20/40 Calls | 9/16 (AM) | 3 Debit Spreads | $1.12K | +$99.00 | +9.76% | Volatility Hedge |
| 8 | KRE $60 Put | 9/18 | 1 buy | $288.00 | -$102.00 | -26.15% | ⚠️ Sector Hedge (Banks) |
| 9 | KRE $60 Put | 12/18 | 2 buys | $750.00 | -$290.00 | -27.88% | ⚠️ Sector Hedge (Banks) |
| 10 | QQQ $540 Put | 12/18 | 1 buy | $2.90K | +$606.00 | +26.52% | Market Hedge |
| 11 | SPY $620 Put | 12/18 | 1 buy | $2.94K | -$43.00 | -1.45% | Market Hedge |
| 12 | XLF $55 Put | 12/18 | 1 buy | $613.00 | -$27.00 | -4.22% | Sector Hedge (Financials) |
| 13 | NVDA $200 Call | 3/19/2027 | 1 buy | $2.21K | +$193.00 | +9.53% | LEAPS Call (AI/Semi) |
| 14 | INTC $40 Call | 12/17/2027 | 1 buy | $2.26K | +$1,315.00 | +139.15% | LEAPS Call (Semi) 🔒 |
| 15 | MU $700/$900 Calls | 12/17/2027 | 1 Debit Spread | $1.96K | +$508.00 | +35.03% | LEAPS Spread (Memory) |
| 16 | NVDA $190 Call | 12/17/2027 | 1 buy | $3.92K | -$1,712.00 | -30.41% | ⚠️ LEAPS Call (AI/Semi) |
| 17 | EEM $70 Call | 1/21/2028 | 1 buy | $359.00 | -$51.00 | -12.44% | LEAPS Call (EM) |
| 18 | EQT $60 Call | 1/21/2028 | 2 buys | $2.96K | +$706.00 | +31.38% | LEAPS Call (Nat Gas/Energy) |
| 19 | EWZ $40 Call | 1/21/2028 | 2 buys | $1.24K | +$16.00 | +1.31% | LEAPS Call (Brazil/EM) |
| 20 | FCX $75 Call | 1/21/2028 | 2 buys | $2.54K | +$461.00 | +22.22% | LEAPS Call (Copper/Mining) |
| 21 | ETHA $30 Call | 6/16/2028 | 1 buy | $388.00 | -$72.00 | -15.65% | LEAPS Call (Crypto/ETH) |
| 22 | XLE $50 Call | 12/15/2028 | 1 buy | $1.50K | -$280.00 | -15.77% | LEAPS Call (Energy) |

---

## 7. Sector Allocation Breakdown (Equities Only)

| Sector | # Positions | Est. Market Value | % of Equity Book | Net P&L |
|--------|-------------|-------------------|------------------|---------|
| **Semiconductors & Equipment** | 12 | ~$23,300 | ~52.9% | ~+$751 |
| ↳ ASML, MU, NVDA, TSM, KLAC, AMAT, LRCX, AVGO, AMKR, SIMO, MPWR, TER | | | | |
| **Optical / Networking / Photonics** | 6 | ~$6,810 | ~15.5% | ~+$1,253 |
| ↳ COHR, LITE, GLW, FN, MTSI, CIEN, AAOI | | | | |
| **Power / Grid / Electrification** | 6 | ~$5,980 | ~13.6% | ~+$873 |
| ↳ BE, VRT, MOD, POWL, GEV, ETN, PWR | | | | |
| **Electrical Infrastructure (Connectors)** | 1 | ~$1,080 | ~2.5% | -$101 |
| ↳ APH | | | | |
| **Emerging Markets ETF** | 1 | ~$1,190 | ~2.7% | -$13 |
| ↳ EWY | | | | |

> Note: Some tickers (LITE, MTSI, COHR) straddle semi and optical categories. Classified by primary revenue driver. AAOI counted in Optical. TER counted in Semis.

---

## 8. Top Winners & Losers

### Equities — Top 5 Winners (by $)

| Ticker | Unrealized $ | % |
|--------|-------------|---|
| CIEN | +$468.09 | +91.04% |
| LITE | +$387.14 | +25.31% |
| AAOI 🔒 | +$275.85 | +49.22% |
| TER | +$275.93 | +30.60% |
| MOD | +$271.47 | +36.14% |

### Equities — Top 5 Losers (by $)

| Ticker | Unrealized $ | % |
|--------|-------------|---|
| ASML | -$297.55 | -5.12% |
| BE | -$157.87 | -4.25% |
| APH | -$100.78 | -8.50% |
| NVDA | -$80.66 | -3.25% |
| TSM | -$68.96 | -4.09% |

### Options — Top 5 Winners (by $)

| Position | Unrealized $ | % |
|----------|-------------|---|
| INTC $40 Call 🔒 | +$1,315.00 | +139.15% |
| EQT $60 Call | +$706.00 | +31.38% |
| QQQ $540 Put (12/18) | +$606.00 | +26.52% |
| MU $700/$900 Calls | +$508.00 | +35.03% |
| FCX $75 Call | +$461.00 | +22.22% |

### Options — Top 5 Losers (by $)

| Position | Unrealized $ | % |
|----------|-------------|---|
| NVDA $190 Call | -$1,712.00 | -30.41% |
| KRE $60 Put (12/18) | -$290.00 | -27.88% |
| XLE $50 Call | -$280.00 | -15.77% |
| IGV $80 Put | -$220.00 | -18.64% |
| IBIT $40 Put | -$197.00 | -33.11% |

---

## 9. Options Strategy Bucket Analysis

### A. Hedge Book (Puts + VIX Spreads)

| Position | Expiry | MV | P&L | % | Time Priority |
|----------|--------|-----|------|---|---------------|
| VIX 30/40 Calls | 4/15 | $78 | -$32 | -29.63% | 🔴 **8 DAYS** |
| VIX 25/35 Calls | 6/17 | $468 | +$3 | +0.65% | 🟡 71 days |
| IBIT $40 Put | 6/18 | $398 | -$197 | -33.11% | 🟡 72 days |
| IGV $80 Put | 6/18 | $960 | -$220 | -18.64% | 🟡 72 days |
| QQQ $550 Put | 6/18 | $1.43K | +$137 | +10.62% | 🟡 72 days |
| VIX 25/35 Calls | 9/16 | $160 | +$10 | +6.67% | 🟢 162 days |
| VIX 20/40 Calls | 9/16 | $1.12K | +$99 | +9.76% | 🟢 162 days |
| KRE $60 Put | 9/18 | $288 | -$102 | -26.15% | 🟢 164 days |
| KRE $60 Put | 12/18 | $750 | -$290 | -27.88% | 🟢 255 days |
| QQQ $540 Put | 12/18 | $2.90K | +$606 | +26.52% | 🟢 255 days |
| SPY $620 Put | 12/18 | $2.94K | -$43 | -1.45% | 🟢 255 days |
| XLF $55 Put | 12/18 | $613 | -$27 | -4.22% | 🟢 255 days |

**Hedge Book Totals:** ~$12,175 MV | Net P&L: ~-$56 | ~16.1% of portfolio

### B. LEAPS Calls (Thematic Leveraged Bets)

| Position | Expiry | MV | P&L | % |
|----------|--------|-----|------|---|
| NVDA $200 Call | 3/19/2027 | $2.21K | +$193 | +9.53% |
| INTC $40 Call 🔒 | 12/17/2027 | $2.26K | +$1,315 | +139.15% |
| MU $700/$900 Calls | 12/17/2027 | $1.96K | +$508 | +35.03% |
| NVDA $190 Call | 12/17/2027 | $3.92K | -$1,712 | -30.41% |
| EEM $70 Call | 1/21/2028 | $359 | -$51 | -12.44% |
| EQT $60 Call | 1/21/2028 | $2.96K | +$706 | +31.38% |
| EWZ $40 Call | 1/21/2028 | $1.24K | +$16 | +1.31% |
| FCX $75 Call | 1/21/2028 | $2.54K | +$461 | +22.22% |
| ETHA $30 Call | 6/16/2028 | $388 | -$72 | -15.65% |
| XLE $50 Call | 12/15/2028 | $1.50K | -$280 | -15.77% |

**LEAPS Book Totals:** ~$19,340 MV | Net P&L: ~+$1,084 | ~25.6% of portfolio

---

## 10. Risk Flags & Thematic Conviction

### ⚠️ Positions Requiring Thesis Review (> −20% Unrealized Loss)

| Position | Unrealized $ | % | Issue |
|----------|-------------|---|-------|
| VIX 30/40 Calls (4/15) | -$32.00 | **-29.63%** | Expiry in 8 days — near-total theta decay likely. Roll or close decision needed **immediately**. |
| IBIT $40 Put (6/18) | -$197.00 | **-33.11%** | Bitcoin rally thesis not playing out. 72 days to expiry — reassess crypto hedge. |
| KRE $60 Put (9/18) | -$102.00 | **-26.15%** | Regional bank stress thesis underwater. Still has 164 days. |
| KRE $60 Put (12/18) | -$290.00 | **-27.88%** | Same thesis, longer-dated tranche. Combined KRE put loss: -$392. |
| NVDA $190 Call (12/17/2027) | -$1,712.00 | **-30.41%** | Largest single $ loss in portfolio. Strike deeply OTM vs current NVDA ~$175. Thesis review: does AI capex justify $190 by Dec 2027? |

### Thematic Conviction Table (Combined Equity + Options P&L by Theme)

| Theme | Equity P&L | Options P&L | Combined P&L | Assessment |
|-------|-----------|-------------|-------------|------------|
| **AI / Semiconductors** | ~+$215 (NVDA, MU, AVGO, TSM, AMKR, SIMO, MPWR) | ~+$304 (NVDA calls net, INTC, MU spread) | ~+$519 | Mixed — INTC LEAPS carrying the book; NVDA $190 Call a major drag |
| **Semi Equipment** | ~+$870 (ASML, KLAC, AMAT, LRCX, TER) | — | ~+$870 | Strong — TER, AMAT, KLAC leading |
| **Optical / Networking** | ~+$1,253 (COHR, LITE, GLW, FN, MTSI, CIEN, AAOI) | — | ~+$1,253 | **Strongest theme** — CIEN +91%, LITE +25%, AAOI +49% |
| **Power / Grid / Electrification** | ~+$873 (BE, VRT, MOD, POWL, GEV, ETN, PWR) | — | ~+$873 | Strong — MOD, POWL, VRT leading |
| **Energy / Commodities** | — | ~+$887 (EQT, FCX, XLE) | ~+$887 | Strong — EQT and FCX carrying |
| **Emerging Markets** | -$13 (EWY) | -$35 (EEM, EWZ) | ~-$48 | Neutral/slight negative — watching |
| **Crypto** | — | -$269 (IBIT put, ETHA call) | ~-$269 | Underwater — both sides losing |
| **Hedge Book (VIX/Index/Sector Puts)** | — | ~-$56 (all put/VIX positions) | ~-$56 | Roughly flat cost of insurance — acceptable |

---

## 11. Time-Sensitivity Alerts

| Priority | Position | Expiry | Days Left | Action Needed |
|----------|----------|--------|-----------|---------------|
| 🔴 **CRITICAL** | VIX 30/40 Calls (4/15) | Apr 15 | **8 days** | Down -29.63%. Theta decay accelerating. Decision: close for salvage value or let expire. |
| 🟡 **WATCH** | VIX 25/35 Calls (6/17) | Jun 17 | 71 days | Roughly breakeven (+0.65%). Monitor VIX levels. |
| 🟡 **WATCH** | IBIT $40 Put (6/18) | Jun 18 | 72 days | Down -33.11%. Thesis needs reassessment before further decay. |
| 🟡 **WATCH** | IGV $80 Put (6/18) | Jun 18 | 72 days | Down -18.64%. Approaching -20% threshold. |
| 🟡 **WATCH** | QQQ $550 Put (6/18) | Jun 18 | 72 days | Profitable (+10.62%). Consider rolling to later expiry to maintain hedge. |

---

## 12. Prioritized Action Items

1. **🔴 IMMEDIATE — VIX 30/40 Calls (4/15):** Expires in 8 days with -29.63% loss. Decide: close for ~$78 salvage or accept total loss. This is the single most time-critical item.

2. **⚠️ THIS WEEK — NVDA $190 Call thesis review:** Largest single-position dollar loss (-$1,712). At -30.41%, well past the -20% review threshold. Evaluate whether NVDA recovery to $190+ by Dec 2027 remains credible given current ~$175 price.

3. **⚠️ THIS WEEK — KRE Put ladder thesis review:** Combined loss of -$392 across two tranches. Regional bank stress thesis underwater. Decide whether to maintain, reduce, or close.

4. **🟡 NEAR-TERM — IBIT $40 Put:** Down -33.11% with 72 days remaining. Bitcoin hedge is bleeding — reassess crypto macro outlook.

5. **🟡 NEAR-TERM — June hedge cluster roll decision:** QQQ $550 Put (6/18), IGV $80 Put (6/18), and IBIT $40 Put (6/18) all expire June 18. Plan roll/close strategy before theta accelerates in May.

6. **📋 PORTFOLIO MAINTENANCE — House money trims:** CIEN (+91%), POWL (+48%), MOD (+36%), and TER (+31%) are strong candidates for partial trims to lock in house money status. Consider trimming to recoup cost basis on at least 1–2 of these.

7. **📋 PORTFOLIO MAINTENANCE — Cash generation:** $0 cash and full margin deployment. Any partial trims from Item 6 would improve margin buffer and provide dry powder.

---

*Report generated April 7, 2026. Data extracted from Robinhood screenshots. Values shown as $K are approximations (±$10). This is not financial advice.*
