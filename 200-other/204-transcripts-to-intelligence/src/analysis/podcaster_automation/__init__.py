"""
Podcaster Automation Module

Identifies automation opportunities for the podcaster themselves based on
what they discussed in the transcript. Generates:
- Software specifications (MVP features, tech stack)
- Automation workflows (n8n, Zapier, Make)
- AI agent ideas (Custom GPTs, Claude projects)
"""

from .detector import OpportunityDetector, AutomationOpportunity
from .software_specs import SoftwareSpecsGenerator, SoftwareSpec
from .workflow_builder import WorkflowBuilder, AutomationWorkflow
from .agent_ideas import AgentIdeaGenerator, AgentIdea
from .pipeline import PodcasterAutomationPipeline, PodcasterAutomationResult, EnrichedOpportunity

__all__ = [
    # Detector
    "OpportunityDetector",
    "AutomationOpportunity",
    # Software specs
    "SoftwareSpecsGenerator",
    "SoftwareSpec",
    # Workflows
    "WorkflowBuilder",
    "AutomationWorkflow",
    # Agent ideas
    "AgentIdeaGenerator",
    "AgentIdea",
    # Pipeline
    "PodcasterAutomationPipeline",
    "PodcasterAutomationResult",
    "EnrichedOpportunity",
]

