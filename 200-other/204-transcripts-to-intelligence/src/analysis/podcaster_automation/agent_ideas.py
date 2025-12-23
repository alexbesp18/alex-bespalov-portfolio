"""
AI Agent Ideas Generator

Generates AI agent/assistant specifications including Custom GPTs,
Claude projects, and autonomous agent architectures.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from ..llm_client import LLMClient, get_client
from ...prompts import PromptLoader
from .detector import AutomationOpportunity, PodcasterContext

__all__ = ["AgentIdeaGenerator", "AgentIdea"]

logger = logging.getLogger(__name__)

FALLBACK_SYSTEM_PROMPT = """You are an AI solutions architect specializing in custom AI agents.
Design practical AI assistants using Custom GPTs, Claude projects, and agent frameworks.
Focus on solutions that provide immediate value with minimal setup.
Always respond in valid JSON format."""

FALLBACK_USER_PROMPT = """Design an AI agent/assistant to solve this automation opportunity.

Opportunity:
- Pain Point: {pain_point}
- Time Spent: {time_spent}
- Current Solution: {current_solution}
- Category: {category}

Podcaster Context:
- Role: {podcaster_role}
- Team Size: {team_size}
- Tech Savviness: {tech_savviness}

Design AI solutions at different complexity levels:
1. Custom GPT (easiest, no coding)
2. Claude Project (with knowledge base)
3. Autonomous Agent (most powerful)

