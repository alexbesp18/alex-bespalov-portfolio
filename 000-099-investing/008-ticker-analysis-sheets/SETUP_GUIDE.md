# Sheet Data Loader - Setup Guide

Pre-fetch technical data and earnings transcripts for the Google Sheets Hype Scorer.

---

## Overview

This Python script reads tickers from your Google Sheet, fetches:
1. **Technical indicators** from Twelve Data (1 credit per stock, 800/day free)
2. **Earnings transcripts** from defeatbeta-api (free, no limits)
3. **AI summaries** via Grok 4.1 (your existing API key)

Then writes the data to helper tabs that your GAS Hype Scorer can reference.

---

## Prerequisites

- Python 3.9 or higher
- Google Cloud account (free tier works)
- Twelve Data API key (free tier: 800 calls/day)
- Grok API key (you already have this from your GAS script)

---

## Step 1: Install Python Dependencies

```bash
pip install gspread google-auth pandas numpy requests defeatbeta-api duckdb
```

Or create a requirements file:

```bash
# requirements.txt
gspread>=5.12.0
google-auth>=2.23.0
pandas>=2.0.0
numpy>=1.24.0
requests>=2.31.0
defeatbeta-api>=0.1.0
duckdb>=0.9.0
```

Then install:
```bash
pip install -r requirements.txt
```

---

## Step 2: Google Sheets API Setup

### 2.1 Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown at the top → **"New Project"**
3. Enter a name (e.g., "Stock Analyzer") → **"Create"**
4. Wait for project creation, then select it

### 2.2 Enable Google Sheets API

1. In the left sidebar, go to **"APIs & Services"** → **"Library"**
2. Search for **"Google Sheets API"**
3. Click on it → **"Enable"**
4. Also search and enable **"Google Drive API"**

### 2.3 Create Service Account

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"Create Credentials"** → **"Service Account"**
3. Fill in:
   - Service account name: `sheet-data-loader`
   - Service account ID: (auto-fills)
   - Description: (optional)
4. Click **"Create and Continue"**
5. For "Grant this service account access", click **"Continue"** (skip role)
6. Click **"Done"**

### 2.4 Download JSON Key

1. In the Credentials page, find your new service account
2. Click on the service account email (e.g., `sheet-data-loader@your-project.iam.gserviceaccount.com`)
3. Go to the **"Keys"** tab
4. Click **"Add Key"** → **"Create new key"**
5. Select **"JSON"** → **"Create"**
6. Save the downloaded file as `google_service_account.json` in your project folder

**⚠️ Keep this file secure! Don't commit it to git.**

### 2.5 Share Your Google Sheet

1. Open your Hype Scorer Google Sheet
2. Click the **"Share"** button (top right)
3. In the "Add people" field, paste the service account email:
   - Find it in your `google_service_account.json` file under `"client_email"`
   - It looks like: `sheet-data-loader@your-project.iam.gserviceaccount.com`
4. Set permission to **"Editor"**
5. Uncheck "Notify people"
6. Click **"Share"**

---

## Step 3: Get Twelve Data API Key

