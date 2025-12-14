"""
Constants and configuration values.

Centralizes magic numbers and configuration values
for easier maintenance and testing.
"""

from typing import Final

# API Configuration
DEFAULT_API_TIMEOUT: Final[int] = 15  # seconds
DEFAULT_OUTPUTSIZE: Final[int] = 200  # days of historical data
MIN_DATA_POINTS: Final[int] = 50  # minimum bars needed for analysis

# Technical Indicator Periods
RSI_PERIOD: Final[int] = 14
MACD_FAST: Final[int] = 12
MACD_SLOW: Final[int] = 26
MACD_SIGNAL: Final[int] = 9
BOLLINGER_PERIOD: Final[int] = 20
BOLLINGER_STD: Final[float] = 2.0
ATR_PERIOD: Final[int] = 14
STOCHASTIC_K: Final[int] = 14
STOCHASTIC_D: Final[int] = 3

# Moving Average Periods
SMA_SHORT: Final[int] = 20
SMA_MEDIUM: Final[int] = 50
SMA_LONG: Final[int] = 200

# Support/Resistance Windows
SR_SHORT_WINDOW: Final[int] = 20
SR_LONG_WINDOW: Final[int] = 90

# Agreement Thresholds
VARIANCE_FULL_AGREEMENT: Final[float] = 1.0
VARIANCE_PARTIAL_AGREEMENT: Final[float] = 2.5
VARIANCE_HIGH: Final[float] = 4.0

# Retry Configuration
MAX_RETRY_ATTEMPTS: Final[int] = 3
RETRY_MIN_WAIT: Final[int] = 2  # seconds
RETRY_MAX_WAIT: Final[int] = 30  # seconds

# Rate Limiting
DELAY_BETWEEN_TICKERS: Final[int] = 2  # seconds

# Ticker Validation
TICKER_PATTERN: Final[str] = r'^[A-Z]{1,5}$'
TICKER_MAX_LENGTH: Final[int] = 5

# Version
__version__: Final[str] = "1.0.0"
