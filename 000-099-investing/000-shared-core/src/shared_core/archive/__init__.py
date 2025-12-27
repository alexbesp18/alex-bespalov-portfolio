"""
Historical data archival to Supabase.

Tiered storage system:
- Tier 1 (Hot): 0-7 days - Raw JSON cache
- Tier 2 (Daily): 7-90 days - Full daily snapshots
- Tier 3 (Monthly): 90+ days - Compressed monthly aggregates
"""

from .supabase_client import (
    SupabaseArchiver,
    archive_daily_indicators,
    get_historical_data,
)

from .aggregator import (
    MonthlyAggregator,
    run_monthly_aggregation,
)

__all__ = [
    # Daily archival
    'SupabaseArchiver',
    'archive_daily_indicators',
    'get_historical_data',
    # Monthly aggregation
    'MonthlyAggregator',
    'run_monthly_aggregation',
]