1. Go to [twelvedata.com](https://twelvedata.com/)
2. Click **"Get Started Free"** or **"Sign Up"**
3. Create an account (email or Google/GitHub)
4. After login, go to **Dashboard** → **API Keys**
5. Copy your API key

**Free tier limits:**
- 800 API calls per day
- 8 API calls per minute
- US equities, forex, crypto included

---

## Step 4: Configure the Script

### 4.1 Copy the Config Template

The config file `sheet_loader_config.json` should be in your project folder.

### 4.2 Edit Configuration

Open `sheet_loader_config.json` and update these values:

```json
{
  "google_sheets": {
    "credentials_file": "google_service_account.json",
    "spreadsheet_name": "Your Exact Sheet Name Here",
    "main_tab": "Hype Scorer",
    "ticker_column": "A",
    "start_row": 2,
    "tech_data_tab": "Tech_Data",
    "transcripts_tab": "Transcripts"
  },

  "twelve_data": {
    "api_key": "your_twelve_data_key_here"
  },

  "grok": {
    "api_key": "xai-your_grok_key_here"
  }
}
```

**Important notes:**
- `spreadsheet_name`: Must match EXACTLY (case-sensitive)
- `main_tab`: The tab containing your ticker list in Column A
- `grok.api_key`: Same key you use in your GAS script

---

## Step 5: Prepare Your Google Sheet

### 5.1 Verify Main Tab Structure

Your main tab (e.g., "Hype Scorer") should have:
- Column A: Tickers (AAPL, NVDA, GME, etc.)
- Row 1: Header row (skipped by script)
- Row 2+: Ticker symbols

### 5.2 Create Helper Tabs (Optional)

The script will auto-create these tabs if they don't exist:

**Tab: `Tech_Data`** (25 columns)
```
Ticker | Price | Change% | RSI | MACD | MACD_Signal | MACD_Hist | ADX | Trend | SMA_20 | SMA_50 | SMA_200 | BB_Upper | BB_Lower | ATR | Stoch_K | Stoch_D | VWAP | OBV_Trend | Volatility | Divergence | Volume_Rel | 52W_High | 52W_Low | Status | Updated
```

**Tab: `Transcripts`** (10 columns)
```
Ticker | Period | Earnings_Date | Char_Count | Key_Metrics | Guidance | Tone | Summary | Status | Updated
```

---

## Step 6: Run the Script

### Basic Usage

```bash
python sheet_data_loader.py
```

### With Options

```bash
# Verbose output (see detailed progress)
python sheet_data_loader.py --verbose

# Dry run (fetch data but don't write to sheet)
python sheet_data_loader.py --dry-run --verbose

# Custom config file location
python sheet_data_loader.py --config /path/to/my_config.json
```

### Expected Output

```
============================================================
SHEET DATA LOADER
============================================================

📋 Reading tickers from 'Hype Scorer' tab, column A...
   Found 25 tickers: NVDA, AAPL, GME, PLTR, TSLA...

📊 FETCHING TECHNICAL DATA (Twelve Data)
----------------------------------------
[1/25] NVDA
    ✅ NVDA: $142.50, RSI=62.4, Trend=UPTREND
[2/25] AAPL
    ✅ AAPL: $189.25, RSI=55.2, Trend=SIDEWAYS
...

📝 FETCHING TRANSCRIPTS (defeatbeta)
----------------------------------------
[1/25] NVDA
    ✅ NVDA 2025Q3: 48,523 chars
    🤖 Summarizing with Grok...
    ✅ Summary complete: Tone=Bullish
...

💾 WRITING TO GOOGLE SHEETS
----------------------------------------
   ✅ Wrote 25 rows to Tech_Data
   ✅ Wrote 20 rows to Transcripts

============================================================
COMPLETE
============================================================
Technical data: 25/25 successful
Transcripts:    20/25 successful

✅ Data written to tabs: 'Tech_Data' and 'Transcripts'
   Now run the Hype Scorer in Google Sheets!
```

---

## Step 7: Verify Data in Google Sheets

1. Open your Google Sheet
2. Check the `Tech_Data` tab:
   - Should have one row per ticker
   - All indicator columns populated
   - Status column shows "OK" or error message

3. Check the `Transcripts` tab:
   - Should have one row per ticker (may be fewer if some don't have transcripts)
   - Key_Metrics, Guidance, Tone, Summary populated
   - Status shows "OK", "NO_DATA", or error message

---

## Step 8: Run the Enhanced Hype Scorer

After running the Python script:

1. In Google Sheets, go to menu: **🚀 Hype Scorer v9.0**
2. Click **"Score All Tickers"**
3. The scorer will now use your pre-fetched technical data and transcript summaries!

---

## Troubleshooting

### "Spreadsheet not found"

**Cause:** Sheet name doesn't match exactly, or not shared with service account.

**Fix:**
1. Check `spreadsheet_name` in config matches your sheet EXACTLY (case-sensitive)
2. Verify you shared the sheet with the service account email
3. The email is in `google_service_account.json` under `client_email`

### "Permission denied"

**Cause:** Service account doesn't have edit access.

**Fix:**
1. Open your Google Sheet
2. Click Share → find the service account
3. Make sure it has "Editor" access (not "Viewer")

### "Rate limit exceeded" from Twelve Data

**Cause:** Too many API calls too fast.

**Fix:**
1. Script has built-in rate limiting (0.5s between calls)
2. If you have 100+ tickers, run in batches or be patient
3. Free tier is 8 calls/minute, 800/day
4. Consider upgrading to Grow plan ($29/month) for no daily limits

### "No transcript found" for many tickers

**Cause:** defeatbeta doesn't have transcripts for all companies.

**This is normal!** Missing transcripts are common for:
- Foreign stocks (non-US companies)
- Small-cap companies
- Pre-revenue/SPAC companies
- Recent IPOs
- Some sectors (utilities, smaller banks)

The Status column will show "NO_DATA" - this is expected, not an error.

### "Grok API error 429"

**Cause:** Grok rate limiting.

**Fix:**
1. The script handles this gracefully (skips summary)
2. Wait a few minutes and re-run
3. Or disable summarization temporarily:
   ```json
   "grok": {
     "summarization_enabled": false
   }
   ```

### "defeatbeta not installed"

**Cause:** Missing Python package.

**Fix:**
```bash
pip install defeatbeta-api duckdb
```

Note: DuckDB is a dependency of defeatbeta-api.

### Script hangs on startup

**Cause:** Usually a network or credential issue.

**Fix:**
1. Check your internet connection
2. Verify `google_service_account.json` path is correct
3. Make sure the JSON file is valid (not corrupted)

---

## Scheduling (Optional)

### Run Before Market Open

**Linux/Mac (cron):**
```bash
# Edit crontab
crontab -e

# Add this line (runs at 9:00 AM ET, Monday-Friday)
0 9 * * 1-5 cd /path/to/project && python sheet_data_loader.py >> loader.log 2>&1
```

**Windows (Task Scheduler):**
1. Open Task Scheduler
2. Create Basic Task → name it "Stock Data Loader"
3. Trigger: Daily at 9:00 AM
4. Action: Start a program
   - Program: `python`
   - Arguments: `C:\path\to\sheet_data_loader.py`
   - Start in: `C:\path\to\project`

**GitHub Actions (free):**
```yaml
# .github/workflows/load_data.yml
name: Load Stock Data
on:
  schedule:
    - cron: '0 13 * * 1-5'  # 9 AM ET (13:00 UTC)
  workflow_dispatch:  # Manual trigger

jobs:
  load:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python sheet_data_loader.py
        env:
          # Store credentials as GitHub secrets
          GOOGLE_CREDS: ${{ secrets.GOOGLE_SERVICE_ACCOUNT }}
```

---

## Cost Summary

| Component | Cost | Limit |
|-----------|------|-------|
| Twelve Data | FREE | 800 calls/day |
| defeatbeta | FREE | Unlimited |
| Grok 4.1 (summarization) | ~$0.002/ticker | ~$0.05 for 25 tickers |
| **Total for 50 tickers** | **~$0.10** | |

---

## Files Reference

```
your_project/
├── sheet_data_loader.py          # Main Python script
├── sheet_loader_config.json      # Your configuration (edit this)
├── google_service_account.json   # Google API credentials (keep secret!)
├── SETUP_GUIDE.md                # This file
└── requirements.txt              # Python dependencies (optional)
```

---

## Next Steps

1. ✅ Complete this setup guide
2. ✅ Run `python sheet_data_loader.py --verbose` to test
3. ⬜ Update your GAS Hype Scorer to read from helper tabs (see `hype_scorer_v9.gs`)
4. ⬜ Set up scheduled runs (optional)

---

## Support

If you run into issues:
1. Check the Troubleshooting section above
2. Run with `--verbose` flag for detailed output
3. Check the Status column in your sheets for specific errors
