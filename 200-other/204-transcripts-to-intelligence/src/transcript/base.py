"""
Abstract base class for transcription strategies.

All transcription strategies must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import Optional

from .models import TranscriptionResult, TranscriptionMethod


class TranscriptionStrategy(ABC):
    """Abstract base class for all transcription strategies."""
    
    # Subclasses must set these
    method: TranscriptionMethod
    priority: int  # Lower = tried first (1 = highest priority)
    
    @abstractmethod
    def is_available(self, video_id: str) -> bool:
        """
        Check if this strategy can be used for the given video.
        
        Args:
            video_id: YouTube video ID (11-character string)
            
        Returns:
            True if this strategy can transcribe the video
        """
        pass
    
    @abstractmethod
    def transcribe(self, video_id: str, **kwargs) -> TranscriptionResult:
        """
        Perform transcription and return result.
        
        Args:
            video_id: YouTube video ID
            **kwargs: Strategy-specific options
            
        Returns:
            TranscriptionResult with full transcript
            
        Raises:
            Exception if transcription fails
        """
        pass
    
    @property
    @abstractmethod
    def estimated_cost_per_hour(self) -> float:
        """
        Return estimated cost in USD per hour of audio.
        
        Returns:
            Cost in USD (0.0 for free strategies)
        """
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(method={self.method.value}, priority={self.priority})"
