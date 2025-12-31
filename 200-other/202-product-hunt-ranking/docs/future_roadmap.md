# Future Roadmap

## Section 1: Deployment & Infrastructure

### Already Complete
- [x] GitHub Actions for scheduled runs (Sundays 12 PM UTC)
- [x] GitHub Actions for CI (lint, type check, test)
- [x] Manual trigger for backfill workflow
- [x] Supabase integration with `product_hunt` schema
- [x] Grok AI enrichment with batch processing
- [x] Dockerfile for containerized runs

### Potential Improvements
- [ ] **Failure Notifications**: Slack webhook or email on workflow failure
  - Use GitHub Actions `on: workflow_run` with status check
  - Or add Slack notification step at end of workflow
- [ ] **Monitoring Dashboard**: GitHub Actions status badge in README
- [ ] **Log Aggregation**: Ship logs to external service (Datadog, Logflare)
- [ ] **Health Check Workflow**: Periodic validation that scraping still works
- [ ] **Secret Rotation**: Automated Supabase key rotation

### Not Needed (Current Scale)
- Container orchestration (Kubernetes) - single script, no server needed
- Load balancing - 1 request/week
- Redis cache - data fits in Supabase

---

## Section 2: Enhancements to Existing Work

### High Priority
- [ ] **Error Alerting**: Notify on scraping failures
  - Slack integration via webhook (simplest)
  - Email via Resend/SendGrid
  - GitHub Issues auto-creation

- [ ] **Weekly Digest Email**: Send AI insights summary
  - Use Grok's `weekly_insights` data
  - Format as HTML email
  - Send via Resend (already used in other projects)

### Medium Priority
- [ ] **Query Interface**: Simple way to explore data
  - Supabase Dashboard (already available)
  - Streamlit app for visualization
  - API endpoint (FastAPI wrapper)

- [ ] **Data Enrichment**: Capture additional fields
  - Comment count (already in HTML, just need to parse)
  - Maker name/handle
  - Product tagline vs description
  - Launch date

- [ ] **Trend Analytics**: Track patterns over time
  - Average upvotes per week
  - Repeat products detection
  - Category distribution charts
  - Week-over-week comparison

### Low Priority
- [ ] **Performance**: Optimize for faster runs
  - Parallel processing for backfill
  - Connection pooling for Supabase

- [ ] **Testing**: Expand coverage
  - Integration tests with test Supabase project
  - Snapshot testing for HTML parsing
  - Mock Grok server for end-to-end tests

### Technical Debt
- [ ] Add structured logging with JSON format - Medium priority
- [ ] Add pre-commit hooks for consistent formatting - Low priority
- [ ] Consider async/await for I/O operations - Low priority

---

## Section 3: Unexplored Future Ideas

### Feature Expansions
- [ ] **Multi-Leaderboard Support**
  - Daily leaderboard
  - Monthly leaderboard
  - All-time leaderboard
  - Filter by category/topic

- [ ] **Multi-Platform Aggregation**
  - Hacker News top posts
  - Reddit trending (r/startups, r/SaaS)
  - Twitter/X trending products
  - GitHub trending repos

### Data Access
- [ ] **REST API**
  - FastAPI wrapper around Supabase queries
  - Rate limiting and caching
  - OpenAPI documentation
  - Vercel deployment

- [ ] **Dashboard**
  - Streamlit or Gradio app
  - Trend visualization (line charts)
  - Search/filter products
  - Export to CSV
  - Weekly insights display

### Advanced Features
- [ ] **Predictive Analytics**
  - Predict "hot" products based on early signals
  - Categorize products automatically (already done with Grok)
  - Identify emerging categories

- [ ] **Notifications**
  - Weekly digest email (high priority)
  - RSS feed of top products
  - Push notifications for specific keywords
  - Slack bot for queries

### Monetization (If Ever Relevant)
- [ ] Premium tier with real-time data
- [ ] API access for developers
- [ ] Custom reports for VCs/investors
- [ ] Affiliate links to featured products

---

## Priority Matrix

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| P0 | Error alerting (Slack webhook) | Low | High |
| P0 | Weekly digest email | Medium | High |
| P1 | Comment count extraction | Low | Medium |
| P1 | Streamlit dashboard | Medium | High |
| P2 | Daily/monthly leaderboards | Medium | Medium |
| P2 | REST API endpoint | Medium | Medium |
| P3 | Multi-platform aggregation | High | Medium |
| P3 | Predictive analytics | High | Low |

---

## Next Steps (Recommended Order)

1. **Immediate**: Add Slack notification on workflow failure
   - Simple webhook call at end of workflow
   - No new infrastructure needed

2. **This Week**: Implement weekly digest email
   - Use Resend (already in other projects)
   - Format AI insights as HTML
   - Add to GitHub Actions workflow

3. **This Month**: Build Streamlit dashboard
   - Connect to Supabase
   - Display trends over time
   - Search/filter products

4. **Next Quarter**: REST API if there's demand
   - FastAPI wrapper
   - Deploy to Vercel
   - Add rate limiting

---

## Dependencies for Future Work

| Feature | Requires |
|---------|----------|
| Slack notifications | Slack webhook URL |
| Email digest | Resend API key, recipient email |
| Dashboard | Streamlit hosting (Streamlit Cloud free tier) |
| REST API | Vercel account, FastAPI setup |
| Multi-platform | Additional scraping logic per platform |
