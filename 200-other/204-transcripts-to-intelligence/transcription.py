"""
Transcription module with multiple fallback strategies.
Tries methods from fastest/cheapest to most comprehensive.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TranscriptionMethod(Enum):
    YOUTUBE_CAPTIONS = "youtube_captions"
    YTDLP_SUBTITLES = "ytdlp_subtitles"
    WHISPER_API = "whisper_api"
    WHISPER_LOCAL = "whisper_local"
    BROWSER_AUTOMATION = "browser_automation"


@dataclass
class TranscriptSegment:
    """A single segment of transcribed text with timing."""
    text: str
    start_seconds: float
    end_seconds: float
    speaker: Optional[str] = None
    confidence: Optional[float] = None


@dataclass
class TranscriptionResult:
    """Complete transcription result."""
    full_text: str
    segments: List[TranscriptSegment]
    method: TranscriptionMethod
    language: str = "en"
    confidence_score: float = 1.0
    word_count: int = 0
    duration_seconds: float = 0.0
    cost_usd: float = 0.0
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        if self.word_count == 0:
            self.word_count = len(self.full_text.split())


class TranscriptionStrategy(ABC):
    """Abstract base class for transcription strategies."""
    
    method: TranscriptionMethod
    priority: int  # Lower = tried first
    
    @abstractmethod
    def is_available(self, video_id: str) -> bool:
        """Check if this strategy can be used for the given video."""
        pass
    
    @abstractmethod
    def transcribe(self, video_id: str, **kwargs) -> TranscriptionResult:
        """Perform transcription and return result."""
        pass
    
    @property
    @abstractmethod
    def estimated_cost_per_hour(self) -> float:
        """Return estimated cost in USD per hour of audio."""
        pass


# =============================================================================
# STRATEGY 1: YouTube Native Captions (Free, Fastest)
# =============================================================================

class YouTubeCaptionsStrategy(TranscriptionStrategy):
    """Extract captions directly from YouTube using youtube-transcript-api."""
    
    method = TranscriptionMethod.YOUTUBE_CAPTIONS
    priority = 1
    
    def is_available(self, video_id: str) -> bool:
        """Check if video has captions available."""
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            return len(list(transcript_list)) > 0
        except Exception as e:
            logger.debug(f"YouTube captions not available: {e}")
            return False
    
    def transcribe(self, video_id: str, **kwargs) -> TranscriptionResult:
        """Extract YouTube captions."""
        from youtube_transcript_api import YouTubeTranscriptApi
        
        # Try to get manual captions first, fall back to auto-generated
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        transcript = None
        is_auto_generated = False
        
        # Prefer manual captions
        try:
            transcript = transcript_list.find_manually_created_transcript(['en'])
        except:
            try:
                transcript = transcript_list.find_generated_transcript(['en'])
                is_auto_generated = True
            except:
                # Get any available transcript
                for t in transcript_list:
                    transcript = t
                    is_auto_generated = t.is_generated
                    break
        
        if not transcript:
            raise ValueError(f"No transcript available for video {video_id}")
        
        data = transcript.fetch()
        
        # Convert to our format
        segments = [
            TranscriptSegment(
                text=item['text'],
                start_seconds=item['start'],
                end_seconds=item['start'] + item['duration']
            )
            for item in data
        ]
        
        full_text = ' '.join(seg.text for seg in segments)
        
        return TranscriptionResult(
            full_text=full_text,
            segments=segments,
            method=self.method,
            language=transcript.language_code,
            confidence_score=0.7 if is_auto_generated else 0.95,
            duration_seconds=segments[-1].end_seconds if segments else 0,
            metadata={'is_auto_generated': is_auto_generated}
        )
    
    @property
    def estimated_cost_per_hour(self) -> float:
        return 0.0


# =============================================================================
# STRATEGY 2: yt-dlp Subtitle Extraction
# =============================================================================

class YtdlpSubtitleStrategy(TranscriptionStrategy):
    """Extract subtitles using yt-dlp (more robust than youtube-transcript-api)."""
    
    method = TranscriptionMethod.YTDLP_SUBTITLES
    priority = 2
    
    def is_available(self, video_id: str) -> bool:
        """Check if yt-dlp can extract subtitles."""
        try:
            import yt_dlp
            url = f"https://www.youtube.com/watch?v={video_id}"
            
            ydl_opts = {
                'skip_download': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'quiet': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return bool(info.get('subtitles') or info.get('automatic_captions'))
        except Exception as e:
            logger.debug(f"yt-dlp subtitles not available: {e}")
            return False
    
    def transcribe(self, video_id: str, **kwargs) -> TranscriptionResult:
        """Extract subtitles via yt-dlp."""
        import yt_dlp
        import json
        import tempfile
        from pathlib import Path
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subtitle"
            
            ydl_opts = {
                'skip_download': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en'],
                'subtitlesformat': 'json3',
                'outtmpl': str(output_path),
                'quiet': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
            
            # Find the subtitle file
            subtitle_file = None
            for ext in ['.en.json3', '.en-US.json3', '.json3']:
                potential_file = Path(str(output_path) + ext)
                if potential_file.exists():
                    subtitle_file = potential_file
                    break
            
            if not subtitle_file:
                raise ValueError("No subtitle file generated")
            
            with open(subtitle_file, 'r') as f:
                data = json.load(f)
            
            # Parse json3 format
            segments = []
            for event in data.get('events', []):
                if 'segs' in event:
                    text = ''.join(seg.get('utf8', '') for seg in event['segs'])
                    if text.strip():
                        segments.append(TranscriptSegment(
                            text=text.strip(),
                            start_seconds=event.get('tStartMs', 0) / 1000,
                            end_seconds=(event.get('tStartMs', 0) + event.get('dDurationMs', 0)) / 1000
                        ))
            
            full_text = ' '.join(seg.text for seg in segments)
            is_auto = 'automatic_captions' in str(subtitle_file)
            
            return TranscriptionResult(
                full_text=full_text,
                segments=segments,
                method=self.method,
                confidence_score=0.7 if is_auto else 0.9,
                duration_seconds=info.get('duration', 0),
                metadata={'source': 'yt-dlp'}
            )
    
    @property
    def estimated_cost_per_hour(self) -> float:
        return 0.0


# =============================================================================
# STRATEGY 3: Whisper API
# =============================================================================

class WhisperAPIStrategy(TranscriptionStrategy):
    """Transcribe audio using OpenAI's Whisper API."""
    
    method = TranscriptionMethod.WHISPER_API
    priority = 3
    
    def __init__(self, api_key: str = None):
        from config.settings import get_settings
        self.api_key = api_key or get_settings().openai.api_key
    
    def is_available(self, video_id: str) -> bool:
        """Always available if API key is set and video can be downloaded."""
        return bool(self.api_key)
    
    def transcribe(self, video_id: str, **kwargs) -> TranscriptionResult:
        """Download audio and transcribe with Whisper."""
        import yt_dlp
        import tempfile
        from pathlib import Path
        from openai import OpenAI
        
        client = OpenAI(api_key=self.api_key)
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = Path(tmpdir) / "audio.mp3"
            
            # Download audio
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '128',
                }],
                'outtmpl': str(audio_path).replace('.mp3', ''),
                'quiet': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
            
            duration = info.get('duration', 0)
            
            # Transcribe with Whisper
            with open(audio_path, 'rb') as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )
            
            # Parse response
            segments = [
                TranscriptSegment(
                    text=seg.text,
                    start_seconds=seg.start,
                    end_seconds=seg.end
                )
                for seg in response.segments
            ]
            
            # Calculate cost: $0.006 per minute
            cost = (duration / 60) * 0.006
            
            return TranscriptionResult(
                full_text=response.text,
                segments=segments,
                method=self.method,
                language=response.language,
                confidence_score=0.95,
                duration_seconds=duration,
                cost_usd=cost,
                metadata={'model': 'whisper-1'}
            )
    
    @property
    def estimated_cost_per_hour(self) -> float:
        return 0.36  # $0.006/min * 60


