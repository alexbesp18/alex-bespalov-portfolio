"""
LLM Client wrapper for analysis module.

Provides a unified interface for interacting with LLM providers
(currently OpenAI/Anthropic) with retry logic and cost tracking.
"""

import json
import logging
import os
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Any, Dict, List

__all__ = ["LLMClient", "LLMResponse", "OpenAIClient", "AnthropicClient", "OpenRouterClient", "get_client"]

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 2.0
MAX_RETRY_DELAY = 60.0
BACKOFF_FACTOR = 2.0
JITTER_FACTOR = 0.25  # +/- 25% randomness


def _get_retry_delay(attempt: int) -> float:
    """Calculate retry delay with exponential backoff and jitter.
    
    Args:
        attempt: Current attempt number (0-indexed).
        
    Returns:
        Delay in seconds.
    """
    delay = INITIAL_RETRY_DELAY * (BACKOFF_FACTOR ** attempt)
    delay = min(delay, MAX_RETRY_DELAY)
    
    # Add jitter
    jitter_range = delay * JITTER_FACTOR
    delay = delay + random.uniform(-jitter_range, jitter_range)
    
    return max(0.1, delay)

# Cost per 1K tokens (approximate, as of Dec 2024)
OPENAI_COSTS = {
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
}

ANTHROPIC_COSTS = {
    "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
    "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
}


@dataclass
class LLMResponse:
    """Response from an LLM call.
    
    Attributes:
        content: The text content of the response.
        model: Model that was used.
        input_tokens: Number of input tokens.
        output_tokens: Number of output tokens.
        cost_usd: Estimated cost in USD.
        latency_seconds: Time taken for the request.
        raw_response: Original response object from provider.
    """
    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_seconds: float = 0.0
    raw_response: Any = None
    
    def parse_json(self) -> Dict[str, Any]:
        """Parse response content as JSON.
        
        Returns:
            Parsed JSON as dictionary.
            
        Raises:
            json.JSONDecodeError: If content is not valid JSON.
        """
        # Try to extract JSON from markdown code blocks
        content = self.content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            # Remove first and last lines (code block markers)
            content = "\n".join(lines[1:-1])
        
        return json.loads(content)


class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs,
    ) -> LLMResponse:
        """Send a completion request to the LLM.
        
        Args:
            prompt: The user prompt.
            system_prompt: Optional system prompt.
            temperature: Sampling temperature (0.0-1.0).
            max_tokens: Maximum tokens in response.
            
        Returns:
            LLMResponse with the completion.
        """
        pass


