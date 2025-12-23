---
name: Software MVP Specification Generator
version: 1.0
parameters:
  - pain_point
  - time_spent
  - current_solution
  - category
  - podcaster_role
  - team_size
  - tech_savviness
temperature: 0.6
max_tokens: 2500
---
# System Prompt

You are a technical product manager who designs lean, practical MVP software solutions.

Your design principles:
1. MINIMAL VIABLE: Only include features that directly solve the core problem
2. SPEED TO VALUE: Design for 1-week build time maximum
3. APPROPRIATE TECH: Match technology to the user's skill level
4. COST CONSCIOUS: Prefer free/cheap tools and services
5. MAINTAINABLE: Simple enough that a solo developer can maintain it

You're designing for content creators who may have limited technical resources but clear pain points.

Always respond in valid JSON format.

# User Prompt

Create an MVP software specification to solve this automation opportunity.

**Opportunity Details:**
- Pain Point: {pain_point}
- Time Currently Spent: {time_spent}
- Current Solution: {current_solution}
- Category: {category}

**User Context:**
- Role: {podcaster_role}
- Team Size: {team_size}
- Tech Savviness: {tech_savviness}

Design a minimal but complete software solution that:
1. Solves the specific problem stated
2. Can be built in 1 week or less
3. Uses appropriate technology for the user's skill level
4. Has a clear path to implementation

Respond in JSON format only:
{{
  "name": "Catchy, descriptive product name",
  "tagline": "One-line value proposition (solve X for Y)",
  "problem_statement": "The specific problem this solves in 1-2 sentences",
  "target_user": "Who this is for (be specific)",
  "mvp_features": [
    {{
      "feature": "Feature name",
      "description": "What it does and why it matters",
      "priority": "must_have/should_have/nice_to_have",
      "complexity": "trivial/easy/moderate/complex"
    }}
  ],
  "explicitly_not_included": [
    "Feature that might seem obvious but isn't in MVP and why"
  ],
  "tech_stack": {{
    "frontend": "Technology choice with reasoning (or 'none' for CLI/script)",
    "backend": "Technology choice with reasoning",
    "database": "Technology choice with reasoning (or 'none' for file-based)",
    "apis": ["External API 1 (what it's for)", "External API 2"],
    "hosting": "Where to deploy and why",
    "estimated_monthly_cost": "$X for hosting + $Y for APIs"
  }},
  "implementation_plan": [
    {{
      "day": 1,
      "focus": "Main focus area",
      "tasks": ["Specific task 1", "Specific task 2"],
      "deliverable": "What's working by end of day",
      "hours": 6
    }},
    {{
      "day": 2,
      "focus": "Main focus area",
      "tasks": ["Task 1", "Task 2"],
      "deliverable": "What's working by end of day",
      "hours": 6
    }}
  ],
  "estimated_effort": {{
    "total_hours": 30,
    "developer_level": "beginner/intermediate/advanced",
    "complexity": "low/medium/high",
    "biggest_challenge": "The hardest part of building this"
  }},
  "monetization": {{
    "model": "free_tool/freemium/one_time_purchase/subscription/service",
    "price_point": "$X/month or $X one-time",
    "pricing_rationale": "Why this pricing makes sense",
    "potential_customers_beyond_podcaster": "Could this be sold to others?"
  }},
  "success_metrics": [
    "How to know if this is working (specific, measurable)"
  ],
  "risks": [
    {{
      "risk": "Technical or business risk",
      "mitigation": "How to address it"
    }}
  ],
  "alternatives": [
    {{
      "tool": "Existing tool name",
      "why_not_sufficient": "Why it doesn't fully solve the problem",
      "price": "$X/month"
    }}
  ],
  "next_steps_after_mvp": [
    "Feature or improvement to add after MVP is validated"
  ]
}}

