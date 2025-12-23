"""
Custom exceptions for the transcript module.

Provides specific exception types for different failure modes,
enabling proper error handling and debugging.
"""


class TranscriptionError(Exception):
    """Base exception for all transcription-related errors.
    
    All other exceptions in this module inherit from this class,
    allowing callers to catch all transcription errors with a single handler.
    
    Example:
        try:
            result = transcribe(video_id)
        except TranscriptionError as e:
            logger.error(f"Transcription failed: {e}")
    """
    pass


class NoTranscriptAvailable(TranscriptionError):
    """Raised when no transcript/captions are available for a video.
    
    This can occur when:
        - The video has captions disabled
        - The video is too new and captions haven't been generated
        - The video's captions are in a language not requested
    
    Attributes:
        video_id: The YouTube video ID that was attempted.
        strategies_tried: List of strategies that were attempted.
    """
    
    def __init__(
        self,
        video_id: str,
        message: str = "No transcript available",
        strategies_tried: list[str] | None = None,
    ):
        self.video_id = video_id
        self.strategies_tried = strategies_tried or []
        super().__init__(f"{message} for video {video_id}")


class VideoNotAccessible(TranscriptionError):
    """Raised when a video cannot be accessed.
    
    This can occur when:
        - The video is private
        - The video has been deleted
        - The video is age-restricted and no cookies provided
        - The video is geographically restricted
        
    Attributes:
        video_id: The YouTube video ID that was attempted.
        reason: Specific reason for inaccessibility, if known.
    """
    
    def __init__(
        self,
        video_id: str,
        reason: str = "Video not accessible",
    ):
        self.video_id = video_id
        self.reason = reason
        super().__init__(f"{reason}: {video_id}")


class InvalidVideoId(TranscriptionError):
    """Raised when a video ID or URL cannot be parsed.
    
    Attributes:
        input_value: The original input that could not be parsed.
    """
    
    def __init__(self, input_value: str):
        self.input_value = input_value
        super().__init__(f"Could not extract valid video ID from: {input_value}")


class APIKeyMissingError(TranscriptionError):
    """Raised when a required API key is not configured.
    
    Attributes:
        service: Name of the service requiring the API key.
        env_var: Environment variable name that should contain the key.
    """
    
    def __init__(
        self,
        service: str = "OpenAI Whisper",
        env_var: str = "OPENAI_API_KEY",
    ):
        self.service = service
        self.env_var = env_var
        super().__init__(
            f"{service} requires API key. Set {env_var} environment variable."
        )


class TranscriptionAPIError(TranscriptionError):
    """Raised when an external API call fails.
    
    Attributes:
        service: Name of the service that failed.
        status_code: HTTP status code, if applicable.
        response: Raw response content, if available.
    """
    
    def __init__(
        self,
        service: str,
        message: str,
        status_code: int | None = None,
        response: str | None = None,
    ):
        self.service = service
        self.status_code = status_code
        self.response = response
        super().__init__(f"{service} API error: {message}")
