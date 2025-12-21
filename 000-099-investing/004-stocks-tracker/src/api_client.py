"""
Stock market data API client using Twelve Data via shared_core.

Provides retry logic, rate limiting, and comprehensive error handling
for fetching stock market data.
"""
import os
import time
from pathlib import Path
from typing import Optional

import pandas as pd
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from shared_core import TwelveDataClient, DataCache
from .config import settings, logger

# Constants
MAX_SYMBOL_LENGTH = 10
MIN_SYMBOL_LENGTH = 1
VALID_DURATIONS = ["1 month", "3 months", "6 months", "1 year", "2 years", "5 years"]


class StockDataClient:
    """Client for fetching stock market data using Twelve Data via shared_core."""

    DURATION_MAPPING: dict[str, int] = {
        "1 month": 30,
        "3 months": 90,
        "6 months": 180,
        "1 year": 365,
        "2 years": 730,
        "5 years": 1825,
    }
    
    _instance = None
    _client = None
    _cache = None
    
    @classmethod
    def _get_client(cls) -> TwelveDataClient:
        """Get or create the TwelveDataClient singleton."""
        if cls._client is None:
            # Get API key from environment or config
            api_key = os.getenv('TWELVE_DATA_API_KEY', settings.twelve_data_api_key if hasattr(settings, 'twelve_data_api_key') else '')
            
            if not api_key:
                raise ValueError(
                    "TWELVE_DATA_API_KEY environment variable or config setting required. "
                    "Get a free API key at https://twelvedata.com/"
                )
            
            # Initialize cache
            cache_dir = Path(__file__).parent.parent / 'data'
            cache_dir.mkdir(exist_ok=True)
            cls._cache = DataCache(cache_dir, verbose=False)
            
            # Initialize client
            cls._client = TwelveDataClient(
                api_key=api_key,
                cache=cls._cache,
                output_size=365,
                rate_limit_sleep=settings.api_delay_seconds if hasattr(settings, 'api_delay_seconds') else 0.5,
                verbose=False
            )
        
        return cls._client

    @staticmethod
    def get_historical_data(symbol: str, duration: str) -> Optional[pd.DataFrame]:
        """
        Fetch historical stock data for a given symbol and duration.

        Includes retry logic, rate limiting, and comprehensive error handling.

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')
            duration: Duration string (e.g., '1 month', '1 year')

        Returns:
            DataFrame with historical price data or None if error.
            DataFrame columns: open, high, low, close, volume
        """
        # Input validation
        if not symbol or not isinstance(symbol, str):
            logger.error(f"Invalid symbol: {symbol}")
            return None
        
        symbol = symbol.strip().upper()
        
        if not (MIN_SYMBOL_LENGTH <= len(symbol) <= MAX_SYMBOL_LENGTH):
            logger.error(
                f"Symbol length invalid: {len(symbol)} "
                f"(must be between {MIN_SYMBOL_LENGTH} and {MAX_SYMBOL_LENGTH})"
            )
            return None
        
        if duration not in VALID_DURATIONS:
            logger.warning(
                f"Unknown duration '{duration}', defaulting to '1 year'. "
                f"Valid durations: {VALID_DURATIONS}"
            )
            duration = "1 year"
        
        try:
            client = StockDataClient._get_client()
            
            logger.info(f"Fetching historical data for {symbol} ({duration})")
            
            # Fetch data via TwelveDataClient
            df = client.get_dataframe(symbol)
            
            if df is None or df.empty:
                logger.warning(f"No data available for {symbol}")
                return None
            
            # Filter to requested duration
            output_size = StockDataClient.DURATION_MAPPING.get(duration, 365)
            if len(df) > output_size:
                df = df.tail(output_size)
            
            # Standardize column names to match previous API (capitalize for backwards compatibility)
            df = df.rename(columns={
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            })
            
            # Set datetime as index if it's a column
            if 'datetime' in df.columns:
                df = df.set_index('datetime')
            
            logger.debug(f"Successfully fetched {len(df)} data points for {symbol}")
            return df

        except ValueError as e:
            logger.warning(f"No data available for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error fetching data for {symbol}: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_current_price(symbol: str) -> Optional[float]:
        """
        Get current stock price.

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')

        Returns:
            Current price as float or None if error or price unavailable
        """
        # Input validation
        if not symbol or not isinstance(symbol, str):
            logger.error(f"Invalid symbol: {symbol}")
            return None
        
        symbol = symbol.strip().upper()
        
        if not (MIN_SYMBOL_LENGTH <= len(symbol) <= MAX_SYMBOL_LENGTH):
            logger.error(
                f"Symbol length invalid: {len(symbol)} "
                f"(must be between {MIN_SYMBOL_LENGTH} and {MAX_SYMBOL_LENGTH})"
            )
            return None
        
        try:
            client = StockDataClient._get_client()
            
            logger.debug(f"Fetching current price for {symbol}")
            
            # Get latest data point
            df = client.get_dataframe(symbol)
            
            if df is None or df.empty:
                logger.warning(f"Price not found for {symbol}")
                return None
            
            current_price = float(df['close'].iloc[-1])
            
            logger.debug(f"Current price for {symbol}: ${current_price:.2f}")
            return current_price

        except Exception as e:
            logger.error(
                f"Error fetching current price for {symbol}: {e}",
                exc_info=True,
            )
            return None
