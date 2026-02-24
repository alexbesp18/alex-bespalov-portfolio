"""Data models for the True Value Oversold report.

Dataclasses and enums only — no business logic.
"""

from dataclasses import dataclass
from enum import Enum


class Tier(Enum):
    """Classification tiers for True Value results."""
    STRUCTURAL_BUY = "Structural Buy"           # Score >= 7.0
    WATCHLIST_ENTRY = "Watchlist Entry"          # Score >= 5.5
    REVERSAL_SPECULATIVE = "Reversal Speculative"  # Score >= 4.0


def assign_tier(score: float) -> Tier:
    """Assign tier based on True Value Score."""
    if score >= 7.0:
        return Tier.STRUCTURAL_BUY
    elif score >= 5.5:
        return Tier.WATCHLIST_ENTRY
    return Tier.REVERSAL_SPECULATIVE


@dataclass
class TrueValueResult:
    """Complete analysis result for a single ticker."""
    ticker: str
    price: float
    true_value_score: float
    tier: Tier
    # 4 component scores (0-10 each, pre-weight)
    oversold_component: float
    structure_component: float
    accumulation_component: float
    reversal_component: float
    # Display fields
    mt_rsi: float
    lt_score: float
    sma_alignment: str      # BULLISH / BEARISH / DEATH_CROSS / GOLDEN_CROSS
    obv_trend: str          # ACCUMULATING / NEUTRAL / DISTRIBUTING
    pct_1m: float
    pct_1y: float
