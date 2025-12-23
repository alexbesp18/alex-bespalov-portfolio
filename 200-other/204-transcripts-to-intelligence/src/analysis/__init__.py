"""
Analysis Module

Provides tools for analyzing YouTube podcast transcripts:
- Segmentation into LLM-digestible chunks
- Topic extraction with LLM
- Business idea generation with enrichments
- Investment thesis extraction with multi-lens analysis
- Quote validation
- Ticker validation

Usage:
    from src.analysis import (
        TranscriptSegmenter, 
        TopicExtractor,
        BusinessIdeaGenerator,
        BusinessPipeline,
        InvestmentThesisExtractor,
        QuoteValidator,
        TickerValidator,
    )
"""

from .models import TranscriptChunk, SegmentationResult
from .segmenter import TranscriptSegmenter, segment_transcript
from .llm_client import (
    LLMClient,
    LLMResponse,
    OpenAIClient,
    AnthropicClient,
    OpenRouterClient,
    get_client,
)
from .topic_extractor import (
    TopicExtractor,
    TopicExtractionResult,
    ChunkAnalysis,
    Quote,
)
# Legacy imports (backward compatible)
from .business_ideas import (
    BusinessIdeaGenerator as _LegacyBusinessIdeaGenerator,
    BusinessIdea as _LegacyBusinessIdea,
    BusinessIdeasResult as _LegacyBusinessIdeasResult,
    ExecutionPlan as _LegacyExecutionPlan,
)
# New modular business imports
from .business import (
    BusinessIdeaGenerator,
    BusinessIdea,
    BusinessIdeasResult,
    LeadGenEnricher,
    LeadGenStrategy,
    NicheValidator,
    NicheValidation,
    CompetitorAnalyzer,
    CompetitorAnalysis,
    BusinessPipeline,
    EnrichedBusinessIdea,
    EnrichedBusinessResult,
)
from .investment_thesis import (
    InvestmentThesisExtractor,
    InvestmentTheme,
    InvestmentThesisResult,
    StockRecommendation,
)
from .quote_validator import QuoteValidator, QuoteValidationResult
from .ticker_validator import TickerValidator, TickerValidationResult
from .base import (
    AnalysisModule,
    AnalysisResult,
    ModuleRegistry,
    register_module,
    get_module,
    list_modules,
)
# Investment module with multi-lens support
from .investment import (
    LensRunner,
    LensResult,
    LensComparator,
    LensComparison,
    ConsensusStock,
    InvestorLens,
    LensAnalysis,
)
# Podcaster automation module
from .podcaster_automation import (
    OpportunityDetector,
    AutomationOpportunity,
    SoftwareSpecsGenerator,
    SoftwareSpec,
    WorkflowBuilder,
    AutomationWorkflow,
    AgentIdeaGenerator,
    AgentIdea,
    PodcasterAutomationPipeline,
    PodcasterAutomationResult,
    EnrichedOpportunity,
)

__all__ = [
    # Segmenter
    "TranscriptChunk",
    "SegmentationResult",
    "TranscriptSegmenter",
    "segment_transcript",
    # LLM Client
    "LLMClient",
    "LLMResponse",
    "OpenAIClient",
    "AnthropicClient",
    "OpenRouterClient",
    "get_client",
    # Topic Extractor
    "TopicExtractor",
    "TopicExtractionResult",
    "ChunkAnalysis",
    "Quote",
    # Business Ideas (modular)
    "BusinessIdeaGenerator",
    "BusinessIdea",
    "BusinessIdeasResult",
    "LeadGenEnricher",
    "LeadGenStrategy",
    "NicheValidator",
    "NicheValidation",
    "CompetitorAnalyzer",
    "CompetitorAnalysis",
    "BusinessPipeline",
    "EnrichedBusinessIdea",
    "EnrichedBusinessResult",
    # Investment Thesis
    "InvestmentThesisExtractor",
    "InvestmentTheme",
    "InvestmentThesisResult",
    "StockRecommendation",
    # Validators
    "QuoteValidator",
    "QuoteValidationResult",
    "TickerValidator",
    "TickerValidationResult",
    # Base classes
    "AnalysisModule",
    "AnalysisResult",
    "ModuleRegistry",
    "register_module",
    "get_module",
    "list_modules",
    # Multi-lens investment
    "LensRunner",
    "LensResult",
    "LensComparator",
    "LensComparison",
    "ConsensusStock",
    "InvestorLens",
    "LensAnalysis",
    # Podcaster automation
    "OpportunityDetector",
    "AutomationOpportunity",
    "SoftwareSpecsGenerator",
    "SoftwareSpec",
    "WorkflowBuilder",
    "AutomationWorkflow",
    "AgentIdeaGenerator",
    "AgentIdea",
    "PodcasterAutomationPipeline",
    "PodcasterAutomationResult",
    "EnrichedOpportunity",
]

__version__ = "0.1.0"
