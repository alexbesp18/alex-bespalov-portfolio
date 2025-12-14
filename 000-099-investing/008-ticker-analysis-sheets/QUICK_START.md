# Quick Start Guide

## Prerequisites

1. Python 3.9+ installed
2. Virtual environment (recommended)
3. Required API keys (see below)

---

## 🎯 What You Need to Do Next

### 1. Google Cloud Service Account (5-10 minutes)

**Steps:**
1. Go to https://console.cloud.google.com/
2. Create a new project (or use existing)
3. Enable **Google Sheets API** and **Google Drive API**
4. Create a service account named `sheet-data-loader`
5. Download the JSON key file
6. **Save it as `google_service_account.json` in this folder**

**Detailed instructions:** See `SETUP_GUIDE.md` Step 2 (lines 53-101)

---

### 2. Get Twelve Data API Key (2 minutes)

**Steps:**
1. Go to https://twelvedata.com/
2. Sign up for free account
3. Go to Dashboard → API Keys
4. Copy your API key

**Free tier:** 800 calls/day, 8 calls/minute

---

### 3. Update Configuration File

Edit `sheet_loader_config.json`:

```json
{
  "google_sheets": {
    "spreadsheet_name": "YOUR_EXACT_SHEET_NAME_HERE",  // ← Change this!
    ...
  },
  "twelve_data": {
    "api_key": "YOUR_TWELVE_DATA_KEY_HERE"  // ← Change this!
  },
  "grok": {
    "api_key": "YOUR_GROK_API_KEY_HERE"  // ← Change this!
  }
}
```

**Important:** 
- `spreadsheet_name` must match your Google Sheet name EXACTLY (case-sensitive)
- Get your Grok API key from https://console.x.ai/

---

### 4. Share Google Sheet with Service Account

1. Open your Google Sheet
2. Click **Share** button
3. Find the `client_email` in `google_service_account.json`
   - Looks like: `sheet-data-loader@project-name.iam.gserviceaccount.com`
4. Paste that email, give it **Editor** access
5. Uncheck "Notify people"
6. Click **Share**

---

### 5. Test It!

```bash
# Activate virtual environment (if using one)
source venv/bin/activate

# Test run (doesn't write to sheet)
python sheet_data_loader.py --dry-run --verbose

# If that works, do a real run
python sheet_data_loader.py --verbose
```

---

## Setup Checklist

- [ ] Python environment ready
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Google service account JSON file created
- [ ] Twelve Data API key obtained
- [ ] Grok API key obtained
- [ ] Config file created from example and populated
- [ ] Google Sheet shared with service account

---

## 🆘 Need Help?

- **Full setup guide:** `SETUP_GUIDE.md`
- **Quick checklist:** `SETUP_CHECKLIST.md`
- **Troubleshooting:** See `SETUP_GUIDE.md` lines 273-349

---

## 🚀 After Setup

Once everything is configured:

1. Run: `python sheet_data_loader.py --verbose`
2. Check your Google Sheet for `Tech_Data` and `Transcripts` tabs
3. In Google Sheets, use menu: **🚀 Hype Scorer v9.0** → **Score All Tickers**

