"""
Investment Thesis Extractor

Extracts investment themes and stock recommendations from podcast transcripts,
each backed by verbatim quotes and validated for US exchanges.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from .llm_client import LLMClient, get_client
from .models import TranscriptChunk

__all__ = [
    "InvestmentThesisExtractor",
    "StockRecommendation", 
    "InvestmentTheme",
    "InvestmentThesisResult",
]

logger = logging.getLogger(__name__)

INVESTMENT_THESIS_PROMPT = """You are a senior equity research analyst. Based on this podcast transcript,
identify investment themes for US public markets over the next 6-18 months.

Requirements:
1. Each theme must be supported by content discussed in the podcast
2. Each theme needs a VERBATIM supporting quote
3. Only recommend stocks traded on NYSE, NASDAQ, or AMEX (NO OTC/Pink Sheets)
4. For each theme, recommend 2-3 specific stocks with rationale

Transcript:
---
{transcript}
---

Respond in JSON format only:
{{
  "themes": [
    {{
      "industry": "Broad industry (e.g., 'Technology')",
      "sub_industry": "Specific sub-sector (e.g., 'AI Infrastructure')",
      "thesis": "Why this sector will outperform",
      "supporting_quote": "EXACT quote from transcript",
      "catalysts": ["catalyst1", "catalyst2"],
      "stocks": [
        {{
          "ticker": "NVDA",
          "company": "NVIDIA Corporation",
          "exchange": "NASDAQ",
          "rationale": "Why this specific stock"
        }}
      ]
    }}
  ]
}}"""

SYSTEM_PROMPT = """You are a senior equity research analyst at a major investment bank.
Provide professional-grade investment analysis backed by specific transcript content.
Only recommend stocks on major US exchanges (NYSE, NASDAQ, AMEX).
Always respond in valid JSON format."""

# Valid US exchanges
VALID_EXCHANGES = {"NYSE", "NASDAQ", "AMEX", "NYSEARCA", "BATS"}


@dataclass
class StockRecommendation:
    """A stock recommendation within a theme.
    
    Attributes:
        ticker: Stock ticker symbol.
        company: Full company name.
        exchange: Stock exchange (NYSE, NASDAQ, AMEX).
        rationale: Why this stock fits the theme.
    """
    ticker: str
    company: str
    exchange: str
    rationale: str
    
    @property
    def is_valid_exchange(self) -> bool:
        """Check if exchange is a valid US exchange."""
        return self.exchange.upper() in VALID_EXCHANGES
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "ticker": self.ticker,
            "company": self.company,
            "exchange": self.exchange,
            "rationale": self.rationale,
        }


@dataclass
class InvestmentTheme:
    """An investment theme with stock recommendations.
    
    Attributes:
        industry: Broad industry category.
        sub_industry: Specific sub-sector.
        thesis: Investment thesis/rationale.
        supporting_quote: Verbatim quote from transcript.
        catalysts: List of potential catalysts.
        stocks: Stock recommendations for this theme.
    """
    industry: str
    sub_industry: str
    thesis: str
    supporting_quote: str
    catalysts: List[str]
    stocks: List[StockRecommendation]
    
    @property
    def valid_stocks(self) -> List[StockRecommendation]:
        """Return only stocks on valid US exchanges."""
        return [s for s in self.stocks if s.is_valid_exchange]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "industry": self.industry,
            "sub_industry": self.sub_industry,
            "thesis": self.thesis,
            "supporting_quote": self.supporting_quote,
            "catalysts": self.catalysts,
            "stocks": [s.to_dict() for s in self.stocks],
        }


@dataclass
class InvestmentThesisResult:
    """Result of investment thesis extraction.
    
    Attributes:
        themes: List of investment themes.
        cost_usd: LLM API cost.
    """
    themes: List[InvestmentTheme]
    cost_usd: float = 0.0
    
    @property
    def num_themes(self) -> int:
        return len(self.themes)
    
    @property
    def all_tickers(self) -> List[str]:
        """Get all unique tickers across themes."""
        tickers = set()
        for theme in self.themes:
            for stock in theme.stocks:
                tickers.add(stock.ticker)
        return sorted(tickers)
    
    @property
    def valid_tickers(self) -> List[str]:
        """Get only tickers on valid US exchanges."""
        tickers = set()
        for theme in self.themes:
            for stock in theme.valid_stocks:
                tickers.add(stock.ticker)
        return sorted(tickers)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "num_themes": self.num_themes,
            "all_tickers": self.all_tickers,
            "cost_usd": self.cost_usd,
            "themes": [t.to_dict() for t in self.themes],
        }


class InvestmentThesisExtractor:
    """Extracts investment themes and stock picks from transcripts.
    
    Example:
        >>> extractor = InvestmentThesisExtractor()
        >>> result = extractor.extract(transcript_text)
        >>> for theme in result.themes:
        ...     print(f"📈 {theme.industry}: {theme.sub_industry}")
        ...     for stock in theme.stocks:
        ...         print(f"   ${stock.ticker} - {stock.company}")
    """
    
    def __init__(
        self,
        client: Optional[LLMClient] = None,
        provider: str = "openrouter",
        model: Optional[str] = None,
    ):
        """Initialize extractor.
        
        Args:
            client: Pre-configured LLM client.
            provider: LLM provider.
            model: Model to use.
        """
        if client:
            self.client = client
        else:
            kwargs = {"model": model} if model else {}
            self.client = get_client(provider, **kwargs)
    
    def extract(
        self,
        transcript: str,
        num_themes: int = 3,
    ) -> InvestmentThesisResult:
        """Extract investment themes from transcript.
        
        Args:
            transcript: Full transcript text.
            num_themes: Target number of themes.
            
        Returns:
            InvestmentThesisResult with themes and stocks.
        """
        prompt = INVESTMENT_THESIS_PROMPT.format(transcript=transcript)
        
        logger.info("Extracting investment themes...")
        
        response = self.client.complete(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.5,  # Balanced for accuracy
            max_tokens=3000,
        )
        
        try:
            data = response.parse_json()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse response: {e}")
            return InvestmentThesisResult(themes=[], cost_usd=response.cost_usd)
        
        themes = []
        for item in data.get("themes", []):
            try:
                stocks = []
                for stock_data in item.get("stocks", []):
                    stock = StockRecommendation(
                        ticker=stock_data.get("ticker", "").upper(),
                        company=stock_data.get("company", ""),
                        exchange=stock_data.get("exchange", "").upper(),
                        rationale=stock_data.get("rationale", ""),
                    )
                    stocks.append(stock)
                
                theme = InvestmentTheme(
                    industry=item.get("industry", ""),
                    sub_industry=item.get("sub_industry", ""),
                    thesis=item.get("thesis", ""),
                    supporting_quote=item.get("supporting_quote", ""),
                    catalysts=item.get("catalysts", []),
                    stocks=stocks,
                )
                themes.append(theme)
            except Exception as e:
                logger.warning(f"Failed to parse theme: {e}")
                continue
        
        # Log warning for invalid exchanges
        for theme in themes:
            invalid = [s for s in theme.stocks if not s.is_valid_exchange]
            if invalid:
                tickers = ", ".join(s.ticker for s in invalid)
                logger.warning(f"Invalid exchanges for: {tickers}")
        
        logger.info(
            f"Extracted {len(themes)} themes with {len(set(s.ticker for t in themes for s in t.stocks))} "
            f"unique tickers (${response.cost_usd:.4f})"
        )
        
        return InvestmentThesisResult(themes=themes, cost_usd=response.cost_usd)
    
    def extract_from_chunks(
        self,
        chunks: List[TranscriptChunk],
        max_words: int = 5000,
    ) -> InvestmentThesisResult:
        """Extract themes from transcript chunks.
        
        Args:
            chunks: List of transcript chunks.
            max_words: Maximum words to include.
            
        Returns:
            InvestmentThesisResult with themes.
        """
        combined_text = []
        total_words = 0
        
        for chunk in chunks:
            if total_words + chunk.word_count > max_words:
                break
            combined_text.append(chunk.text)
            total_words += chunk.word_count
        
        transcript = " ".join(combined_text)
        return self.extract(transcript)
