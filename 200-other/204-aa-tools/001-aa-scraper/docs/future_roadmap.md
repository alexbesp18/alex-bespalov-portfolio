# Future Roadmap

Consolidated roadmap covering deployment, enhancements, and new ideas.

---

## Section 1: Deployment & Infrastructure

### Cron Scheduling
**Status:** COMPLETE | **Effort:** Low | **Impact:** High

Running on VPS (REDACTED_VPS_IP) with 7 cron jobs:
```cron
# SimplyMiles - every 10 min (keeps session alive)
*/10 * * * * cd /root/aa_scraper && /root/aa_scraper/venv/bin/python scrapers/simplymiles_api.py

# Portal - every 4 hours
30 */4 * * * cd /root/aa_scraper && /root/aa_scraper/venv/bin/python scrapers/portal.py

# Hotels - every 6 hours
0 */6 * * * cd /root/aa_scraper && /root/aa_scraper/venv/bin/python scrapers/hotels.py

# Stack detection - every 2h (+15m offset)
15 */2 * * * cd /root/aa_scraper && /root/aa_scraper/venv/bin/python scripts/run_all.py --detect

# Alert check - every 2h (+20m offset)
20 */2 * * * cd /root/aa_scraper && /root/aa_scraper/venv/bin/python scripts/run_all.py --alerts

# Daily digest - 8am Central (14:00 UTC)
0 14 * * * cd /root/aa_scraper && /root/aa_scraper/venv/bin/python scripts/send_digest.py

# Hotel matrix verification - weekly Sunday 3am
0 3 * * 0 cd /root/aa_scraper && /root/aa_scraper/venv/bin/python scripts/hotel_discovery.py --verify
```

### Push Notifications
**Status:** COMPLETE | **Effort:** Low | **Impact:** High

Implemented in `alerts/push.py` with dual support:
- **ntfy.sh** (free, recommended) - set `NTFY_TOPIC` in .env
- **Pushover** ($5 one-time) - set `PUSHOVER_USER_KEY` and `PUSHOVER_APP_TOKEN`

### Supabase Database
**Status:** COMPLETE (2026-01-03) | **Effort:** Medium | **Impact:** High

Migrated from SQLite to cloud PostgreSQL:
- Web dashboard access
- Accessible from anywhere
- Automatic backups
- 12 tables: simplymiles_offers, portal_rates, hotel_deals, stacked_opportunities, alert_history, scraper_health, hotel_yield_matrix, hotel_yield_history, discovery_progress, merchant_history, deal_discoveries, hotel_yield_baselines

Configuration:
```bash
DB_MODE=supabase
SUPABASE_URL=https://rxsmmrmahnvaarwsngtb.supabase.co
SUPABASE_KEY=eyJ...  # service_role key
```

### VPS Deployment
**Status:** COMPLETE | **Effort:** Medium | **Impact:** High

Running on DigitalOcean droplet:
- IP: REDACTED_VPS_IP
- SSH: `ssh root@REDACTED_VPS_IP`
- VNC: Port 5900, password REDACTED_VNC_PASS (visual debugging)
- Project path: `/root/aa_scraper/`
- Database: Supabase (cloud PostgreSQL)

### FastAPI Backend
**Status:** Planned (Phase 6) | **Effort:** Medium | **Impact:** High

```
GET  /api/v1/deals/stacked          # All stacked opportunities
GET  /api/v1/deals/stacked/top      # Top N by score
GET  /api/v1/deals/hotels           # Current hotel deals
GET  /api/v1/matrix/:city           # Yield matrix for city
GET  /api/v1/health                 # System health status
POST /api/v1/scraper/run/:name      # Trigger scraper manually
```

### HTMX Dashboard
**Status:** Planned (Phase 6) | **Effort:** Medium | **Impact:** Medium

Server-rendered HTML with minimal JavaScript. FastAPI + Jinja2 + HTMX + TailwindCSS.

```
templates/
├── base.html           # Layout with nav
├── dashboard.html      # Main overview
├── deals/stacked.html  # Stacked deals table
├── deals/hotels.html   # Hotel deals grid
└── matrix/heatmap.html # Yield heatmap
```

### Docker Containerization
**Status:** Planned | **Effort:** Medium | **Impact:** Medium

Not prioritized - VPS deployment working well without containerization.

---

## Section 2: Enhancements to Existing Work

