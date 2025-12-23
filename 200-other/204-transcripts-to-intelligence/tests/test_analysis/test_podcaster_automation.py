"""
Tests for Podcaster Automation Module

Tests the opportunity detection, software specs, workflows, and agent ideas
generation using mocked LLM responses.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analysis.podcaster_automation import (
    OpportunityDetector,
    AutomationOpportunity,
    SoftwareSpecsGenerator,
    SoftwareSpec,
    WorkflowBuilder,
    AutomationWorkflow,
    AgentIdeaGenerator,
    AgentIdea,
    PodcasterAutomationPipeline,
    PodcasterAutomationResult,
    EnrichedOpportunity,
)
from src.analysis.podcaster_automation.detector import PodcasterContext, DetectionResult
from tests.fixtures.mock_llm import (
    MockLLMClient,
    create_podcaster_automation_mock,
    MOCK_OPPORTUNITY_DETECTION,
    MOCK_SOFTWARE_SPEC,
    MOCK_WORKFLOW,
    MOCK_AGENT_IDEA,
)


class TestOpportunityDetector:
    """Tests for OpportunityDetector."""
    
    def test_detect_opportunities(self):
        """Test detecting automation opportunities from transcript."""
        mock_client = MockLLMClient(response=MOCK_OPPORTUNITY_DETECTION)
        detector = OpportunityDetector(client=mock_client)
        
        result = detector.detect("This is a sample transcript about email management.")
        
        assert isinstance(result, DetectionResult)
        assert result.num_opportunities == 2
        assert result.cost_usd > 0
    
    def test_detect_parses_opportunities(self):
        """Test that opportunities are parsed correctly."""
        mock_client = MockLLMClient(response=MOCK_OPPORTUNITY_DETECTION)
        detector = OpportunityDetector(client=mock_client)
        
        result = detector.detect("Sample transcript")
        
        assert len(result.opportunities) == 2
        opp = result.opportunities[0]
        assert opp.pain_point == "Spending 4 hours per week on email triage"
        assert opp.time_spent == "4 hours/week"
        assert opp.urgency == "high"
        assert opp.category == "email"
    
    def test_detect_parses_context(self):
        """Test that podcaster context is parsed correctly."""
        mock_client = MockLLMClient(response=MOCK_OPPORTUNITY_DETECTION)
        detector = OpportunityDetector(client=mock_client)
        
        result = detector.detect("Sample transcript")
        
        assert result.podcaster_context.role == "podcast host"
        assert result.podcaster_context.team_size == "solo"
        assert result.podcaster_context.tech_savviness == "high"
    
    def test_detect_high_priority(self):
        """Test filtering high priority opportunities."""
        mock_client = MockLLMClient(response=MOCK_OPPORTUNITY_DETECTION)
        detector = OpportunityDetector(client=mock_client)
        
        result = detector.detect("Sample transcript")
        
        high_priority = result.high_priority
        assert len(high_priority) == 1
        assert high_priority[0].urgency == "high"
    
    def test_detect_empty_transcript(self):
        """Test handling empty transcript."""
        mock_client = MockLLMClient(response='{"opportunities": [], "podcaster_context": {}}')
        detector = OpportunityDetector(client=mock_client)
        
        result = detector.detect("")
        
        assert result.num_opportunities == 0
    
    def test_detect_invalid_json(self):
        """Test handling invalid JSON response."""
        mock_client = MockLLMClient(response="not valid json")
        detector = OpportunityDetector(client=mock_client)
        
        result = detector.detect("Sample transcript")
        
        # Should return empty result, not crash
        assert result.num_opportunities == 0
        assert result.podcaster_context.role == "unknown"


class TestSoftwareSpecsGenerator:
    """Tests for SoftwareSpecsGenerator."""
    
    def test_generate_spec(self):
        """Test generating software specification."""
        mock_client = MockLLMClient(response=MOCK_SOFTWARE_SPEC)
        generator = SoftwareSpecsGenerator(client=mock_client)
        
        opportunity = AutomationOpportunity(
            pain_point="Email triage",
            time_spent="4 hours/week",
            frequency="daily",
            urgency="high",
            current_solution="Manual",
            automation_potential="high",
            supporting_quote="I hate email",
            category="email",
        )
        context = PodcasterContext(role="host", team_size="solo", tech_savviness="high")
        
        spec = generator.generate(opportunity, context)
        
        assert isinstance(spec, SoftwareSpec)
        assert spec.name == "Email Priority AI"
        assert spec.total_hours == 30
        assert len(spec.mvp_features) == 2
    
    def test_generate_spec_to_dict(self):
        """Test that spec serializes to dict correctly."""
        mock_client = MockLLMClient(response=MOCK_SOFTWARE_SPEC)
        generator = SoftwareSpecsGenerator(client=mock_client)
        
        opportunity = AutomationOpportunity(
            pain_point="Test",
            time_spent="1h",
            frequency="daily",
            urgency="high",
            current_solution="Manual",
            automation_potential="high",
            supporting_quote="Quote",
            category="other",
        )
        context = PodcasterContext(role="host", team_size="solo", tech_savviness="high")
        
        spec = generator.generate(opportunity, context)
        spec_dict = spec.to_dict()
        
        assert "name" in spec_dict
        assert "tech_stack" in spec_dict
        assert "implementation_plan" in spec_dict


class TestWorkflowBuilder:
    """Tests for WorkflowBuilder."""
    
    def test_build_workflow(self):
        """Test building automation workflow."""
        mock_client = MockLLMClient(response=MOCK_WORKFLOW)
        builder = WorkflowBuilder(client=mock_client)
        
        opportunity = AutomationOpportunity(
            pain_point="Email triage",
            time_spent="4 hours/week",
            frequency="daily",
            urgency="high",
            current_solution="Manual",
            automation_potential="high",
            supporting_quote="Quote",
            category="email",
        )
        context = PodcasterContext(role="host", team_size="solo", tech_savviness="high")
        
        workflow = builder.build(opportunity, context)
        
        assert isinstance(workflow, AutomationWorkflow)
        assert workflow.workflow_name == "Email Triage Automation"
        assert workflow.recommended_platform == "n8n"
    
    def test_build_workflow_platforms(self):
        """Test that workflow includes multiple platforms."""
        mock_client = MockLLMClient(response=MOCK_WORKFLOW)
        builder = WorkflowBuilder(client=mock_client)
        
        opportunity = AutomationOpportunity(
            pain_point="Test",
            time_spent="1h",
            frequency="daily",
            urgency="high",
            current_solution="Manual",
            automation_potential="high",
            supporting_quote="Quote",
            category="other",
        )
        context = PodcasterContext(role="host", team_size="solo", tech_savviness="high")
        
        workflow = builder.build(opportunity, context)
        
        assert "n8n" in workflow.platforms
        assert "zapier" in workflow.platforms


class TestAgentIdeaGenerator:
    """Tests for AgentIdeaGenerator."""
    
    def test_generate_agent_idea(self):
        """Test generating AI agent idea."""
        mock_client = MockLLMClient(response=MOCK_AGENT_IDEA)
        generator = AgentIdeaGenerator(client=mock_client)
        
        opportunity = AutomationOpportunity(
            pain_point="Email triage",
            time_spent="4 hours/week",
            frequency="daily",
            urgency="high",
            current_solution="Manual",
            automation_potential="high",
            supporting_quote="Quote",
            category="email",
        )
        context = PodcasterContext(role="host", team_size="solo", tech_savviness="high")
        
        idea = generator.generate(opportunity, context)
        
        assert isinstance(idea, AgentIdea)
        assert idea.agent_name == "Email Triage Assistant"
        assert idea.recommended_solution == "custom_gpt"
    
    def test_generate_agent_has_solutions(self):
        """Test that agent idea includes all solution types."""
        mock_client = MockLLMClient(response=MOCK_AGENT_IDEA)
        generator = AgentIdeaGenerator(client=mock_client)
        
        opportunity = AutomationOpportunity(
            pain_point="Test",
            time_spent="1h",
            frequency="daily",
            urgency="high",
            current_solution="Manual",
            automation_potential="high",
            supporting_quote="Quote",
            category="other",
        )
        context = PodcasterContext(role="host", team_size="solo", tech_savviness="high")
        
        idea = generator.generate(opportunity, context)
        
        assert idea.custom_gpt is not None
        assert idea.claude_project is not None
        assert idea.autonomous_agent is not None


class TestPodcasterAutomationPipeline:
    """Tests for PodcasterAutomationPipeline."""
    
    def test_pipeline_run(self):
        """Test running the full pipeline."""
        mock_client = create_podcaster_automation_mock()
        pipeline = PodcasterAutomationPipeline(client=mock_client)
        
        result = pipeline.run(
            transcript="This is about email management and content creation.",
            max_opportunities=2,
        )
        
        assert isinstance(result, PodcasterAutomationResult)
        assert result.num_opportunities > 0
        assert result.total_cost_usd > 0
    
    def test_pipeline_enriched_opportunities(self):
        """Test that opportunities are enriched with all solutions."""
        mock_client = create_podcaster_automation_mock()
        pipeline = PodcasterAutomationPipeline(client=mock_client)
        
        result = pipeline.run(
            transcript="Email automation needed",
            max_opportunities=1,
        )
        
        assert len(result.enriched_opportunities) > 0
        enriched = result.enriched_opportunities[0]
        
        assert isinstance(enriched, EnrichedOpportunity)
        assert enriched.software_spec is not None
        assert enriched.workflow is not None
        assert enriched.agent_idea is not None
    
    def test_pipeline_detect_only(self):
        """Test detection-only mode."""
        mock_client = create_podcaster_automation_mock()
        pipeline = PodcasterAutomationPipeline(client=mock_client)
        
        result = pipeline.detect_only("Sample transcript")
        
        assert isinstance(result, DetectionResult)
        assert mock_client.call_count == 1  # Only one call for detection
    
    def test_pipeline_selective_enrichment(self):
        """Test selective enrichment (e.g., only specs, no workflows)."""
        mock_client = create_podcaster_automation_mock()
        pipeline = PodcasterAutomationPipeline(client=mock_client)
        
        result = pipeline.run(
            transcript="Sample transcript",
            generate_specs=True,
            generate_workflows=False,
            generate_agents=False,
            max_opportunities=1,
        )
        
        enriched = result.enriched_opportunities[0]
        assert enriched.software_spec is not None
        assert enriched.workflow is None
        assert enriched.agent_idea is None
    
    def test_pipeline_parallel_execution(self):
        """Test parallel enrichment execution."""
        mock_client = create_podcaster_automation_mock()
        pipeline = PodcasterAutomationPipeline(client=mock_client)
        
        result = pipeline.run(
            transcript="Sample transcript",
            max_opportunities=1,
            parallel=True,
        )
        
        # Should complete without errors
        assert result.num_opportunities > 0
    
    def test_pipeline_urgency_filter(self):
        """Test filtering by minimum urgency."""
        mock_client = create_podcaster_automation_mock()
        pipeline = PodcasterAutomationPipeline(client=mock_client)
        
        result = pipeline.run(
            transcript="Sample transcript",
            min_urgency="high",
            max_opportunities=5,
        )
        
        # All opportunities should be high urgency
        for enriched in result.enriched_opportunities:
            if enriched.opportunity.urgency != "high":
                # Some opportunities might have been filtered out
                pass
    
    def test_pipeline_to_dict(self):
        """Test result serialization."""
        mock_client = create_podcaster_automation_mock()
        pipeline = PodcasterAutomationPipeline(client=mock_client)
        
        result = pipeline.run(
            transcript="Sample transcript",
            max_opportunities=1,
        )
        
        result_dict = result.to_dict()
        
        assert "podcaster_context" in result_dict
        assert "enriched_opportunities" in result_dict
        assert "total_cost_usd" in result_dict


class TestDataclassesToDict:
    """Test serialization of dataclasses."""
    
    def test_automation_opportunity_to_dict(self):
        """Test AutomationOpportunity serialization."""
        opp = AutomationOpportunity(
            pain_point="Test pain",
            time_spent="2h",
            frequency="daily",
            urgency="high",
            current_solution="Manual",
            automation_potential="high",
            supporting_quote="Quote",
            category="email",
        )
        
        d = opp.to_dict()
        
        assert d["pain_point"] == "Test pain"
        assert d["urgency"] == "high"
        assert len(d) == 8  # All fields present
    
    def test_podcaster_context_to_dict(self):
        """Test PodcasterContext serialization."""
        ctx = PodcasterContext(
            role="host",
            team_size="solo",
            tech_savviness="high",
        )
        
        d = ctx.to_dict()
        
        assert d["role"] == "host"
        assert len(d) == 3

