"""Tests for Grok integration."""
from unittest.mock import MagicMock, patch
import pytest
from src.llm.grok import GrokSummarizer

def test_grok_initialization():
    """Test GrokSummarizer initializes SharedLLMClient."""
    with patch("src.llm.grok.SharedLLMClient") as MockShared:
        client = GrokSummarizer("test-key")
        MockShared.assert_called_once()
        args, kwargs = MockShared.call_args
        assert args[0] == "grok"
        assert args[1] == "test-key"

def test_grok_summarize_delegation():
    """Test summarize calls SharedLLMClient."""
    with patch("src.llm.grok.SharedLLMClient") as MockShared:
        instance = MockShared.return_value
        instance.call_llm.return_value = "Summary: Test"
        
        client = GrokSummarizer("test-key")
        # Text must be > 500 chars to trigger LLM
        long_text = "test " * 200 
        result = client.summarize("AAPL", "Q1", long_text)
        
        assert result['Summary'] == "Test"
        instance.call_llm.assert_called_once()

def test_grok_technicals_delegation():
    """Test analyze_technicals calls SharedLLMClient with JSON instruction."""
    with patch("src.llm.grok.SharedLLMClient") as MockShared:
        instance = MockShared.return_value
        instance.call_llm.return_value = '{"Bullish_Score": 8, "Bullish_Reason": "Good"}'
        
        client = GrokSummarizer("test-key")
        result = client.analyze_technicals("AAPL", {"RSI": 50})
        
        assert result['Bullish_Score'] == 8
        instance.call_llm.assert_called_once()
        # Verify system message requested JSON
        call_args = instance.call_llm.call_args
        assert "valid JSON" in call_args.kwargs['system_message']
