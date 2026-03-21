"""Compute 20 recommendation picks from model data."""

from __future__ import annotations

import math

from src.models import AIModel, Pick


# Tier rank: lower = better quality
_TIER_RANK = {"deep": 1, "flagship": 2, "fast": 3}


def _blended_price(m: AIModel) -> float:
    return (m.input_price or 0) + (m.output_price or 0)


def _tier_rank(m: AIModel) -> int:
    return _TIER_RANK.get(m.tier, 3)


def _value_score(m: AIModel) -> float:
    """Higher = better value. Exponential tier weights with root-scaled price."""
    tier_weight = {1: 10.0, 2: 4.0, 3: 1.0}.get(_tier_rank(m), 1.0)
    price = _blended_price(m) + 0.01
    return tier_weight / (price ** 0.3 + 0.1)


# ── Sort Keys ────────────────────────────────────────────────────

def _sort_price_asc(m: AIModel) -> tuple:
    return (_blended_price(m),)


def _sort_tier_then_price(m: AIModel) -> tuple:
    return (_tier_rank(m), _blended_price(m))


def _sort_value_score(m: AIModel) -> tuple:
    return (-_value_score(m),)


_SORT_FUNCS = {
    "price_asc": _sort_price_asc,
    "tier_desc": _sort_tier_then_price,
    "tier_then_price": _sort_tier_then_price,
    "value_score": _sort_value_score,
}


# ── Use Cases ────────────────────────────────────────────────────

USE_CASES: dict[str, dict] = {
    "absolute_cheapest": {
        "filters": {},
        "sort": "price_asc",
        "why": "Lowest blended price across all models",
    },
    "cheapest_flagship": {
        "filters": {"tier": "flagship"},
        "sort": "price_asc",
        "why": "Cheapest flagship-tier model",
    },
    "cheapest_with_tools": {
        "filters": {"has_tools": True},
        "sort": "price_asc",
        "why": "Cheapest model with tool/function calling",
    },
    "cheapest_with_search": {
        "filters": {"has_web_search": True},
        "sort": "price_asc",
        "why": "Cheapest model with API-level web search",
    },
    "cheapest_with_vision": {
        "filters": {"has_vision": True},
        "sort": "price_asc",
        "why": "Cheapest model with image input support",
    },
    "cheapest_with_reasoning": {
        "filters": {"has_reasoning": True},
        "sort": "price_asc",
        "why": "Cheapest model with extended reasoning",
    },
    "cheapest_100k_ctx": {
        "filters": {"min_context": 100_000},
        "sort": "price_asc",
        "why": "Cheapest model with 100K+ context window",
    },
    "cheapest_500k_ctx": {
        "filters": {"min_context": 500_000},
        "sort": "price_asc",
        "why": "Cheapest model with 500K+ context window",
    },
    "cheapest_1m_ctx": {
        "filters": {"min_context": 1_000_000},
        "sort": "price_asc",
        "why": "Cheapest model with 1M+ context window",
    },
    "best_under_1_dollar": {
        "filters": {"max_input": 1.0},
        "sort": "tier_desc",
        "why": "Best quality tier under $1/M input",
    },
    "best_under_3_dollars": {
        "filters": {"max_input": 3.0},
        "sort": "tier_desc",
        "why": "Best quality tier under $3/M input",
    },
    "best_deep_thinker": {
        "filters": {"tier": "deep"},
        "sort": "tier_then_price",
        "why": "Best deep-reasoning model by quality then price",
    },
    "best_open_weight": {
        "filters": {"is_open_weight": True},
        "sort": "tier_desc",
        "why": "Best quality open-weight model",
    },
    "cheapest_tools_search": {
        "filters": {"has_tools": True, "has_web_search": True},
        "sort": "price_asc",
        "why": "Cheapest model with both tools and web search",
    },
    "cheapest_tools_reason": {
        "filters": {"has_tools": True, "has_reasoning": True},
        "sort": "price_asc",
        "why": "Cheapest model with both tools and reasoning",
    },
    "best_for_agents": {
        "filters": {"has_tools": True, "has_reasoning": True},
        "sort": "tier_then_price",
        "why": "Best for agentic workflows (tools + reasoning, quality first)",
    },
    "best_for_research": {
        "filters": {"has_web_search": True, "has_reasoning": True},
        "sort": "tier_then_price",
        "why": "Best for research (search + reasoning, quality first)",
    },
    "best_for_classification": {
        "filters": {"has_json_output": True},
        "sort": "price_asc",
        "why": "Cheapest model with structured JSON output",
    },
    "best_for_long_docs": {
        "filters": {"min_context": 200_000},
        "sort": "tier_then_price",
        "why": "Best for long documents (200K+ context, quality first)",
    },
    "best_value": {
        "filters": {},
        "sort": "value_score",
        "why": "Best quality-to-price ratio across all models",
    },
}


def compute_picks(scan_date: str, all_models: list[AIModel]) -> list[Pick]:
    """Compute 20 recommendation picks from model data in-memory."""
    # Only consider models with a real price
    priced = [m for m in all_models if (m.input_price or 0) > 0]

    picks: list[Pick] = []

    for use_case, config in USE_CASES.items():
        filtered = _apply_filters(priced, config["filters"])
        if not filtered:
            continue

        sort_fn = _SORT_FUNCS[config["sort"]]
        filtered.sort(key=sort_fn)
        winner = filtered[0]

        picks.append(Pick(
            scan_date=scan_date,
            use_case=use_case,
            model_id=winner.model_id,
            model_name=winner.model_name,
            provider=winner.provider,
            input_price=winner.input_price,
            output_price=winner.output_price,
            context_window=winner.context_window,
            why=config["why"],
        ))

    return picks


def _apply_filters(models: list[AIModel], filters: dict) -> list[AIModel]:
    """Apply filter criteria to model list."""
    result = list(models)

    for key, value in filters.items():
        if key == "tier":
            result = [m for m in result if m.tier == value]
        elif key == "has_tools":
            result = [m for m in result if m.has_tools]
        elif key == "has_web_search":
            result = [m for m in result if m.has_web_search]
        elif key == "has_vision":
            result = [m for m in result if m.has_vision]
        elif key == "has_reasoning":
            result = [m for m in result if m.has_reasoning]
        elif key == "has_json_output":
            result = [m for m in result if m.has_json_output]
        elif key == "is_open_weight":
            result = [m for m in result if m.is_open_weight]
        elif key == "min_context":
            result = [m for m in result if (m.context_window or 0) >= value]
        elif key == "max_input":
            result = [m for m in result if (m.input_price or 0) <= value]

    return result
