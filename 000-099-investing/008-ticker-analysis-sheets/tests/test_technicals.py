import pandas as pd
import numpy as np
from src.analysis.technical import TechnicalCalculator

def test_sma():
    data = pd.Series([1, 2, 3, 4, 5])
    sma = TechnicalCalculator.sma(data, 3)
    # [NaN, NaN, 2, 3, 4]
    assert np.isnan(sma.iloc[0])
    assert sma.iloc[2] == 2.0
    assert sma.iloc[4] == 4.0

def test_rsi():
    # Simple increasing sequence (RSI should be 100 or high)
    data = pd.Series(range(20))
    # We need enough data for the period (14)
    # Gains: 1, 1, 1... 
    # Avg Gain = 1, Avg Loss = 0 -> RS = inf -> RSI = 100
    rsi = TechnicalCalculator.rsi(data, 14)
    assert rsi.iloc[-1] == 100.0

def test_rsi_flat():
    data = pd.Series([10] * 20)
    rsi = TechnicalCalculator.rsi(data, 14)
    # No gains, no losses?
    # Delta is 0.
    # Gain=0, Loss=0. 0/0 -> NaN usually or handled.
    # Original code: rs = gain / loss.replace(0, np.nan)
    # If loss is 0, rs is NaN.
    # rsi = 100 - (100 / (1 + nan)) -> nan
    assert np.isnan(rsi.iloc[-1])
