"""
Technical calculator for 008-alerts.

This module is now a thin wrapper around shared_core functionality.
The shared_core.data module provides:
- process_ohlcv_data() for DataFrame creation with indicators
- calculate_bullish_score() for scoring
- calculate_matrix() for binary flags
"""

from shared_core import TechnicalCalculator as SharedTechnicalCalculator
from shared_core.data import (
    process_ohlcv_data,
    calculate_bullish_score,
    calculate_matrix,
)


class TechnicalCalculator(SharedTechnicalCalculator):
    """
    Technical calculator extending shared_core with alert-specific processing.
    
    Most methods are now delegated to shared_core.data module.
    This class is kept for backward compatibility.
    """
    
    def __init__(self):
        super().__init__()

    def process_data(self, time_series_data):
        """
        Takes raw Twelve Data time series and returns a DataFrame with indicators.
        Delegates to shared_core.data.process_ohlcv_data.
        """
        return process_ohlcv_data(time_series_data, include_indicators=True)

    def calculate_bullish_score(self, df):
        """
        Computes 1-10 bullish score based on the latest row.
        Delegates to shared_core.data.calculate_bullish_score.
        """
        return calculate_bullish_score(df)

    def calculate_matrix(self, df) -> dict:
        """
        Generates a dictionary of binary flags for matrix/dashboard output.
        Delegates to shared_core.data.calculate_matrix.
        """
        return calculate_matrix(df)

