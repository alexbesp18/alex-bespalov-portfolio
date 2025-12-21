"""Unit tests for the oversold scorer module."""

import pandas as pd
import pytest
from src.oversold_scorer import (
    OversoldScorer,
    score_rsi,
    score_williams_r,
    score_stochastic,
    score_sma200_distance,
    score_consecutive_red,
)


class TestScoreRSI:
    """Tests for RSI scoring function."""
    
    def test_extremely_oversold(self):
        """RSI below 15 should score 10."""
        assert score_rsi(10.0) == 10.0
        assert score_rsi(14.9) == 10.0
    
    def test_very_oversold(self):
        """RSI 15-20 should score 9."""
        assert score_rsi(15.0) == 9.0
        assert score_rsi(19.9) == 9.0
    
    def test_oversold(self):
        """RSI 25-30 should score 6."""
        assert score_rsi(25.0) == 6.0
        assert score_rsi(29.9) == 6.0
    
    def test_neutral(self):
        """RSI above 50 should score 1."""
        assert score_rsi(50.0) == 1.0
        assert score_rsi(70.0) == 1.0
    
    def test_nan_handling(self):
        """NaN should return 0."""
        assert score_rsi(float('nan')) == 0.0


class TestScoreWilliamsR:
    """Tests for Williams %R scoring function."""
    
    def test_extremely_oversold(self):
        """Williams %R below -95 should score 10."""
        assert score_williams_r(-98.0) == 10.0
        assert score_williams_r(-95.1) == 10.0
    
    def test_oversold(self):
        """Williams %R -85 to -80 should score 4."""
        assert score_williams_r(-82.0) == 4.0
    
    def test_neutral(self):
        """Williams %R above -70 should score 1."""
        assert score_williams_r(-50.0) == 1.0
        assert score_williams_r(-20.0) == 1.0
    
    def test_nan_handling(self):
        """NaN should return 0."""
        assert score_williams_r(float('nan')) == 0.0


class TestScoreStochastic:
    """Tests for Stochastic %K scoring function."""
    
    def test_extremely_oversold(self):
        """Stoch %K below 5 should score 10."""
        assert score_stochastic(3.0) == 10.0
    
    def test_oversold(self):
        """Stoch %K 15-20 should score 5."""
        assert score_stochastic(18.0) == 5.0
    
    def test_neutral(self):
        """Stoch %K above 30 should score 1."""
        assert score_stochastic(50.0) == 1.0


class TestScoreSMA200Distance:
    """Tests for SMA200 distance scoring."""
    
    def test_significantly_below(self):
        """Price 30%+ below SMA200 should score 10."""
        # 65 is 35% below 100, which is > 30%
        assert score_sma200_distance(65.0, 100.0) == 10.0
    
    def test_moderately_below(self):
        """Price 10-15% below SMA200 should score based on thresholds."""
        # 85 is 15% below 100, which triggers pct_below > 10 → score 5
        assert score_sma200_distance(85.0, 100.0) == 5.0
    
    def test_above_sma(self):
        """Price above SMA200 should score 1."""
        assert score_sma200_distance(110.0, 100.0) == 1.0


class TestScoreConsecutiveRed:
    """Tests for consecutive red days scoring."""
    
    def test_many_red_days(self):
        """7+ consecutive red days should score 10."""
        df = pd.DataFrame({
            'close': [100, 99, 98, 97, 96, 95, 94, 93, 92]
        })
        assert score_consecutive_red(df) == 10.0
    
    def test_few_red_days(self):
        """3 consecutive red days should score 3."""
        df = pd.DataFrame({
            'close': [100, 101, 100, 99, 98]  # Last 3 are down
        })
        assert score_consecutive_red(df) == 3.0
    
    def test_no_red_days(self):
        """0 consecutive red days should score 1."""
        df = pd.DataFrame({
            'close': [100, 101, 102, 103]
        })
        assert score_consecutive_red(df) == 1.0
    
    def test_empty_df(self):
        """Empty DataFrame should return 0."""
        assert score_consecutive_red(None) == 0.0
        assert score_consecutive_red(pd.DataFrame({'close': [100]})) == 0.0


class TestOversoldScorer:
    """Integration tests for the OversoldScorer class."""
    
    def test_score_returns_oversold_score(self):
        """Scorer should return OversoldScore dataclass."""
        scorer = OversoldScorer()
        
        # Create a mock DataFrame with oversold indicators
        df = pd.DataFrame({
            'close': [100] * 50 + [80],  # 51 rows needed
            'RSI': [50] * 50 + [20],
            'WILLIAMS_R': [-50] * 50 + [-90],
            'STOCH_K': [50] * 50 + [10],
            'BB_LOWER': [90] * 51,
            'BB_MIDDLE': [100] * 51,
            'SMA_200': [100] * 51,
        })
        
        result = scorer.score(df)
        
        assert hasattr(result, 'final_score')
        assert hasattr(result, 'components')
        assert hasattr(result, 'raw_values')
        assert 1.0 <= result.final_score <= 10.0
    
    def test_score_with_insufficient_data(self):
        """Scorer should return 0 for insufficient data."""
        scorer = OversoldScorer()
        
        # Only 10 rows - not enough
        df = pd.DataFrame({'close': [100] * 10})
        result = scorer.score(df)
        
        assert result.final_score == 0.0
    
    def test_custom_weights(self):
        """Scorer should accept custom weights."""
        custom_weights = {
            "rsi": 1.0,  # 100% weight on RSI
            "williams_r": 0.0,
            "stochastic": 0.0,
            "bollinger": 0.0,
            "sma200_distance": 0.0,
            "consecutive_red": 0.0,
        }
        
        scorer = OversoldScorer(weights=custom_weights)
        assert scorer.weights["rsi"] == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
