# AI Model Scanner

Daily bot that catalogs AI model pricing and capabilities from OpenRouter + Grok web search, assigns quality tiers, stores in Supabase, and computes 20 recommendation picks.

## How It Works

```
OpenRouter /models (free)  ──┐
                              ├──> Merge + Tier ──> Supabase ──> 20 Picks ──> Reports
Grok web search (~$0.03)  ──┘
```

1. **OpenRouter**: Free GET request returns ~400+ models with pricing, context windows, and capability flags
2. **Grok**: One web search call catches new releases and price changes from the last 7 days
3. **Tiers**: Models classified as `fast` (cheap/quick), `flagship` (balanced), or `deep` (max capability)
4. **Picks**: 20 pre-computed recommendations for common use cases (cheapest with tools, best for agents, etc.)
5. **Reports**: Daily markdown report + a `claude_md_snippet.md` for dropping into any project

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env from template
cp .env.example .env
# Fill in: SUPABASE_URL, SUPABASE_SERVICE_KEY, XAI_API_KEY

# Run
python -m src.main
```

## Cost

| Component | Per Run | Monthly |
|-----------|---------|---------|
| OpenRouter GET /models | $0.00 | $0.00 |
| Grok web search | ~$0.03 | ~$0.90 |
| Supabase | $0.00 | $0.00 |
| GitHub Actions | $0.00 | $0.00 |
| **Total** | **~$0.03** | **~$0.90** |

## The 20 Picks

| Key | What it finds |
|-----|---------------|
| `absolute_cheapest` | Lowest price across all models |
| `cheapest_flagship` | Cheapest flagship-tier model |
| `cheapest_with_tools` | Cheapest with function calling |
| `cheapest_with_search` | Cheapest with web search |
| `cheapest_with_vision` | Cheapest with image input |
| `cheapest_with_reasoning` | Cheapest with extended reasoning |
| `cheapest_100k_ctx` | Cheapest with 100K+ context |
| `cheapest_500k_ctx` | Cheapest with 500K+ context |
| `cheapest_1m_ctx` | Cheapest with 1M+ context |
| `best_under_1_dollar` | Best quality under $1/M input |
| `best_under_3_dollars` | Best quality under $3/M input |
| `best_deep_thinker` | Best deep reasoning model |
| `best_open_weight` | Best open-weight model |
| `cheapest_tools_search` | Cheapest with tools + search |
| `cheapest_tools_reason` | Cheapest with tools + reasoning |
| `best_for_agents` | Best for agentic workflows |
| `best_for_research` | Best for web research |
| `best_for_classification` | Cheapest with JSON output |
| `best_for_long_docs` | Best for long documents |
| `best_value` | Best quality-to-price ratio |
