"""
Unit tests for topic extractor.

Tests TopicExtractor with mocked LLM responses.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from src.analysis.models import TranscriptChunk
from src.analysis.topic_extractor import (
    TopicExtractor,
    TopicExtractionResult,
    ChunkAnalysis,
    Quote,
)
from src.analysis.llm_client import LLMResponse


class TestQuote:
    """Tests for Quote dataclass."""

    def test_basic_creation(self) -> None:
        """Test creating a quote."""
        quote = Quote(text="This is a quote", speaker="John")
        assert quote.text == "This is a quote"
        assert quote.speaker == "John"

    def test_default_speaker(self) -> None:
        """Test default speaker is Unknown."""
        quote = Quote(text="Quote text")
        assert quote.speaker == "Unknown"

    def test_to_dict(self) -> None:
        """Test serialization."""
        quote = Quote(text="Test", speaker="Jane")
        assert quote.to_dict() == {"text": "Test", "speaker": "Jane"}


class TestChunkAnalysis:
    """Tests for ChunkAnalysis dataclass."""

    def test_basic_creation(self) -> None:
        """Test creating an analysis."""
        analysis = ChunkAnalysis(
            chunk_index=0,
            start_seconds=0.0,
            end_seconds=60.0,
            topics=["AI", "Technology"],
            summary="Discussion about AI",
            quote=Quote(text="AI is transformative"),
        )
        assert analysis.chunk_index == 0
        assert len(analysis.topics) == 2

    def test_to_dict(self) -> None:
        """Test serialization."""
        analysis = ChunkAnalysis(
            chunk_index=1,
            start_seconds=60.0,
            end_seconds=120.0,
            topics=["Topic1"],
            summary="Summary text",
            quote=Quote(text="A quote"),
            cost_usd=0.001,
        )
        data = analysis.to_dict()
        
        assert data["chunk_index"] == 1
        assert data["topics"] == ["Topic1"]
        assert data["cost_usd"] == 0.001


class TestTopicExtractionResult:
    """Tests for TopicExtractionResult dataclass."""

    @pytest.fixture
    def sample_analyses(self) -> list[ChunkAnalysis]:
        """Create sample analyses for testing."""
        return [
            ChunkAnalysis(
                chunk_index=0,
                start_seconds=0.0,
                end_seconds=60.0,
                topics=["AI", "Technology"],
                summary="First chunk",
                quote=Quote(text="Quote 1"),
                cost_usd=0.001,
            ),
            ChunkAnalysis(
                chunk_index=1,
                start_seconds=60.0,
                end_seconds=120.0,
                topics=["AI", "Business"],  # AI is duplicate
                summary="Second chunk",
                quote=Quote(text="Quote 2"),
                cost_usd=0.001,
            ),
        ]

    def test_topic_deduplication(self, sample_analyses: list[ChunkAnalysis]) -> None:
        """Test that topics are deduplicated."""
        result = TopicExtractionResult(analyses=sample_analyses)
        
        # Should have 3 unique topics, not 4
        assert len(result.all_topics) == 3
        assert "AI" in result.all_topics
        assert "Technology" in result.all_topics
        assert "Business" in result.all_topics

    def test_total_cost(self, sample_analyses: list[ChunkAnalysis]) -> None:
        """Test total cost calculation."""
        result = TopicExtractionResult(analyses=sample_analyses)
        assert result.total_cost_usd == 0.002

    def test_all_quotes(self, sample_analyses: list[ChunkAnalysis]) -> None:
        """Test getting all quotes."""
        result = TopicExtractionResult(analyses=sample_analyses)
        quotes = result.all_quotes
        
        assert len(quotes) == 2
        assert quotes[0].text == "Quote 1"

    def test_empty_analyses(self) -> None:
        """Test with empty analyses list."""
        result = TopicExtractionResult(analyses=[])
        
        assert result.num_chunks == 0
        assert result.all_topics == []
        assert result.total_cost_usd == 0.0


class TestTopicExtractor:
    """Tests for TopicExtractor class."""

    @pytest.fixture
    def mock_client(self) -> Mock:
        """Create a mock LLM client."""
        client = Mock()
        client.complete.return_value = LLMResponse(
            content='{"topics": ["AI", "Technology"], "summary": "Test summary", "quote": {"text": "A quote", "speaker": "John"}}',
            model="test-model",
            input_tokens=100,
            output_tokens=50,
            cost_usd=0.001,
        )
        return client

    @pytest.fixture
    def sample_chunk(self) -> TranscriptChunk:
        """Create a sample chunk for testing."""
        return TranscriptChunk(
            text="This is a test transcript about AI and technology.",
            chunk_index=0,
            start_seconds=0.0,
            end_seconds=60.0,
        )

    def test_extract_single(
        self, mock_client: Mock, sample_chunk: TranscriptChunk
    ) -> None:
        """Test extracting from a single chunk."""
        extractor = TopicExtractor(client=mock_client)
        analysis = extractor.extract_single(sample_chunk)
        
        assert analysis.chunk_index == 0
        assert analysis.topics == ["AI", "Technology"]
        assert analysis.summary == "Test summary"
        assert analysis.quote.text == "A quote"
        assert analysis.cost_usd == 0.001

    def test_extract_multiple(
        self, mock_client: Mock, sample_chunk: TranscriptChunk
    ) -> None:
        """Test extracting from multiple chunks."""
        chunks = [
            sample_chunk,
            TranscriptChunk(
                text="Second chunk content.",
                chunk_index=1,
                start_seconds=60.0,
                end_seconds=120.0,
            ),
        ]
        
        extractor = TopicExtractor(client=mock_client)
        result = extractor.extract(chunks)
        
        assert result.num_chunks == 2
        assert mock_client.complete.call_count == 2

    def test_extract_with_max_chunks(
        self, mock_client: Mock, sample_chunk: TranscriptChunk
    ) -> None:
        """Test max_chunks parameter."""
        chunks = [sample_chunk] * 5  # 5 chunks
        
        extractor = TopicExtractor(client=mock_client)
        result = extractor.extract(chunks, max_chunks=2)
        
        assert result.num_chunks == 2
        assert mock_client.complete.call_count == 2

    def test_extract_empty_chunks(self, mock_client: Mock) -> None:
        """Test with empty chunks list."""
        extractor = TopicExtractor(client=mock_client)
        result = extractor.extract([])
        
        assert result.num_chunks == 0
        assert mock_client.complete.call_count == 0

    def test_json_parsing_error_handled(
        self, sample_chunk: TranscriptChunk
    ) -> None:
        """Test handling of JSON parsing errors."""
        client = Mock()
        client.complete.return_value = LLMResponse(
            content="Not valid JSON",
            model="test-model",
            cost_usd=0.001,
        )
        
        extractor = TopicExtractor(client=client)
        analysis = extractor.extract_single(sample_chunk)
        
        # Should return a minimal result, not crash
        assert analysis.topics == ["Parsing error"]
        assert "Failed to parse" in analysis.summary

    def test_format_time(self, mock_client: Mock) -> None:
        """Test time formatting."""
        extractor = TopicExtractor(client=mock_client)
        
        assert extractor._format_time(0) == "00:00"
        assert extractor._format_time(65) == "01:05"
        assert extractor._format_time(3661) == "61:01"
