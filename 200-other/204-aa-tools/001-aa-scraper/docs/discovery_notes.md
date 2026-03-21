# Discovery Notes - AA Points Monitor

## Instructions

Before implementing scrapers, manually inspect each website to understand their structure.
Fill in the sections below with your findings.

---

## 1. SimplyMiles (simplymiles.com)

### Login Flow
- [x] Visited site and logged in with AA credentials
- Login URL: `https://www.simplymiles.com/sso_login` (redirects to AA SSO)
- Authentication method: AA SSO (login.aa.com)
- After login redirects to: `https://www.simplymiles.com/home`

### Offer Card Structure
```html
<div class="card box-shadow h-100">
  <div class="card-img-top">
    <div class="right-buttons">
      <div class="add">+</div>
    </div>
    <div class="info-badge">Expiring soon</div>
    <div class="logo-container">
      <img class="logo-img" src="...">
    </div>
  </div>
  <div class="card-body text-center">
    <p class="card-title font-fmd txt-grey pt-4">Kindle and Kindle Unlimited</p>
    <p class="font-bold pt-3">135 miles + 135 Loyalty Points on a purchase of $5 or more</p>
  </div>
  <div class="card-footer pt-0 pt-md-2">
    <div class="button-container mb-3">
      <a class="btn btn-light-blue py-3 px-5">Activate offer</a>
    </div>
    <p class="text-center txt-grey font-fsm mb-3">Expires 12/31/2025</p>
    <a class="link txt-light-blue">Details</a>
  </div>
</div>
```

### Key CSS Selectors
```
Offer container: .offers-container .inner-container
Offer rows: .offers-container .inner-container .row
Card columns: [class*="col"]
Card: .card
Merchant name: .card-title
Offer text: .card-body .font-bold
Miles/LP amount: (parsed from offer text)
Minimum spend: (parsed from offer text - "purchase of $X or more")
Expiration date: .card-footer p.txt-grey (format: "Expires MM/DD/YYYY")
"Expiring Soon" badge: .info-badge (text: "Expiring soon")
Activate button: .btn-light-blue
Details link: .link.txt-light-blue
```

### Offer Text Patterns
Two formats observed:
1. Flat bonus: `{miles} miles + {lp} Loyalty Points on a purchase of ${min_spend} or more`
   - Example: "135 miles + 135 Loyalty Points on a purchase of $5 or more"
2. Per-dollar: `{miles} miles + {lp} Loyalty Points per $1 spent on any purchase`
   - Example: "4 miles + 4 Loyalty Points per $1 spent on any purchase"

### Pagination / Loading
- [ ] Infinite scroll
- [x] Numbered pagination
- [ ] "Load more" button
- Total offers visible: 142 (across 8 pages, ~18-20 per page)

**Pagination Selectors:**
```
Container: .pagination
Page item: .page-item
Page link: .page-link
Active page: .page-item.active
Next/Prev: Arrow buttons at ends
```

### API Calls (Network Tab)
```
Endpoint: POST https://www.simplymiles.com/get-activated-offers
Method: POST
Purpose: Returns user's activated offers (not the full offer list)
Note: Full offers are server-rendered HTML, no JSON API for offer list
```

### Anti-Bot Measures Detected
- [ ] Cloudflare
- [ ] reCAPTCHA
- [ ] Rate limiting (none observed)
- [x] Akamai Bot Detection (sensor_data POST requests observed)

### API Endpoints Tested (2024-12-28)
```
FOUND:
  GET /featured-landing-page-offers
  - Returns JSON array of 13 featured offers
  - No auth required
  - Contains: id, merchant_name, merchant_logo, display_order
  - NOT the full catalog (~142 offers)

  POST /get-activated-offers
  - Returns user's activated offers (requires auth)
  - Not useful for scraping all available offers

NOT FOUND (404):
  /offers, /all-offers, /get-offers, /api/offers
  /api/v1/offers, /available-offers, /offers/all

CONCLUSION: Full offer catalog is server-rendered HTML only
```

