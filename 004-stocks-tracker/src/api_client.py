"""
Stock market data API client using yfinance (free, no API key required).

Provides retry logic, rate limiting, and comprehensive error handling
for fetching stock market data from Yahoo Finance.
"""
import logging
import time
from typing import Optional

import pandas as pd
import yfinance as yf
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from .config import settings, logger

# Constants
MAX_SYMBOL_LENGTH = 10
MIN_SYMBOL_LENGTH = 1
VALID_DURATIONS = ["1 month", "3 months", "6 months", "1 year", "2 years", "5 years"]


class StockDataClient:
    """Client for fetching stock market data with retry logic and rate limiting."""

    DURATION_MAPPING: dict[str, str] = {
        "1 month": "1mo",
        "3 months": "3mo",
        "6 months": "6mo",
        "1 year": "1y",
        "2 years": "2y",
        "5 years": "5y",
    }

    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(
            multiplier=1,
            min=settings.retry_base_delay,
            max=settings.retry_max_delay,
        ),
        retry=retry_if_exception_type((ConnectionError, TimeoutError, Exception)),
        reraise=True,
    )
    def _fetch_historical_data_internal(
        symbol: str, period: str
    ) -> pd.DataFrame:
        """
        Internal method to fetch historical data with retry logic.

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')
            period: Period string for yfinance (e.g., '1y', '6mo')

        Returns:
            DataFrame with historical price data

        Raises:
            Exception: If data fetch fails after retries
        """
        logger.debug(f"Fetching historical data for {symbol} with period {period}")
        hist = yf.download(
            tickers=symbol,
            period=period,
            progress=False,
            auto_adjust=True,
        )

        if hist.empty:
            raise ValueError(f"No data returned for {symbol} with period {period}")

        return hist

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
            DataFrame columns typically include: Open, High, Low, Close, Volume
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
            period = StockDataClient.DURATION_MAPPING.get(duration, "1y")
            logger.info(f"Fetching historical data for {symbol} ({duration})")

            # Fetch data with retry logic
            hist = StockDataClient._fetch_historical_data_internal(symbol, period)

            # Add delay to avoid rate limiting
            time.sleep(settings.api_delay_seconds)

            logger.debug(
                f"Successfully fetched {len(hist)} data points for {symbol}"
            )
            return hist

        except ValueError as e:
            logger.warning(f"No data available for {symbol}: {e}")
            return None
        except (ConnectionError, TimeoutError) as e:
            logger.error(
                f"Network error fetching data for {symbol}: {e}",
                exc_info=True,
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error fetching data for {symbol}: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(
            multiplier=1,
            min=settings.retry_base_delay,
            max=settings.retry_max_delay,
        ),
        retry=retry_if_exception_type((ConnectionError, TimeoutError, Exception)),
        reraise=True,
    )
    def get_current_price(symbol: str) -> Optional[float]:
        """
        Get current stock price with retry logic.

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
            logger.debug(f"Fetching current price for {symbol}")
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Try different price fields (yfinance may use different keys)
            current_price = info.get("currentPrice") or info.get("regularMarketPrice")

            if current_price is None:
                logger.warning(
                    f"Price not found in info dict for {symbol}. "
                    f"Available keys: {list(info.keys())[:10]}..."
                )
                return None

            logger.debug(f"Current price for {symbol}: ${current_price}")
            return float(current_price)

        except (ConnectionError, TimeoutError) as e:
            logger.error(
                f"Network error fetching current price for {symbol}: {e}",
                exc_info=True,
            )
            return None
        except Exception as e:
            logger.error(
                f"Error fetching current price for {symbol}: {e}",
                exc_info=True,
            )
            return None
