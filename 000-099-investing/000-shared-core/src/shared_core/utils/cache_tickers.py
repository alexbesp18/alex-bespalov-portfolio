"""
Cache ticker utilities.

Extracts ticker symbols from cached data files.
Used by 008-alerts, 009-reversals, and 010-oversold to discover
which tickers have cached data from 007-ticker-analysis.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union


def get_cached_tickers(
    cache_dir: Union[str, Path],
    date: Optional[str] = None,
) -> List[str]:
    """
    Get ticker symbols from cached data files.
    
    Looks for files matching the pattern: TICKER_YYYY-MM-DD.json
    
    Args:
        cache_dir: Path to the cache directory (e.g., 007-ticker-analysis/data/twelve_data)
        date: Date string in YYYY-MM-DD format. Defaults to today.
        
    Returns:
        Sorted list of unique ticker symbols found in cache for the given date.
        
    Example:
        >>> tickers = get_cached_tickers("/path/to/007-ticker-analysis/data/twelve_data")
        >>> print(tickers)
        ['AAPL', 'GOOGL', 'MSFT', 'NVDA']
    """
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')

    cache_path = Path(cache_dir) if isinstance(cache_dir, str) else cache_dir
    tickers: List[str] = []

    if not cache_path.exists():
        return []

    # Look for files matching pattern: *_{date}.json
    for f in cache_path.glob(f"*_{date}.json"):
        # Extract ticker from filename like "NVDA_2024-12-21.json"
        ticker = f.stem.replace(f"_{date}", "")
        if ticker:
            tickers.append(ticker)

    return sorted(set(tickers))


def get_latest_cached_tickers(
    cache_dir: Union[str, Path],
    lookback_days: int = 7,
) -> List[str]:
    """
    Get ticker symbols from most recent cached data files.
    
    Useful when today's cache might not exist yet.
    Searches back up to lookback_days to find cached data.
    
    Args:
        cache_dir: Path to the cache directory
        lookback_days: Maximum days to look back (default 7)
        
    Returns:
        Sorted list of unique ticker symbols found in cache.
    """
    from datetime import timedelta

    cache_path = Path(cache_dir) if isinstance(cache_dir, str) else cache_dir

    if not cache_path.exists():
        return []

    all_tickers: set = set()

    for i in range(lookback_days):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        tickers = get_cached_tickers(cache_path, date)
        if tickers:
            all_tickers.update(tickers)
            break  # Found data, stop looking back

    return sorted(all_tickers)


def get_cache_dates(cache_dir: Union[str, Path]) -> List[str]:
    """
    Get all unique dates available in the cache.
    
    Args:
        cache_dir: Path to the cache directory
        
    Returns:
        Sorted list of date strings (YYYY-MM-DD) in descending order (most recent first)
    """
    cache_path = Path(cache_dir) if isinstance(cache_dir, str) else cache_dir

    if not cache_path.exists():
        return []

    dates: set = set()

    for f in cache_path.glob("*.json"):
        # Extract date from filename like "NVDA_2024-12-21.json"
        parts = f.stem.rsplit('_', 1)
        if len(parts) == 2:
            date_str = parts[1]
            # Validate it's a date
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
                dates.add(date_str)
            except ValueError:
                continue

    return sorted(dates, reverse=True)

