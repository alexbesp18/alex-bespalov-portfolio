"""
Workflow Builder

Generates automation workflow ideas for n8n, Zapier, and Make.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from ..llm_client import LLMClient, get_client
from ...prompts import PromptLoader
from .detector import AutomationOpportunity, PodcasterContext

__all__ = ["WorkflowBuilder", "AutomationWorkflow"]

logger = logging.getLogger(__name__)

FALLBACK_SYSTEM_PROMPT = """You are an automation expert specializing in no-code/low-code workflow tools.
Design practical automation workflows using n8n, Zapier, or Make.
Focus on workflows that non-technical users can implement.
Always respond in valid JSON format."""

FALLBACK_USER_PROMPT = """Design an automation workflow to solve this opportunity.

Opportunity:
- Pain Point: {pain_point}
- Time Spent: {time_spent}
- Current Solution: {current_solution}
- Category: {category}

Podcaster Context:
- Role: {podcaster_role}
- Team Size: {team_size}
- Tech Savviness: {tech_savviness}

Create workflows for multiple platforms:
1. n8n (self-hosted, most flexible)
2. Zapier (easiest to use)
3. Make/Integromat (visual, powerful)

Respond in JSON format only:
{{
  "workflow_name": "Descriptive name",
  "description": "What this workflow accomplishes",
  "trigger": {{
    "type": "schedule/webhook/app_event/manual",
    "description": "When this workflow runs",
    "example": "Every morning at 9 AM"
  }},
  "platforms": {{
    "n8n": {{
      "difficulty": "easy/medium/hard",
      "nodes": [
        {{
          "node_type": "Node name (e.g., 'Gmail Trigger')",
          "purpose": "What this node does",
          "config_notes": "Key configuration"
        }}
      ],
      "estimated_setup_time": "X minutes"
    }},
    "zapier": {{
      "difficulty": "easy/medium/hard",
      "zaps": [
        {{
          "trigger": "App + trigger event",
          "actions": ["Action 1", "Action 2"],
          "filters": "Any filter conditions"
        }}
      ],
      "estimated_setup_time": "X minutes",
      "pricing_tier": "free/starter/professional"
    }},
    "make": {{
      "difficulty": "easy/medium/hard",
      "modules": [
        {{
          "module": "App module",
          "purpose": "What it does"
        }}
      ],
      "estimated_setup_time": "X minutes"
    }}
  }},
  "required_integrations": ["App 1", "App 2"],
  "data_flow": "Description of how data moves through the workflow",
  "error_handling": "How to handle failures",
  "recommended_platform": "n8n/zapier/make",
  "recommendation_reason": "Why this platform is best for this user"
}}"""


@dataclass
class WorkflowNode:
    """A node/step in a workflow."""
    node_type: str
    purpose: str
    config_notes: str = ""
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "node_type": self.node_type,
            "purpose": self.purpose,
            "config_notes": self.config_notes,
        }


@dataclass
class PlatformWorkflow:
    """Workflow implementation for a specific platform."""
    platform: str
    difficulty: str
    nodes: List[WorkflowNode]
    setup_time: str
    extra_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "difficulty": self.difficulty,
            "nodes": [n.to_dict() for n in self.nodes],
            "setup_time": self.setup_time,
            **self.extra_info,
        }


@dataclass
class AutomationWorkflow:
    """Complete automation workflow specification.
    
    Attributes:
        workflow_name: Name of the workflow.
        description: What it accomplishes.
        trigger_type: When it runs.
        trigger_description: Trigger details.
        platforms: Platform-specific implementations.
        required_integrations: Apps that need to be connected.
        data_flow: How data moves through.
        error_handling: How to handle failures.
        recommended_platform: Best platform for this user.
        recommendation_reason: Why.
        cost_usd: LLM API cost.
    """
    workflow_name: str
    description: str
    trigger_type: str
    trigger_description: str
    platforms: Dict[str, PlatformWorkflow]
    required_integrations: List[str]
    data_flow: str
    error_handling: str
    recommended_platform: str
    recommendation_reason: str
    cost_usd: float = 0.0
    
    def get_platform(self, name: str) -> Optional[PlatformWorkflow]:
        """Get workflow for a specific platform."""
        return self.platforms.get(name)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_name": self.workflow_name,
            "description": self.description,
            "trigger_type": self.trigger_type,
            "trigger_description": self.trigger_description,
            "platforms": {k: v.to_dict() for k, v in self.platforms.items()},
            "required_integrations": self.required_integrations,
            "data_flow": self.data_flow,
            "error_handling": self.error_handling,
            "recommended_platform": self.recommended_platform,
            "recommendation_reason": self.recommendation_reason,
            "cost_usd": self.cost_usd,
        }


class WorkflowBuilder:
    """Generates automation workflow specifications.
    
    Example:
        >>> builder = WorkflowBuilder()
        >>> workflow = builder.build(opportunity, context)
        >>> print(f"⚡ {workflow.workflow_name}")
        >>> print(f"   Recommended: {workflow.recommended_platform}")
    """
    
    PROMPT_PATH = "podcaster_automation/workflow_builder.md"
    
    def __init__(
        self,
        client: Optional[LLMClient] = None,
        provider: str = "openrouter",
        model: Optional[str] = None,
        prompt_loader: Optional[PromptLoader] = None,
    ):
        """Initialize builder."""
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
    
    def build(
        self,
        opportunity: AutomationOpportunity,
        context: PodcasterContext,
    ) -> AutomationWorkflow:
        """Build workflow specification for an opportunity.
        
        Args:
            opportunity: The automation opportunity.
            context: Context about the podcaster.
            
        Returns:
            AutomationWorkflow with platform implementations.
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
        
        logger.info(f"Building workflow for: {opportunity.pain_point[:50]}...")
        
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
            return self._empty_workflow(response.cost_usd)
        
        try:
            # Parse trigger
            trigger_data = data.get("trigger", {})
            
            # Parse platforms
            platforms = {}
            platforms_data = data.get("platforms", {})
            
            for platform_name in ["n8n", "zapier", "make"]:
                if platform_name in platforms_data:
                    pdata = platforms_data[platform_name]
                    nodes = []
                    
                    # Handle different node structures
                    node_list = pdata.get("nodes", pdata.get("modules", pdata.get("zaps", [])))
                    for node in node_list:
                        if isinstance(node, dict):
                            nodes.append(WorkflowNode(
                                node_type=node.get("node_type", node.get("module", node.get("trigger", ""))),
                                purpose=node.get("purpose", ""),
                                config_notes=node.get("config_notes", ""),
                            ))
                    
                    platforms[platform_name] = PlatformWorkflow(
                        platform=platform_name,
                        difficulty=pdata.get("difficulty", "medium"),
                        nodes=nodes,
                        setup_time=pdata.get("estimated_setup_time", "unknown"),
                        extra_info={
                            k: v for k, v in pdata.items()
                            if k not in ("difficulty", "nodes", "modules", "zaps", "estimated_setup_time")
                        },
                    )
            
            workflow = AutomationWorkflow(
                workflow_name=data.get("workflow_name", "Untitled Workflow"),
                description=data.get("description", ""),
                trigger_type=trigger_data.get("type", "manual"),
                trigger_description=trigger_data.get("description", ""),
                platforms=platforms,
                required_integrations=data.get("required_integrations", []),
                data_flow=data.get("data_flow", ""),
                error_handling=data.get("error_handling", ""),
                recommended_platform=data.get("recommended_platform", "zapier"),
                recommendation_reason=data.get("recommendation_reason", ""),
                cost_usd=response.cost_usd,
            )
            
            logger.info(f"Built workflow: {workflow.workflow_name} (${response.cost_usd:.4f})")
            
            return workflow
            
        except Exception as e:
            logger.error(f"Failed to parse workflow: {e}")
            return self._empty_workflow(response.cost_usd)
    
    def _empty_workflow(self, cost: float) -> AutomationWorkflow:
        """Return an empty workflow on failure."""
        return AutomationWorkflow(
            workflow_name="Generation Failed",
            description="",
            trigger_type="manual",
            trigger_description="",
            platforms={},
            required_integrations=[],
            data_flow="",
            error_handling="",
            recommended_platform="unknown",
            recommendation_reason="Generation failed",
            cost_usd=cost,
        )

