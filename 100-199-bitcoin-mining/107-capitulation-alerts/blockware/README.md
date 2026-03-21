# Blockware Capitulation Alert Bot

Monitors the Blockware Solutions miner marketplace for extreme bargain deals
on new-gen Bitcoin miners (S21, S21+, S21 Pro, S21 XP, S21 Hydro, SealMiner A2,
Whatsminer M66S) and sends Telegram alerts when high-quality listings appear at
>=60% discount from their last trade price.

## How it works

- Polls Blockware's public GraphQL API (`opengraphql` endpoint, no auth needed)
- Fetches trade stats via `tradeStatsByModel` (all-time + 90-day windowed)
- **Quality filters**: Skips offers with efficiency > 17.5 W/TH or deal score < 50
- **Primary trigger**: >=60% off last trade price
- **Fallback**: >=60% off 90-day midpoint (if no last trade data)
- **No data**: skips offer entirely (no reliable benchmark)
- Each alert shows 3 discount benchmarks: last trade, ATH, and 90-day average
- Tracks sent alert IDs in `data/sent_alerts.json` to avoid duplicates
- State is committed back to repo by GitHub Actions

## Setup

1. Create a Telegram bot via @BotFather, get the token
2. Get your chat ID (message @userinfobot or create a channel)
3. Add secrets to GitHub repo: `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`
4. Push to GitHub — the cron runs every 10 minutes automatically

## Local testing

```bash
cp .env.example .env
# Edit .env with your real tokens
pip install -r requirements.txt
python -m src.main
```

Without Telegram credentials set, it runs in dry-run mode (prints alerts to console).
