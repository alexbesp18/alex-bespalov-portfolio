# Future: New Ideas & Explorations

Pure new concepts, features, and directions not yet implemented or designed.

---

## 1. Multi-Program Support

### Concept
Expand beyond AA to track loyalty points across multiple programs.

### Programs to Consider
| Program | Portal | Card-Linked | Hotels |
|---------|--------|-------------|--------|
| AA AAdvantage | ✅ Current | ✅ SimplyMiles | ✅ Current |
| United MileagePlus | MileagePlus Shopping | — | United Hotels |
| Delta SkyMiles | SkyMiles Shopping | — | Delta Hotels |
| Southwest Rapid Rewards | Rapid Rewards Shopping | — | — |
| Chase Ultimate Rewards | Chase Shop Through | — | Chase Travel |
| Amex Membership Rewards | Amex Offers | Amex Offers | Amex Travel |
| Capital One Miles | Capital One Shopping | — | Capital One Travel |

### Architecture Approach
```
┌─────────────────────────────────────────┐
│           Program Interface             │
│  - scrape_offers()                      │
│  - scrape_portal_rates()                │
│  - scrape_hotels()                      │
│  - get_point_value()  # cents per point │
└─────────────────────────────────────────┘
          ↑           ↑           ↑
    ┌─────┴───┐ ┌─────┴───┐ ┌─────┴───┐
    │   AA    │ │ United  │ │  Delta  │
    │ Plugin  │ │ Plugin  │ │ Plugin  │
    └─────────┘ └─────────┘ └─────────┘
```

### Cross-Program Comparisons
```
Amazon purchase $50:
  AA eShopping:     5 mi/$ = 250 miles (~$2.50 value)
  United Shopping:  3 mi/$ = 150 miles (~$1.95 value)
  Chase UR Mall:    2x     = 100 UR    (~$2.00 value)
  ➤ Best: AA eShopping
```

---

## 2. Browser Extension

### Concept
Chrome/Firefox extension showing deal info while shopping.

### Features
- **Badge indicator:** Show current portal rate on any merchant site
- **SimplyMiles check:** "Offer available" indicator
- **Stack alert:** "This merchant can be stacked!"
- **Quick activate:** One-click offer activation
- **Price comparison:** Show LP value vs cash back

### UI Mockup
```
┌────────────────────────────────────┐
│ 🛫 AA Points Helper        [⚙️] [×]│
├────────────────────────────────────┤
│ amazon.com                          │
│                                     │
│ 📊 Portal Rate: 5 mi/$              │
│ 💳 SimplyMiles: 150 LP bonus ✓      │
│ 💰 Combined: ~35 LP/$               │
│                                     │
│ [Activate SimplyMiles] [Go to Portal]│
└────────────────────────────────────┘
```

### Technical Approach
```javascript
// content-script.js
const merchant = detectMerchant(window.location.hostname);
const dealInfo = await fetchDealInfo(merchant);

if (dealInfo.hasStack) {
  showStackBadge(dealInfo);
}
```

---

## 3. Purchase Tracking & ROI

### Concept
Track actual purchases to measure realized LP earnings vs expected.

### Features
- Manual purchase entry
- Receipt scanning (OCR)
- Bank statement import
- AA account sync (scrape posted miles)
- Running totals and projections

### Data Model
```python
@dataclass
class Purchase:
    id: str
    merchant: str
    amount: float
    date: datetime
    expected_miles: int
    actual_miles: Optional[int]  # Filled when posted
    channels_used: list[str]  # ["portal", "simplymiles", "cc"]
    status: Literal["pending", "posted", "disputed"]

@dataclass
class ROISummary:
    total_spent: float
    total_miles_expected: int
    total_miles_posted: int
    blended_yield: float
    status_progress: float  # % toward goal
```

### Reporting
```
┌─────────────────────────────────────────┐
│ DECEMBER 2024 SUMMARY                   │
├─────────────────────────────────────────┤
│ Purchases: 12                           │
│ Total Spent: $487.32                    │
│ Miles Posted: 7,842 ✓                   │
│ Miles Pending: 1,250 ⏳                 │
│ Blended Yield: 18.7 LP/$                │
│                                         │
│ Status Progress: 52,842 / 75,000 (70%)  │
│ Est. Platinum: March 2025               │
└─────────────────────────────────────────┘
```

---

## 4. ML-Based Yield Prediction

### Concept
Predict future yields based on historical patterns.

### Input Features
- Day of week
- Month / season
- Days until check-in
- Historical yield for same combo
- Promotional calendar events
- Competitor pricing signals

### Model Options
1. **Simple:** Linear regression on historical averages
2. **Medium:** Gradient boosting (XGBoost/LightGBM)
3. **Advanced:** Time series (Prophet, ARIMA)

