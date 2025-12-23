"""
Unit tests for the transcript segmenter.

Tests TranscriptSegmenter and related functions.
"""

import pytest

from src.analysis.models import TranscriptChunk, SegmentationResult
from src.analysis.segmenter import (
    TranscriptSegmenter,
    segment_transcript,
    DEFAULT_CHUNK_SIZE_SECONDS,
    DEFAULT_OVERLAP_SECONDS,
)


class MockSegment:
    """Mock TranscriptSegment for testing without importing transcript module."""
    
    def __init__(self, text: str, start: float, end: float):
        self.text = text
        self.start_seconds = start
        self.end_seconds = end


class TestTranscriptChunk:
    """Tests for TranscriptChunk dataclass."""

    def test_basic_creation(self) -> None:
        """Test creating a chunk with required fields."""
        chunk = TranscriptChunk(
            text="Hello world",
            chunk_index=0,
            start_seconds=0.0,
            end_seconds=60.0,
        )
        assert chunk.text == "Hello world"
        assert chunk.chunk_index == 0
        assert chunk.word_count == 2

    def test_duration_properties(self) -> None:
        """Test duration calculations."""
        chunk = TranscriptChunk(
            text="Test",
            chunk_index=0,
            start_seconds=0.0,
            end_seconds=180.0,
        )
        assert chunk.duration_seconds == 180.0
        assert chunk.duration_minutes == 3.0

    def test_to_dict(self) -> None:
        """Test serialization."""
        chunk = TranscriptChunk(
            text="Test chunk",
            chunk_index=1,
            start_seconds=60.0,
            end_seconds=120.0,
            overlap_words=10,
        )
        data = chunk.to_dict()
        
        assert data["chunk_index"] == 1
        assert data["start_seconds"] == 60.0
        assert data["end_seconds"] == 120.0
        assert data["overlap_words"] == 10


class TestSegmentationResult:
    """Tests for SegmentationResult dataclass."""

    def test_properties(self) -> None:
        """Test computed properties."""
        chunks = [
            TranscriptChunk("One two three", 0, 0.0, 60.0),
            TranscriptChunk("Four five six", 1, 60.0, 120.0),
        ]
        result = SegmentationResult(
            chunks=chunks,
            total_duration_seconds=120.0,
            total_word_count=6,
            chunk_size_seconds=60.0,
            overlap_seconds=0.0,
        )
        
        assert result.num_chunks == 2
        assert result.avg_chunk_words == 3.0


class TestTranscriptSegmenter:
    """Tests for TranscriptSegmenter class."""

    def test_default_initialization(self) -> None:
        """Test default segmenter creation."""
        segmenter = TranscriptSegmenter()
        
        assert segmenter.chunk_size_seconds == DEFAULT_CHUNK_SIZE_SECONDS
        assert segmenter.overlap_seconds == DEFAULT_OVERLAP_SECONDS

    def test_custom_initialization(self) -> None:
        """Test custom chunk size."""
        segmenter = TranscriptSegmenter(
            chunk_size_seconds=300.0,
            overlap_seconds=30.0,
        )
        
        assert segmenter.chunk_size_seconds == 300.0
        assert segmenter.overlap_seconds == 30.0

    def test_invalid_chunk_size_raises(self) -> None:
        """Test validation of chunk size."""
        with pytest.raises(ValueError, match="chunk_size_seconds must be between"):
            TranscriptSegmenter(chunk_size_seconds=10.0)  # Too small
        
        with pytest.raises(ValueError, match="chunk_size_seconds must be between"):
            TranscriptSegmenter(chunk_size_seconds=1000.0)  # Too large

    def test_invalid_overlap_raises(self) -> None:
        """Test validation of overlap."""
        with pytest.raises(ValueError, match="overlap_seconds must be non-negative"):
            TranscriptSegmenter(overlap_seconds=-5.0)
        
        with pytest.raises(ValueError, match="overlap_seconds must be less than"):
            TranscriptSegmenter(chunk_size_seconds=60.0, overlap_seconds=60.0)

    def test_segment_empty_list(self) -> None:
        """Test segmentation of empty segments list."""
        segmenter = TranscriptSegmenter()
        result = segmenter.segment([], 0.0)
        
        assert result.num_chunks == 0
        assert result.total_word_count == 0

    def test_segment_basic(self) -> None:
        """Test basic segmentation."""
        segments = [
            MockSegment("First segment text here.", 0.0, 60.0),
            MockSegment("Second segment continues.", 60.0, 120.0),
            MockSegment("Third segment ends.", 120.0, 180.0),
            MockSegment("Fourth segment starts.", 180.0, 240.0),
        ]
        
        segmenter = TranscriptSegmenter(
            chunk_size_seconds=120.0,
            overlap_seconds=0.0,
        )
        result = segmenter.segment(segments, 240.0)
        
        assert result.num_chunks == 2
        assert result.total_duration_seconds == 240.0

    def test_segment_with_overlap(self) -> None:
        """Test segmentation with overlap."""
        segments = [
            MockSegment("Word " * 50, 0.0, 60.0),
            MockSegment("Word " * 50, 60.0, 120.0),
            MockSegment("Word " * 50, 120.0, 180.0),
        ]
        
        segmenter = TranscriptSegmenter(
            chunk_size_seconds=100.0,
            overlap_seconds=20.0,
        )
        result = segmenter.segment(segments, 180.0)
        
        # Should create at least 2 chunks
        assert result.num_chunks >= 2


class TestSegmentByWords:
    """Tests for word-based segmentation."""

    def test_segment_by_words_basic(self) -> None:
        """Test basic word-based segmentation."""
        text = " ".join(["word"] * 1000)
        
        segmenter = TranscriptSegmenter()
        result = segmenter.segment_by_words(text, words_per_chunk=100, overlap_words=0)
        
        assert result.num_chunks == 10
        assert all(c.word_count == 100 for c in result.chunks)

    def test_segment_by_words_with_overlap(self) -> None:
        """Test word-based segmentation with overlap."""
        text = " ".join(["word"] * 200)
        
        segmenter = TranscriptSegmenter()
        result = segmenter.segment_by_words(text, words_per_chunk=100, overlap_words=20)
        
        # First chunk has no overlap, subsequent ones do
        assert result.chunks[0].overlap_words == 0
        if result.num_chunks > 1:
            assert result.chunks[1].overlap_words == 20

    def test_segment_by_words_empty(self) -> None:
        """Test word-based segmentation of empty text."""
        segmenter = TranscriptSegmenter()
        result = segmenter.segment_by_words("", words_per_chunk=100)
        
        assert result.num_chunks == 0


class TestConvenienceFunction:
    """Tests for segment_transcript function."""

    def test_convenience_function(self) -> None:
        """Test the convenience function."""
        segments = [
            MockSegment("Hello world test.", 0.0, 60.0),
            MockSegment("More content here.", 60.0, 120.0),
        ]
        
        result = segment_transcript(
            segments,
            total_duration=120.0,
            chunk_size_seconds=180.0,
        )
        
        assert result.num_chunks >= 1
        assert result.chunk_size_seconds == 180.0
