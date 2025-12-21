"""
fetch_prices.py — Twelve Data API fetcher using shared_core CacheAwareFetcher.

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


class PriceFetcher:
    """
    Fetches price data from Twelve Data API with shared cache support.
    
    Wrapper around shared_core.CacheAwareFetcher for backward compatibility.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._fetcher = CacheAwareFetcher(
            api_key=api_key,
            cache_dir=SHARED_CACHE_DIR,
            rate_limit_delay=7.5,  # 8 requests/minute
            output_size=250,
        )
    
    def fetch_ticker(self, symbol: str, outputsize: int = 250) -> Optional[Dict[str, Any]]:
        """
        Fetch OHLCV data for a single ticker.
        First checks shared cache, then falls back to API.
        
        Returns dict with 'values' containing historical data.
        """
        return self._fetcher.fetch(symbol)
    
    def fetch_all_tickers(self, tickers: List[str]) -> Dict[str, Optional[Dict]]:
        """
        Fetch data for all tickers, using cache when available.
        Only applies rate limiting for API calls (not cached data).
        
        Args:
            tickers: List of ticker symbols
            
        Returns:
            Dict mapping symbol -> API response (or None if failed)
        """
        return self._fetcher.fetch_batch(tickers)


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    api_key = os.getenv("TWELVE_DATA_API_KEY")
    if api_key:
        fetcher = PriceFetcher(api_key)
        data = fetcher.fetch_ticker("AAPL")
        if data:
            print(f"Fetched {len(data.get('values', []))} rows for AAPL")