class OpenAIClient(LLMClient):
    """OpenAI API client with retry logic.
    
    Example:
        >>> client = OpenAIClient(model="gpt-4o-mini")
        >>> response = client.complete("What is 2+2?")
        >>> print(response.content)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
    ):
        """Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key. Defaults to OPENAI_API_KEY env var.
            model: Model to use (default: gpt-4o-mini).
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        
        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY env var.")
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs,
    ) -> LLMResponse:
        """Send completion request to OpenAI."""
        from openai import OpenAI, APIError, RateLimitError
        
        client = OpenAI(api_key=self.api_key)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        last_error = None
        start_time = time.time()
        
        for attempt in range(MAX_RETRIES):
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                
                latency = time.time() - start_time
                
                # Calculate cost
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                cost = self._calculate_cost(input_tokens, output_tokens)
                
                return LLMResponse(
                    content=response.choices[0].message.content,
                    model=self.model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_usd=cost,
                    latency_seconds=latency,
                    raw_response=response,
                )
                
            except RateLimitError as e:
                last_error = e
                delay = _get_retry_delay(attempt)
                logger.warning(
                    f"Rate limited (attempt {attempt + 1}/{MAX_RETRIES}), "
                    f"retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
            except APIError as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = _get_retry_delay(attempt)
                    logger.warning(
                        f"API error (attempt {attempt + 1}/{MAX_RETRIES}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
            except Exception as e:
                # Catch network errors, timeouts, etc.
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = _get_retry_delay(attempt)
                    logger.warning(
                        f"Request error (attempt {attempt + 1}/{MAX_RETRIES}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
        
        raise RuntimeError(f"OpenAI API failed after {MAX_RETRIES} attempts: {last_error}")
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for token usage."""
        costs = OPENAI_COSTS.get(self.model, {"input": 0.0, "output": 0.0})
        return (input_tokens / 1000 * costs["input"]) + (output_tokens / 1000 * costs["output"])


class AnthropicClient(LLMClient):
    """Anthropic Claude API client with retry logic.
    
    Example:
        >>> client = AnthropicClient(model="claude-3-5-sonnet-20241022")
        >>> response = client.complete("What is 2+2?")
        >>> print(response.content)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
    ):
        """Initialize Anthropic client.
        
        Args:
            api_key: Anthropic API key. Defaults to ANTHROPIC_API_KEY env var.
            model: Model to use (default: claude-3-5-sonnet).
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
        
        if not self.api_key:
            raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY env var.")
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs,
    ) -> LLMResponse:
        """Send completion request to Anthropic."""
        import anthropic
        
        client = anthropic.Anthropic(api_key=self.api_key)
        
        last_error = None
        start_time = time.time()
        
        for attempt in range(MAX_RETRIES):
            try:
                response = client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    system=system_prompt or "",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    **kwargs,
                )
                
                latency = time.time() - start_time
                
                # Calculate cost
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                cost = self._calculate_cost(input_tokens, output_tokens)
                
                return LLMResponse(
                    content=response.content[0].text,
                    model=self.model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_usd=cost,
                    latency_seconds=latency,
                    raw_response=response,
                )
                
            except anthropic.RateLimitError as e:
                last_error = e
                delay = _get_retry_delay(attempt)
                logger.warning(
                    f"Rate limited (attempt {attempt + 1}/{MAX_RETRIES}), "
                    f"retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
            except anthropic.APIError as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = _get_retry_delay(attempt)
                    logger.warning(
                        f"API error (attempt {attempt + 1}/{MAX_RETRIES}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = _get_retry_delay(attempt)
                    logger.warning(
                        f"Request error (attempt {attempt + 1}/{MAX_RETRIES}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
        
        raise RuntimeError(f"Anthropic API failed after {MAX_RETRIES} attempts: {last_error}")
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for token usage."""
        costs = ANTHROPIC_COSTS.get(self.model, {"input": 0.0, "output": 0.0})
        return (input_tokens / 1000 * costs["input"]) + (output_tokens / 1000 * costs["output"])


# OpenRouter costs (approximate)
OPENROUTER_COSTS = {
    "x-ai/grok-4.1-fast": {"input": 0.003, "output": 0.015},
    "x-ai/grok-4": {"input": 0.01, "output": 0.03},
    "anthropic/claude-3.5-sonnet": {"input": 0.003, "output": 0.015},
    "openai/gpt-4o": {"input": 0.0025, "output": 0.01},
}


class OpenRouterClient(LLMClient):
    """OpenRouter API client - access many models through one API.
    
    OpenRouter provides OpenAI-compatible API access to models from
    xAI (Grok), Anthropic, OpenAI, Meta, and more.
    
    Example:
        >>> client = OpenRouterClient(model="x-ai/grok-4.1-fast")
        >>> response = client.complete("What is 2+2?")
        >>> print(response.content)
    """
    
    BASE_URL = "https://openrouter.ai/api/v1"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "x-ai/grok-4.1-fast",
        max_tokens: int = 4000,
    ):
        """Initialize OpenRouter client.
        
        Args:
            api_key: OpenRouter API key. Defaults to OPENROUTER_API_KEY env var.
            model: Model to use (default: x-ai/grok-4.1-fast).
            max_tokens: Default max tokens for responses.
        """
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.model = model
        self.default_max_tokens = max_tokens
        
        if not self.api_key:
            raise ValueError("OpenRouter API key required. Set OPENROUTER_API_KEY env var.")
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """Send completion request to OpenRouter."""
        from openai import OpenAI, APIError, RateLimitError
        
        # OpenRouter uses OpenAI-compatible API
        client = OpenAI(
            api_key=self.api_key,
            base_url=self.BASE_URL,
        )
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        last_error = None
        start_time = time.time()
        
        actual_max_tokens = max_tokens or self.default_max_tokens
        
        for attempt in range(MAX_RETRIES):
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=actual_max_tokens,
                    **kwargs,
                )
                
                latency = time.time() - start_time
                
                # Calculate cost
                input_tokens = response.usage.prompt_tokens if response.usage else 0
                output_tokens = response.usage.completion_tokens if response.usage else 0
                cost = self._calculate_cost(input_tokens, output_tokens)
                
                return LLMResponse(
                    content=response.choices[0].message.content,
                    model=self.model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_usd=cost,
                    latency_seconds=latency,
                    raw_response=response,
                )
                
            except RateLimitError as e:
                last_error = e
                delay = _get_retry_delay(attempt)
                logger.warning(
                    f"Rate limited (attempt {attempt + 1}/{MAX_RETRIES}), "
                    f"retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
            except APIError as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = _get_retry_delay(attempt)
                    logger.warning(
                        f"API error (attempt {attempt + 1}/{MAX_RETRIES}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = _get_retry_delay(attempt)
                    logger.warning(
                        f"Request error (attempt {attempt + 1}/{MAX_RETRIES}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
        
        raise RuntimeError(f"OpenRouter API failed after {MAX_RETRIES} attempts: {last_error}")
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for token usage."""
        costs = OPENROUTER_COSTS.get(self.model, {"input": 0.003, "output": 0.015})
        return (input_tokens / 1000 * costs["input"]) + (output_tokens / 1000 * costs["output"])


def get_client(provider: str = "openrouter", **kwargs) -> LLMClient:
    """Factory function to get an LLM client.
    
    Args:
        provider: "openrouter", "openai", or "anthropic"
        **kwargs: Passed to client constructor.
        
    Returns:
        Configured LLM client.
    """
    if provider == "openrouter":
        return OpenRouterClient(**kwargs)
    elif provider == "openai":
        return OpenAIClient(**kwargs)
    elif provider == "anthropic":
        return AnthropicClient(**kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}")
