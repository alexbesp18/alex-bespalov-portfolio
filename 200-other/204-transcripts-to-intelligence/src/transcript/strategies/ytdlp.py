"""
Strategy 2: yt-dlp Subtitle Extraction

More robust than youtube-transcript-api. Downloads subtitle files
directly and parses them. Better at handling edge cases like
age-restricted videos (with cookies) and regional restrictions.
"""

import json
import logging
import tempfile
from pathlib import Path
from typing import List, Optional

from ..base import TranscriptionStrategy
from ..exceptions import NoTranscriptAvailable, VideoNotAccessible
from ..models import (
    TranscriptionMethod,
    TranscriptionResult,
    TranscriptSegment,
)

__all__ = ["YtdlpStrategy"]

logger = logging.getLogger(__name__)

# Confidence scores for different caption types
MANUAL_CAPTION_CONFIDENCE = 0.90
AUTO_GENERATED_CONFIDENCE = 0.70


class YtdlpStrategy(TranscriptionStrategy):
    """
    Extract subtitles using yt-dlp library.
    
    This strategy is more robust than the YouTube API approach and can
    handle edge cases like age-restricted videos (when cookies are provided).
    It downloads subtitle files in JSON3 format and parses them locally.
    
    Attributes:
        method: The transcription method enum value.
        priority: Priority order for the orchestrator (2 = second choice).
        
    Example:
        >>> strategy = YtdlpStrategy()
        >>> if strategy.is_available("dQw4w9WgXcQ"):
        ...     result = strategy.transcribe("dQw4w9WgXcQ")
        ...     print(f"Got {result.word_count} words")
    """
    
    method = TranscriptionMethod.YTDLP
    priority = 2  # Try second
    
    def is_available(self, video_id: str) -> bool:
        """
        Check if yt-dlp can extract subtitles for this video.
        
        Args:
            video_id: YouTube video ID (11-character string).
            
        Returns:
            True if subtitles can be extracted for this video.
        """
        try:
            import yt_dlp
            
            url = f"https://www.youtube.com/watch?v={video_id}"
            
            ydl_opts = {
                "skip_download": True,
                "writesubtitles": True,
                "writeautomaticsub": True,
                "quiet": True,
                "no_warnings": True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                has_subs = bool(
                    info.get("subtitles") or info.get("automatic_captions")
                )
                return has_subs
                
        except Exception as e:
            logger.debug(f"yt-dlp check failed for {video_id}: {e}")
            return False
    
    def transcribe(self, video_id: str, **kwargs) -> TranscriptionResult:
        """
        Extract subtitles via yt-dlp.
        
        Downloads subtitle files in JSON3 format to a temporary directory,
        then parses them into our standard segment format.
        
        Args:
            video_id: YouTube video ID (11-character string).
            language: Preferred language code (default: 'en').
            
        Returns:
            TranscriptionResult containing the transcript text and segments.
            
        Raises:
            NoTranscriptAvailable: If no subtitles can be extracted.
            VideoNotAccessible: If the video cannot be accessed.
        """
        import yt_dlp
        
        language = kwargs.get("language", "en")
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_template = str(Path(tmpdir) / "subtitle")
            
            ydl_opts = {
                "skip_download": True,
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitleslangs": [language, f"{language}-US", f"{language}-GB"],
                "subtitlesformat": "json3",
                "outtmpl": output_template,
                "quiet": True,
                "no_warnings": True,
            }
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
            except yt_dlp.utils.DownloadError as e:
                if "Video unavailable" in str(e) or "Private video" in str(e):
                    raise VideoNotAccessible(video_id, str(e)) from e
                raise NoTranscriptAvailable(
                    video_id, f"yt-dlp extraction failed: {e}"
                ) from e
            
            # Find the downloaded subtitle file
            subtitle_file = self._find_subtitle_file(Path(tmpdir), language)
            
            if not subtitle_file:
                raise NoTranscriptAvailable(
                    video_id,
                    "No subtitle file generated",
                    strategies_tried=["ytdlp"],
                )
            
            # Parse the JSON3 format
            segments = self._parse_json3(subtitle_file)
            
            if not segments:
                raise NoTranscriptAvailable(
                    video_id,
                    "Subtitle file was empty",
                    strategies_tried=["ytdlp"],
                )
            
            # Determine if auto-generated based on available subtitle sources
            manual_subs = info.get("subtitles", {})
            is_auto = language not in manual_subs
            
            full_text = " ".join(seg.text for seg in segments)
            duration = info.get("duration", 0) or segments[-1].end_seconds
            
            confidence = (
                AUTO_GENERATED_CONFIDENCE if is_auto 
                else MANUAL_CAPTION_CONFIDENCE
            )
            
            return TranscriptionResult(
                full_text=full_text,
                segments=segments,
                method=self.method,
                video_id=video_id,
                language=language,
                confidence_score=confidence,
                duration_seconds=duration,
                is_auto_generated=is_auto,
                cost_usd=0.0,
                metadata={
                    "source": "yt-dlp",
                    "video_title": info.get("title", ""),
                    "channel": info.get("channel", ""),
                },
            )
    
    def _find_subtitle_file(
        self, directory: Path, language: str
    ) -> Optional[Path]:
        """
        Find the subtitle file in the temp directory.
        
        Args:
            directory: Directory to search in.
            language: Language code to prioritize.
            
        Returns:
            Path to subtitle file, or None if not found.
        """
        patterns = [
            f"*.{language}.json3",
            f"*.{language}-US.json3",
            f"*.{language}-GB.json3",
            "*.json3",
        ]
        
        for pattern in patterns:
            files = list(directory.glob(pattern))
            if files:
                return files[0]
        
        return None
    
    def _parse_json3(self, filepath: Path) -> List[TranscriptSegment]:
        """
        Parse YouTube's JSON3 subtitle format.
        
        Args:
            filepath: Path to the JSON3 subtitle file.
            
        Returns:
            List of TranscriptSegment objects.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        segments: List[TranscriptSegment] = []
        
        for event in data.get("events", []):
            if "segs" not in event:
                continue
                
            # Combine all text segments within this event
            text_parts = []
            for seg in event.get("segs", []):
                text = seg.get("utf8", "")
                if text and text.strip():
                    text_parts.append(text)
            
            combined_text = "".join(text_parts).strip()
            
            if combined_text:
                start_ms = event.get("tStartMs", 0)
                duration_ms = event.get("dDurationMs", 0)
                
                segments.append(TranscriptSegment(
                    text=combined_text,
                    start_seconds=start_ms / 1000.0,
                    end_seconds=(start_ms + duration_ms) / 1000.0,
                ))
        
        return segments
    
    @property
    def estimated_cost_per_hour(self) -> float:
        """Return cost per hour of audio (free for this strategy)."""
        return 0.0
