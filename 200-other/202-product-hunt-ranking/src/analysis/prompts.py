"""Prompt templates for Grok AI analysis."""

PRODUCT_CATEGORIZATION_PROMPT = """Analyze this Product Hunt product and categorize it.

PRODUCT:
Name: {name}
Description: {description}
URL: {url}
Upvotes: {upvotes}

Return a JSON object with these exact fields:

{{
  "category": "<primary category - one of: AI, SaaS, Developer Tools, Design, Productivity, Marketing, Finance, Health, Education, E-commerce, Social, Hardware, Gaming, Other>",
  "subcategory": "<more specific subcategory, e.g., 'AI Writing Assistant', 'No-Code Builder'>",
  "target_audience": "<primary audience - one of: Developers, Designers, Marketers, Founders, Teams, Consumers, Enterprise, Creators>",
  "pricing_model": "<one of: Free, Freemium, Paid, Enterprise, Open Source>",
  "tech_stack": ["<inferred technologies if obvious, e.g., 'AI/ML', 'React', 'API'>"],
  "innovation_score": <1-10 based on novelty and technical innovation>,
  "market_fit_score": <1-10 based on clear value prop and target market>
}}

SCORING GUIDE:
Innovation Score:
- 9-10: Genuinely novel approach, new technology application
- 7-8: Interesting twist on existing concept
- 5-6: Solid execution of known idea
- 3-4: Me-too product, minor iteration
- 1-2: Commodity/clone

Market Fit Score:
- 9-10: Clear pain point, obvious value, strong demand signal (high upvotes)
- 7-8: Good value prop, defined audience
- 5-6: Decent idea but unclear differentiation
- 3-4: Niche or unclear value
- 1-2: Solution looking for problem

Be objective. High upvotes suggest market interest but don't guarantee innovation."""


WEEKLY_INSIGHTS_PROMPT = """Analyze these top 10 Product Hunt products from Week {week_number} of {year}.

PRODUCTS:
{products_json}

Provide a comprehensive analysis in this exact JSON format:

{{
  "top_trends": [
    "<trend 1 - e.g., 'AI-powered writing tools dominating'>",
    "<trend 2 - e.g., 'Focus on developer productivity'>",
    "<trend 3 - e.g., 'Rise of vertical SaaS solutions'>"
  ],
  "notable_launches": "<2-3 sentence narrative highlighting the most interesting products and why they stood out>",
  "category_breakdown": {{
    "<category>": <count>,
    "<category>": <count>
  }},
  "sentiment": "<one of: Bullish, Neutral, Bearish based on innovation quality and market reception>",
  "key_observation": "<single most important insight from this week's launches>"
}}

ANALYSIS GUIDELINES:
- Identify patterns across multiple products
- Note any surprising entries or absences
- Consider upvote distribution (high variance vs clustered)
- Look for emerging themes vs established categories
- Assess overall quality of launches this week

Sentiment Guide:
- Bullish: Strong innovation, high engagement, diverse categories
- Neutral: Mixed quality, average engagement
- Bearish: Weak launches, low innovation, oversaturated categories"""


BATCH_CATEGORIZATION_PROMPT = """Analyze these {count} Product Hunt products with deep insights.

PRODUCTS:
{products_list}

Return a JSON object with a "products" array containing one object per product, in the same order:

{{
  "products": [
    {{
      "rank": 1,
      "category": "<AI|SaaS|Developer Tools|Design|Productivity|Marketing|Finance|Health|Education|E-commerce|Social|Hardware|Gaming|Other>",
      "subcategory": "<specific type, e.g., 'AI Image Generator', 'Code Assistant'>",
      "target_audience": "<Developers|Designers|Marketers|Founders|Teams|Consumers|Enterprise|Creators>",
      "pricing_model": "<Free|Freemium|Paid|Enterprise|Open Source>",
      "tech_stack": ["<inferred technologies>"],
      "innovation_score": <1-10>,
      "market_fit_score": <1-10>,
      "one_liner": "<10-15 word summary of what it does and why it matters>",
      "key_differentiator": "<what makes this stand out from competitors>",
      "comparable_products": ["<similar product 1>", "<similar product 2>"],
      "stage": "<MVP|Growth|Established|Pivot>",
      "moat": "<network effects|tech|brand|data|switching costs|none>",
      "red_flags": ["<potential issues if any>"],
      "bullish_signals": ["<positive indicators>"]
    }},
    ...
  ]
}}

DEEP ANALYSIS GUIDELINES:
- one_liner: Crisp value prop, not marketing fluff
- key_differentiator: What's genuinely novel vs. existing solutions
- comparable_products: Name actual competitors or similar tools
- stage: MVP (just launched), Growth (gaining traction), Established (proven), Pivot (changing direction)
- moat: Sustainable competitive advantage (be skeptical - most have none)
- red_flags: Overpromising, crowded market, unclear value, bad timing, etc.
- bullish_signals: Strong traction, novel tech, clear pain point, good timing

SCORING:
- innovation_score 9-10: Genuinely novel, first-mover advantage
- innovation_score 7-8: Interesting twist on existing concept
- innovation_score 5-6: Solid execution, nothing new
- innovation_score 1-4: Me-too, clone

- market_fit_score 9-10: Obvious pain point, strong demand signals
- market_fit_score 7-8: Clear audience, good value prop
- market_fit_score 5-6: Unclear differentiation
- market_fit_score 1-4: Solution looking for problem

Be brutally honest. High upvotes don't equal innovation."""