### Use Cases
- "Best day to book Vegas in February"
- "Optimal advance booking window"
- "Anomaly detection for exceptional deals"
- "Price drop predictions"

### Implementation Sketch
```python
from sklearn.ensemble import GradientBoostingRegressor

def train_yield_predictor():
    db = get_database()
    history = db.get_historical_yields()

    X = prepare_features(history)  # dow, month, advance, etc.
    y = history["yield_ratio"]

    model = GradientBoostingRegressor()
    model.fit(X, y)

    return model

def predict_yield(city, check_in_date, duration):
    features = extract_features(city, check_in_date, duration)
    return model.predict([features])[0]
```

---

## 5. Social & Community Features

### Concept
Share deals with trusted friends/family, crowdsource intelligence.

### Features
- **Private groups:** Share deals with specific people
- **Deal voting:** Upvote/downvote deal quality
- **Crowdsourced aliases:** Community-submitted merchant matches
- **Success stories:** "I earned X miles on Y"
- **Leaderboards:** Gamification for engagement

### Privacy Model
```
┌─────────────────────────────────────┐
│ Sharing Levels:                     │
│                                     │
│ 🔒 Private    - Only you            │
│ 👥 Group      - Selected people     │
│ 🌐 Community  - All users           │
│ 📢 Public     - Anyone (no login)   │
└─────────────────────────────────────┘
```

### Deal Feed
```
┌─────────────────────────────────────────┐
│ 🔥 HOT DEALS IN YOUR NETWORK            │
├─────────────────────────────────────────┤
│ @john_doe found: Amazon Kindle 30 LP/$  │
│ 👍 12  💬 3  🔄 Share                    │
├─────────────────────────────────────────┤
│ @travel_hacker: Vegas hotel 28 LP/$     │
│ 👍 8   💬 1  🔄 Share                    │
└─────────────────────────────────────────┘
```

---

## 6. Credit Card Optimization

### Concept
Recommend the best card to use for each purchase.

### Data Needed
- Card bonus categories (rotating and permanent)
- Current promotional offers
- Point transfer partners
- Annual fee and break-even analysis

### Decision Engine
```python
@dataclass
class CardRecommendation:
    card: str
    earn_rate: float
    points_earned: int
    point_value: float  # cents
    total_value: float
    reasoning: str

def recommend_card(merchant: str, amount: float, user_cards: list[Card]):
    recommendations = []

    for card in user_cards:
        category = categorize_merchant(merchant)
        earn_rate = card.get_earn_rate(category)
        points = amount * earn_rate
        value = points * card.point_value

        recommendations.append(CardRecommendation(
            card=card.name,
            earn_rate=earn_rate,
            points_earned=points,
            point_value=card.point_value,
            total_value=value,
            reasoning=f"{earn_rate}x on {category}"
        ))

    return sorted(recommendations, key=lambda x: x.total_value, reverse=True)
```

### Example Output
```
Purchase: Uber Eats $35

Card Options:
1. 🥇 AA Mastercard     3x dining  = 105 mi  ($1.47 value)
2. 🥈 Chase Sapphire    3x dining  = 105 UR  ($1.58 value)*
3. 🥉 Amex Gold         4x dining  = 140 MR  ($1.40 value)

* Chase UR transfers 1:1 to AA if needed

Recommendation: Use Chase Sapphire (best value)
But if you need AA miles: Use AA Mastercard
```

---

## 7. Flight Award Integration

### Concept
Connect LP earning to actual flight redemptions.

### Features
- Track award availability for target routes
- Calculate "real" LP value based on redemption
- Alert when you have enough for specific flights
- Sweet spot finder (best value redemptions)

### Award Search Integration
```python
@dataclass
class AwardFlight:
    origin: str
    destination: str
    date: datetime
    cabin: str  # economy, business, first
    miles_required: int
    taxes_fees: float
    cash_price: float  # For comparison
    value_per_mile: float  # cents

def find_award_sweet_spots(origin: str, flexible_dates: bool = True):
    """Find high-value award redemptions from origin."""
    routes = get_aa_routes_from(origin)
    awards = []

    for route in routes:
        availability = search_award_availability(route)
        for flight in availability:
            cash_price = get_cash_price(flight)
            value = (cash_price - flight.taxes_fees) / flight.miles_required * 100

            if value > 1.5:  # >1.5 cpp is good value
                awards.append(flight)

    return sorted(awards, key=lambda x: x.value_per_mile, reverse=True)
```

