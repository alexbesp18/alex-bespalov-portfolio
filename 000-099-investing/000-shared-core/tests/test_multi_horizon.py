"""
Tests for Multi-Horizon Technical Analysis Calculator.
"""

import pandas as pd
import numpy as np
import pytest
from datetime import datetime, timedelta

from shared_core.scoring.multi_horizon import (
    MultiHorizonCalculator,
    TimeHorizon,
    HORIZON_CONFIGS,
)


@pytest.fixture
def sample_df():
    """Create sample OHLCV DataFrame for testing."""
    dates = pd.date_range(end=datetime.now(), periods=300, freq='D')
    np.random.seed(42)

    # Generate realistic price data with trend
    base_price = 100
    returns = np.random.randn(300) * 0.02
    prices = base_price * np.cumprod(1 + returns)

    df = pd.DataFrame({
        'datetime': dates,
        'open': prices * (1 + np.random.randn(300) * 0.005),
        'high': prices * (1 + np.abs(np.random.randn(300) * 0.01)),
        'low': prices * (1 - np.abs(np.random.randn(300) * 0.01)),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, 300),
    })
    return df


@pytest.fixture
def oversold_df():
    """Create DataFrame with oversold conditions."""
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')

    # Declining prices (oversold)
    prices = np.linspace(150, 80, 100)

    df = pd.DataFrame({
        'datetime': dates,
        'open': prices * 1.01,
        'high': prices * 1.02,
        'low': prices * 0.99,
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, 100),
    })
    return df


@pytest.fixture
def uptrend_df():
    """Create DataFrame with strong uptrend."""
    dates = pd.date_range(end=datetime.now(), periods=200, freq='D')

    # Rising prices (uptrend)
    prices = np.linspace(50, 150, 200) + np.random.randn(200) * 2

    df = pd.DataFrame({
        'datetime': dates,
        'open': prices * 0.99,
        'high': prices * 1.02,
        'low': prices * 0.98,
        'close': prices,
        'volume': np.linspace(1000000, 3000000, 200).astype(int),  # Rising volume
    })
    return df


class TestHorizonConfigs:
    """Test time horizon configurations."""

    def test_all_horizons_defined(self):
        """Verify all three horizons have configs."""
        assert TimeHorizon.SHORT_TERM in HORIZON_CONFIGS
        assert TimeHorizon.MID_TERM in HORIZON_CONFIGS
        assert TimeHorizon.LONG_TERM in HORIZON_CONFIGS

    def test_short_term_periods_smaller(self):
        """Short-term should use smaller periods."""
        st = HORIZON_CONFIGS[TimeHorizon.SHORT_TERM]
        mt = HORIZON_CONFIGS[TimeHorizon.MID_TERM]
        lt = HORIZON_CONFIGS[TimeHorizon.LONG_TERM]

        assert st.rsi_period < mt.rsi_period < lt.rsi_period
        assert st.adx_period < mt.adx_period < lt.adx_period
        assert st.vol_avg_period < mt.vol_avg_period < lt.vol_avg_period


class TestMultiHorizonCalculator:
    """Test the main calculator."""

    def test_initialization(self):
        """Test calculator initializes correctly."""
        calc = MultiHorizonCalculator()
        assert calc.calc is not None

    def test_calculate_all_returns_all_columns(self, sample_df):
        """Verify all expected columns are returned."""
        calc = MultiHorizonCalculator()
        result = calc.calculate_all(sample_df)

        # Base columns
        assert 'Price' in result
        assert 'Change%' in result

        # Short-term columns
        assert 'ST_RSI_7' in result
        assert 'ST_Stoch_K' in result
        assert 'ST_MACD_Hist' in result
        assert 'ST_Price_vs_EMA10' in result
        assert 'ST_Vol_Ratio_5d' in result

        # Mid-term columns
        assert 'MT_RSI_14' in result
        assert 'MT_MACD_Hist' in result
        assert 'MT_Price_vs_SMA50' in result
        assert 'MT_ADX' in result
        assert 'MT_Divergence' in result
        assert 'MT_Vol_Trend_20d' in result
        assert 'MT_Reversal_Score' in result
        assert 'MT_Entry_Score' in result
        assert 'MT_Conviction' in result

        # Long-term columns
        assert 'LT_RSI_21' in result
        assert 'LT_MACD_Hist' in result
        assert 'LT_Price_vs_SMA200' in result
        assert 'LT_SMA50_vs_SMA200' in result
        assert 'LT_ADX_21' in result
        assert 'LT_OBV_Trend_50d' in result
        assert 'LT_52W_Position' in result
        assert 'LT_Trend' in result
        assert 'LT_Months_in_Trend' in result
        assert 'LT_Score' in result

    def test_rsi_values_in_range(self, sample_df):
        """RSI values should be between 0 and 100."""
        calc = MultiHorizonCalculator()
        result = calc.calculate_all(sample_df)

        assert 0 <= result['ST_RSI_7'] <= 100
        assert 0 <= result['MT_RSI_14'] <= 100
        assert 0 <= result['LT_RSI_21'] <= 100

    def test_scores_in_range(self, sample_df):
        """Scores should be between 1 and 10."""
        calc = MultiHorizonCalculator()
        result = calc.calculate_all(sample_df)

        assert 1.0 <= result['MT_Reversal_Score'] <= 10.0
        assert 1.0 <= result['MT_Entry_Score'] <= 10.0
        assert 1.0 <= result['LT_Score'] <= 10.0

    def test_52w_position_in_range(self, sample_df):
        """52-week position should be between 0% and 100%."""
        calc = MultiHorizonCalculator()
        result = calc.calculate_all(sample_df)

        # Extract numeric value from string like "45%"
        position = float(result['LT_52W_Position'].rstrip('%'))
        assert 0 <= position <= 100


