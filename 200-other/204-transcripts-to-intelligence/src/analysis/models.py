"""
Data models for the analysis module.

Provides common data structures for transcript segmentation and analysis results.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class TranscriptChunk:
    """
    A chunk of transcript text for LLM analysis.
    
    Represents a portion of the full transcript, typically 2-5 minutes
    of content, optimized for LLM context windows.
    
    Attributes:
        text: The transcript text for this chunk.
        chunk_index: Zero-based index of this chunk.
        start_seconds: Start time in the original video.
        end_seconds: End time in the original video.
        word_count: Number of words in this chunk.
        overlap_words: Number of words overlapping with previous chunk.
    """
    text: str
    chunk_index: int
    start_seconds: float
    end_seconds: float
    word_count: int = 0
    overlap_words: int = 0
    
    def __post_init__(self):
        """Calculate word count if not provided."""
        if self.word_count == 0 and self.text:
            self.word_count = len(self.text.split())
    
    @property
    def duration_seconds(self) -> float:
        """Duration of this chunk in seconds."""
        return self.end_seconds - self.start_seconds
    
    @property
    def duration_minutes(self) -> float:
        """Duration of this chunk in minutes."""
        return self.duration_seconds / 60.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "chunk_index": self.chunk_index,
            "start_seconds": self.start_seconds,
            "end_seconds": self.end_seconds,
            "duration_seconds": self.duration_seconds,
            "word_count": self.word_count,
            "overlap_words": self.overlap_words,
            "text": self.text,
        }


@dataclass
class SegmentationResult:
    """
    Result of segmenting a transcript into chunks.
    
    Attributes:
        chunks: List of transcript chunks.
        total_duration_seconds: Total duration of the original content.
        total_word_count: Total words across all chunks (excluding overlaps).
        chunk_size_seconds: Target chunk size used for segmentation.
        overlap_seconds: Overlap between chunks for context.
    """
    chunks: List[TranscriptChunk]
    total_duration_seconds: float
    total_word_count: int
    chunk_size_seconds: float
    overlap_seconds: float
    
    @property
    def num_chunks(self) -> int:
        """Number of chunks in the result."""
        return len(self.chunks)
    
    @property
    def avg_chunk_words(self) -> float:
        """Average words per chunk."""
        if not self.chunks:
            return 0.0
        return sum(c.word_count for c in self.chunks) / len(self.chunks)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "num_chunks": self.num_chunks,
            "total_duration_seconds": self.total_duration_seconds,
            "total_word_count": self.total_word_count,
            "chunk_size_seconds": self.chunk_size_seconds,
            "overlap_seconds": self.overlap_seconds,
            "avg_chunk_words": self.avg_chunk_words,
            "chunks": [c.to_dict() for c in self.chunks],
        }
