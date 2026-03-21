# Init Considerations

Quick-start guide for the AA Hotels Yield Finder.

## Start Here

1. **Live URL:** https://quickaahotels.vercel.app
2. **GitHub:** https://github.com/alexbesp18/quick_aa_hotels (private)
3. **Local dev:** `npm run dev` → http://localhost:3000

## Project Structure

```
quick_aa_hotels/
├── app/
│   ├── page.tsx            # Main UI (form + results table)
│   ├── layout.tsx          # Root layout
│   └── api/search/route.ts # API endpoint
├── lib/
│   └── hotels.ts           # AA Hotels API client
├── docs/                   # Documentation
└── package.json
```

## Key Files

| File | Purpose |
|------|---------|
| `lib/hotels.ts` | API client - search creation, result fetching, yield calculation |
| `app/api/search/route.ts` | Validates params, calls hotels.ts |
| `app/page.tsx` | Form UI, results table, loading/error states |

## How It Works

1. User picks city + dates
2. Frontend calls `/api/search?city=austin&checkIn=2026-01-10&checkOut=2026-01-12`
3. Backend calls AA Hotels API (2 requests: create search → get results)
4. Parse results, calculate yield (miles/price), sort, return top 10

## Cities

Hardcoded in `lib/hotels.ts` with Agoda place IDs:
- Austin, Dallas, Houston, Las Vegas
- New York, Boston, San Francisco, Los Angeles

To add a city: find its Agoda place ID from AA Hotels URL and add to `CITIES` object.

## Decisions Already Made

| Decision | Why |
|----------|-----|
| No auth | Public tool, no user accounts |
| Server-side API | Avoid CORS, hide request details |
| Top 10 only | Keep it simple |
| Premium member miles | Show best possible yield |

## Common Tasks

### Add a City
1. Go to aadvantagehotels.com, search the city
2. Extract place ID from URL (e.g., `placeId=AGODA_CITY|4542`)
3. Add to `CITIES` in `lib/hotels.ts`

### Deploy Changes
```bash
git add -A && git commit -m "message" && git push
# Vercel auto-deploys
```

*Last updated: 2026-01-01*
