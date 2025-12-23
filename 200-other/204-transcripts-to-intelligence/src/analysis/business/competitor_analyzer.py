"""
Competitor Analyzer

Analyzes competitive landscape for business ideas:
- Existing solutions
- Differentiation opportunities
- Market gaps
- Competitive advantages
"""

import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from ..llm_client import LLMClient, get_client
from ...prompts import PromptLoader

__all__ = ["CompetitorAnalyzer", "CompetitorAnalysis"]

logger = logging.getLogger(__name__)

FALLBACK_SYSTEM_PROMPT = """You are a competitive intelligence analyst specializing in tech startups.
Analyze competitive landscapes to identify opportunities and threats.
Be specific about existing solutions and differentiation strategies.
Always respond in valid JSON format."""

FALLBACK_USER_PROMPT = """Analyze the competitive landscape for this business idea.

Business Idea: {idea_title}
Description: {idea_description}
Target Market: {target_market}

Identify:
1. DIRECT COMPETITORS: Similar solutions in the market
2. INDIRECT COMPETITORS: Alternative approaches to solving the same problem
3. DIFFERENTIATION OPPORTUNITIES: How to stand out
4. MARKET GAPS: Underserved segments or unmet needs
5. COMPETITIVE MOAT: Potential sustainable advantages

Respond in JSON format only:
{{
  "competitive_intensity": "low/medium/high/very_high",
  "market_maturity": "nascent/emerging/growing/mature/declining",
  "direct_competitors": [
    {{
      "name": "Company/Product name",
      "description": "What they do",
      "strengths": ["strength1"],
      "weaknesses": ["weakness1"],
      "pricing": "$X/month or unknown",
      "market_share": "estimate or unknown"
    }}
  ],
  "indirect_competitors": [
    {{
      "name": "Alternative solution",
      "approach": "How they solve the problem differently"
    }}
  ],
  "differentiation_opportunities": [
    {{
      "strategy": "How to differentiate",
      "feasibility": "easy/medium/hard",
      "impact": "low/medium/high"
    }}
  ],
  "market_gaps": [
    {{
      "gap": "Description of gap",
      "size": "small/medium/large",
      "why_unserved": "Reason this gap exists"
    }}
  ],
  "potential_moats": [
    {{
      "moat_type": "network_effects/data/switching_costs/brand/expertise/speed",
      "description": "How to build this moat",
      "time_to_build": "months/years"
    }}
  ],
  "recommendation": "proceed/proceed_with_caution/pivot/avoid",
  "key_insight": "Most important competitive insight"
}}"""


@dataclass
class Competitor:
    """A direct competitor."""
    name: str
    description: str
    strengths: List[str]
    weaknesses: List[str]
    pricing: str
    market_share: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "pricing": self.pricing,
            "market_share": self.market_share,
        }


@dataclass
class IndirectCompetitor:
    """An indirect competitor or alternative solution."""
    name: str
    approach: str
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "approach": self.approach,
        }


@dataclass
class DifferentiationStrategy:
    """A differentiation opportunity."""
    strategy: str
    feasibility: str  # easy/medium/hard
    impact: str  # low/medium/high
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "strategy": self.strategy,
            "feasibility": self.feasibility,
            "impact": self.impact,
        }


@dataclass
class MarketGap:
    """An identified market gap."""
    gap: str
    size: str  # small/medium/large
    why_unserved: str
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "gap": self.gap,
            "size": self.size,
            "why_unserved": self.why_unserved,
        }


@dataclass
class PotentialMoat:
    """A potential competitive moat."""
    moat_type: str
    description: str
    time_to_build: str
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "moat_type": self.moat_type,
            "description": self.description,
            "time_to_build": self.time_to_build,
        }


@dataclass
class CompetitorAnalysis:
    """Complete competitive analysis result.
    
    Attributes:
        competitive_intensity: Level of competition.
        market_maturity: Stage of market development.
        direct_competitors: List of direct competitors.
        indirect_competitors: List of indirect competitors.
        differentiation_opportunities: Ways to stand out.
        market_gaps: Underserved areas.
        potential_moats: Sustainable advantages.
        recommendation: Strategic recommendation.
        key_insight: Most important insight.
        cost_usd: LLM API cost.
    """
    competitive_intensity: str
    market_maturity: str
    direct_competitors: List[Competitor]
    indirect_competitors: List[IndirectCompetitor]
    differentiation_opportunities: List[DifferentiationStrategy]
    market_gaps: List[MarketGap]
    potential_moats: List[PotentialMoat]
    recommendation: str
    key_insight: str
    cost_usd: float = 0.0
    
    @property
    def is_favorable(self) -> bool:
        """Returns True if competitive landscape is favorable."""
        return self.recommendation in ("proceed", "proceed_with_caution")
    
    @property
    def num_direct_competitors(self) -> int:
        return len(self.direct_competitors)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "competitive_intensity": self.competitive_intensity,
            "market_maturity": self.market_maturity,
            "direct_competitors": [c.to_dict() for c in self.direct_competitors],
            "indirect_competitors": [c.to_dict() for c in self.indirect_competitors],
            "differentiation_opportunities": [d.to_dict() for d in self.differentiation_opportunities],
            "market_gaps": [g.to_dict() for g in self.market_gaps],
            "potential_moats": [m.to_dict() for m in self.potential_moats],
            "recommendation": self.recommendation,
            "key_insight": self.key_insight,
            "is_favorable": self.is_favorable,
            "cost_usd": self.cost_usd,
        }


