import logging
import re
from typing import List, Set

from bs4 import BeautifulSoup

from src.models import Product

logger = logging.getLogger(__name__)

def parse_products(html_content: str, limit: int = 10) -> List[Product]:
    """
    Parses HTML content to extract product details.
    
    Based on Product Hunt's HTML structure:
    - Product links are <a href="/products/slug-name">
    - Description is text near the product link in the same parent container
    - Upvotes are in a <button> containing a <p> with the number
    
    Args:
        html_content: Raw HTML string from the Product Hunt page.
        limit: Maximum number of products to return.
        
    Returns:
        List of Product objects.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    products: List[Product] = []
    seen_slugs: Set[str] = set()

    # Find all product links
    product_links = soup.find_all('a', href=re.compile(r'^/products/'))
    
    rank = 0
    for link in product_links:
        href = link.get('href')
        title = link.get_text(strip=True)
        
        # Validation
        if not title or len(title) < 2:
            continue
        
        # Skip potential false positives
        if title.lower() in ['comment', 'review', 'link', 'comments', 'reviews']:
            continue

        if href in seen_slugs:
            continue
            
        seen_slugs.add(href)
        rank += 1
        
        full_link = f"https://www.producthunt.com{href}"
        
        # Extract description: Look for text in parent/sibling elements
        description = ""
        parent = link.find_parent()
        if parent:
            # Get parent's parent to find sibling divs with description text
            grandparent = parent.find_parent()
            if grandparent:
                # Description is usually text that's not the title and not too short
                for text in grandparent.stripped_strings:
                    if text != title and len(text) > 10 and len(text) < 200:
                        # Skip things that look like categories
                        if '·' not in text and not text.startswith('http'):
                            description = text
                            break
        
        # Extract upvotes: Look for button with p containing a number
        # Upvotes are the LARGER number (comments are smaller)
        upvotes = 0
        all_numbers = []
        # Walk up to find the product card container (usually 5-10 levels up)
        card_container = link
        for _ in range(10):
            card_container = card_container.find_parent()
            if card_container is None:
                break
            # Look for button elements with vote counts
            buttons = card_container.find_all('button')
            for btn in buttons:
                # Find p tags inside button that contain just a number
                p_tags = btn.find_all('p')
                for p in p_tags:
                    text = p.get_text(strip=True)
                    if text.isdigit() and int(text) > 0:
                        all_numbers.append(int(text))
            if len(all_numbers) >= 2:  # Found both comments and upvotes
                break
        
        # Upvotes are always the larger number
        if all_numbers:
            upvotes = max(all_numbers)
        
        try:
            product = Product(
                rank=rank,
                name=title,
                url=full_link,
                description=description,
                upvotes=upvotes
            )
            products.append(product)
        except Exception as e:
            logger.warning(f"Failed to create Product model for {title}: {e}")
        
        if len(products) >= limit:
            break
            
    logger.info(f"Parsed {len(products)} products.")
    return products
