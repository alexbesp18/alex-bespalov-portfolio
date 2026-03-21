"""yfinance data fetching. Fetches option chains and filters to specific strikes."""

import logging
import time

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


def fetch_chain_for_expiration(
    ticker_symbol: str, expiration: str, delay: float = 2.0
) -> tuple[float, pd.DataFrame]:
    """
    Fetch the call option chain for a specific ticker + expiration.
    Returns (spot_price, calls_dataframe).
    """
    ticker = yf.Ticker(ticker_symbol)
    spot = ticker.info.get("regularMarketPrice") or ticker.info.get("currentPrice") or 0
    chain = ticker.option_chain(expiration)
    calls = chain.calls.copy()
    calls["volume"] = calls["volume"].fillna(0).astype(int)
    time.sleep(delay)
    return float(spot), calls


def fetch_strikes_from_chain(
    calls_df: pd.DataFrame, strikes: set[float]
) -> pd.DataFrame:
    """Filter a chain DataFrame to only the specific strikes we care about."""
    return calls_df[calls_df["strike"].isin(strikes)]
