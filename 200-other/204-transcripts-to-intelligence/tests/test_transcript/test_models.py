"""
Unit tests for transcript module data models.

Tests TranscriptSegment and TranscriptionResult dataclasses.
"""

import pytest

from src.transcript.models import (
    TranscriptionMethod,
    TranscriptSegment,
    TranscriptionResult,
)


class TestTranscriptSegment:
    """Tests for TranscriptSegment dataclass."""

    def test_basic_creation(self) -> None:
        """Test creating a segment with required fields."""
        segment = TranscriptSegment(
            text="Hello world",
            start_seconds=0.0,
            end_seconds=5.0,
        )
        assert segment.text == "Hello world"
        assert segment.start_seconds == 0.0
        assert segment.end_seconds == 5.0
        assert segment.speaker is None
        assert segment.confidence is None

    def test_duration_property(self) -> None:
        """Test duration calculation."""
        segment = TranscriptSegment(
            text="Test",
            start_seconds=10.0,
            end_seconds=25.5,
        )
        assert segment.duration == 15.5

    def test_to_dict(self) -> None:
        """Test dictionary serialization."""
        segment = TranscriptSegment(
            text="Test text",
            start_seconds=1.0,
            end_seconds=2.0,
            speaker="Speaker A",
            confidence=0.95,
        )
        result = segment.to_dict()
        
        assert result["text"] == "Test text"
        assert result["start"] == 1.0
        assert result["end"] == 2.0
        assert result["speaker"] == "Speaker A"
        assert result["confidence"] == 0.95

    def test_optional_fields(self) -> None:
        """Test with optional speaker and confidence."""
        segment = TranscriptSegment(
            text="With speaker",
            start_seconds=0.0,
            end_seconds=1.0,
            speaker="John",
            confidence=0.85,
        )
        assert segment.speaker == "John"
        assert segment.confidence == 0.85


class TestTranscriptionResult:
    """Tests for TranscriptionResult dataclass."""

    @pytest.fixture
    def sample_segments(self) -> list[TranscriptSegment]:
        """Create sample segments for testing."""
        return [
            TranscriptSegment(text="First segment", start_seconds=0.0, end_seconds=5.0),
            TranscriptSegment(text="Second segment", start_seconds=5.0, end_seconds=10.0),
        ]

    def test_basic_creation(self, sample_segments: list[TranscriptSegment]) -> None:
        """Test creating a result with required fields."""
        result = TranscriptionResult(
            full_text="First segment Second segment",
            segments=sample_segments,
            method=TranscriptionMethod.YOUTUBE_API,
            video_id="test123abc",
        )
        assert result.video_id == "test123abc"
        assert result.method == TranscriptionMethod.YOUTUBE_API
        assert len(result.segments) == 2

    def test_word_count_auto_calculation(self, sample_segments: list[TranscriptSegment]) -> None:
        """Test automatic word count calculation."""
        result = TranscriptionResult(
            full_text="One two three four five",
            segments=sample_segments,
            method=TranscriptionMethod.YTDLP,
            video_id="test123abc",
        )
        assert result.word_count == 5

    def test_word_count_explicit(self, sample_segments: list[TranscriptSegment]) -> None:
        """Test explicit word count is preserved."""
        result = TranscriptionResult(
            full_text="One two three",
            segments=sample_segments,
            method=TranscriptionMethod.YTDLP,
            video_id="test123abc",
            word_count=100,  # Explicit override
        )
        assert result.word_count == 100

    def test_to_dict(self, sample_segments: list[TranscriptSegment]) -> None:
        """Test dictionary serialization."""
        result = TranscriptionResult(
            full_text="Test text",
            segments=sample_segments,
            method=TranscriptionMethod.WHISPER_API,
            video_id="abc12345678",
            language="en",
            confidence_score=0.95,
            duration_seconds=60.0,
            cost_usd=0.36,
            is_auto_generated=False,
            metadata={"model": "whisper-1"},
        )
        data = result.to_dict()
        
        assert data["video_id"] == "abc12345678"
        assert data["method"] == "whisper_api"
        assert data["language"] == "en"
        assert data["confidence_score"] == 0.95
        assert data["duration_seconds"] == 60.0
        assert data["cost_usd"] == 0.36
        assert data["is_auto_generated"] is False
        assert len(data["segments"]) == 2
        assert data["metadata"]["model"] == "whisper-1"

    def test_preview_short_text(self, sample_segments: list[TranscriptSegment]) -> None:
        """Test preview with text shorter than limit."""
        result = TranscriptionResult(
            full_text="Short text",
            segments=sample_segments,
            method=TranscriptionMethod.YOUTUBE_API,
            video_id="test123abc",
        )
        assert result.preview(500) == "Short text"

    def test_preview_long_text(self, sample_segments: list[TranscriptSegment]) -> None:
        """Test preview with text longer than limit."""
        long_text = "A" * 1000
        result = TranscriptionResult(
            full_text=long_text,
            segments=sample_segments,
            method=TranscriptionMethod.YOUTUBE_API,
            video_id="test123abc",
        )
        preview = result.preview(100)
        assert len(preview) == 103  # 100 chars + "..."
        assert preview.endswith("...")


class TestTranscriptionMethod:
    """Tests for TranscriptionMethod enum."""

    def test_enum_values(self) -> None:
        """Test enum has expected values."""
        assert TranscriptionMethod.YOUTUBE_API.value == "youtube_api"
        assert TranscriptionMethod.YTDLP.value == "ytdlp"
        assert TranscriptionMethod.WHISPER_API.value == "whisper_api"

    def test_enum_count(self) -> None:
        """Test expected number of methods."""
        assert len(TranscriptionMethod) == 3
