import pytest
from src.utils.parsing import parse_products, Product

HTML_SAMPLE = """
<html>
<body>
    <div>
        <a href="/products/awesome-tool">Awesome Tool</a>
        <a href="/products/another-tool">Another Tool</a>
        <a href="/products/bad-link">Link</a> <!-- Should be ignored -->
        <a href="/about">About</a> <!-- Should be ignored -->
    </div>
</body>
</html>
"""

def test_parse_valid_products():
    """Test parsing logic extracts products correctly as Product models."""
    products = parse_products(HTML_SAMPLE)
    
    assert len(products) == 2
    assert isinstance(products[0], Product)
    assert products[0].rank == 1
    assert products[0].name == "Awesome Tool"
    # Pydantic HttpUrl might need string conversion depending on version, 
    # but here we defined it as str in the simplified model or HttpUrl
    assert str(products[0].url) == "https://www.producthunt.com/products/awesome-tool"
    assert products[1].rank == 2
    assert products[1].name == "Another Tool"

def test_parse_limit():
    """Test that the limit parameter is respected."""
    products = parse_products(HTML_SAMPLE, limit=1)
    assert len(products) == 1
    assert products[0].name == "Awesome Tool"

def test_parse_empty():
    """Test parsing empty or irrelevant HTML."""
    assert parse_products("") == []
    assert parse_products("<html></html>") == []

def test_malformed_url_handled(caplog):
    """Test that malformed URLs don't crash the scraper."""
    # Simulating a case where href might be missing or invalid if we had strict validation
    # For now, our regex filters most bad things, but let's ensure resilience
    html = """<html><a href="/products/">Empty Slug</a></html>"""
    products = parse_products(html)
    # The regex requires characters after /products/, so this might be skipped by logic
    # or empty slug if accepted by regex.
    # Our regex is r'^/products/', so it matches.
    # Logic checks len(title) < 2
    pass