### Session Persistence
- Cookie names observed: AA SSO cookies
- localStorage keys: Standard session data
- Estimated session duration: Several hours (requires re-auth periodically)
- Playwright persistent context works well

---

## 2. eShopping Portal (aadvantageeshopping.com)

### Page Structure
- [x] Visited main merchants page
- URL: `https://www.aadvantageeshopping.com/b____.htm` (All stores)
- Authentication: Not required (public site), but logged-in state available

### Merchant List Structure
The site uses a class prefix `mn_` (merchant network). Two views available:
1. **Featured carousels** - "Top stores", "Winter deals" sections
2. **Alphabetical list** - A-Z organized store list with filters

```html
<!-- Merchant item in list -->
<li>
  <a href="...">Merchant Name</a>
  <div class="mn_rebateV4">
    <span class="mn_elevationOldValue">Was 1.5 miles/$</span>
    <span class="mn_elevationNewValue">Now 4 miles/$</span>
  </div>
</li>

<!-- Or for non-elevated rates -->
<li>
  <a href="...">Merchant Name</a>
  <div class="mn_rebateV4">
    <span class="mn_elevationNewValue">2 miles/$</span>
  </div>
</li>
```

### Key CSS Selectors
```
Merchant container: .mn_categoryMerchant (cards) or li (list)
Merchant name: a (link inside container)
Rate container: .mn_rebateV4
Old rate (was): .mn_elevationOldValue
Current rate: .mn_elevationNewValue
Tiered rate indicator: .mn_rebateTiered
Tiered prefix: .mn_tieredPrefix ("Up to")
```

### Rate Text Formats
1. Per-dollar: "X miles/$" or "X mile/$"
2. Flat bonus: "X miles" (for signup bonuses etc.)
3. Tiered: "Up to X miles" or "Up to X miles/$"
4. Elevated: "Was X, Now Y" (old + new values)

Examples observed:
- "Earn 2 miles/$"
- "Earn 600 miles"
- "Up to 4,900 miles"
- "Was 1.5 miles/$" → "Now 4 miles/$"

### API Discovery (Network Tab)
```
Note: Server-rendered HTML, no JSON API observed for merchant list
The site appears to render all merchants in the page HTML
```

### Sort/Filter Options
- Sort by: A-Z (alphabetical), RATE (by miles rate)
- Jump to: Letter dropdown (A, B, C, ...)
- Filter by: Category dropdown

### Recommendation
- [x] Use HTTP API (faster, simpler) - HTML can be fetched directly
- [ ] Use Playwright (dynamic content)
- Reason: Page is server-rendered, no authentication required for merchant rates

---

## 3. AAdvantage Hotels (aadvantagehotels.com)

### Search Flow
- [x] Performed test searches for Austin, TX
- Search URL pattern: `https://www.aadvantagehotels.com/search?adults=2&checkIn=MM%2FDD%2FYYYY&checkOut=MM%2FDD%2FYYYY&...`
- Authentication: Not required (public site), login available for personalized rates

### Search URL Parameters
```
Full URL example:
https://www.aadvantagehotels.com/search?
  adults=2
  &checkIn=01%2F10%2F2026
  &checkOut=01%2F12%2F2026
  &children=0
  &currency=USD
  &language=en
  &latitude=30.267153
  &longitude=-97.743061
  &locationType=CITY
  &mode=earn                      (earn or redeem)
  &placeId=AGODA_CITY%7C4542      (Agoda city ID)
  &program=aadvantage
  &query=Austin%20%28TX%29%2C%20United%20States
  &rooms=1
  &source=AGODA
```

### API Discovery (Network Tab)
```
Note: Server-side rendered via Next.js/React (Chakra UI)
No JSON API observed for hotel search results
Data appears embedded in server-rendered HTML
Backend powered by: Agoda/RocketMiles platform
```

