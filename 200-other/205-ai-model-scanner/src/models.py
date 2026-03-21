"""Data models for AI Model Scanner."""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class AIModel:
    scan_date: str
    provider: str
    model_id: str
    model_name: str
    tier: str
    input_price: float
    output_price: float
    context_window: int | None
    has_tools: bool
    has_vision: bool
    has_reasoning: bool
    has_web_search: bool
    has_json_output: bool
    is_open_weight: bool
    is_openai_compat: bool
    source: str       # "openrouter" | "grok_search"
    is_new: bool

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Pick:
    scan_date: str
    use_case: str
    model_id: str
    model_name: str
    provider: str
    input_price: float
    output_price: float
    context_window: int | None
    why: str

    def to_dict(self) -> dict:
        return asdict(self)
