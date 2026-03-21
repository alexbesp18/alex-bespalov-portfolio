"""Centralized configuration for AI Model Scanner."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ── Environment Variables ────────────────────────────────────────

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
XAI_API_KEY = os.environ.get("XAI_API_KEY", "")

# ── Constants ────────────────────────────────────────────────────

SCHEMA = "ai_scanner"

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/models"

XAI_RESPONSES_URL = "https://api.x.ai/v1/responses"
XAI_MODEL = "grok-4-1-fast"

RETENTION_DAYS = 90

# ── Paths ────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# ── Tier Overrides ───────────────────────────────────────────────
# ~30 important models with manually verified tiers.
# Key = model_id as it appears AFTER the provider prefix in OpenRouter
# (e.g., "gpt-4o" not "openai/gpt-4o").

TIER_OVERRIDES: dict[str, str] = {
    # OpenAI
    "gpt-4.1": "flagship",
    "gpt-4.1-mini": "fast",
    "gpt-4.1-nano": "fast",
    "gpt-4o": "flagship",
    "gpt-4o-mini": "fast",
    "o3": "deep",
    "o3-pro": "deep",
    "o3-mini": "fast",
    "o4-mini": "fast",
    "gpt-4.5-preview": "deep",
    # Anthropic
    "claude-opus-4-6": "deep",
    "claude-sonnet-4-6": "flagship",
    "claude-haiku-4-5-20251001": "fast",
    "claude-3.5-sonnet": "flagship",
    "claude-3.5-haiku": "fast",
    # Google
    "gemini-2.5-pro": "deep",
    "gemini-2.5-flash": "fast",
    "gemini-2.0-flash": "fast",
    "gemini-2.0-flash-lite": "fast",
    # xAI
    "grok-4": "flagship",
    "grok-4-1-fast": "fast",
    "grok-3": "flagship",
    "grok-3-fast": "fast",
    "grok-3-mini": "fast",
    # DeepSeek
    "deepseek-r1": "deep",
    "deepseek-chat": "flagship",
    "deepseek-reasoner": "deep",
    # Perplexity
    "sonar-deep-research": "deep",
    "sonar-pro": "flagship",
    "sonar": "fast",
    # Meta
    "llama-4-maverick": "flagship",
    "llama-4-scout": "fast",
    # Mistral
    "mistral-large": "flagship",
    "mistral-small": "fast",
    "codestral": "flagship",
    # Qwen
    "qwen-2.5-72b-instruct": "flagship",
    "qwen-2.5-coder-32b-instruct": "flagship",
    "qwq-32b": "deep",
}

# ── Open-Weight Providers ────────────────────────────────────────
# Provider prefixes from OpenRouter IDs for known open-weight model families.

OPEN_WEIGHT_PROVIDERS: set[str] = {
    "meta-llama",
    "deepseek",
    "mistralai",
    "qwen",
    "microsoft",
    "nvidia",
    "01-ai",
    "tiiuae",
    "cohere",
    "databricks",
    "upstage",
    "google",  # gemma models
    "allenai",
    "mosaicml",
}

# ── Grok Search Prompt ───────────────────────────────────────────

GROK_PROMPT = """Search the web for AI model API releases and pricing changes from the LAST 7 DAYS ONLY.

Check these providers: OpenAI, Anthropic, Google Gemini, xAI Grok, DeepSeek, Mistral, Perplexity, Moonshot Kimi, Alibaba Qwen.

For each NEW model or PRICE CHANGE you find, return this JSON. If nothing changed, return {"updates": []}.

{
  "updates": [
    {
      "provider": "openai",
      "model_id": "gpt-5.4",
      "model_name": "GPT-5.4",
      "event": "new_release",
      "input_price_per_1m": 2.50,
      "output_price_per_1m": 15.00,
      "context_window": 1050000,
      "has_tools": true,
      "has_vision": true,
      "has_reasoning": true,
      "has_web_search": true,
      "has_json_output": true,
      "release_date": "2026-03-05",
      "source_url": "https://example.com/blog/model-release"
    }
  ]
}

RULES:
- ONLY include events from the last 7 days. Skip older models.
- Prices must be in USD per 1 MILLION tokens.
- "has_web_search" means API-level tool, not chatbot product feature.
- If you find conflicting prices, note both in a "notes" field.
- Return ONLY valid JSON. No markdown, no explanation."""
