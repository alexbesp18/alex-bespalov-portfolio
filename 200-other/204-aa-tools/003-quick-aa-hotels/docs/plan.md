# Project Plan

## What We're Building (One Sentence)
Simple web tool to find AA hotels with the best AAdvantage miles per dollar yield.

## Short-Term Goals (This Week/Sprint)
1. [x] Build search UI with city/date selection
2. [x] Integrate AA Hotels API
3. [x] Deploy to Vercel
4. [x] Document for future reference

## Mid-Term Goals (This Month)
1. [ ] Add more cities if needed
2. [ ] Consider caching for faster searches

## Long-Term Vision (3-6 Months)
1. [ ] Potentially merge into aa_scraper dashboard
2. [ ] Add historical yield tracking

## Non-Goals (Explicitly Out of Scope)
- **Authentication** - Public tool, no login needed
- **Booking integration** - Just links to AA Hotels site
- **Multiple room types** - Shows best yield per hotel only
- **Complex filters** - Keep it minimal

## Success Metrics
- Returns top 10 hotels sorted by LP/$ within 5 seconds
- Works on mobile and desktop

## Current Implementation Status

### Complete
- Next.js 14 app with TypeScript + Tailwind
- AA Hotels API integration (2-step: create search → fetch results)
- City selector (8 cities with Agoda place IDs)
- Date pickers with smart defaults
- Results table with rank, name, rating, price, miles, yield, booking link
- Deployed to Vercel

### In Progress
- Nothing - project is complete

### Blocked
- Nothing

## Dependencies and Requirements

### External Services
- AA Hotels API (public, no auth needed)
- Vercel (hosting)

### Tech Stack
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS

*Last updated: 2026-01-01*
