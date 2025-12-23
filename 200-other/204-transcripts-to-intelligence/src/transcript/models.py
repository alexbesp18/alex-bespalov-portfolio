"""
Data models for transcript module.

Provides common data structures used across all transcription strategies.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any


class TranscriptionMethod(Enum):
    """Available transcription methods."""
    YOUTUBE_API = "youtube_api"        # youtube-transcript-api
    YTDLP = "ytdlp"                    # yt-dlp subtitle extraction
    WHISPER_LOCAL = "whisper_local"    # Local Whisper via faster-whisper
    WHISPER_API = "whisper_api"        # OpenAI Whisper API


@dataclass
class TranscriptSegment:
    """A single segment of transcribed text with timing information."""
    text: str
    start_seconds: float
    end_seconds: float
    speaker: Optional[str] = None
    confidence: Optional[float] = None
    
    @property
    def duration(self) -> float:
        """Duration of this segment in seconds."""
        return self.end_seconds - self.start_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "text": self.text,
            "start": self.start_seconds,
            "end": self.end_seconds,
            "speaker": self.speaker,
            "confidence": self.confidence,
        }


@dataclass
class TranscriptionResult:
    """Complete transcription result from any strategy."""
    full_text: str
    segments: List[TranscriptSegment]
    method: TranscriptionMethod
    video_id: str
    language: str = "en"
    confidence_score: float = 1.0
    word_count: int = 0
    duration_seconds: float = 0.0
    cost_usd: float = 0.0
    is_auto_generated: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Calculate word count if not provided."""
        if self.word_count == 0 and self.full_text:
            self.word_count = len(self.full_text.split())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "video_id": self.video_id,
            "method": self.method.value,
            "language": self.language,
            "confidence_score": self.confidence_score,
            "word_count": self.word_count,
            "duration_seconds": self.duration_seconds,
            "cost_usd": self.cost_usd,
            "is_auto_generated": self.is_auto_generated,
            "full_text": self.full_text,
            "segments": [s.to_dict() for s in self.segments],
            "metadata": self.metadata,
        }
    
    def preview(self, chars: int = 500) -> str:
        """Return first N characters of the transcript."""
        if len(self.full_text) <= chars:
            return self.full_text
        return self.full_text[:chars] + "..."
