"""
Analysis module: LLM-powered extraction of insights from transcripts.
Handles topic extraction, business ideas, and investment theses.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import json
import logging
import re
from anthropic import Anthropic

logger = logging.getLogger(__name__)


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class Quote:
    """A verbatim quote from the transcript."""
    text: str
    speaker: Optional[str] = None
    timestamp_seconds: Optional[float] = None
    verified: bool = False  # Set to True after validation


@dataclass
class TopicSegment:
    """Analysis of a 3-minute transcript segment."""
    segment_index: int
    start_seconds: int
    end_seconds: int
    transcript_chunk: str
    topics: List[str]
    summary: str
    quote: Quote


@dataclass
class BusinessIdea:
    """A 24-hour business idea derived from the podcast."""
    index: int
    title: str
    description: str
    supporting_quote: Quote
    plan_hours_1_4: str
    plan_hours_5_12: str
    plan_hours_13_24: str
    estimated_cost: str
    target_market: str


@dataclass
class StockPick:
    """A stock recommendation."""
    ticker: str
    company_name: str
    exchange: str
    rationale: str
    is_validated: bool = False
    market_cap_billions: Optional[float] = None


@dataclass
class InvestmentThesis:
    """An investment theme with supporting stocks."""
    industry: str
    sub_industry: str
    thesis_summary: str
    supporting_quote: Quote
    catalysts: List[str]
    stocks: List[StockPick]
    time_horizon: str = "6-18 months"


@dataclass
class FullAnalysis:
    """Complete analysis output for a podcast."""
    video_id: str
    title: str
    segments: List[TopicSegment]
    business_ideas: List[BusinessIdea]
    investment_theses: List[InvestmentThesis]
    total_analysis_cost: float = 0.0


# =============================================================================
# TRANSCRIPT SEGMENTER
# =============================================================================

class TranscriptSegmenter:
    """Split transcript into time-based segments for analysis."""
    
    def __init__(self, segment_duration_seconds: int = 180):
        self.segment_duration = segment_duration_seconds
    
    def segment(
        self, 
        full_text: str, 
        segments: List[Any],  # TranscriptSegment from transcription
        total_duration: float
    ) -> List[Dict[str, Any]]:
        """
        Split transcript into fixed-duration chunks.
        
        Returns list of dicts with:
        - segment_index: int
        - start_seconds: int
        - end_seconds: int
        - text: str
        """
        if not segments:
            # Fallback: split by estimated time based on word count
            words = full_text.split()
            words_per_second = len(words) / total_duration if total_duration > 0 else 2.5
            words_per_segment = int(words_per_second * self.segment_duration)
            
            chunks = []
            for i in range(0, len(words), words_per_segment):
                chunk_words = words[i:i + words_per_segment]
                segment_idx = i // words_per_segment
                chunks.append({
                    'segment_index': segment_idx,
                    'start_seconds': segment_idx * self.segment_duration,
                    'end_seconds': (segment_idx + 1) * self.segment_duration,
                    'text': ' '.join(chunk_words)
                })
            return chunks
        
        # Use actual timestamps from transcription
        chunks = []
        current_chunk = []
        current_start = 0
        segment_idx = 0
        
        for seg in segments:
            current_chunk.append(seg.text)
            
            # Check if we've exceeded segment duration
            if seg.end_seconds >= (segment_idx + 1) * self.segment_duration:
                chunks.append({
                    'segment_index': segment_idx,
                    'start_seconds': current_start,
                    'end_seconds': int(seg.end_seconds),
                    'text': ' '.join(current_chunk)
                })
                current_chunk = []
                current_start = int(seg.end_seconds)
                segment_idx += 1
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append({
                'segment_index': segment_idx,
                'start_seconds': current_start,
                'end_seconds': int(segments[-1].end_seconds) if segments else current_start + self.segment_duration,
                'text': ' '.join(current_chunk)
            })
        
        return chunks


# =============================================================================
# QUOTE VALIDATOR
# =============================================================================

class QuoteValidator:
    """Validate that quotes actually exist in the transcript."""
    
    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold
    
    def validate(self, quote: str, transcript: str) -> bool:
        """
        Check if quote exists in transcript.
        Uses exact match first, then fuzzy matching.
        """
        # Normalize
        quote_clean = self._normalize(quote)
        transcript_clean = self._normalize(transcript)
        
        # 1. Exact match
        if quote_clean in transcript_clean:
            return True
        
        # 2. Fuzzy match with sliding window
        try:
            from rapidfuzz import fuzz
            
            quote_words = quote_clean.split()
            transcript_words = transcript_clean.split()
            window_size = len(quote_words)
            
            for i in range(len(transcript_words) - window_size + 1):
                window = ' '.join(transcript_words[i:i + window_size])
                similarity = fuzz.ratio(quote_clean, window) / 100
                if similarity >= self.threshold:
                    return True
        except ImportError:
            # Fallback: simple substring check with tolerance
            words = quote_clean.split()
            if len(words) >= 3:
                # Check if at least 70% of words appear in sequence
                for i in range(len(words) - 2):
                    phrase = ' '.join(words[i:i+3])
                    if phrase in transcript_clean:
                        return True
        
        return False
    
    def find_closest_match(self, quote: str, transcript: str) -> Optional[str]:
        """Find the closest matching text in transcript."""
        try:
            from rapidfuzz import fuzz, process
            
            quote_clean = self._normalize(quote)
            transcript_words = self._normalize(transcript).split()
            window_size = len(quote_clean.split())
            
            best_match = None
            best_score = 0
            
            for i in range(len(transcript_words) - window_size + 1):
                window = ' '.join(transcript_words[i:i + window_size])
                score = fuzz.ratio(quote_clean, window)
                if score > best_score:
                    best_score = score
                    best_match = window
            
            return best_match if best_score >= self.threshold * 100 else None
        except ImportError:
            return None
    
    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize text for comparison."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        return text.strip()


# =============================================================================
# TICKER VALIDATOR
# =============================================================================

class TickerValidator:
    """Validate US stock tickers."""
    
    VALID_EXCHANGES = {'NYQ', 'NMS', 'NGM', 'ASE', 'NYSE', 'NASDAQ', 'AMEX'}
    
    def validate(self, ticker: str) -> Dict[str, Any]:
        """
        Validate a stock ticker.
        
        Returns dict with:
        - valid: bool
        - ticker: str
        - company: str
        - exchange: str
        - market_cap: float
        - is_otc: bool
        - error: Optional[str]
        """
        try:
            import yfinance as yf
            
            stock = yf.Ticker(ticker.upper())
            info = stock.info
            
            if not info or info.get('regularMarketPrice') is None:
                return {
                    'valid': False,
                    'ticker': ticker,
                    'error': 'Ticker not found or no market data'
                }
            
            exchange = info.get('exchange', '')
            is_otc = exchange in {'PNK', 'OTC', 'OTCQB', 'OTCQX'}
            is_valid_exchange = exchange in self.VALID_EXCHANGES or \
                               any(ex in exchange.upper() for ex in ['NYSE', 'NASDAQ', 'AMEX'])
            
            return {
                'valid': is_valid_exchange and not is_otc,
                'ticker': ticker.upper(),
                'company': info.get('shortName', info.get('longName', '')),
                'exchange': exchange,
                'market_cap': info.get('marketCap', 0) / 1e9 if info.get('marketCap') else None,
                'is_otc': is_otc,
                'error': 'OTC stock not allowed' if is_otc else None
            }
            
        except Exception as e:
            return {
                'valid': False,
                'ticker': ticker,
                'error': str(e)
            }
    
    def validate_batch(self, tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        """Validate multiple tickers."""
        return {ticker: self.validate(ticker) for ticker in tickers}


# =============================================================================
# LLM ANALYZER
# =============================================================================

class PodcastAnalyzer:
    """Main analyzer class using Claude for LLM-powered extraction."""
    
    def __init__(self, api_key: str = None, model: str = None):
        from config.settings import get_settings
        settings = get_settings()
        
        self.client = Anthropic(api_key=api_key or settings.anthropic.api_key)
        self.model = model or settings.anthropic.model
        self.quote_validator = QuoteValidator()
        self.ticker_validator = TickerValidator()
        self.total_cost = 0.0
    
    def _call_llm(self, system: str, user: str, max_tokens: int = 4096) -> str:
        """Make LLM API call and track cost."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": user}],
            system=system
        )
        
        # Estimate cost (Sonnet pricing)
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = (input_tokens * 0.003 + output_tokens * 0.015) / 1000
        self.total_cost += cost
        
        return response.content[0].text
    
    def _parse_json(self, text: str) -> Dict:
        """Extract and parse JSON from LLM response."""
        # Try to find JSON in response
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Try parsing entire response
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.debug(f"Response was: {text[:500]}")
            raise ValueError(f"Could not parse LLM response as JSON: {e}")
    
    def analyze_segment(self, segment: Dict, full_transcript: str) -> TopicSegment:
        """Analyze a single 3-minute segment."""
        system = """You are analyzing a podcast transcript segment. Extract key information.
        
IMPORTANT: The quote MUST be VERBATIM text from the transcript. Do not paraphrase or modify."""
        
        user = f"""Analyze this podcast segment and extract:
1. KEY TOPICS: 2-4 main topics discussed
2. SUMMARY: 2-3 sentence summary
3. DIRECT QUOTE: The single most insightful quote (MUST be exact text from segment)

Segment [{segment['segment_index']}]: {segment['start_seconds']//60}:{segment['start_seconds']%60:02d} - {segment['end_seconds']//60}:{segment['end_seconds']%60:02d}
---
{segment['text']}
---

Respond ONLY with valid JSON:
{{"topics": ["topic1", "topic2"], "summary": "...", "quote": {{"text": "exact verbatim quote", "speaker": "name or Unknown"}}}}"""
        
        response = self._call_llm(system, user, max_tokens=1000)
        data = self._parse_json(response)
        
        quote = Quote(
            text=data['quote']['text'],
            speaker=data['quote'].get('speaker'),
            verified=self.quote_validator.validate(data['quote']['text'], segment['text'])
        )
        
        # If quote not verified, try to find closest match
        if not quote.verified:
            closest = self.quote_validator.find_closest_match(data['quote']['text'], segment['text'])
            if closest:
                quote.text = closest
                quote.verified = True
        
        return TopicSegment(
            segment_index=segment['segment_index'],
            start_seconds=segment['start_seconds'],
            end_seconds=segment['end_seconds'],
            transcript_chunk=segment['text'],
            topics=data['topics'],
            summary=data['summary'],
            quote=quote
        )
    
    def extract_business_ideas(self, transcript: str) -> List[BusinessIdea]:
        """Extract 3 business ideas that can be started in 24 hours."""
        system = """You are a startup strategist. Extract actionable business ideas from podcasts.

CRITICAL: Each supporting_quote MUST be VERBATIM text from the transcript. Do not paraphrase."""
        
        user = f"""Based on this podcast transcript, identify 3 business ideas that could be started within 24 hours.

Requirements:
1. Each idea MUST be directly inspired by content discussed in the podcast
2. Each idea MUST include a VERBATIM supporting quote (exact words from transcript)
3. Ideas should be actionable within 24 hours with minimal capital
4. Focus on: services, digital products, arbitrage, or consulting

Transcript:
---
{transcript[:50000]}
---

Respond ONLY with valid JSON:
{{
  "ideas": [
    {{
      "title": "Business name/concept",
      "description": "What it is and why it works",
      "supporting_quote": "EXACT quote from transcript",
      "plan_hours_1_4": "Immediate actions",
      "plan_hours_5_12": "Build/setup phase",
      "plan_hours_13_24": "Launch/test phase",
      "estimated_cost": "$X-$Y",
      "target_market": "Who you're selling to"
    }}
  ]
}}"""
        
        response = self._call_llm(system, user, max_tokens=3000)
        data = self._parse_json(response)
        
        ideas = []
        for i, idea_data in enumerate(data.get('ideas', [])[:3]):
            quote = Quote(
                text=idea_data['supporting_quote'],
                verified=self.quote_validator.validate(idea_data['supporting_quote'], transcript)
            )
            
            ideas.append(BusinessIdea(
                index=i + 1,
                title=idea_data['title'],
                description=idea_data['description'],
                supporting_quote=quote,
                plan_hours_1_4=idea_data.get('plan_hours_1_4', ''),
                plan_hours_5_12=idea_data.get('plan_hours_5_12', ''),
                plan_hours_13_24=idea_data.get('plan_hours_13_24', ''),
                estimated_cost=idea_data.get('estimated_cost', 'TBD'),
                target_market=idea_data.get('target_market', '')
            ))
        
        return ideas
    
    def extract_investment_theses(self, transcript: str) -> List[InvestmentThesis]:
        """Extract 5 investment themes with 3 stocks each."""
        system = """You are a senior equity research analyst. Extract investment themes from podcasts.

CRITICAL RULES:
1. Supporting quotes MUST be VERBATIM from the transcript
2. Only recommend stocks on NYSE, NASDAQ, or AMEX (NO OTC/Pink Sheets)
3. Focus on liquid, established companies"""
        
        user = f"""Based on this podcast, identify 5 investment themes for US public markets (6-18 month horizon).

Requirements:
1. Each theme needs a VERBATIM supporting quote from the podcast
2. Only recommend stocks traded on NYSE, NASDAQ, or AMEX (NO OTC)
3. For each theme, recommend 3 specific stocks with rationale

Transcript:
---
{transcript[:50000]}
---

Respond ONLY with valid JSON:
{{
  "themes": [
    {{
      "industry": "Broad industry",
      "sub_industry": "Specific sub-sector",
      "thesis": "Why this sector will outperform",
      "supporting_quote": "EXACT quote from transcript",
      "catalysts": ["catalyst1", "catalyst2"],
      "stocks": [
        {{"ticker": "NVDA", "company": "NVIDIA Corporation", "exchange": "NASDAQ", "rationale": "Why this stock"}}
      ]
    }}
  ]
}}"""
        
        response = self._call_llm(system, user, max_tokens=4000)
        data = self._parse_json(response)
        
        theses = []
        for theme_data in data.get('themes', [])[:5]:
            quote = Quote(
                text=theme_data['supporting_quote'],
                verified=self.quote_validator.validate(theme_data['supporting_quote'], transcript)
            )
            
            # Validate stocks
            stocks = []
            for stock_data in theme_data.get('stocks', [])[:3]:
                validation = self.ticker_validator.validate(stock_data['ticker'])
                
                stocks.append(StockPick(
                    ticker=stock_data['ticker'].upper(),
                    company_name=validation.get('company') or stock_data.get('company', ''),
                    exchange=validation.get('exchange') or stock_data.get('exchange', ''),
                    rationale=stock_data.get('rationale', ''),
                    is_validated=validation.get('valid', False),
                    market_cap_billions=validation.get('market_cap')
                ))
            
            theses.append(InvestmentThesis(
                industry=theme_data['industry'],
                sub_industry=theme_data['sub_industry'],
                thesis_summary=theme_data['thesis'],
                supporting_quote=quote,
                catalysts=theme_data.get('catalysts', []),
                stocks=stocks
            ))
        
        return theses
    
    def full_analysis(
        self, 
        video_id: str,
        title: str,
        transcript: str,
        segments: List[Any]
    ) -> FullAnalysis:
        """Run complete analysis pipeline."""
        self.total_cost = 0.0
        
        # Segment transcript
        segmenter = TranscriptSegmenter()
        chunks = segmenter.segment(
            transcript, 
            segments, 
            segments[-1].end_seconds if segments else len(transcript.split()) / 2.5
        )
        
        # Analyze each segment
        logger.info(f"Analyzing {len(chunks)} segments...")
        topic_segments = []
        for chunk in chunks:
            try:
                segment_analysis = self.analyze_segment(chunk, transcript)
                topic_segments.append(segment_analysis)
            except Exception as e:
                logger.warning(f"Failed to analyze segment {chunk['segment_index']}: {e}")
        
        # Extract business ideas
        logger.info("Extracting business ideas...")
        business_ideas = self.extract_business_ideas(transcript)
        
        # Extract investment theses
        logger.info("Extracting investment theses...")
        investment_theses = self.extract_investment_theses(transcript)
        
        return FullAnalysis(
            video_id=video_id,
            title=title,
            segments=topic_segments,
            business_ideas=business_ideas,
            investment_theses=investment_theses,
            total_analysis_cost=self.total_cost
        )
