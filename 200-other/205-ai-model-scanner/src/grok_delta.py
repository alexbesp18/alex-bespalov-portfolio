"""One Grok API call to find models released or repriced in the last 7 days."""

from __future__ import annotations

import json

import httpx

from src.config import XAI_API_KEY, XAI_RESPONSES_URL, XAI_MODEL, GROK_PROMPT


async def search_new_releases() -> list[dict]:
    """Single Grok search for new AI model releases/price changes.

    Returns list of dicts with model data, or empty list on any failure.
    This is non-fatal — the pipeline continues without Grok delta.
    """
    if not XAI_API_KEY:
        print("  [warn] No XAI_API_KEY set, skipping Grok delta search")
        return []

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                XAI_RESPONSES_URL,
                headers={
                    "Authorization": f"Bearer {XAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": XAI_MODEL,
                    "input": [
                        {"role": "system", "content": "Return only valid JSON. No markdown."},
                        {"role": "user", "content": GROK_PROMPT},
                    ],
                    "tools": [{"type": "web_search"}],
                    "temperature": 0.1,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        # Extract text content from response blocks
        text = _extract_text(data)
        if not text:
            print("  [warn] Grok returned empty response")
            return []

        parsed = _parse_json(text)
        updates = parsed.get("updates", [])

        # Tag each update
        for u in updates:
            u["source"] = "grok_search"
            u["is_new"] = True

        return updates

    except Exception as e:
        print(f"  [warn] Grok delta search failed: {e}")
        return []


def _extract_text(data: dict) -> str:
    """Extract text content from xAI Responses API output."""
    text_parts = []
    for block in data.get("output", []):
        if isinstance(block, dict):
            if block.get("type") == "message":
                for content in block.get("content", []):
                    if isinstance(content, dict) and content.get("type") == "output_text":
                        text_parts.append(content.get("text", ""))
            elif "text" in block:
                text_parts.append(block["text"])
    return "".join(text_parts)


def _parse_json(text: str) -> dict:
    """Parse JSON from text that may be wrapped in markdown code fences."""
    text = text.strip()

    # Strip markdown code fences
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json or ```)
        lines = lines[1:]
        # Remove last line if it's ```)
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in the text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass

        print(f"  [warn] Could not parse Grok JSON: {text[:200]}")
        return {"updates": []}
