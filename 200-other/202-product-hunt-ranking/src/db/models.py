"""Pydantic models for database records."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class PHProduct(BaseModel):
    """Raw scraped product data (matches existing Product model)."""

    week_date: date
    week_number: int
    year: int
    rank: int
    name: str
    description: str = ""
    upvotes: int = 0
    url: str


class GrokEnrichment(BaseModel):
    """Grok-generated enrichment fields."""

    category: str | None = None
    subcategory: str | None = None
    target_audience: str | None = None
    tech_stack: list[str] | None = None
    maker_info: dict[str, Any] | None = None
    pricing_model: str | None = None
    innovation_score: float | None = Field(default=None, ge=0, le=10)
    market_fit_score: float | None = Field(default=None, ge=0, le=10)


class EnrichedProduct(PHProduct):
    """Product with Grok enrichment."""

    category: str | None = None
    subcategory: str | None = None
    target_audience: str | None = None
    tech_stack: list[str] | None = None
    maker_info: dict[str, Any] | None = None
    pricing_model: str | None = None
    innovation_score: float | None = None
    market_fit_score: float | None = None
    scraped_at: datetime | None = None
    analyzed_at: datetime | None = None

    def to_db_dict(self) -> dict[str, Any]:
        """Convert to dictionary for Supabase upsert."""
        data = {
            "week_date": self.week_date.isoformat(),
            "week_number": self.week_number,
            "year": self.year,
            "rank": self.rank,
            "name": self.name,
            "description": self.description,
            "upvotes": self.upvotes,
            "url": self.url,
        }
        # Only include enriched fields if they have values
        if self.category:
            data["category"] = self.category
        if self.subcategory:
            data["subcategory"] = self.subcategory
        if self.target_audience:
            data["target_audience"] = self.target_audience
        if self.tech_stack:
            data["tech_stack"] = self.tech_stack
        if self.maker_info:
            data["maker_info"] = self.maker_info
        if self.pricing_model:
            data["pricing_model"] = self.pricing_model
        if self.innovation_score is not None:
            data["innovation_score"] = self.innovation_score
        if self.market_fit_score is not None:
            data["market_fit_score"] = self.market_fit_score
        if self.analyzed_at:
            data["analyzed_at"] = self.analyzed_at.isoformat()
        return data


class PHWeeklyInsights(BaseModel):
    """Weekly AI-generated insights."""

    week_date: date
    year: int
    week_number: int
    top_trends: list[str] = Field(default_factory=list)
    notable_launches: str = ""
    category_breakdown: dict[str, int] = Field(default_factory=dict)
    avg_upvotes: float = 0.0
    sentiment: str = "Neutral"
    full_analysis: str = ""

    def to_db_dict(self) -> dict[str, Any]:
        """Convert to dictionary for Supabase upsert."""
        return {
            "week_date": self.week_date.isoformat(),
            "year": self.year,
            "week_number": self.week_number,
            "top_trends": self.top_trends,
            "notable_launches": self.notable_launches,
            "category_breakdown": self.category_breakdown,
            "avg_upvotes": self.avg_upvotes,
            "sentiment": self.sentiment,
            "full_analysis": self.full_analysis,
        }
