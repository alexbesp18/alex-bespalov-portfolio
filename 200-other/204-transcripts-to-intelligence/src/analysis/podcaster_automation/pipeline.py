"""
Podcaster Automation Pipeline

Orchestrates the full podcaster automation analysis:
1. Detect automation opportunities
2. Generate software specs for each
3. Build workflow designs for each
4. Create AI agent ideas for each
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from ..llm_client import LLMClient, get_client
from ...prompts import PromptLoader
from .detector import OpportunityDetector, AutomationOpportunity, PodcasterContext, DetectionResult
from .software_specs import SoftwareSpecsGenerator, SoftwareSpec
from .workflow_builder import WorkflowBuilder, AutomationWorkflow
from .agent_ideas import AgentIdeaGenerator, AgentIdea

__all__ = ["PodcasterAutomationPipeline", "PodcasterAutomationResult", "EnrichedOpportunity"]

logger = logging.getLogger(__name__)


@dataclass
class EnrichedOpportunity:
    """An automation opportunity with all generated solutions.
    
    Attributes:
        opportunity: The original opportunity.
        software_spec: MVP software specification.
        workflow: Automation workflow design.
        agent_idea: AI agent specification.
    """
    opportunity: AutomationOpportunity
    software_spec: Optional[SoftwareSpec] = None
    workflow: Optional[AutomationWorkflow] = None
    agent_idea: Optional[AgentIdea] = None
    
    @property
    def total_cost_usd(self) -> float:
        """Total LLM cost for this opportunity."""
        cost = 0.0
        if self.software_spec:
            cost += self.software_spec.cost_usd
        if self.workflow:
            cost += self.workflow.cost_usd
        if self.agent_idea:
            cost += self.agent_idea.cost_usd
        return cost
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "opportunity": self.opportunity.to_dict(),
            "software_spec": self.software_spec.to_dict() if self.software_spec else None,
            "workflow": self.workflow.to_dict() if self.workflow else None,
            "agent_idea": self.agent_idea.to_dict() if self.agent_idea else None,
            "total_cost_usd": self.total_cost_usd,
        }


@dataclass
class PodcasterAutomationResult:
    """Complete result of podcaster automation analysis.
    
    Attributes:
        podcaster_context: Context about the podcaster.
        enriched_opportunities: Opportunities with solutions.
        detection_cost_usd: Cost of opportunity detection.
        total_cost_usd: Total LLM cost.
    """
    podcaster_context: PodcasterContext
    enriched_opportunities: List[EnrichedOpportunity]
    detection_cost_usd: float = 0.0
    
    @property
    def num_opportunities(self) -> int:
        return len(self.enriched_opportunities)
    
    @property
    def total_cost_usd(self) -> float:
        """Total LLM cost for all operations."""
        enrichment_cost = sum(e.total_cost_usd for e in self.enriched_opportunities)
        return self.detection_cost_usd + enrichment_cost
    
    @property
    def high_priority_opportunities(self) -> List[EnrichedOpportunity]:
        """Get high-urgency opportunities."""
        return [
            e for e in self.enriched_opportunities
            if e.opportunity.urgency == "high"
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "podcaster_context": self.podcaster_context.to_dict(),
            "num_opportunities": self.num_opportunities,
            "detection_cost_usd": self.detection_cost_usd,
            "total_cost_usd": self.total_cost_usd,
            "enriched_opportunities": [e.to_dict() for e in self.enriched_opportunities],
        }


class PodcasterAutomationPipeline:
    """Orchestrates full podcaster automation analysis.
    
    The pipeline:
    1. Detects automation opportunities from transcript
    2. For each opportunity, generates:
       - Software MVP specification
       - Automation workflow design
       - AI agent specification
    
    Example:
        >>> pipeline = PodcasterAutomationPipeline()
        >>> result = pipeline.run(transcript_text)
        >>> for opp in result.enriched_opportunities:
        ...     print(f"🔧 {opp.opportunity.pain_point}")
        ...     if opp.software_spec:
        ...         print(f"   📱 Software: {opp.software_spec.name}")
        ...     if opp.workflow:
        ...         print(f"   ⚡ Workflow: {opp.workflow.workflow_name}")
        ...     if opp.agent_idea:
        ...         print(f"   🤖 Agent: {opp.agent_idea.agent_name}")
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
            client: Pre-configured LLM client (shared across generators).
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
        
        # Initialize components with shared client
        self.detector = OpportunityDetector(
            client=self.client,
            prompt_loader=self.prompt_loader,
        )
        self.specs_generator = SoftwareSpecsGenerator(
            client=self.client,
            prompt_loader=self.prompt_loader,
        )
        self.workflow_builder = WorkflowBuilder(
            client=self.client,
            prompt_loader=self.prompt_loader,
        )
        self.agent_generator = AgentIdeaGenerator(
            client=self.client,
            prompt_loader=self.prompt_loader,
        )
    
    def run(
        self,
        transcript: str,
        generate_specs: bool = True,
        generate_workflows: bool = True,
        generate_agents: bool = True,
        max_opportunities: int = 5,
        min_urgency: Optional[str] = None,
        parallel: bool = True,
    ) -> PodcasterAutomationResult:
        """Run the full podcaster automation pipeline.
        
        Args:
            transcript: Transcript text to analyze.
            generate_specs: Whether to generate software specs.
            generate_workflows: Whether to generate workflow designs.
            generate_agents: Whether to generate agent ideas.
            max_opportunities: Maximum opportunities to process.
            min_urgency: Minimum urgency level ("high", "medium", "low").
            parallel: Run enrichment generators in parallel (faster, same cost).
            
        Returns:
            PodcasterAutomationResult with all enriched opportunities.
        """
        logger.info("Starting podcaster automation pipeline...")
        
        # Step 1: Detect opportunities
        detection_result = self.detector.detect(transcript)
        
        if not detection_result.opportunities:
            logger.warning("No automation opportunities detected")
            return PodcasterAutomationResult(
                podcaster_context=detection_result.podcaster_context,
                enriched_opportunities=[],
                detection_cost_usd=detection_result.cost_usd,
            )
        
        logger.info(f"Detected {len(detection_result.opportunities)} opportunities")
        
        # Filter by urgency if specified
        opportunities = detection_result.opportunities
        if min_urgency:
            urgency_order = {"high": 3, "medium": 2, "low": 1}
            min_level = urgency_order.get(min_urgency, 0)
            opportunities = [
                o for o in opportunities
                if urgency_order.get(o.urgency, 0) >= min_level
            ]
        
        # Limit number of opportunities
        opportunities = opportunities[:max_opportunities]
        
        # Step 2-4: Enrich each opportunity
        enriched = []
        context = detection_result.podcaster_context
        
        for opp in opportunities:
            logger.info(f"Enriching: {opp.pain_point[:50]}...")
            
            if parallel and sum([generate_specs, generate_workflows, generate_agents]) > 1:
                # Run enrichment generators in parallel
                enriched_opp = self._enrich_parallel(
                    opp, context, generate_specs, generate_workflows, generate_agents
                )
            else:
                # Sequential execution
                enriched_opp = EnrichedOpportunity(opportunity=opp)
                
                if generate_specs:
                    enriched_opp.software_spec = self.specs_generator.generate(opp, context)
                
                if generate_workflows:
                    enriched_opp.workflow = self.workflow_builder.build(opp, context)
                
                if generate_agents:
                    enriched_opp.agent_idea = self.agent_generator.generate(opp, context)
            
            enriched.append(enriched_opp)
        
        result = PodcasterAutomationResult(
            podcaster_context=context,
            enriched_opportunities=enriched,
            detection_cost_usd=detection_result.cost_usd,
        )
        
        logger.info(
            f"Pipeline complete: {result.num_opportunities} opportunities, "
            f"${result.total_cost_usd:.4f} total"
        )
        
        return result
    
    def _enrich_parallel(
        self,
        opportunity: AutomationOpportunity,
        context: PodcasterContext,
        generate_specs: bool,
        generate_workflows: bool,
        generate_agents: bool,
    ) -> EnrichedOpportunity:
        """Enrich an opportunity using parallel execution.
        
        Runs spec/workflow/agent generators concurrently for faster processing.
        
        Args:
            opportunity: The opportunity to enrich.
            context: Podcaster context.
            generate_specs: Whether to generate software specs.
            generate_workflows: Whether to generate workflow designs.
            generate_agents: Whether to generate agent ideas.
            
        Returns:
            EnrichedOpportunity with all requested solutions.
        """
        enriched = EnrichedOpportunity(opportunity=opportunity)
        
        # Build list of tasks to run
        tasks = []
        if generate_specs:
            tasks.append(('spec', self.specs_generator.generate, opportunity, context))
        if generate_workflows:
            tasks.append(('workflow', self.workflow_builder.build, opportunity, context))
        if generate_agents:
            tasks.append(('agent', self.agent_generator.generate, opportunity, context))
        
        if not tasks:
            return enriched
        
        # Run tasks in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            for task_name, func, opp, ctx in tasks:
                future = executor.submit(func, opp, ctx)
                futures[future] = task_name
            
            for future in as_completed(futures):
                task_name = futures[future]
                try:
                    result = future.result()
                    if task_name == 'spec':
                        enriched.software_spec = result
                    elif task_name == 'workflow':
                        enriched.workflow = result
                    elif task_name == 'agent':
                        enriched.agent_idea = result
                except Exception as e:
                    logger.error(f"Failed to generate {task_name}: {e}")
        
        return enriched
    
    def detect_only(self, transcript: str) -> DetectionResult:
        """Only detect opportunities without generating solutions.
        
        Args:
            transcript: Transcript text to analyze.
            
        Returns:
            DetectionResult with opportunities.
        """
        return self.detector.detect(transcript)
    
    def enrich_opportunity(
        self,
        opportunity: AutomationOpportunity,
        context: PodcasterContext,
        generate_specs: bool = True,
        generate_workflows: bool = True,
        generate_agents: bool = True,
    ) -> EnrichedOpportunity:
        """Enrich a single opportunity with solutions.
        
        Args:
            opportunity: The opportunity to enrich.
            context: Podcaster context.
            generate_specs: Whether to generate software specs.
            generate_workflows: Whether to generate workflow designs.
            generate_agents: Whether to generate agent ideas.
            
        Returns:
            EnrichedOpportunity with solutions.
        """
        enriched = EnrichedOpportunity(opportunity=opportunity)
        
        if generate_specs:
            enriched.software_spec = self.specs_generator.generate(opportunity, context)
        
        if generate_workflows:
            enriched.workflow = self.workflow_builder.build(opportunity, context)
        
        if generate_agents:
            enriched.agent_idea = self.agent_generator.generate(opportunity, context)
        
        return enriched

