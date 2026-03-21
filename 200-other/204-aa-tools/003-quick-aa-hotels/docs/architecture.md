# Architecture

## Overview

Minimal Next.js app that queries the AA Hotels API and displays results sorted by miles/dollar yield.

```
┌─────────────────────────────────────────────────────────────┐
│                     BROWSER (Client)                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  app/page.tsx                                        │   │
│  │  - City dropdown (8 cities)                          │   │
│  │  - Date pickers (check-in/out)                       │   │
│  │  - Results table (top 10 by LP/$)                    │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │ fetch /api/search
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   VERCEL (Server)                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  app/api/search/route.ts                             │   │
│  │  - Validates params                                  │   │
│  │  - Calls lib/hotels.ts                               │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  lib/hotels.ts                                       │   │
│  │  - createSearch() → UUID                             │   │
│  │  - getResults(uuid) → hotels                         │   │
│  │  - Parse, sort by yield, return top 10               │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │ 2 API calls
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              AA HOTELS API (External)                       │
│  GET /rest/aadvantage-hotels/searchRequest → {uuid}         │
│  GET /rest/aadvantage-hotels/search/{uuid} → {results:[]}   │
└─────────────────────────────────────────────────────────────┘
```

## Components

### `app/page.tsx` - UI
- Client component (`'use client'`)
- Form with city dropdown, date inputs, search button
- Results table with hotel details
- Loading and error states

### `app/api/search/route.ts` - API Route
- Validates: city, checkIn, checkOut params
- Calls `searchHotels()` from lib
- Returns JSON response

### `lib/hotels.ts` - API Client
- `CITIES` - Agoda place IDs for 8 cities
- `createSearch()` - Creates search, returns UUID
- `getResults()` - Fetches results by UUID
- `searchHotels()` - Main function, returns top 10 sorted by yield

## Data Flow

1. User selects city + dates, clicks Search
2. Frontend calls `/api/search?city=austin&checkIn=2026-01-10&checkOut=2026-01-12`
3. API route validates params
4. `createSearch()` calls AA Hotels API → gets UUID
5. 500ms delay
6. `getResults()` fetches hotel results
7. Parse each hotel: extract name, price, miles
8. Calculate yield: `miles / price`
9. Sort by yield descending
10. Return top 10

## Cities (Agoda Place IDs)

| City | ID |
|------|----|
| Austin | 4542 |
| Dallas | 8683 |
| Houston | 1178 |
| Las Vegas | 17072 |
| New York | 318 |
| Boston | 9254 |
| San Francisco | 13801 |
| Los Angeles | 12772 |

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Next.js App Router | Vercel native, simple deployment |
| Server-side API calls | Avoid CORS, hide request details |
| No caching | Fresh results every search |
| Top 10 only | Keep UI simple |
| Premium member miles | Use `max(base, bonus)` for best yield |

*Last updated: 2026-01-01*
