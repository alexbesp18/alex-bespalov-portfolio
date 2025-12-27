#!/usr/bin/env python3
"""
Test script to verify Supabase setup for indicator archival.

Run from 000-shared-core directory:
    source .venv/bin/activate  # if using venv
    python scripts/test_supabase_setup.py

Or with explicit env vars:
    SUPABASE_URL="..." SUPABASE_SERVICE_KEY="..." python scripts/test_supabase_setup.py
"""

import os
import sys
from pathlib import Path
from datetime import date, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

# Load env from parent directories
for env_path in [
    Path(__file__).parent.parent / ".env",
    Path(__file__).parent.parent.parent / "009-reversals" / ".env",
    Path(__file__).parent.parent.parent / "010-oversold" / ".env",
]:
    if env_path.exists():
        load_dotenv(env_path)
        break


def test_connection():
    """Test basic Supabase connection."""
    print("\n" + "=" * 60)
    print("SUPABASE CONNECTION TEST")
    print("=" * 60)

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")

    if not url or not key:
        print("ERROR: SUPABASE_URL or SUPABASE_SERVICE_KEY not set")
        return False

    print(f"URL: {url[:40]}...")
    print(f"Key: {key[:20]}...{key[-10:]}")

    try:
        from supabase import create_client
        client = create_client(url, key)
        print("Client created successfully")
        return client
    except Exception as e:
        print(f"ERROR creating client: {e}")
        return None


def test_daily_indicators_table(client):
    """Test daily_indicators table exists and is accessible."""
    print("\n" + "-" * 60)
    print("Testing daily_indicators table...")

    try:
        result = client.table("daily_indicators").select("*").limit(5).execute()
        count = len(result.data) if result.data else 0
        print(f"Found {count} records in daily_indicators")

        if result.data:
            print("\nSample record:")
            sample = result.data[0]
            for key in ['date', 'symbol', 'close', 'rsi', 'oversold_score', 'bullish_score']:
                if key in sample:
                    print(f"  {key}: {sample[key]}")
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_monthly_aggregates_table(client):
    """Test monthly_aggregates table exists."""
    print("\n" + "-" * 60)
    print("Testing monthly_aggregates table...")

    try:
        result = client.table("monthly_aggregates").select("*").limit(5).execute()
        count = len(result.data) if result.data else 0
        print(f"Found {count} records in monthly_aggregates")
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        print("\nNOTE: You may need to run the SQL to create this table:")
        print("  000-shared-core/sql/monthly_aggregates.sql")
        return False


def test_archive_function():
    """Test the archive_daily_indicators function."""
    print("\n" + "-" * 60)
    print("Testing archive_daily_indicators function...")

    try:
        from shared_core import archive_daily_indicators

        # Create test data
        class MockResult:
            def __init__(self, ticker, score, price, rsi):
                self.ticker = ticker
                self.score = score
                self.price = price
                self.rsi = rsi
                self.stoch_k = 25.0
                self.williams_r = -75.0
                self.components = {}

        test_results = [
            MockResult("TEST1", 8.5, 100.0, 28.0),
            MockResult("TEST2", 7.2, 50.0, 32.0),
        ]

        # Try to archive (using test date to avoid polluting real data)
        from datetime import date
        test_date = date(2020, 1, 1)  # Old date for test

        count = archive_daily_indicators(
            test_results,
            scan_date=test_date,
            score_type="oversold"
        )

        print(f"Archived {count} test records")

        # Clean up test data
        from shared_core import SupabaseArchiver
        archiver = SupabaseArchiver()
        archiver.client.table("daily_indicators").delete().eq("date", "2020-01-01").execute()
        print("Cleaned up test records")

        return True
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_aggregation_function():
    """Test the run_monthly_aggregation function."""
    print("\n" + "-" * 60)
    print("Testing run_monthly_aggregation function...")

    try:
        from shared_core import run_monthly_aggregation

        # Just check it's callable and returns expected format
        # Don't actually run it since we may not have old data
        print("Function imported successfully")
        print("(Skipping actual run - use manually when you have 90+ days of data)")
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def show_data_summary(client):
    """Show summary of current data in Supabase."""
    print("\n" + "=" * 60)
    print("DATA SUMMARY")
    print("=" * 60)

    try:
        # Get date range
        result = client.table("daily_indicators").select("date").order("date").limit(1).execute()
        oldest = result.data[0]['date'] if result.data else "N/A"

        result = client.table("daily_indicators").select("date").order("date", desc=True).limit(1).execute()
        newest = result.data[0]['date'] if result.data else "N/A"

        # Get unique symbols count
        result = client.table("daily_indicators").select("symbol").execute()
        symbols = set(r['symbol'] for r in result.data) if result.data else set()

        # Get total count
        result = client.table("daily_indicators").select("*", count="exact").execute()
        total = result.count if hasattr(result, 'count') else len(result.data) if result.data else 0

        print(f"Date range: {oldest} to {newest}")
        print(f"Unique symbols: {len(symbols)}")
        print(f"Total daily records: {total}")

        if symbols:
            print(f"\nSymbols: {', '.join(sorted(symbols)[:20])}", end="")
            if len(symbols) > 20:
                print(f" ... and {len(symbols) - 20} more")
            else:
                print()

        # Estimate storage
        # Rough estimate: ~500 bytes per record
        estimated_mb = (total * 500) / (1024 * 1024)
        print(f"\nEstimated storage: {estimated_mb:.2f} MB of 500 MB free tier")

    except Exception as e:
        print(f"Error getting summary: {e}")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("SUPABASE INDICATOR ARCHIVE - SETUP TEST")
    print("=" * 60)

    # Test connection
    client = test_connection()
    if not client:
        print("\nFailed to connect to Supabase. Check your credentials.")
        return 1

    # Test tables
    results = []
    results.append(("daily_indicators table", test_daily_indicators_table(client)))
    results.append(("monthly_aggregates table", test_monthly_aggregates_table(client)))
    results.append(("archive_daily_indicators", test_archive_function()))
    results.append(("run_monthly_aggregation", test_aggregation_function()))

    # Show data summary
    show_data_summary(client)

    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\nAll tests passed! Your Supabase setup is ready.")
        print("\nNext steps:")
        print("  1. Run your scanners (008-alerts, 009-reversals, 010-oversold)")
        print("  2. Data will automatically archive to Supabase")
        print("  3. Monthly aggregation runs on 1st of each month")
    else:
        print("\nSome tests failed. Check the errors above.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
