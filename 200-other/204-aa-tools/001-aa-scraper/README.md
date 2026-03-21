# AA Points Arbitrage Monitor

Automated system to monitor American Airlines loyalty point earning opportunities and alert when exceptional deals arise.

**Strategy:** Minimal dollar commitment, maximum LP (Loyalty Points) yield.

## Overview

This system monitors three data sources to find high-yield LP earning opportunities:

1. **SimplyMiles** - Card-linked offers (requires AA credentials)
2. **AAdvantage eShopping Portal** - Shopping portal rates
3. **AAdvantage Hotels** - Hotel booking bonuses

The magic happens when you **stack** multiple earning channels:

```
Portal (X mi/$) + SimplyMiles (bonus) + Credit Card (1 mi/$) = Combined Yield

Example: $5 Kindle purchase → 10 + 135 + 5 = 150 LPs = 30 LP/$
```

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Configure Environment

```bash
# Copy template and edit with your values
cp env.template .env

# Required settings:
# RESEND_API_KEY=re_xxxxxxxxxxxxx
# ALERT_EMAIL_TO=your@email.com
```

### 3. Set Up SimplyMiles Authentication

```bash
# Opens browser for manual login
python scripts/setup_auth.py

# Follow the prompts to log into SimplyMiles
# Your session will be saved for automated scraping
```

### 4. Run the System

```bash
# Full pipeline: scrape all sources, detect opportunities, send alerts
python scripts/run_all.py

# Or run individual components:
python scrapers/simplymiles.py --test  # Test SimplyMiles scraper
python scrapers/portal.py --test       # Test Portal scraper
python scrapers/hotels.py --test       # Test Hotels scraper
python scripts/send_digest.py --preview  # Preview daily digest
```

### 5. Test Email Delivery

```bash
python scripts/test_alerts.py           # Test immediate alert
python scripts/test_alerts.py --digest  # Test daily digest
```

## Project Structure

```
aa_scraper/
├── config/
│   ├── settings.py          # All thresholds and configuration
│   └── cities.py             # Hotel city configurations
├── scrapers/
│   ├── simplymiles.py        # Playwright-based, authenticated
│   ├── portal.py             # HTTP-based, public
│   └── hotels.py             # API/HTTP hybrid
├── core/
│   ├── database.py           # SQLite operations
│   ├── normalizer.py         # Merchant name matching (rapidfuzz)
│   ├── stack_detector.py     # Opportunity matching
│   └── scorer.py             # Deal scoring logic
├── alerts/
│   ├── sender.py             # Resend email integration
│   ├── evaluator.py          # Threshold checking, deduplication
│   ├── formatter.py          # Email templates
│   └── health.py             # Scraper health monitoring
├── scripts/
│   ├── setup_auth.py         # Initial SimplyMiles login
│   ├── run_all.py            # Full pipeline runner
│   ├── send_digest.py        # Daily digest sender
│   └── test_alerts.py        # Email testing
├── tests/                    # Unit and integration tests
├── docs/
│   └── discovery_notes.md    # Site structure documentation
├── browser_data/             # Playwright session (gitignored)
├── data/                     # SQLite database
└── logs/                     # Log files
```

## Alert Thresholds

| Deal Type | Immediate Alert | Daily Digest |
|-----------|-----------------|--------------|
| Stacked (Portal + SimplyMiles) | ≥15 LP/$ | ≥10 LP/$ |
| Hotels | ≥25 LP/$ | ≥15 LP/$ |
| Portal only | ≥20 LP/$ | ≥10 LP/$ |

## Scoring System

Deals are scored based on:

- **Base yield:** Total miles / spend
- **Low commitment bonus:** +40% for spend <$50, +30% for <$100
- **Urgency bonus:** +20% for offers expiring within 48 hours
- **Austin bonus:** +15% for local hotel deals

## Cron Setup (Production)

```cron
# SimplyMiles - every 2 hours
0 */2 * * * cd /opt/aa-monitor && python scrapers/simplymiles.py

# Portal - every 4 hours
30 */4 * * * cd /opt/aa-monitor && python scrapers/portal.py

# Hotels - every 6 hours
0 */6 * * * cd /opt/aa-monitor && python scrapers/hotels.py

# Stack detection - after scrapers
15 */2 * * * cd /opt/aa-monitor && python -c "from core.stack_detector import run_detection; run_detection()"

# Daily digest - 8am Central
0 8 * * * cd /opt/aa-monitor && python scripts/send_digest.py
```

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_scorer.py

# Run with coverage
pytest --cov=core --cov=alerts
```

## Configuration

All settings are in `config/settings.py`:

- **Alert thresholds:** When to send immediate vs digest alerts
- **Scraper settings:** Delays, retries, staleness thresholds
- **Matching settings:** Fuzzy match threshold, merchant aliases
- **Scoring settings:** Bonus multipliers, penalties

## Troubleshooting

### SimplyMiles session expired

```bash
python scripts/setup_auth.py
```

The system will also email you when re-authentication is needed.

### No offers found

Check the discovery notes and update CSS selectors in the scraper if the site structure changed.

### Email not sending

1. Verify `RESEND_API_KEY` is set in `.env`
2. Test with `python scripts/test_alerts.py`
3. Check Resend dashboard for delivery status

### Database issues

```bash
# View database contents
sqlite3 data/aa_monitor.db ".tables"
sqlite3 data/aa_monitor.db "SELECT * FROM simplymiles_offers LIMIT 5;"

# Reset database (deletes all data)
rm data/aa_monitor.db
python -c "from core.database import get_database; get_database()"
```

## Development

### Adding a new merchant alias

Edit `config/settings.py`:

```python
aliases: dict = field(default_factory=lambda: {
    # Add your alias here
    "new merchant name": "canonical name",
})
```

### Adjusting thresholds

Edit `config/settings.py`:

```python
@dataclass
class AlertThresholds:
    stack_immediate_alert: float = 15.0  # Adjust as needed
    stack_daily_digest: float = 10.0
```

## Status Tracking

- **Current:** Gold (40,000 LPs)
- **Target:** Platinum (75,000 LPs)
- **Gap:** 35,000 LPs

Update in `config/settings.py` as you earn LPs:

```python
current_lp: int = 40000  # Update this
target_lp: int = 75000
```

## License

Personal use only.

---

*Built with Claude Code CLI - December 2024*

