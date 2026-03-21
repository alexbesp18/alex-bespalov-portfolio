# Chrome Extension Discovery Script

## For Claude Code to Execute via Chrome Extension

Copy these instructions to Claude Code when connected to the Chrome Extension.

---

## SITE 1: SimplyMiles

### Step 1: Navigate
```
Go to: https://www.simplymiles.com
User must be logged in with AA credentials
```

### Step 2: Inspect Page (Claude via Extension)

Execute these inspection tasks:

```javascript
// Task 1: Find the offer container
// Look for the parent element containing all offer cards
document.querySelectorAll('[class*="offer"], [class*="card"], [class*="grid"]')

// Task 2: Find individual offer cards
// Each offer should have merchant name, miles, min spend
document.querySelectorAll('[class*="offer"]').length // How many?

// Task 3: Get sample offer HTML
// Copy the outerHTML of one offer card
document.querySelector('[class*="offer"]')?.outerHTML

// Task 4: Find specific elements within an offer
const card = document.querySelector('[class*="offer"]');
if (card) {
  console.log('Merchant:', card.querySelector('h2, h3, [class*="merchant"], [class*="name"]')?.textContent);
  console.log('Miles:', card.querySelector('[class*="mile"], [class*="point"]')?.textContent);
  console.log('Expiry:', card.querySelector('[class*="expir"], [class*="date"]')?.textContent);
}
```

### Step 3: Check Network Tab

Look for:
- XHR/Fetch requests when page loads
- Any `/api/` endpoints
- JSON responses containing offer data

### Step 4: Document Findings

Output in this format:
```yaml
simplymiles_selectors:
  container: "[actual-selector]"
  offer_card: "[actual-selector]"
  merchant_name: "[actual-selector]"
  offer_text: "[actual-selector]"
  miles: "[actual-selector]"
  min_spend: "[actual-selector]"
  expiration: "[actual-selector]"
  api_endpoint: null  # or actual endpoint if found
```

---

## SITE 2: eShopping Portal

### Step 1: Navigate
```
Go to: https://www.aadvantageeshopping.com/b____.htm
(All stores page - no login required)
```

### Step 2: Inspect Page

```javascript
// Task 1: Find store/merchant cards
document.querySelectorAll('[class*="store"], [class*="merchant"], [class*="shop"]').length

// Task 2: Get sample store HTML
document.querySelector('[class*="store"]')?.outerHTML

// Task 3: Find rate display
// Look for "X mi/$" or "X miles per dollar"
const cards = document.querySelectorAll('[class*="store"], [class*="merchant"]');
cards[0]?.textContent // Check what info is visible

// Task 4: Find specific elements
const store = document.querySelector('[class*="store"]');
if (store) {
  console.log('Name:', store.querySelector('[class*="name"], h2, h3, a')?.textContent);
  console.log('Rate:', store.querySelector('[class*="rate"], [class*="mile"], [class*="earn"]')?.textContent);
}
```

### Step 3: PRIORITY - Check for API

Open Network tab, refresh page, and look for:
- Any JSON endpoints
- Requests containing "store" or "merchant"
- API responses with rate data

```javascript
// If you can access fetch history:
// Look for URLs like:
// /api/stores
// /api/merchants  
// /data/stores.json
```

### Step 4: Document Findings

```yaml
portal_selectors:
  has_api: true/false
  api_endpoint: "[endpoint if found]"
  api_sample: |
    [paste sample JSON response]
  container: "[actual-selector]"
  store_card: "[actual-selector]"
  store_name: "[actual-selector]"
  miles_rate: "[actual-selector]"
  bonus_indicator: "[actual-selector]"
```

---

## SITE 3: AAdvantage Hotels

### Step 1: Navigate & Search
```
Go to: https://www.aadvantagehotels.com
Search for: Austin, TX
Dates: 2 weeks from today, 2 nights
```

### Step 2: BEFORE Searching - Open Network Tab

This is critical to capture the search API call.

### Step 3: Perform Search & Capture API

Look in Network tab for:
- POST or GET request when search is submitted
- Request URL and parameters
- Response format (JSON)

```javascript
// Example of what to look for:
// Request URL: https://www.aadvantagehotels.com/api/hotels/search
// Request body: {destination: "Austin, TX", checkin: "...", checkout: "..."}
// Response: {hotels: [{name: "...", rate: 150, miles: 5000}, ...]}
```

### Step 4: Inspect Hotel Results

```javascript
// Find hotel result cards
document.querySelectorAll('[class*="hotel"], [class*="property"], [class*="result"]').length

// Get sample HTML
document.querySelector('[class*="hotel"]')?.outerHTML

// Find specific data
const hotel = document.querySelector('[class*="hotel"]');
if (hotel) {
  console.log('Name:', hotel.querySelector('[class*="name"], h2, h3')?.textContent);
  console.log('Rate:', hotel.querySelector('[class*="price"], [class*="rate"]')?.textContent);
  console.log('Miles:', hotel.querySelector('[class*="mile"], [class*="point"]')?.textContent);
}
```

### Step 5: Document Findings

```yaml
hotels_api:
  search_endpoint: "[actual URL]"
  method: "POST"  # or GET
  request_format: |
    {
      "destination": "Austin, TX",
      "checkin": "2025-01-15",
      "checkout": "2025-01-17",
      "rooms": 1
    }
  response_sample: |
    [paste sample response]
  
  # If HTML scraping needed:
  hotel_card: "[actual-selector]"
  hotel_name: "[actual-selector]"
  price: "[actual-selector]"
  miles: "[actual-selector]"
```

---

## After All 3 Sites Inspected

### Update Scraper Files

Use the documented selectors to update:

1. **`scrapers/simplymiles.py`** line ~180
2. **`scrapers/portal.py`** line ~130
3. **`scrapers/hotels.py`** line ~90

### Test Each Scraper

```bash
source venv/bin/activate
python scrapers/simplymiles.py --test
python scrapers/portal.py --test
python scrapers/hotels.py --test
```

### Commit the Updates

```bash
git add scrapers/ docs/discovery_notes.md
git commit -m "Update selectors from discovery phase"
```

---

## Quick Reference: Common Selectors to Try

```javascript
// Offer/Card containers
'[class*="card"]'
'[class*="offer"]'
'[class*="item"]'
'[class*="tile"]'
'[class*="result"]'

// Names/Titles
'h2', 'h3', 'h4'
'[class*="name"]'
'[class*="title"]'
'[class*="merchant"]'
'[class*="store"]'
'[class*="hotel"]'

// Rates/Miles
'[class*="rate"]'
'[class*="mile"]'
'[class*="point"]'
'[class*="earn"]'
'[class*="bonus"]'

// Prices
'[class*="price"]'
'[class*="cost"]'
'[class*="rate"]'
'[data-price]'

// Expiration
'[class*="expir"]'
'[class*="date"]'
'[class*="valid"]'
```

---

*Use this script with Claude Code + Chrome Extension to complete Phase 0*

