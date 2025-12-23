"""
Business Ideas Module

Modular business idea generation with enrichment pipeline:
- Core idea generation from transcript
- Lead generation strategy (first 100 customers)
- Niche validation (SaaS/AI budget indicators)
- Competitor analysis
"""

from .generator import BusinessIdeaGenerator, BusinessIdea, BusinessIdeasResult
from .lead_gen import LeadGenEnricher, LeadGenStrategy
from .niche_validator import NicheValidator, NicheValidation
from .competitor_analyzer import CompetitorAnalyzer, CompetitorAnalysis
from .pipeline import BusinessPipeline, EnrichedBusinessIdea, EnrichedBusinessResult

__all__ = [
    # Core generator
    "BusinessIdeaGenerator",
    "BusinessIdea",
    "BusinessIdeasResult",
    # Enrichers
    "LeadGenEnricher",
    "LeadGenStrategy",
    "NicheValidator",
    "NicheValidation",
    "CompetitorAnalyzer",
    "CompetitorAnalysis",
    # Pipeline
    "BusinessPipeline",
    "EnrichedBusinessIdea",
    "EnrichedBusinessResult",
]

