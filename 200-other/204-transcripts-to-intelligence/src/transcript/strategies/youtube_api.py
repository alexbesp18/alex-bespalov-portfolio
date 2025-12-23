"""
Strategy 1: YouTube API (youtube-transcript-api)

The fastest and free approach. Fetches captions directly from YouTube.
Tries manual captions first, falls back to auto-generated.
"""

import logging
from typing import List

from youtube_transcript_api import (
    YouTubeTranscriptApi,
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

from ..base import TranscriptionStrategy
from ..exceptions import NoTranscriptAvailable, VideoNotAccessible
from ..models import (
    TranscriptionMethod,
    TranscriptionResult,
    TranscriptSegment,
)

__all__ = ["YouTubeAPIStrategy"]

logger = logging.getLogger(__name__)

# Confidence scores for different caption types
MANUAL_CAPTION_CONFIDENCE = 0.95
AUTO_GENERATED_CONFIDENCE = 0.70


class YouTubeAPIStrategy(TranscriptionStrategy):
    """
    Extract captions directly from YouTube using youtube-transcript-api.
    
    This is the fastest and cheapest method for obtaining transcripts,
    but requires the video to have captions enabled.
    
    Attributes:
        method: The transcription method enum value.
        priority: Priority order for the orchestrator (1 = highest).
        
    Example:
        >>> strategy = YouTubeAPIStrategy()
        >>> if strategy.is_available("dQw4w9WgXcQ"):
        ...     result = strategy.transcribe("dQw4w9WgXcQ")
        ...     print(f"Got {result.word_count} words")
    """
    
    method = TranscriptionMethod.YOUTUBE_API
    priority = 1  # Try first (fastest and free)
    
    def is_available(self, video_id: str) -> bool:
        """
        Check if video has captions available via YouTube API.
        
        Args:
            video_id: YouTube video ID (11-character string).
            
        Returns:
            True if captions are available for this video.
        """
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            return len(list(transcript_list)) > 0
        except (NoTranscriptFound, TranscriptsDisabled) as e:
            logger.debug(f"No captions for {video_id}: {e}")
            return False
        except VideoUnavailable as e:
            logger.debug(f"Video unavailable {video_id}: {e}")
            return False
        except Exception as e:
            logger.debug(f"YouTube API check failed for {video_id}: {e}")
            return False
    
    def transcribe(self, video_id: str, **kwargs) -> TranscriptionResult:
        """
        Extract YouTube captions for a video.
        
        Attempts to fetch captions in the following priority order:
        1. Manually created captions in requested language
        2. Auto-generated captions in requested language
        3. Any available transcript as fallback
        
        Args:
            video_id: YouTube video ID (11-character string).
            language: Preferred language code (default: 'en').
            
        Returns:
            TranscriptionResult containing the transcript text and segments.
            
        Raises:
            NoTranscriptAvailable: If no captions exist for this video.
            VideoNotAccessible: If the video cannot be accessed.
        """
        language = kwargs.get("language", "en")
        
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        except VideoUnavailable as e:
            raise VideoNotAccessible(video_id, str(e)) from e
        except (NoTranscriptFound, TranscriptsDisabled) as e:
            raise NoTranscriptAvailable(video_id, str(e)) from e
        
        transcript = None
        is_auto_generated = False
        
        # Priority: manual captions > auto-generated > any available
        try:
            transcript = transcript_list.find_manually_created_transcript([language])
            logger.info(f"Found manual captions for {video_id}")
        except NoTranscriptFound:
            try:
                transcript = transcript_list.find_generated_transcript([language])
                is_auto_generated = True
                logger.info(f"Found auto-generated captions for {video_id}")
            except NoTranscriptFound:
                # Get any available transcript as last resort
                for t in transcript_list:
                    transcript = t
                    is_auto_generated = t.is_generated
                    logger.info(
                        f"Using fallback transcript ({t.language_code}) for {video_id}"
                    )
                    break
        
        if not transcript:
            raise NoTranscriptAvailable(
                video_id,
                "No transcript found in any language",
                strategies_tried=["youtube_api"],
            )
        
        # Fetch the actual caption data
        data = transcript.fetch()
        
        # Convert to our segment format
        segments: List[TranscriptSegment] = [
            TranscriptSegment(
                text=item["text"],
                start_seconds=item["start"],
                end_seconds=item["start"] + item["duration"],
            )
            for item in data
        ]
        
        # Combine all segments into full text
        full_text = " ".join(seg.text for seg in segments)
        
        # Calculate duration from last segment
        duration = segments[-1].end_seconds if segments else 0.0
        
        confidence = (
            AUTO_GENERATED_CONFIDENCE if is_auto_generated 
            else MANUAL_CAPTION_CONFIDENCE
        )
        
        return TranscriptionResult(
            full_text=full_text,
            segments=segments,
            method=self.method,
            video_id=video_id,
            language=transcript.language_code,
            confidence_score=confidence,
            duration_seconds=duration,
            is_auto_generated=is_auto_generated,
            cost_usd=0.0,
            metadata={
                "source": "youtube-transcript-api",
                "transcript_language": transcript.language_code,
            },
        )
    
    @property
    def estimated_cost_per_hour(self) -> float:
        """Return cost per hour of audio (free for this strategy)."""
        return 0.0
