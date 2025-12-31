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


BATCH_CATEGORIZATION_PROMPT = """Categorize these {count} Product Hunt products in a single response.

PRODUCTS:
{products_list}

Return a JSON array with one object per product, in the same order:

[
  {{
    "rank": 1,
    "category": "<AI|SaaS|Developer Tools|Design|Productivity|Marketing|Finance|Health|Education|E-commerce|Social|Hardware|Gaming|Other>",
    "subcategory": "<specific type>",
    "target_audience": "<Developers|Designers|Marketers|Founders|Teams|Consumers|Enterprise|Creators>",
    "pricing_model": "<Free|Freemium|Paid|Enterprise|Open Source>",
    "tech_stack": ["<tech1>", "<tech2>"],
    "innovation_score": <1-10>,
    "market_fit_score": <1-10>
  }},
  ...
]

Be concise but accurate. Use the product's description and name to infer details."""