class CompetitorAnalyzer:
    """Analyzes competitive landscape for business ideas.
    
    Example:
        >>> analyzer = CompetitorAnalyzer()
        >>> analysis = analyzer.analyze(
        ...     idea_title="AI Meeting Notes",
        ...     idea_description="Automated meeting transcription and action items",
        ...     target_market="Remote teams"
        ... )
        >>> print(f"Competitors: {analysis.num_direct_competitors}")
        >>> print(f"Recommendation: {analysis.recommendation}")
    """
    
    PROMPT_PATH = "business/competitor_check.md"
    
    def __init__(
        self,
        client: Optional[LLMClient] = None,
        provider: str = "openrouter",
        model: Optional[str] = None,
        prompt_loader: Optional[PromptLoader] = None,
    ):
        """Initialize analyzer.
        
        Args:
            client: Pre-configured LLM client.
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
        self._template = None
    
    def _get_template(self):
        """Load prompt template (cached)."""
        if self._template is None:
            try:
                self._template = self.prompt_loader.load(self.PROMPT_PATH)
            except FileNotFoundError:
                logger.warning(f"Prompt file not found: {self.PROMPT_PATH}, using fallback")
                self._template = None
        return self._template
    
    def analyze(
        self,
        idea_title: str,
        idea_description: str,
        target_market: str,
    ) -> CompetitorAnalysis:
        """Analyze competitive landscape for a business idea.
        
        Args:
            idea_title: Title of the business idea.
            idea_description: Description of what the business does.
            target_market: Target customer segment.
            
        Returns:
            CompetitorAnalysis with comprehensive competitive intelligence.
        """
        template = self._get_template()
        
        if template:
            system_prompt, user_prompt = template.format(
                idea_title=idea_title,
                idea_description=idea_description,
                target_market=target_market,
            )
        else:
            system_prompt = FALLBACK_SYSTEM_PROMPT
            user_prompt = FALLBACK_USER_PROMPT.format(
                idea_title=idea_title,
                idea_description=idea_description,
                target_market=target_market,
            )
        
        logger.info(f"Analyzing competitors for: {idea_title}")
        
        temperature = 0.5
        max_tokens = 2500
        if template and template.metadata:
            temperature = template.metadata.get("temperature", temperature)
            max_tokens = template.metadata.get("max_tokens", max_tokens)
        
        response = self.client.complete(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        try:
            data = response.parse_json()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse response: {e}")
            return self._empty_analysis(response.cost_usd)
        
        try:
            # Parse direct competitors
            direct = []
            for item in data.get("direct_competitors", []):
                direct.append(Competitor(
                    name=item.get("name", "Unknown"),
                    description=item.get("description", ""),
                    strengths=item.get("strengths", []),
                    weaknesses=item.get("weaknesses", []),
                    pricing=item.get("pricing", "Unknown"),
                    market_share=item.get("market_share", "Unknown"),
                ))
            
            # Parse indirect competitors
            indirect = []
            for item in data.get("indirect_competitors", []):
                indirect.append(IndirectCompetitor(
                    name=item.get("name", "Unknown"),
                    approach=item.get("approach", ""),
                ))
            
            # Parse differentiation opportunities
            diff = []
            for item in data.get("differentiation_opportunities", []):
                diff.append(DifferentiationStrategy(
                    strategy=item.get("strategy", ""),
                    feasibility=item.get("feasibility", "medium"),
                    impact=item.get("impact", "medium"),
                ))
            
            # Parse market gaps
            gaps = []
            for item in data.get("market_gaps", []):
                gaps.append(MarketGap(
                    gap=item.get("gap", ""),
                    size=item.get("size", "medium"),
                    why_unserved=item.get("why_unserved", ""),
                ))
            
            # Parse potential moats
            moats = []
            for item in data.get("potential_moats", []):
                moats.append(PotentialMoat(
                    moat_type=item.get("moat_type", ""),
                    description=item.get("description", ""),
                    time_to_build=item.get("time_to_build", ""),
                ))
            
            analysis = CompetitorAnalysis(
                competitive_intensity=data.get("competitive_intensity", "unknown"),
                market_maturity=data.get("market_maturity", "unknown"),
                direct_competitors=direct,
                indirect_competitors=indirect,
                differentiation_opportunities=diff,
                market_gaps=gaps,
                potential_moats=moats,
                recommendation=data.get("recommendation", "unknown"),
                key_insight=data.get("key_insight", ""),
                cost_usd=response.cost_usd,
            )
            
            logger.info(
                f"Competitor analysis: {len(direct)} direct, "
                f"{analysis.recommendation} (${response.cost_usd:.4f})"
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to parse analysis: {e}")
            return self._empty_analysis(response.cost_usd)
    
    def _empty_analysis(self, cost: float) -> CompetitorAnalysis:
        """Return an empty analysis result."""
        return CompetitorAnalysis(
            competitive_intensity="unknown",
            market_maturity="unknown",
            direct_competitors=[],
            indirect_competitors=[],
            differentiation_opportunities=[],
            market_gaps=[],
            potential_moats=[],
            recommendation="unknown",
            key_insight="Analysis failed",
            cost_usd=cost,
        )

