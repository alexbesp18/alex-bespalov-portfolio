"""
Pydantic models for structured LLM responses.

Using structured output models ensures type safety and
catches parsing errors with clear validation messages.
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class TechnicalAnalysisResult(BaseModel):
    """
    Structured response from LLM technical analysis.
    
    Validates all required fields and ensures proper
    numeric ranges for technical indicators.
    """
    technical_score: float = Field(
        ...,
        ge=0,
        le=10,
        description="Overall technical strength score (0=very bearish, 10=very bullish)"
    )
    optimal_entry: float = Field(
        ...,
        gt=0,
        description="Suggested entry price based on technical analysis"
    )
    closest_support: float = Field(
        ...,
        gt=0,
        description="Nearest support level below current price"
    )
    key_support: float = Field(
        ...,
        gt=0,
        description="Major support level (longer timeframe)"
    )
    closest_resistance: float = Field(
        ...,
        gt=0,
        description="Nearest resistance level above current price"
    )
    strongest_resistance: float = Field(
        ...,
        gt=0,
        description="Major resistance level (longer timeframe)"
    )
    reasoning: str = Field(
        ...,
        min_length=10,
        description="Brief 2-3 sentence technical explanation"
    )
    
    @field_validator('technical_score')
    @classmethod
    def validate_score(cls, v: float) -> float:
        """Ensure score is rounded to 1 decimal."""
        return round(v, 1)
    
    @field_validator('optimal_entry', 'closest_support', 'key_support', 
                     'closest_resistance', 'strongest_resistance')
    @classmethod
    def validate_price(cls, v: float) -> float:
        """Ensure prices are rounded to 2 decimals."""
        return round(v, 2)


class ArbitrationResult(TechnicalAnalysisResult):
    """
    Extended result from Claude arbitration.
    
    Includes additional context about the consensus process.
    """
    confidence: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Arbitrator confidence in the consensus (0-1)"
    )


class AnalysisError(BaseModel):
    """Structured error response."""
    success: bool = False
    model: str
    error: str
    cost: float = 0.0
