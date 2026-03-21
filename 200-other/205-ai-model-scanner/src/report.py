"""Generate markdown reports and claude.md snippet."""

from __future__ import annotations

from datetime import date

from src.config import OUTPUTS_DIR
from src.models import AIModel, Pick


def write_markdown(scan_date: str, models: list[AIModel], picks: list[Pick]) -> None:
    """Generate outputs/latest.md with daily scan results."""
    total = len(models)
    by_tier = {}
    for m in models:
        by_tier[m.tier] = by_tier.get(m.tier, 0) + 1
    new_count = sum(1 for m in models if m.is_new)

    lines = [
        f"# AI Model Scanner Report",
        f"_Generated: {scan_date}_",
        "",
        "## Summary",
        f"- **Total models**: {total}",
        f"- **By tier**: {by_tier.get('fast', 0)} fast | {by_tier.get('flagship', 0)} flagship | {by_tier.get('deep', 0)} deep",
        f"- **New today**: {new_count}",
        "",
    ]

    # Top 20 picks
    lines.append("## Top 20 Picks")
    lines.append("")
    lines.append("| Use Case | Model | Provider | Input $/M | Output $/M | Context | Why |")
    lines.append("|----------|-------|----------|-----------|------------|---------|-----|")

    for p in picks:
        ctx = f"{p.context_window:,}" if p.context_window else "?"
        lines.append(
            f"| {p.use_case} | {p.model_name} | {p.provider} | "
            f"${p.input_price:.2f} | ${p.output_price:.2f} | {ctx} | {p.why} |"
        )

    lines.append("")

    # New models section
    new_models = [m for m in models if m.is_new]
    if new_models:
        lines.append("## New Models (from Grok search)")
        lines.append("")
        lines.append("| Model | Provider | Tier | Input $/M | Context |")
        lines.append("|-------|----------|------|-----------|---------|")
        for m in new_models:
            ctx = f"{m.context_window:,}" if m.context_window else "?"
            lines.append(f"| {m.model_name} | {m.provider} | {m.tier} | ${m.input_price:.2f} | {ctx} |")
        lines.append("")

    # Tier breakdown
    lines.append("## Models by Tier")
    lines.append("")
    for tier in ["deep", "flagship", "fast"]:
        tier_models = sorted(
            [m for m in models if m.tier == tier],
            key=lambda m: (m.input_price or 0) + (m.output_price or 0),
        )
        lines.append(f"### {tier.capitalize()} ({len(tier_models)})")
        lines.append("")
        if tier_models[:10]:
            lines.append("| Model | Provider | Input $/M | Output $/M | Context |")
            lines.append("|-------|----------|-----------|------------|---------|")
            for m in tier_models[:10]:
                ctx = f"{m.context_window:,}" if m.context_window else "?"
                lines.append(
                    f"| {m.model_name} | {m.provider} | "
                    f"${m.input_price:.2f} | ${m.output_price:.2f} | {ctx} |"
                )
            if len(tier_models) > 10:
                lines.append(f"| ... and {len(tier_models) - 10} more | | | | |")
        lines.append("")

    content = "\n".join(lines)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUTS_DIR / "latest.md").write_text(content)
    print(f"  [ok] Wrote outputs/latest.md ({total} models, {len(picks)} picks)")


def write_claude_md_snippet() -> None:
    """Generate outputs/claude_md_snippet.md — the actual product.

    This is the block that gets dropped into every project's CLAUDE.md.
    It contains instructions for Claude to query Supabase MCP for live model data.
    """
    today = date.today().isoformat()

    content = f"""## AI Model Selection (Live Data)

This project uses a live AI model database updated daily at 7am UTC.
The data lives in Supabase under the `ai_scanner` schema.
_Last generated: {today}_

### RULE: Before choosing, hardcoding, or recommending any AI model, Claude MUST:

1. Query `ai_scanner.latest_picks` via Supabase MCP to get today's recommendations
2. Check `ai_scanner.upgrade_suggestions` to see if this project has cheaper alternatives
3. If the task matches a known use case, use the pre-computed pick

### How to query (via Supabase MCP):

**Get the best model for a specific need:**
```sql
SELECT * FROM ai_scanner.pick('cheapest_with_tools');
-- Other keys: absolute_cheapest, cheapest_flagship, cheapest_with_search,
-- cheapest_with_vision, cheapest_with_reasoning, cheapest_100k_ctx,
-- cheapest_500k_ctx, cheapest_1m_ctx, best_under_1_dollar,
-- best_under_3_dollars, best_deep_thinker, best_open_weight,
-- cheapest_tools_search, cheapest_tools_reason, best_for_agents,
-- best_for_research, best_for_classification, best_for_long_docs, best_value
```

**Check if this project should switch models:**
```sql
SELECT * FROM ai_scanner.upgrade_suggestions
WHERE project_name = 'THIS_PROJECT_NAME';
```

**Custom filter (find exactly what you need):**
```sql
SELECT model_name, model_id, provider, input_price, output_price, context_window
FROM ai_scanner.latest
WHERE has_tools = true
  AND has_reasoning = true
  AND input_price < 3.0
  AND context_window >= 200000
ORDER BY input_price ASC
LIMIT 5;
```

**Register this project's current model usage** (do this once, update when switching):
```sql
INSERT INTO ai_scanner.projects (project_name, task, current_model, current_provider, needs_tools, needs_search, needs_reasoning, min_context)
VALUES ('THIS_PROJECT_NAME', 'primary_task', 'model-id-here', 'provider', true, false, true, 100000)
ON CONFLICT (project_name, task) DO UPDATE SET
  current_model = EXCLUDED.current_model,
  current_provider = EXCLUDED.current_provider,
  updated_at = now();
```

### Decision Tree:

When selecting a model for a task in this project:
- **Simple/high-volume?** -> `pick('absolute_cheapest')` or `pick('cheapest_with_tools')`
- **Needs web data?** -> `pick('cheapest_with_search')` or `pick('best_for_research')`
- **Quality matters?** -> `pick('best_under_3_dollars')` or `pick('best_deep_thinker')`
- **Long input?** -> `pick('cheapest_500k_ctx')` or `pick('cheapest_1m_ctx')`
- **Investment analysis?** -> `pick('best_for_research')` (needs search + reasoning)
- **Coding/agents?** -> `pick('best_for_agents')` (needs tools + reasoning)
- **Budget-critical?** -> `pick('best_value')` -- best quality-to-price ratio

### Prices change daily. NEVER rely on memorized prices. Always query.
"""
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUTS_DIR / "claude_md_snippet.md").write_text(content)
    print(f"  [ok] Wrote outputs/claude_md_snippet.md")
