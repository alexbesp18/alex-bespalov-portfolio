"""Tests for LLM client integration with Shared Core."""

from unittest.mock import MagicMock, patch

import pytest

from src.config import Settings
from src.llm.client import LLMClient


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    return Settings(
        anthropic_api_key="sk-ant-test",
        openai_api_key="sk-test",
        xai_api_key="xai-test",
        google_api_key="test-key",
    )


def test_llm_client_initialization_claude(mock_settings):
    """Test LLM client initialization checks for API key."""
    provider_settings = {
        "model": "sonnet-4.5",
        "max_tokens": 64000,
    }
    
    with patch("src.llm.client.SharedLLMClient") as MockSharedClient:
        client = LLMClient(mock_settings, "claude", provider_settings)
        
        # Verify SharedLLMClient was initialized with correct args
        MockSharedClient.assert_called_once()
        args, _ = MockSharedClient.call_args
        assert args[0] == "claude"
        assert args[1] == "sk-ant-test"
        assert args[2] == provider_settings


def test_llm_client_call_delegation(mock_settings):
    """Test that call_llm delegates to SharedLLMClient."""
    provider_settings = {"model": "gpt-4"}
    
    with patch("src.llm.client.SharedLLMClient") as MockSharedClient:
        mock_instance = MockSharedClient.return_value
        mock_instance.call_llm.return_value = "Response"
        
        client = LLMClient(mock_settings, "openai", provider_settings)
        result = client.call_llm("Prompt", max_tokens=100)
        
        assert result == "Response"
        mock_instance.call_llm.assert_called_once_with("Prompt", max_tokens=100, stream=False)
