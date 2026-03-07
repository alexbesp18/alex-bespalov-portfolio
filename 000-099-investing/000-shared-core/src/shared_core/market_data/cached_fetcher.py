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

import datetime
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from shared_core.config.constants import CACHE_CONFIG, RATE_LIMITS
from shared_core.market_data.twelve_data import ApiCreditExhausted, _build_key_pool

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
        api_keys: Optional[List[str]] = None,
    ):
        """
        Initialize the cache-aware fetcher.

        Args:
            api_key: Twelve Data API key (primary)
            cache_dir: Path to cache directory (default: auto-detect from project structure)
            rate_limit_delay: Delay between API calls in seconds
            output_size: Number of data points to fetch from API
            api_keys: Optional list of API keys for rotation on credit exhaustion
        """
        self._key_pool = _build_key_pool(api_key, api_keys)
        self._key_index = 0
        self.api_key = self._key_pool[0]
        self.base_url = "https://api.twelvedata.com"
        self.rate_limit_delay = rate_limit_delay
        self.output_size = output_size
        self.today = os.environ.get('CACHE_DATE') or datetime.date.today().isoformat()

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

    def _rotate_key(self) -> bool:
        """Advance to the next API key. Returns False if all keys exhausted."""
        self._key_index += 1
        if self._key_index >= len(self._key_pool):
            return False
        self.api_key = self._key_pool[self._key_index]
        logger.info(f"🔄 Rotating to API key {self._key_index + 1}/{len(self._key_pool)}")
        return True

    def _fetch_from_api_once(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Single API fetch attempt. Raises ApiCreditExhausted on credit errors.
        Raises RequestException on network errors (for tenacity to retry).
        """
        url = f"{self.base_url}/time_series"
        params = {
            "symbol": symbol,
            "interval": "1day",
            "outputsize": self.output_size,
            "apikey": self.api_key,
        }

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "status" in data and data["status"] == "error":
            msg = data.get("message", "Unknown")
            if "credit" in msg.lower():
                raise ApiCreditExhausted(self._key_index)
            logger.error(f"API error for {symbol}: {msg}")
            return None

        if "values" not in data:
            logger.warning(f"No values in API response for {symbol}")
            return None

        if "meta" not in data:
            data["meta"] = {}
        data["meta"]["source"] = "api"

        logger.info(f"🌐 Fetched from API: {symbol} ({len(data['values'])} rows)")
        return data

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
    )
    def _fetch_with_retry(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Retries on network errors only. ApiCreditExhausted passes through."""
        return self._fetch_from_api_once(symbol)

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

        # Fall back to API with key rotation
        while True:
            try:
                return self._fetch_with_retry(symbol)
            except ApiCreditExhausted:
                if not self._rotate_key():
                    logger.error(f"All API keys exhausted fetching {symbol}")
                    return None

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
        all_keys_exhausted = False

        for i, symbol in enumerate(symbols):
            if all_keys_exhausted:
                results[symbol] = None
                continue

            logger.info(f"Fetching {symbol} ({i+1}/{total})...")

            # Check cache first (no rate limit needed)
            cached = self.get_cached_data(symbol)
            if cached:
                results[symbol] = cached
                cache_hits += 1
                continue

            # API call with rotation loop (handles any number of keys)
            fetched = False
            while True:
                try:
                    results[symbol] = self._fetch_with_retry(symbol)
                    api_calls += 1
                    fetched = True
                    break
                except ApiCreditExhausted:
                    if not self._rotate_key():
                        logger.error("All API keys exhausted in batch fetch")
                        results[symbol] = None
                        all_keys_exhausted = True
                        break

            if not fetched:
                continue

            # Rate limit for API calls (skip for last ticker)
            if i < total - 1:
                time.sleep(self.rate_limit_delay)

        logger.info(f"Completed: {cache_hits} from cache, {api_calls} from API")
        return results

    def is_cached(self, symbol: str) -> bool:
        """Check if ticker has today's cache without loading data."""
        if not self.cache_dir or not self.cache_dir.exists():
            return False
        cache_file = self.cache_dir / f"{symbol}_{self.today}.json"
        return cache_file.exists()

