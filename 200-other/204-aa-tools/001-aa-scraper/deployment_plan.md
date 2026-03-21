# Deployment Plan: AA Points Arbitrage Monitor

## Executive Summary

**What:** Deploy the AA Points Monitor for always-on autonomous operation.

**Current State:** Fully operational locally. All scrapers work, alerts send via email/push, tests pass (151).

**Target State:** 24/7 automated operation with cron scheduling on a dedicated machine.

**Deployment Options:**
| Option | Cost | Complexity | Recommendation |
|--------|------|------------|----------------|
| **Option A: Local Mac (Always-On)** | $0 | Low | Best for testing |
| **Option B: VPS (DigitalOcean)** | $6/mo | Medium | **Recommended** |
| **Option C: Home Server/Raspberry Pi** | $0-50 | Medium | Good alternative |

---

## Decision Required

Before proceeding, choose deployment target:

- [ ] **Option A:** Keep running on local Mac with cron (simplest, but Mac must stay on)
- [ ] **Option B:** Deploy to VPS (recommended for reliability)
- [ ] **Option C:** Deploy to home server/Raspberry Pi

**Recommendation:** Start with **Option A** to validate cron scheduling works, then migrate to **Option B** for reliability.

---

## 1. Deployment Overview

### Components to Deploy

| Component | Type | Notes |
|-----------|------|-------|
| Python application | CLI scripts | No web server needed initially |
| SQLite database | Local file | `data/aa_monitor.db` |
| Browser data | Persistent context | For SimplyMiles auth |
| Cron jobs | System scheduler | 7 scheduled tasks |
| Log files | Rotating logs | 7-day retention |

### Services Already Configured

| Service | Status | Purpose |
|---------|--------|---------|
| Resend API | Configured | Email delivery |
| ntfy.sh | Configured | Push notifications (free) |
| Pushover | Optional | Push notifications ($5) |

### NOT Needed for Initial Deployment

- Web server (no dashboard yet)
- Docker (optional, adds complexity)
- Nginx/SSL (no web interface)
- Domain name (no web interface)
- Database server (SQLite is sufficient)

---

## 2. Accounts & Services Checklist

### Required (Already Have)

```
[x] Resend API
    - URL: https://resend.com
    - Purpose: Email delivery
    - Status: Already configured in .env
    - Cost: Free tier (100 emails/day)

[x] ntfy.sh
    - URL: https://ntfy.sh
    - Purpose: Push notifications
    - Status: Ready to configure
    - Cost: Free (no account needed)
```

### Required for VPS Deployment (Option B)

```
[ ] DigitalOcean Account
    - URL: https://cloud.digitalocean.com/registrations/new
    - Purpose: VPS hosting
    - Tier: Basic Droplet ($6/mo)
    - Signup time: 5 minutes
    - Requires: Credit card or PayPal

[ ] SSH Key (if not already have)
    - Purpose: Secure server access
    - Generate with: ssh-keygen -t ed25519
```

### Optional Enhancements

```
[ ] Pushover (optional)
    - URL: https://pushover.net
    - Purpose: Alternative push notifications
    - Cost: $5 one-time per platform
    - Signup time: 2 minutes

[ ] UptimeRobot (optional)
    - URL: https://uptimerobot.com
    - Purpose: Monitor if scraper is running
    - Cost: Free tier
    - Note: Would need to add health endpoint
```

---

## 3. Credentials & Environment Variables

### Current .env Template

```bash
# Required for all deployments
RESEND_API_KEY=re_xxxxxxxxxxxxx
ALERT_EMAIL_TO=your@email.com
ALERT_EMAIL_FROM=alerts@yourdomain.com
TZ=America/Chicago

# Optional paths (defaults work for local)
DATABASE_PATH=data/aa_monitor.db
BROWSER_DATA_PATH=browser_data
LOG_LEVEL=INFO

# Push notifications (choose one)
NTFY_TOPIC=aa-points-yourname
# PUSHOVER_USER_KEY=xxxxx
# PUSHOVER_APP_TOKEN=xxxxx
```

### Credential Sources

| Variable | Where to Get |
|----------|--------------|
| `RESEND_API_KEY` | Resend Dashboard → API Keys → Create |
| `ALERT_EMAIL_FROM` | Must be verified domain in Resend |
| `NTFY_TOPIC` | Make up unique name, subscribe in ntfy app |
| `PUSHOVER_*` | Pushover Dashboard after purchase |

### Security Notes

```
[ ] .env file is in .gitignore
[ ] No secrets in codebase
[ ] browser_data/ contains session cookies - don't share
```

---

## 4. Pre-Deployment Checklist

### Local Validation (Do First)

