# Bitcoin Mining Calculator Suite - Project Summary

## Overview

This suite contains 7 specialized tools for Bitcoin mining profitability analysis, portfolio management, and related financial calculations. All React applications share a common library (`100-shared-core`) for calculations, constants, and utilities.

**Consolidated from 9 original projects to 7** (Dec 2025):
- Merged: 102-electricity-calculator → 101
- Merged: 105-acquisition-calculator → 101
- Merged: 106-hosted-portfolio → 104

---

## Project Directory

| # | Directory | Name | Purpose |
|---|-----------|------|---------|
| 100 | `100-shared-core` | Shared Core Library | NPM package with shared calculations, constants, formatters |
| 101 | `101-mining-profitability-calculator` | Mining Profitability Calculator | Matrix comparison of miner profitability |
| 102 | `102-btc-loan-calculator` | BTC Loan Calculator | Bitcoin-backed loan risk management |
| 103 | `103-miner-price-tracker` | Miner Price Tracker | Historical miner hardware price tracking |
| 104 | `104-portfolio-analyzer` | Portfolio Analyzer | Comprehensive investment portfolio analysis |
| 105 | `105-landing-page` | Landing Page | Marketing page linking to all calculators |
| 106 | `106-miner-price-scraper` | Miner Price Scraper | Python/Jupyter scraper for OneMiners marketplace |

---

## Detailed Project Descriptions

### 100-shared-core

**Type:** NPM Package (`@btc-mining/shared-core`)

**Purpose:** Central library providing shared utilities, calculations, and constants used across all calculator applications.

**Key Modules:**

| Module | Description |
|--------|-------------|
| `calculations/mining.js` | Core mining math: daily BTC, monthly profit, breakeven analysis |
| `calculations/projections.js` | Multi-year profit projections (1-3 years) |
| `calculations/taxes.js` | MACRS depreciation, federal/state tax calculations |
| `calculations/risk.js` | IRR, NPV, quick insights, risk metrics |
| `calculations/options.js` | Black-Scholes options valuation |
| `constants/bitcoin.js` | Block reward, blocks/day, halving dates |
| `constants/electricity.js` | Electricity rate presets by region |
| `constants/tax.js` | MACRS rates, state tax rates |
| `data/miners.js` | Canonical miner database (31 models) |
| `data/scenarios.js` | Market scenario presets |
| `formatters/*` | Currency, numbers, hashrates, dates |
| `storage/*` | localStorage with compression, migration |
| `validation/*` | Number validation, miner schema validation |
| `hooks/*` | useLocalStorage, useMiningCalculations, useScenarios |

**Tech Stack:**
- Pure JavaScript ES6+
- Babel for transpilation
- Jest for testing

**Usage:**
```javascript
import {
  calculateMonthlyProfit,
  MINER_DATABASE,
  formatCurrency,
  useLocalStorage
} from '@btc-mining/shared-core';
```

---

### 101-mining-profitability-calculator

**Type:** React Application

**Purpose:** Compare mining profitability across multiple miners and electricity rates in a matrix view. Includes Acquisition Mode for reverse calculations.

**Key Features:**
- **Matrix View:** Side-by-side comparison of 20+ miner models
- **Electricity Rate Columns:** $0.047 - $0.10/kWh profitability grid
- **Projections:** 1-year and 2-year profit forecasts
- **Scenarios:** Conservative, Current Market, Bullish presets
- **Tax Optimization:** MACRS depreciation, bonus depreciation
- **Export:** CSV export of profit matrix
- **Heat Map:** Color-coded profitability visualization
- **Acquisition Mode:** Calculate maximum purchase price to achieve target profit (merged from old 105 project)

**Calculations Performed:**
- Daily/monthly BTC mined based on network hashrate share
- Electricity costs based on power consumption
- Pool fees (default 2%)
- Federal + state tax impact
- After-tax profit and ROI
- Breakeven electricity rate

