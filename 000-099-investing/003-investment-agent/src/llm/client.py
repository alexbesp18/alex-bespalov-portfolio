"""Unified LLM client with retry logic and multi-provider support."""

import logging
import sys
from pathlib import Path
from typing import Any

# Add shared_core to path (robust relative path)
sys.path.append(str(Path(__file__).parents[3] / "000-shared-core" / "src"))

try:
    from shared_core.llm.client import LLMClient as SharedLLMClient
except ImportError:
    logging.warning("Could not import shared_core. Ensure 000-shared-core is in python path.")
    SharedLLMClient = None

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.config import Settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class LLMClient:
    """Unified LLM client supporting multiple providers with retry logic."""
    
    def __init__(self, settings: Settings, provider: str, provider_settings: dict[str, Any]):
        """Initialize LLM client for a specific provider.
        
        Args:
            settings: Application settings
            provider: Provider name (claude, openai, grok, gemini)
            provider_settings: Provider-specific settings dictionary
        """
        self.settings = settings
        self.provider = provider
        self.provider_settings = provider_settings
        self.client_wrapper: Any = None
        self.max_tokens: int = provider_settings.get("max_tokens", 64000)
        
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the appropriate API client via Shared Core."""
        if not SharedLLMClient:
            raise ImportError("SharedLLMClient dependency missing")

        api_key = ""
        
        if self.provider == "claude":
            api_key = self.settings.anthropic_api_key
        elif self.provider == "openai":
            api_key = self.settings.openai_api_key
        elif self.provider == "grok":
            api_key = self.settings.xai_api_key
        elif self.provider == "gemini":
            api_key = self.settings.google_api_key
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
            
        if not api_key:
            raise ValueError(f"{self.provider} API key not set")
            
        # Prepare settings for shared client
        shared_settings = self.provider_settings.copy()
        
        # Shared client handles normalization, so we just pass the dict
        self.client_wrapper = SharedLLMClient(self.provider, api_key, shared_settings)
        # Exposure for introspection if needed
        self.model_name = self.client_wrapper.model_name 

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((RuntimeError, Exception)),
        reraise=True
    )
    def call_llm(self, prompt: str, max_tokens: int | None = None, stream: bool = False) -> str:
        """Call LLM with automatic retry on failure.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate (uses default if None)
            stream: Whether to stream the response (for large outputs)
            
        Returns:
            LLM response text
            
        Raises:
            RuntimeError: If LLM call fails after retries
        """
        if not self.client_wrapper:
             raise RuntimeError("Client not initialized")

        return self.client_wrapper.call_llm(prompt, max_tokens=max_tokens, stream=stream)
