"""
Software Specs Generator

Generates MVP software specifications for automation opportunities.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from ..llm_client import LLMClient, get_client
from ...prompts import PromptLoader
from .detector import AutomationOpportunity, PodcasterContext

__all__ = ["SoftwareSpecsGenerator", "SoftwareSpec"]

logger = logging.getLogger(__name__)

FALLBACK_SYSTEM_PROMPT = """You are a technical product manager who creates MVP specifications.
Design simple, focused software solutions that solve specific problems.
Prioritize speed to value and minimal viable features.
Always respond in valid JSON format."""

FALLBACK_USER_PROMPT = """Create an MVP software specification to solve this automation opportunity.

Opportunity:
- Pain Point: {pain_point}
- Time Spent: {time_spent}
- Current Solution: {current_solution}
- Category: {category}

Podcaster Context:
- Role: {podcaster_role}
- Team Size: {team_size}
- Tech Savviness: {tech_savviness}

Design a minimal but complete software solution:
1. Keep the MVP small (buildable in 1 week)
2. Focus on the core problem
3. Choose appropriate tech for the user's skill level
4. Include clear implementation steps

Respond in JSON format only:
{{
  "name": "Clear product name",
  "tagline": "One-line value proposition",
  "problem_statement": "The specific problem this solves",
  "target_user": "Who this is for",
  "mvp_features": [
    {{
      "feature": "Feature name",
      "description": "What it does",
      "priority": "must_have/should_have/nice_to_have"
    }}
  ],
  "tech_stack": {{
    "frontend": "Technology or 'none'",
    "backend": "Technology",
    "database": "Technology or 'none'",
    "apis": ["External APIs needed"],
    "hosting": "Where to deploy"
  }},
  "implementation_plan": [
    {{
      "day": 1,
      "tasks": ["Task 1", "Task 2"],
      "deliverable": "What's done by end of day"
    }}
  ],
  "estimated_effort": {{
    "total_hours": 40,
    "developer_level": "beginner/intermediate/advanced",
    "complexity": "low/medium/high"
  }},
  "monetization": {{
    "model": "free/freemium/paid/subscription",
    "price_point": "$X/month or 'free'",
    "target_customers": "Who would pay"
  }},
  "risks": ["Technical or business risks"],
  "alternatives": ["Existing tools that partially solve this"]
}}"""


@dataclass
class Feature:
    """A software feature."""
    feature: str
    description: str
    priority: str  # must_have/should_have/nice_to_have
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "feature": self.feature,
            "description": self.description,
            "priority": self.priority,
        }


@dataclass
class TechStack:
    """Technology stack for the software."""
    frontend: str
    backend: str
    database: str
    apis: List[str]
    hosting: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "frontend": self.frontend,
            "backend": self.backend,
            "database": self.database,
            "apis": self.apis,
            "hosting": self.hosting,
        }


@dataclass
class ImplementationDay:
    """A day in the implementation plan."""
    day: int
    tasks: List[str]
    deliverable: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "day": self.day,
            "tasks": self.tasks,
            "deliverable": self.deliverable,
        }


@dataclass
class SoftwareSpec:
    """Complete software specification.
    
    Attributes:
        name: Product name.
        tagline: One-line value proposition.
        problem_statement: The problem this solves.
        target_user: Who this is for.
        mvp_features: List of MVP features.
        tech_stack: Technology stack.
        implementation_plan: Day-by-day plan.
        total_hours: Estimated development hours.
        developer_level: Required skill level.
        complexity: Project complexity.
        monetization_model: How to monetize.
        price_point: Pricing.
        risks: Technical/business risks.
        alternatives: Existing tools.
        cost_usd: LLM API cost.
    """
    name: str
    tagline: str
    problem_statement: str
    target_user: str
    mvp_features: List[Feature]
    tech_stack: TechStack
    implementation_plan: List[ImplementationDay]
    total_hours: int
    developer_level: str
    complexity: str
    monetization_model: str
    price_point: str
    risks: List[str]
    alternatives: List[str]
    cost_usd: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "tagline": self.tagline,
            "problem_statement": self.problem_statement,
            "target_user": self.target_user,
            "mvp_features": [f.to_dict() for f in self.mvp_features],
            "tech_stack": self.tech_stack.to_dict(),
            "implementation_plan": [d.to_dict() for d in self.implementation_plan],
            "total_hours": self.total_hours,
            "developer_level": self.developer_level,
            "complexity": self.complexity,
            "monetization_model": self.monetization_model,
            "price_point": self.price_point,
            "risks": self.risks,
            "alternatives": self.alternatives,
            "cost_usd": self.cost_usd,
        }


class SoftwareSpecsGenerator:
    """Generates MVP software specifications.
    
    Example:
        >>> generator = SoftwareSpecsGenerator()
        >>> spec = generator.generate(opportunity, context)
        >>> print(f"📱 {spec.name}: {spec.tagline}")
        >>> print(f"   Build time: {spec.total_hours}h ({spec.complexity})")
    """
    
    PROMPT_PATH = "podcaster_automation/software_specs.md"
    
    def __init__(
        self,
        client: Optional[LLMClient] = None,
        provider: str = "openrouter",
        model: Optional[str] = None,
        prompt_loader: Optional[PromptLoader] = None,
    ):
        """Initialize generator."""
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
        opportunity: AutomationOpportunity,
        context: PodcasterContext,
    ) -> SoftwareSpec:
        """Generate software spec for an opportunity.
        
        Args:
            opportunity: The automation opportunity.
            context: Context about the podcaster.
            
        Returns:
            SoftwareSpec with MVP specification.
        """
        template = self._get_template()
        
        format_kwargs = {
            "pain_point": opportunity.pain_point,
            "time_spent": opportunity.time_spent,
            "current_solution": opportunity.current_solution,
            "category": opportunity.category,
            "podcaster_role": context.role,
            "team_size": context.team_size,
            "tech_savviness": context.tech_savviness,
        }
        
        if template:
            system_prompt, user_prompt = template.format(**format_kwargs)
        else:
            system_prompt = FALLBACK_SYSTEM_PROMPT
            user_prompt = FALLBACK_USER_PROMPT.format(**format_kwargs)
        
        logger.info(f"Generating software spec for: {opportunity.pain_point[:50]}...")
        
        temperature = 0.6
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
            return self._empty_spec(response.cost_usd)
        
        try:
            # Parse features
            features = []
            for item in data.get("mvp_features", []):
                features.append(Feature(
                    feature=item.get("feature", ""),
                    description=item.get("description", ""),
                    priority=item.get("priority", "should_have"),
                ))
            
            # Parse tech stack
            ts_data = data.get("tech_stack", {})
            tech_stack = TechStack(
                frontend=ts_data.get("frontend", "none"),
                backend=ts_data.get("backend", "Python"),
                database=ts_data.get("database", "none"),
                apis=ts_data.get("apis", []),
                hosting=ts_data.get("hosting", "Local"),
            )
            
            # Parse implementation plan
            impl_plan = []
            for item in data.get("implementation_plan", []):
                impl_plan.append(ImplementationDay(
                    day=item.get("day", 1),
                    tasks=item.get("tasks", []),
                    deliverable=item.get("deliverable", ""),
                ))
            
            # Parse effort
            effort = data.get("estimated_effort", {})
            
            # Parse monetization
            monetization = data.get("monetization", {})
            
            spec = SoftwareSpec(
                name=data.get("name", "Untitled"),
                tagline=data.get("tagline", ""),
                problem_statement=data.get("problem_statement", ""),
                target_user=data.get("target_user", ""),
                mvp_features=features,
                tech_stack=tech_stack,
                implementation_plan=impl_plan,
                total_hours=effort.get("total_hours", 40),
                developer_level=effort.get("developer_level", "intermediate"),
                complexity=effort.get("complexity", "medium"),
                monetization_model=monetization.get("model", "free"),
                price_point=monetization.get("price_point", "free"),
                risks=data.get("risks", []),
                alternatives=data.get("alternatives", []),
                cost_usd=response.cost_usd,
            )
            
            logger.info(f"Generated spec: {spec.name} (${response.cost_usd:.4f})")
            
            return spec
            
        except Exception as e:
            logger.error(f"Failed to parse spec: {e}")
            return self._empty_spec(response.cost_usd)
    
    def _empty_spec(self, cost: float) -> SoftwareSpec:
        """Return an empty spec on failure."""
        return SoftwareSpec(
            name="Generation Failed",
            tagline="",
            problem_statement="",
            target_user="",
            mvp_features=[],
            tech_stack=TechStack("", "", "", [], ""),
            implementation_plan=[],
            total_hours=0,
            developer_level="unknown",
            complexity="unknown",
            monetization_model="unknown",
            price_point="unknown",
            risks=["Generation failed"],
            alternatives=[],
            cost_usd=cost,
        )

