"""
Mock LLM Client

Provides mock implementations of LLMClient for testing without API calls.
"""

import json
from typing import Optional, Dict, Any

from src.analysis.llm_client import LLMClient, LLMResponse


class MockLLMClient(LLMClient):
    """Mock LLM client that returns predefined responses.
    
    Example:
        >>> client = MockLLMClient(response='{"answer": "42"}')
        >>> response = client.complete("What is the answer?")
        >>> response.parse_json()
        {'answer': '42'}
    """
    
    def __init__(
        self,
        response: str = "{}",
        cost_usd: float = 0.001,
        model: str = "mock-model",
        responses: Optional[Dict[str, str]] = None,
    ):
        """Initialize mock client.
        
        Args:
            response: Default response content (JSON string).
            cost_usd: Simulated cost per call.
            model: Simulated model name.
            responses: Optional dict mapping prompt substrings to responses.
        """
        self.default_response = response
        self.cost_usd = cost_usd
        self.model = model
        self.responses = responses or {}
        self.call_count = 0
        self.calls: list = []
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs,
    ) -> LLMResponse:
        """Return mock response.
        
        If responses dict is set, looks for matching prompt substring.
        Otherwise returns default response.
        """
        self.call_count += 1
        self.calls.append({
            "prompt": prompt,
            "system_prompt": system_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
        })
        
        # Find matching response
        content = self.default_response
        for substring, response in self.responses.items():
            if substring.lower() in prompt.lower():
                content = response
                break
        
        return LLMResponse(
            content=content,
            model=self.model,
            input_tokens=len(prompt.split()),
            output_tokens=len(content.split()),
            cost_usd=self.cost_usd,
            latency_seconds=0.1,
        )


# Sample mock responses for podcaster automation tests
MOCK_OPPORTUNITY_DETECTION = json.dumps({
    "opportunities": [
        {
            "pain_point": "Spending 4 hours per week on email triage",
            "time_spent": "4 hours/week",
            "frequency": "daily",
            "urgency": "high",
            "current_solution": "Manual sorting in Gmail",
            "automation_potential": "high",
            "supporting_quote": "I spend way too much time on email every day",
            "category": "email",
        },
        {
            "pain_point": "Manual transcript editing",
            "time_spent": "2 hours/week",
            "frequency": "weekly",
            "urgency": "medium",
            "current_solution": "Using Descript",
            "automation_potential": "medium",
            "supporting_quote": "Editing transcripts is tedious",
            "category": "content",
        },
    ],
    "podcaster_context": {
        "role": "podcast host",
        "team_size": "solo",
        "tech_savviness": "high",
    },
})


MOCK_SOFTWARE_SPEC = json.dumps({
    "name": "Email Priority AI",
    "tagline": "AI-powered email triage for busy professionals",
    "problem_statement": "Podcasters spend too much time sorting email",
    "target_user": "Solo podcasters with high email volume",
    "mvp_features": [
        {
            "feature": "Gmail integration",
            "description": "Connect to Gmail via OAuth",
            "priority": "must_have",
        },
        {
            "feature": "Priority scoring",
            "description": "AI ranks emails by importance",
            "priority": "must_have",
        },
    ],
    "tech_stack": {
        "frontend": "none",
        "backend": "Python/FastAPI",
        "database": "SQLite",
        "apis": ["Gmail API", "OpenAI API"],
        "hosting": "Railway",
    },
    "implementation_plan": [
        {"day": 1, "tasks": ["Setup project", "Gmail OAuth"], "deliverable": "Auth working", "hours": 6},
    ],
    "estimated_effort": {
        "total_hours": 30,
        "developer_level": "intermediate",
        "complexity": "medium",
    },
    "monetization": {
        "model": "freemium",
        "price_point": "$10/month",
    },
    "risks": ["Gmail API rate limits"],
    "alternatives": ["SaneBox"],
})


MOCK_WORKFLOW = json.dumps({
    "workflow_name": "Email Triage Automation",
    "description": "Automatically categorize and prioritize emails",
    "trigger": {
        "type": "schedule",
        "description": "Every 15 minutes",
        "example": "Check for new emails",
    },
    "platforms": {
        "n8n": {
            "difficulty": "medium",
            "nodes": [
                {"node_type": "Gmail Trigger", "purpose": "Watch inbox", "config_notes": "OAuth setup"},
            ],
            "estimated_setup_time": "30 minutes",
        },
        "zapier": {
            "difficulty": "easy",
            "zaps": [{"trigger": "New Email", "actions": ["Categorize", "Label"]}],
            "estimated_setup_time": "15 minutes",
            "pricing_tier": "professional",
        },
    },
    "required_integrations": ["Gmail", "OpenAI"],
    "data_flow": "Email -> AI Classification -> Label -> Notify",
    "error_handling": "Retry on failure, notify on repeated errors",
    "recommended_platform": "n8n",
    "recommendation_reason": "Free and self-hosted",
})


MOCK_AGENT_IDEA = json.dumps({
    "agent_name": "Email Triage Assistant",
    "purpose": "AI assistant that prioritizes and summarizes emails",
    "solutions": {
        "custom_gpt": {
            "name": "Email Triage GPT",
            "description": "Helps prioritize your emails",
            "instructions": "You are an email triage assistant...",
            "conversation_starters": ["Summarize my important emails"],
            "knowledge_files": ["Email templates"],
            "capabilities": ["Web browsing"],
            "setup_time": "15 minutes",
            "limitations": ["Cannot send emails"],
        },
        "claude_project": {
            "name": "Email Manager",
            "system_prompt": "You help manage email workflows...",
            "knowledge_base": ["Email best practices"],
            "custom_instructions": "Be concise",
            "use_cases": ["Daily email review"],
            "setup_time": "20 minutes",
        },
        "autonomous_agent": {
            "framework": "LangChain",
            "architecture": "Single agent with tools",
            "tools": [{"tool_name": "Gmail", "purpose": "Read emails", "api_or_service": "Gmail API"}],
            "memory_type": "conversation",
            "autonomy_level": "supervised",
            "development_effort": "20 hours",
            "hosting": "Railway",
            "cost_estimate": "$50/month",
        },
    },
    "recommended_solution": "custom_gpt",
    "recommendation_reason": "Easiest to set up for solo user",
    "implementation_steps": ["Create GPT", "Add instructions", "Test"],
    "success_metrics": ["Email response time reduced by 50%"],
})


def create_podcaster_automation_mock() -> MockLLMClient:
    """Create a mock client configured for podcaster automation tests."""
    return MockLLMClient(
        responses={
            "automation opportunities": MOCK_OPPORTUNITY_DETECTION,
            "software spec": MOCK_SOFTWARE_SPEC,
            "MVP software": MOCK_SOFTWARE_SPEC,
            "workflow": MOCK_WORKFLOW,
            "automation workflow": MOCK_WORKFLOW,
            "AI agent": MOCK_AGENT_IDEA,
            "agent idea": MOCK_AGENT_IDEA,
        },
        cost_usd=0.01,
    )

