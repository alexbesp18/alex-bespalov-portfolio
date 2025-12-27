#!/usr/bin/env python3
"""
Debug script for Supabase connection and archival.

Run with:
    SUPABASE_URL=your-url SUPABASE_SERVICE_KEY=your-key python debug_supabase.py

Or set the env vars in your shell first.
"""

import os
import sys
import logging
from datetime import date

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_env_vars():
    """Check if required environment variables are set."""
    print("\n" + "=" * 60)
    print("STEP 1: Environment Variables Check")
    print("=" * 60)

    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")

    print(f"SUPABASE_URL: {'✓ Set' if url else '✗ NOT SET'}")
    if url:
        print(f"  URL starts with: {url[:30]}...")

    print(f"SUPABASE_SERVICE_KEY: {'✓ Set' if key else '✗ NOT SET'}")
    if key:
        print(f"  Key length: {len(key)} chars")
        print(f"  Key starts with: {key[:20]}...")

    if not url or not key:
        print("\n❌ ERROR: Missing environment variables!")
        print("Set them with:")
        print("  export SUPABASE_URL='your-project-url'")
        print("  export SUPABASE_SERVICE_KEY='your-service-role-key'")
        return False

    return True


def check_supabase_import():
    """Check if supabase package is installed."""
    print("\n" + "=" * 60)
    print("STEP 2: Supabase Package Check")
    print("=" * 60)

    try:
        from supabase import create_client
        print("✓ supabase package is installed")
        return True
    except ImportError:
        print("✗ supabase package NOT installed")
        print("Install with: pip install supabase")
        return False


def test_connection():
    """Test basic Supabase connection."""
    print("\n" + "=" * 60)
    print("STEP 3: Connection Test")
    print("=" * 60)

    try:
        from supabase import create_client

        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_KEY")

        print("Creating Supabase client...")
        client = create_client(url, key)
        print("✓ Client created successfully")

        # Try to query the table
        print("\nQuerying daily_indicators table...")
        result = client.table("daily_indicators").select("*").limit(1).execute()

        print(f"✓ Query successful!")
        print(f"  Records returned: {len(result.data)}")

        if result.data:
            print(f"  Sample record keys: {list(result.data[0].keys())}")
            print(f"  Sample date: {result.data[0].get('date')}")
            print(f"  Sample symbol: {result.data[0].get('symbol')}")

        return True

    except Exception as e:
        print(f"✗ Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_insert():
    """Test inserting a test record."""
    print("\n" + "=" * 60)
    print("STEP 4: Insert Test (with TEST symbol)")
    print("=" * 60)

    try:
        from supabase import create_client

        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_KEY")

        client = create_client(url, key)

        test_record = {
            "date": date.today().isoformat(),
            "symbol": "DEBUG_TEST",
            "close": 123.45,
            "rsi": 50.0,
            "bullish_score": 5.0,
        }

        print(f"Upserting test record: {test_record}")

        response = client.table("daily_indicators").upsert(
            test_record, on_conflict="date,symbol"
        ).execute()

        print(f"✓ Upsert successful!")
        print(f"  Response data count: {len(response.data) if response.data else 0}")
        if response.data:
            print(f"  Inserted record: {response.data[0]}")

        # Verify the insert
        print("\nVerifying insert...")
        verify = client.table("daily_indicators").select("*").eq(
            "symbol", "DEBUG_TEST"
        ).eq("date", date.today().isoformat()).execute()

        if verify.data:
            print(f"✓ Verification successful - record exists in table")
            print(f"  Record: {verify.data[0]}")
        else:
            print("✗ Verification failed - record not found after insert!")

        # Clean up test record
        print("\nCleaning up test record...")
        client.table("daily_indicators").delete().eq(
            "symbol", "DEBUG_TEST"
        ).execute()
        print("✓ Test record deleted")

        return True

    except Exception as e:
        print(f"✗ Insert test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_archive_function():
    """Test the actual archive_daily_indicators function."""
    print("\n" + "=" * 60)
    print("STEP 5: archive_daily_indicators Function Test")
    print("=" * 60)

    try:
        # Add parent path for imports
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        from shared_core.archive import archive_daily_indicators

        test_data = [
            {
                'symbol': 'DEBUG_FUNC_TEST',
                'close': 100.0,
                'rsi': 45.0,
                'macd': 1.5,
                'bullish_score': 7.5,
            }
        ]

        print(f"Calling archive_daily_indicators with test data...")
        result = archive_daily_indicators(test_data, score_type="bullish")

        print(f"✓ Function returned: {result}")

        if result > 0:
            print("✓ Archive function working correctly!")

            # Clean up
            from supabase import create_client
            url = os.environ.get("SUPABASE_URL")
            key = os.environ.get("SUPABASE_SERVICE_KEY")
            client = create_client(url, key)
            client.table("daily_indicators").delete().eq(
                "symbol", "DEBUG_FUNC_TEST"
            ).execute()
            print("✓ Test record cleaned up")
        else:
            print("✗ Function returned 0 - check logs above for details")

        return result > 0

    except Exception as e:
        print(f"✗ Function test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_table_schema():
    """Check the table schema in Supabase."""
    print("\n" + "=" * 60)
    print("STEP 6: Table Schema Check")
    print("=" * 60)

    try:
        from supabase import create_client

        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_KEY")

        client = create_client(url, key)

        # Get a sample record to see columns
        result = client.table("daily_indicators").select("*").limit(1).execute()

        if result.data:
            columns = list(result.data[0].keys())
            print(f"✓ Table columns ({len(columns)}):")
            for col in sorted(columns):
                print(f"  - {col}")
        else:
            print("Table exists but is empty")
            print("Trying to get schema from empty insert...")

            # Try inserting minimal record to see what columns are required
            try:
                client.table("daily_indicators").insert({
                    "date": "1900-01-01",
                    "symbol": "SCHEMA_CHECK",
                    "close": 0
                }).execute()

                # If it worked, delete and report
                client.table("daily_indicators").delete().eq(
                    "symbol", "SCHEMA_CHECK"
                ).execute()
                print("✓ Minimal insert succeeded (date, symbol, close are required)")

            except Exception as e:
                print(f"Schema check via insert failed: {e}")

        return True

    except Exception as e:
        print(f"✗ Schema check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all debug checks."""
    print("\n" + "=" * 60)
    print("SUPABASE DEBUG SCRIPT")
    print("=" * 60)

    results = {}

    # Run all checks
    results['env_vars'] = check_env_vars()

    if results['env_vars']:
        results['import'] = check_supabase_import()

        if results['import']:
            results['connection'] = test_connection()

            if results['connection']:
                results['schema'] = check_table_schema()
                results['insert'] = test_insert()
                results['archive_function'] = test_archive_function()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for check, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {check}: {status}")

    all_passed = all(results.values())

    if all_passed:
        print("\n✓ All checks passed! Supabase integration is working.")
    else:
        print("\n✗ Some checks failed. Review the output above for details.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
