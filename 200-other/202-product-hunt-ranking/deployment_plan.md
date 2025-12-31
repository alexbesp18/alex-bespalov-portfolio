# Deployment Plan

## 1. Deployment Overview

### Components
This is a **serverless pipeline** - no traditional server deployment needed.

| Component | Hosting | Status |
|-----------|---------|--------|
| Weekly Scraper | GitHub Actions | Already deployed |
| Historical Backfill | GitHub Actions | Already deployed |
| CI Pipeline | GitHub Actions | Already deployed |
| Database | Supabase | Already provisioned |
| AI Enrichment | Grok API (xAI) | External service |
| Email Digest | Resend | External service |

### Architecture
```
GitHub Actions (Sundays 12 PM UTC)
        ↓
   Python Script
        ↓
   ┌────┴────┐
   ↓         ↓
Grok AI   Supabase
   ↓         ↓
   └────┬────┘
        ↓
   Resend Email
```

### Cost Considerations
| Service | Tier | Cost |
|---------|------|------|
| GitHub Actions | Free tier | $0 (2,000 min/month) |
| Supabase | Free tier | $0 (500 MB, 50K requests) |
| Grok API | Pay-per-use | ~$0.01/week (1 batch call) |
| Resend | Free tier | $0 (100 emails/day) |

**Total estimated cost: ~$0.50/month** (Grok API only)

---

## 2. Accounts & Registrations Needed

All accounts should already exist based on current setup:

```
[x] GitHub
    - URL: https://github.com
    - Purpose: Code hosting, CI/CD via Actions
    - Status: Already configured

[x] Supabase
    - URL: https://supabase.com
    - Purpose: PostgreSQL database
    - Project ID: rxsmmrmahnvaarwsngtb
    - Status: Already provisioned

[x] xAI (Grok)
    - URL: https://console.x.ai
    - Purpose: AI product categorization
    - Status: API key required

[x] Resend
    - URL: https://resend.com
    - Purpose: Email digest delivery
    - Status: API key required
```

---

## 3. Credentials & API Keys

### Required GitHub Secrets

Navigate to: **Repository → Settings → Secrets and variables → Actions**

```
[x] SUPABASE_URL
    - Value: https://rxsmmrmahnvaarwsngtb.supabase.co
    - Source: Supabase Dashboard → Settings → API → Project URL

[x] SUPABASE_SERVICE_KEY
    - Value: eyJhbGciOiJIUzI1NiIs... (service_role key)
    - Source: Supabase Dashboard → Settings → API → service_role (secret)
    - ⚠️ Use service_role, NOT anon key

[x] GROK_API_KEY
    - Value: xai-...
    - Source: https://console.x.ai → API Keys
    - Note: Optional - pipeline works without it (no AI enrichment)

[x] RESEND_API_KEY
    - Value: re_...
    - Source: https://resend.com/api-keys
    - Note: Optional - no email if not set

[x] EMAIL_FROM
    - Value: digest@yourdomain.com or onboarding@resend.dev
    - Note: Must be verified domain or use Resend's test domain

[x] EMAIL_TO
    - Value: your-email@example.com
    - Note: Comma-separated for multiple recipients
```

### Verification Command
```bash
# Check secrets are configured (from GitHub CLI)
gh secret list --repo alexbesp18/alex-bespalov-portfolio
```

---

## 4. Pre-Deployment Checklist

```
[x] Code pushed to main branch
[x] All tests passing (56/56)
[x] ruff check clean
[x] mypy type check clean
[x] GitHub Actions workflows exist
    - 202_ph_ranking_weekly.yml
    - 202_ph_ranking_backfill.yml
    - 202_ph_ranking_ci.yml
[x] Supabase schema created
    - product_hunt.products table
    - product_hunt.weekly_insights table
[ ] GitHub secrets configured (user confirmed)
[ ] First manual run successful
[ ] Email delivery verified
```

---

## 5. Deployment Steps

### Phase A: Verify Secrets Configuration

```
1. [ ] Go to: https://github.com/alexbesp18/alex-bespalov-portfolio/settings/secrets/actions
2. [ ] Verify these secrets exist:
       - SUPABASE_URL
       - SUPABASE_SERVICE_KEY
       - GROK_API_KEY (optional)
       - RESEND_API_KEY (optional)
       - EMAIL_FROM (optional)
       - EMAIL_TO (optional)
3. [ ] Confirm: Screenshot or list secrets present
```

### Phase B: Test Manual Trigger

```
1. [ ] Go to: https://github.com/alexbesp18/alex-bespalov-portfolio/actions
2. [ ] Click: "Weekly Product Hunt Rankings" workflow
3. [ ] Click: "Run workflow" dropdown
4. [ ] Click: "Run workflow" button (green)
5. [ ] Wait: ~2-3 minutes for completion
6. [ ] Verify: Check workflow run is green ✓
```

### Phase C: Verify Data Storage

