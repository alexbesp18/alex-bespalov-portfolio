# Phase 0: Discovery Instructions for Claude Code + Chrome Extension

## Overview

This document provides step-by-step instructions for using Claude Code with the Claude Chrome Extension to inspect and document the HTML structures of the three target websites:

1. **SimplyMiles** (simplymiles.com) - Authenticated
2. **eShopping Portal** (aadvantageeshopping.com) - Public
3. **AAdvantage Hotels** (aadvantagehotels.com) - Public

---

## Prerequisites

1. **Claude Chrome Extension** installed and connected to Claude Code
2. Browser logged into **SimplyMiles** with AA credentials
3. Claude Code session active in the `aa_scraper` project

---

## Instructions for Claude Code

### Task 1: Inspect SimplyMiles (Authenticated)

**User Action Required:** Navigate to https://www.simplymiles.com and log in with your AA credentials.

**Claude Code via Chrome Extension:**

1. Once logged in and on the offers page, inspect the page structure:
   ```
   GOAL: Document the HTML structure of offer cards
   
   FIND:
   - Container element holding all offers (class/id)
   - Individual offer card element (class/id)
   - Merchant name element within card
   - Offer details element (miles amount, LP amount)
   - Minimum spend element (if present)
   - Expiration date element
   - "Expiring Soon" badge element
   ```

2. Extract sample HTML for different offer types:
   - Flat bonus offer (e.g., "135 miles + 135 LP on purchase of $5 or more")
   - Per-dollar offer (e.g., "4 miles + 4 LP per $1 spent")
   
3. Check the Network tab for API calls:
   - Look for XHR/Fetch requests when page loads
   - Document any JSON endpoints that return offer data
   - Note authentication headers required

4. Document pagination/scrolling behavior:
   - Is it infinite scroll?
   - Pagination buttons?
   - "Load more" button?

**Output Format:**
```yaml
simplymiles:
  offer_container: ".offer-grid"  # or whatever the actual selector is
  offer_card: ".offer-card"
  merchant_name: ".merchant-name"
  offer_text: ".offer-details"
  miles_amount: ".miles-value"
  min_spend: ".min-purchase"
  expiration: ".expiry-date"
  expiring_badge: ".expiring-soon"
  pagination_type: "infinite_scroll"  # or "pagination" or "load_more"
  api_endpoint: "/api/offers"  # if discovered
  sample_html: |
    <div class="offer-card">
      <!-- paste actual HTML here -->
    </div>
```

---

### Task 2: Inspect eShopping Portal (Public)

**User Action Required:** Navigate to https://www.aadvantageeshopping.com/b____.htm (all stores page)

**Claude Code via Chrome Extension:**

1. Inspect the merchant/store listing:
   ```
   GOAL: Document the HTML structure of merchant cards
   
   FIND:
   - Container element for merchant grid/list
   - Individual merchant card element
   - Merchant name element
   - Miles per dollar rate element
   - Bonus/elevated rate indicator
   - Category element
   - Shop link/button
   ```

2. **PRIORITY:** Check Network tab for API:
   - Many shopping portals have JSON APIs
   - Look for requests to `/api/`, `/data/`, or `*.json` endpoints
   - Document the response structure

3. Check for bonus/elevated rates:
   - How are they visually indicated?
   - Different CSS class? Badge? Color?

**Output Format:**
```yaml
portal:
  use_api: true  # or false
  api_endpoint: "/api/stores"
  api_response_sample: |
    {"stores": [{"name": "...", "rate": 5, "bonus": true}]}
  
  # If HTML scraping needed:
  merchant_container: ".stores-grid"
  merchant_card: ".store-card"
  merchant_name: ".store-name"
  miles_rate: ".miles-rate"
  bonus_indicator: ".bonus-badge"
  category: ".category-tag"
  shop_link: "a.shop-button"
```

---

### Task 3: Inspect AAdvantage Hotels (Public)

**User Action Required:** Navigate to https://www.aadvantagehotels.com and search for "Austin, TX" with dates 2 weeks from now.

**Claude Code via Chrome Extension:**

1. Before searching, open Network tab to capture API calls

2. Perform a search and inspect:
   ```
   GOAL: Document the search API and result structure
   
   FIND:
   - Search API endpoint (what URL is called?)
   - Request parameters (city, dates, rooms, etc.)
   - Response format (JSON?)
   - Hotel result card structure
   ```

3. For each hotel result, identify:
   - Hotel name element
   - Nightly rate element
   - Miles earned element (base + bonus)
   - Total miles element
   - Booking link

**Output Format:**
```yaml
hotels:
  search_api: "https://www.aadvantagehotels.com/api/search"
  request_params:
    destination: "Austin, TX"
    checkin: "2025-01-10"
    checkout: "2025-01-12"
    rooms: 1
    adults: 2
  response_sample: |
    {"hotels": [{"name": "...", "rate": 150, "miles": 5000}]}
  
  # If HTML scraping needed:
  hotel_card: ".hotel-result"
  hotel_name: ".hotel-name"
  nightly_rate: ".price"
  miles_earned: ".miles-value"
  bonus_miles: ".bonus-miles"
```

---

## After Discovery

Once you have documented all three sites, update the following files:

### 1. Update `docs/discovery_notes.md`
Fill in all the actual selectors and API endpoints discovered.

### 2. Update Scrapers

**`scrapers/simplymiles.py`:**
- Update `offer_selectors` list with actual CSS selectors
- Update `scrape_offers()` function to use correct selectors
- Update `parse_offer_text()` if offer format differs

**`scrapers/portal.py`:**
- If API found: implement `try_api_endpoint()` with actual endpoint
- If HTML: update `card_selectors` and `parse_store_card()`

**`scrapers/hotels.py`:**
- Update `search_hotels()` with actual API endpoint and params
- Update `parse_api_response()` or `parse_html_response()` as needed

---

## Verification Checklist

After updating scrapers, verify with:

```bash
# Activate environment
source venv/bin/activate

# Test SimplyMiles (requires auth setup first)
python scripts/setup_auth.py  # Login manually
python scrapers/simplymiles.py --test

# Test Portal
python scrapers/portal.py --test

# Test Hotels
python scrapers/hotels.py --test
```

Each should output sample data without errors.

---

## Troubleshooting

### SimplyMiles shows login page
- Session expired, run `setup_auth.py` again

### Selectors not finding elements
- Site may have changed, re-inspect with Chrome Extension
- Try more general selectors first, then narrow down

### API returns 403/401
- Check if authentication cookies are required
- May need to use Playwright instead of HTTP

### Rate limiting (429)
- Increase delays in scraper config
- Reduce scrape frequency

---

*Created for Claude Code + Chrome Extension workflow*

