"""
Lens Runner

Runs transcript analysis through multiple investor lens frameworks.
Supports parallel execution and individual lens analysis.
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from ..llm_client import LLMClient, get_client
from ...prompts import PromptLoader
from .models import (
    InvestorLens,
    LensAnalysis,
    StockPick,
    INVESTOR_LENSES,
    get_lens,
    list_lenses,
    get_all_lenses,
)

__all__ = ["LensRunner", "LensResult"]

logger = logging.getLogger(__name__)

FALLBACK_SYSTEM_PROMPT = """You are a senior investment analyst applying a specific investor's framework.
Analyze the transcript through this lens and provide investment recommendations.
Always respond in valid JSON format."""

FALLBACK_USER_PROMPT = """Analyze this podcast transcript through the lens of {investor_name}.

{investor_name}'s Framework:
- Focus Areas: {focus_areas}
- Key Questions: {key_questions}

Apply this framework to identify:
1. Investment themes that align with {investor_name}'s approach
2. Specific stock recommendations with rationale
3. Risks and opportunities from this perspective
4. Key insight this investor would highlight

Transcript:
---
{transcript}
---

Respond in JSON format only:
{{
  "themes": ["Theme 1", "Theme 2"],
  "stocks": [
    {{
      "ticker": "NVDA",
      "company": "NVIDIA Corporation",
      "exchange": "NASDAQ",
      "rationale": "Why {investor_name} would like this stock",
      "conviction": "high/medium/low"
    }}
  ],
  "key_insight": "The most important insight from {investor_name}'s perspective",
  "risks": ["Risk 1", "Risk 2"],
  "opportunities": ["Opportunity 1", "Opportunity 2"],
  "time_horizon": "X months/years",
  "conviction": "high/medium/low",
  "supporting_quotes": ["Exact quote from transcript"]
}}"""


@dataclass
class LensResult:
    """Result of running multiple lens analyses.
    
    Attributes:
        analyses: List of LensAnalysis results.
        total_cost_usd: Total LLM API cost.
    """
    analyses: List[LensAnalysis]
    total_cost_usd: float = 0.0
    
    @property
    def num_lenses(self) -> int:
        return len(self.analyses)
    
    @property
    def all_tickers(self) -> List[str]:
        """Get all unique tickers across all lenses."""
        tickers = set()
        for analysis in self.analyses:
            for stock in analysis.stocks:
                tickers.add(stock.ticker)
        return sorted(tickers)
    
    def get_analysis(self, lens_key: str) -> Optional[LensAnalysis]:
        """Get analysis for a specific lens."""
        for analysis in self.analyses:
            if analysis.lens.key == lens_key:
                return analysis
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "num_lenses": self.num_lenses,
            "all_tickers": self.all_tickers,
            "total_cost_usd": self.total_cost_usd,
            "analyses": [a.to_dict() for a in self.analyses],
        }


class LensRunner:
    """Runs transcript through multiple investor lens frameworks.
    
    Supports both sequential and parallel execution of multiple lenses.
    
    Example:
        >>> runner = LensRunner()
        >>> result = runner.run_all_lenses(transcript)
        >>> for analysis in result.analyses:
        ...     print(f"{analysis.lens.name}: {analysis.key_insight}")
        ...     for stock in analysis.stocks:
        ...         print(f"  ${stock.ticker} ({stock.conviction})")
    """
    
    def __init__(
        self,
        client: Optional[LLMClient] = None,
        provider: str = "openrouter",
        model: Optional[str] = None,
        prompt_loader: Optional[PromptLoader] = None,
    ):
        """Initialize lens runner.
        
        Args:
            client: Pre-configured LLM client.
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
        self._template_cache: Dict[str, Any] = {}
    
    def _get_template(self, lens: InvestorLens):
        """Load prompt template for a lens (cached)."""
        if lens.key not in self._template_cache:
            try:
                self._template_cache[lens.key] = self.prompt_loader.load(lens.prompt_path)
            except FileNotFoundError:
                logger.warning(f"Prompt file not found: {lens.prompt_path}, using fallback")
                self._template_cache[lens.key] = None
        return self._template_cache[lens.key]
    
    def run_lens(
        self,
        transcript: str,
        lens_key: str,
        time_horizon: str = "6-18 months",
    ) -> LensAnalysis:
        """Run analysis through a single investor lens.
        
        Args:
            transcript: Transcript text to analyze.
            lens_key: Key of the lens to use (e.g., "gavin_baker").
            time_horizon: Investment time horizon.
            
        Returns:
            LensAnalysis with results.
            
        Raises:
            ValueError: If lens_key is not found.
        """
        lens = get_lens(lens_key)
        if not lens:
            available = ", ".join(list_lenses())
            raise ValueError(f"Unknown lens: {lens_key}. Available: {available}")
        
        return self._run_single_lens(transcript, lens, time_horizon)
    
    def run_lenses(
        self,
        transcript: str,
        lens_keys: List[str],
        time_horizon: str = "6-18 months",
        parallel: bool = True,
        max_workers: int = 3,
    ) -> LensResult:
        """Run analysis through multiple investor lenses.
        
        Args:
            transcript: Transcript text to analyze.
            lens_keys: List of lens keys to use.
            time_horizon: Investment time horizon.
            parallel: Whether to run lenses in parallel.
            max_workers: Maximum parallel workers.
            
        Returns:
            LensResult with all analyses.
        """
        lenses = []
        for key in lens_keys:
            lens = get_lens(key)
            if lens:
                lenses.append(lens)
            else:
                logger.warning(f"Unknown lens: {key}, skipping")
        
        if not lenses:
            return LensResult(analyses=[], total_cost_usd=0.0)
        
        if parallel and len(lenses) > 1:
            return self._run_parallel(transcript, lenses, time_horizon, max_workers)
        else:
            return self._run_sequential(transcript, lenses, time_horizon)
    
    def run_all_lenses(
        self,
        transcript: str,
        time_horizon: str = "6-18 months",
        parallel: bool = True,
        max_workers: int = 3,
    ) -> LensResult:
        """Run analysis through all available investor lenses.
        
        Args:
            transcript: Transcript text to analyze.
            time_horizon: Investment time horizon.
            parallel: Whether to run lenses in parallel.
            max_workers: Maximum parallel workers.
            
        Returns:
            LensResult with all analyses.
        """
        lenses = get_all_lenses()
        
        if parallel and len(lenses) > 1:
            return self._run_parallel(transcript, lenses, time_horizon, max_workers)
        else:
            return self._run_sequential(transcript, lenses, time_horizon)
    
    def _run_sequential(
        self,
        transcript: str,
        lenses: List[InvestorLens],
        time_horizon: str,
    ) -> LensResult:
        """Run lenses sequentially."""
        analyses = []
        total_cost = 0.0
        
        for lens in lenses:
            logger.info(f"Running lens: {lens.name}")
            try:
                analysis = self._run_single_lens(transcript, lens, time_horizon)
                analyses.append(analysis)
                total_cost += analysis.cost_usd
            except Exception as e:
                logger.error(f"Lens {lens.name} failed: {e}")
                continue
        
        return LensResult(analyses=analyses, total_cost_usd=total_cost)
    
    def _run_parallel(
        self,
        transcript: str,
        lenses: List[InvestorLens],
        time_horizon: str,
        max_workers: int,
    ) -> LensResult:
        """Run lenses in parallel."""
        analyses = []
        total_cost = 0.0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_lens = {
                executor.submit(
                    self._run_single_lens, transcript, lens, time_horizon
                ): lens
                for lens in lenses
            }
            
            for future in as_completed(future_to_lens):
                lens = future_to_lens[future]
                try:
                    analysis = future.result()
                    analyses.append(analysis)
                    total_cost += analysis.cost_usd
                    logger.info(f"Completed lens: {lens.name}")
                except Exception as e:
                    logger.error(f"Lens {lens.name} failed: {e}")
                    continue
        
        return LensResult(analyses=analyses, total_cost_usd=total_cost)
    
    def _run_single_lens(
        self,
        transcript: str,
        lens: InvestorLens,
        time_horizon: str,
    ) -> LensAnalysis:
        """Run analysis through a single lens."""
        template = self._get_template(lens)
        
        if template:
            system_prompt, user_prompt = template.format(
                transcript=transcript,
                investor_name=lens.name,
                time_horizon=time_horizon,
            )
        else:
            system_prompt = FALLBACK_SYSTEM_PROMPT
            user_prompt = FALLBACK_USER_PROMPT.format(
                transcript=transcript,
                investor_name=lens.name,
                focus_areas=", ".join(lens.focus_areas),
                key_questions=", ".join(lens.key_questions),
            )
        
        temperature = 0.5
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
            logger.error(f"Failed to parse response for {lens.name}: {e}")
            return self._empty_analysis(lens, response.cost_usd)
        
        try:
            # Parse stocks
            stocks = []
            for item in data.get("stocks", []):
                stocks.append(StockPick(
                    ticker=item.get("ticker", "").upper(),
                    company=item.get("company", ""),
                    exchange=item.get("exchange", "").upper(),
                    rationale=item.get("rationale", ""),
                    conviction=item.get("conviction", "medium"),
                ))
            
            return LensAnalysis(
                lens=lens,
                themes=data.get("themes", []),
                stocks=stocks,
                key_insight=data.get("key_insight", ""),
                risks=data.get("risks", []),
                opportunities=data.get("opportunities", []),
                time_horizon=data.get("time_horizon", time_horizon),
                conviction=data.get("conviction", "medium"),
                supporting_quotes=data.get("supporting_quotes", []),
                cost_usd=response.cost_usd,
            )
            
        except Exception as e:
            logger.error(f"Failed to parse analysis for {lens.name}: {e}")
            return self._empty_analysis(lens, response.cost_usd)
    
    def _empty_analysis(self, lens: InvestorLens, cost: float) -> LensAnalysis:
        """Return an empty analysis result."""
        return LensAnalysis(
            lens=lens,
            themes=[],
            stocks=[],
            key_insight="Analysis failed",
            risks=[],
            opportunities=[],
            time_horizon="",
            conviction="low",
            supporting_quotes=[],
            cost_usd=cost,
        )
    
    @staticmethod
    def available_lenses() -> List[str]:
        """List available lens keys."""
        return list_lenses()

