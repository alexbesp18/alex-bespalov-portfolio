"""Tier assignment logic for AI models."""

from __future__ import annotations

import re

from src.config import TIER_OVERRIDES


def assign_tier(model_id: str, provider: str, input_price: float | None, has_reasoning: bool) -> str:
    """Assign a tier (fast/flagship/deep) to a model.

    Priority:
    1. Exact match in TIER_OVERRIDES
    2. Word-boundary keyword heuristic
    3. Price-based fallback
    """
    # 1. Check overrides (exact model_id match)
    if model_id in TIER_OVERRIDES:
        return TIER_OVERRIDES[model_id]

    # 2. Word-boundary keyword heuristic (split on -, _, ., /)
    words = set(re.split(r'[-_./]', model_id.lower()))

    fast_keywords = {"mini", "nano", "flash", "lite", "small", "haiku", "instant", "turbo"}
    deep_keywords = {"heavy", "deep", "opus", "ultra"}

    if words & fast_keywords:
        return "fast"
    if words & deep_keywords:
        return "deep"

    # 3. Price + reasoning heuristic
    if input_price is None:
        return "flagship"

    if has_reasoning and input_price > 5.0:
        return "deep"

    if input_price < 0.5:
        return "fast"

    if input_price > 15.0:
        return "deep"

    return "flagship"
