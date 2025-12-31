import pytest
import pandas as pd
import numpy as np
from src.calculator import TechnicalCalculator

class TestTechnicalCalculator:
    
    def test_sma_calculation(self, sample_market_data):
        calc = TechnicalCalculator()
        sma20 = calc.sma(sample_market_data['close'], 20)
        assert len(sma20) == 100
        assert pd.isna(sma20.iloc[18])
        assert not pd.isna(sma20.iloc[19])
        
    def test_process_data_structure(self):
        calc = TechnicalCalculator()
        
        # Mock raw Twelve Data response format
        raw_data = {
            "values": [
                {"datetime": "2024-01-01", "open": 100, "high": 105, "low": 95, "close": 102, "volume": 1000},
                {"datetime": "2024-01-02", "open": 102, "high": 107, "low": 100, "close": 105, "volume": 1200}
            ]
        }
        
        df = calc.process_data(raw_data)
        
        assert isinstance(df, pd.DataFrame)
        assert 'SMA_20' in df.columns
        assert 'RSI' in df.columns
        assert 'MACD_HIST' in df.columns
        
    def test_calculate_bullish_score_insufficient_data(self):
        calc = TechnicalCalculator()
        df = pd.DataFrame({'close': range(10)}) # Too short
        score, breakdown = calc.calculate_bullish_score(df)
        assert score == 0
        assert breakdown == {}
        
    def test_calculate_bullish_score_uptrend(self, sample_market_data):
        calc = TechnicalCalculator()
        
        # Ensure indicators are present (simulate process_data)
        df = sample_market_data.copy()
        df['SMA_20'] = df['close'].rolling(20).mean()
        df['SMA_50'] = df['close'].rolling(50).mean()
        df['SMA_200'] = df['close'].rolling(200).min() # Mock low 200 SMA to simulate uptrend
        
        # Mock other requirements
        df['MACD_HIST'] = 1.0 
        df['RSI'] = 60
        df['ADX'] = 30
        df['OBV'] = np.linspace(1000, 2000, 100)
        
        score, breakdown = calc.calculate_bullish_score(df)
        
        # Expect reasonably high score due to uptrend setup
        assert score > 5
        assert 'trend' in breakdown
        assert 'rsi' in breakdown
        
    def test_calculate_matrix(self, sample_market_data):
        calc = TechnicalCalculator()
        df = sample_market_data.copy()
        
        # Manually add some indicators
        df['SMA_50'] = 100
        df['SMA_200'] = 90
        
        matrix = calc.calculate_matrix(df)
        
        assert '_price' in matrix
        assert 'golden_cross' in matrix
        assert 'rsi_above_70' in matrix
        assert isinstance(matrix['golden_cross'], int)
