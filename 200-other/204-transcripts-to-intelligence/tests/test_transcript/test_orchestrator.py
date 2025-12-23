"""
Unit tests for transcript orchestrator and URL parsing.

Tests extract_video_id function and TranscriptOrchestrator class.
"""

import pytest

from src.transcript.orchestrator import extract_video_id, TranscriptOrchestrator
from src.transcript.models import TranscriptionMethod
from src.transcript.exceptions import InvalidVideoId


class TestExtractVideoId:
    """Tests for extract_video_id function."""

    def test_raw_video_id(self) -> None:
        """Test extracting from raw 11-character ID."""
        assert extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"
        assert extract_video_id("NHAzpG95ptI") == "NHAzpG95ptI"

    def test_standard_youtube_url(self) -> None:
        """Test standard youtube.com/watch URL."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_youtube_url_with_params(self) -> None:
        """Test URL with additional query parameters."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120&list=PLtest"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_short_youtu_be_url(self) -> None:
        """Test short youtu.be URLs."""
        url = "https://youtu.be/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_embed_url(self) -> None:
        """Test embed URLs."""
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_v_url(self) -> None:
        """Test /v/ format URLs."""
        url = "https://www.youtube.com/v/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_invalid_url_raises(self) -> None:
        """Test that invalid URLs raise ValueError."""
        with pytest.raises(ValueError, match="Could not extract video ID"):
            extract_video_id("https://google.com/not-youtube")

    def test_invalid_short_id_raises(self) -> None:
        """Test that short IDs raise ValueError."""
        with pytest.raises(ValueError, match="Could not extract video ID"):
            extract_video_id("abc123")  # Too short

    def test_empty_string_raises(self) -> None:
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="Could not extract video ID"):
            extract_video_id("")

    def test_video_id_with_special_chars(self) -> None:
        """Test video IDs with underscores and hyphens."""
        assert extract_video_id("abc_123-XYZ") == "abc_123-XYZ"
        assert extract_video_id("https://youtu.be/abc_123-XYZ") == "abc_123-XYZ"


class TestTranscriptOrchestrator:
    """Tests for TranscriptOrchestrator class."""

    def test_default_strategies(self) -> None:
        """Test default strategy initialization."""
        orchestrator = TranscriptOrchestrator()
        
        # Should have at least YouTube API and yt-dlp
        methods = [s.method for s in orchestrator.strategies]
        assert TranscriptionMethod.YOUTUBE_API in methods
        assert TranscriptionMethod.YTDLP in methods

    def test_strategies_sorted_by_priority(self) -> None:
        """Test strategies are sorted by priority."""
        orchestrator = TranscriptOrchestrator()
        
        priorities = [s.priority for s in orchestrator.strategies]
        assert priorities == sorted(priorities)

    def test_list_strategies(self) -> None:
        """Test list_strategies method."""
        orchestrator = TranscriptOrchestrator()
        strategies = orchestrator.list_strategies()
        
        assert len(strategies) >= 2
        assert all("method" in s for s in strategies)
        assert all("priority" in s for s in strategies)
        assert all("cost_per_hour" in s for s in strategies)

    def test_whisper_not_added_without_key(self) -> None:
        """Test Whisper strategy not added if no API key."""
        orchestrator = TranscriptOrchestrator(openai_api_key=None)
        
        methods = [s.method for s in orchestrator.strategies]
        # Should not have Whisper if no key provided
        # (unless OPENAI_API_KEY env var is set)

    def test_custom_strategies(self) -> None:
        """Test custom strategy list."""
        from src.transcript.strategies import YouTubeAPIStrategy
        
        custom = [YouTubeAPIStrategy()]
        orchestrator = TranscriptOrchestrator(strategies=custom)
        
        assert len(orchestrator.strategies) == 1
        assert orchestrator.strategies[0].method == TranscriptionMethod.YOUTUBE_API


class TestOrchestratorTranscribe:
    """Tests for orchestrator.transcribe method (requires mocking for unit tests)."""

    def test_invalid_video_id_raises(self) -> None:
        """Test that invalid video ID raises ValueError."""
        orchestrator = TranscriptOrchestrator()
        
        with pytest.raises(ValueError, match="Could not extract video ID"):
            orchestrator.transcribe("not-a-valid-url-or-id")

    def test_force_method_filters_strategies(self) -> None:
        """Test force_method parameter works."""
        orchestrator = TranscriptOrchestrator()
        
        # This should fail with "all strategies failed" since we're forcing
        # a method that won't work on a fake video
        with pytest.raises(ValueError, match="All transcription strategies failed"):
            orchestrator.transcribe(
                "dQw4w9WgXcQ",  # Valid ID but may not have captions
                force_method=TranscriptionMethod.YOUTUBE_API,
            )
