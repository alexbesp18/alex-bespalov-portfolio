"""
Transcript Module

A multi-strategy YouTube transcript extraction system.
Tries the fastest/cheapest methods first, falling back to more
robust (but potentially costly) methods as needed.

Usage:
    from src.transcript import transcribe, get_video_id
    
    # Simple usage
    result = transcribe("https://www.youtube.com/watch?v=VIDEO_ID")
    print(result.full_text)
    
    # Advanced usage with orchestrator
    from src.transcript import TranscriptOrchestrator
    
    orchestrator = TranscriptOrchestrator(openai_api_key="sk-...")
    result = orchestrator.transcribe("VIDEO_ID", min_confidence=0.8)

Strategies (in order of priority):
    1. YouTube API - Free, fastest, requires captions
    2. yt-dlp - Free, more robust subtitle extraction
    3. Whisper API - Paid ($0.36/hr), highest accuracy
"""

from .models import (
    TranscriptionMethod,
    TranscriptSegment, 
    TranscriptionResult,
)
from .base import TranscriptionStrategy
from .exceptions import (
    TranscriptionError,
    NoTranscriptAvailable,
    VideoNotAccessible,
    InvalidVideoId,
    APIKeyMissingError,
    TranscriptionAPIError,
)
from .orchestrator import (
    TranscriptOrchestrator,
    transcribe,
    get_video_id,
    extract_video_id,
)
from .strategies import (
    YouTubeAPIStrategy,
    YtdlpStrategy,
    WhisperAPIStrategy,
)

__all__ = [
    # Main entry points
    "transcribe",
    "get_video_id",
    "extract_video_id",
    "TranscriptOrchestrator",
    # Models
    "TranscriptionMethod",
    "TranscriptSegment",
    "TranscriptionResult",
    # Base class
    "TranscriptionStrategy",
    # Strategies
    "YouTubeAPIStrategy",
    "YtdlpStrategy",
    "WhisperAPIStrategy",
    # Exceptions
    "TranscriptionError",
    "NoTranscriptAvailable",
    "VideoNotAccessible",
    "InvalidVideoId",
    "APIKeyMissingError",
    "TranscriptionAPIError",
]

__version__ = "0.1.0"
