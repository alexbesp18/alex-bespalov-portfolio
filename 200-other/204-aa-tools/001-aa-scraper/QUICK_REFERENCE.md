# AA Points Monitor - Quick Reference

## One-Line Summary
Automated system to find high-yield AA Loyalty Point opportunities by monitoring SimplyMiles (142 offers), eShopping Portal, and AAdvantage Hotels, alerting Alex via Resend email when deals exceed thresholds.

## Alex's Goal
- **Current:** Gold (40K LPs) → **Target:** Platinum (75K LPs) = **35K LP gap**
- **Budget:** ~$500/mo | **Strategy:** Minimal spend, maximum LP yield

## The Money Maker: Stacking
```
Portal (X mi/$) + SimplyMiles (bonus) + CC (1 mi/$) = Combined Yield
Example: $5 Kindle purchase → 10 + 135 + 5 = 150 LPs = 30 LP/$
```

## Tech Stack
- **VPS:** $6/mo DigitalOcean/Vultr, Ubuntu 24.04
- **Language:** Python 3.11 + Playwright
- **Database:** SQLite (local file)
- **Email:** Resend (novaconsultpro.com verified)
- **Auth:** Playwright persistent browser context for SimplyMiles

## Alert Thresholds
| Type | Immediate | Daily Digest |
|------|-----------|--------------|
| Stacked deals | ≥15 LP/$ | ≥10 LP/$ |
| Hotels | ≥25 LP/$ | ≥15 LP/$ |

## Scrape Schedule
- SimplyMiles: Every 2 hours (authenticated)
- Portal: Every 4 hours (public)
- Hotels: Every 6 hours (public)
- Daily digest: 8am CT

## Priority Cities for Hotels
Austin, Dallas, Houston, Las Vegas, New York, Boston, San Francisco, Los Angeles

## Key Files
- `PROJECT_HANDOFF.md` — Full context (this is the comprehensive doc)
- `scrapers/simplymiles.py` — Playwright + saved session
- `core/stack_detector.py` — Match SimplyMiles ↔ Portal
- `alerts/sender.py` — Resend integration

## Build Order
1. SimplyMiles scraper + auth setup
2. Portal scraper  
3. Stack detection logic
4. Alert system (Resend)
5. Hotel scraper
6. VPS deployment + cron

## Credentials Needed
- `RESEND_API_KEY` — Alex has this
- SimplyMiles login — AA credentials, Mastercard already linked
