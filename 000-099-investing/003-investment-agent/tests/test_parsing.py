"""Tests for structured output parsing."""

import pytest

from src.utils.parsing import (
    Company,
    InvestmentOpportunity,
    Theme,
    extract_json_from_text,
    parse_companies_response,
    parse_opportunities_response,
    parse_themes_response,
)


def test_extract_json_from_text_simple():
    """Test extracting JSON from simple text."""
    text = '{"key": "value"}'
    result = extract_json_from_text(text)
    assert result == {"key": "value"}


def test_extract_json_from_text_code_block():
    """Test extracting JSON from markdown code block."""
    text = '```json\n{"key": "value"}\n```'
    result = extract_json_from_text(text)
    assert result == {"key": "value"}


def test_extract_json_from_text_with_extra():
    """Test extracting JSON from text with extra content."""
    text = 'Some text before {"key": "value"} some text after'
    result = extract_json_from_text(text)
    assert result == {"key": "value"}


def test_extract_json_invalid():
    """Test that invalid JSON returns None."""
    text = "This is not JSON at all"
    result = extract_json_from_text(text)
    assert result is None


def test_parse_themes_response(sample_themes_json: str):
    """Test parsing themes from JSON response."""
    themes = parse_themes_response(sample_themes_json)
    assert len(themes) == 2
    assert themes[0].name == "AI Infrastructure"
    assert themes[0].timestamp == "00:02:15"
    assert isinstance(themes[0], Theme)


def test_parse_companies_response(sample_companies_json: str):
    """Test parsing companies from JSON response."""
    companies = parse_companies_response(sample_companies_json)
    assert len(companies) == 2
    assert companies[0].ticker == "NVDA"
    assert companies[0].market_cap == "Large"
    assert isinstance(companies[0], Company)


def test_parse_opportunities_response(sample_opportunities_json: str):
    """Test parsing opportunities from JSON response."""
    opportunities = parse_opportunities_response(sample_opportunities_json)
    assert len(opportunities) == 1
    assert opportunities[0].ticker == "NVDA"
    assert opportunities[0].market_cap == "Large"
    assert isinstance(opportunities[0], InvestmentOpportunity)


def test_parse_invalid_response():
    """Test that invalid response raises ValueError."""
    with pytest.raises(ValueError):
        parse_themes_response("Invalid JSON")


def test_theme_model():
    """Test Theme Pydantic model."""
    theme = Theme(
        name="Test Theme",
        timestamp="00:01:00",
        rationale="Test rationale"
    )
    assert theme.name == "Test Theme"
    assert theme.timestamp == "00:01:00"


def test_company_model():
    """Test Company Pydantic model."""
    company = Company(
        ticker="TEST",
        market_cap="Mid",
        primary_business="Test business",
        theme="Test theme"
    )
    assert company.ticker == "TEST"
    assert company.market_cap == "Mid"


def test_investment_opportunity_model():
    """Test InvestmentOpportunity Pydantic model."""
    opp = InvestmentOpportunity(
        ticker="TEST",
        market_cap="Large",
        earnings_metrics="Test metrics",
        thesis="Test thesis"
    )
    assert opp.ticker == "TEST"
    assert opp.thesis == "Test thesis"


def test_market_cap_validation():
    """Test market cap validation and normalization."""
    # Test normalization (lowercase -> capitalized)
    company = Company(
        ticker="TEST",
        market_cap="small",
        primary_business="Test",
        theme="Test"
    )
    assert company.market_cap == "Small"
    
    # Test invalid market cap
    with pytest.raises(ValueError, match="market_cap must be one of"):
        Company(
            ticker="TEST",
            market_cap="Invalid",
            primary_business="Test",
            theme="Test"
        )


def test_empty_parsing_results():
    """Test that empty parsing results raise appropriate errors."""
    # Empty themes
    with pytest.raises(ValueError, match="No valid themes"):
        parse_themes_response('{"themes": []}')
    
    # Empty companies
    with pytest.raises(ValueError, match="No valid companies"):
        parse_companies_response('{"companies": []}')
    
    # Empty opportunities
    with pytest.raises(ValueError, match="No valid opportunities"):
        parse_opportunities_response('{"opportunities": []}')

