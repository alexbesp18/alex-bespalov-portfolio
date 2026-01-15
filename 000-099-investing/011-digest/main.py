#!/usr/bin/env python3
"""
Daily Digest Runner.

Consolidates results from 008-alerts, 009-reversals, and 010-oversold
into a single daily digest email.

Run after all scanners complete in GitHub Actions.

Usage:
    python main.py                  # Send digest email
    python main.py --dry-run        # Preview without sending
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add shared-core to path
sys.path.insert(0, str(Path(__file__).parent.parent / "000-shared-core" / "src"))

from shared_core import setup_logging
from shared_core.notifications import DigestFormatter, ResendEmailClient, EmailConfig

logger = setup_logging("DIGEST")


def load_json_file(path: Path) -> Dict[str, Any]:
    """Load JSON file if exists, return empty dict otherwise."""
    if not path.exists():
        logger.warning(f"State file not found: {path}")
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load {path}: {e}")
        return {}


def load_alerts_results(base_dir: Path) -> List[Dict[str, Any]]:
    """Load results from 008-alerts state file."""
    state_path = base_dir / "008-alerts" / "state" / "last_run.json"
    state = load_json_file(state_path)
    signals = state.get("signals", {})
    # Handle both dict (portfolio + watchlist) and list formats
    if isinstance(signals, dict):
        return signals.get("portfolio", []) + signals.get("watchlist", [])
    return signals if isinstance(signals, list) else []


def load_reversals_results(base_dir: Path) -> List[Dict[str, Any]]:
    """Load results from 009-reversals state file."""
    state_path = base_dir / "009-reversals" / "data" / "state.json"
    state = load_json_file(state_path)

    # Extract results from last_digest if available
    last_digest = state.get("last_digest", {})
    return last_digest.get("results", [])


def load_oversold_results(base_dir: Path) -> List[Dict[str, Any]]:
    """Load results from 010-oversold state file."""
    state_path = base_dir / "010-oversold" / "data" / "last_run.json"
    state = load_json_file(state_path)
    return state.get("results", [])


def main():
    parser = argparse.ArgumentParser(description="Send consolidated daily digest email")
    parser.add_argument("--dry-run", action="store_true", help="Preview without sending")
    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent
    logger.info(f"Loading scanner results from {base_dir}")

    # Load results from each scanner
    alerts_data = load_alerts_results(base_dir)
    reversals_data = load_reversals_results(base_dir)
    oversold_data = load_oversold_results(base_dir)

    logger.info(
        f"Loaded: {len(alerts_data)} alerts, "
        f"{len(reversals_data)} reversals, "
        f"{len(oversold_data)} oversold"
    )

    # Check if any signals exist
    total_signals = len(alerts_data) + len(reversals_data) + len(oversold_data)

    if total_signals == 0:
        logger.info("No signals from any scanner. Skipping digest.")
        return

    # Format digest
    formatter = DigestFormatter()
    html_body = formatter.format_digest(
        alerts_data=alerts_data,
        reversals_data=reversals_data,
        oversold_data=oversold_data,
    )

    subject = formatter.format_subject(
        alerts_count=len(alerts_data),
        reversals_count=len(reversals_data),
        oversold_count=len(oversold_data),
    )

    if args.dry_run:
        logger.info("=== DRY RUN - Email Preview ===")
        logger.info(f"Subject: {subject}")
        logger.info(f"Body length: {len(html_body)} chars")
        print("\n" + "=" * 60)
        print(f"Subject: {subject}")
        print("=" * 60)
        # Print a text summary instead of full HTML
        print(f"\nSummary:")
        print(f"  - {len(alerts_data)} trading signals")
        print(f"  - {len(reversals_data)} reversal candidates")
        print(f"  - {len(oversold_data)} oversold opportunities")
        return

    # Send email
    api_key = os.environ.get("RESEND_API_KEY")
    from_email = os.environ.get("SENDER_EMAIL")
    to_emails = os.environ.get("NOTIFICATION_EMAILS", "").split(",")
    to_emails = [e.strip() for e in to_emails if e.strip()]

    if not api_key or not from_email or not to_emails:
        logger.error("Missing email configuration. Set RESEND_API_KEY, SENDER_EMAIL, NOTIFICATION_EMAILS")
        sys.exit(1)

    config = EmailConfig(
        api_key=api_key,
        from_address=from_email,
        to_addresses=to_emails,
    )
    client = ResendEmailClient(config)

    try:
        client.send(subject=subject, html=html_body)
        logger.info(f"Digest sent successfully: {subject}")
    except Exception as e:
        logger.error(f"Failed to send digest: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
