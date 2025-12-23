"""
Niche Validator

Validates business idea niches for SaaS/AI automation potential:
- Budget indicators (ability to pay)
- Pain severity assessment
- Decision-maker accessibility
- Market size estimation
"""

import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from ..llm_client import LLMClient, get_client
from ...prompts import PromptLoader

__all__ = ["NicheValidator", "NicheValidation"]

logger = logging.getLogger(__name__)

FALLBACK_SYSTEM_PROMPT = """You are a market research analyst specializing in B2B SaaS and AI automation markets.
Evaluate business niches for their viability as targets for software/AI solutions.
Be realistic and data-driven in your assessments.
Always respond in valid JSON format."""

FALLBACK_USER_PROMPT = """Evaluate this business idea's target niche for SaaS/AI automation potential.

Business Idea: {idea_title}
Description: {idea_description}
Target Market: {target_market}

Analyze the niche on these dimensions:

1. BUDGET INDICATORS: Does this niche have money to spend on SaaS/AI solutions?
   - Average company size and revenue
   - Current software spending patterns
   - AI/automation adoption signals

2. PAIN SEVERITY: How painful is the problem being solved?
   - Frequency of the problem
   - Cost of not solving it
   - Current workarounds

3. ACCESSIBILITY: How easy is it to reach decision-makers?
   - Who makes buying decisions
   - Where they congregate
   - Sales cycle length

4. MARKET SIZE: TAM/SAM/SOM estimation
   - Total addressable market
   - Serviceable addressable market
   - Realistic first-year target

Respond in JSON format only:
{{
  "overall_score": 1-10,
  "recommendation": "strong_yes/yes/maybe/no/strong_no",
  "budget_indicators": {{
    "score": 1-10,
    "avg_company_revenue": "$X-$Y",
    "software_budget_estimate": "$X-$Y/month",
    "ai_adoption_stage": "early/growing/mature",
    "evidence": ["specific evidence points"]
  }},
  "pain_severity": {{
    "score": 1-10,
    "frequency": "daily/weekly/monthly/quarterly",
    "cost_of_inaction": "description of costs",
    "current_workarounds": ["how they solve it now"],
    "urgency": "critical/high/medium/low"
  }},
  "accessibility": {{
    "score": 1-10,
    "decision_maker": "title/role",
    "congregating_places": ["where to find them"],
    "sales_cycle": "days/weeks/months",
    "gatekeepers": "description of barriers"
  }},
  "market_size": {{
    "tam": "$X",
    "sam": "$X",
    "som_year1": "$X",
    "num_potential_customers": "X companies/individuals"
  }},
  "red_flags": ["potential issues"],
  "green_flags": ["positive signals"]
}}"""


@dataclass
class BudgetIndicators:
    """Budget and spending indicators for a niche."""
    score: int
    avg_company_revenue: str
    software_budget_estimate: str
    ai_adoption_stage: str
    evidence: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "avg_company_revenue": self.avg_company_revenue,
            "software_budget_estimate": self.software_budget_estimate,
            "ai_adoption_stage": self.ai_adoption_stage,
            "evidence": self.evidence,
        }


@dataclass
class PainSeverity:
    """Pain severity assessment for a niche."""
    score: int
    frequency: str
    cost_of_inaction: str
    current_workarounds: List[str]
    urgency: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "frequency": self.frequency,
            "cost_of_inaction": self.cost_of_inaction,
            "current_workarounds": self.current_workarounds,
            "urgency": self.urgency,
        }


@dataclass
class Accessibility:
    """Decision-maker accessibility assessment."""
    score: int
    decision_maker: str
    congregating_places: List[str]
    sales_cycle: str
    gatekeepers: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "decision_maker": self.decision_maker,
            "congregating_places": self.congregating_places,
            "sales_cycle": self.sales_cycle,
            "gatekeepers": self.gatekeepers,
        }


@dataclass
class MarketSize:
    """Market size estimation."""
    tam: str
    sam: str
    som_year1: str
    num_potential_customers: str
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "tam": self.tam,
            "sam": self.sam,
            "som_year1": self.som_year1,
            "num_potential_customers": self.num_potential_customers,
        }


@dataclass
class NicheValidation:
    """Complete niche validation result.
    
    Attributes:
        overall_score: 1-10 score for niche viability.
        recommendation: Recommendation level.
        budget_indicators: Budget and spending analysis.
        pain_severity: Pain severity assessment.
        accessibility: Decision-maker accessibility.
        market_size: TAM/SAM/SOM estimates.
        red_flags: Potential issues.
        green_flags: Positive signals.
        cost_usd: LLM API cost.
    """
    overall_score: int
    recommendation: str
    budget_indicators: BudgetIndicators
    pain_severity: PainSeverity
    accessibility: Accessibility
    market_size: MarketSize
    red_flags: List[str]
    green_flags: List[str]
    cost_usd: float = 0.0
    
    @property
    def is_viable(self) -> bool:
        """Returns True if recommendation is positive."""
        return self.recommendation in ("strong_yes", "yes")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "recommendation": self.recommendation,
            "is_viable": self.is_viable,
            "budget_indicators": self.budget_indicators.to_dict(),
            "pain_severity": self.pain_severity.to_dict(),
            "accessibility": self.accessibility.to_dict(),
            "market_size": self.market_size.to_dict(),
            "red_flags": self.red_flags,
            "green_flags": self.green_flags,
            "cost_usd": self.cost_usd,
        }


