# Ticker Analysis Sheets

Google Sheets data loader for automated stock analysis. Fetches technical data and earnings transcripts, then populates Google Sheets for scoring.

## Features

- Twelve Data API integration for technical indicators
- Earnings transcript fetching and summarization
- Google Sheets API integration
- Grok-powered transcript summarization
- Modular loader scripts (technicals, transcripts, combined)

## Setup

1. Copy the example config:
   ```bash
   cp sheet_loader_config.example.json sheet_loader_config.json
   ```

2. Add your API keys to `sheet_loader_config.json`:
   - Twelve Data API key
   - Grok API key

3. Set up Google Cloud service account:
   - Create a service account in Google Cloud Console
   - Download the JSON key file as `google_service_account.json`
   - Share your Google Sheet with the service account email

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

See `SETUP_GUIDE.md` for detailed instructions.

## Usage

Test run (dry run):
```bash
python sheet_data_loader.py --dry-run --verbose
```

Real run:
```bash
python sheet_data_loader.py --verbose
```

## Files

- `sheet_data_loader.py` - Main loader script
- `sheet_data_loader_v2.py` - Updated version
- `sheet_loader_combined.py` - Combined technicals + transcripts
- `sheet_loader_technicals.py` - Technical data only
- `sheet_loader_transcripts.py` - Transcripts only
- `hype_scorer_v9.gs` - Google Apps Script for scoring

## Documentation

- `QUICK_START.md` - Quick setup guide
- `SETUP_GUIDE.md` - Detailed setup instructions
- `SETUP_CHECKLIST.md` - Setup checklist

## Tech Stack

- Python
- Google Sheets API
- Twelve Data API
- Grok API (xAI)
- Google Apps Script

## License

Private/Internal Use