# =============================================================================
# STRATEGY 4: Local Whisper (whisper.cpp or faster-whisper)
# =============================================================================

class WhisperLocalStrategy(TranscriptionStrategy):
    """Transcribe using local Whisper model."""
    
    method = TranscriptionMethod.WHISPER_LOCAL
    priority = 4
    
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self._model = None
    
    def is_available(self, video_id: str) -> bool:
        """Check if faster-whisper is installed."""
        try:
            import faster_whisper
            return True
        except ImportError:
            return False
    
    def transcribe(self, video_id: str, **kwargs) -> TranscriptionResult:
        """Download and transcribe with local Whisper."""
        import yt_dlp
        import tempfile
        from pathlib import Path
        from faster_whisper import WhisperModel
        
        # Lazy load model
        if self._model is None:
            self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = Path(tmpdir) / "audio.wav"
            
            # Download audio as WAV for Whisper
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '16',
                }],
                'outtmpl': str(audio_path).replace('.wav', ''),
                'quiet': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
            
            # Transcribe
            segments_gen, info_dict = self._model.transcribe(
                str(audio_path),
                beam_size=5,
                language="en"
            )
            
            segments = [
                TranscriptSegment(
                    text=seg.text,
                    start_seconds=seg.start,
                    end_seconds=seg.end
                )
                for seg in segments_gen
            ]
            
            full_text = ' '.join(seg.text for seg in segments)
            
            return TranscriptionResult(
                full_text=full_text,
                segments=segments,
                method=self.method,
                language=info_dict.language if hasattr(info_dict, 'language') else 'en',
                confidence_score=0.9,
                duration_seconds=info.get('duration', 0),
                cost_usd=0.0,
                metadata={'model': f'whisper-{self.model_size}'}
            )
    
    @property
    def estimated_cost_per_hour(self) -> float:
        return 0.0