**Main Component:** `src/components/MiningCalculator.js` (73.8 KB)

**Input Parameters:**
| Parameter | Description | Default |
|-----------|-------------|---------|
| BTC Price Start | Starting Bitcoin price | $110,000 |
| BTC Price End | Year-end Bitcoin price | $150,000 |
| Network Hashrate | Network hashrate in EH/s | 900 EH/s |
| Pool Fee | Mining pool fee % | 2% |
| Federal Tax Rate | Federal income tax rate | 35% |
| State Tax Rate | State income tax rate | 0% |
| Bonus Depreciation | 100% first-year depreciation | Enabled |

**Tech Stack:**
- React 19.1.0
- Recharts (charts)
- Tailwind CSS
- lucide-react (icons)

**Deployment:** https://bitcoin-mining-calculator.vercel.app

---

### 102-btc-loan-calculator

**Type:** React Application

**Purpose:** Risk management tool for Bitcoin-backed loans with LTV monitoring and liquidation analysis.

**Key Features:**
- **LTV Monitoring:** Real-time loan-to-value ratio tracking
- **Liquidation Alerts:** Calculate exact liquidation price
- **Margin Call Warnings:** Buffer to margin call threshold
- **Price Shock Scenarios:** Model sudden BTC price drops
- **Future Projections:** Project loan health over time
- **Interest Calculations:** Daily/monthly interest costs

**Calculations Performed:**
- Current LTV = Loan Amount / Collateral Value
- Liquidation Price = Loan / (BTC * Liquidation LTV)
- Buffer to Margin Call ($ and %)
- Available borrowing power at target LTV
- Withdrawable collateral while maintaining target LTV

**Main Component:** `src/App.js` (32.8 KB)

**Input Parameters:**
| Parameter | Description | Default |
|-----------|-------------|---------|
| BTC Collateral | Amount of BTC as collateral | 0.05 BTC |
| Current BTC Price | Current market price | $65,000 |
| Loan Amount | USD loan amount | $0 |
| Annual Interest Rate | Loan APR | 5% |
| Target LTV | Desired loan-to-value ratio | 50% |
| Margin Call LTV | Margin call threshold | 70% |
| Liquidation LTV | Forced liquidation threshold | 80% |

**Tech Stack:**
- React 19.1.0
- Tailwind CSS (inline)
- lucide-react (icons)

**Deployment:** https://btc-loan-calculator.vercel.app

---

### 103-miner-price-tracker

**Type:** React Application

**Purpose:** Track historical miner hardware prices over time with data import/export capabilities.

**Key Features:**
- **Price History:** Track miner prices across dates
- **Data Import:** Upload Excel (.xlsx) or CSV files
- **Intraday Tracking:** Multiple price updates per day
- **Rollback:** Undo recent data changes
- **Miner Database:** Built-in efficiency specifications
- **Charts:** Price trend visualizations
- **Search/Filter:** Find miners by model, manufacturer

**Data Management:**
- LocalStorage with versioning (v1.1.0)
- Compression for large datasets
- Upload history tracking
- Max price tracking per miner

**Main Component:** `src/components/MinerPriceTracker.js` (82.5 KB)

**Supported File Formats:**
| Format | Library |
|--------|---------|
| Excel (.xlsx) | xlsx |
| CSV | papaparse |

**Tech Stack:**
- React 19.1.0
- Recharts (charts)
- xlsx (Excel parsing)
- papaparse (CSV parsing)
- lucide-react (icons)

**Deployment:** https://miner-price-tracker.vercel.app

---

### 104-portfolio-analyzer

**Type:** React Application

**Purpose:** Comprehensive investment portfolio analysis across multiple asset classes including Bitcoin, stocks, mining operations, and options.