```
[ ] All tests pass: pytest tests/ -v
[ ] Full pipeline runs: python scripts/run_all.py
[ ] Email works: python scripts/test_alerts.py
[ ] Push works: python -c "from alerts.push import send_push; send_push('Test', 'Hello')"
[ ] SimplyMiles auth valid: python scrapers/simplymiles_api.py --test
[ ] .env has all required values
```

### File System Ready

```
[ ] logs/ directory exists (or will be created)
[ ] data/ directory exists with aa_monitor.db
[ ] browser_data/ has valid SimplyMiles session
[ ] venv/ has all dependencies installed
```

---

## 5. Deployment Steps

### Option A: Local Mac Deployment

**Time estimate:** 15 minutes

#### Phase A1: Validate Environment

```bash
# 1. Verify virtual environment
[ ] source venv/bin/activate
[ ] python --version  # Should be 3.11+

# 2. Run tests
[ ] pytest tests/ -q
    Expected: 151 passed

# 3. Test full pipeline
[ ] python scripts/run_all.py
    Expected: Scrapers run, no errors
```

#### Phase A2: Configure Push Notifications

```bash
# 1. Choose ntfy topic name (unique to you)
[ ] Edit .env: NTFY_TOPIC=aa-points-alex

# 2. Install ntfy app on phone
[ ] iOS: App Store → "ntfy"
[ ] Android: Play Store → "ntfy"

# 3. Subscribe to your topic in the app
[ ] Open ntfy → + → Enter topic name

# 4. Test push notification
[ ] python -c "from alerts.push import send_push; send_push('Test', 'AA Monitor is working!')"
    Expected: Notification on phone
```

#### Phase A3: Install Cron Jobs

```bash
# 1. Preview cron entries
[ ] python scripts/setup_cron.py --show
    Review the schedule:
    - SimplyMiles: every 2 hours
    - Portal: every 4 hours
    - Hotels: every 6 hours
    - Alerts: 20 min after each cycle
    - Digest: 8am daily

# 2. Install cron jobs
[ ] python scripts/setup_cron.py --install

# 3. Verify installation
[ ] crontab -l
    Expected: See AA-SCRAPER-MANAGED section
```

#### Phase A4: Verify Cron is Running

```bash
# Wait for first scheduled run, then check logs
[ ] ls -la logs/
[ ] tail -20 logs/simplymiles.log
[ ] tail -20 logs/alerts.log

# Or manually trigger a run
[ ] python scripts/run_all.py
```

#### Phase A5: Keep Mac Awake (Important!)

```bash
# Prevent Mac from sleeping
[ ] System Settings → Energy Saver → Prevent automatic sleeping

# Or use caffeinate for testing
[ ] caffeinate -d &  # Prevent display sleep
```

---

### Option B: VPS Deployment (DigitalOcean)

**Time estimate:** 45 minutes

#### Phase B1: Create Droplet

```
1. [ ] Log in to DigitalOcean: https://cloud.digitalocean.com

2. [ ] Create → Droplets

3. [ ] Choose options:
   - Region: San Francisco or nearest
   - Image: Ubuntu 24.04 LTS
   - Size: Basic → Regular → $6/mo (1GB RAM, 1 CPU)
   - Authentication: SSH Key (add your public key)
   - Hostname: aa-scraper

4. [ ] Create Droplet

5. [ ] Note the IP address: _______________
```

#### Phase B2: Initial Server Setup

```bash
# 1. SSH into server
[ ] ssh root@YOUR_IP_ADDRESS

# 2. Create non-root user
[ ] adduser alex
[ ] usermod -aG sudo alex
[ ] rsync --archive --chown=alex:alex ~/.ssh /home/alex

# 3. Log in as new user
[ ] exit
[ ] ssh alex@YOUR_IP_ADDRESS

# 4. Update system
[ ] sudo apt update && sudo apt upgrade -y
```

#### Phase B3: Install Dependencies

```bash
# 1. Install Python and tools
[ ] sudo apt install -y python3.11 python3.11-venv python3-pip git

# 2. Install Playwright system dependencies
[ ] sudo apt install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2

# 3. Verify Python
[ ] python3.11 --version
```

#### Phase B4: Deploy Application

```bash
# 1. Clone or upload project
[ ] cd ~
[ ] git clone YOUR_REPO_URL aa_scraper
# OR upload via scp:
# scp -r /path/to/aa_scraper alex@YOUR_IP:~/

# 2. Set up virtual environment
[ ] cd aa_scraper
[ ] python3.11 -m venv venv
[ ] source venv/bin/activate
[ ] pip install -r requirements.txt

# 3. Install Playwright browser
[ ] playwright install chromium

# 4. Create .env file
[ ] cp env.template .env
[ ] nano .env  # Fill in your values
```

#### Phase B5: Transfer Browser Session