class TestOversoldConditions:
    """Test detection of oversold conditions."""

    def test_low_rsi_detected(self, oversold_df):
        """Verify low RSI is detected in oversold conditions."""
        calc = MultiHorizonCalculator()
        result = calc.calculate_all(oversold_df)

        # In a strong downtrend, RSI should be low
        assert result['MT_RSI_14'] < 40

    def test_higher_reversal_score_when_oversold(self, oversold_df, uptrend_df):
        """Reversal score should be higher for oversold stocks."""
        calc = MultiHorizonCalculator()

        oversold_result = calc.calculate_all(oversold_df)
        uptrend_result = calc.calculate_all(uptrend_df)

        # Oversold stock should have higher reversal score
        assert oversold_result['MT_Reversal_Score'] >= uptrend_result['MT_Reversal_Score']


class TestUptrendConditions:
    """Test detection of uptrend conditions."""

    def test_positive_trend_indicators(self, uptrend_df):
        """Verify positive trend is detected."""
        calc = MultiHorizonCalculator()
        result = calc.calculate_all(uptrend_df)

        # Long-term trend should be uptrend or strong uptrend
        assert result['LT_Trend'] in ['UPTREND', 'STRONG_UPTREND']

    def test_higher_lt_score_in_uptrend(self, uptrend_df, oversold_df):
        """Long-term score should be higher in uptrend."""
        calc = MultiHorizonCalculator()

        uptrend_result = calc.calculate_all(uptrend_df)
        oversold_result = calc.calculate_all(oversold_df)

        # Uptrend should have higher LT score
        assert uptrend_result['LT_Score'] > oversold_result['LT_Score']


class TestDivergenceDetection:
    """Test divergence detection."""

    def test_divergence_values(self, sample_df):
        """Verify divergence returns valid values."""
        calc = MultiHorizonCalculator()
        result = calc.calculate_all(sample_df)

        valid_divergences = [
            'NONE', 'BULLISH', 'BEARISH',
            'STRONG_BULLISH', 'STRONG_BEARISH'
        ]
        assert result['MT_Divergence'] in valid_divergences


class TestConvictionLevels:
    """Test conviction level assignment."""

    def test_conviction_values(self, sample_df):
        """Verify conviction returns valid values."""
        calc = MultiHorizonCalculator()
        result = calc.calculate_all(sample_df)

        valid_convictions = ['HIGH', 'MEDIUM', 'LOW', 'NONE']
        assert result['MT_Conviction'] in valid_convictions


class TestEntryScore:
    """Test entry score calculation."""

    def test_entry_score_considers_trend_position(self, uptrend_df):
        """Entry score should factor in trend position."""
        calc = MultiHorizonCalculator()
        result = calc.calculate_all(uptrend_df)

        # In uptrend, entry score should be reasonable
        assert result['MT_Entry_Score'] >= 4.0

    def test_entry_score_different_from_reversal(self, sample_df):
        """Entry score can differ from reversal score."""
        calc = MultiHorizonCalculator()
        result = calc.calculate_all(sample_df)

        # They measure different things, so may differ
        # Just verify they're both valid scores
        assert 1.0 <= result['MT_Entry_Score'] <= 10.0
        assert 1.0 <= result['MT_Reversal_Score'] <= 10.0


class TestInsufficientData:
    """Test handling of insufficient data."""

    def test_empty_result_for_short_df(self):
        """Should return empty result for insufficient data."""
        calc = MultiHorizonCalculator()

        short_df = pd.DataFrame({
            'datetime': pd.date_range('2024-01-01', periods=10),
            'open': [100] * 10,
            'high': [101] * 10,
            'low': [99] * 10,
            'close': [100] * 10,
            'volume': [1000000] * 10,
        })

        result = calc.calculate_all(short_df)

        # Should return defaults
        assert result['Price'] == 0.0
        assert result['MT_Conviction'] == 'NONE'

    def test_handles_none_df(self):
        """Should handle None DataFrame."""
        calc = MultiHorizonCalculator()
        result = calc.calculate_all(None)

        assert result['Price'] == 0.0
        assert result['MT_Entry_Score'] == 5.0


class TestMAClassification:
    """Test moving average cross classification."""

    def test_valid_ma_cross_values(self, sample_df):
        """MA cross should return valid classification."""
        calc = MultiHorizonCalculator()
        result = calc.calculate_all(sample_df)

        valid_crosses = [
            'GOLDEN_CROSS', 'DEATH_CROSS',
            'BULLISH', 'BEARISH', 'NEUTRAL'
        ]
        assert result['LT_SMA50_vs_SMA200'] in valid_crosses


class TestVolumeTrend:
    """Test volume trend classification."""

    def test_valid_volume_trend_values(self, sample_df):
        """Volume trend should return valid classification."""
        calc = MultiHorizonCalculator()
        result = calc.calculate_all(sample_df)

        valid_trends = ['ACCUMULATING', 'DISTRIBUTING', 'NEUTRAL']
        assert result['MT_Vol_Trend_20d'] in valid_trends
        assert result['LT_OBV_Trend_50d'] in valid_trends
