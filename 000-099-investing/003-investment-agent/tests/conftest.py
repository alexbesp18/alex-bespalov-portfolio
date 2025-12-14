"""Pytest configuration and fixtures."""

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.config import Settings


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings with mock API keys."""
    # Use environment variables if set, otherwise use dummy values
    return Settings(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", "sk-ant-test"),
        openai_api_key=os.getenv("OPENAI_API_KEY", "sk-test"),
        xai_api_key=os.getenv("XAI_API_KEY", "xai-test"),
        google_api_key=os.getenv("GOOGLE_API_KEY", "test-key"),
        log_level="DEBUG",
    )


@pytest.fixture
def sample_transcript() -> str:
    """Sample transcript for testing."""
    return """
Investment Podcast Transcript - AI Infrastructure Boom
Episode Date: January 10, 2025

[00:02:15] Host: Welcome back. Today we're diving deep into the AI infrastructure boom.

[00:02:45] Guest: NVIDIA just reported Q4 earnings, and their data center revenue was up 217% year-over-year.

[00:04:12] Host: That's incredible. What about the supporting infrastructure?

[00:04:30] Guest: Vertiv Technologies just reported earnings, and they're seeing similar explosive growth.
"""


@pytest.fixture
def sample_themes_json() -> str:
    """Sample themes JSON response."""
    return """
{
  "themes": [
    {
      "name": "AI Infrastructure",
      "timestamp": "00:02:15",
      "rationale": "Unprecedented growth in data center infrastructure"
    },
    {
      "name": "Semiconductor Equipment",
      "timestamp": "00:04:30",
      "rationale": "Strong demand for advanced logic and memory"
    }
  ]
}
"""


@pytest.fixture
def sample_companies_json() -> str:
    """Sample companies JSON response."""
    return """
{
  "companies": [
    {
      "ticker": "NVDA",
      "market_cap": "Large",
      "primary_business": "AI chips and data center GPUs",
      "theme": "AI Infrastructure"
    },
    {
      "ticker": "VRT",
      "market_cap": "Mid",
      "primary_business": "Data center thermal management",
      "theme": "AI Infrastructure"
    }
  ]
}
"""


@pytest.fixture
def sample_opportunities_json() -> str:
    """Sample opportunities JSON response."""
    return """
{
  "opportunities": [
    {
      "ticker": "NVDA",
      "market_cap": "Large",
      "earnings_metrics": "Q4 revenue up 217% YoY to $18.4B [link]",
      "thesis": "AI chip demand exceeding supply with multi-quarter backlog"
    }
  ]
}
"""


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    mock = MagicMock()
    mock.call_llm.return_value = '{"test": "response"}'
    return mock

