"""
CacheAwareFetcher - Unified cache-aware data fetcher for Twelve Data.

This module provides a centralized fetcher that:
1. Checks the shared cache (008-ticker-analysis/data/twelve_data/) for today's data
2. Falls back to Twelve Data API if cache miss
3. Handles the column-oriented DataFrame JSON format from the cache

Usage:
    from shared_core.market_data.cached_fetcher import CacheAwareFetcher

    fetcher = CacheAwareFetcher(api_key="...", cache_dir=Path("../008-ticker-analysis/data/twelve_data"))
    data = fetcher.fetch("AAPL")  # Returns API-format dict with 'values'
"""

import json
import time
import datetime
import logging
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from shared_core.config.constants import RATE_LIMITS, CACHE_CONFIG

logger = logging.getLogger(__name__)


class CacheAwareFetcher:
    """
    Unified cache-aware fetcher for Twelve Data API.

    Checks shared cache first, falls back to API on cache miss.
    Handles pandas DataFrame column-oriented JSON format from cache.
    """

    def __init__(
        self,
        api_key: str,
        cache_dir: Optional[Path] = None,
        rate_limit_delay: float = RATE_LIMITS.TWELVE_DATA_DEFAULT_DELAY,
        output_size: int = CACHE_CONFIG.DEFAULT_OUTPUT_SIZE,
    ):
        """
        Initialize the cache-aware fetcher.

        Args:
            api_key: Twelve Data API key
            cache_dir: Path to cache directory (default: auto-detect from project structure)
            rate_limit_delay: Delay between API calls in seconds
            output_size: Number of data points to fetch from API
        """
        self.api_key = api_key
        self.base_url = "https://api.twelvedata.com"
        self.rate_limit_delay = rate_limit_delay
        self.output_size = output_size
        self.today = datetime.date.today().isoformat()

        # Auto-detect cache directory if not provided
        if cache_dir is None:
            # Try common relative paths from consumer projects
            possible_paths = [
                Path(__file__).parent.parent.parent.parent.parent / "007-ticker-analysis" / "data" / "twelve_data",
                Path.cwd().parent / "007-ticker-analysis" / "data" / "twelve_data",
                Path.cwd() / ".." / "007-ticker-analysis" / "data" / "twelve_data",
            ]
            for path in possible_paths:
                if path.exists():
                    cache_dir = path.resolve()
                    break

        self.cache_dir = cache_dir
        if self.cache_dir and self.cache_dir.exists():
            logger.debug(f"Cache directory: {self.cache_dir}")
        else:
            logger.warning(f"Cache directory not found: {cache_dir}")

    def _parse_cached_json(self, data: Dict[str, Any], symbol: str) -> Optional[Dict[str, Any]]:
        """
        Parse column-oriented DataFrame JSON into API-like format.

        Cache format (pandas to_json with orient='columns'):
            {"datetime": {"0": "2024-01-01", ...}, "open": {"0": 100.0, ...}, ...}

        Returns API-like format:
            {"values": [{"datetime": "2024-01-01", "open": "100.0", ...}, ...], ...}
        """
        if not isinstance(data, dict):
            return None

        # Check for required columns
        if "datetime" not in data or "close" not in data:
            return None

        datetime_col = data.get("datetime", {})
        open_col = data.get("open", {})
        high_col = data.get("high", {})
        low_col = data.get("low", {})
        close_col = data.get("close", {})
        volume_col = data.get("volume", {})

        values = []
        for idx in sorted(datetime_col.keys(), key=int):
            dt_val = datetime_col.get(idx, "")
            # Handle both "2024-01-01" and "2024-01-01T00:00:00.000" formats
            if isinstance(dt_val, str) and len(dt_val) >= 10:
                dt_val = dt_val[:10]

            values.append({
                "datetime": dt_val,
                "open": str(open_col.get(idx, "")),
                "high": str(high_col.get(idx, "")),
                "low": str(low_col.get(idx, "")),
                "close": str(close_col.get(idx, "")),
                "volume": str(int(float(volume_col.get(idx, 0)))) if volume_col.get(idx) else "0"
            })

        return {
            "values": values,
            "status": "ok",
            "meta": {"symbol": symbol, "source": "cache"}
        }

    def get_cached_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Check shared cache for today's data.

        Args:
            symbol: Ticker symbol (e.g., "AAPL")

        Returns:
            API-format dict with 'values' if cached, None otherwise
        """
        if not self.cache_dir or not self.cache_dir.exists():
            return None

        cache_file = self.cache_dir / f"{symbol}_{self.today}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r') as f:
                raw_data = json.load(f)

            result = self._parse_cached_json(raw_data, symbol)
            if result and result.get("values"):
                logger.info(f"📁 Using cached data for {symbol} ({len(result['values'])} rows)")
                return result

        except json.JSONDecodeError as e:
            logger.warning(f"Cache JSON parse error for {symbol}: {e}")
        except OSError as e:
            logger.warning(f"Cache file read error for {symbol}: {e}")
        except (KeyError, TypeError) as e:
            logger.warning(f"Cache data structure error for {symbol}: {e}")

        return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _fetch_from_api(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch data from Twelve Data API.

        Args:
            symbol: Ticker symbol

        Returns:
            API response dict with 'values' key, or None on error
        """
        url = f"{self.base_url}/time_series"
        params = {
            "symbol": symbol,
            "interval": "1day",
            "outputsize": self.output_size,
            "apikey": self.api_key
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if "status" in data and data["status"] == "error":
                logger.error(f"API error for {symbol}: {data.get('message', 'Unknown')}")
                return None

            if "values" not in data:
                logger.warning(f"No values in API response for {symbol}")
                return None

            # Add source metadata
            if "meta" not in data:
                data["meta"] = {}
            data["meta"]["source"] = "api"

            logger.info(f"🌐 Fetched from API: {symbol} ({len(data['values'])} rows)")
            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching {symbol}: {e}")
            raise

    def fetch(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch data for a single ticker (cache-first, API fallback).

        Args:
            symbol: Ticker symbol

        Returns:
            Dict with 'values' key containing OHLCV data, or None on error
        """
        # Check cache first
        cached = self.get_cached_data(symbol)
        if cached:
            return cached

        # Fall back to API
        return self._fetch_from_api(symbol)

    def fetch_batch(self, symbols: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Fetch data for multiple tickers with rate limiting.

        Only applies rate limiting for API calls (not cached data).

        Args:
            symbols: List of ticker symbols

        Returns:
            Dict mapping symbol -> data dict (or None if failed)
        """
        results = {}
        total = len(symbols)
        api_calls = 0
        cache_hits = 0

        for i, symbol in enumerate(symbols):
            logger.info(f"Fetching {symbol} ({i+1}/{total})...")

            # Check cache first (no rate limit needed)
            cached = self.get_cached_data(symbol)
            if cached:
                results[symbol] = cached
                cache_hits += 1
                continue

            # API call needed
            try:
                results[symbol] = self._fetch_from_api(symbol)
                api_calls += 1

                # Rate limit for API calls (skip for last ticker)
                if i < total - 1:
                    time.sleep(self.rate_limit_delay)

            except requests.exceptions.RequestException as e:
                logger.error(f"Network error fetching {symbol}: {e}")
                results[symbol] = None
            except (ValueError, KeyError, TypeError) as e:
                logger.error(f"Data error fetching {symbol}: {e}")
                results[symbol] = None

        logger.info(f"Completed: {cache_hits} from cache, {api_calls} from API")
        return results

    def is_cached(self, symbol: str) -> bool:
        """Check if ticker has today's cache without loading data."""
        if not self.cache_dir or not self.cache_dir.exists():
            return False
        cache_file = self.cache_dir / f"{symbol}_{self.today}.json"
        return cache_file.exists()

