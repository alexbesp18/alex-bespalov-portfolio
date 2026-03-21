#!/usr/bin/env python3
"""
Auto-pattern scrape for Railway cron.

Automatically selects pattern based on current hour (CT):
- 0-8: morning (near-term 1-21 days)
- 9-14: afternoon (mid-term 15-45 days)
- 15-23: evening (long-term 30-60 days)

Usage:
    python railway/auto_pattern_scrape.py

Set cron to run 3x daily: 0 2,10,18 * * *
"""

import asyncio
import os
import sys
from datetime import datetime

import pytz

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force Supabase mode
os.environ['DB_MODE'] = 'supabase'


def get_pattern_for_hour() -> str:
    """Determine pattern based on current hour in Central Time."""
    ct = pytz.timezone('America/Chicago')
    hour = datetime.now(ct).hour

    if hour < 9:
        return 'morning'
    elif hour < 15:
        return 'afternoon'
    else:
        return 'evening'


if __name__ == '__main__':
    pattern = get_pattern_for_hour()
    print(f"Auto-detected pattern: {pattern} (hour={datetime.now().hour})")

    # Import and run with detected pattern
    from railway.daily_scrape import main
    asyncio.run(main(pattern=pattern))
