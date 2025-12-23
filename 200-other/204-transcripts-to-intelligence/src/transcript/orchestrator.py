"""
Transcription Orchestrator

Tries transcription strategies in priority order, falling back to 
the next strategy if one fails. Provides a simple interface for
transcribing videos without worrying about which method to use.
"""

import logging
import re
from typing import List, Optional, Type
from urllib.parse import urlparse, parse_qs

from .base import TranscriptionStrategy
from .models import TranscriptionMethod, TranscriptionResult
from .strategies import YouTubeAPIStrategy, YtdlpStrategy, WhisperLocalStrategy, WhisperAPIStrategy

logger = logging.getLogger(__name__)


def extract_video_id(url_or_id: str) -> str:
    """
    Extract YouTube video ID from various URL formats or return as-is if already an ID.
    
    Supported formats:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://youtube.com/v/VIDEO_ID
        - https://www.youtube.com/embed/VIDEO_ID
        - VIDEO_ID (11 character string)
        
    Args:
        url_or_id: YouTube URL or video ID
        
    Returns:
        11-character video ID
        
    Raises:
        ValueError if no valid video ID found
    """
    # Already a video ID (11 chars, alphanumeric + _ -)
    if re.match(r"^[a-zA-Z0-9_-]{11}$", url_or_id):
        return url_or_id
    
    # Try parsing as URL
    try:
        parsed = urlparse(url_or_id)
        
        # youtube.com/watch?v=VIDEO_ID
        if "youtube.com" in parsed.netloc:
            if parsed.path == "/watch":
                query = parse_qs(parsed.query)
                if "v" in query:
                    return query["v"][0]
            # youtube.com/v/VIDEO_ID or youtube.com/embed/VIDEO_ID
            elif parsed.path.startswith(("/v/", "/embed/")):
                return parsed.path.split("/")[2]
        
        # youtu.be/VIDEO_ID
        elif "youtu.be" in parsed.netloc:
            return parsed.path.lstrip("/")[:11]
            
    except Exception:
        pass
    
    raise ValueError(f"Could not extract video ID from: {url_or_id}")


class TranscriptOrchestrator:
    """
    Orchestrates transcription by trying strategies in priority order.
    Falls back to the next strategy if one fails.
    """
    
    def __init__(
        self,
        strategies: Optional[List[TranscriptionStrategy]] = None,
        openai_api_key: Optional[str] = None,
    ):
        """
        Initialize orchestrator with transcription strategies.
        
        Args:
            strategies: Custom list of strategies. If None, uses defaults.
            openai_api_key: OpenAI API key for Whisper strategy.
        """
        if strategies:
            self.strategies = sorted(strategies, key=lambda s: s.priority)
        else:
            # Default strategy order (cheapest first)
            self.strategies = [
                YouTubeAPIStrategy(),
                YtdlpStrategy(),
            ]
            
            # Add local Whisper if faster-whisper is available
            try:
                import faster_whisper  # noqa: F401
                self.strategies.append(WhisperLocalStrategy())
            except ImportError:
                logger.debug("faster-whisper not installed, skipping local Whisper")
            
            # Only add Whisper API if API key is available
            whisper = WhisperAPIStrategy(api_key=openai_api_key)
            if whisper.api_key:
                self.strategies.append(whisper)
    
    def transcribe(
        self,
        url_or_video_id: str,
        force_method: Optional[TranscriptionMethod] = None,
        min_confidence: float = 0.0,
    ) -> TranscriptionResult:
        """
        Transcribe video using the best available strategy.
        
        Args:
            url_or_video_id: YouTube URL or video ID
            force_method: Force a specific transcription method
            min_confidence: Minimum confidence score required
            
        Returns:
            TranscriptionResult with full transcript
            
        Raises:
            ValueError if no strategy succeeds
        """
        video_id = extract_video_id(url_or_video_id)
        errors: List[tuple] = []
        
        for strategy in self.strategies:
            # Skip if forcing a different method
            if force_method and strategy.method != force_method:
                continue
            
            strategy_name = strategy.method.value
            
            try:
                logger.info(f"Trying strategy: {strategy_name}")
                
                # Check if strategy is available
                if not strategy.is_available(video_id):
                    logger.debug(f"Strategy {strategy_name} not available")
                    errors.append((strategy_name, "Not available for this video"))
                    continue
                
                # Attempt transcription
                result = strategy.transcribe(video_id)
                
                # Check confidence threshold
                if result.confidence_score < min_confidence:
                    logger.warning(
                        f"Strategy {strategy_name} confidence {result.confidence_score:.2f} "
                        f"below threshold {min_confidence}"
                    )
                    errors.append((strategy_name, f"Confidence {result.confidence_score} < {min_confidence}"))
                    continue
                
                logger.info(
                    f"✅ Success with {strategy_name} "
                    f"(confidence: {result.confidence_score:.2f}, "
                    f"words: {result.word_count:,})"
                )
                return result
                
            except Exception as e:
                logger.warning(f"Strategy {strategy_name} failed: {e}")
                errors.append((strategy_name, str(e)))
                continue
        
        # All strategies failed
        error_details = "; ".join(f"{name}: {err}" for name, err in errors)
        raise ValueError(f"All transcription strategies failed for {video_id}. Errors: {error_details}")
    
    def get_available_strategies(self, video_id: str) -> List[TranscriptionStrategy]:
        """Return list of strategies available for this video."""
        return [s for s in self.strategies if s.is_available(video_id)]
    
    def list_strategies(self) -> List[dict]:
        """List all configured strategies with their details."""
        return [
            {
                "method": s.method.value,
                "priority": s.priority,
                "cost_per_hour": s.estimated_cost_per_hour,
            }
            for s in self.strategies
        ]


# Convenience functions for simple usage

def transcribe(url_or_video_id: str, **kwargs) -> TranscriptionResult:
    """
    Transcribe a YouTube video using the best available method.
    
    This is the main entry point for simple usage.
    
    Args:
        url_or_video_id: YouTube URL or video ID
        **kwargs: Passed to orchestrator.transcribe()
        
    Returns:
        TranscriptionResult with full transcript
    """
    orchestrator = TranscriptOrchestrator()
    return orchestrator.transcribe(url_or_video_id, **kwargs)


def get_video_id(url: str) -> str:
    """Extract video ID from a YouTube URL."""
    return extract_video_id(url)
