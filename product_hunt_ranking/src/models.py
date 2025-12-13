from pydantic import BaseModel, HttpUrl, Field
from typing import Optional

class Product(BaseModel):
    """
    Represents a product scraped from Product Hunt.
    """
    week_date: str = Field(..., description="Date of the week (Monday) for this ranking")
    rank: int = Field(..., ge=1, description="Weekly ranking position")
    name: str = Field(..., min_length=1, description="Name of the product")
    url: str = Field(..., description="Full URL to the product page")
    upvotes: int = Field(default=0, ge=0, description="Number of upvotes")
