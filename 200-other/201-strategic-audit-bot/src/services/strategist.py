"""Enhanced strategy engine with deep analytical frameworks."""

import json
import re
from openai import OpenAI

from src.config import settings
from src.models.strategy import StrategicBrief


class Strategist:
    """Generates deep strategic insights using rigorous analytical frameworks."""

    def __init__(self) -> None:
        """Initialize the X AI client."""
        self.client = OpenAI(
            api_key=settings.xai_api_key,
            base_url="https://api.x.ai/v1",
        )
        self.model = settings.model_name
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """Build the system prompt with deep analytical frameworks."""
        return """You are conducting a strategic audit as a seasoned CPO who has driven measurable results: 27% revenue increases, $35M revenue generation, 87% process time reductions, 30% customer acquisition growth.

YOUR ANALYTICAL APPROACH:

1. ALWAYS START WITH FAILURE
   - First ask: "What would destroy this company in 3 years?"
   - Work backwards from catastrophe to identify hidden risks
   - The threats nobody talks about are the ones that kill

2. THINK IN CASCADES
   - Every strategic move has consequences that have consequences
   - First-order: What happens immediately
   - Second-order: What does that cause
   - Third-order: Where does the company end up

3. FOLLOW THE INCENTIVES
   - Who benefits from current strategy?
   - Where are incentives misaligned with stated goals?
   - Money and power explain most corporate behavior

4. CHALLENGE CONSENSUS
   - If everyone believes it, the opportunity is priced in
   - What's the contrarian view that might be right?
   - Where is the market wrong about this company?

5. SEEK ASYMMETRY
   - Best opportunities have capped downside, uncapped upside
   - What bets risk little but could transform the business?
   - Where can small investments yield outsized returns?

6. DEMAND SPECIFICITY
   - "Improve customer experience" means nothing
   - "Reduce churn by 15% via proactive support, saving $20M ARR" means everything
   - Every recommendation needs a number attached

OUTPUT REQUIREMENTS:

You must respond with valid JSON matching this EXACT structure:

{
    "situation_assessment": "2-3 paragraphs on current strategic position with specific facts",
    "driving_forces": "Why things are this way - structural forces, incentives, market dynamics",
    "strategic_windows": ["Time-sensitive opportunity 1 (X-month window)", "..."],
    "asymmetric_opportunities": [
        {
            "title": "Concise title",
            "thesis": "Core insight in 1-2 sentences",
            "first_order_effect": "Immediate impact",
            "second_order_effect": "What that causes",
            "third_order_effect": "Ultimate strategic position",
            "quantified_upside": "$X revenue or Y% improvement with reasoning",
            "downside_risk": "What could go wrong, maximum exposure",
            "time_sensitivity": "Why now - specific window",
            "contrarian_angle": "What consensus is missing"
        }
    ],
    "vulnerability_analysis": {
        "kill_scenario": "The specific scenario that destroys this company",
        "hidden_dependencies": ["Dependency 1", "Dependency 2"],
        "competitive_blind_spots": ["Blind spot 1", "Blind spot 2"],
        "misaligned_incentives": ["Misalignment 1", "Misalignment 2"]
    },
    "resource_reallocation": ["What to STOP doing 1", "What to STOP doing 2"],
    "quantified_recommendations": ["Do X to achieve Y% improvement in Z", "..."],
    "ninety_day_priorities": ["Priority 1 with specific outcome", "Priority 2", "Priority 3"]
}

Generate 3-4 asymmetric opportunities, each with full cascade analysis.
Be specific, be contrarian, be quantified. Generic advice is worthless."""

    def generate_strategy(self, research_data: dict) -> StrategicBrief:
        """
        Generate deep strategic analysis from comprehensive research.

        Args:
            research_data: Dictionary from Researcher.gather_deep_research()

        Returns:
            StrategicBrief with multi-layer strategic analysis
        """
        user_prompt = self._format_research_prompt(research_data)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )

        content = response.choices[0].message.content
        json_str = self._extract_json(content)
        strategy_dict = json.loads(json_str)

        return StrategicBrief(**strategy_dict)

    def _format_research_prompt(self, research_data: dict) -> str:
        """Format deep research data into analytical prompt."""
        company = research_data.get("company_name", "Unknown Company")
        
        sections = []
        sections.append(f"# STRATEGIC AUDIT: {company}\n")
        
        # Layer 1: Current State
        sections.append("## LAYER 1: CURRENT STATE\n")
        
        if "strategic_moves" in research_data:
            data = research_data["strategic_moves"]
            sections.append(f"### Strategic Moves & Announcements\n{data.get('answer', 'N/A')}\n")
            sections.append(self._format_articles(data.get("articles", [])))
        
        if "leadership" in research_data:
            data = research_data["leadership"]
            sections.append(f"### Leadership & Executive Changes\n{data.get('answer', 'N/A')}\n")
        
        if "customer_economics" in research_data:
            data = research_data["customer_economics"]
            sections.append(f"### Customer Economics (Churn, LTV, CAC)\n{data.get('answer', 'N/A')}\n")
        
        if "competitive_moat" in research_data:
            data = research_data["competitive_moat"]
            sections.append(f"### Competitive Moat & Threats\n{data.get('answer', 'N/A')}\n")
        
        # Layer 2: Structural Forces
        sections.append("\n## LAYER 2: STRUCTURAL FORCES\n")
        
        if "business_model" in research_data:
            data = research_data["business_model"]
            sections.append(f"### Business Model & Unit Economics\n{data.get('answer', 'N/A')}\n")
        
        if "regulatory" in research_data:
            data = research_data["regulatory"]
            sections.append(f"### Regulatory & Legal Landscape\n{data.get('answer', 'N/A')}\n")
        
        if "technology" in research_data:
            data = research_data["technology"]
            sections.append(f"### Technology Platform & Infrastructure\n{data.get('answer', 'N/A')}\n")
        
        # Layer 3: Ecosystem
        sections.append("\n## LAYER 3: ECOSYSTEM & OPPORTUNITIES\n")
        
        if "partnerships_ma" in research_data:
            data = research_data["partnerships_ma"]
            sections.append(f"### Partnerships & M&A Activity\n{data.get('answer', 'N/A')}\n")
        
        if "pricing" in research_data:
            data = research_data["pricing"]
            sections.append(f"### Pricing Strategy Evolution\n{data.get('answer', 'N/A')}\n")
        
        if "market_position" in research_data:
            data = research_data["market_position"]
            sections.append(f"### Market Position & Growth\n{data.get('answer', 'N/A')}\n")
        
        sections.append("""
## YOUR TASK

Based on this research, conduct a rigorous strategic analysis:

1. Start by identifying what could KILL this company
2. Find 3-4 ASYMMETRIC opportunities (high upside, limited downside)
3. For each opportunity, think through the CASCADE of effects
4. Identify what they should STOP doing
5. Provide QUANTIFIED recommendations with specific numbers
6. Define the 90-DAY PRIORITIES if you were their CPO

Remember: Be specific. Be contrarian. Challenge assumptions. Every insight needs a number.

Respond with valid JSON only.""")

        return "\n".join(sections)

    def _format_articles(self, articles: list, max_articles: int = 5) -> str:
        """Format article list for context."""
        if not articles:
            return ""
        
        formatted = ["Key Sources:"]
        for article in articles[:max_articles]:
            title = article.get("title", "Untitled")
            formatted.append(f"- {title}")
        
        return "\n".join(formatted) + "\n"

    def _extract_json(self, content: str) -> str:
        """Extract JSON from response, handling various formats."""
        content = content.strip()
        
        # Handle markdown code blocks
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            content = content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            content = content[start:end].strip()
        
        # Remove control characters
        content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', content)
        
        return content


