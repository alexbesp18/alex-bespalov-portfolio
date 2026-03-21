#!/usr/bin/env python3
"""
Cron Setup Script for AA Points Arbitrage Monitor.

Generates and optionally installs crontab entries for automated scraping.

Usage:
    python scripts/setup_cron.py           # Show crontab entries
    python scripts/setup_cron.py --install # Install to user crontab
    python scripts/setup_cron.py --remove  # Remove from user crontab
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Get paths
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
VENV_PYTHON = PROJECT_ROOT / "venv" / "bin" / "python"
LOG_DIR = PROJECT_ROOT / "logs"

# Cron marker for identifying our entries
CRON_MARKER = "# AA-SCRAPER-MANAGED"

def get_cron_entries() -> str:
    """Generate crontab entries for the scraper."""

    # Ensure log directory exists
    LOG_DIR.mkdir(exist_ok=True)

    entries = f"""
{CRON_MARKER}-START
# AA Points Arbitrage Monitor - Automated Scraping
# Installed by: python scripts/setup_cron.py --install
# Remove with:  python scripts/setup_cron.py --remove

# Environment
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin

# SimplyMiles API - every 2 hours (offers change frequently)
0 */2 * * * cd {PROJECT_ROOT} && {VENV_PYTHON} scrapers/simplymiles_api.py >> {LOG_DIR}/simplymiles.log 2>&1

# Portal scraper - every 4 hours (rates more stable)
30 */4 * * * cd {PROJECT_ROOT} && {VENV_PYTHON} scrapers/portal.py >> {LOG_DIR}/portal.log 2>&1

# Hotels scraper - every 6 hours (availability changes slowly)
0 */6 * * * cd {PROJECT_ROOT} && {VENV_PYTHON} scrapers/hotels.py >> {LOG_DIR}/hotels.log 2>&1

# Stack detection - 15 min after scrapers (every 2 hours)
15 */2 * * * cd {PROJECT_ROOT} && {VENV_PYTHON} -c "from core.stack_detector import detect_stacked_opportunities; detect_stacked_opportunities()" >> {LOG_DIR}/stack_detector.log 2>&1

# Alert check - 20 min after stack detection (every 2 hours)
20 */2 * * * cd {PROJECT_ROOT} && {VENV_PYTHON} scripts/check_alerts.py >> {LOG_DIR}/alerts.log 2>&1

# Daily digest - 8am Central time
0 8 * * * cd {PROJECT_ROOT} && {VENV_PYTHON} scripts/send_digest.py >> {LOG_DIR}/digest.log 2>&1

# Hotel matrix verification - weekly on Sunday at 3am
0 3 * * 0 cd {PROJECT_ROOT} && {VENV_PYTHON} scripts/hotel_discovery.py --verify >> {LOG_DIR}/hotel_verify.log 2>&1

# Log rotation - daily at midnight (keep 7 days)
0 0 * * * find {LOG_DIR} -name "*.log" -mtime +7 -delete 2>/dev/null

{CRON_MARKER}-END
"""
    return entries.strip()


def get_current_crontab() -> str:
    """Get current user crontab."""
    try:
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True
        )
        return result.stdout if result.returncode == 0 else ""
    except Exception:
        return ""


def install_cron():
    """Install cron entries to user crontab."""
    current = get_current_crontab()
    new_entries = get_cron_entries()

    # Remove any existing entries first
    lines = current.split("\n")
    filtered = []
    in_managed_block = False

    for line in lines:
        if f"{CRON_MARKER}-START" in line:
            in_managed_block = True
            continue
        if f"{CRON_MARKER}-END" in line:
            in_managed_block = False
            continue
        if not in_managed_block:
            filtered.append(line)

    # Add new entries
    new_crontab = "\n".join(filtered).strip()
    if new_crontab:
        new_crontab += "\n\n"
    new_crontab += new_entries + "\n"

    # Install
    process = subprocess.Popen(
        ["crontab", "-"],
        stdin=subprocess.PIPE,
        text=True
    )
    process.communicate(input=new_crontab)

    if process.returncode == 0:
        print("✅ Cron entries installed successfully!")
        print(f"\n📁 Logs will be written to: {LOG_DIR}/")
        print("\n📋 Installed schedule:")
        print("   • SimplyMiles: Every 2 hours")
        print("   • Portal: Every 4 hours")
        print("   • Hotels: Every 6 hours")
        print("   • Stack detection: Every 2 hours (15 min offset)")
        print("   • Alerts check: Every 2 hours (20 min offset)")
        print("   • Daily digest: 8am")
        print("   • Matrix verification: Sunday 3am")
        print("\n💡 View current crontab with: crontab -l")
    else:
        print("❌ Failed to install cron entries")
        sys.exit(1)


def remove_cron():
    """Remove our cron entries from user crontab."""
    current = get_current_crontab()

    if CRON_MARKER not in current:
        print("ℹ️  No AA-SCRAPER entries found in crontab")
        return

    # Filter out our entries
    lines = current.split("\n")
    filtered = []
    in_managed_block = False

    for line in lines:
        if f"{CRON_MARKER}-START" in line:
            in_managed_block = True
            continue
        if f"{CRON_MARKER}-END" in line:
            in_managed_block = False
            continue
        if not in_managed_block:
            filtered.append(line)

    new_crontab = "\n".join(filtered).strip() + "\n"

    # Install cleaned crontab
    process = subprocess.Popen(
        ["crontab", "-"],
        stdin=subprocess.PIPE,
        text=True
    )
    process.communicate(input=new_crontab)

    if process.returncode == 0:
        print("✅ AA-SCRAPER cron entries removed")
    else:
        print("❌ Failed to remove cron entries")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Manage cron jobs for AA Points Arbitrage Monitor"
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="Install cron entries to user crontab"
    )
    parser.add_argument(
        "--remove",
        action="store_true",
        help="Remove cron entries from user crontab"
    )

    args = parser.parse_args()

    if args.install:
        install_cron()
    elif args.remove:
        remove_cron()
    else:
        # Just show what would be installed
        print("📋 Cron entries for AA Points Arbitrage Monitor:\n")
        print(get_cron_entries())
        print("\n" + "="*60)
        print("To install: python scripts/setup_cron.py --install")
        print("To remove:  python scripts/setup_cron.py --remove")


if __name__ == "__main__":
    main()
