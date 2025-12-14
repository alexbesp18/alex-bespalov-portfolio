"""Structured output parsing utilities."""

import json
import logging
import re
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator

logger = logging.getLogger(__name__)


class Theme(BaseModel):
    """Investment theme model."""
    
    name: str = Field(..., description="Theme name")
    timestamp: str | None = Field(None, description="Timestamp if available")
    rationale: str = Field(..., description="Rationale for theme")


class Company(BaseModel):
    """Company model."""
    
    ticker: str = Field(..., description="Stock ticker symbol", min_length=1, max_length=10)
    market_cap: str = Field(..., description="Market cap size: Small, Mid, or Large")
    primary_business: str = Field(..., description="Primary business line", min_length=1)
    theme: str = Field(..., description="Associated investment theme", min_length=1)
    
    @field_validator("market_cap")
    @classmethod
    def validate_market_cap(cls, v: str) -> str:
        """Validate market cap is one of allowed values."""
        allowed = {"Small", "Mid", "Large", "small", "mid", "large"}
        if v not in allowed:
            raise ValueError(f"market_cap must be one of {allowed}, got '{v}'")
        return v.capitalize()  # Normalize to capitalized


class InvestmentOpportunity(BaseModel):
    """Investment opportunity model."""
    
    ticker: str = Field(..., description="Stock ticker symbol", min_length=1, max_length=10)
    market_cap: str = Field(..., description="Market cap size: Small, Mid, or Large")
    earnings_metrics: str = Field(..., description="Key earnings metrics with dates and links", min_length=1)
    thesis: str = Field(..., description="One sentence investment thesis", min_length=1)
    
    @field_validator("market_cap")
    @classmethod
    def validate_market_cap(cls, v: str) -> str:
        """Validate market cap is one of allowed values."""
        allowed = {"Small", "Mid", "Large", "small", "mid", "large"}
        if v not in allowed:
            raise ValueError(f"market_cap must be one of {allowed}, got '{v}'")
        return v.capitalize()  # Normalize to capitalized


def extract_json_from_text(text: str) -> dict[str, Any] | None:
    """Extract JSON from text that may contain markdown or other formatting.
    
    Args:
        text: Text that may contain JSON
        
    Returns:
        Parsed JSON dictionary or None if extraction fails
    """
    if not text or not text.strip():
        logger.warning("Empty text provided for JSON extraction")
        return None
    
    # Try to find JSON code block (most common format)
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError as e:
            logger.debug(f"Failed to parse JSON code block: {e}")
    
    # Try to find JSON object directly (balanced braces)
    # Use a more robust pattern that finds the outermost JSON object
    brace_count = 0
    start_idx = -1
    for i, char in enumerate(text):
        if char == '{':
            if brace_count == 0:
                start_idx = i
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0 and start_idx != -1:
                try:
                    return json.loads(text[start_idx:i+1])
                except json.JSONDecodeError:
                    continue
    
    # Try parsing entire text as JSON (fallback)
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        logger.debug("Failed to parse text as JSON")
        return None


def parse_themes_response(response: str) -> list[Theme]:
    """Parse themes from LLM response.
    
    Args:
        response: LLM response text
        
    Returns:
        List of Theme objects
        
    Raises:
        ValueError: If parsing fails
    """
    data = extract_json_from_text(response)
    if not data or "themes" not in data:
        raise ValueError("Invalid themes response format")
    
    themes = []
    for i, theme_data in enumerate(data["themes"]):
        try:
            themes.append(Theme(**theme_data))
        except ValidationError as e:
            logger.warning(f"Failed to parse theme {i+1}: {e}. Skipping.")
            continue
    
    if not themes:
        raise ValueError("No valid themes found in response after parsing")
    
    return themes


def parse_companies_response(response: str) -> list[Company]:
    """Parse companies from LLM response.
    
    Args:
        response: LLM response text
        
    Returns:
        List of Company objects
        
    Raises:
        ValueError: If parsing fails
    """
    data = extract_json_from_text(response)
    if not data or "companies" not in data:
        raise ValueError("Invalid companies response format")
    
    companies = []
    for i, company_data in enumerate(data["companies"]):
        try:
            companies.append(Company(**company_data))
        except ValidationError as e:
            logger.warning(f"Failed to parse company {i+1}: {e}. Skipping.")
            continue
    
    if not companies:
        raise ValueError("No valid companies found in response after parsing")
    
    return companies


def parse_opportunities_response(response: str) -> list[InvestmentOpportunity]:
    """Parse investment opportunities from LLM response.
    
    Args:
        response: LLM response text
        
    Returns:
        List of InvestmentOpportunity objects
        
    Raises:
        ValueError: If parsing fails
    """
    data = extract_json_from_text(response)
    if not data or "opportunities" not in data:
        raise ValueError("Invalid opportunities response format")
    
    opportunities = []
    for i, opp_data in enumerate(data["opportunities"]):
        try:
            opportunities.append(InvestmentOpportunity(**opp_data))
        except ValidationError as e:
            logger.warning(f"Failed to parse opportunity {i+1}: {e}. Skipping.")
            continue
    
    if not opportunities:
        raise ValueError("No valid opportunities found in response after parsing")
    
    return opportunities