**Key Features:**
- **Multi-Asset Tracking:** BTC cold storage, stocks (MSTR, NVDA), mining, options
- **Options Valuation:** Black-Scholes approximation for calls/puts
- **Mining Operations:** Track multiple hosting providers
- **Debt Management:** Credit card payoff strategies
- **Withdrawal Planning:** Optimal withdrawal strategies
- **Risk Analysis:** Concentration metrics, volatility assessment
- **Projections:** 3-month to 3-year forecasts

**Asset Categories:**
| Category | Description |
|----------|-------------|
| BTC Cold Storage | Bitcoin held in cold wallets |
| Growth Stocks | General equity positions |
| MSTR Stock | MicroStrategy specific tracking |
| BTC Miners | Hosted mining operations |
| Options | IBIT, MSTR, NVDA calls/puts |
| Debt | Credit card balances |

**Calculations Performed:**
- Portfolio total value and allocation %
- Mining profitability per provider
- Options intrinsic/time value
- Debt payoff optimization (avalanche vs snowball)
- Withdrawal tax efficiency

**Main Component:** `src/components/PortfolioAnalyzer.js` (82.3 KB)

**Tech Stack:**
- React 19.1.0
- Recharts (pie charts, line charts, bar charts)
- xlsx, papaparse (data import)
- Tailwind CSS
- lucide-react (icons)

**Deployment:** https://portfolio-analyzer.vercel.app

---

### 105-landing-page

**Type:** React Application

**Purpose:** Marketing landing page that aggregates and links to all calculator tools.

**Key Features:**
- **Calculator Directory:** Cards for each tool with descriptions
- **Feature Highlights:** Key capabilities per tool
- **Trust Indicators:** Privacy, real-time calculations, tax optimization
- **Donation Links:** Strike and BTC address for tips
- **Responsive Design:** Mobile-friendly layout

**Listed Calculators:**
1. Bitcoin Mining Profitability Calculator (101) - includes Acquisition Mode
2. BTC Loan Calculator (102)
3. Miner Price Tracker (103)
4. Portfolio Analyzer (104) - includes multi-company hosting
5. Retirement Inflation Calculator (external)

**Main Component:** `src/App.js` (12.0 KB)

**Tech Stack:**
- React 19.1.0
- Tailwind CSS
- lucide-react (icons)

**Deployment:** https://mine-and-hodl.vercel.app

---

### 106-miner-price-scraper

**Type:** Python/Jupyter Notebook

**Purpose:** Web scraping tool to extract miner listings from the OneMiners marketplace.

**Key Features:**
- **Selenium Automation:** Headless Chrome browser automation
- **OneMiners Integration:** Login and scrape marketplace
- **Data Extraction:** Model, hashrate, price, location, energy price
- **JSON Export:** Timestamped data files
- **Multi-Crypto Support:** BTC, KAS, ALPH, DOGE, ALEO, LTC miners

**Extracted Fields:**
| Field | Example |
|-------|---------|
| cryptocurrency | BTC, KAS, ALPH |
| model_name | Antminer S21 - 233 TH/s |
| hashrate | 21 TH/s |
| location | Unknown |
| energy_price | $0.065/kWh |
| current_price | 5,500 USD |
| sale_price | 5,200 USD |
| daily_earnings | $12.50 |
| shared | true/false |

**Main File:** `scrape_oneminers.ipynb`

**Tech Stack:**
- Python 3.11
- Selenium + webdriver-manager
- BeautifulSoup4
- Pandas
- Jupyter Notebook

**Dependencies:**
```
selenium>=4.23.1
webdriver-manager>=4.0.2
pandas>=1.5.0
openpyxl>=3.0.0
jupyter>=1.0.0
requests>=2.28.0
beautifulsoup4>=4.11.0
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    105-landing-page                              │
│                   (Marketing/Directory)                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │ links to
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────────┐
│ 101-mining-     │ │ 102-btc-    │ │ 103-miner-      │
│ profitability   │ │ loan        │ │ price-tracker   │
│ calculator      │ │ calculator  │ │                 │
└────────┬────────┘ └──────┬──────┘ └────────┬────────┘
         │                 │                  │
         └─────────────────┼──────────────────┘
                           │ imports from
                           ▼
              ┌────────────────────────┐
              │    100-shared-core     │
              │  @btc-mining/shared-core│
              └────────────────────────┘
                           ▲
         ┌─────────────────┘
         │ imports from
┌────────┴────────┐
│ 104-portfolio-  │
│ analyzer        │
└─────────────────┘

┌─────────────────┐
│ 106-miner-      │  (Python - separate ecosystem)
│ price-scraper   │
└─────────────────┘
```

