import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import pandas as pd
import numpy as np
import datetime
from src.state_manager import StateManager

@pytest.fixture
def sample_market_data():
    """Returns a DataFrame with 100 periods of mock OHLCV data."""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    
    # Create an uptrend
    close = np.linspace(100, 150, 100)
    
    # Add some noise
    np.random.seed(42)
    noise = np.random.normal(0, 1, 100)
    close += noise
    
    df = pd.DataFrame({
        'datetime': dates,
        'open': close - 1,
        'high': close + 2,
        'low': close - 2,
        'close': close,
        'volume': np.random.randint(1000, 5000, 100)
    })
    
    # Set index like the real calculator expects
    df = df.set_index('datetime')
    return df

@pytest.fixture
def empty_state(tmp_path):
    """Returns a StateManager instance pointed at a temp file."""
    state_path = tmp_path / "state.json"
    return StateManager(str(state_path))
