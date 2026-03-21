# Future: Deployment & Infrastructure

Production deployment, APIs, frontend/backend services, and operational infrastructure.

---

## Current State

| Component | Status | Notes |
|-----------|--------|-------|
| Scrapers | ✅ Local | Manual or cron execution |
| Database | ✅ SQLite | Local file |
| Alerts | ✅ Resend API | Email only |
| Frontend | ❌ None | CLI only |
| API | ❌ None | Direct DB access |
| Hosting | ❌ None | Local machine |

---

## 1. Scheduling & Automation

### Cron Setup (Immediate)
**Status:** Ready to implement | **Effort:** Low

```cron
# SimplyMiles - every 2 hours (offers change frequently)
0 */2 * * * cd /path/to/aa_scraper && /path/to/venv/bin/python scrapers/simplymiles_api.py

# Portal - every 4 hours (rates more stable)
30 */4 * * * cd /path/to/aa_scraper && /path/to/venv/bin/python scrapers/portal.py

# Hotels - every 6 hours (availability changes slowly)
0 */6 * * * cd /path/to/aa_scraper && /path/to/venv/bin/python scrapers/hotels.py

# Stack detection - after scrapers
15 */2 * * * cd /path/to/aa_scraper && /path/to/venv/bin/python -c "from core.stack_detector import detect_stacked_opportunities; detect_stacked_opportunities()"

# Daily digest - 8am local time
0 8 * * * cd /path/to/aa_scraper && /path/to/venv/bin/python scripts/send_digest.py

# Hotel matrix verification - weekly
0 3 * * 0 cd /path/to/aa_scraper && /path/to/venv/bin/python scripts/hotel_discovery.py --verify
```

### Systemd Services (Alternative)
**Status:** Optional | **Effort:** Medium

```ini
# /etc/systemd/system/aa-scraper.service
[Unit]
Description=AA Points Scraper
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/opt/aa-scraper
ExecStart=/opt/aa-scraper/venv/bin/python scripts/run_all.py
User=aa-scraper

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/aa-scraper.timer
[Unit]
Description=Run AA Scraper every 2 hours

[Timer]
OnCalendar=*:00/2:00
Persistent=true

[Install]
WantedBy=timers.target
```

---

## 2. Backend API

### REST API with FastAPI
**Status:** Planned | **Effort:** Medium | **Priority:** High

Expose data via REST endpoints for frontend/mobile consumption.

#### Endpoints Design

```
GET  /api/v1/deals/stacked          # All stacked opportunities
GET  /api/v1/deals/stacked/top      # Top N by score
GET  /api/v1/deals/hotels           # Current hotel deals
GET  /api/v1/deals/hotels/city/:id  # Hotels by city

GET  /api/v1/matrix/:city           # Yield matrix for city
GET  /api/v1/matrix/best            # Best combinations overall

GET  /api/v1/health                 # System health status
GET  /api/v1/stats                  # Dashboard statistics

POST /api/v1/alerts/test            # Trigger test alert
POST /api/v1/scraper/run/:name      # Trigger scraper manually
```

#### Implementation Skeleton

```python
# api/main.py
from fastapi import FastAPI, HTTPException
from core.database import get_database

app = FastAPI(title="AA Points API", version="1.0.0")

@app.get("/api/v1/deals/stacked")
async def get_stacked_deals(limit: int = 50, min_yield: float = 5.0):
    db = get_database()
    deals = db.get_stacked_opportunities(min_yield=min_yield)
    return {"deals": deals[:limit], "count": len(deals)}

@app.get("/api/v1/health")
async def health_check():
    db = get_database()
    freshness = db.get_data_freshness_report()
    return {"status": "healthy", "freshness": freshness}
```

#### Dependencies
```
fastapi>=0.104.0
uvicorn>=0.24.0
```

#### Run Command
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 3. Frontend Options

### Option A: HTMX + Jinja2 (Recommended)
**Status:** Planned | **Effort:** Medium | **Priority:** High

Server-rendered HTML with minimal JavaScript. Fast to build, easy to maintain.

```
templates/
├── base.html           # Layout with nav
├── dashboard.html      # Main overview
├── deals/
│   ├── stacked.html    # Stacked deals table
│   ├── hotels.html     # Hotel deals grid
│   └── detail.html     # Single deal view
├── matrix/
│   ├── heatmap.html    # Yield heatmap
│   └── city.html       # City detail
└── components/
    ├── deal_card.html  # Reusable deal card
    └── stats_bar.html  # Stats summary
```

**Tech:** FastAPI + Jinja2 + HTMX + TailwindCSS

### Option B: React SPA
**Status:** Consider later | **Effort:** High

Full single-page app with rich interactivity.

**Pros:** Smooth UX, offline capable, mobile-ready
**Cons:** More complexity, separate build process, overkill for single user

### Option C: Streamlit
**Status:** Quick prototype | **Effort:** Low

Rapid dashboard for data exploration.

```python
# dashboard.py
import streamlit as st
from core.database import get_database

st.title("AA Points Dashboard")

db = get_database()
deals = db.get_stacked_opportunities()

st.metric("Top Yield", f"{deals[0]['deal_score']:.1f} LP/$")
st.dataframe(deals[:20])
```

**Run:** `streamlit run dashboard.py`

---

## 4. Notification Channels

### Current: Email (Resend)
✅ Implemented - HTML + text emails via Resend API