### Database Improvements

#### Database Indexes
**Status:** COMPLETE | Created via Supabase dashboard.

#### Automatic Data Cleanup
**Status:** Planned | Lower priority with Supabase (generous storage).

### Scraper Improvements

#### Rate Change Tracking
**Status:** Planned | **Priority:** Low
Track portal rate changes over time to identify trends.

#### Session Auto-Refresh Detection
**Status:** MITIGATED | **Priority:** Low
Session keep-alive service runs every 10 minutes. Proactive warnings at 5 days session age. Manual re-auth workflow documented.

#### Parallel Hotel Scraping
**Status:** Planned | Lower priority (current sequential approach works fine).

### Scoring Improvements

#### Dynamic Thresholds
**Status:** Planned | Adjust thresholds based on recent deal quality.

#### Time-Decay Scoring
**Status:** Implemented | Urgency modifier: +20% for <48h expiration.

### Alert Improvements

#### Smart Batching
**Status:** Implemented | 24-hour cooldown prevents duplicate alerts.

#### Alert Fatigue Prevention
**Status:** Implemented | 20% improvement threshold, 24h cooldown.

### Testing Improvements

#### Test Coverage
**Status:** Good | 154 tests passing. Target 90%+ on core modules.

#### Integration Tests
**Status:** Partial | Full A-Z pipeline test available via `scripts/run_all.py`.

### Code Quality

#### Type Hints
**Status:** Partial | Priority: Medium | Add throughout codebase.

#### Custom Exception Classes
**Status:** COMPLETE | Implemented in `core/exceptions.py`:
- ScraperError, SessionExpiredError, RateLimitError, ParseError
- HttpClientError, ConfigurationError

---

## Section 3: Unexplored Future Ideas

### Browser Extension
Chrome extension showing deal info while shopping:
- Badge indicator with current portal rate
- SimplyMiles offer availability check
- Combined stack yield display
- Quick activate button

### Purchase Tracking & ROI
Track actual purchases to measure realized LP earnings vs expected:
- Manual purchase entry
- Receipt scanning (OCR)
- Running totals and projections

### Multi-Program Support
Expand beyond AA to track multiple loyalty programs:
- United MileagePlus
- Delta SkyMiles
- Chase Ultimate Rewards
- Amex Membership Rewards

### Credit Card Optimization
Recommend best card to use for each purchase based on:
- Bonus categories
- Point transfer partners
- Point valuations

### Flight Award Integration
Connect LP earning to actual flight redemptions:
- Track award availability for target routes
- Calculate "real" LP value based on redemption
- Alert when you have enough for specific flights

### ML-Based Yield Prediction
Predict future yields based on historical patterns:
- Day of week, season, advance booking
- Promotional calendar events
- Anomaly detection for exceptional deals

### Alternative Data Sources
Expand data collection:
- Deal aggregator sites (The Points Guy, Doctor of Credit)
- Reddit r/churning, r/awardtravel
- Email newsletters for limited-time offers

---

## Priority Matrix (Updated)

| Item | Effort | Impact | Status |
|------|--------|--------|--------|
| Cron scheduling | Low | High | COMPLETE |
| Push notifications | Low | High | COMPLETE |
| Add database indexes | Low | High | COMPLETE |
| Supabase migration | Medium | High | COMPLETE |
| VPS deployment | Medium | High | COMPLETE |
| Session stability | Medium | High | COMPLETE |
| FastAPI backend | Medium | High | Next |
| HTMX dashboard | Medium | Medium | Planned |
| Rate change tracking | Low | Medium | Planned |
| Type hints | Medium | Medium | Ongoing |
| Docker setup | Medium | Medium | Low priority |

---

## Implementation Notes

### Completed Infrastructure
- VPS at REDACTED_VPS_IP with 7 cron jobs
- Supabase cloud database (12 tables)
- Email alerts via Resend API
- Push notifications (ntfy.sh + Pushover)
- Session keep-alive service
- Health monitoring system

### Next Phase (Dashboard)
1. Build FastAPI backend for data access
2. Create HTMX dashboard for visual deal browsing
3. Consider authentication for web access

### Low Priority / Future
- Docker containerization (VPS works fine)
- ML-based predictions (current matrix approach sufficient)
- Multi-program support (scope creep)

---

*Last updated: 2026-01-03*
