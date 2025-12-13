import re
import logging
import time
from typing import List, Dict, Set, Optional, Tuple
from bs4 import BeautifulSoup
import datetime
import requests

logger = logging.getLogger(__name__)

from src.models import Product

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}


def fetch_product_details(product_url: str) -> Tuple[str, str]:
    """
    Fetch individual product page to extract description and website URL.
    
    Args:
        product_url: Full URL to the Product Hunt product page.
        
    Returns:
        Tuple of (website_url, description). Empty strings if not found.
    """
    website_url = ""
    description = ""
    
    try:
        response = requests.get(product_url, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to find the "Visit" or "Get it" button which links to actual product
            # Look for external links that aren't to Product Hunt
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                text = link.get_text(strip=True).lower()
                
                # Skip internal PH links
                if 'producthunt.com' in href or href.startswith('/'):
                    continue
                    
                # Look for "visit", "get it", "website" type buttons
                if any(keyword in text for keyword in ['visit', 'get', 'website', 'try', 'open']):
                    website_url = href
                    break
                    
                # Also check for button-like elements with external URLs
                if href.startswith('http') and not website_url:
                    website_url = href
            
            # Try to find description - usually in meta tags or specific elements
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                description = meta_desc.get('content', '')[:200]  # Limit length
            
            # Fallback: look for tagline/description text near the product name
            if not description:
                for tag in soup.find_all(['p', 'span', 'div']):
                    text = tag.get_text(strip=True)
                    if 20 < len(text) < 200 and not text.startswith('http'):
                        description = text
                        break
                        
    except Exception as e:
        logger.debug(f"Failed to fetch details for {product_url}: {e}")
    
    return website_url, description


def parse_products(html_content: str, limit: int = 10, week_date: Optional[str] = None, fetch_details: bool = True) -> List[Product]:
    """
    Parses HTML content to extract product details using robust link finding strategy.
    
    Args:
        html_content: Raw HTML string from the Product Hunt page.
        limit: Maximum number of products to return.
        week_date: Optional date string for this week (if not provided, uses today).
        fetch_details: If True, fetch individual product pages for descriptions/website URLs.
        
    Returns:
        List of Product objects with rank, upvotes, description, and website URL.
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
        upvotes = 0
        parent = link.find_parent()
        if parent:
            for _ in range(5):
                if parent is None:
                    break
                text = parent.get_text()
                numbers = re.findall(r'\b(\d{2,5})\b', text)
                if numbers:
                    upvotes = int(numbers[0])
                    break
                parent = parent.find_parent()
        
        # Fetch additional details from product page
        website_url = ""
        description = ""
        if fetch_details:
            logger.info(f"  Fetching details for: {title}")
            website_url, description = fetch_product_details(full_link)
            time.sleep(1)  # Rate limit between requests
        
        try:
            product = Product(
                week_date=week_date,
                rank=rank,
                name=title,
                url=full_link,
                website_url=website_url,
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
