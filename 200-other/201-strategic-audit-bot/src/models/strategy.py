"""Enhanced Pydantic models for deep strategic analysis."""

from pydantic import BaseModel, Field


class DeepOpportunity(BaseModel):
    """A strategic opportunity with multi-layer analysis."""

    title: str = Field(..., description="Concise opportunity title")
    thesis: str = Field(..., description="The core insight driving this opportunity")
    first_order_effect: str = Field(
        ..., description="Immediate impact if pursued"
    )
    second_order_effect: str = Field(
        ..., description="What the first-order effect causes"
    )
    third_order_effect: str = Field(
        ..., description="Ultimate strategic position achieved"
    )
    quantified_upside: str = Field(
        ..., description="Specific estimate: $X revenue, Y% improvement, etc."
    )
    downside_risk: str = Field(
        ..., description="What could go wrong and maximum exposure"
    )
    time_sensitivity: str = Field(
        ..., description="Why act now vs later - window of opportunity"
    )
    contrarian_angle: str = Field(
        ..., description="What consensus is missing or getting wrong"
    )


class VulnerabilityAnalysis(BaseModel):
    """Analysis of existential risks and hidden fragilities."""

    kill_scenario: str = Field(
        ..., description="The scenario that destroys this company in 3 years"
    )
    hidden_dependencies: list[str] = Field(
        default_factory=list,
        description="Single points of failure most overlook"
    )
    competitive_blind_spots: list[str] = Field(
        default_factory=list,
        description="Where they're exposed to disruption"
    )
    misaligned_incentives: list[str] = Field(
        default_factory=list,
        description="Where internal incentives conflict with strategy"
    )


class StrategicBrief(BaseModel):
    """Comprehensive strategic analysis with layered thinking."""

    # Layer 1: Current State
    situation_assessment: str = Field(
        ..., description="Current strategic position and context"
    )
    
    # Layer 2: Root Causes
    driving_forces: str = Field(
        ..., description="Why things are the way they are - structural forces"
    )
    
    # Layer 3: Time-Sensitive Insights
    strategic_windows: list[str] = Field(
        default_factory=list,
        description="Time-sensitive opportunities that won't last"
    )
    
    # Deep Opportunities
    asymmetric_opportunities: list[DeepOpportunity] = Field(
        default_factory=list,
        description="High upside, limited downside opportunities"
    )
    
    # Risk Analysis
    vulnerability_analysis: VulnerabilityAnalysis = Field(
        ..., description="Existential risks and fragilities"
    )
    
    # Action Items
    resource_reallocation: list[str] = Field(
        default_factory=list,
        description="What to STOP doing to free up resources"
    )
    
    quantified_recommendations: list[str] = Field(
        default_factory=list,
        description="Specific, measurable actions with expected outcomes"
    )
    
    ninety_day_priorities: list[str] = Field(
        default_factory=list,
        description="Top 3-5 actions for the first 90 days"
    )


# Keep backward compatible models for simpler use cases
class Opportunity(BaseModel):
    """Simple opportunity model for basic analysis."""

    title: str = Field(..., description="Short title for the opportunity")
    description: str = Field(..., description="Detailed description")
    impact: str = Field(..., description="High, Medium, or Low")
    effort: str = Field(..., description="High, Medium, or Low")
    category: str = Field(..., description="Product, Market, Technology, Operations")


if __name__ == "__main__":
    # Test enhanced model validation
    test_opportunity = DeepOpportunity(
        title="Embedded Finance Platform for SaaS",
        thesis="SaaS companies want to offer financial services but lack infrastructure",
        first_order_effect="Revenue from embedded finance API fees",
        second_order_effect="Deep integration creates switching costs",
        third_order_effect="Becomes the financial infrastructure layer for SaaS",
        quantified_upside="$500M ARR opportunity within 3 years based on TAM",
        downside_risk="$50M development cost if adoption slower than expected",
        time_sensitivity="First-mover advantage before banks build competing APIs",
        contrarian_angle="Market thinks payments is commoditizing; embedded finance is defensible",
    )
    print(f"Deep Opportunity:\n{test_opportunity.model_dump_json(indent=2)}\n")

    test_vulnerability = VulnerabilityAnalysis(
        kill_scenario="Regulatory change requiring banking licenses for payment processing",
        hidden_dependencies=[
            "AWS infrastructure concentration",
            "Key banking partner relationships",
        ],
        competitive_blind_spots=[
            "Apple/Google entering B2B payments",
            "Blockchain-based settlement bypassing traditional rails",
        ],
        misaligned_incentives=[
            "Sales comp favoring volume over margin",
            "Engineering rewarded for features not reliability",
        ],
    )
    print(f"Vulnerability Analysis:\n{test_vulnerability.model_dump_json(indent=2)}\n")

    test_brief = StrategicBrief(
        situation_assessment="Market leader in developer-focused payments with strong moat",
        driving_forces="API-first approach created network effects; developer loyalty is key",
        strategic_windows=[
            "AI integration before competitors (6-month window)",
            "Embedded finance while banks are slow (18-month window)",
        ],
        asymmetric_opportunities=[test_opportunity],
        vulnerability_analysis=test_vulnerability,
        resource_reallocation=[
            "Reduce investment in mature payment rails optimization",
            "Stop building custom enterprise features for single clients",
        ],
        quantified_recommendations=[
            "Launch embedded finance API targeting 1000 SaaS partners in Y1",
            "Increase developer relations budget by 40% to defend moat",
        ],
        ninety_day_priorities=[
            "Ship embedded finance MVP to 10 beta partners",
            "Hire Head of AI/ML to lead intelligent routing",
            "Renegotiate AWS contract for 20% cost reduction",
        ],
    )
    print(f"Strategic Brief:\n{test_brief.model_dump_json(indent=2)}")