### Hotel Card Structure
Site uses Chakra UI with dynamically generated class names (css-xxxxx).
Class names may change between deployments - rely on structure + text patterns.

```html
<!-- Hotel results container -->
<div class="chakra-stack css-1eopsh2">
  <!-- Each hotel is an anchor tag -->
  <a class="chakra-link css-du0jrd" href="/hotel/...">
    <!-- Image carousel -->
    <div class="default-carousel">...</div>

    <!-- Hotel info section -->
    <div class="css-13lpchn">
      <div class="css-nurbhq">
        <!-- Location -->
        <h4 class="chakra-text css-6iz5q7">Austin City Center</h4>
        <!-- Hotel name -->
        <h3 class="chakra-text css-48nr6r">The LINE Hotel Austin</h3>
        <!-- Star rating -->
        <div class="css-6c5u59">☆☆☆☆ ★★★★ 4-star property</div>
        <!-- Review score -->
        <span>8.4</span><span>Excellent</span><span>464 reviews</span>
        <!-- Badges -->
        <span>Free cancellation</span>
      </div>

      <!-- Miles & pricing section -->
      <div class="css-oxv9w">
        <!-- Base member miles -->
        <div class="css-gmlely">
          <div class="chakra-text css-1uje7gz">Earn 1,200 miles per stay</div>
          <span>AAdvantage® member</span>
        </div>
        <!-- Bonus cardmember miles -->
        <div class="css-jh3a5k">
          <p class="chakra-text css-jvp12g">Earn 13,000 miles per stay</p>
          <span>AAdvantage® credit cardmembers with status</span>
        </div>
        <!-- Price -->
        <h3 class="chakra-text css-1ndtlri">$481</h3>
        <span>Total (2 nights)</span>
        <span>includes fees</span>
      </div>
    </div>
  </a>
</div>
```

### Key CSS Selectors (Chakra UI - may change)
```
Results container: .chakra-stack (parent of hotel cards)
Hotel card link: a.chakra-link
Hotel name: h3.chakra-text (within card, first h3)
Location: h4.chakra-text (within card)
Star rating: div containing "star property" text
Review score: parsed from text (e.g., "8.4Excellent464 reviews")
Price: h3.chakra-text containing "$" (usually css-1ndtlri)
Miles (member): div containing "Earn X miles per stay" + "AAdvantage® member"
Miles (cardmember): div containing "Earn X miles per stay" + "cardmembers"
Free cancellation: span containing "Free cancellation"
```

### Miles Text Patterns
```
Base miles: "Earn {number} miles per stay" (AAdvantage® member)
Bonus miles: "Earn {number} miles per stay" (AAdvantage® credit cardmembers with status)
Numbers include commas: "1,200", "13,000"
```

### Recommendation
- [x] Use Playwright (dynamic React/Chakra UI content)
- [ ] Use HTTP API (no API found)
- Reason: Site is React-based with server-rendered content, Chakra UI components
- Note: Class names are dynamically generated, use text content for reliable extraction

### CORS / Auth Requirements
- [x] No authentication required for search
- [ ] Login available for personalized member rates
- Platform: Agoda/RocketMiles backend

---

## Summary & Implementation Decisions

### SimplyMiles
- Approach: Playwright persistent context (requires AA SSO authentication)
- Key challenges: Session persistence, pagination handling
- Selectors confirmed: [x] All selectors verified 2024-12-28
- **API Status:** Only `/get-activated-offers` found (returns user activations, not full catalog)
- Full offer catalog is server-rendered HTML - keep Playwright approach

### eShopping Portal
- **UPDATED 2024-12-28:** Cartera API discovered!
- **Primary approach:** Cartera REST API (fast, reliable, no browser needed)
- **API Endpoint:** `https://api.cartera.com/content/v4/merchants/all`
- **Parameters:** `brand_id=251, app_key=9ec260e91abc101aaec68280da6a5487, app_id=672b9fbb`
- Returns 1,400+ merchants with `name`, `rebate.value`, `rebate.isElevation`
- **Fallback:** Playwright HTML scraping if API fails
- Key selectors (fallback): `.mn_rebateV4`, `.mn_elevationOldValue`, `.mn_elevationNewValue`