Respond in JSON format only:
{{
  "agent_name": "Descriptive name",
  "purpose": "What this agent accomplishes",
  "solutions": {{
    "custom_gpt": {{
      "name": "GPT name",
      "description": "GPT description for OpenAI",
      "instructions": "System prompt / instructions (be specific)",
      "conversation_starters": ["Example prompt 1", "Example prompt 2"],
      "knowledge_files": ["Type of file to upload"],
      "capabilities": ["Web browsing", "Code interpreter", "DALL-E"],
      "setup_time": "X minutes",
      "limitations": ["What it can't do"]
    }},
    "claude_project": {{
      "name": "Project name",
      "system_prompt": "Detailed system prompt",
      "knowledge_base": ["Documents to add"],
      "custom_instructions": "Style and behavior guidelines",
      "use_cases": ["Specific use case 1", "Use case 2"],
      "setup_time": "X minutes"
    }},
    "autonomous_agent": {{
      "framework": "LangChain/AutoGPT/CrewAI/custom",
      "architecture": "Description of agent architecture",
      "tools": [
        {{
          "tool_name": "Tool name",
          "purpose": "What it does",
          "api_or_service": "API/service required"
        }}
      ],
      "memory_type": "short-term/long-term/both",
      "autonomy_level": "supervised/semi-autonomous/fully-autonomous",
      "development_effort": "X hours",
      "hosting": "Where to run it",
      "cost_estimate": "$X/month"
    }}
  }},
  "recommended_solution": "custom_gpt/claude_project/autonomous_agent",
  "recommendation_reason": "Why this is best for the user",
  "implementation_steps": [
    "Step 1: ...",
    "Step 2: ..."
  ],
  "success_metrics": ["How to measure if it's working"]
}}"""


@dataclass
class CustomGPTSpec:
    """Specification for a Custom GPT."""
    name: str
    description: str
    instructions: str
    conversation_starters: List[str]
    knowledge_files: List[str]
    capabilities: List[str]
    setup_time: str
    limitations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "instructions": self.instructions,
            "conversation_starters": self.conversation_starters,
            "knowledge_files": self.knowledge_files,
            "capabilities": self.capabilities,
            "setup_time": self.setup_time,
            "limitations": self.limitations,
        }


@dataclass
class ClaudeProjectSpec:
    """Specification for a Claude Project."""
    name: str
    system_prompt: str
    knowledge_base: List[str]
    custom_instructions: str
    use_cases: List[str]
    setup_time: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "system_prompt": self.system_prompt,
            "knowledge_base": self.knowledge_base,
            "custom_instructions": self.custom_instructions,
            "use_cases": self.use_cases,
            "setup_time": self.setup_time,
        }


@dataclass
class AgentTool:
    """A tool for an autonomous agent."""
    tool_name: str
    purpose: str
    api_or_service: str
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "tool_name": self.tool_name,
            "purpose": self.purpose,
            "api_or_service": self.api_or_service,
        }


@dataclass
class AutonomousAgentSpec:
    """Specification for an autonomous agent."""
    framework: str
    architecture: str
    tools: List[AgentTool]
    memory_type: str
    autonomy_level: str
    development_effort: str
    hosting: str
    cost_estimate: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "framework": self.framework,
            "architecture": self.architecture,
            "tools": [t.to_dict() for t in self.tools],
            "memory_type": self.memory_type,
            "autonomy_level": self.autonomy_level,
            "development_effort": self.development_effort,
            "hosting": self.hosting,
            "cost_estimate": self.cost_estimate,
        }


@dataclass
class AgentIdea:
    """Complete AI agent specification.
    
    Attributes:
        agent_name: Name of the agent.
        purpose: What it accomplishes.
        custom_gpt: Custom GPT specification.
        claude_project: Claude Project specification.
        autonomous_agent: Autonomous agent specification.
        recommended_solution: Which solution is best.
        recommendation_reason: Why.
        implementation_steps: How to implement.
        success_metrics: How to measure success.
        cost_usd: LLM API cost.
    """
    agent_name: str
    purpose: str
    custom_gpt: Optional[CustomGPTSpec]
    claude_project: Optional[ClaudeProjectSpec]
    autonomous_agent: Optional[AutonomousAgentSpec]
    recommended_solution: str
    recommendation_reason: str
    implementation_steps: List[str]
    success_metrics: List[str]
    cost_usd: float = 0.0
    
    def get_recommended(self) -> Optional[Any]:
        """Get the recommended solution specification."""
        if self.recommended_solution == "custom_gpt":
            return self.custom_gpt
        elif self.recommended_solution == "claude_project":
            return self.claude_project
        elif self.recommended_solution == "autonomous_agent":
            return self.autonomous_agent
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "purpose": self.purpose,
            "custom_gpt": self.custom_gpt.to_dict() if self.custom_gpt else None,
            "claude_project": self.claude_project.to_dict() if self.claude_project else None,
            "autonomous_agent": self.autonomous_agent.to_dict() if self.autonomous_agent else None,
            "recommended_solution": self.recommended_solution,
            "recommendation_reason": self.recommendation_reason,
            "implementation_steps": self.implementation_steps,
            "success_metrics": self.success_metrics,
            "cost_usd": self.cost_usd,
        }


class AgentIdeaGenerator:
    """Generates AI agent specifications.
    
    Example:
        >>> generator = AgentIdeaGenerator()
        >>> idea = generator.generate(opportunity, context)
        >>> print(f"🤖 {idea.agent_name}")
        >>> print(f"   Recommended: {idea.recommended_solution}")
    """
    
    PROMPT_PATH = "podcaster_automation/agent_ideas.md"
    
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
    ) -> AgentIdea:
        """Generate AI agent specification for an opportunity.
        
        Args:
            opportunity: The automation opportunity.
            context: Context about the podcaster.
            
        Returns:
            AgentIdea with solution specifications.
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
        
        logger.info(f"Generating agent idea for: {opportunity.pain_point[:50]}...")
        
        temperature = 0.6
        max_tokens = 3000
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
            return self._empty_idea(response.cost_usd)
        
        try:
            solutions = data.get("solutions", {})
            
            # Parse Custom GPT
            custom_gpt = None
            if "custom_gpt" in solutions:
                gpt = solutions["custom_gpt"]
                custom_gpt = CustomGPTSpec(
                    name=gpt.get("name", ""),
                    description=gpt.get("description", ""),
                    instructions=gpt.get("instructions", ""),
                    conversation_starters=gpt.get("conversation_starters", []),
                    knowledge_files=gpt.get("knowledge_files", []),
                    capabilities=gpt.get("capabilities", []),
                    setup_time=gpt.get("setup_time", "unknown"),
                    limitations=gpt.get("limitations", []),
                )
            
            # Parse Claude Project
            claude_project = None
            if "claude_project" in solutions:
                cp = solutions["claude_project"]
                claude_project = ClaudeProjectSpec(
                    name=cp.get("name", ""),
                    system_prompt=cp.get("system_prompt", ""),
                    knowledge_base=cp.get("knowledge_base", []),
                    custom_instructions=cp.get("custom_instructions", ""),
                    use_cases=cp.get("use_cases", []),
                    setup_time=cp.get("setup_time", "unknown"),
                )
            
            # Parse Autonomous Agent
            autonomous_agent = None
            if "autonomous_agent" in solutions:
                aa = solutions["autonomous_agent"]
                tools = []
                for tool in aa.get("tools", []):
                    tools.append(AgentTool(
                        tool_name=tool.get("tool_name", ""),
                        purpose=tool.get("purpose", ""),
                        api_or_service=tool.get("api_or_service", ""),
                    ))
                autonomous_agent = AutonomousAgentSpec(
                    framework=aa.get("framework", ""),
                    architecture=aa.get("architecture", ""),
                    tools=tools,
                    memory_type=aa.get("memory_type", "short-term"),
                    autonomy_level=aa.get("autonomy_level", "supervised"),
                    development_effort=aa.get("development_effort", "unknown"),
                    hosting=aa.get("hosting", ""),
                    cost_estimate=aa.get("cost_estimate", "unknown"),
                )
            
            idea = AgentIdea(
                agent_name=data.get("agent_name", "Untitled Agent"),
                purpose=data.get("purpose", ""),
                custom_gpt=custom_gpt,
                claude_project=claude_project,
                autonomous_agent=autonomous_agent,
                recommended_solution=data.get("recommended_solution", "custom_gpt"),
                recommendation_reason=data.get("recommendation_reason", ""),
                implementation_steps=data.get("implementation_steps", []),
                success_metrics=data.get("success_metrics", []),
                cost_usd=response.cost_usd,
            )
            
            logger.info(f"Generated agent idea: {idea.agent_name} (${response.cost_usd:.4f})")
            
            return idea
            
        except Exception as e:
            logger.error(f"Failed to parse agent idea: {e}")
            return self._empty_idea(response.cost_usd)
    
    def _empty_idea(self, cost: float) -> AgentIdea:
        """Return an empty idea on failure."""
        return AgentIdea(
            agent_name="Generation Failed",
            purpose="",
            custom_gpt=None,
            claude_project=None,
            autonomous_agent=None,
            recommended_solution="unknown",
            recommendation_reason="Generation failed",
            implementation_steps=[],
            success_metrics=[],
            cost_usd=cost,
        )

