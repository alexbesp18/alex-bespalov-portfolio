import pytest
import pandas as pd
from src.triggers import TriggerEngine

class TestTriggersReversal:
    
    def test_upside_reversal_trigger(self, sample_market_data):
        engine = TriggerEngine()
        
        triggers = [
            {"type": "upside_reversal_score", "threshold": 7, "action": "BUY_REV"}
        ]
        
        # Matrix must have the score
        matrix = {"upside_rev_score": 8.0}
        
        result = engine.evaluate("TEST", sample_market_data, score=0, ticker_triggers=triggers, matrix=matrix)
        
        assert len(result) == 1
        assert result[0]['action'] == 'BUY_REV'
        assert "Upside Rev Score 8.0 >= 7" in result[0]['detail']

    def test_macd_flip_trigger(self, sample_market_data):
        engine = TriggerEngine()
        df = sample_market_data.copy()
        
        # Create flip
        df['MACD_HIST'] = 0
        # Prev (-2) was negative, Curr (-1) is positive
        df.iloc[-2, df.columns.get_loc('MACD_HIST')] = -0.5
        df.iloc[-1, df.columns.get_loc('MACD_HIST')] = 0.5
        
        triggers = [
            {"type": "macd_histogram_flip_positive", "action": "ALERT"}
        ]
        
        result = engine.evaluate("TEST", df, score=0, ticker_triggers=triggers)
        
        assert len(result) == 1
        assert "flipped positive" in result[0]['detail']
