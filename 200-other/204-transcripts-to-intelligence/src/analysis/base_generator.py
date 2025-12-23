"""
Base Prompt Generator

Abstract base class for all LLM-powered generators.
Reduces code duplication across business ideas, investment thesis,
and podcaster automation generators.

Usage:
    class MyGenerator(BasePromptGenerator):
        PROMPT_PATH = "category/my_prompt.md"
        
        def generate(self, *args, **kwargs):
            template = self._get_template()
            system, user = template.format(**kwargs)
            response = self._complete(user, system)
            return self._parse_response(response)
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple

from .llm_client import LLMClient, LLMResponse, get_client

try:
    from ..prompts import PromptLoader
except ImportError:
    # Handle case where prompts module isn't loaded
    PromptLoader = None

__all__ = ["BasePromptGenerator"]

logger = logging.getLogger(__name__)


class BasePromptGenerator(ABC):
    """Abstract base class for prompt-based generators.
    
    Provides common functionality for:
    - LLM client initialization
    - Prompt template loading with caching
    - LLM completion with configurable parameters
    - Response parsing
    
    Subclasses must define:
    - PROMPT_PATH: Path to the prompt template
    - FALLBACK_SYSTEM_PROMPT: System prompt if template not found
    - FALLBACK_USER_PROMPT: User prompt template if template not found
    
    Example:
        class MyGenerator(BasePromptGenerator):
            PROMPT_PATH = "my_category/my_prompt.md"
            FALLBACK_SYSTEM_PROMPT = "You are a helpful assistant."
            FALLBACK_USER_PROMPT = "Analyze: {input}"
            
            def generate(self, input_text: str) -> MyResult:
                response = self._generate(input=input_text)
                data = response.parse_json()
                return MyResult(**data)
    """
    
    # Subclasses must override these
    PROMPT_PATH: str = ""
    FALLBACK_SYSTEM_PROMPT: str = ""
    FALLBACK_USER_PROMPT: str = ""
    
    # Default LLM parameters (can be overridden by prompt metadata)
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_MAX_TOKENS: int = 2000
    
    def __init__(
        self,
        client: Optional[LLMClient] = None,
        provider: str = "openrouter",
        model: Optional[str] = None,
        prompt_loader: Optional[Any] = None,
    ):
        """Initialize generator with LLM client and prompt loader.
        
        Args:
            client: Pre-configured LLM client.
            provider: LLM provider if creating new client.
            model: Model to use if creating new client.
            prompt_loader: Custom prompt loader.
        """
        if client:
            self.client = client
        else:
            kwargs = {"model": model} if model else {}
            self.client = get_client(provider, **kwargs)
        
        if PromptLoader is not None:
            self.prompt_loader = prompt_loader or PromptLoader()
        else:
            self.prompt_loader = None
        
        self._template = None
    
    def _get_template(self) -> Optional[Any]:
        """Load prompt template with caching.
        
        Returns:
            Loaded template or None if not found.
        """
        if self._template is not None:
            return self._template
        
        if not self.prompt_loader or not self.PROMPT_PATH:
            return None
        
        try:
            self._template = self.prompt_loader.load(self.PROMPT_PATH)
            return self._template
        except FileNotFoundError:
            logger.warning(
                f"Prompt file not found: {self.PROMPT_PATH}, using fallback"
            )
            return None
        except Exception as e:
            logger.warning(f"Failed to load prompt: {e}, using fallback")
            return None
    
    def _get_prompts(self, **format_kwargs) -> Tuple[str, str]:
        """Get system and user prompts, formatted with kwargs.
        
        Args:
            **format_kwargs: Variables to substitute in the prompt.
            
        Returns:
            Tuple of (system_prompt, user_prompt).
        """
        template = self._get_template()
        
        if template:
            return template.format(**format_kwargs)
        
        # Use fallback prompts
        system_prompt = self.FALLBACK_SYSTEM_PROMPT
        user_prompt = self.FALLBACK_USER_PROMPT.format(**format_kwargs)
        
        return system_prompt, user_prompt
    
    def _get_llm_params(self) -> Dict[str, Any]:
        """Get LLM parameters from template or defaults.
        
        Returns:
            Dict with temperature and max_tokens.
        """
        template = self._get_template()
        
        temperature = self.DEFAULT_TEMPERATURE
        max_tokens = self.DEFAULT_MAX_TOKENS
        
        if template and hasattr(template, 'metadata') and template.metadata:
            temperature = template.metadata.get("temperature", temperature)
            max_tokens = template.metadata.get("max_tokens", max_tokens)
        
        return {
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
    
    def _complete(
        self,
        user_prompt: str,
        system_prompt: str,
        **kwargs,
    ) -> LLMResponse:
        """Send completion request to LLM.
        
        Args:
            user_prompt: The user prompt.
            system_prompt: The system prompt.
            **kwargs: Additional parameters for the LLM.
            
        Returns:
            LLMResponse from the completion.
        """
        params = self._get_llm_params()
        params.update(kwargs)
        
        return self.client.complete(
            prompt=user_prompt,
            system_prompt=system_prompt,
            **params,
        )
    
    def _generate(self, **format_kwargs) -> LLMResponse:
        """Generate LLM response using prompts.
        
        This is the main method for subclasses to use.
        
        Args:
            **format_kwargs: Variables for prompt formatting.
            
        Returns:
            LLMResponse from the completion.
        """
        system_prompt, user_prompt = self._get_prompts(**format_kwargs)
        return self._complete(user_prompt, system_prompt)
    
    def _parse_json_response(
        self,
        response: LLMResponse,
        default: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Parse JSON from LLM response with error handling.
        
        Args:
            response: The LLM response.
            default: Default value if parsing fails.
            
        Returns:
            Parsed JSON dict or default.
        """
        try:
            return response.parse_json()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return default or {}
    
    @abstractmethod
    def generate(self, *args, **kwargs) -> Any:
        """Generate output from input.
        
        Subclasses must implement this method.
        
        Returns:
            Generated result (type depends on subclass).
        """
        pass

