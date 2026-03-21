# Alex Bespalov

**Building automated financial analysis systems in Python and React.**

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Astro](https://img.shields.io/badge/Astro-BC52EE?style=for-the-badge&logo=astro&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-3FCF8E?style=for-the-badge&logo=supabase&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)

Everything here runs in production — daily cron jobs, live deployments, real alerts.

---

## Featured Projects

### Stock Technicals Pipeline

Daily automated analysis of 80+ tickers — technical indicators, reversal detection, and oversold scoring — delivered as email alerts every weekday at 4:30 PM ET.

```mermaid
graph LR
    A["007 Ticker Analysis<br/><i>Twelve Data API → cache</i>"] --> B["008 Alerts<br/><i>Score-based triggers</i>"]
    A --> C["009 Reversals<br/><i>Divergence detection</i>"]
    A --> D["010 Oversold<br/><i>Multi-indicator scoring</i>"]
    B --> E["📧 Daily Alert Digest"]
    C --> F["📧 Reversal Signals"]
    D --> G["📧 Oversold Scores"]
```

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Twelve Data](https://img.shields.io/badge/Twelve_Data-1E88E5?style=flat-square)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat-square&logo=github-actions&logoColor=white)
![Resend](https://img.shields.io/badge/Resend-000000?style=flat-square)

Powered by a shared Python library (11k LOC) with RSI, MACD, Bollinger Bands, Williams %R, ADX, and more. GitHub Actions cache shares ticker data across parallel consumer jobs.

---

### LEAPS Options Tracker

Drawdown monitoring for long-dated call options with Black-Scholes delta valuation, dual drawdown tracking (ATH + 30-day rolling peak), and graduated Telegram alerts at -20% / -40% / -60%.

[![Live Demo](https://img.shields.io/badge/Live_Demo-00C853?style=for-the-badge&logo=vercel&logoColor=white)](https://optionstracker-pi.vercel.app)

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Astro](https://img.shields.io/badge/Astro-BC52EE?style=flat-square&logo=astro&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-3FCF8E?style=flat-square&logo=supabase&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-26A5E4?style=flat-square&logo=telegram&logoColor=white)

Python cron fetches daily options data → computes mid-price and drawdowns → persists to Supabase → Astro dashboard renders on Vercel.

---

### Mining Capitulation Alerts

Telegram bots monitoring 2 ASIC miner marketplaces (SimpleMining, Blockware) for capitulation deals — alerts when new-gen hardware drops 60–75% off ATH. Filters by efficiency (≤17.5 J/TH), computes revenue and ROI from live hashprice.

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup-43B02A?style=flat-square)
![Telegram](https://img.shields.io/badge/Telegram-26A5E4?style=flat-square&logo=telegram&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat-square&logo=github-actions&logoColor=white)

Runs every 10 minutes + daily digest. Multi-benchmark discount logic (last trade, ATH, 90-day average).

---

### Product Hunt Weekly Digest

Sunday scraper → AI enrichment via xAI Grok → Supabase storage → email digest with ranked products, AI-generated insights, and category breakdowns.

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup-43B02A?style=flat-square)
![xAI Grok](https://img.shields.io/badge/xAI_Grok-1DA1F2?style=flat-square)
![Supabase](https://img.shields.io/badge/Supabase-3FCF8E?style=flat-square&logo=supabase&logoColor=white)
![Resend](https://img.shields.io/badge/Resend-000000?style=flat-square)

Full pipeline: scrape → AI enrich → upsert → email. Runs automatically every Sunday via GitHub Actions.

---

### Bitcoin Mining Calculators

Suite of 5 production React financial calculators — profitability matrices across electricity rates, BTC-backed loan risk, hardware price tracking, multi-asset portfolio modeling with Black-Scholes options valuation.

[![Mining Calculator](https://img.shields.io/badge/Mining_Calc-00C853?style=for-the-badge&logo=vercel&logoColor=white)](https://bitcoin-mining-calculator.vercel.app)
[![Loan Calculator](https://img.shields.io/badge/Loan_Calc-00C853?style=for-the-badge&logo=vercel&logoColor=white)](https://btc-loan-calculator.vercel.app)
[![Price Tracker](https://img.shields.io/badge/Price_Tracker-00C853?style=for-the-badge&logo=vercel&logoColor=white)](https://miner-price-tracker.vercel.app)
[![Portfolio](https://img.shields.io/badge/Portfolio-00C853?style=for-the-badge&logo=vercel&logoColor=white)](https://portfolio-analyzer.vercel.app)
[![Hub](https://img.shields.io/badge/Hub-00C853?style=for-the-badge&logo=vercel&logoColor=white)](https://mine-and-hodl.vercel.app)

![React](https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black)
![Recharts](https://img.shields.io/badge/Recharts-FF6384?style=flat-square)
![Tailwind](https://img.shields.io/badge/Tailwind-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-000000?style=flat-square&logo=vercel&logoColor=white)

All 5 apps deployed and running on Vercel. Shared zero-dependency JS library for mining calculations, constants, and formatters.

---

## Also Built

- **AA Points Tools** — American Airlines points optimization (SimplyMiles scraper, streak optimizer, hotel search)
- **Shared Core Libraries** — Python (11k LOC) and JavaScript packages powering all projects above

---

## Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)
![React](https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black)
![Astro](https://img.shields.io/badge/Astro-BC52EE?style=flat-square&logo=astro&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-3FCF8E?style=flat-square&logo=supabase&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-000000?style=flat-square&logo=vercel&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat-square&logo=github-actions&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-26A5E4?style=flat-square&logo=telegram&logoColor=white)

---

<details>
<summary>Repository Structure</summary>

```
000-099-investing/
├── 000-shared-core/         # Python library — technical indicators, caching, LLM clients
├── 007-ticker-analysis/     # Cache producer → Twelve Data API + Google Sheets
├── 008-alerts/              # Daily trading alerts → email
├── 009-reversals/           # Mid-term reversal detection
├── 010-oversold/            # Multi-indicator oversold scoring
└── 012-options-tracker/     # LEAPS drawdown monitor + Astro dashboard

100-199-bitcoin-mining/
├── 100-shared-core/         # Shared JS library — calculations, constants, formatters
├── 101-mining-profitability-calculator/
├── 102-btc-loan-calculator/
├── 103-miner-price-tracker/
├── 104-portfolio-analyzer/
├── 105-landing-page/
├── 106-miner-price-scraper/
└── 107-capitulation-alerts/ # SimpleMining + Blockware marketplace bots

200-other/
├── 202-product-hunt-ranking/  # Weekly AI-enriched digest
└── 204-aa-tools/              # AA points optimization suite
```

</details>

---

Austin, TX · [GitHub](https://github.com/alexbesp18) · Open to Data Engineering, AI Engineering, and Quantitative Developer roles