### Add: Push Notifications
**Status:** Planned | **Effort:** Low | **Priority:** Medium

#### Option 1: Pushover (Recommended)
- $5 one-time purchase
- Simple API
- iOS + Android + Desktop

```python
# alerts/push.py
import httpx

def send_push(title: str, message: str, priority: int = 0):
    httpx.post("https://api.pushover.net/1/messages.json", data={
        "token": os.environ["PUSHOVER_APP_TOKEN"],
        "user": os.environ["PUSHOVER_USER_KEY"],
        "title": title,
        "message": message,
        "priority": priority,  # -1=quiet, 0=normal, 1=high
    })
```

#### Option 2: ntfy.sh (Free)
- Self-hostable
- No account needed
- Simple POST to topic

```python
import httpx

def send_ntfy(topic: str, title: str, message: str):
    httpx.post(f"https://ntfy.sh/{topic}",
        headers={"Title": title},
        content=message
    )
```

#### Option 3: Telegram Bot
- Free
- Rich formatting
- Requires bot setup

```python
import httpx

def send_telegram(message: str):
    bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    httpx.post(f"https://api.telegram.org/bot{bot_token}/sendMessage",
        json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    )
```

### Add: SMS Alerts
**Status:** Future | **Effort:** Low

Twilio for critical alerts (>25 LP/$ deals).

```python
from twilio.rest import Client

def send_sms(message: str):
    client = Client(account_sid, auth_token)
    client.messages.create(body=message, from_="+1...", to="+1...")
```

---

## 5. Containerization

### Docker Setup
**Status:** Planned | **Effort:** Medium | **Priority:** Medium

```dockerfile
# Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install system deps for Playwright
RUN apt-get update && apt-get install -y \
    wget gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium --with-deps

# Copy application
COPY . .

# Default command
CMD ["python", "scripts/run_all.py"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  scraper:
    build: .
    volumes:
      - ./data:/app/data
      - ./browser_data:/app/browser_data
    env_file: .env
    command: python scripts/run_all.py

  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    env_file: .env
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000

  scheduler:
    build: .
    volumes:
      - ./data:/app/data
      - ./browser_data:/app/browser_data
    env_file: .env
    command: python -m schedule_runner  # Custom scheduler
```

### Kubernetes (Future)
For multi-instance deployment if needed.

---

## 6. Database Options

### Current: SQLite
✅ Simple, no setup, good for single user

### Option: PostgreSQL
**Status:** Consider if scaling | **Effort:** Medium

**When to migrate:**
- Multiple users
- Concurrent writes needed
- Remote access required
- Data > 1GB

**Migration path:**
1. Export SQLite to SQL
2. Create PostgreSQL schema
3. Import data
4. Update `DATABASE_URL` in config

### Option: SQLite + Litestream
**Status:** Recommended for backup | **Effort:** Low

Stream SQLite changes to S3 for backup/restore.

```yaml
# litestream.yml
dbs:
  - path: /app/data/aa_monitor.db
    replicas:
      - url: s3://bucket/aa-monitor
```

---

## 7. Monitoring & Observability

### Health Endpoint
```python
@app.get("/health")
def health():
    db = get_database()
    return {
        "status": "ok",
        "database": "connected",
        "scrapers": db.get_scraper_health_summary(),
        "last_alert": db.get_last_alert_time()
    }
```

### Prometheus Metrics
```python
from prometheus_client import Counter, Gauge, generate_latest

deals_found = Counter('deals_found_total', 'Total deals found', ['type'])
scraper_duration = Gauge('scraper_duration_seconds', 'Scraper run time', ['scraper'])

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Uptime Monitoring
- UptimeRobot (free tier)
- Healthchecks.io (cron monitoring)
- Better Stack (logs + uptime)

---

## 8. Security Hardening

### Secrets Management
```bash
# Current: .env file
# Better: Use a secrets manager

# Option 1: 1Password CLI
op read "op://Vault/AA-Scraper/RESEND_API_KEY"

# Option 2: AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id aa-scraper

# Option 3: HashiCorp Vault
vault kv get -field=api_key secret/aa-scraper
```

### API Authentication
```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != os.environ["API_KEY"]:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

@app.get("/api/v1/deals", dependencies=[Depends(verify_api_key)])
async def get_deals():
    ...
```

---

## 9. Deployment Targets

### Local Mac (Current)
- Cron for scheduling
- SQLite for storage
- Terminal for monitoring

### VPS (Recommended Next Step)
- DigitalOcean Droplet ($6/mo)
- Docker Compose
- Nginx reverse proxy
- Let's Encrypt SSL

### Raspberry Pi (Low Cost)
- Always-on, low power
- Docker or native Python
- Local network access

### Cloud Functions (Serverless)
- AWS Lambda + EventBridge
- Google Cloud Functions + Scheduler
- Cold start latency concern for Playwright

---

## Implementation Priority

| Phase | Component | Effort | Impact |
|-------|-----------|--------|--------|
| 1 | Cron scheduling | Low | High |
| 2 | Push notifications | Low | High |
| 3 | FastAPI backend | Medium | High |
| 4 | HTMX frontend | Medium | Medium |
| 5 | Docker setup | Medium | Medium |
| 6 | VPS deployment | Medium | High |
| 7 | Monitoring | Low | Medium |

---

*Last updated: 2024-12-29*
