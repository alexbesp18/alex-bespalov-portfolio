from pydantic import BaseModel, HttpUrl, Field

class Product(BaseModel):
    """
    Represents a product scraped from Product Hunt.
    """
    name: str = Field(..., min_length=1, description="Name of the product")
    url: str = Field(..., description="Full URL to the product page")
    description: str = Field(default="N/A", description="Short description of the product")