---

## Shared Dependencies

All React applications share these core dependencies:

| Package | Version | Purpose |
|---------|---------|---------|
| react | 19.1.0 | UI framework |
| react-dom | 19.1.0 | DOM rendering |
| react-scripts | 5.0.1 | Build tooling |
| @btc-mining/shared-core | file:../100-shared-core | Shared library |
| lucide-react | ^0.522.0 | Icons |

**Optional per-project:**
| Package | Used In | Purpose |
|---------|---------|---------|
| recharts | 101, 103, 104 | Charts/visualizations |
| tailwindcss | 101, 104 | CSS framework |
| xlsx | 103, 104 | Excel file parsing |
| papaparse | 103, 104 | CSV parsing |

---

## Deployment URLs

| Project | URL |
|---------|-----|
| 101 Mining Calculator | https://bitcoin-mining-calculator.vercel.app |
| 102 BTC Loan Calculator | https://btc-loan-calculator.vercel.app |
| 103 Miner Price Tracker | https://miner-price-tracker.vercel.app |
| 104 Portfolio Analyzer | https://portfolio-analyzer.vercel.app |
| 105 Landing Page | https://mine-and-hodl.vercel.app |

---

## Consolidation History

**Original Projects (9):**
1. 100-shared-core
2. 101-bitcoin-mining-calculator
3. 102-bitcoin-mining-electricity-calculator *(deleted - features should merge to 101)*
4. 103-btc-loan-calculator
5. 104-miner-price-tracker
6. 105-miner-acquisition-calculator *(deleted - features should merge to 101)*
7. 106-hosted-mining-portfolio *(deleted - features should merge to 104)*
8. 107-crypto-calculators-landing
9. 108-miner-price-analytics
10. 109-portfolio-analyzer

**Consolidated Projects (7):**
1. 100-shared-core
2. 101-mining-profitability-calculator *(renamed)*
3. 102-btc-loan-calculator *(renumbered from 103)*
4. 103-miner-price-tracker *(renumbered from 104)*
5. 104-portfolio-analyzer *(renumbered from 109)*
6. 105-landing-page *(renumbered from 107)*
7. 106-miner-price-scraper *(renumbered from 108)*

**Features Pending Migration:**
- [x] 102's 3-year projections → **Already in shared-core** (`calculateThreeYearProfit`, `calculateMultiYearProjection`)
- [x] 102's halving awareness → **Already in shared-core** (`getEffectiveBlockReward`, `getHalvingInRange`, `HALVING_DATES`)
- [x] 102's IRR calculations → **Already in shared-core** (`calculateIRR`, `calculateNPV`, `calculateRiskMetrics`)
- [x] 105's acquisition mode → add to 101 as toggle (**COMPLETED**)
- [x] 101 now imports constants from shared-core (BLOCK_REWARD, BLOCKS_PER_DAY, MACRS_RATES)
- [x] 106's multi-company tracking → **Already in 104** (miningProviders with add/delete/edit per provider)

**All features successfully consolidated!**

---

## Future Improvements

1. ~~**Complete feature merges** from deleted projects into their targets~~ ✅ Done
2. ~~**Standardize on shared-core** - remove remaining duplicate code in 101~~ ✅ Done (101 now imports from shared-core)
3. **Add E2E tests** for critical calculation paths
4. **Create Storybook** for shared components
5. **Add TypeScript** for better type safety
6. **Implement CI/CD** for automated testing and deployment
