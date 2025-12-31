# Future Roadmap

## Section 1: Deployment & Infrastructure

### Already Complete
- [x] GitHub Actions for scheduled runs (Sundays 12 PM UTC)
- [x] GitHub Actions for CI (lint, type check, test)
- [x] Manual trigger for backfill workflow
- [x] Google Sheets integration with service account

### Potential Improvements
- [ ] **Failure Notifications**: Slack webhook or email on workflow failure
- [ ] **Monitoring Dashboard**: GitHub Actions status badge in README
- [ ] **Log Aggregation**: Ship logs to external service for debugging
- [ ] **Health Check Workflow**: Periodic validation that scraping still works
- [ ] **Secret Rotation**: Automated service account key rotation

### Not Needed (Current Scale)
- Container deployment (single script, no server needed)
- Load balancing (1 request/week)
- Database (Google Sheets sufficient)

---

## Section 2: Enhancements to Existing Work

### High Priority
- [ ] **Error Alerting**: Notify on scraping failures
  - Slack integration via webhook
  - Email via SendGrid/SES
  - GitHub Issues auto-creation

- [ ] **Data Enrichment**: Capture additional fields
  - Comment count (already in HTML)
  - Maker name/handle
  - Product tagline vs description
  - Launch date

### Medium Priority
- [ ] **Analytics**: Track trends over time
  - Average upvotes per week
  - Repeat products detection
  - Category analysis (if extractable)

- [ ] **Validation**: Ensure data quality
  - Verify 10 products captured each week
  - Alert if upvote numbers seem wrong
  - Compare week-over-week for anomalies

### Low Priority
- [ ] **Performance**: Optimize for faster runs
  - Parallel processing for backfill
  - Connection pooling for sheets API

- [ ] **Testing**: Expand coverage
  - Integration tests with real sheets (test account)
  - Snapshot testing for HTML parsing
  - Mock server for end-to-end tests

### Technical Debt
- [ ] Remove duplicate " 2" files (macOS copy artifacts)
- [ ] Add pre-commit hooks for consistent formatting
- [ ] Consider async/await for I/O operations

---

## Section 3: Unexplored Future Ideas

### Feature Expansions
- [ ] **Multi-Leaderboard Support**
  - Daily leaderboard
  - Monthly leaderboard
  - All-time leaderboard
  - Filter by category/topic

- [ ] **Multi-Platform**
  - Hacker News top posts
  - Reddit trending
  - Twitter/X trending products
  - GitHub trending repos

### Data Access
- [ ] **REST API**
  - Simple FastAPI wrapper
  - Serve historical data as JSON
  - Rate limiting and caching

- [ ] **Dashboard**
  - Streamlit or Gradio app
  - Trend visualization
  - Search/filter products
  - Export to CSV

### Advanced Features
- [ ] **ML/AI Integration**
  - Predict "hot" products based on early signals
  - Categorize products automatically
  - Summarize product descriptions with LLM

- [ ] **Notifications**
  - Weekly digest email
  - RSS feed of top products
  - Push notifications for specific keywords

### Monetization (If Ever Relevant)
- [ ] Premium tier with real-time data
- [ ] API access for developers
- [ ] Custom reports for VCs/investors

---

## Priority Matrix

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| P0 | Error alerting | Low | High |
| P1 | Comment count extraction | Low | Medium |
| P1 | Health check workflow | Low | Medium |
| P2 | Daily/monthly leaderboards | Medium | Medium |
| P2 | Trend dashboard | Medium | High |
| P3 | REST API | Medium | Low |
| P3 | Multi-platform support | High | Medium |

---

## Next Steps (Recommended Order)

1. **Immediate**: Add Slack notification on workflow failure
2. **This Month**: Extract comment counts alongside upvotes
3. **Next Quarter**: Build simple trend dashboard
4. **Future**: Consider API if there's demand
