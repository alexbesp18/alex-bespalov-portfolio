
import pytest
from unittest.mock import MagicMock, patch
from shared_core.llm.client import LLMClient

@pytest.fixture
def mock_anthropic():
    with patch("anthropic.Anthropic") as mock:
        yield mock

@pytest.fixture
def mock_openai():
    with patch("openai.OpenAI") as mock:
        yield mock

def test_initialization_claude(mock_anthropic):
    settings = {"model": "sonnet-4.5"}
    client = LLMClient("claude", "test-key", settings)
    
    mock_anthropic.assert_called_once_with(api_key="test-key")
    assert client.model_name == "claude-sonnet-4-20250514"

def test_initialization_openai(mock_openai):
    settings = {"model": "gpt-4"}
    client = LLMClient("openai", "test-key", settings)
    
    mock_openai.assert_called_once_with(api_key="test-key")
    assert client.model_name == "gpt-4"

def test_initialization_unknown_provider():
    with pytest.raises(ValueError, match="Unknown provider"):
        LLMClient("unknown", "test-key", {})

def test_call_claude(mock_anthropic):
    # Setup mock response
    mock_instance = mock_anthropic.return_value
    mock_response = MagicMock()
    mock_block = MagicMock()
    mock_block.text = "Hello Claude"
    mock_response.content = [mock_block]
    mock_instance.messages.create.return_value = mock_response

    client = LLMClient("claude", "test-key", {"model": "sonnet-4.5"})
    response = client.call_llm("Hi")
    
    assert response == "Hello Claude"
    mock_instance.messages.create.assert_called_once()

def test_call_with_system_message(mock_anthropic):
    # Setup mock
    mock_instance = mock_anthropic.return_value
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Response")]
    mock_instance.messages.create.return_value = mock_response
    
    client = LLMClient("claude", "test-key", {"model": "sonnet-4.5"})
    client.call_llm("Prompt", system_message="System")
    
    # Check if system arg was passed
    call_args = mock_instance.messages.create.call_args[1]
    assert call_args["system"] == "System"
    assert call_args["messages"][0]["content"] == "Prompt"
