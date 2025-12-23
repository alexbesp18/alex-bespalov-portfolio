"""
Investment Analysis Module

Modular investment thesis extraction with multi-lens analysis:
- Core thesis extraction from transcript
- Multiple investor lens frameworks (Gavin Baker, Jordi Visser, etc.)
- Lens comparison and synthesis
- Stock validation
"""

from .thesis_extractor import (
    InvestmentThesisExtractor,
    InvestmentTheme,
    InvestmentThesisResult,
    StockRecommendation,
)
from .lens_runner import LensRunner, LensResult
from .lens_comparator import LensComparator, LensComparison, ConsensusStock
from .models import InvestorLens, LensAnalysis

__all__ = [
    # Core extractor
    "InvestmentThesisExtractor",
    "InvestmentTheme",
    "InvestmentThesisResult",
    "StockRecommendation",
    # Lens system
    "InvestorLens",
    "LensAnalysis",
    "LensRunner",
    "LensResult",
    "LensComparator",
    "LensComparison",
    "ConsensusStock",
]

