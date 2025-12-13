import re
import logging
from typing import List, Dict, Set, Optional
from bs4 import BeautifulSoup
import datetime

logger = logging.getLogger(__name__)

from src.models import Product

def parse_products(html_content: str, limit: int = 10, week_date: Optional[str] = None) -> List[Product]:
    """
    Parses HTML content to extract product details using robust link finding strategy.
    
    Args:
        html_content: Raw HTML string from the Product Hunt page.
        limit: Maximum number of products to return.
        week_date: Optional date string for this week (if not provided, uses today).
        
    Returns:
        List of Product objects with rank and upvotes.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    products: List[Product] = []
    seen_slugs: Set[str] = set()
    
    # Use provided week_date or default to today
    if week_date is None:
        week_date = datetime.date.today().strftime("%Y-%m-%d")

    # Strategy: Robust Link Finding
    # We prioritize <a> tags that look like product links (/products/slug-name)
    product_links = soup.find_all('a', href=re.compile(r'^/products/'))
    
    rank = 0
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
        rank += 1
        
        full_link = f"https://www.producthunt.com{href}"
        
        # Try to extract upvotes - look for nearby number patterns
        # Product Hunt often has upvotes near the product link
        upvotes = 0
        parent = link.find_parent()
        if parent:
            # Look for numbers that could be upvotes (usually 3-5 digits for popular products)
            for _ in range(5):  # Walk up a few levels
                if parent is None:
                    break
                text = parent.get_text()
                # Look for standalone numbers (likely upvotes)
                numbers = re.findall(r'\b(\d{2,5})\b', text)
                if numbers:
                    # Take the first reasonable number as upvotes
                    upvotes = int(numbers[0])
                    break
                parent = parent.find_parent()
        
        try:
            product = Product(
                week_date=week_date,
                rank=rank,
                name=title,
                url=full_link,
                upvotes=upvotes
            )
            products.append(product)
        except Exception as e:
            logger.warning(f"Failed to create Product model for {title}: {e}")
        
        if len(products) >= limit:
            break
            
    logger.info(f"Parsed {len(products)} products.")
    return products