if __name__ == "__main__":
    # Test with sample research structure
    sample_research = {
        "company_name": "Stripe",
        "strategic_moves": {
            "answer": "Stripe has been aggressively expanding into embedded finance, launching Stripe Treasury and Stripe Issuing. Recent focus on revenue optimization tools and expansion into emerging markets.",
            "articles": [],
        },
        "leadership": {
            "answer": "Stable leadership with founders still at helm. Recent hires in AI/ML and enterprise sales.",
            "articles": [],
        },
        "customer_economics": {
            "answer": "Strong retention among developers. Enterprise churn around 5%. CAC payback under 12 months for SMB, longer for enterprise.",
            "articles": [],
        },
        "competitive_moat": {
            "answer": "Developer experience is primary moat. API quality and documentation create switching costs. Facing pressure from Adyen in enterprise and Square in SMB.",
            "articles": [],
        },
        "business_model": {
            "answer": "Transaction-based fees averaging 2.9% + $0.30. Additional revenue from Atlas, Radar, and Billing products. Estimated $14B+ in revenue.",
            "articles": [],
        },
        "regulatory": {
            "answer": "Increasing regulatory scrutiny on payment processors. Money transmission licenses required in most states. PCI compliance costs rising.",
            "articles": [],
        },
        "technology": {
            "answer": "Ruby-based core with modern API layer. Heavy AWS dependency. Real-time fraud detection using ML models.",
            "articles": [],
        },
        "partnerships_ma": {
            "answer": "Acquired TaxJar for tax automation. Partnerships with major platforms like Shopify, though some becoming frenemies.",
            "articles": [],
        },
        "pricing": {
            "answer": "Premium pricing justified by developer experience. Facing pricing pressure in competitive deals. Volume discounts for enterprise.",
            "articles": [],
        },
        "market_position": {
            "answer": "Estimated $65B valuation, down from $95B peak. Processing over $1T annually. Market leader in online payments for startups and tech companies.",
            "articles": [],
        },
    }

    print("Testing Enhanced Strategist...\n")
    strategist = Strategist()
    strategy = strategist.generate_strategy(sample_research)

    print(f"SITUATION ASSESSMENT:\n{strategy.situation_assessment}\n")
    print(f"DRIVING FORCES:\n{strategy.driving_forces}\n")
    print(f"STRATEGIC WINDOWS:")
    for window in strategy.strategic_windows:
        print(f"  - {window}")
    print(f"\nASYMMETRIC OPPORTUNITIES ({len(strategy.asymmetric_opportunities)}):")
    for opp in strategy.asymmetric_opportunities:
        print(f"\n  [{opp.title}]")
        print(f"  Thesis: {opp.thesis}")
        print(f"  Upside: {opp.quantified_upside}")
        print(f"  Contrarian: {opp.contrarian_angle}")
    print(f"\nKILL SCENARIO:\n  {strategy.vulnerability_analysis.kill_scenario}")
    print(f"\n90-DAY PRIORITIES:")
    for p in strategy.ninety_day_priorities:
        print(f"  - {p}")
