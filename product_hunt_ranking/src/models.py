from pydantic import BaseModel, HttpUrl, Field

class Product(BaseModel):
    """
    Represents a product scraped from Product Hunt.
    """
    rank: int = Field(..., ge=1, description="Weekly ranking position")
    name: str = Field(..., min_length=1, description="Name of the product")
    url: str = Field(..., description="Full URL to the product page")
    description: str = Field(default="", description="Product tagline/description")
    upvotes: int = Field(default=0, ge=0, description="Number of upvotes")
