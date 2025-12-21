"""
fetch_prices.py — Twelve Data API fetcher with rate limiting.

Rate limit: 8 requests/minute = 7.5 seconds between calls.
"""

import os
import time
import logging
import requests
from typing import Dict, List, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

RATE_LIMIT = 8  # requests per minute
DELAY = 60 / RATE_LIMIT  # 7.5 seconds between calls


class PriceFetcher:
    """Fetches price data from Twelve Data API with rate limiting."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.twelvedata.com"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def fetch_ticker(self, symbol: str, outputsize: int = 250) -> Optional[Dict[str, Any]]:
        """
        Fetch OHLCV data for a single ticker.
        Returns dict with 'values' containing historical data.
        """
        url = f"{self.base_url}/time_series"
        params = {
            "symbol": symbol,
            "interval": "1day",
            "outputsize": outputsize,
            "apikey": self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if "status" in data and data["status"] == "error":
                logger.error(f"API Error for {symbol}: {data.get('message', 'Unknown')}")
                return None
            
            if "values" not in data:
                logger.warning(f"No values in response for {symbol}")
                return None
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching {symbol}: {e}")
            raise
    
    def fetch_all_tickers(self, tickers: List[str]) -> Dict[str, Optional[Dict]]:
        """
        Fetch data for all tickers with rate limiting.
        
        Args:
            tickers: List of ticker symbols
            
        Returns:
            Dict mapping symbol -> API response (or None if failed)
        """
        results = {}
        total = len(tickers)
        
        for i, ticker in enumerate(tickers):
            logger.info(f"Fetching {ticker} ({i+1}/{total})...")
            
            try:
                results[ticker] = self.fetch_ticker(ticker)
            except Exception as e:
                logger.error(f"Failed to fetch {ticker}: {e}")
                results[ticker] = None
            
            # Rate limit: sleep between calls (except after last one)
            if i < total - 1:
                logger.debug(f"Sleeping {DELAY:.1f}s for rate limit...")
                time.sleep(DELAY)
        
        return results


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    api_key = os.getenv("TWELVE_DATA_API_KEY")
    if api_key:
        fetcher = PriceFetcher(api_key)
        data = fetcher.fetch_ticker("AAPL")
        if data:
            print(f"Fetched {len(data.get('values', []))} rows for AAPL")
