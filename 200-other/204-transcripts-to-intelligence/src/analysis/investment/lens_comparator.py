"""
Lens Comparator

Compares and synthesizes results from multiple investor lens analyses.
Identifies consensus picks, divergence, and generates unified recommendations.
"""

import logging
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set

from .models import LensAnalysis, StockPick
from .lens_runner import LensResult

__all__ = ["LensComparator", "LensComparison", "ConsensusStock"]

logger = logging.getLogger(__name__)


@dataclass
class ConsensusStock:
    """A stock that appears in multiple lens analyses.
    
    Attributes:
        ticker: Stock ticker symbol.
        company: Company name.
        lens_count: Number of lenses recommending this stock.
        lenses: Names of lenses that recommended it.
        avg_conviction: Average conviction level across lenses.
        rationales: Rationales from each lens.
    """
    ticker: str
    company: str
    lens_count: int
    lenses: List[str]
    avg_conviction: str
    rationales: Dict[str, str]  # lens_name -> rationale
    
    @property
    def consensus_strength(self) -> str:
        """Categorize consensus strength."""
        if self.lens_count >= 4:
            return "strong"
        elif self.lens_count >= 2:
            return "moderate"
        else:
            return "weak"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticker": self.ticker,
            "company": self.company,
            "lens_count": self.lens_count,
            "lenses": self.lenses,
            "avg_conviction": self.avg_conviction,
            "consensus_strength": self.consensus_strength,
            "rationales": self.rationales,
        }


@dataclass
class LensDivergence:
    """Analysis of where lenses disagree.
    
    Attributes:
        topic: What they disagree on.
        perspectives: Each lens's view.
    """
    topic: str
    perspectives: Dict[str, str]  # lens_name -> perspective
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "perspectives": self.perspectives,
        }


@dataclass
class LensComparison:
    """Complete comparison of multi-lens analysis.
    
    Attributes:
        consensus_stocks: Stocks recommended by multiple lenses.
        unique_stocks: Stocks recommended by only one lens.
        divergences: Points of disagreement.
        common_themes: Themes appearing across lenses.
        synthesis: Unified investment thesis.
        confidence: Overall confidence level.
        total_unique_tickers: Count of unique tickers.
    """
    consensus_stocks: List[ConsensusStock]
    unique_stocks: Dict[str, List[StockPick]]  # lens_name -> stocks
    divergences: List[LensDivergence]
    common_themes: List[str]
    synthesis: str
    confidence: str
    total_unique_tickers: int
    
    @property
    def top_picks(self) -> List[ConsensusStock]:
        """Get stocks with strongest consensus."""
        return [s for s in self.consensus_stocks if s.consensus_strength in ("strong", "moderate")]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "consensus_stocks": [s.to_dict() for s in self.consensus_stocks],
            "unique_stocks": {
                lens: [s.to_dict() for s in stocks]
                for lens, stocks in self.unique_stocks.items()
            },
            "divergences": [d.to_dict() for d in self.divergences],
            "common_themes": self.common_themes,
            "synthesis": self.synthesis,
            "confidence": self.confidence,
            "total_unique_tickers": self.total_unique_tickers,
            "num_top_picks": len(self.top_picks),
        }


