"""
Strategy 2.5: Local Whisper (faster-whisper)

Uses faster-whisper for local transcription without API costs.
Provides offline processing capability and zero marginal cost.
Requires initial model download (~1-3GB depending on model size).
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import List, Optional

from ..base import TranscriptionStrategy
from ..exceptions import (
    NoTranscriptAvailable,
    TranscriptionError,
    VideoNotAccessible,
)
from ..models import (
    TranscriptionMethod,
    TranscriptionResult,
    TranscriptSegment,
)

__all__ = ["WhisperLocalStrategy"]

logger = logging.getLogger(__name__)

# Confidence scores by model size
MODEL_CONFIDENCE = {
    "tiny": 0.70,
    "base": 0.80,
    "small": 0.85,
    "medium": 0.90,
    "large-v2": 0.95,
    "large-v3": 0.95,
}

# Default model if not specified
DEFAULT_MODEL = "base"


class WhisperLocalStrategy(TranscriptionStrategy):
    """
    Transcribe audio using local Whisper model via faster-whisper.
    
    This strategy provides free transcription by running Whisper locally.
    It requires the faster-whisper library and will download models on first use.
    GPU acceleration is used when available (CUDA/Metal).
    
    Attributes:
        method: The transcription method enum value.
        priority: Priority order for the orchestrator (2.5 = between yt-dlp and API).
        model_size: Size of the Whisper model to use.
        
    Example:
        >>> strategy = WhisperLocalStrategy(model_size="base")
        >>> if strategy.is_available("dQw4w9WgXcQ"):
        ...     result = strategy.transcribe("dQw4w9WgXcQ")
        ...     print(f"Got {result.word_count} words (free!)")
    """
    
    method = TranscriptionMethod.WHISPER_LOCAL
    priority = 2.5  # Between yt-dlp (2) and Whisper API (3)
    
    def __init__(
        self,
        model_size: str = DEFAULT_MODEL,
        device: str = "auto",
        compute_type: str = "auto",
    ):
        """
        Initialize with model configuration.
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large-v2, large-v3).
            device: Device to use ("auto", "cpu", "cuda").
            compute_type: Compute type ("auto", "int8", "float16", "float32").
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None
    
    def is_available(self, video_id: str) -> bool:
        """
        Check if local Whisper transcription is possible.
        
        Verifies that faster-whisper is installed and the video can be downloaded.
        
        Args:
            video_id: YouTube video ID (11-character string).
            
        Returns:
            True if local Whisper transcription is possible.
        """
        # Check if faster-whisper is available
        try:
            import faster_whisper  # noqa: F401
        except ImportError:
            logger.debug("faster-whisper not installed")
            return False
        
        # Check if yt-dlp can download the video
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
        Download audio and transcribe with local Whisper.
        
        Downloads the video's audio track using yt-dlp, then transcribes
        using faster-whisper running locally.
        
        Args:
            video_id: YouTube video ID (11-character string).
            language: Language hint for Whisper (default: 'en').
            
        Returns:
            TranscriptionResult containing the transcript text and segments.
            
        Raises:
            VideoNotAccessible: If the video cannot be downloaded.
            TranscriptionError: If transcription fails.
        """
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise TranscriptionError(
                "faster-whisper not installed. Install with: pip install faster-whisper"
            )
        
        import yt_dlp
        
        language = kwargs.get("language", "en")
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = Path(tmpdir) / "audio"
            
            # Download audio
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
            }
            
            logger.info(f"Downloading audio for {video_id}...")
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
            except yt_dlp.utils.DownloadError as e:
                raise VideoNotAccessible(video_id, str(e)) from e
            
            duration = info.get("duration", 0)
            
            # Find audio file
            audio_file = self._find_audio_file(audio_path)
            
            if not audio_file:
                raise NoTranscriptAvailable(
                    video_id,
                    "Audio file not found after download",
                    strategies_tried=["whisper_local"],
                )
            
            # Load model (lazy initialization)
            logger.info(f"Transcribing with local Whisper ({self.model_size})...")
            
            if self._model is None:
                self._model = self._load_model(WhisperModel)
            
            # Transcribe
            segments_generator, transcribe_info = self._model.transcribe(
                str(audio_file),
                language=language if language != "auto" else None,
                beam_size=5,
                vad_filter=True,
            )
            
            # Collect segments
            segments: List[TranscriptSegment] = []
            full_text_parts: List[str] = []
            
            for segment in segments_generator:
                text = segment.text.strip()
                if text:
                    segments.append(TranscriptSegment(
                        text=text,
                        start_seconds=segment.start,
                        end_seconds=segment.end,
                    ))
                    full_text_parts.append(text)
            
            full_text = " ".join(full_text_parts)
            
            # Get confidence score based on model size
            confidence = MODEL_CONFIDENCE.get(self.model_size, 0.85)
            
            return TranscriptionResult(
                full_text=full_text,
                segments=segments,
                method=self.method,
                video_id=video_id,
                language=transcribe_info.language if hasattr(transcribe_info, "language") else language,
                confidence_score=confidence,
                duration_seconds=duration,
                is_auto_generated=False,
                cost_usd=0.0,  # Free!
                metadata={
                    "source": "faster-whisper",
                    "model": self.model_size,
                    "device": self.device,
                    "video_title": info.get("title", ""),
                    "channel": info.get("channel", ""),
                },
            )
    
    def _load_model(self, WhisperModel):
        """Load the Whisper model with appropriate settings."""
        device = self.device
        compute_type = self.compute_type
        
        # Auto-detect best device
        if device == "auto":
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"
        
        # Auto-select compute type based on device
        if compute_type == "auto":
            compute_type = "float16" if device == "cuda" else "int8"
        
        logger.info(f"Loading Whisper model: {self.model_size} on {device} ({compute_type})")
        
        return WhisperModel(
            self.model_size,
            device=device,
            compute_type=compute_type,
        )
    
    def _find_audio_file(self, base_path: Path) -> Optional[Path]:
        """Find the downloaded audio file with various extensions."""
        for ext in [".mp3", ".m4a", ".webm", ".opus", ".wav"]:
            audio_file = Path(str(base_path) + ext)
            if audio_file.exists():
                return audio_file
        return None
    
    @property
    def estimated_cost_per_hour(self) -> float:
        """Return cost per hour of audio (free for local)."""
        return 0.0

