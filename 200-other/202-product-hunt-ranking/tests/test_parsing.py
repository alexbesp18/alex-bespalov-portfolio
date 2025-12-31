from src.utils.parsing import Product, parse_products

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


def test_malformed_url_handled():
    """Test that malformed URLs don't crash the scraper."""
    # Empty slug after /products/ - regex matches but URL is technically valid
    html = """<html><a href="/products/">Empty Slug</a></html>"""
    products = parse_products(html)
    # Should still parse since "Empty Slug" is a valid title (len > 2)
    # and the URL format is valid (just has trailing slash)
    assert len(products) == 1
    assert products[0].name == "Empty Slug"
    assert products[0].url == "https://www.producthunt.com/products/"


def test_duplicate_products_filtered():
    """Test that duplicate product links are filtered out."""
    html = """
    <html>
    <body>
        <a href="/products/same-product">Same Product</a>
        <a href="/products/same-product">Same Product Again</a>
        <a href="/products/different">Different Product</a>
    </body>
    </html>
    """
    products = parse_products(html)
    assert len(products) == 2
    assert products[0].name == "Same Product"
    assert products[1].name == "Different Product"
