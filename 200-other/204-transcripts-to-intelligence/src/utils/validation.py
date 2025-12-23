"""
Input Validation Utilities

Provides validation and sanitization for user inputs.
"""

import re
import unicodedata
from typing import Optional
from urllib.parse import parse_qs, urlparse

__all__ = [
    "validate_youtube_url",
    "sanitize_filename",
    "extract_video_id_safe",
    "ValidationError",
]


class ValidationError(ValueError):
    """Raised when input validation fails."""
    pass


# YouTube URL patterns
YOUTUBE_PATTERNS = [
    # Standard watch URL
    r'^(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
    # Short URL
    r'^(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})',
    # Embed URL
    r'^(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
    # Shorts URL
    r'^(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
    # Just the video ID
    r'^([a-zA-Z0-9_-]{11})$',
]

COMPILED_PATTERNS = [re.compile(p) for p in YOUTUBE_PATTERNS]


def validate_youtube_url(url: str) -> bool:
    """Validate that a string is a valid YouTube URL or video ID.
    
    Args:
        url: The URL or video ID to validate.
        
    Returns:
        True if valid, False otherwise.
        
    Example:
        >>> validate_youtube_url("https://youtube.com/watch?v=dQw4w9WgXcQ")
        True
        >>> validate_youtube_url("dQw4w9WgXcQ")
        True
        >>> validate_youtube_url("not-a-valid-url")
        False
    """
    if not url or not isinstance(url, str):
        return False
    
    url = url.strip()
    
    for pattern in COMPILED_PATTERNS:
        if pattern.match(url):
            return True
    
    return False


def extract_video_id_safe(url: str) -> Optional[str]:
    """Extract YouTube video ID from URL with validation.
    
    Args:
        url: YouTube URL or video ID.
        
    Returns:
        11-character video ID, or None if invalid.
        
    Example:
        >>> extract_video_id_safe("https://youtube.com/watch?v=dQw4w9WgXcQ")
        'dQw4w9WgXcQ'
        >>> extract_video_id_safe("invalid")
        None
    """
    if not url or not isinstance(url, str):
        return None
    
    url = url.strip()
    
    # Try each pattern
    for pattern in COMPILED_PATTERNS:
        match = pattern.match(url)
        if match:
            return match.group(1)
    
    # Try parsing as URL with query params
    try:
        parsed = urlparse(url)
        if parsed.netloc in ('youtube.com', 'www.youtube.com'):
            query_params = parse_qs(parsed.query)
            video_id = query_params.get('v', [None])[0]
            if video_id and len(video_id) == 11:
                return video_id
    except Exception:
        pass
    
    return None


def sanitize_filename(
    name: str,
    max_length: int = 50,
    replacement: str = "_",
) -> str:
    """Sanitize a string to be safe for use as a filename.
    
    Removes or replaces characters that could cause issues:
    - Path separators (/, \\)
    - Special characters
    - Unicode normalization
    - Leading/trailing whitespace
    - Reserved filenames (Windows)
    
    Args:
        name: The string to sanitize.
        max_length: Maximum length of the result.
        replacement: Character to replace invalid chars with.
        
    Returns:
        Safe filename string.
        
    Example:
        >>> sanitize_filename("My Video: Episode 1/2!")
        'my_video_episode_1_2'
        >>> sanitize_filename("../../../etc/passwd")
        'etc_passwd'
    """
    if not name:
        return "untitled"
    
    # Normalize unicode
    name = unicodedata.normalize('NFKD', name)
    
    # Convert to ASCII, ignoring errors
    name = name.encode('ascii', 'ignore').decode('ascii')
    
    # Remove path separators and dangerous patterns
    name = re.sub(r'[/\\]', replacement, name)
    name = re.sub(r'\.\.', '', name)  # Remove directory traversal
    
    # Replace non-alphanumeric (except space, dash, underscore)
    name = re.sub(r'[^\w\s-]', '', name)
    
    # Replace whitespace with replacement
    name = re.sub(r'\s+', replacement, name)
    
    # Replace multiple replacements with single
    name = re.sub(f'{re.escape(replacement)}+', replacement, name)
    
    # Lowercase and strip
    name = name.lower().strip(replacement)
    
    # Truncate
    if len(name) > max_length:
        name = name[:max_length].rstrip(replacement)
    
    # Handle reserved Windows filenames
    reserved = {'con', 'prn', 'aux', 'nul', 'com1', 'lpt1'}
    if name.lower() in reserved:
        name = f"{name}_file"
    
    return name or "untitled"


def validate_priority(priority: str) -> str:
    """Validate and normalize priority level.
    
    Args:
        priority: Priority string.
        
    Returns:
        Normalized priority ('high', 'normal', 'low').
        
    Raises:
        ValidationError: If priority is invalid.
    """
    valid = {'high', 'normal', 'low'}
    normalized = priority.lower().strip()
    
    if normalized not in valid:
        raise ValidationError(
            f"Invalid priority '{priority}'. Must be one of: {valid}"
        )
    
    return normalized


def validate_urgency(urgency: str) -> str:
    """Validate and normalize urgency level.
    
    Args:
        urgency: Urgency string.
        
    Returns:
        Normalized urgency ('high', 'medium', 'low').
        
    Raises:
        ValidationError: If urgency is invalid.
    """
    valid = {'high', 'medium', 'low'}
    normalized = urgency.lower().strip()
    
    if normalized not in valid:
        raise ValidationError(
            f"Invalid urgency '{urgency}'. Must be one of: {valid}"
        )
    
    return normalized

