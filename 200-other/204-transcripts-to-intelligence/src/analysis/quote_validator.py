"""
Quote Validator

Validates that LLM-generated quotes actually exist in the original transcript.
Returns validation status and closest matches for invalid quotes.
"""

import logging
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import List, Optional, Dict, Any, Tuple

__all__ = ["QuoteValidator", "QuoteValidationResult"]

logger = logging.getLogger(__name__)

# Thresholds
DEFAULT_SIMILARITY_THRESHOLD = 0.8  # 80% similarity to consider a match
DEFAULT_FUZZY_THRESHOLD = 0.6  # 60% similarity to suggest as close match


@dataclass
class QuoteValidationResult:
    """Result of validating a single quote.
    
    Attributes:
        original_quote: The quote that was validated.
        is_valid: True if quote exists in transcript.
        similarity_score: Best match similarity (0.0-1.0).
        matched_text: The matched text from transcript (if valid).
        closest_match: Closest match if not exactly valid.
        start_position: Character position in transcript (if found).
    """
    original_quote: str
    is_valid: bool
    similarity_score: float
    matched_text: Optional[str] = None
    closest_match: Optional[str] = None
    start_position: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_quote": self.original_quote,
            "is_valid": self.is_valid,
            "similarity_score": self.similarity_score,
            "matched_text": self.matched_text,
            "closest_match": self.closest_match,
            "start_position": self.start_position,
        }


class QuoteValidator:
    """Validates quotes against the original transcript.
    
    Performs both exact matching and fuzzy matching to handle
    minor LLM paraphrasing or transcription variations.
    
    Example:
        >>> validator = QuoteValidator(transcript_text)
        >>> result = validator.validate("AI is transformative")
        >>> print(f"Valid: {result.is_valid} ({result.similarity_score:.0%})")
    """
    
    def __init__(
        self,
        transcript: str,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        fuzzy_threshold: float = DEFAULT_FUZZY_THRESHOLD,
    ):
        """Initialize validator with transcript.
        
        Args:
            transcript: The original transcript text.
            similarity_threshold: Minimum similarity for valid match.
            fuzzy_threshold: Minimum similarity for closest match suggestion.
        """
        self.transcript = transcript
        self.transcript_lower = transcript.lower()
        self.similarity_threshold = similarity_threshold
        self.fuzzy_threshold = fuzzy_threshold
        
        # Pre-process: normalize whitespace
        self.normalized_transcript = self._normalize(transcript)
    
    def validate(self, quote: str) -> QuoteValidationResult:
        """Validate a single quote against the transcript.
        
        Args:
            quote: The quote to validate.
            
        Returns:
            QuoteValidationResult with validation details.
        """
        if not quote or not quote.strip():
            return QuoteValidationResult(
                original_quote=quote,
                is_valid=False,
                similarity_score=0.0,
            )
        
        normalized_quote = self._normalize(quote)
        
        # Step 1: Try exact match (case-insensitive)
        exact_pos = self.transcript_lower.find(quote.lower())
        if exact_pos >= 0:
            return QuoteValidationResult(
                original_quote=quote,
                is_valid=True,
                similarity_score=1.0,
                matched_text=self.transcript[exact_pos:exact_pos + len(quote)],
                start_position=exact_pos,
            )
        
        # Step 2: Try normalized match
        norm_pos = self.normalized_transcript.lower().find(normalized_quote.lower())
        if norm_pos >= 0:
            return QuoteValidationResult(
                original_quote=quote,
                is_valid=True,
                similarity_score=0.95,
                matched_text=normalized_quote,
                start_position=norm_pos,
            )
        
        # Step 3: Fuzzy match - find best matching window
        best_match, best_score, best_pos = self._find_best_match(normalized_quote)
        
        is_valid = best_score >= self.similarity_threshold
        
        return QuoteValidationResult(
            original_quote=quote,
            is_valid=is_valid,
            similarity_score=best_score,
            matched_text=best_match if is_valid else None,
            closest_match=best_match if not is_valid and best_score >= self.fuzzy_threshold else None,
            start_position=best_pos if is_valid else None,
        )
    
    def validate_many(self, quotes: List[str]) -> List[QuoteValidationResult]:
        """Validate multiple quotes.
        
        Args:
            quotes: List of quotes to validate.
            
        Returns:
            List of validation results.
        """
        return [self.validate(q) for q in quotes]
    
    def validation_summary(self, quotes: List[str]) -> Dict[str, Any]:
        """Get summary statistics for quote validation.
        
        Args:
            quotes: List of quotes to validate.
            
        Returns:
            Summary with counts and percentages.
        """
        results = self.validate_many(quotes)
        
        valid_count = sum(1 for r in results if r.is_valid)
        total = len(results)
        
        return {
            "total_quotes": total,
            "valid_quotes": valid_count,
            "invalid_quotes": total - valid_count,
            "validation_rate": valid_count / total if total > 0 else 0.0,
            "average_similarity": sum(r.similarity_score for r in results) / total if total > 0 else 0.0,
            "results": [r.to_dict() for r in results],
        }
    
    def _normalize(self, text: str) -> str:
        """Normalize text for comparison."""
        # Remove extra whitespace
        text = " ".join(text.split())
        # Remove some punctuation that might differ
        text = re.sub(r"[""''\"']", "", text)
        return text.strip()
    
    def _find_best_match(
        self, quote: str, window_factor: float = 1.5
    ) -> Tuple[str, float, int]:
        """Find the best matching window in the transcript.
        
        Uses a sliding window approach to find the substring
        with highest similarity to the quote.
        """
        quote_len = len(quote)
        window_size = int(quote_len * window_factor)
        
        best_match = ""
        best_score = 0.0
        best_pos = -1
        
        # Sample positions to avoid O(n*m) complexity on long transcripts
        transcript = self.normalized_transcript
        step = max(1, len(transcript) // 1000)  # At most 1000 comparisons
        
        for i in range(0, len(transcript) - window_size + 1, step):
            window = transcript[i:i + window_size]
            
            # Quick length check
            if abs(len(window) - quote_len) > quote_len * 0.5:
                continue
            
            score = SequenceMatcher(None, quote.lower(), window.lower()).ratio()
            
            if score > best_score:
                best_score = score
                best_match = window
                best_pos = i
        
        return best_match, best_score, best_pos
