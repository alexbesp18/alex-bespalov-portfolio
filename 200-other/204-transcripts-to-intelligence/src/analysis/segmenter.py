"""
Transcript Segmenter

Splits transcripts into chunks optimized for LLM analysis.
Supports time-based chunking with configurable overlap for context preservation.
"""

import logging
from typing import List, Optional

from .models import TranscriptChunk, SegmentationResult

__all__ = ["TranscriptSegmenter", "segment_transcript"]

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CHUNK_SIZE_SECONDS = 180.0  # 3 minutes
DEFAULT_OVERLAP_SECONDS = 15.0  # 15 seconds overlap
MIN_CHUNK_SIZE_SECONDS = 30.0  # Minimum chunk size
MAX_CHUNK_SIZE_SECONDS = 600.0  # Maximum 10 minutes


class TranscriptSegmenter:
    """
    Splits transcripts into chunks for LLM processing.
    
    Uses time-based segmentation to create chunks of approximately equal
    duration, with optional overlap to preserve context between chunks.
    
    Attributes:
        chunk_size_seconds: Target duration for each chunk.
        overlap_seconds: Overlap between consecutive chunks.
        
    Example:
        >>> from src.transcript import transcribe
        >>> result = transcribe("VIDEO_ID")
        >>> segmenter = TranscriptSegmenter(chunk_size_seconds=180)
        >>> chunks = segmenter.segment(result.segments, result.duration_seconds)
        >>> print(f"Split into {chunks.num_chunks} chunks")
    """
    
    def __init__(
        self,
        chunk_size_seconds: float = DEFAULT_CHUNK_SIZE_SECONDS,
        overlap_seconds: float = DEFAULT_OVERLAP_SECONDS,
    ):
        """
        Initialize the segmenter.
        
        Args:
            chunk_size_seconds: Target duration for each chunk (default: 180s).
            overlap_seconds: Overlap between chunks for context (default: 15s).
            
        Raises:
            ValueError: If chunk_size is outside allowed range.
        """
        if not MIN_CHUNK_SIZE_SECONDS <= chunk_size_seconds <= MAX_CHUNK_SIZE_SECONDS:
            raise ValueError(
                f"chunk_size_seconds must be between {MIN_CHUNK_SIZE_SECONDS} "
                f"and {MAX_CHUNK_SIZE_SECONDS}, got {chunk_size_seconds}"
            )
        
        if overlap_seconds < 0:
            raise ValueError("overlap_seconds must be non-negative")
        
        if overlap_seconds >= chunk_size_seconds:
            raise ValueError("overlap_seconds must be less than chunk_size_seconds")
        
        self.chunk_size_seconds = chunk_size_seconds
        self.overlap_seconds = overlap_seconds
    
    def segment(
        self,
        segments: List,  # List[TranscriptSegment] from transcript module
        total_duration: float,
    ) -> SegmentationResult:
        """
        Segment transcript into chunks.
        
        Args:
            segments: List of TranscriptSegment objects from transcript module.
            total_duration: Total duration of the transcript in seconds.
            
        Returns:
            SegmentationResult containing all chunks.
        """
        if not segments:
            logger.warning("Empty segments list provided")
            return SegmentationResult(
                chunks=[],
                total_duration_seconds=0.0,
                total_word_count=0,
                chunk_size_seconds=self.chunk_size_seconds,
                overlap_seconds=self.overlap_seconds,
            )
        
        chunks: List[TranscriptChunk] = []
        chunk_index = 0
        
        # Calculate chunk boundaries
        effective_chunk_size = self.chunk_size_seconds - self.overlap_seconds
        current_start = 0.0
        
        while current_start < total_duration:
            chunk_end = min(current_start + self.chunk_size_seconds, total_duration)
            
            # Find segments that fall within this chunk
            chunk_segments = self._get_segments_in_range(
                segments, current_start, chunk_end
            )
            
            if chunk_segments:
                # Combine segment texts
                chunk_text = " ".join(seg.text for seg in chunk_segments)
                
                # Calculate actual start/end from segment boundaries
                actual_start = chunk_segments[0].start_seconds
                actual_end = chunk_segments[-1].end_seconds
                
                # Calculate overlap words (from previous chunk)
                overlap_words = 0
                if chunks and self.overlap_seconds > 0:
                    overlap_words = self._count_overlap_words(
                        chunks[-1], chunk_text
                    )
                
                chunks.append(TranscriptChunk(
                    text=chunk_text,
                    chunk_index=chunk_index,
                    start_seconds=actual_start,
                    end_seconds=actual_end,
                    overlap_words=overlap_words,
                ))
                
                chunk_index += 1
            
            # Move to next chunk, accounting for overlap
            current_start += effective_chunk_size
        
        # Calculate total word count (excluding overlaps)
        total_word_count = sum(
            c.word_count - c.overlap_words for c in chunks
        )
        
        logger.info(
            f"Segmented {total_duration:.1f}s transcript into {len(chunks)} chunks "
            f"(avg {total_word_count / len(chunks):.0f} words each)"
        )
        
        return SegmentationResult(
            chunks=chunks,
            total_duration_seconds=total_duration,
            total_word_count=total_word_count,
            chunk_size_seconds=self.chunk_size_seconds,
            overlap_seconds=self.overlap_seconds,
        )
    
    def segment_by_words(
        self,
        full_text: str,
        words_per_chunk: int = 500,
        overlap_words: int = 50,
    ) -> SegmentationResult:
        """
        Segment by word count instead of time.
        
        Useful when segment timing is not available or when you want
        consistent token counts for LLM processing.
        
        Args:
            full_text: Complete transcript text.
            words_per_chunk: Target words per chunk (default: 500).
            overlap_words: Words to overlap between chunks (default: 50).
            
        Returns:
            SegmentationResult containing all chunks.
        """
        words = full_text.split()
        total_words = len(words)
        
        if total_words == 0:
            return SegmentationResult(
                chunks=[],
                total_duration_seconds=0.0,
                total_word_count=0,
                chunk_size_seconds=0.0,
                overlap_seconds=0.0,
            )
        
        chunks: List[TranscriptChunk] = []
        chunk_index = 0
        effective_chunk_size = words_per_chunk - overlap_words
        
        start_idx = 0
        while start_idx < total_words:
            end_idx = min(start_idx + words_per_chunk, total_words)
            chunk_words = words[start_idx:end_idx]
            chunk_text = " ".join(chunk_words)
            
            # Estimate timing (assuming ~150 words per minute)
            estimated_start = (start_idx / 150) * 60
            estimated_end = (end_idx / 150) * 60
            
            actual_overlap = overlap_words if chunk_index > 0 else 0
            
            chunks.append(TranscriptChunk(
                text=chunk_text,
                chunk_index=chunk_index,
                start_seconds=estimated_start,
                end_seconds=estimated_end,
                word_count=len(chunk_words),
                overlap_words=actual_overlap,
            ))
            
            chunk_index += 1
            start_idx += effective_chunk_size
        
        return SegmentationResult(
            chunks=chunks,
            total_duration_seconds=chunks[-1].end_seconds if chunks else 0.0,
            total_word_count=total_words,
            chunk_size_seconds=0.0,  # Not applicable for word-based
            overlap_seconds=0.0,
        )
    
    def _get_segments_in_range(
        self,
        segments: List,
        start_time: float,
        end_time: float,
    ) -> List:
        """Get segments that overlap with the given time range."""
        return [
            seg for seg in segments
            if seg.end_seconds > start_time and seg.start_seconds < end_time
        ]
    
    def _count_overlap_words(
        self,
        previous_chunk: TranscriptChunk,
        current_text: str,
    ) -> int:
        """Estimate overlap words between consecutive chunks."""
        # Simple estimation based on overlap ratio
        prev_words = previous_chunk.text.split()
        curr_words = current_text.split()
        
        # Find common suffix/prefix
        overlap_count = 0
        max_overlap = min(len(prev_words), len(curr_words), 100)
        
        for i in range(1, max_overlap + 1):
            if prev_words[-i:] == curr_words[:i]:
                overlap_count = i
        
        return overlap_count


def segment_transcript(
    segments: List,
    total_duration: float,
    chunk_size_seconds: float = DEFAULT_CHUNK_SIZE_SECONDS,
    overlap_seconds: float = DEFAULT_OVERLAP_SECONDS,
) -> SegmentationResult:
    """
    Convenience function to segment a transcript.
    
    Args:
        segments: List of TranscriptSegment objects.
        total_duration: Total duration in seconds.
        chunk_size_seconds: Target chunk size (default: 180s).
        overlap_seconds: Overlap between chunks (default: 15s).
        
    Returns:
        SegmentationResult with all chunks.
    """
    segmenter = TranscriptSegmenter(
        chunk_size_seconds=chunk_size_seconds,
        overlap_seconds=overlap_seconds,
    )
    return segmenter.segment(segments, total_duration)