### Goal Tracking
```
┌─────────────────────────────────────────┐
│ 🎯 YOUR REDEMPTION GOALS                │
├─────────────────────────────────────────┤
│ AUS → Tokyo (Business)                  │
│ Miles needed: 85,000                    │
│ You have: 52,000                        │
│ Gap: 33,000 miles                       │
│ At 15 LP/$: Spend $2,200 more           │
│ Est. date: April 2025                   │
├─────────────────────────────────────────┤
│ [Search Availability] [Set Alert]       │
└─────────────────────────────────────────┘
```

---

## 8. Alternative Data Sources

### Concept
Expand data collection beyond official sources.

### Sources to Explore

#### Deal Aggregator Sites
- The Points Guy deal alerts
- Doctor of Credit
- Frequent Miler

#### Social Media
- Twitter/X deal accounts (@ThePointsGuy, etc.)
- Reddit r/churning, r/awardtravel
- FlyerTalk forums

#### Email Newsletters
- Parse promotional emails
- Track limited-time offers

### Implementation Considerations
```python
class DealAggregator:
    """Collect deals from third-party sources."""

    async def fetch_reddit_deals(self, subreddit: str = "churning"):
        # Use Reddit API or PRAW
        pass

    async def fetch_twitter_deals(self, accounts: list[str]):
        # Use Twitter API v2
        pass

    async def parse_deal_email(self, email_content: str):
        # NLP to extract deal details
        pass

    def deduplicate_with_primary(self, external_deals: list):
        """Match external deals with our primary sources."""
        pass
```

---

## 9. Automated Activation

### Concept
Automatically activate SimplyMiles offers.

### Risk Assessment
| Factor | Risk Level | Mitigation |
|--------|------------|------------|
| ToS violation | Medium | Review terms carefully |
| Session stability | High | Robust error handling |
| UI changes | High | Selector monitoring |
| Account lockout | Medium | Conservative rate limits |

### Safer Alternative: One-Click Deep Links
```python
def generate_activation_link(offer_id: str) -> str:
    """Generate deep link to pre-filled activation page."""
    return f"https://simplymiles.com/activate?offer={offer_id}&auto=1"
```

### If Implementing Full Automation
```python
async def auto_activate_offers(offers: list[Offer], max_per_session: int = 5):
    """
    Automatically activate SimplyMiles offers.

    WARNING: Use at your own risk. May violate ToS.
    """
    browser = await launch_browser()

    try:
        await login_to_simplymiles(browser)

        activated = 0
        for offer in offers[:max_per_session]:
            try:
                await activate_single_offer(browser, offer)
                activated += 1
                await random_delay(5, 15)  # Be respectful
            except ActivationError as e:
                logger.warning(f"Failed to activate {offer.merchant}: {e}")

        return activated
    finally:
        await browser.close()
```

---

## 10. Moonshot Ideas

### Voice Assistant Integration
```
"Hey Siri, what's the best AA deal right now?"

→ "The best deal is Amazon Kindle at 30 LP per dollar.
   Spend $5 to earn 150 loyalty points.
   Should I send you the details?"
```

### AR Shopping Companion
- Point phone at store → see LP yield overlay
- Scan barcode → show stacking opportunities
- Location-based alerts when near high-yield merchants

### Automated Shopping Bot
```python
async def execute_optimal_shopping(
    shopping_list: list[str],
    budget: float,
    constraints: dict
) -> list[Purchase]:
    """
    Given a shopping list and budget, execute purchases
    through optimal channels automatically.

    WARNING: This is a concept only. Significant legal and
    practical considerations apply.
    """
    pass
```

### LP Arbitrage Marketplace
- Connect people who want LPs with people who have deals
- "I'll buy your $5 Kindle for $7, you earn the 150 LPs"
- Escrow system for trust

---

## Idea Evaluation Framework

When evaluating new ideas:

| Criterion | Weight | Question |
|-----------|--------|----------|
| LP Impact | 35% | How many additional LPs can this generate? |
| Effort | 25% | How long to build and maintain? |
| Risk | 20% | What could go wrong? Legal/ToS issues? |
| Novelty | 10% | Is this unique/innovative? |
| Fun | 10% | Is this enjoyable to build/use? |

### Scoring Template
```
Idea: [Name]

LP Impact:    [ ] Low  [ ] Medium  [ ] High
Effort:       [ ] Low  [ ] Medium  [ ] High
Risk:         [ ] Low  [ ] Medium  [ ] High
Novelty:      [ ] Low  [ ] Medium  [ ] High
Fun:          [ ] Low  [ ] Medium  [ ] High

Total Score: ___/50
Priority: ___
```

---

## Contributing New Ideas

To add an idea to this document:

1. **Describe clearly:** What is it?
2. **Explain value:** Why would someone want this?
3. **Sketch approach:** How might it work?
4. **Note risks:** What could go wrong?
5. **Estimate effort:** Low/Medium/High

---

*Last updated: 2024-12-29*
*Ideas are just ideas until built. Dream big, ship small.*
