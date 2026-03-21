"""Fetch and parse all models from OpenRouter API."""

from __future__ import annotations

import httpx

from src.config import OPENROUTER_API_URL, OPEN_WEIGHT_PROVIDERS
from src.models import AIModel
from src.tiers import assign_tier


# Providers known to have web search at the API level
_SEARCH_PROVIDERS = {"perplexity"}


async def fetch_all_models(scan_date: str) -> list[AIModel]:
    """Fetch all models from OpenRouter. Free, no API key needed."""
    transport = httpx.AsyncHTTPTransport(retries=3)
    async with httpx.AsyncClient(timeout=30, transport=transport) as client:
        resp = await client.get(OPENROUTER_API_URL)
        resp.raise_for_status()
        data = resp.json()

    models: list[AIModel] = []
    for m in data.get("data", []):
        try:
            model = _parse_model(m, scan_date)
            if model is not None:
                models.append(model)
        except Exception as e:
            print(f"  [warn] Skipping malformed model {m.get('id', '?')}: {e}")

    return models


def _parse_model(m: dict, scan_date: str) -> AIModel | None:
    """Parse a single OpenRouter model entry into an AIModel."""
    or_id = m.get("id", "")
    if not or_id or "/" not in or_id:
        return None

    pricing = m.get("pricing", {}) or {}
    prompt_price = pricing.get("prompt", "0")
    completion_price = pricing.get("completion", "0")

    # Convert per-token to per-1M tokens
    input_price = float(prompt_price) * 1_000_000
    output_price = float(completion_price) * 1_000_000

    # Skip invalid prices (OpenRouter returns -1.0 for routing models like auto/bodybuilder)
    if input_price < 0 or output_price < 0:
        return None

    # Skip free/community models (noise)
    if input_price == 0 and output_price == 0 and "free" in or_id.lower():
        return None

    provider = or_id.split("/")[0]
    model_id = or_id.split("/", 1)[1]

    supported = m.get("supported_parameters", []) or []
    architecture = m.get("architecture", {}) or {}
    input_modalities = architecture.get("input_modalities", []) or []

    has_tools = "tools" in supported
    has_vision = "image" in input_modalities
    has_reasoning = "reasoning" in supported
    has_web_search = "web_search_options" in supported or provider in _SEARCH_PROVIDERS
    has_json_output = "response_format" in supported or "structured_outputs" in supported
    is_open_weight = provider in OPEN_WEIGHT_PROVIDERS

    context_window = m.get("context_length")
    if context_window is not None:
        context_window = int(context_window)

    tier = assign_tier(model_id, provider, input_price, has_reasoning)

    return AIModel(
        scan_date=scan_date,
        provider=provider,
        model_id=model_id,
        model_name=m.get("name", or_id),
        tier=tier,
        input_price=round(input_price, 4),
        output_price=round(output_price, 4),
        context_window=context_window,
        has_tools=has_tools,
        has_vision=has_vision,
        has_reasoning=has_reasoning,
        has_web_search=has_web_search,
        has_json_output=has_json_output,
        is_open_weight=is_open_weight,
        is_openai_compat=True,
        source="openrouter",
        is_new=False,
    )
