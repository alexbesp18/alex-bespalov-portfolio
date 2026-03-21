# Hotel Discovery Progress Snapshot

**Session ID:** `discovery_20251228_152930_5cf5fd1e`

**To resume:** 
```bash
source venv/bin/activate && python scripts/hotel_discovery.py --resume discovery_20251228_152930_5cf5fd1e --max-time 60
```

## Current Status
- Progress: 619/1,176 (52.6%)
- Best Yield: 32.1 LP/$ (Rio Hotel & Casino, Las Vegas)
- Hotels Scanned: ~27,000
- Errors: 0

## Top Discoveries So Far

| City | Pattern | Yield | Hotel |
|------|---------|-------|-------|
| Las Vegas | Thu 1n 21d | 32.1 LP/$ | Rio Hotel & Casino ★★★★ |
| Las Vegas | Thu 1n 14d | 31.6 LP/$ | Westgate Las Vegas ★★★★ |
| Las Vegas | Mon/Sun/Tue 1n 14d | 31.4 LP/$ | The LINQ Hotel ★★★★ |
| Dallas | Thu 1n 90d | 29.5 LP/$ | Hilton Lincoln Centre ★★★★ |
| Los Angeles | - | 25.2 LP/$ | Moxy Downtown LA |
| San Francisco | - | 24.4 LP/$ | InterContinental Mark Hopkins |
| Houston | - | 24.3 LP/$ | Various |
| New York | - | 23.6 LP/$ | NEW YORKER BY LOTTE |
| Austin | - | 23.3 LP/$ | The LINE Hotel |
| Boston | - | 20.6 LP/$ | The Colonnade Hotel |

## Key Pattern
**Las Vegas dominates** with 14-21 day advance bookings for 1-night stays. Thursday and Sunday are sweet spots.

## Database Location
`data/aa_monitor.db` - tables: `hotel_yield_matrix`, `discovery_progress`

## Query to see top deals:
```sql
SELECT city, day_of_week, duration, advance_days, 
       ROUND(top_premium_yield, 1) as yield, top_premium_hotel
FROM hotel_yield_matrix 
WHERE top_premium_yield IS NOT NULL
ORDER BY top_premium_yield DESC LIMIT 20;
```
