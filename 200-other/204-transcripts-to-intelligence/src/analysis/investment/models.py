"""
Investment Analysis Models

Data models for multi-lens investment analysis.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class InvestorLens:
    """An investor lens/framework for analysis.
    
    Attributes:
        name: Investor name (e.g., "Gavin Baker").
        key: Unique key for the lens (e.g., "gavin_baker").
        focus_areas: What this investor focuses on.
        key_questions: Questions they ask.
        prompt_path: Path to prompt file.
    """
    name: str
    key: str
    focus_areas: List[str]
    key_questions: List[str]
    prompt_path: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "key": self.key,
            "focus_areas": self.focus_areas,
            "key_questions": self.key_questions,
            "prompt_path": self.prompt_path,
        }


# Pre-defined investor lenses
INVESTOR_LENSES = {
    "gavin_baker": InvestorLens(
        name="Gavin Baker",
        key="gavin_baker",
        focus_areas=[
            "Growth at reasonable price",
            "Technology adoption curves",
            "Unit economics at scale",
            "Market share dynamics",
        ],
        key_questions=[
            "What's the TAM trajectory?",
            "Are unit economics improving with scale?",
            "What's the sustainable growth rate?",
            "How defensible is market share?",
        ],
        prompt_path="investment/lenses/gavin_baker.md",
    ),
    "jordi_visser": InvestorLens(
        name="Jordi Visser",
        key="jordi_visser",
        focus_areas=[
            "Macro liquidity conditions",
            "Flow dynamics",
            "Positioning and sentiment",
            "Cross-asset correlations",
        ],
        key_questions=[
            "How do macro conditions affect this?",
            "What's the positioning picture?",
            "Where are flows going?",
            "What's the risk/reward asymmetry?",
        ],
        prompt_path="investment/lenses/jordi_visser.md",
    ),
    "leopold_aschenbrenner": InvestorLens(
        name="Leopold Aschenbrenner",
        key="leopold_aschenbrenner",
        focus_areas=[
            "AI compute scaling laws",
            "AGI timelines",
            "Infrastructure requirements",
            "Geopolitical AI dynamics",
        ],
        key_questions=[
            "What compute is needed?",
            "When does this capability arrive?",
            "Who controls the infrastructure?",
            "What are the scaling bottlenecks?",
        ],
        prompt_path="investment/lenses/leopold_aschenbrenner.md",
    ),
    "karpathy": InvestorLens(
        name="Andrej Karpathy",
        key="karpathy",
        focus_areas=[
            "Technical AI feasibility",
            "Model architecture trends",
            "Data moats",
            "Engineering complexity",
        ],
        key_questions=[
            "Can this technically work?",
            "What's the data advantage?",
            "How hard is this to replicate?",
            "What are the technical moats?",
        ],
        prompt_path="investment/lenses/karpathy.md",
    ),
    "dwarkesh": InvestorLens(
        name="Dwarkesh Patel",
        key="dwarkesh",
        focus_areas=[
            "Long-term civilizational bets",
            "Transformative technology",
            "Tail risks and opportunities",
            "Historical analogies",
        ],
        key_questions=[
            "What's the 10-year view?",
            "What are the tail risks?",
            "What historical parallels exist?",
            "How does this change society?",
        ],
        prompt_path="investment/lenses/dwarkesh.md",
    ),
}


def get_lens(key: str) -> Optional[InvestorLens]:
    """Get an investor lens by key."""
    return INVESTOR_LENSES.get(key)


def list_lenses() -> List[str]:
    """List available lens keys."""
    return list(INVESTOR_LENSES.keys())


def get_all_lenses() -> List[InvestorLens]:
    """Get all investor lenses."""
    return list(INVESTOR_LENSES.values())


@dataclass
class StockPick:
    """A stock recommendation from a lens analysis."""
    ticker: str
    company: str
    exchange: str
    rationale: str
    conviction: str = "medium"  # low/medium/high
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "ticker": self.ticker,
            "company": self.company,
            "exchange": self.exchange,
            "rationale": self.rationale,
            "conviction": self.conviction,
        }


@dataclass
class LensAnalysis:
    """Analysis result from a single investor lens.
    
    Attributes:
        lens: The investor lens used.
        themes: Investment themes identified.
        stocks: Stock recommendations.
        key_insight: Most important insight.
        risks: Identified risks.
        opportunities: Identified opportunities.
        time_horizon: Recommended investment horizon.
        conviction: Overall conviction level.
        supporting_quotes: Quotes from transcript.
        cost_usd: LLM API cost.
    """
    lens: InvestorLens
    themes: List[str]
    stocks: List[StockPick]
    key_insight: str
    risks: List[str]
    opportunities: List[str]
    time_horizon: str
    conviction: str  # low/medium/high
    supporting_quotes: List[str]
    cost_usd: float = 0.0
    
    @property
    def tickers(self) -> List[str]:
        """Get list of ticker symbols."""
        return [s.ticker for s in self.stocks]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "lens": self.lens.to_dict(),
            "themes": self.themes,
            "stocks": [s.to_dict() for s in self.stocks],
            "key_insight": self.key_insight,
            "risks": self.risks,
            "opportunities": self.opportunities,
            "time_horizon": self.time_horizon,
            "conviction": self.conviction,
            "supporting_quotes": self.supporting_quotes,
            "cost_usd": self.cost_usd,
        }

