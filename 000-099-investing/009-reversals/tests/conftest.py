import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import pandas as pd
import numpy as np

@pytest.fixture
def sample_market_data():
    """Returns a DataFrame with 100 periods of mock OHLCV data."""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    close = np.linspace(100, 150, 100)
    
    df = pd.DataFrame({
        'datetime': dates,
        'open': close - 1,
        'high': close + 2,
        'low': close - 2,
        'close': close,
        'volume': np.full(100, 1000)
    })
    df = df.set_index('datetime')
    return df

@pytest.fixture
def divergence_setup_data():
    """
    Creates data with a bullish divergence pattern:
    Price makes lower low, RSI makes higher low.
    """
    dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
    
    # Base price downtrend
    close = np.linspace(100, 80, 50)
    
    # Create Lower Low in price at end
    close[-10] = 85 # Swing low 1
    close[-1] = 80  # Swing low 2 (Lower)
    
    # RSI Mock (simulate via separate series) -> passed manually or calculated
    # Here we just return the DF, indicators need to be added by test
    
    df = pd.DataFrame({
        'datetime': dates,
        'close': close,
        'high': close + 2,
        'low': close - 2,
        'volume': np.full(50, 1000)
    })
    df = df.set_index('datetime')
    return df
