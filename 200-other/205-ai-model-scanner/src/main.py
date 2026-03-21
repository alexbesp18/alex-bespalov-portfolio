"""AI Model Scanner — main orchestrator."""

from __future__ import annotations

import asyncio
import sys
from datetime import date, timedelta

from src import db
from src.config import RETENTION_DAYS
from src.models import AIModel
from src.tiers import assign_tier
from src import openrouter
from src import grok_delta
from src import recommender
from src import report


async def _run() -> None:
    today = date.today().isoformat()

    print("=" * 60)
    print(f"AI Model Scanner — {today}")
    print("=" * 60)

    # ── Step 1: Fetch data (parallel) ─────────────────────────────
    print("\n[1/6] Fetching models...")

    or_models, grok_updates = await asyncio.gather(
        openrouter.fetch_all_models(today),
        grok_delta.search_new_releases(),
    )

    print(f"  OpenRouter: {len(or_models)} models")
    print(f"  Grok delta: {len(grok_updates)} updates")

    # ── Step 2: Merge + deduplicate ───────────────────────────────
    print("\n[2/6] Merging and assigning tiers...")

    all_models = _merge(or_models, grok_updates, today)
    print(f"  Total after merge: {len(all_models)} models")

    # ── Step 3: Upsert to Supabase ────────────────────────────────
    print("\n[3/6] Upserting to Supabase...")

    try:
        # Delete today's old data first (ensures stale/filtered models don't persist)
        db.models().delete().eq("scan_date", today).execute()
        model_dicts = [m.to_dict() for m in all_models]
        # Batch insert in chunks of 500 to avoid payload limits
        for i in range(0, len(model_dicts), 500):
            chunk = model_dicts[i:i + 500]
            db.models().insert(chunk).execute()
        print(f"  Inserted {len(model_dicts)} model rows")
    except Exception as e:
        print(f"  [FATAL] Supabase upsert failed: {e}")
        sys.exit(1)

    # ── Step 4: Compute picks ─────────────────────────────────────
    print("\n[4/6] Computing 20 recommendations...")

    picks = recommender.compute_picks(today, all_models)
    print(f"  Generated {len(picks)} picks")

    # Delete old picks for today, then insert new
    try:
        db.picks().delete().eq("scan_date", today).execute()
        pick_dicts = [p.to_dict() for p in picks]
        db.picks().insert(pick_dicts).execute()
        print(f"  Inserted {len(picks)} picks to Supabase")
    except Exception as e:
        print(f"  [FATAL] Picks insert failed: {e}")
        sys.exit(1)

    # ── Step 5: Generate reports ──────────────────────────────────
    print("\n[5/6] Generating reports...")

    try:
        report.write_markdown(today, all_models, picks)
        report.write_claude_md_snippet()
    except Exception as e:
        print(f"  [warn] Report generation failed: {e}")

    # ── Step 6: Prune old data ────────────────────────────────────
    print("\n[6/6] Pruning data older than {0} days...".format(RETENTION_DAYS))

    try:
        cutoff = (date.today() - timedelta(days=RETENTION_DAYS)).isoformat()
        r1 = db.models().delete().lt("scan_date", cutoff).execute()
        r2 = db.picks().delete().lt("scan_date", cutoff).execute()
        pruned = len(r1.data) + len(r2.data)
        if pruned > 0:
            print(f"  Pruned {pruned} old rows")
        else:
            print("  Nothing to prune")
    except Exception as e:
        print(f"  [warn] Prune failed: {e}")

    # ── Summary ───────────────────────────────────────────────────
    by_tier = {}
    for m in all_models:
        by_tier[m.tier] = by_tier.get(m.tier, 0) + 1
    new_count = sum(1 for m in all_models if m.is_new)

    print("\n" + "=" * 60)
    print(f"Done. {len(all_models)} models ({by_tier.get('fast', 0)} fast, "
          f"{by_tier.get('flagship', 0)} flagship, {by_tier.get('deep', 0)} deep)")
    print(f"New: {new_count} | Picks: {len(picks)}")
    print("=" * 60)


def _merge(or_models: list[AIModel], grok_updates: list[dict], scan_date: str) -> list[AIModel]:
    """Merge OpenRouter models with Grok delta updates.

    - If Grok reports a model that exists in OpenRouter: keep OpenRouter data (more reliable pricing)
    - If Grok reports a model NOT in OpenRouter: add it with source="grok_search"
    """
    # Index OpenRouter models by model_id for dedup
    or_index: dict[str, AIModel] = {}
    for m in or_models:
        or_index[m.model_id.lower()] = m

    merged = list(or_models)

    for update in grok_updates:
        model_id = update.get("model_id", "").lower()
        if not model_id:
            continue

        if model_id in or_index:
            # Model exists in OpenRouter — skip (OpenRouter pricing is more reliable)
            continue

        # New model from Grok — add it
        provider = update.get("provider", "unknown").lower()
        input_price = float(update.get("input_price_per_1m", 0) or 0)
        output_price = float(update.get("output_price_per_1m", 0) or 0)
        has_reasoning = bool(update.get("has_reasoning", False))

        tier = assign_tier(model_id, provider, input_price, has_reasoning)

        merged.append(AIModel(
            scan_date=scan_date,
            provider=provider,
            model_id=update.get("model_id", model_id),
            model_name=update.get("model_name", model_id),
            tier=tier,
            input_price=round(input_price, 4),
            output_price=round(output_price, 4),
            context_window=update.get("context_window"),
            has_tools=bool(update.get("has_tools", False)),
            has_vision=bool(update.get("has_vision", False)),
            has_reasoning=has_reasoning,
            has_web_search=bool(update.get("has_web_search", False)),
            has_json_output=bool(update.get("has_json_output", False)),
            is_open_weight=False,
            is_openai_compat=True,
            source="grok_search",
            is_new=True,
        ))

    return merged


def main():
    asyncio.run(_run())


if __name__ == "__main__":
    main()
