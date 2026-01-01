# Future Roadmap

## Section 1: Deployment & Infrastructure

### Already Complete
- [x] GitHub Actions for scheduled runs (Sundays 12 PM UTC)
- [x] GitHub Actions for CI (lint, type check, test)
- [x] Manual trigger for backfill workflow
- [x] Supabase integration with `product_hunt` schema (3 tables)
- [x] Grok AI enrichment with batch processing
- [x] Weekly digest email via Resend
- [x] GitHub Actions status badges in README
- [x] Dockerfile for containerized runs

### Potential Improvements
- [ ] **Slack Notifications**: Webhook on workflow failure
  - Use GitHub Actions `on: workflow_run` with status check
  - Or add Slack notification step at end of workflow
- [ ] **Log Aggregation**: Ship logs to external service (Datadog, Logflare)
- [ ] **Health Check Workflow**: Periodic validation that scraping still works
- [ ] **Secret Rotation**: Automated Supabase key rotation

### Not Needed (Current Scale)
- Container orchestration (Kubernetes) - single script, no server needed
- Load balancing - 1 request/week
- Redis cache - data fits in Supabase

---

## Section 2: Enhancements to Existing Work

### High Priority (P1)
- [ ] **Comment Count Extraction**: Parse comment count from HTML
  - Already in HTML, just need to parse separately from upvotes
  - Add `comment_count` field to products table

- [ ] **Streamlit Dashboard**: Simple visualization interface
  - Connect to Supabase
  - Display trends over time
  - Search/filter products
  - Category breakdown charts
  - Solo builder pick history

### Medium Priority (P2)
- [ ] **Data Enrichment**: Capture additional fields
  - Maker name/handle
  - Product tagline vs description
  - Launch date

- [ ] **Trend Analytics**: Enhanced pattern detection
  - Average upvotes per week (trend line)
  - Repeat products detection
  - Week-over-week comparison
  - Emerging categories

### Low Priority (P3)
- [ ] **Performance**: Optimize for faster runs
  - Parallel processing for backfill
  - Connection pooling for Supabase

- [ ] **Testing**: Expand coverage
  - Integration tests with test Supabase project
  - Snapshot testing for HTML parsing
  - Mock Grok server for end-to-end tests
  - Tests for email digest module

### Technical Debt
- [ ] Add structured logging with JSON format - Low
- [ ] Add pre-commit hooks for consistent formatting - Low
- [ ] Consider async/await for I/O operations - Low

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

- [ ] **Advanced Dashboard**
  - Streamlit or Gradio app
  - Trend visualization (line charts)
  - Export to CSV
  - RSS feed integration

### Advanced Features
- [ ] **Predictive Analytics**
  - Predict "hot" products based on early signals
  - Identify emerging categories
  - Historical pattern matching

- [ ] **Enhanced Notifications**
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

| Priority | Item | Effort | Impact | Status |
|----------|------|--------|--------|--------|
| ~~P0~~ | ~~Error alerting~~ | ~~Low~~ | ~~High~~ | ✅ Done (GH Actions) |
| ~~P0~~ | ~~Weekly digest email~~ | ~~Medium~~ | ~~High~~ | ✅ Done |
| P1 | Comment count extraction | Low | Medium | Todo |
| P1 | Streamlit dashboard | Medium | High | Todo |
| P2 | Daily/monthly leaderboards | Medium | Medium | Todo |
| P2 | REST API endpoint | Medium | Medium | Todo |
| P3 | Multi-platform aggregation | High | Medium | Todo |
| P3 | Predictive analytics | High | Low | Todo |

---

## Next Steps (Recommended Order)

1. **Monitoring Phase**: Observe first 2-3 automated runs
   - Verify email delivery
   - Check Supabase data accuracy
   - Monitor GitHub Actions logs

2. **This Week**: Extract comment counts
   - Simple HTML parsing change
   - Add column to products table

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
| Dashboard | Streamlit hosting (Streamlit Cloud free tier) |
| REST API | Vercel account, FastAPI setup |
| Multi-platform | Additional scraping logic per platform |
| Comment count | Supabase schema migration |
