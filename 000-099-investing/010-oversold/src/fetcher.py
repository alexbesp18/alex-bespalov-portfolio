"""
fetcher.py — Twelve Data API fetcher using shared_core CacheAwareFetcher.

Uses shared cache from 008-ticker-analysis if available from today,
otherwise fetches fresh data from API.
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from shared_core.market_data.cached_fetcher import CacheAwareFetcher

logger = logging.getLogger(__name__)

# Shared cache location (relative to this file's directory)
SHARED_CACHE_DIR = Path(__file__).parent.parent.parent / "007-ticker-analysis" / "data" / "twelve_data"


class TwelveDataFetcher:
    """
    Fetches data from Twelve Data API with shared cache support.
    
    Wrapper around shared_core.CacheAwareFetcher for backward compatibility.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._fetcher = CacheAwareFetcher(
            api_key=api_key,
            cache_dir=SHARED_CACHE_DIR,
            rate_limit_delay=12.0,  # ~5 requests/minute (conservative)
            output_size=300,
        )

    def fetch_time_series(self, symbol: str, interval: str = "1day", outputsize: int = 300) -> Optional[Dict[str, Any]]:
        """
        Fetch data for a single symbol, checking cache first.
        
        Args:
            symbol: Ticker symbol
            interval: Time interval (ignored, always 1day)
            outputsize: Number of data points (used for API fallback)
            
        Returns:
            Dict with 'values' containing OHLCV data
        """
        return self._fetcher.fetch(symbol)

    def fetch_batch_time_series(self, symbols: List[str], interval: str = "1day", outputsize: int = 300) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Fetch data for multiple symbols, using cache when available.
        Only applies rate limiting for API calls (not cached data).
        
        Args:
            symbols: List of ticker symbols
            interval: Time interval (ignored, always 1day)
            outputsize: Number of data points
            
        Returns:
            Dict mapping symbol -> data dict
        """
        return self._fetcher.fetch_batch(symbols)


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    api_key = os.getenv("TWELVE_DATA_API_KEY")
    if api_key:
        fetcher = TwelveDataFetcher(api_key)
        data = fetcher.fetch_time_series("AAPL")
        if data:
            print(f"Fetched {len(data.get('values', []))} rows for AAPL")
