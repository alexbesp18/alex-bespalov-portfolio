"""
Lead Generation Enricher

Generates first 100 customers strategy for business ideas:
- First 10 specific customer types
- Channels to reach first 100 customers
- Outreach templates
- Pricing validation signals
"""

import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from ..llm_client import LLMClient, get_client
from ...prompts import PromptLoader

__all__ = ["LeadGenEnricher", "LeadGenStrategy"]

logger = logging.getLogger(__name__)

FALLBACK_SYSTEM_PROMPT = """You are a growth marketing expert specializing in early-stage customer acquisition.
Generate specific, actionable strategies for finding the first 100 customers.
Always respond in valid JSON format."""

FALLBACK_USER_PROMPT = """For this business idea, create a detailed lead generation strategy to acquire the first 100 paying customers.

Business Idea: {idea_title}
Description: {idea_description}
Target Market: {target_market}

Generate a specific strategy including:
1. First 10 ideal customer profiles (specific company types, job titles, or demographics)
2. Top 5 channels to reach these customers (with specific subreddits, LinkedIn groups, communities)
3. 3 outreach templates (cold email, DM, community post)
4. 3 signals that validate pricing/willingness to pay

Respond in JSON format only:
{{
  "first_10_customers": [
    {{
      "profile": "Specific customer description",
      "where_to_find": "Specific location/platform",
      "pain_level": "high/medium/low"
    }}
  ],
  "channels": [
    {{
      "channel": "Channel name",
      "specific_locations": ["r/specificsubreddit", "LinkedIn group name"],
      "expected_conversion": "X%",
      "effort_level": "low/medium/high"
    }}
  ],
  "outreach_templates": [
    {{
      "type": "cold_email/dm/community_post",
      "subject_or_hook": "...",
      "body": "..."
    }}
  ],
  "pricing_validation_signals": [
    "Signal that indicates willingness to pay"
  ]
}}"""


@dataclass
class CustomerProfile:
    """A specific ideal customer profile."""
    profile: str
    where_to_find: str
    pain_level: str  # high/medium/low
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "profile": self.profile,
            "where_to_find": self.where_to_find,
            "pain_level": self.pain_level,
        }


@dataclass
class Channel:
    """A customer acquisition channel."""
    channel: str
    specific_locations: List[str]
    expected_conversion: str
    effort_level: str  # low/medium/high
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "channel": self.channel,
            "specific_locations": self.specific_locations,
            "expected_conversion": self.expected_conversion,
            "effort_level": self.effort_level,
        }


@dataclass
class OutreachTemplate:
    """An outreach template for customer acquisition."""
    type: str  # cold_email/dm/community_post
    subject_or_hook: str
    body: str
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "type": self.type,
            "subject_or_hook": self.subject_or_hook,
            "body": self.body,
        }


@dataclass
class LeadGenStrategy:
    """Complete lead generation strategy for an idea.
    
    Attributes:
        first_10_customers: Specific ideal customer profiles.
        channels: Customer acquisition channels.
        outreach_templates: Ready-to-use outreach templates.
        pricing_validation_signals: Signals of willingness to pay.
        cost_usd: LLM API cost.
    """
    first_10_customers: List[CustomerProfile]
    channels: List[Channel]
    outreach_templates: List[OutreachTemplate]
    pricing_validation_signals: List[str]
    cost_usd: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "first_10_customers": [c.to_dict() for c in self.first_10_customers],
            "channels": [c.to_dict() for c in self.channels],
            "outreach_templates": [t.to_dict() for t in self.outreach_templates],
            "pricing_validation_signals": self.pricing_validation_signals,
            "cost_usd": self.cost_usd,
        }


class LeadGenEnricher:
    """Enriches business ideas with lead generation strategies.
    
    Example:
        >>> enricher = LeadGenEnricher()
        >>> strategy = enricher.enrich(
        ...     idea_title="AI Code Review Bot",
        ...     idea_description="Automated PR reviews using GPT-4",
        ...     target_market="Small dev teams"
        ... )
        >>> print(f"Found {len(strategy.channels)} channels")
    """
    
    PROMPT_PATH = "business/lead_gen.md"
    
    def __init__(
        self,
        client: Optional[LLMClient] = None,
        provider: str = "openrouter",
        model: Optional[str] = None,
        prompt_loader: Optional[PromptLoader] = None,
    ):
        """Initialize enricher.
        
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
    
    def enrich(
        self,
        idea_title: str,
        idea_description: str,
        target_market: str,
    ) -> LeadGenStrategy:
        """Generate lead gen strategy for a business idea.
        
        Args:
            idea_title: Title of the business idea.
            idea_description: Description of what the business does.
            target_market: Target customer segment.
            
        Returns:
            LeadGenStrategy with customer acquisition plan.
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
        
        logger.info(f"Generating lead gen strategy for: {idea_title}")
        
        temperature = 0.7
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
            return LeadGenStrategy(
                first_10_customers=[],
                channels=[],
                outreach_templates=[],
                pricing_validation_signals=[],
                cost_usd=response.cost_usd,
            )
        
        # Parse customer profiles
        customers = []
        for item in data.get("first_10_customers", []):
            try:
                customers.append(CustomerProfile(
                    profile=item.get("profile", ""),
                    where_to_find=item.get("where_to_find", ""),
                    pain_level=item.get("pain_level", "medium"),
                ))
            except Exception as e:
                logger.warning(f"Failed to parse customer profile: {e}")
        
        # Parse channels
        channels = []
        for item in data.get("channels", []):
            try:
                channels.append(Channel(
                    channel=item.get("channel", ""),
                    specific_locations=item.get("specific_locations", []),
                    expected_conversion=item.get("expected_conversion", ""),
                    effort_level=item.get("effort_level", "medium"),
                ))
            except Exception as e:
                logger.warning(f"Failed to parse channel: {e}")
        
        # Parse templates
        templates = []
        for item in data.get("outreach_templates", []):
            try:
                templates.append(OutreachTemplate(
                    type=item.get("type", ""),
                    subject_or_hook=item.get("subject_or_hook", ""),
                    body=item.get("body", ""),
                ))
            except Exception as e:
                logger.warning(f"Failed to parse template: {e}")
        
        signals = data.get("pricing_validation_signals", [])
        
        logger.info(f"Generated lead gen strategy (${response.cost_usd:.4f})")
        
        return LeadGenStrategy(
            first_10_customers=customers,
            channels=channels,
            outreach_templates=templates,
            pricing_validation_signals=signals,
            cost_usd=response.cost_usd,
        )

