import re
import logging
from typing import List, Dict, Set, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

from src.models import Product

def parse_products(html_content: str, limit: int = 10) -> List[Product]:
    """
    Parses HTML content to extract product details using robust link finding strategy.
    
    Args:
        html_content: Raw HTML string from the Product Hunt page.
        limit: Maximum number of products to return.
        
    Returns:
        List of Product objects.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    products: List[Product] = []
    seen_slugs: Set[str] = set()

    # Strategy: Robust Link Finding
    # We prioritize <a> tags that look like product links (/products/slug-name)
    product_links = soup.find_all('a', href=re.compile(r'^/products/'))
    
    for link in product_links:
        href = link.get('href')
        title = link.get_text(strip=True)
        
        # Validation
        if not title or len(title) < 2:
            continue
        
        # Skip potential false positives
        if title.lower() in ['comment', 'review', 'link']:
            continue

        if href in seen_slugs:
            continue
            
        seen_slugs.add(href)
        
        full_link = f"https://www.producthunt.com{href}"
        
        # Description Extraction Placeholder
        description = "N/A"
        
        try:
            product = Product(
                name=title,
                url=full_link,
                description=description
            )
            products.append(product)
        except Exception as e:
            logger.warning(f"Failed to create Product model for {title}: {e}")
        
        if len(products) >= limit:
            break
            
    logger.info(f"Parsed {len(products)} products.")
    return products