### Hotels
- Approach: REST API (httpx) - same as older scripts
- **API Endpoints:**
  1. `GET /rest/aadvantage-hotels/places` - City lookup
  2. `GET /rest/aadvantage-hotels/searchRequest` - Create search
  3. `GET /rest/aadvantage-hotels/search/{uuid}` - Get results
- No browser needed - pure HTTP requests
- Backend: Agoda/RocketMiles platform

### Night Duration Testing (2024-12-28)
**v2 Test (Corrected Methodology):**
- Compared same nights booked differently: Thu-Sat as 2-night booking vs Thu+Fri as separate 1-night bookings
- Test date: Thu 01/15/2026 + Fri 01/16/2026
- Tested all 8 cities (Austin + Las Vegas returned usable data)

**Results (38 hotel comparisons):**
- Multi-night booking better: **71.1%** (27 hotels)
- Separate bookings better: 18.4% (7 hotels)
- Equal yield: 10.5% (4 hotels)

**Key Finding:** Multi-night bookings average **+1.01 mi/$** better yield in Austin

**Recommendation:** Keep current 2-night weekend approach - multi-night bookings have clearly better yields
- Note: 6 cities returned 0 parsable hotels (API structure issue, not search failure)

### Night Duration Testing v3 (2024-12-28)
**Comprehensive Test - Multiple Day/Night Combinations:**

Expanded testing to cover:
- Day-of-week: Monday, Wednesday, Thursday, Friday starts
- Night durations: 2-night, 3-night, 4-night stays
- Split strategies: 1+1, 2+1, 1+1+1, 2+2

**Results by Configuration (Austin data, ~35-38 hotels each):**

| Configuration | Hotels Compared | Multi-night Win % | Insight |
|--------------|-----------------|-------------------|---------|
| 2-night Mon  | 35              | 51%               | Marginal advantage |
| 2-night Wed  | 37              | 57%               | Slight advantage |
| **2-night Fri** | 38           | **68%**           | **Best for multi-night** |
| 3-night Thu  | 36              | 58%               | Slight advantage |
| 3-night Fri  | 35              | 51%               | Marginal |
| **4-night Thu** | 36           | **33%**           | **Separate 2+2 BETTER** |

**Key Findings:**
1. **Friday 2-night stays** have the strongest multi-night booking advantage (68% win rate)
2. **4-night stays** show separate 2+2 bookings outperform single 4-night booking (67% for separate)
3. Day-of-week matters: Weekend starts favor multi-night, weekday starts are marginal
4. 3-night stays: Multi-night slightly favored but not decisive

**Updated Recommendations:**
- **2-night weekend stays (Fri-Sun):** Keep multi-night booking approach ✓
- **4-night stays:** Consider separate 2+2 bookings for better yields
- **3-night stays:** Multi-night acceptable, but marginal benefit
- **Weekday 2-night stays:** No strong preference either way

**FIXED (2024-12-28):** 6 cities (Dallas, Houston, NYC, Boston, SF, LA) were returning 0 results due to **incorrect Agoda place IDs** in `config/cities.py`. The place IDs were discovered by searching on the website and extracting from the URL.

**Corrected Place IDs:**
| City | Old (wrong) | Correct |
|------|-------------|---------|
| Dallas | 6092 | **8683** |
| Houston | 7901 | **1178** |
| Las Vegas | 9055 | **17072** |
| New York | 11426 | **318** |
| Boston | 4848 | **9254** |
| San Francisco | 15280 | **13801** |
| Los Angeles | 9109 | **12772** |
| Austin | 4542 | 4542 (was correct) |

---

*Last updated: 2024-12-28*
*Completed by: Claude Code + Chrome Extension*
