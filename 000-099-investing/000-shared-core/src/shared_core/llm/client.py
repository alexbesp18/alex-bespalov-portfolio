"""Unified LLM client with retry logic and multi-provider support."""

import logging
from typing import Any, Dict, Optional

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

# Use standard logging, let consumer configure handlers
logger = logging.getLogger(__name__)


class LLMClient:
    """Unified LLM client supporting multiple providers with retry logic."""
    
    def __init__(self, provider: str, api_key: str, provider_settings: Dict[str, Any]):
        """Initialize LLM client for a specific provider.
        
        Args:
            provider: Provider name (claude, openai, grok, gemini)
            api_key: API key for the provider
            provider_settings: Provider-specific settings dictionary.
                             Should contain 'model' and optionally 'max_tokens', etc.
        """
        self.provider = provider
        self.api_key = api_key
        self.provider_settings = provider_settings
        self.client: Any = None
        self.model_name: str = ""
        self.max_tokens: int = provider_settings.get("max_tokens", 64000)
        
        self._initialize_client()
        self._sanitize_caps()
    
    def _initialize_client(self) -> None:
        """Initialize the appropriate API client."""
        if not self.api_key:
            raise ValueError(f"API key not provided for {self.provider}")

        if self.provider == "claude":
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
            self.model_name = self._get_model_mapping("claude", self.provider_settings.get("model", ""))
            
        elif self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            self.model_name = self._get_model_mapping("openai", self.provider_settings.get("model", ""))
            
        elif self.provider == "grok":
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.x.ai/v1"
            )
            self.model_name = self._get_model_mapping("grok", self.provider_settings.get("model", ""))
            
        elif self.provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai
            self.model_name = self._get_model_mapping("gemini", self.provider_settings.get("model", ""))
            
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
            
        # Update max_tokens from settings if present
        if "max_tokens" in self.provider_settings:
            self.max_tokens = self.provider_settings["max_tokens"]
    
    def _get_model_mapping(self, provider: str, model_key: str) -> str:
        """Map config model names to actual API model strings.
        
        Args:
            provider: Provider name
            model_key: Model key from config
            
        Returns:
            Actual API model string
        """
        mappings = {
            "claude": {
                "sonnet-4.5": "claude-sonnet-4-20250514",
                "opus-4.1": "claude-opus-4-20250514"
            },
            "openai": {
                "gpt-5": "gpt-5",
                "gpt-5-mini": "gpt-5-mini",
                "gpt-5-nano": "gpt-5-nano",
                "gpt-4": "gpt-4",
            },
            "grok": {
                "grok-4": "grok-4",
                "grok-4-fast": "grok-4-fast",
                "grok-3-mini": "grok-3-mini"
            },
            "gemini": {
                "gemini-2.5-pro": "gemini-2.5-pro",
                "gemini-2.5-flash": "gemini-2.5-flash"
            }
        }
        return mappings.get(provider, {}).get(model_key, model_key)
    
    def _sanitize_caps(self) -> None:
        """Normalize caps and budgets to avoid common API errors."""
        try:
            if self.provider == "claude" and self.provider_settings.get("use_extended_thinking"):
                mb = int(self.provider_settings.get("thinking_budget_tokens", 0))
                mt = int(self.provider_settings.get("max_tokens", 0))
                if mb >= mt:
                    # Keep budget strictly less than max tokens
                    self.provider_settings["thinking_budget_tokens"] = max(mt - 1, 0)
            if self.provider == "grok":
                # Grok-4 uses a combined context window around 256k, keep output conservative
                self.max_tokens = min(self.max_tokens or 0, 128000)
        except Exception as e:
            logger.warning(f"Error sanitizing caps: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((RuntimeError, Exception)),
        reraise=True
    )
    def call_llm(self, prompt: str, system_message: str | None = None, max_tokens: int | None = None, stream: bool = False) -> str:
        """Call LLM with automatic retry on failure.
        
        Args:
            prompt: Input prompt
            system_message: Optional system instruction
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            LLM response text
        """
        if max_tokens is None:
            max_tokens = self.max_tokens
        
        logger.debug(f"Calling {self.provider} model {self.model_name} with {max_tokens} max tokens")
        
        try:
            if self.provider == "claude":
                return self._call_claude(prompt, system_message, max_tokens, stream)
            elif self.provider == "openai":
                return self._call_openai(prompt, system_message, max_tokens)
            elif self.provider == "grok":
                return self._call_grok(prompt, system_message, max_tokens)
            elif self.provider == "gemini":
                return self._call_gemini(prompt, system_message, max_tokens)
            else:
                raise ValueError(f"Unknown provider: {self.provider}")
        except Exception as e:
            logger.error(f"LLM call failed: {e}", exc_info=True)
            raise RuntimeError(f"{self.provider} call failed: {e}") from e
    
    def _call_claude(self, prompt: str, system_message: str | None, max_tokens: int, stream: bool) -> str:
        """Call Claude API."""
        thinking_arg = None
        if self.provider_settings.get("use_extended_thinking"):
            try:
                think_budget = min(
                    int(self.provider_settings.get("thinking_budget_tokens", 0)),
                    int(self.provider_settings.get("max_tokens", 0)) - 1
                )
                if think_budget > 0:
                    thinking_arg = {"type": "enabled", "budget_tokens": think_budget}
            except Exception:
                thinking_arg = None
        
        kwargs = {
            "model": self.model_name,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "thinking": thinking_arg if thinking_arg else None
        }
        
        if system_message:
            kwargs["system"] = system_message
            
        if stream and max_tokens > 16000:
            response_text = ""
            try:
                with self.client.messages.stream(**kwargs) as stream_response:
                    for text in stream_response.text_stream:
                        response_text += text
                return response_text
            except Exception:
                pass
        
        kwargs["timeout"] = 600.0
        response = self.client.messages.create(**kwargs)
        return "".join([blk.text for blk in response.content if getattr(blk, "text", None)])
    
    def _call_openai(self, prompt: str, system_message: str | None, max_tokens: int) -> str:
        """Call OpenAI Responses API."""
        use_web = self.provider_settings.get("web_search", {}).get("enabled", False)
        reasoning_effort = self.provider_settings.get("reasoning_effort", "medium")
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        tools = [{"type": "web_search"}] if use_web else None
        
        resp = self.client.responses.create(
            model=self.model_name,
            input=messages,
            max_output_tokens=max_tokens,
            reasoning={"effort": reasoning_effort},
            tools=tools
        )
        return getattr(resp, "output_text", None) or self._responses_text_fallback(resp)
    
    def _call_grok(self, prompt: str, system_message: str | None, max_tokens: int) -> str:
        """Call xAI Grok API."""
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        resp = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=max_tokens
        )
        return resp.choices[0].message.content
    
    def _call_gemini(self, prompt: str, system_message: str | None, max_tokens: int) -> str:
        """Call Google Gemini API."""
        # Gemini uses 'system_instruction' in GenerativeModel init or generate_content
        # Creating a new model or updating it is one way.
        # Simple way: passing system_instruction to GenerativeModel constructor if we could, 
        # but we reuse self.client.GenerativeModel.
        # Alternatively, prepend simple system prompt to text often works well for Gemini if API doesn't support it dynamically per call easily on old SDKs.
        # Latest SDK supports system_instruction at model creation.
        
        model_kwargs = {}
        if system_message:
            model_kwargs["system_instruction"] = system_message
            
        model = self.client.GenerativeModel(self.model_name, **model_kwargs)
        
        use_web = self.provider_settings.get("web_search", {}).get("enabled", False)
        gen_cfg = {
            "max_output_tokens": max_tokens,
            "temperature": self.provider_settings.get("temperature", 0.7)
        }
        
        if use_web:
            try:
                response = model.generate_content(
                    prompt,
                    tools=["google_search"],
                    generation_config=gen_cfg,
                )
            except Exception:
                response = model.generate_content(prompt, generation_config=gen_cfg)
        else:
            response = model.generate_content(prompt, generation_config=gen_cfg)
        
        return getattr(response, "text", None) or self._gemini_text_fallback(response)

    
    @staticmethod
    def _responses_text_fallback(resp: Any) -> str:
        """Fallback to collect text from Responses API structured output."""
        try:
            if hasattr(resp, "output") and isinstance(resp.output, list):
                parts = []
                for item in resp.output:
                    if isinstance(item, dict):
                        txt = item.get("content", "")
                        parts.append(txt if isinstance(txt, str) else "")
                return "\n".join([p for p in parts if p])
        except Exception:
            pass
        return ""
    
    @staticmethod
    def _gemini_text_fallback(response: Any) -> str:
        """Fallback to collect text from Gemini responses."""
        try:
            if hasattr(response, "candidates"):
                parts = []
                for c in response.candidates:
                    if hasattr(c, "content") and hasattr(c.content, "parts"):
                        for p in c.content.parts:
                            if hasattr(p, "text"):
                                parts.append(p.text)
                return "\n".join(parts)
        except Exception:
            pass
        return ""