class NicheValidator:
    """Validates business niches for SaaS/AI potential.
    
    Example:
        >>> validator = NicheValidator()
        >>> validation = validator.validate(
        ...     idea_title="AI Contract Review",
        ...     idea_description="Automated legal document analysis",
        ...     target_market="Mid-size law firms"
        ... )
        >>> print(f"Score: {validation.overall_score}/10")
        >>> print(f"Viable: {validation.is_viable}")
    """
    
    PROMPT_PATH = "business/niche_validation.md"
    
    def __init__(
        self,
        client: Optional[LLMClient] = None,
        provider: str = "openrouter",
        model: Optional[str] = None,
        prompt_loader: Optional[PromptLoader] = None,
    ):
        """Initialize validator.
        
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
    
    def validate(
        self,
        idea_title: str,
        idea_description: str,
        target_market: str,
    ) -> NicheValidation:
        """Validate a business niche.
        
        Args:
            idea_title: Title of the business idea.
            idea_description: Description of what the business does.
            target_market: Target customer segment.
            
        Returns:
            NicheValidation with comprehensive analysis.
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
        
        logger.info(f"Validating niche for: {idea_title}")
        
        temperature = 0.5
        max_tokens = 2000
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
            # Return minimal validation
            return self._empty_validation(response.cost_usd)
        
        try:
            # Parse budget indicators
            bi_data = data.get("budget_indicators", {})
            budget_indicators = BudgetIndicators(
                score=bi_data.get("score", 5),
                avg_company_revenue=bi_data.get("avg_company_revenue", "Unknown"),
                software_budget_estimate=bi_data.get("software_budget_estimate", "Unknown"),
                ai_adoption_stage=bi_data.get("ai_adoption_stage", "unknown"),
                evidence=bi_data.get("evidence", []),
            )
            
            # Parse pain severity
            ps_data = data.get("pain_severity", {})
            pain_severity = PainSeverity(
                score=ps_data.get("score", 5),
                frequency=ps_data.get("frequency", "unknown"),
                cost_of_inaction=ps_data.get("cost_of_inaction", "Unknown"),
                current_workarounds=ps_data.get("current_workarounds", []),
                urgency=ps_data.get("urgency", "medium"),
            )
            
            # Parse accessibility
            acc_data = data.get("accessibility", {})
            accessibility = Accessibility(
                score=acc_data.get("score", 5),
                decision_maker=acc_data.get("decision_maker", "Unknown"),
                congregating_places=acc_data.get("congregating_places", []),
                sales_cycle=acc_data.get("sales_cycle", "Unknown"),
                gatekeepers=acc_data.get("gatekeepers", "None identified"),
            )
            
            # Parse market size
            ms_data = data.get("market_size", {})
            market_size = MarketSize(
                tam=ms_data.get("tam", "Unknown"),
                sam=ms_data.get("sam", "Unknown"),
                som_year1=ms_data.get("som_year1", "Unknown"),
                num_potential_customers=ms_data.get("num_potential_customers", "Unknown"),
            )
            
            validation = NicheValidation(
                overall_score=data.get("overall_score", 5),
                recommendation=data.get("recommendation", "maybe"),
                budget_indicators=budget_indicators,
                pain_severity=pain_severity,
                accessibility=accessibility,
                market_size=market_size,
                red_flags=data.get("red_flags", []),
                green_flags=data.get("green_flags", []),
                cost_usd=response.cost_usd,
            )
            
            logger.info(
                f"Niche validation: {validation.overall_score}/10 "
                f"({validation.recommendation}) ${response.cost_usd:.4f}"
            )
            
            return validation
            
        except Exception as e:
            logger.error(f"Failed to parse validation: {e}")
            return self._empty_validation(response.cost_usd)
    
    def _empty_validation(self, cost: float) -> NicheValidation:
        """Return an empty validation result."""
        return NicheValidation(
            overall_score=0,
            recommendation="unknown",
            budget_indicators=BudgetIndicators(0, "", "", "", []),
            pain_severity=PainSeverity(0, "", "", [], ""),
            accessibility=Accessibility(0, "", [], "", ""),
            market_size=MarketSize("", "", "", ""),
            red_flags=["Failed to analyze"],
            green_flags=[],
            cost_usd=cost,
        )

