"""
Pytest configuration and fixtures for Stock Tracker tests.
"""
import pandas as pd
import pytest


@pytest.fixture
def sample_historical_data() -> pd.DataFrame:
    """
    Create sample historical stock data for testing.

    Returns:
        DataFrame with Open, High, Low, Close, Volume columns
    """
    dates = pd.date_range("2023-01-01", periods=10, freq="D")
    data = {
        "Open": [100.0, 102.0, 101.0, 103.0, 105.0, 104.0, 106.0, 108.0, 107.0, 110.0],
        "High": [102.0, 103.0, 102.5, 104.0, 106.0, 105.0, 107.0, 109.0, 108.0, 111.0],
        "Low": [99.0, 101.0, 100.5, 102.0, 104.0, 103.0, 105.0, 107.0, 106.0, 109.0],
        "Close": [101.0, 102.5, 101.5, 103.5, 105.5, 104.5, 106.5, 108.5, 107.5, 110.5],
        "Volume": [1000000] * 10,
    }
    df = pd.DataFrame(data, index=dates)
    return df


@pytest.fixture
def sample_metrics() -> dict:
    """
    Sample metrics dictionary for testing.

    Returns:
        Dictionary with expected metric keys and values
    """
    return {
        "start_price": 100.0,
        "min_price": 95.0,
        "max_price": 120.0,
        "current_price": 110.0,
        "current_percentile": 91.67,  # (110/120) * 100
        "price_range": 25.0,
        "change_percent": 10.0,  # ((110-100)/100) * 100
    }


@pytest.fixture
def empty_dataframe() -> pd.DataFrame:
    """Return an empty DataFrame for testing edge cases."""
    return pd.DataFrame()


@pytest.fixture
def single_row_dataframe() -> pd.DataFrame:
    """Return a DataFrame with a single row for testing edge cases."""
    return pd.DataFrame({"Close": [100.0]}, index=[pd.Timestamp("2023-01-01")])

