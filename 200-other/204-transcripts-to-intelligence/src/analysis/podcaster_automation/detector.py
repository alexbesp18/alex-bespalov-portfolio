"""
Automation Opportunity Detector

Analyzes transcripts to identify pain points and automation opportunities
that the podcaster themselves experiences or discusses.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from ..llm_client import LLMClient, get_client
from ...prompts import PromptLoader

__all__ = ["OpportunityDetector", "AutomationOpportunity"]

logger = logging.getLogger(__name__)

FALLBACK_SYSTEM_PROMPT = """You are an automation consultant analyzing podcasts for opportunities.
Identify pain points and repetitive tasks that the podcaster mentions experiencing.
Focus on problems that could be solved with software, automation workflows, or AI agents.
Always respond in valid JSON format."""

FALLBACK_USER_PROMPT = """Analyze this podcast transcript to identify automation opportunities for the podcaster.

Look for:
1. TIME SINKS: Tasks they mention spending significant time on
2. REPETITIVE WORK: Things they do repeatedly that could be automated
3. PAIN POINTS: Frustrations with current tools or processes
4. MANUAL PROCESSES: Things they wish were automated
5. WORKFLOW BOTTLENECKS: Where they get stuck or slowed down

Transcript:
---
{transcript}
---

Respond in JSON format only:
{{
  "opportunities": [
    {{
      "pain_point": "Clear description of the problem",
      "time_spent": "X hours/week or 'unknown'",
      "frequency": "daily/weekly/monthly/occasional",
      "urgency": "high/medium/low",
      "current_solution": "How they currently handle this",
      "automation_potential": "high/medium/low",
      "supporting_quote": "Exact quote from transcript",
      "category": "email/content/scheduling/research/communication/other"
    }}
  ],
  "podcaster_context": {{
    "role": "What the podcaster does",
    "team_size": "solo/small/medium/large or unknown",
    "tech_savviness": "high/medium/low based on discussion"
  }}
}}"""


@dataclass
class AutomationOpportunity:
    """An identified automation opportunity.
    
    Attributes:
        pain_point: Description of the problem.
        time_spent: Estimated time spent on this task.
        frequency: How often this occurs.
        urgency: Priority level.
        current_solution: How they currently handle it.
        automation_potential: How automatable this is.
        supporting_quote: Quote from transcript.
        category: Category of the opportunity.
    """
    pain_point: str
    time_spent: str
    frequency: str
    urgency: str
    current_solution: str
    automation_potential: str
    supporting_quote: str
    category: str
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "pain_point": self.pain_point,
            "time_spent": self.time_spent,
            "frequency": self.frequency,
            "urgency": self.urgency,
            "current_solution": self.current_solution,
            "automation_potential": self.automation_potential,
            "supporting_quote": self.supporting_quote,
            "category": self.category,
        }


@dataclass
class PodcasterContext:
    """Context about the podcaster."""
    role: str
    team_size: str
    tech_savviness: str
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "role": self.role,
            "team_size": self.team_size,
            "tech_savviness": self.tech_savviness,
        }


@dataclass
class DetectionResult:
    """Result of opportunity detection.
    
    Attributes:
        opportunities: List of identified opportunities.
        podcaster_context: Context about the podcaster.
        cost_usd: LLM API cost.
    """
    opportunities: List[AutomationOpportunity]
    podcaster_context: PodcasterContext
    cost_usd: float = 0.0
    
    @property
    def num_opportunities(self) -> int:
        return len(self.opportunities)
    
    @property
    def high_priority(self) -> List[AutomationOpportunity]:
        """Get high-urgency opportunities."""
        return [o for o in self.opportunities if o.urgency == "high"]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "num_opportunities": self.num_opportunities,
            "opportunities": [o.to_dict() for o in self.opportunities],
            "podcaster_context": self.podcaster_context.to_dict(),
            "cost_usd": self.cost_usd,
        }


class OpportunityDetector:
    """Detects automation opportunities from podcast transcripts.
    
    Example:
        >>> detector = OpportunityDetector()
        >>> result = detector.detect(transcript_text)
        >>> for opp in result.opportunities:
        ...     print(f"🔧 {opp.pain_point}")
        ...     print(f"   Time: {opp.time_spent}, Urgency: {opp.urgency}")
    """
    
    PROMPT_PATH = "podcaster_automation/opportunity_detector.md"
    
    def __init__(
        self,
        client: Optional[LLMClient] = None,
        provider: str = "openrouter",
        model: Optional[str] = None,
        prompt_loader: Optional[PromptLoader] = None,
    ):
        """Initialize detector.
        
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
    
    def detect(self, transcript: str) -> DetectionResult:
        """Detect automation opportunities in a transcript.
        
        Args:
            transcript: The podcast transcript text.
            
        Returns:
            DetectionResult with identified opportunities.
        """
        template = self._get_template()
        
        if template:
            system_prompt, user_prompt = template.format(transcript=transcript)
        else:
            system_prompt = FALLBACK_SYSTEM_PROMPT
            user_prompt = FALLBACK_USER_PROMPT.format(transcript=transcript)
        
        logger.info("Detecting automation opportunities...")
        
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
            return DetectionResult(
                opportunities=[],
                podcaster_context=PodcasterContext("unknown", "unknown", "unknown"),
                cost_usd=response.cost_usd,
            )
        
        # Parse opportunities
        opportunities = []
        for item in data.get("opportunities", []):
            try:
                opportunities.append(AutomationOpportunity(
                    pain_point=item.get("pain_point", ""),
                    time_spent=item.get("time_spent", "unknown"),
                    frequency=item.get("frequency", "unknown"),
                    urgency=item.get("urgency", "medium"),
                    current_solution=item.get("current_solution", ""),
                    automation_potential=item.get("automation_potential", "medium"),
                    supporting_quote=item.get("supporting_quote", ""),
                    category=item.get("category", "other"),
                ))
            except Exception as e:
                logger.warning(f"Failed to parse opportunity: {e}")
        
        # Parse context
        ctx_data = data.get("podcaster_context", {})
        context = PodcasterContext(
            role=ctx_data.get("role", "unknown"),
            team_size=ctx_data.get("team_size", "unknown"),
            tech_savviness=ctx_data.get("tech_savviness", "unknown"),
        )
        
        logger.info(f"Detected {len(opportunities)} opportunities (${response.cost_usd:.4f})")
        
        return DetectionResult(
            opportunities=opportunities,
            podcaster_context=context,
            cost_usd=response.cost_usd,
        )