# =============================================================================
# ORCHESTRATOR: Tries strategies in order
# =============================================================================

class TranscriptionOrchestrator:
    """
    Orchestrates transcription by trying strategies in priority order.
    Falls back to next strategy if one fails.
    """
    
    def __init__(self, strategies: List[TranscriptionStrategy] = None):
        if strategies:
            self.strategies = sorted(strategies, key=lambda s: s.priority)
        else:
            # Default strategy order
            from config.settings import get_settings
            settings = get_settings()
            
            self.strategies = [
                YouTubeCaptionsStrategy(),
                YtdlpSubtitleStrategy(),
            ]
            
            # Add Whisper strategies based on config
            if settings.transcription.use_local_whisper:
                self.strategies.append(
                    WhisperLocalStrategy(settings.transcription.local_whisper_model)
                )
            elif settings.openai.is_configured():
                self.strategies.append(WhisperAPIStrategy())
    
    def transcribe(
        self, 
        video_id: str, 
        force_method: TranscriptionMethod = None,
        min_confidence: float = 0.0
    ) -> TranscriptionResult:
        """
        Transcribe video using best available strategy.
        
        Args:
            video_id: YouTube video ID
            force_method: Force a specific transcription method
            min_confidence: Minimum confidence score required
            
        Returns:
            TranscriptionResult with full transcript
            
        Raises:
            ValueError if no strategy succeeds
        """
        errors = []
        
        for strategy in self.strategies:
            # Skip if forcing a different method
            if force_method and strategy.method != force_method:
                continue
            
            try:
                logger.info(f"Trying transcription strategy: {strategy.method.value}")
                
                if not strategy.is_available(video_id):
                    logger.debug(f"Strategy {strategy.method.value} not available")
                    continue
                
                result = strategy.transcribe(video_id)
                
                # Check confidence threshold
                if result.confidence_score < min_confidence:
                    logger.warning(
                        f"Strategy {strategy.method.value} confidence "
                        f"{result.confidence_score} below threshold {min_confidence}"
                    )
                    continue
                
                logger.info(
                    f"Transcription successful with {strategy.method.value} "
                    f"(confidence: {result.confidence_score:.2f}, "
                    f"words: {result.word_count})"
                )
                return result
                
            except Exception as e:
                logger.warning(f"Strategy {strategy.method.value} failed: {e}")
                errors.append((strategy.method.value, str(e)))
                continue
        
        # All strategies failed
        error_msg = "; ".join(f"{m}: {e}" for m, e in errors)
        raise ValueError(f"All transcription strategies failed. Errors: {error_msg}")
    
    def get_available_strategies(self, video_id: str) -> List[TranscriptionStrategy]:
        """Return list of strategies available for this video."""
        return [s for s in self.strategies if s.is_available(video_id)]


# Convenience function
def transcribe_video(video_id: str, **kwargs) -> TranscriptionResult:
    """Transcribe a YouTube video using the best available method."""
    orchestrator = TranscriptionOrchestrator()
    return orchestrator.transcribe(video_id, **kwargs)
