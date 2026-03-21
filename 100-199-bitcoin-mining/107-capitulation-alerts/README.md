# Mining Capitulation Alerts

Telegram bots monitoring ASIC miner marketplaces for capitulation deals on new-gen Bitcoin miners.

## Bots

| Bot | Marketplace | Trigger | Schedule |
|-----|-------------|---------|----------|
| **SimpleMining** | SimpleMining.io | >=60% off last trade / 90d avg | Every 10 min + daily digest |
| **Blockware** | Blockware marketplace | >=75% off ATH | Every 10 min + daily digest |

Both bots filter for high-efficiency miners (<=17.5 J/TH), compute revenue/ROI from hashprice, and send structured Telegram alerts with multi-benchmark context.

## Tech Stack

Python, requests, BeautifulSoup, Telegram Bot API, GitHub Actions (cron)
