"""Pytest fixtures for testing."""

import pytest

# Sample OHLCV data for testing
SAMPLE_OHLCV_DATA = [
    {'datetime': '2024-01-01', 'open': 100.0, 'high': 105.0, 'low': 99.0, 'close': 104.0, 'volume': 1000000},
    {'datetime': '2024-01-02', 'open': 104.0, 'high': 108.0, 'low': 103.0, 'close': 107.0, 'volume': 1200000},
    {'datetime': '2024-01-03', 'open': 107.0, 'high': 110.0, 'low': 106.0, 'close': 109.0, 'volume': 1100000},
    {'datetime': '2024-01-04', 'open': 109.0, 'high': 112.0, 'low': 108.0, 'close': 111.0, 'volume': 1300000},
    {'datetime': '2024-01-05', 'open': 111.0, 'high': 115.0, 'low': 110.0, 'close': 114.0, 'volume': 1400000},
]


@pytest.fixture
def sample_prices():
    """Sample close prices for indicator testing."""
    import pandas as pd
    data = [100 + i + (i % 3) for i in range(50)]  # 50 days of simulated prices
    return pd.Series(data)


@pytest.fixture
def sample_ohlcv_df():
    """Sample OHLCV DataFrame for indicator testing."""
    import pandas as pd
    import numpy as np
    
    np.random.seed(42)
    n = 100
    
    close = 100 + np.cumsum(np.random.randn(n) * 2)
    high = close + np.abs(np.random.randn(n))
    low = close - np.abs(np.random.randn(n))
    open_price = (close + np.random.randn(n) * 0.5)
    
    df = pd.DataFrame({
        'datetime': pd.date_range('2024-01-01', periods=n),
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': np.random.randint(100000, 2000000, n)
    })
    
    return df


@pytest.fixture
def sample_config_dict():
    """Sample configuration dictionary."""
    return {
        'api_keys': {
            'anthropic': 'test-key',
            'openai': 'test-key',
            'google': 'test-key',
            'xai': 'test-key',
            'twelve_data': 'test-key'
        },
        'google_sheet_url': 'https://docs.google.com/spreadsheets/test',
        'claude_settings': {
            'enabled': True,
            'model': 'sonnet-4.5'
        },
        'openai_settings': {
            'enabled': True,
            'model': 'gpt-4o'
        },
        'gemini_settings': {
            'enabled': True,
            'model': 'gemini-2.0-flash'
        },
        'grok_settings': {
            'enabled': True,
            'model': 'grok-2'
        },
        'global_settings': {
            'use_concurrent': True,
            'max_workers': 3
        }
    }
