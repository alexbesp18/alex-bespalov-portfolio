import pytest
import pandas as pd
from src.triggers import TriggerEngine

class TestTriggerEngine:
    
    def test_evaluate_basic_score_trigger(self, sample_market_data):
        engine = TriggerEngine()
        
        triggers = [
            {"type": "score_above", "value": 7, "action": "BUY"}
        ]
        
        # Case 1: Score matches
        result = engine.evaluate("TEST", sample_market_data, score=8.0, ticker_triggers=triggers)
        assert len(result) == 1
        assert result[0]['action'] == 'BUY'
        assert result[0]['type'] == 'score_above'
        
        # Case 2: Score too low
        result = engine.evaluate("TEST", sample_market_data, score=6.0, ticker_triggers=triggers)
        assert len(result) == 0

    def test_evaluate_price_cross_ma(self, sample_market_data):
        engine = TriggerEngine()
        df = sample_market_data.copy()
        
        # Create a crossover event at the end
        df['SMA_200'] = 140
        
        # Set last two closes to simulate cross up
        df.iloc[-2, df.columns.get_loc('close')] = 139 # Below
        df.iloc[-1, df.columns.get_loc('close')] = 141 # Above
        
        triggers = [
            {"type": "price_crosses_above_ma", "ma": "SMA_200", "action": "BUY_CROSS"}
        ]
        
        result = engine.evaluate("TEST", df, score=5.0, ticker_triggers=triggers)
        
        assert len(result) == 1
        assert result[0]['action'] == 'BUY_CROSS'
        assert "crossed above SMA_200" in result[0]['detail']

    def test_trigger_deduplication_key(self):
        engine = TriggerEngine()
        trigger = {"type": "score_above", "value": 7, "action": "BUY"}
        
        key1 = engine._trigger_key("AAPL", trigger)
        key2 = engine._trigger_key("AAPL", trigger)
        
        assert key1 == key2
        assert "AAPL_score_above_BUY_7" in key1

    def test_complex_volume_spike_trigger(self, sample_market_data):
        engine = TriggerEngine()
        df = sample_market_data.copy()
        
        # Flatten volume first
        df['volume'] = 1000
        
        # Spike the last one
        df.iloc[-1, df.columns.get_loc('volume')] = 5000
        
        triggers = [
            {"type": "volume_spike", "multiplier": 3.0, "action": "ALERT"}
        ]
        
        result = engine.evaluate("TEST", df, score=5.0, ticker_triggers=triggers)
        
        assert len(result) == 1
        assert result[0]['type'] == 'volume_spike'
