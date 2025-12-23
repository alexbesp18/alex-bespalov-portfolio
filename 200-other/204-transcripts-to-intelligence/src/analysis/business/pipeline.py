"""
Business Enrichment Pipeline

Orchestrates the full business idea enrichment flow:
1. Generate core ideas from transcript
2. Validate each niche
3. Generate lead gen strategy
4. Analyze competitive landscape
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from .generator import BusinessIdeaGenerator, BusinessIdea, BusinessIdeasResult
from .lead_gen import LeadGenEnricher, LeadGenStrategy
from .niche_validator import NicheValidator, NicheValidation
from .competitor_analyzer import CompetitorAnalyzer, CompetitorAnalysis
from ..llm_client import LLMClient, get_client
from ...prompts import PromptLoader

__all__ = ["BusinessPipeline", "EnrichedBusinessIdea", "EnrichedBusinessResult"]

logger = logging.getLogger(__name__)


@dataclass
class EnrichedBusinessIdea:
    """A business idea with all enrichments.
    
    Attributes:
        idea: The core business idea.
        niche_validation: Niche viability analysis.
        lead_gen: Lead generation strategy.
        competitor_analysis: Competitive landscape.
    """
    idea: BusinessIdea
    niche_validation: Optional[NicheValidation] = None
    lead_gen: Optional[LeadGenStrategy] = None
    competitor_analysis: Optional[CompetitorAnalysis] = None
    
    @property
    def total_cost_usd(self) -> float:
        """Total LLM cost for all enrichments."""
        cost = 0.0
        if self.niche_validation:
            cost += self.niche_validation.cost_usd
        if self.lead_gen:
            cost += self.lead_gen.cost_usd
        if self.competitor_analysis:
            cost += self.competitor_analysis.cost_usd
        return cost
    
    @property
    def is_viable(self) -> bool:
        """Returns True if niche validation passed."""
        if self.niche_validation:
            return self.niche_validation.is_viable
        return True  # Assume viable if not validated
    
    @property
    def overall_score(self) -> int:
        """Returns niche validation score or 0."""
        if self.niche_validation:
            return self.niche_validation.overall_score
        return 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "idea": self.idea.to_dict(),
            "niche_validation": self.niche_validation.to_dict() if self.niche_validation else None,
            "lead_gen": self.lead_gen.to_dict() if self.lead_gen else None,
            "competitor_analysis": self.competitor_analysis.to_dict() if self.competitor_analysis else None,
            "total_cost_usd": self.total_cost_usd,
            "is_viable": self.is_viable,
            "overall_score": self.overall_score,
        }


@dataclass
class EnrichedBusinessResult:
    """Complete result of business idea enrichment pipeline.
    
    Attributes:
        ideas: List of enriched business ideas.
        generation_cost_usd: Cost for initial idea generation.
        total_cost_usd: Total cost including all enrichments.
    """
    ideas: List[EnrichedBusinessIdea]
    generation_cost_usd: float = 0.0
    
    @property
    def num_ideas(self) -> int:
        return len(self.ideas)
    
    @property
    def viable_ideas(self) -> List[EnrichedBusinessIdea]:
        """Return only ideas that passed niche validation."""
        return [i for i in self.ideas if i.is_viable]
    
    @property
    def total_cost_usd(self) -> float:
        """Total cost for all operations."""
        enrichment_cost = sum(i.total_cost_usd for i in self.ideas)
        return self.generation_cost_usd + enrichment_cost
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "num_ideas": self.num_ideas,
            "num_viable": len(self.viable_ideas),
            "generation_cost_usd": self.generation_cost_usd,
            "total_cost_usd": self.total_cost_usd,
            "ideas": [i.to_dict() for i in self.ideas],
        }


class BusinessPipeline:
    """Orchestrates full business idea enrichment pipeline.
    
    The pipeline runs ideas through multiple enrichment stages:
    1. Generate ideas from transcript
    2. Validate niche viability (optional)
    3. Generate lead gen strategy (optional)
    4. Analyze competitors (optional)
    
    Example:
        >>> pipeline = BusinessPipeline()
        >>> result = pipeline.run(
        ...     transcript=transcript_text,
        ...     num_ideas=3,
        ...     validate_niche=True,
        ...     generate_leads=True,
        ...     analyze_competitors=True,
        ... )
        >>> for idea in result.viable_ideas:
        ...     print(f"✅ {idea.idea.title} (Score: {idea.overall_score}/10)")
    """
    
    def __init__(
        self,
        client: Optional[LLMClient] = None,
        provider: str = "openrouter",
        model: Optional[str] = None,
        prompt_loader: Optional[PromptLoader] = None,
    ):
        """Initialize pipeline with shared resources.
        
        Args:
            client: Pre-configured LLM client (shared across enrichers).
            provider: LLM provider.
            model: Model to use.
            prompt_loader: Custom prompt loader.
        """
        if client:
            self.client = client
        else:
            kwargs = {"model": model} if model else {}
            self.client = get_client(provider, **kwargs)
        
        self.prompt_loader = prompt_loader or PromptLoader()
        
        # Initialize enrichers with shared client
        self.generator = BusinessIdeaGenerator(
            client=self.client,
            prompt_loader=self.prompt_loader,
        )
        self.niche_validator = NicheValidator(
            client=self.client,
            prompt_loader=self.prompt_loader,
        )
        self.lead_gen_enricher = LeadGenEnricher(
            client=self.client,
            prompt_loader=self.prompt_loader,
        )
        self.competitor_analyzer = CompetitorAnalyzer(
            client=self.client,
            prompt_loader=self.prompt_loader,
        )
    
    def run(
        self,
        transcript: str,
        num_ideas: int = 3,
        validate_niche: bool = True,
        generate_leads: bool = True,
        analyze_competitors: bool = True,
        skip_non_viable: bool = False,
        min_viability_score: int = 5,
    ) -> EnrichedBusinessResult:
        """Run the full enrichment pipeline.
        
        Args:
            transcript: Transcript text to analyze.
            num_ideas: Number of ideas to generate.
            validate_niche: Whether to validate niche viability.
            generate_leads: Whether to generate lead gen strategy.
            analyze_competitors: Whether to analyze competitors.
            skip_non_viable: Skip enrichments for non-viable niches.
            min_viability_score: Minimum score to consider viable (1-10).
            
        Returns:
            EnrichedBusinessResult with all enriched ideas.
        """
        logger.info(f"Starting business pipeline for {num_ideas} ideas")
        
        # Step 1: Generate core ideas
        ideas_result = self.generator.generate(transcript, num_ideas=num_ideas)
        
        if not ideas_result.ideas:
            logger.warning("No ideas generated")
            return EnrichedBusinessResult(
                ideas=[],
                generation_cost_usd=ideas_result.cost_usd,
            )
        
        logger.info(f"Generated {len(ideas_result.ideas)} ideas")
        
        # Step 2-4: Enrich each idea
        enriched_ideas = []
        
        for idea in ideas_result.ideas:
            enriched = EnrichedBusinessIdea(idea=idea)
            
            # Step 2: Niche validation
            if validate_niche:
                logger.info(f"Validating niche: {idea.title}")
                enriched.niche_validation = self.niche_validator.validate(
                    idea_title=idea.title,
                    idea_description=idea.description,
                    target_market=idea.target_market,
                )
                
                # Skip further enrichment if non-viable
                if skip_non_viable and enriched.overall_score < min_viability_score:
                    logger.info(f"Skipping non-viable idea: {idea.title} (score: {enriched.overall_score})")
                    enriched_ideas.append(enriched)
                    continue
            
            # Step 3: Lead generation
            if generate_leads:
                logger.info(f"Generating lead gen: {idea.title}")
                enriched.lead_gen = self.lead_gen_enricher.enrich(
                    idea_title=idea.title,
                    idea_description=idea.description,
                    target_market=idea.target_market,
                )
            
            # Step 4: Competitor analysis
            if analyze_competitors:
                logger.info(f"Analyzing competitors: {idea.title}")
                enriched.competitor_analysis = self.competitor_analyzer.analyze(
                    idea_title=idea.title,
                    idea_description=idea.description,
                    target_market=idea.target_market,
                )
            
            enriched_ideas.append(enriched)
        
        result = EnrichedBusinessResult(
            ideas=enriched_ideas,
            generation_cost_usd=ideas_result.cost_usd,
        )
        
        logger.info(
            f"Pipeline complete: {result.num_ideas} ideas, "
            f"{len(result.viable_ideas)} viable, "
            f"${result.total_cost_usd:.4f} total"
        )
        
        return result
    
    def enrich_existing_ideas(
        self,
        ideas: List[BusinessIdea],
        validate_niche: bool = True,
        generate_leads: bool = True,
        analyze_competitors: bool = True,
    ) -> List[EnrichedBusinessIdea]:
        """Enrich a list of existing business ideas.
        
        Args:
            ideas: List of BusinessIdea objects to enrich.
            validate_niche: Whether to validate niche viability.
            generate_leads: Whether to generate lead gen strategy.
            analyze_competitors: Whether to analyze competitors.
            
        Returns:
            List of EnrichedBusinessIdea objects.
        """
        enriched_ideas = []
        
        for idea in ideas:
            enriched = EnrichedBusinessIdea(idea=idea)
            
            if validate_niche:
                enriched.niche_validation = self.niche_validator.validate(
                    idea_title=idea.title,
                    idea_description=idea.description,
                    target_market=idea.target_market,
                )
            
            if generate_leads:
                enriched.lead_gen = self.lead_gen_enricher.enrich(
                    idea_title=idea.title,
                    idea_description=idea.description,
                    target_market=idea.target_market,
                )
            
            if analyze_competitors:
                enriched.competitor_analysis = self.competitor_analyzer.analyze(
                    idea_title=idea.title,
                    idea_description=idea.description,
                    target_market=idea.target_market,
                )
            
            enriched_ideas.append(enriched)
        
        return enriched_ideas