class LensComparator:
    """Compares and synthesizes multi-lens analysis results.
    
    Example:
        >>> runner = LensRunner()
        >>> result = runner.run_all_lenses(transcript)
        >>> comparator = LensComparator()
        >>> comparison = comparator.compare(result)
        >>> print(f"Top picks: {[s.ticker for s in comparison.top_picks]}")
    """
    
    def compare(self, lens_result: LensResult) -> LensComparison:
        """Compare results from multiple lens analyses.
        
        Args:
            lens_result: Result from LensRunner with multiple analyses.
            
        Returns:
            LensComparison with consensus and divergence analysis.
        """
        if not lens_result.analyses:
            return self._empty_comparison()
        
        # Find consensus stocks
        consensus_stocks = self._find_consensus_stocks(lens_result.analyses)
        
        # Find unique stocks per lens
        unique_stocks = self._find_unique_stocks(lens_result.analyses, consensus_stocks)
        
        # Find common themes
        common_themes = self._find_common_themes(lens_result.analyses)
        
        # Analyze divergences
        divergences = self._analyze_divergences(lens_result.analyses)
        
        # Generate synthesis
        synthesis = self._generate_synthesis(
            lens_result.analyses,
            consensus_stocks,
            common_themes,
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            lens_result.analyses,
            consensus_stocks,
        )
        
        # Count unique tickers
        all_tickers = set()
        for analysis in lens_result.analyses:
            for stock in analysis.stocks:
                all_tickers.add(stock.ticker)
        
        return LensComparison(
            consensus_stocks=consensus_stocks,
            unique_stocks=unique_stocks,
            divergences=divergences,
            common_themes=common_themes,
            synthesis=synthesis,
            confidence=confidence,
            total_unique_tickers=len(all_tickers),
        )
    
    def _find_consensus_stocks(
        self,
        analyses: List[LensAnalysis],
    ) -> List[ConsensusStock]:
        """Find stocks that appear in multiple analyses."""
        # Count ticker occurrences
        ticker_count: Counter = Counter()
        ticker_info: Dict[str, Dict] = {}
        
        for analysis in analyses:
            for stock in analysis.stocks:
                ticker_count[stock.ticker] += 1
                
                if stock.ticker not in ticker_info:
                    ticker_info[stock.ticker] = {
                        "company": stock.company,
                        "lenses": [],
                        "convictions": [],
                        "rationales": {},
                    }
                
                ticker_info[stock.ticker]["lenses"].append(analysis.lens.name)
                ticker_info[stock.ticker]["convictions"].append(stock.conviction)
                ticker_info[stock.ticker]["rationales"][analysis.lens.name] = stock.rationale
        
        # Build consensus stocks (2+ lenses)
        consensus = []
        for ticker, count in ticker_count.most_common():
            if count >= 2:
                info = ticker_info[ticker]
                avg_conviction = self._average_conviction(info["convictions"])
                
                consensus.append(ConsensusStock(
                    ticker=ticker,
                    company=info["company"],
                    lens_count=count,
                    lenses=info["lenses"],
                    avg_conviction=avg_conviction,
                    rationales=info["rationales"],
                ))
        
        return consensus
    
    def _find_unique_stocks(
        self,
        analyses: List[LensAnalysis],
        consensus: List[ConsensusStock],
    ) -> Dict[str, List[StockPick]]:
        """Find stocks unique to each lens."""
        consensus_tickers = {s.ticker for s in consensus}
        unique: Dict[str, List[StockPick]] = {}
        
        for analysis in analyses:
            lens_name = analysis.lens.name
            unique_stocks = [
                s for s in analysis.stocks
                if s.ticker not in consensus_tickers
            ]
            if unique_stocks:
                unique[lens_name] = unique_stocks
        
        return unique
    
    def _find_common_themes(
        self,
        analyses: List[LensAnalysis],
    ) -> List[str]:
        """Find themes that appear across multiple lenses."""
        theme_count: Counter = Counter()
        
        for analysis in analyses:
            for theme in analysis.themes:
                # Normalize theme for comparison
                normalized = theme.lower().strip()
                theme_count[theme] += 1
        
        # Return themes appearing in 2+ analyses
        common = [
            theme for theme, count in theme_count.most_common()
            if count >= 2
        ]
        
        return common[:5]  # Top 5 common themes
    
    def _analyze_divergences(
        self,
        analyses: List[LensAnalysis],
    ) -> List[LensDivergence]:
        """Analyze where lenses disagree."""
        divergences = []
        
        # Check conviction levels
        convictions = {a.lens.name: a.conviction for a in analyses}
        unique_convictions = set(convictions.values())
        if len(unique_convictions) > 1:
            divergences.append(LensDivergence(
                topic="Overall conviction level",
                perspectives=convictions,
            ))
        
        # Check time horizons
        time_horizons = {a.lens.name: a.time_horizon for a in analyses}
        unique_horizons = set(time_horizons.values())
        if len(unique_horizons) > 1:
            divergences.append(LensDivergence(
                topic="Investment time horizon",
                perspectives=time_horizons,
            ))
        
        # Check key risks
        all_risks: Set[str] = set()
        for analysis in analyses:
            all_risks.update(analysis.risks)
        
        if len(all_risks) > 0:
            risk_perspectives = {
                a.lens.name: ", ".join(a.risks[:2]) if a.risks else "No specific risks"
                for a in analyses
            }
            divergences.append(LensDivergence(
                topic="Key risks identified",
                perspectives=risk_perspectives,
            ))
        
        return divergences
    
    def _generate_synthesis(
        self,
        analyses: List[LensAnalysis],
        consensus: List[ConsensusStock],
        common_themes: List[str],
    ) -> str:
        """Generate a unified synthesis of all analyses."""
        parts = []
        
        # Consensus summary
        if consensus:
            top_picks = [s.ticker for s in consensus[:3]]
            parts.append(f"Consensus picks: {', '.join(top_picks)}")
        
        # Theme summary
        if common_themes:
            parts.append(f"Common themes: {', '.join(common_themes[:3])}")
        
        # Key insights
        insights = [a.key_insight for a in analyses if a.key_insight]
        if insights:
            parts.append(f"Key insight: {insights[0]}")
        
        return " | ".join(parts) if parts else "Insufficient data for synthesis"
    
    def _calculate_confidence(
        self,
        analyses: List[LensAnalysis],
        consensus: List[ConsensusStock],
    ) -> str:
        """Calculate overall confidence level."""
        if not analyses:
            return "low"
        
        # Factors that increase confidence
        score = 0
        
        # More lenses = more confidence
        score += min(len(analyses), 5)
        
        # Consensus picks = more confidence
        if consensus:
            score += min(len(consensus), 3) * 2
        
        # Strong consensus = more confidence
        strong_consensus = [s for s in consensus if s.lens_count >= 3]
        score += len(strong_consensus) * 2
        
        # Average conviction across analyses
        convictions = [a.conviction for a in analyses]
        high_conviction = sum(1 for c in convictions if c == "high")
        score += high_conviction
        
        if score >= 12:
            return "high"
        elif score >= 6:
            return "medium"
        else:
            return "low"
    
    def _average_conviction(self, convictions: List[str]) -> str:
        """Calculate average conviction level."""
        values = {"high": 3, "medium": 2, "low": 1}
        avg = sum(values.get(c, 2) for c in convictions) / len(convictions)
        
        if avg >= 2.5:
            return "high"
        elif avg >= 1.5:
            return "medium"
        else:
            return "low"
    
    def _empty_comparison(self) -> LensComparison:
        """Return an empty comparison result."""
        return LensComparison(
            consensus_stocks=[],
            unique_stocks={},
            divergences=[],
            common_themes=[],
            synthesis="No analyses to compare",
            confidence="low",
            total_unique_tickers=0,
        )

