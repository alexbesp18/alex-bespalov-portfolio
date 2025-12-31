"""Pydantic models for database records."""

from datetime import date, datetime
from typing import List, Optional, Dict, Any
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
    category: Optional[str] = None
    subcategory: Optional[str] = None
    target_audience: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    maker_info: Optional[Dict[str, Any]] = None
    pricing_model: Optional[str] = None
    innovation_score: Optional[float] = Field(default=None, ge=0, le=10)
    market_fit_score: Optional[float] = Field(default=None, ge=0, le=10)


class EnrichedProduct(PHProduct):
    """Product with Grok enrichment."""
    category: Optional[str] = None
    subcategory: Optional[str] = None
    target_audience: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    maker_info: Optional[Dict[str, Any]] = None
    pricing_model: Optional[str] = None
    innovation_score: Optional[float] = None
    market_fit_score: Optional[float] = None
    scraped_at: Optional[datetime] = None
    analyzed_at: Optional[datetime] = None

    def to_db_dict(self) -> Dict[str, Any]:
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
    top_trends: List[str] = Field(default_factory=list)
    notable_launches: str = ""
    category_breakdown: Dict[str, int] = Field(default_factory=dict)
    avg_upvotes: float = 0.0
    sentiment: str = "Neutral"
    full_analysis: str = ""

    def to_db_dict(self) -> Dict[str, Any]:
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
