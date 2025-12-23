"""
Business Idea Generator

Core module for extracting actionable 24-hour business ideas from transcripts.
Uses external prompts for easy customization.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any

from ..llm_client import LLMClient, get_client
from ..models import TranscriptChunk
from ...prompts import PromptLoader

__all__ = ["BusinessIdeaGenerator", "BusinessIdea", "BusinessIdeasResult"]

logger = logging.getLogger(__name__)

# Fallback prompt if external file not found
FALLBACK_SYSTEM_PROMPT = """You are a startup strategist with expertise in rapid business validation.
Generate actionable ideas backed by specific content from the transcript.
Always respond in valid JSON format."""

FALLBACK_USER_PROMPT = """You are a startup strategist. Based on this podcast transcript, identify 
{num_ideas} business ideas that could be started within 24 hours with minimal capital.

Requirements:
1. Each idea must be DIRECTLY inspired by content in the podcast
2. Each idea must include a VERBATIM supporting quote from the transcript
3. Ideas should be actionable within 24 hours
4. Focus on: services, digital products, arbitrage, or consulting

Transcript:
---
{transcript}
---

Respond in JSON format only:
{{
  "ideas": [
    {{
      "title": "Business name/concept",
      "description": "What it is and why it works",
      "supporting_quote": "EXACT quote from transcript",
      "execution_plan": {{
        "hours_1_4": "Immediate actions",
        "hours_5_12": "Build/setup phase", 
        "hours_13_24": "Launch/test phase"
      }},
      "estimated_cost": "$X-$Y",
      "target_market": "Who you're selling to"
    }}
  ]
}}"""


@dataclass
class ExecutionPlan:
    """24-hour execution plan for a business idea."""
    hours_1_4: str
    hours_5_12: str
    hours_13_24: str
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "hours_1_4": self.hours_1_4,
            "hours_5_12": self.hours_5_12,
            "hours_13_24": self.hours_13_24,
        }


@dataclass
class BusinessIdea:
    """A 24-hour business idea extracted from transcript.
    
    Attributes:
        title: Name/concept of the business.
        description: What it is and why it works.
        supporting_quote: Verbatim quote from transcript.
        execution_plan: 24-hour action plan.
        estimated_cost: Cost range to start.
        target_market: Target customer segment.
    """
    title: str
    description: str
    supporting_quote: str
    execution_plan: ExecutionPlan
    estimated_cost: str
    target_market: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "supporting_quote": self.supporting_quote,
            "execution_plan": self.execution_plan.to_dict(),
            "estimated_cost": self.estimated_cost,
            "target_market": self.target_market,
        }


@dataclass
class BusinessIdeasResult:
    """Result of business idea generation.
    
    Attributes:
        ideas: List of generated business ideas.
        cost_usd: LLM API cost for generation.
    """
    ideas: List[BusinessIdea]
    cost_usd: float = 0.0
    
    @property
    def num_ideas(self) -> int:
        return len(self.ideas)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "num_ideas": self.num_ideas,
            "cost_usd": self.cost_usd,
            "ideas": [idea.to_dict() for idea in self.ideas],
        }


class BusinessIdeaGenerator:
    """Generates 24-hour business ideas from transcript content.
    
    Uses external prompt files for easy customization. Falls back to
    built-in prompts if external files are not found.
    
    Example:
        >>> generator = BusinessIdeaGenerator()
        >>> result = generator.generate(transcript_text, num_ideas=3)
        >>> for idea in result.ideas:
        ...     print(f"💡 {idea.title}")
        ...     print(f"   Quote: {idea.supporting_quote[:100]}...")
    """
    
    PROMPT_PATH = "business/idea_generation.md"
    
    def __init__(
        self,
        client: Optional[LLMClient] = None,
        provider: str = "openrouter",
        model: Optional[str] = None,
        prompt_loader: Optional[PromptLoader] = None,
    ):
        """Initialize generator.
        
        Args:
            client: Pre-configured LLM client.
            provider: LLM provider ("openai", "anthropic", "openrouter").
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
    
    def generate(
        self,
        transcript: str,
        num_ideas: int = 3,
    ) -> BusinessIdeasResult:
        """Generate business ideas from transcript.
        
        Args:
            transcript: Full transcript text or concatenated chunks.
            num_ideas: Target number of ideas (hint for LLM).
            
        Returns:
            BusinessIdeasResult with generated ideas.
        """
        # Get prompt from template or fallback
        template = self._get_template()
        
        if template:
            system_prompt, user_prompt = template.format(
                transcript=transcript,
                num_ideas=num_ideas,
            )
        else:
            system_prompt = FALLBACK_SYSTEM_PROMPT
            user_prompt = FALLBACK_USER_PROMPT.format(
                transcript=transcript,
                num_ideas=num_ideas,
            )
        
        logger.info(f"Generating {num_ideas} business ideas...")
        
        # Get temperature from template metadata or use default
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
            return BusinessIdeasResult(ideas=[], cost_usd=response.cost_usd)
        
        ideas = []
        for item in data.get("ideas", []):
            try:
                plan_data = item.get("execution_plan", {})
                plan = ExecutionPlan(
                    hours_1_4=plan_data.get("hours_1_4", ""),
                    hours_5_12=plan_data.get("hours_5_12", ""),
                    hours_13_24=plan_data.get("hours_13_24", ""),
                )
                
                idea = BusinessIdea(
                    title=item.get("title", "Untitled"),
                    description=item.get("description", ""),
                    supporting_quote=item.get("supporting_quote", ""),
                    execution_plan=plan,
                    estimated_cost=item.get("estimated_cost", "Unknown"),
                    target_market=item.get("target_market", ""),
                )
                ideas.append(idea)
            except Exception as e:
                logger.warning(f"Failed to parse idea: {e}")
                continue
        
        logger.info(f"Generated {len(ideas)} business ideas (${response.cost_usd:.4f})")
        
        return BusinessIdeasResult(ideas=ideas, cost_usd=response.cost_usd)
    
    def generate_from_chunks(
        self,
        chunks: List[TranscriptChunk],
        max_words: int = 5000,
        num_ideas: int = 3,
    ) -> BusinessIdeasResult:
        """Generate ideas from transcript chunks.
        
        Args:
            chunks: List of transcript chunks.
            max_words: Maximum words to include (for token limits).
            num_ideas: Target number of ideas.
            
        Returns:
            BusinessIdeasResult with generated ideas.
        """
        # Combine chunks up to word limit
        combined_text = []
        total_words = 0
        
        for chunk in chunks:
            if total_words + chunk.word_count > max_words:
                break
            combined_text.append(chunk.text)
            total_words += chunk.word_count
        
        transcript = " ".join(combined_text)
        return self.generate(transcript, num_ideas=num_ideas)

