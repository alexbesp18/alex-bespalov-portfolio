"""
Shared fixtures for all shared_core tests.

Provides:
- Sample OHLCV DataFrames with realistic price action
- Mock API responses
- Temporary file paths for state tests
- Common test data
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

# Ensure shared_core is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_ohlcv_df():
    """
    250-day OHLCV DataFrame with realistic price action.
    
    Uses seed 42 for reproducibility. Includes:
    - Trending price with random walk
    - Realistic OHLC relationships
    - Volume data
    """
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=250, freq='D')
    base_price = 100.0
    returns = np.random.normal(0.001, 0.02, 250)
    prices = base_price * np.cumprod(1 + returns)
    
    return pd.DataFrame({
        'open': prices * (1 + np.random.uniform(-0.01, 0.01, 250)),
        'high': prices * (1 + np.abs(np.random.uniform(0, 0.02, 250))),
        'low': prices * (1 - np.abs(np.random.uniform(0, 0.02, 250))),
        'close': prices,
        'volume': np.random.randint(1_000_000, 10_000_000, 250)
    }, index=dates)


@pytest.fixture
def sample_ohlcv_df_with_indicators(sample_ohlcv_df):
    """
    OHLCV DataFrame with pre-calculated indicators.
    
    Adds: SMA_20, SMA_50, SMA_200, RSI, MACD_HIST, STOCH_K, STOCH_D,
    ADX, OBV, BB_UPPER, BB_MIDDLE, BB_LOWER, WILLIAMS_R
    """
    from shared_core.data.process_ohlcv import add_standard_indicators
    return add_standard_indicators(sample_ohlcv_df.copy())


@pytest.fixture
def sample_api_response(sample_ohlcv_df):
    """
    Mock Twelve Data API response format.
    
    Returns dict with 'values' key containing list of OHLCV dicts.
    """
    df = sample_ohlcv_df.reset_index()
    df['datetime'] = df['index'].astype(str)
    return {"values": df.drop(columns=['index']).to_dict('records')}


@pytest.fixture
def empty_api_response():
    """Empty API response for edge case testing."""
    return {"values": []}


@pytest.fixture
def insufficient_api_response():
    """API response with insufficient data (< 20 rows)."""
    return {
        "values": [
            {"datetime": "2024-01-01", "open": 100, "high": 101, 
             "low": 99, "close": 100.5, "volume": 1000000}
            for _ in range(10)
        ]
    }


@pytest.fixture
def tmp_state_path(tmp_path):
    """Temporary path for state file tests."""
    return str(tmp_path / "state.json")


@pytest.fixture
def tmp_archive_path(tmp_path):
    """Temporary path for archive file tests."""
    return str(tmp_path / "archive.json")


@pytest.fixture
def tmp_cache_dir(tmp_path):
    """Temporary directory for cache tests with sample files."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    
    # Create sample cache files for today
    today = datetime.now().strftime('%Y-%m-%d')
    for ticker in ["AAPL", "NVDA", "GOOGL"]:
        (cache_dir / f"{ticker}_{today}.json").write_text('{"values": []}')
    
    # Create yesterday's files too
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    for ticker in ["AAPL", "MSFT"]:
        (cache_dir / f"{ticker}_{yesterday}.json").write_text('{"values": []}')
    
    return str(cache_dir)


@pytest.fixture
def sample_watchlist_json(tmp_path):
    """Create a sample watchlist JSON file."""
    import json
    
    watchlist = {
        "entries": [
            {"symbol": "AAPL", "list_type": "portfolio", "triggers": []},
            {"symbol": "NVDA", "list_type": "watchlist", "triggers": []},
            {"symbol": "GOOGL", "list_type": "watchlist", "triggers": []},
        ],
        "default_triggers": [
            {"type": "score_above", "value": 7, "action": "BUY"}
        ]
    }
    
    path = tmp_path / "watchlist.json"
    path.write_text(json.dumps(watchlist))
    return str(path)


@pytest.fixture
def sample_legacy_watchlist_json(tmp_path):
    """Create a legacy format watchlist JSON file."""
    import json
    
    watchlist = {
        "portfolio": ["AAPL", "TSLA"],
        "watchlist": ["NVDA", "GOOGL"],
    }
    
    path = tmp_path / "legacy_watchlist.json"
    path.write_text(json.dumps(watchlist))
    return str(path)


@pytest.fixture
def sample_flags():
    """Sample flag values for trigger testing."""
    return {
        'above_SMA200': True,
        'below_SMA200': False,
        'above_SMA50': True,
        'new_20day_high': False,
        'volume_above_1.5x_avg': False,
        'crosses_above_SMA200': False,
        'crosses_below_SMA200': False,
        'rsi_crosses_above_30': False,
        'rsi_crosses_above_60': False,
        'rsi': 45.0,
        'score': 7.5,
        'close': 150.0,
    }


@pytest.fixture
def sample_triggered_signals():
    """Sample triggered signals for state manager testing."""
    return [
        {
            "symbol": "NVDA",
            "trigger_key": "NVDA_score_above_BUY_7",
            "message": "BUY: Score 8.5 >= 7",
        },
        {
            "symbol": "AAPL",
            "trigger_key": "AAPL_price_crosses_above_ma_SMA_200",
            "message": "BUY: Price crossed above SMA_200",
        },
    ]


@pytest.fixture
def uptrend_df():
    """DataFrame with clear uptrend for testing bullish scores."""
    np.random.seed(123)
    dates = pd.date_range(end=datetime.now(), periods=250, freq='D')
    # Strong uptrend with positive drift
    returns = np.random.normal(0.003, 0.01, 250)
    prices = 100.0 * np.cumprod(1 + returns)
    
    return pd.DataFrame({
        'open': prices * 0.995,
        'high': prices * 1.01,
        'low': prices * 0.99,
        'close': prices,
        'volume': np.random.randint(1_000_000, 10_000_000, 250)
    }, index=dates)


@pytest.fixture
def downtrend_df():
    """DataFrame with clear downtrend for testing bearish/oversold scores."""
    np.random.seed(456)
    dates = pd.date_range(end=datetime.now(), periods=250, freq='D')
    # Strong downtrend with negative drift
    returns = np.random.normal(-0.003, 0.01, 250)
    prices = 100.0 * np.cumprod(1 + returns)
    
    return pd.DataFrame({
        'open': prices * 1.005,
        'high': prices * 1.01,
        'low': prices * 0.99,
        'close': prices,
        'volume': np.random.randint(1_000_000, 10_000_000, 250)
    }, index=dates)


@pytest.fixture
def divergence_df():
    """DataFrame designed to show bullish divergence."""
    np.random.seed(789)
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    
    # Price makes lower lows but RSI would show higher lows (bullish divergence)
    # First half: decline
    prices1 = np.linspace(100, 80, 50)
    # Second half: further decline but flattening
    prices2 = np.linspace(80, 75, 50)
    prices = np.concatenate([prices1, prices2])
    
    # Add some noise
    prices = prices + np.random.normal(0, 1, 100)
    
    return pd.DataFrame({
        'open': prices * 1.001,
        'high': prices * 1.02,
        'low': prices * 0.98,
        'close': prices,
        'volume': np.random.randint(1_000_000, 10_000_000, 100)
    }, index=dates)


# Marker for slow tests
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )

