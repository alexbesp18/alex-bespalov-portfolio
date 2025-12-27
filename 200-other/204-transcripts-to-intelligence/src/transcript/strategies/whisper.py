"""
Strategy 3: OpenAI Whisper API

Downloads audio via yt-dlp and transcribes using OpenAI's Whisper API.
Highest accuracy but costs $0.006 per minute of audio (~$0.36/hour).
"""

import logging
import os
import tempfile
import time
from pathlib import Path
from typing import List, Optional

from ..base import TranscriptionStrategy
from ..exceptions import (
    APIKeyMissingError,
    NoTranscriptAvailable,
    TranscriptionAPIError,
    VideoNotAccessible,
)
from ..models import (
    TranscriptionMethod,
    TranscriptionResult,
    TranscriptSegment,
)

__all__ = ["WhisperAPIStrategy"]

logger = logging.getLogger(__name__)

# Cost configuration
WHISPER_COST_PER_MINUTE = 0.006  # USD
WHISPER_CONFIDENCE_SCORE = 0.95

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2.0


class WhisperAPIStrategy(TranscriptionStrategy):
    """
    Transcribe audio using OpenAI's Whisper API.
    
    This strategy provides the highest accuracy transcription by downloading
    the video's audio and sending it to OpenAI's Whisper model. It works
    even when no captions are available on YouTube.
    
    Attributes:
        method: The transcription method enum value.
        priority: Priority order for the orchestrator (3 = last resort).
        api_key: The OpenAI API key for authentication.
        
    Example:
        >>> strategy = WhisperAPIStrategy(api_key="sk-...")
        >>> if strategy.is_available("dQw4w9WgXcQ"):
        ...     result = strategy.transcribe("dQw4w9WgXcQ")
        ...     print(f"Cost: ${result.cost_usd:.4f}")
    """
    
    method = TranscriptionMethod.WHISPER_API
    priority = 3  # Try last (most expensive)
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize with OpenAI API key.
        
        Args:
            api_key: OpenAI API key. If not provided, reads from
                OPENAI_API_KEY environment variable.
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
    
    def is_available(self, video_id: str) -> bool:
        """
        Check if Whisper API can be used for this video.
        
        Verifies both that an API key is configured and that the video
        can be downloaded.
        
        Args:
            video_id: YouTube video ID (11-character string).
            
        Returns:
            True if Whisper transcription is possible.
        """
        if not self.api_key:
            logger.debug("Whisper API not available: No API key configured")
            return False
        
        # Verify the video can be downloaded
        try:
            import yt_dlp
            url = f"https://www.youtube.com/watch?v={video_id}"
            
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=False)
            return True
            
        except Exception as e:
            logger.debug(f"Cannot download video {video_id}: {e}")
            return False
    
    def transcribe(self, video_id: str, **kwargs) -> TranscriptionResult:
        """
        Download audio and transcribe with Whisper API.
        
        Downloads the video's audio track using yt-dlp, then sends it
        to OpenAI's Whisper API for transcription. Includes retry logic
        for transient failures.
        
        Args:
            video_id: YouTube video ID (11-character string).
            language: Language hint for Whisper (default: 'en').
            
        Returns:
            TranscriptionResult containing the transcript text and segments.
            
        Raises:
            APIKeyMissingError: If no OpenAI API key is configured.
            VideoNotAccessible: If the video cannot be downloaded.
            TranscriptionAPIError: If the Whisper API call fails.
        """
        if not self.api_key:
            raise APIKeyMissingError("OpenAI Whisper", "OPENAI_API_KEY")
        
        import yt_dlp
        from openai import OpenAI, APIError, RateLimitError
        
        language = kwargs.get("language", "en")
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        client = OpenAI(api_key=self.api_key)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = Path(tmpdir) / "audio"
            
            # Download audio as MP3 with bot-detection bypass options
            ydl_opts = {
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "128",
                }],
                "outtmpl": str(audio_path),
                "quiet": True,
                "no_warnings": True,
                # Bot detection bypass options
                "extractor_args": {
                    "youtube": {
                        "player_client": ["android", "web"],  # Try Android client first
                    }
                },
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                },
                "sleep_interval": 1,  # Small delay between requests
                "max_sleep_interval": 3,
            }
            
            logger.info(f"Downloading audio for {video_id}...")
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
            except yt_dlp.utils.DownloadError as e:
                raise VideoNotAccessible(video_id, str(e)) from e
            
            duration = info.get("duration", 0)
            
            # Find the downloaded audio file
            audio_file = self._find_audio_file(audio_path)
            
            if not audio_file:
                raise NoTranscriptAvailable(
                    video_id,
                    "Audio file not found after download",
                    strategies_tried=["whisper_api"],
                )
            
            logger.info("Transcribing with Whisper API...")
            
            # Transcribe with retry logic
            response = self._transcribe_with_retry(
                client, audio_file, language
            )
            
            # Parse response into segments
            segments: List[TranscriptSegment] = []
            
            if hasattr(response, "segments") and response.segments:
                for seg in response.segments:
                    segments.append(TranscriptSegment(
                        text=seg.text.strip(),
                        start_seconds=seg.start,
                        end_seconds=seg.end,
                    ))
            
            # Calculate cost
            cost = (duration / 60.0) * WHISPER_COST_PER_MINUTE
            
            return TranscriptionResult(
                full_text=response.text,
                segments=segments,
                method=self.method,
                video_id=video_id,
                language=getattr(response, "language", language),
                confidence_score=WHISPER_CONFIDENCE_SCORE,
                duration_seconds=duration,
                is_auto_generated=False,
                cost_usd=cost,
                metadata={
                    "source": "openai-whisper",
                    "model": "whisper-1",
                    "video_title": info.get("title", ""),
                    "channel": info.get("channel", ""),
                },
            )
    
    def _find_audio_file(self, base_path: Path) -> Optional[Path]:
        """
        Find the downloaded audio file with various extensions.
        
        Args:
            base_path: Base path without extension.
            
        Returns:
            Path to audio file, or None if not found.
        """
        for ext in [".mp3", ".m4a", ".webm", ".opus", ".wav"]:
            audio_file = Path(str(base_path) + ext)
            if audio_file.exists():
                return audio_file
        return None
    
    def _transcribe_with_retry(self, client, audio_file: Path, language: str):
        """
        Transcribe audio with exponential backoff retry.
        
        Args:
            client: OpenAI client instance.
            audio_file: Path to audio file.
            language: Language code for transcription.
            
        Returns:
            Whisper API response.
            
        Raises:
            TranscriptionAPIError: If all retries fail.
        """
        from openai import APIError, RateLimitError
        
        last_error = None
        
        for attempt in range(MAX_RETRIES):
            try:
                with open(audio_file, "rb") as f:
                    return client.audio.transcriptions.create(
                        model="whisper-1",
                        file=f,
                        response_format="verbose_json",
                        timestamp_granularities=["segment"],
                        language=language,
                    )
            except RateLimitError as e:
                last_error = e
                delay = RETRY_DELAY_SECONDS * (2 ** attempt)
                logger.warning(
                    f"Rate limited, retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})"
                )
                time.sleep(delay)
            except APIError as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY_SECONDS * (2 ** attempt)
                    logger.warning(
                        f"API error, retrying in {delay}s: {e}"
                    )
                    time.sleep(delay)
        
        raise TranscriptionAPIError(
            service="OpenAI Whisper",
            message=f"Failed after {MAX_RETRIES} attempts: {last_error}",
        )
    
    @property
    def estimated_cost_per_hour(self) -> float:
        """Return cost per hour of audio ($0.36/hour)."""
        return WHISPER_COST_PER_MINUTE * 60