**Important:** SimplyMiles requires authenticated browser cookies.

```bash
# On your local Mac:
[ ] tar -czf browser_data.tar.gz browser_data/
[ ] scp browser_data.tar.gz alex@YOUR_IP:~/aa_scraper/

# On the server:
[ ] cd ~/aa_scraper
[ ] tar -xzf browser_data.tar.gz
[ ] rm browser_data.tar.gz

# Test the session works
[ ] python scrapers/simplymiles_api.py --test
```

#### Phase B6: Validate on Server

```bash
# Run tests
[ ] pytest tests/ -q
    Expected: 151 passed

# Test full pipeline
[ ] python scripts/run_all.py
    Expected: No errors, data in database

# Test alerts
[ ] python scripts/test_alerts.py
    Expected: Email received
```

#### Phase B7: Install Cron on Server

```bash
# Install cron jobs
[ ] python scripts/setup_cron.py --install

# Verify
[ ] crontab -l
```

---

## 6. Post-Deployment Verification

### Immediate Checks

```
[ ] Cron jobs installed: crontab -l
[ ] Log directory created: ls logs/
[ ] No Python errors in logs
[ ] First scheduled run completes
```

### After 2 Hours (First Cycle)

```
[ ] SimplyMiles scraped: tail logs/simplymiles.log
[ ] Portal scraped: tail logs/portal.log  (at 4-hour mark)
[ ] Stack detection ran: tail logs/stack_detector.log
[ ] Alert check ran: tail logs/alerts.log
```

### After 24 Hours

```
[ ] Daily digest received (8am)
[ ] No error emails from cron
[ ] Database growing: ls -la data/aa_monitor.db
[ ] Logs rotating properly
```

### Weekly Check

```
[ ] Hotel matrix verification ran (Sunday 3am)
[ ] SimplyMiles session still valid
[ ] Alert thresholds feel right (tune if needed)
```

---

## 7. Rollback Plan

### If Cron Jobs Cause Issues

```bash
# Remove all cron jobs
python scripts/setup_cron.py --remove

# Verify removed
crontab -l
```

### If VPS Has Issues

```bash
# Keep local Mac running as backup
# Simply re-enable local cron

# To redeploy to fresh VPS:
# 1. Create new Droplet
# 2. Follow Phase B steps again
```

### If SimplyMiles Session Expires

```bash
# This WILL happen every 7-30 days

# On local Mac:
python scripts/setup_auth.py  # Re-authenticate in browser

# Then upload new session to VPS:
tar -czf browser_data.tar.gz browser_data/
scp browser_data.tar.gz alex@YOUR_IP:~/aa_scraper/
# Extract on server as in Phase B5
```

---

## 8. Ongoing Maintenance

### Weekly Tasks

```
[ ] Check logs for errors: tail logs/*.log
[ ] Verify emails/pushes are arriving
[ ] Monitor alert quality (too many? too few?)
```

### Monthly Tasks

```
[ ] Review alert thresholds in config/settings.py
[ ] Check disk space: df -h
[ ] Update dependencies: pip install -U -r requirements.txt
[ ] Run tests: pytest tests/ -q
```

### When SimplyMiles Session Expires

```
[ ] Run setup_auth.py on Mac with browser
[ ] Upload new browser_data to VPS (if applicable)
[ ] Test: python scrapers/simplymiles_api.py --test
```

---

## 9. Future Enhancements (After Stable)

Once cron deployment is stable for 1-2 weeks:

### Phase 2: Dashboard (Optional)

```
- Add FastAPI backend
- Add HTMX dashboard
- Deploy with nginx + SSL
- Requires: Domain name, Let's Encrypt
```

### Phase 3: Dockerization (Optional)

```
- Create Dockerfile
- Create docker-compose.yml
- Simplifies deployments
- Requires: Docker knowledge
```

---

## 10. Cost Summary

### Option A: Local Mac

| Item | Cost |
|------|------|
| Hosting | $0 (your Mac) |
| Email (Resend) | $0 (free tier) |
| Push (ntfy) | $0 |
| **Total** | **$0/month** |

### Option B: VPS

| Item | Cost |
|------|------|
| DigitalOcean Droplet | $6/month |
| Email (Resend) | $0 (free tier) |
| Push (ntfy) | $0 |
| **Total** | **$6/month** |

---

## Quick Start Commands

```bash
# Validate everything works
pytest tests/ -q && python scripts/run_all.py

# Set up push notifications
# Edit .env with NTFY_TOPIC, then:
python -c "from alerts.push import send_push; send_push('Test', 'Working!')"

# Install cron jobs
python scripts/setup_cron.py --install

# Check cron is running (after 2 hours)
tail -20 logs/*.log
```

---

*Created: 2024-12-29*
*Status: Ready for review and approval*