```
1. [ ] Go to: https://supabase.com/dashboard/project/rxsmmrmahnvaarwsngtb
2. [ ] Navigate: Table Editor → product_hunt schema
3. [ ] Check: products table has rows for current week
4. [ ] Check: weekly_insights table has entry for current week
5. [ ] Verify: Data looks correct (names, upvotes, categories)
```

### Phase D: Verify Email Delivery (if configured)

```
1. [ ] Check inbox for EMAIL_TO address
2. [ ] Look for: "Product Hunt Weekly Digest" email
3. [ ] Verify: Email contains top 10 products with AI insights
4. [ ] If no email: Check workflow logs for RESEND errors
```

---

## 6. Post-Deployment Verification

### Immediate Checks
```
[ ] GitHub Actions workflow completed successfully
[ ] Supabase has data for current week (products table)
[ ] Supabase has insights for current week (weekly_insights table)
[ ] Email received (if RESEND configured)
[ ] No errors in workflow logs
```

### Ongoing Monitoring
```
[ ] Workflow runs every Sunday 12 PM UTC
[ ] Check GitHub Actions tab weekly for failures
[ ] Monitor Supabase usage (stay under free tier limits)
[ ] Check email delivery weekly
```

### Verification Queries (Supabase SQL Editor)
```sql
-- Check latest products
SELECT week_date, rank, name, upvotes, category
FROM product_hunt.products
ORDER BY week_date DESC, rank ASC
LIMIT 20;

-- Check insights exist
SELECT week_date, top_trends, sentiment, avg_upvotes
FROM product_hunt.weekly_insights
ORDER BY week_date DESC
LIMIT 5;

-- Count total weeks collected
SELECT COUNT(DISTINCT week_date) as weeks_collected
FROM product_hunt.products;
```

---

## 7. Rollback Plan

### If Workflow Fails
1. Check workflow logs for error details
2. Most common issues:
   - **Supabase auth error**: Verify SUPABASE_SERVICE_KEY is correct
   - **Grok rate limit**: Wait and retry, or remove GROK_API_KEY to skip enrichment
   - **HTML parsing error**: Product Hunt may have changed DOM structure
3. Re-run workflow manually after fixing

### If Bad Data Inserted
```sql
-- Delete specific week's data
DELETE FROM product_hunt.products
WHERE week_date = '2025-01-06';

DELETE FROM product_hunt.weekly_insights
WHERE week_date = '2025-01-06';
```

### Support Links
- GitHub Actions: https://docs.github.com/en/actions
- Supabase: https://supabase.com/docs
- Grok API: https://docs.x.ai
- Resend: https://resend.com/docs

---

## 8. Future CI/CD Improvements

Already implemented:
- [x] Automatic CI on push/PR (lint, type check, test)
- [x] Scheduled weekly runs (Sundays 12 PM UTC)
- [x] Manual trigger for backfill

Future considerations:
- [ ] Add status badges to README (already present)
- [ ] Email notification on workflow failure
- [ ] Slack notification on workflow failure (if Slack used)
- [ ] Dashboard deployment (Streamlit Cloud - P1)

---

## 9. Quick Reference

### Manual Run
```bash
# Via GitHub CLI
gh workflow run "Weekly Product Hunt Rankings" --repo alexbesp18/alex-bespalov-portfolio
```

### Local Testing
```bash
cd 200-other/202-product-hunt-ranking

# Set environment variables
export SUPABASE_URL='https://rxsmmrmahnvaarwsngtb.supabase.co'
export SUPABASE_SERVICE_KEY='your-key'
export GROK_API_KEY='your-key'  # optional
export RESEND_API_KEY='your-key'  # optional
export EMAIL_FROM='your-email'
export EMAIL_TO='your-email'

# Run weekly scraper
python -m src.main

# Run backfill (last 10 weeks)
python -m backfill.main
```

### Workflow URLs
- Weekly: https://github.com/alexbesp18/alex-bespalov-portfolio/actions/workflows/202_ph_ranking_weekly.yml
- Backfill: https://github.com/alexbesp18/alex-bespalov-portfolio/actions/workflows/202_ph_ranking_backfill.yml
- CI: https://github.com/alexbesp18/alex-bespalov-portfolio/actions/workflows/202_ph_ranking_ci.yml

---

## 10. Decision Points

**No decisions required** - all infrastructure is already in place.

If you want to proceed:
1. Verify secrets are configured (Phase A)
2. Run a manual test (Phase B)
3. Verify data appears in Supabase (Phase C)
4. Wait for next Sunday 12 PM UTC for automatic run

---

## Estimated Time

| Phase | Time |
|-------|------|
| A: Verify Secrets | 2 min |
| B: Manual Trigger | 3 min |
| C: Verify Storage | 2 min |
| D: Verify Email | 1 min |
| **Total** | **~10 min** |

The project is essentially already deployed. This plan is verification, not deployment.
