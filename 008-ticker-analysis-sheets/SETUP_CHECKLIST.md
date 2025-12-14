# Setup Checklist - Quick Reference

## Step 1: Python Dependencies

Install required packages:
```bash
pip install -r requirements.txt
```

Or with a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt
```

---

## ⬜ Step 2: Google Cloud Service Account Setup

### 2.1 Create Google Cloud Project
1. Go to https://console.cloud.google.com/
2. Click project dropdown → **"New Project"**
3. Name: "Stock Analyzer" (or any name)
4. Click **"Create"**

### 2.2 Enable APIs
1. Go to **"APIs & Services"** → **"Library"**
2. Search and enable:
   - **Google Sheets API** → Enable
   - **Google Drive API** → Enable

### 2.3 Create Service Account
1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"Create Credentials"** → **"Service Account"**
3. Name: `sheet-data-loader`
4. Click **"Create and Continue"**
5. Skip role assignment → **"Continue"**
6. Click **"Done"**

### 2.4 Download JSON Key
1. Click on the service account email (e.g., `sheet-data-loader@your-project.iam.gserviceaccount.com`)
2. Go to **"Keys"** tab
3. Click **"Add Key"** → **"Create new key"**
4. Select **"JSON"** → **"Create"**
5. **Save the file as `google_service_account.json` in this project folder**

⚠️ **IMPORTANT:** Keep this file secure! Don't commit it to git.

---

## ⬜ Step 3: Get Twelve Data API Key

1. Go to https://twelvedata.com/
2. Click **"Get Started Free"** or **"Sign Up"**
3. Create account (email or Google/GitHub)
4. After login, go to **Dashboard** → **API Keys**
5. Copy your API key

**Free tier limits:**
- 800 API calls per day
- 8 API calls per minute

---

## Step 4: Get Grok API Key

1. Go to: https://console.x.ai/
2. Create an account and generate an API key
3. Format: `xai-...` (starts with "xai-")

---

## ⬜ Step 5: Configure sheet_loader_config.json

Edit `sheet_loader_config.json` and update:

1. **`google_sheets.spreadsheet_name`**: Your exact Google Sheet name (case-sensitive)
   - Example: `"Retail Hype Scorer"` (must match exactly)

2. **`twelve_data.api_key`**: Your Twelve Data API key
   - Replace `"YOUR_TWELVE_DATA_API_KEY"` with your actual key

3. **`grok.api_key`**: Your Grok API key
   - Replace `"xai-YOUR_GROK_API_KEY"` with your actual key (include "xai-" prefix)

---

## ⬜ Step 6: Share Google Sheet with Service Account

1. Open your Google Sheet (the one named in config)
2. Click **"Share"** button (top right)
3. In the service account JSON file (`google_service_account.json`), find the `"client_email"` field
   - It looks like: `sheet-data-loader@your-project.iam.gserviceaccount.com`
4. Paste this email into the "Add people" field
5. Set permission to **"Editor"**
6. **Uncheck** "Notify people"
7. Click **"Share"**

---

## ⬜ Step 7: Prepare Your Google Sheet

### Main Tab Structure
Your main tab (e.g., "Hype Scorer") should have:
- **Column A**: Ticker symbols (AAPL, NVDA, GME, etc.)
- **Row 1**: Header row (will be skipped)
- **Row 2+**: Ticker symbols

### Helper Tabs
The script will auto-create these tabs if they don't exist:
- `Tech_Data` - Technical indicators
- `Transcripts` - Earnings transcript summaries

---

## Step 8: Test the Setup

### Dry Run (Test without writing to sheet)
```bash
source venv/bin/activate  # If using venv
python sheet_data_loader.py --dry-run --verbose
```

### Full Run
```bash
python sheet_data_loader.py --verbose
```

---

## Troubleshooting

### "Spreadsheet not found"
- Check `spreadsheet_name` in config matches EXACTLY (case-sensitive)
- Verify you shared the sheet with the service account email

### "Permission denied"
- Make sure service account has "Editor" access (not "Viewer")

### "Rate limit exceeded" (Twelve Data)
- Free tier: 8 calls/minute, 800/day
- Script has built-in rate limiting (0.5s between calls)
- Wait or upgrade to paid plan

### "defeatbeta not installed"
- Already installed! If you see this, make sure you activated the virtual environment:
  ```bash
  source venv/bin/activate
  ```

---

## Next Steps After Setup

1. ✅ Run `python sheet_data_loader.py --verbose` to fetch data
2. ✅ Check the `Tech_Data` and `Transcripts` tabs in your Google Sheet
3. ✅ Run the Hype Scorer from Google Sheets menu: **🚀 Hype Scorer v9.0** → **Score All Tickers**

---

## Quick Command Reference

```bash
# Activate virtual environment
source venv/bin/activate

# Test run (no data written)
python sheet_data_loader.py --dry-run --verbose

# Full run
python sheet_data_loader.py --verbose

# Custom config file
python sheet_data_loader.py --config custom_config.json
```

