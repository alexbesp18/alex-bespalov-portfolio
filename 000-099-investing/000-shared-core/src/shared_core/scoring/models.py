"""
Data models for scoring results.

Provides structured output from scoring functions.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional


class DivergenceType(Enum):
    """Type of divergence detected between price and indicator."""
    NONE = "none"
    BULLISH = "bullish"
    BEARISH = "bearish"


@dataclass
class DivergenceResult:
    """
    Result from divergence detection.

    Attributes:
        type: Type of divergence (NONE, BULLISH, BEARISH)
        strength: Magnitude of the divergence (higher = stronger signal)
        description: Human-readable description of the divergence
    """
    type: DivergenceType
    strength: float
    description: str

    @classmethod
    def none(cls, reason: str = "No divergence detected") -> "DivergenceResult":
        """Create a no-divergence result."""
        return cls(DivergenceType.NONE, 0.0, reason)

    @classmethod
    def bullish(cls, strength: float, description: str) -> "DivergenceResult":
        """Create a bullish divergence result."""
        return cls(DivergenceType.BULLISH, strength, description)

    @classmethod
    def bearish(cls, strength: float, description: str) -> "DivergenceResult":
        """Create a bearish divergence result."""
        return cls(DivergenceType.BEARISH, strength, description)


@dataclass
class ReversalScore:
    """
    Result from reversal scoring calculation.

    Attributes:
        raw_score: Score before multipliers (1-10 scale)
        final_score: Score after volume and ADX multipliers
        volume_multiplier: Applied volume adjustment (0.75-1.1)
        adx_multiplier: Applied ADX regime adjustment (0.85-1.1)
        components: Individual indicator scores before weighting
        divergence: Detected divergence (if any)
    """
    raw_score: float
    final_score: float
    volume_multiplier: float
    adx_multiplier: float
    components: Dict[str, float] = field(default_factory=dict)
    divergence: Optional[DivergenceResult] = None

    @classmethod
    def empty(cls, reason: str = "Insufficient data") -> "ReversalScore":
        """Create an empty/zero score result."""
        return cls(
            raw_score=0.0,
            final_score=0.0,
            volume_multiplier=1.0,
            adx_multiplier=1.0,
            components={},
            divergence=DivergenceResult.none(reason),
        )


@dataclass
class OversoldScore:
    """
    Result from oversold scoring calculation.

    Attributes:
        final_score: Composite oversold score (1-10, higher = more oversold)
        components: Individual indicator scores before weighting
        raw_values: Actual indicator values from the data
    """
    final_score: float
    components: Dict[str, float] = field(default_factory=dict)
    raw_values: Dict[str, float] = field(default_factory=dict)

    @classmethod
    def empty(cls) -> "OversoldScore":
        """Create an empty/zero score result."""
        return cls(
            final_score=0.0,
            components={},
            raw_values={},
        )


@dataclass
class BullishScore:
    """
    Result from bullish scoring calculation.

    Attributes:
        final_score: Composite bullish score (1-10, higher = more bullish)
        components: Individual indicator scores before weighting
    """
    final_score: float
    components: Dict[str, float] = field(default_factory=dict)

    @classmethod
    def empty(cls) -> "BullishScore":
        """Create an empty/zero score result."""
        return cls(final_score=0.0, components={})

