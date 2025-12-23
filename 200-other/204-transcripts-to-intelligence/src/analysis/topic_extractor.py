"""
Topic Extractor

Extracts key topics, summaries, and notable quotes from transcript chunks
using LLM analysis.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from .llm_client import LLMClient, LLMResponse, get_client
from .models import TranscriptChunk

__all__ = ["TopicExtractor", "TopicExtractionResult", "ChunkAnalysis"]

logger = logging.getLogger(__name__)

# Default prompt template (curly braces in JSON example are doubled for escaping)
TOPIC_EXTRACTION_PROMPT = """You are analyzing a podcast transcript segment. Extract:

1. KEY TOPICS: List 2-4 main topics discussed in this segment
2. SUMMARY: 2-3 sentence summary of the discussion
3. DIRECT QUOTE: Select the single most insightful or actionable quote
   - Must be VERBATIM from the transcript
   - Aim for 1-3 sentences

Segment [{chunk_index}]: {start_time} - {end_time}
---
{text}
---

Respond in JSON format only, no markdown:
{{
  "topics": ["topic1", "topic2"],
  "summary": "...",
  "quote": {{
    "text": "exact verbatim quote from transcript",
    "speaker": "speaker name or 'Unknown'"
  }}
}}"""

SYSTEM_PROMPT = """You are an expert podcast analyst. Extract key insights from transcripts.
Always respond in valid JSON format. Be concise but comprehensive."""


@dataclass
class Quote:
    """A notable quote extracted from the transcript."""
    text: str
    speaker: str = "Unknown"
    
    def to_dict(self) -> Dict[str, str]:
        return {"text": self.text, "speaker": self.speaker}


@dataclass
class ChunkAnalysis:
    """Analysis result for a single transcript chunk.
    
    Attributes:
        chunk_index: Index of the analyzed chunk.
        start_seconds: Start time in the video.
        end_seconds: End time in the video.
        topics: List of key topics identified.
        summary: Brief summary of the chunk content.
        quote: Notable quote from the chunk.
        cost_usd: LLM API cost for this analysis.
    """
    chunk_index: int
    start_seconds: float
    end_seconds: float
    topics: List[str]
    summary: str
    quote: Quote
    cost_usd: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_index": self.chunk_index,
            "start_seconds": self.start_seconds,
            "end_seconds": self.end_seconds,
            "topics": self.topics,
            "summary": self.summary,
            "quote": self.quote.to_dict(),
            "cost_usd": self.cost_usd,
        }


@dataclass
class TopicExtractionResult:
    """Complete topic extraction result for all chunks.
    
    Attributes:
        analyses: List of per-chunk analyses.
        all_topics: Deduplicated list of all topics found.
        total_cost_usd: Total LLM API cost.
    """
    analyses: List[ChunkAnalysis]
    all_topics: List[str] = field(default_factory=list)
    total_cost_usd: float = 0.0
    
    def __post_init__(self):
        """Compute derived fields."""
        if not self.all_topics and self.analyses:
            # Deduplicate topics while preserving order
            seen = set()
            topics = []
            for analysis in self.analyses:
                for topic in analysis.topics:
                    topic_lower = topic.lower()
                    if topic_lower not in seen:
                        seen.add(topic_lower)
                        topics.append(topic)
            self.all_topics = topics
        
        if self.total_cost_usd == 0.0 and self.analyses:
            self.total_cost_usd = sum(a.cost_usd for a in self.analyses)
    
    @property
    def num_chunks(self) -> int:
        return len(self.analyses)
    
    @property
    def all_quotes(self) -> List[Quote]:
        return [a.quote for a in self.analyses]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "num_chunks": self.num_chunks,
            "all_topics": self.all_topics,
            "total_cost_usd": self.total_cost_usd,
            "analyses": [a.to_dict() for a in self.analyses],
        }


class TopicExtractor:
    """Extracts topics and insights from transcript chunks using LLM.
    
    Example:
        >>> from src.analysis import TranscriptSegmenter, TopicExtractor
        >>> 
        >>> # Segment transcript
        >>> segmenter = TranscriptSegmenter()
        >>> chunks = segmenter.segment_by_words(transcript_text)
        >>> 
        >>> # Extract topics
        >>> extractor = TopicExtractor()
        >>> result = extractor.extract(chunks.chunks)
        >>> 
        >>> for topic in result.all_topics:
        ...     print(f"- {topic}")
    """
    
    def __init__(
        self,
        client: Optional[LLMClient] = None,
        provider: str = "openrouter",
        model: Optional[str] = None,
        prompt_template: str = TOPIC_EXTRACTION_PROMPT,
    ):
        """Initialize topic extractor.
        
        Args:
            client: Pre-configured LLM client. If None, creates one.
            provider: LLM provider ("openai" or "anthropic").
            model: Model to use. Defaults to provider's default.
            prompt_template: Custom prompt template.
        """
        self.prompt_template = prompt_template
        
        if client:
            self.client = client
        else:
            kwargs = {}
            if model:
                kwargs["model"] = model
            self.client = get_client(provider, **kwargs)
    
    def extract(
        self,
        chunks: List[TranscriptChunk],
        max_chunks: Optional[int] = None,
    ) -> TopicExtractionResult:
        """Extract topics from transcript chunks.
        
        Args:
            chunks: List of TranscriptChunk objects to analyze.
            max_chunks: Maximum chunks to process (for testing/cost control).
            
        Returns:
            TopicExtractionResult with all analyses.
        """
        if not chunks:
            return TopicExtractionResult(analyses=[])
        
        chunks_to_process = chunks[:max_chunks] if max_chunks else chunks
        analyses: List[ChunkAnalysis] = []
        
        logger.info(f"Extracting topics from {len(chunks_to_process)} chunks...")
        
        for chunk in chunks_to_process:
            try:
                analysis = self._analyze_chunk(chunk)
                analyses.append(analysis)
                logger.debug(
                    f"Chunk {chunk.chunk_index}: {len(analysis.topics)} topics, "
                    f"${analysis.cost_usd:.4f}"
                )
            except Exception as e:
                logger.error(f"Failed to analyze chunk {chunk.chunk_index}: {e}")
                # Continue with other chunks
                continue
        
        result = TopicExtractionResult(analyses=analyses)
        
        logger.info(
            f"Extracted {len(result.all_topics)} unique topics from "
            f"{result.num_chunks} chunks (${result.total_cost_usd:.4f})"
        )
        
        return result
    
    def extract_single(self, chunk: TranscriptChunk) -> ChunkAnalysis:
        """Extract topics from a single chunk.
        
        Args:
            chunk: The chunk to analyze.
            
        Returns:
            ChunkAnalysis for this chunk.
        """
        return self._analyze_chunk(chunk)
    
    def _analyze_chunk(self, chunk: TranscriptChunk) -> ChunkAnalysis:
        """Analyze a single chunk with LLM."""
        # Format the prompt
        prompt = self.prompt_template.format(
            chunk_index=chunk.chunk_index,
            start_time=self._format_time(chunk.start_seconds),
            end_time=self._format_time(chunk.end_seconds),
            text=chunk.text,
        )
        
        # Call LLM
        response = self.client.complete(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.3,  # Lower temperature for more consistent extraction
            max_tokens=500,
        )
        
        # Parse response
        try:
            data = response.parse_json()
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {response.content}")
            # Return minimal result
            return ChunkAnalysis(
                chunk_index=chunk.chunk_index,
                start_seconds=chunk.start_seconds,
                end_seconds=chunk.end_seconds,
                topics=["Parsing error"],
                summary="Failed to parse LLM response",
                quote=Quote(text="", speaker="Unknown"),
                cost_usd=response.cost_usd,
            )
        
        # Extract fields with defaults
        topics = data.get("topics", [])
        summary = data.get("summary", "")
        quote_data = data.get("quote", {})
        
        quote = Quote(
            text=quote_data.get("text", ""),
            speaker=quote_data.get("speaker", "Unknown"),
        )
        
        return ChunkAnalysis(
            chunk_index=chunk.chunk_index,
            start_seconds=chunk.start_seconds,
            end_seconds=chunk.end_seconds,
            topics=topics,
            summary=summary,
            quote=quote,
            cost_usd=response.cost_usd,
        )
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds as MM:SS."""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
