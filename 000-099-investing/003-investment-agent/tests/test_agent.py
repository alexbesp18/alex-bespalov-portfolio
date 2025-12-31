"""Integration tests for investment agent."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.agent.investment_agent import InvestmentAgent
from src.config import Settings


@pytest.fixture
def test_input_file(tmp_path: Path, sample_transcript: str) -> Path:
    """Create a temporary input file."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    input_file = input_dir / "test_transcript.txt"
    input_file.write_text(sample_transcript)
    return input_file


def test_agent_initialization(test_settings: Settings):
    """Test agent initialization."""
    agent = InvestmentAgent(test_settings)
    assert agent.settings == test_settings
    assert agent.llm_client is None


def test_load_prompt():
    """Test loading prompt from file."""
    settings = Settings(
        anthropic_api_key="sk-ant-test",
        openai_api_key="sk-test",
        xai_api_key="xai-test",
        google_api_key="test-key",
    )
    agent = InvestmentAgent(settings)
    
    prompt = agent._load_prompt("theme_extraction")
    assert "transcript" in prompt
    assert len(prompt) > 0


def test_read_input_file(test_settings: Settings, test_input_file: Path):
    """Test reading input file."""
    agent = InvestmentAgent(test_settings)
    agent.settings.input_folder = test_input_file.parent
    
    content = agent.read_input_file()
    assert len(content) > 0
    assert "Investment Podcast" in content


def test_read_input_file_not_found(test_settings: Settings):
    """Test reading input file when folder doesn't exist."""
    agent = InvestmentAgent(test_settings)
    agent.settings.input_folder = Path("/nonexistent/path")
    
    with pytest.raises(FileNotFoundError):
        agent.read_input_file()


def test_model_mapping():
    """Test model name mapping."""
    settings = Settings(
        anthropic_api_key="sk-ant-test",
        openai_api_key="sk-test",
        xai_api_key="xai-test",
        google_api_key="test-key",
    )
    agent = InvestmentAgent(settings)
    
    assert agent._get_model_mapping("claude", "sonnet-4.5") == "claude-sonnet-4-20250514"
    assert agent._get_model_mapping("openai", "gpt-4") == "gpt-4"
    assert agent._get_model_mapping("grok", "grok-4") == "grok-4"


def test_save_output(test_settings: Settings, tmp_path: Path):
    """Test saving output to file."""
    agent = InvestmentAgent(test_settings)
    agent.provider = "claude"
    agent.settings.output_folder = tmp_path / "output"
    
    output_path = agent.save_output(
        step1="Theme 1: AI Infrastructure",
        step2="Company 1: NVDA",
        step3="Opportunity 1: NVDA - Strong growth"
    )
    
    assert output_path.exists()
    content = output_path.read_text()
    assert "INVESTMENT ANALYSIS REPORT" in content
    assert "Theme 1: AI Infrastructure" in content


def test_print_company_summary(test_settings: Settings, sample_opportunities_json: str):
    """Test printing company summary."""
    from src.utils.parsing import parse_opportunities_response
    
    agent = InvestmentAgent(test_settings)
    opportunities = parse_opportunities_response(sample_opportunities_json)
    
    # Should not raise exception
    agent.print_company_summary(opportunities[0])


def test_extract_console_summary(test_settings: Settings, sample_opportunities_json: str):
    """Test extracting console summary from structured output."""
    agent = InvestmentAgent(test_settings)
    
    # Should not raise exception
    agent.extract_console_summary(sample_opportunities_json)

