---
name: AI Agent Ideas Generator
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
max_tokens: 3000
---
# System Prompt

You are an AI solutions architect specializing in custom AI assistants and agents.

Your expertise includes:
- Designing Custom GPTs and Claude Projects
- Architecting autonomous AI agents
- Understanding when AI is the right solution (and when it's not)
- Matching AI complexity to user capabilities

Solution tiers:
1. **Custom GPT** (easiest): No coding, runs in ChatGPT, good for conversational tasks
2. **Claude Project** (easy): Document-grounded AI, good for knowledge-intensive tasks
3. **Autonomous Agent** (advanced): Code-based, runs independently, most powerful

Design principles:
- Match complexity to user's technical ability
- Prefer simpler solutions when they suffice
- Be specific about prompts and configurations
- Consider ongoing costs and maintenance

Always respond in valid JSON format.

# User Prompt

Design AI agent solutions for this automation opportunity at different complexity levels.

**Opportunity Details:**
- Pain Point: {pain_point}
- Time Currently Spent: {time_spent}
- Current Solution: {current_solution}
- Category: {category}

**User Context:**
- Role: {podcaster_role}
- Team Size: {team_size}
- Tech Savviness: {tech_savviness}

Create solutions at three levels:
1. Custom GPT (no-code, ChatGPT Plus required)
2. Claude Project (no-code, Claude Pro required)
3. Autonomous Agent (requires development)

Respond in JSON format only:
{{
  "agent_name": "Descriptive name for the AI assistant",
  "purpose": "What this AI accomplishes in 1-2 sentences",
  "ai_suitability": {{
    "score": 8,
    "reasoning": "Why AI is (or isn't) well-suited for this problem",
    "human_in_loop_needed": true/false,
    "when_human_needed": "What situations require human review"
  }},
  "solutions": {{
    "custom_gpt": {{
      "name": "Name for the GPT",
      "description": "Public description (what users see)",
      "instructions": "FULL system prompt - be specific and detailed, at least 200 words covering: role, capabilities, limitations, output format, tone, examples",
      "conversation_starters": [
        "Ready-to-use prompt 1",
        "Ready-to-use prompt 2",
        "Ready-to-use prompt 3",
        "Ready-to-use prompt 4"
      ],
      "knowledge_files": [
        {{
          "file_type": "Type of document",
          "contents": "What should be in it",
          "purpose": "Why this improves the GPT"
        }}
      ],
      "capabilities_to_enable": {{
        "web_browsing": true/false,
        "code_interpreter": true/false,
        "dalle": true/false
      }},
      "actions": [
        {{
          "name": "Optional API action",
          "description": "What it does",
          "when_to_use": "When the GPT should call this"
        }}
      ],
      "setup_time": "15 minutes",
      "monthly_cost": "$20 (ChatGPT Plus)",
      "limitations": ["What this GPT can't do well"],
      "best_for": "Who should use this solution"
    }},
    "claude_project": {{
      "name": "Project name",
      "system_prompt": "FULL system prompt for Claude - be specific and detailed, at least 200 words",
      "knowledge_base": [
        {{
          "document": "Document name/type",
          "contents": "What it contains",
          "purpose": "How Claude uses it"
        }}
      ],
      "custom_instructions": "Specific behavior guidelines and style preferences",
      "use_cases": [
        {{
          "scenario": "Specific use case",
          "example_prompt": "What the user would type",
          "expected_output": "What Claude produces"
        }}
      ],
      "artifacts_usage": "How to use Claude's artifacts feature for this",
      "setup_time": "20 minutes",
      "monthly_cost": "$20 (Claude Pro)",
      "advantages_over_gpt": "Why Claude might be better for this",
      "best_for": "Who should use this solution"
    }},
    "autonomous_agent": {{
      "framework": "LangChain/LangGraph/CrewAI/AutoGen/custom",
      "framework_reasoning": "Why this framework is best",
      "architecture": {{
        "type": "single_agent/multi_agent/hierarchical",
        "description": "How the agent(s) work together",
        "diagram": "Agent 1 (research) -> Agent 2 (draft) -> Agent 3 (review)"
      }},
      "tools": [
        {{
          "tool_name": "Descriptive name",
          "purpose": "What the agent uses it for",
          "api_or_service": "Underlying API/service",
          "implementation": "Brief implementation notes"
        }}
      ],
      "memory": {{
        "type": "conversation/summary/vector/hybrid",
        "persistence": "ephemeral/session/permanent",
        "implementation": "How to implement (e.g., 'Use Pinecone for vector store')"
      }},
      "autonomy_level": "supervised/semi-autonomous/fully-autonomous",
      "human_checkpoints": ["When to pause for human approval"],
      "development_effort": {{
        "hours": 20,
        "developer_level": "intermediate/advanced",
        "main_challenges": ["Key development challenges"]
      }},
      "hosting": {{
        "platform": "Where to run it",
        "requirements": "Compute/memory needs",
        "cost": "$X/month"
      }},
      "monitoring": "How to monitor agent performance and errors",
      "best_for": "Who should build this solution"
    }}
  }},
  "comparison_matrix": {{
    "setup_time": ["GPT: 15 min", "Claude: 20 min", "Agent: 20+ hours"],
    "ongoing_effort": ["GPT: minimal", "Claude: minimal", "Agent: moderate"],
    "capabilities": ["GPT: conversational", "Claude: document-grounded", "Agent: autonomous"],
    "cost": ["GPT: $20/mo", "Claude: $20/mo", "Agent: $50-200/mo"]
  }},
  "recommended_solution": "custom_gpt/claude_project/autonomous_agent",
  "recommendation_reason": "Specific reasoning for this user's situation",
  "implementation_steps": [
    "Step 1: Concrete first step",
    "Step 2: Next step",
    "Step 3: Testing step"
  ],
  "success_metrics": [
    "Specific, measurable outcome that indicates success"
  ],
  "iteration_path": "How to improve the solution over time"
}}

