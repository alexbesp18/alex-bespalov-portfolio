"""
Stock price calculations and metrics.

Provides functions to calculate various stock performance metrics
from historical price data.
"""
from typing import Optional, TypedDict

import pandas as pd

from .config import logger

# Constants
CLOSE_COLUMN = "Close"
MIN_DATA_POINTS_REQUIRED = 2


class StockMetrics(TypedDict):
    """Type definition for stock metrics dictionary."""

    start_price: float
    min_price: float
    max_price: float
    current_price: float
    current_percentile: float
    price_range: float
    change_percent: float


class StockCalculator:
    """Calculate stock price metrics from historical data."""

    @staticmethod
    def calculate_metrics(
        hist_data: pd.DataFrame,
    ) -> Optional[StockMetrics]:
        """
        Calculate comprehensive stock metrics from historical price data.

        Computes key performance indicators including price range, percentiles,
        and percentage changes over the specified time period.

        Args:
            hist_data: DataFrame with historical price data. Must contain
                      a 'Close' column with closing prices.

        Returns:
            Dictionary containing calculated metrics:
                - start_price: Price at the beginning of the period
                - min_price: Minimum price during the period
                - max_price: Maximum price during the period
                - current_price: Most recent closing price
                - current_percentile: Current price as percentile of max (0-100)
                  where 100% = at peak, 0% = at minimum
                - price_range: Difference between max and min prices
                - change_percent: Percentage change from start to current price
            Returns None if input data is invalid or calculation fails.

        Example:
            >>> import pandas as pd
            >>> data = pd.DataFrame({'Close': [100, 110, 105, 120]})
            >>> metrics = StockCalculator.calculate_metrics(data)
            >>> print(metrics['change_percent'])
            20.0
        """
        if hist_data is None or hist_data.empty:
            logger.warning("Cannot calculate metrics: empty or None DataFrame")
            return None

        try:
            # Validate that 'Close' column exists
            if CLOSE_COLUMN not in hist_data.columns:
                logger.error(
                    f"DataFrame missing '{CLOSE_COLUMN}' column. "
                    f"Available columns: {list(hist_data.columns)}"
                )
                return None

            # Use Close prices for calculations
            prices = hist_data[CLOSE_COLUMN]

            if len(prices) < MIN_DATA_POINTS_REQUIRED:
                logger.warning(
                    f"Insufficient data points for calculation: {len(prices)} "
                    f"(minimum required: {MIN_DATA_POINTS_REQUIRED})"
                )
                return None

            start_price = float(prices.iloc[0])
            current_price = float(prices.iloc[-1])
            min_price = float(prices.min())
            max_price = float(prices.max())

            # Calculate current price as percentile of max
            # 100% means current price equals max, 0% means at minimum
            if max_price > 0:
                current_percentile = (current_price / max_price) * 100
            else:
                logger.warning("Max price is zero or negative, setting percentile to 0")
                current_percentile = 0.0

            # Calculate price change percentage
            if start_price > 0:
                change_percent = ((current_price - start_price) / start_price) * 100
            else:
                logger.warning("Start price is zero or negative, setting change to 0")
                change_percent = 0.0

            price_range = max_price - min_price

            metrics: StockMetrics = {
                "start_price": round(start_price, 2),
                "min_price": round(min_price, 2),
                "max_price": round(max_price, 2),
                "current_price": round(current_price, 2),
                "current_percentile": round(current_percentile, 2),
                "price_range": round(price_range, 2),
                "change_percent": round(change_percent, 2),
            }

            logger.debug(f"Calculated metrics: {metrics}")
            return metrics

        except KeyError as e:
            logger.error(f"Missing required column in DataFrame: {e}", exc_info=True)
            return None
        except (ValueError, IndexError) as e:
            logger.error(
                f"Data processing error during metric calculation: {e}",
                exc_info=True,
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error calculating metrics: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def format_metrics_display(
        symbol: str, name: str, metrics: Optional[StockMetrics]
    ) -> str:
        """
        Format stock metrics as a human-readable string.

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')
            name: Company name (e.g., 'Apple Inc.')
            metrics: Dictionary of calculated metrics from calculate_metrics()

        Returns:
            Formatted markdown string with metrics, or error message if metrics
            are None or unavailable.

        Example:
            >>> metrics = {'start_price': 100, 'current_price': 120, ...}
            >>> output = StockCalculator.format_metrics_display('AAPL', 'Apple', metrics)
        """
        if not metrics:
            return f"{symbol} ({name}): Data unavailable"

        change_symbol = "+" if metrics["change_percent"] >= 0 else ""

        return f"""
**{symbol} - {name}**
- Start Price: ${metrics['start_price']:.2f}
- Min Price: ${metrics['min_price']:.2f}
- Max Price: ${metrics['max_price']:.2f}
- Current Price: ${metrics['current_price']:.2f} ({metrics['current_percentile']:.2f}% of max)
- Change: {change_symbol}{metrics['change_percent']:.2f}%
        """
