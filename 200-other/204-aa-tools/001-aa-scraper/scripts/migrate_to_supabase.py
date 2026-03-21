#!/usr/bin/env python3
"""
Migrate data from SQLite to Supabase.

This script transfers all existing data from the local SQLite database
to the cloud Supabase PostgreSQL database.

Usage:
    python scripts/migrate_to_supabase.py          # Migrate all tables
    python scripts/migrate_to_supabase.py --test   # Dry run (no writes)
    python scripts/migrate_to_supabase.py --table simplymiles_offers  # Migrate single table
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import get_settings
from core.database import get_database
from core.supabase_db import get_supabase_database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Tables to migrate in order (respecting foreign key constraints)
MIGRATION_TABLES = [
    'simplymiles_offers',
    'portal_rates',
    'hotel_deals',
    'stacked_opportunities',
    'alert_history',
    'scraper_health',
    'hotel_yield_matrix',
]


def get_sqlite_data(table_name: str) -> List[Dict[str, Any]]:
    """Fetch all data from a SQLite table."""
    db = get_database()

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]

        # Convert to list of dicts
        data = []
        for row in rows:
            row_dict = dict(zip(columns, row))
            # Remove SQLite auto-increment id (Supabase uses UUID)
            if 'id' in row_dict:
                del row_dict['id']
            data.append(row_dict)

        return data


def migrate_table(table_name: str, test_mode: bool = False) -> Dict[str, Any]:
    """
    Migrate a single table from SQLite to Supabase.

    Returns:
        Dict with migration status and counts
    """
    result = {
        'table': table_name,
        'status': 'unknown',
        'source_count': 0,
        'migrated_count': 0,
        'errors': []
    }

    try:
        # Fetch from SQLite
        data = get_sqlite_data(table_name)
        result['source_count'] = len(data)

        if not data:
            result['status'] = 'skipped'
            logger.info(f"{table_name}: No data to migrate")
            return result

        logger.info(f"{table_name}: Found {len(data)} rows to migrate")

        if test_mode:
            result['status'] = 'test_success'
            result['migrated_count'] = len(data)
            logger.info(f"{table_name}: [TEST MODE] Would migrate {len(data)} rows")
            return result

        # Insert into Supabase
        supabase_db = get_supabase_database()

        # Batch insert for efficiency
        batch_size = 100
        migrated = 0

        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]

            try:
                supabase_db.client.table(table_name).insert(batch).execute()
                migrated += len(batch)
                logger.debug(f"{table_name}: Migrated batch {i//batch_size + 1}")
            except Exception as e:
                error_msg = f"Batch {i//batch_size + 1}: {str(e)}"
                result['errors'].append(error_msg)
                logger.warning(f"{table_name}: {error_msg}")

        result['migrated_count'] = migrated
        result['status'] = 'success' if migrated == len(data) else 'partial'

        logger.info(f"{table_name}: Migrated {migrated}/{len(data)} rows")

    except Exception as e:
        result['status'] = 'error'
        result['errors'].append(str(e))
        logger.error(f"{table_name}: Migration failed - {e}")

    return result


def verify_migration(table_name: str) -> Dict[str, Any]:
    """Verify row counts match between SQLite and Supabase."""
    sqlite_db = get_database()
    supabase_db = get_supabase_database()

    with sqlite_db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        sqlite_count = cursor.fetchone()[0]

    result = supabase_db.client.table(table_name).select('*', count='exact').execute()
    supabase_count = result.count

    return {
        'table': table_name,
        'sqlite_count': sqlite_count,
        'supabase_count': supabase_count,
        'match': sqlite_count == supabase_count
    }


def run_migration(
    tables: List[str] = None,
    test_mode: bool = False,
    verify: bool = True
) -> Dict[str, Any]:
    """
    Run the full migration.

    Args:
        tables: Specific tables to migrate (None = all)
        test_mode: If True, don't actually write to Supabase
        verify: If True, verify row counts after migration

    Returns:
        Dict with overall migration results
    """
    settings = get_settings()

    if not settings.supabase_url or not settings.supabase_key:
        logger.error("SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return {'status': 'error', 'message': 'Missing Supabase credentials'}

    tables_to_migrate = tables or MIGRATION_TABLES

    results = {
        'status': 'unknown',
        'started_at': datetime.now().isoformat(),
        'tables': [],
        'verification': [],
        'summary': {
            'total_tables': len(tables_to_migrate),
            'successful': 0,
            'failed': 0,
            'total_rows': 0
        }
    }

    logger.info(f"Starting migration of {len(tables_to_migrate)} tables...")
    logger.info(f"Test mode: {test_mode}")

    for table in tables_to_migrate:
        table_result = migrate_table(table, test_mode)
        results['tables'].append(table_result)

        if table_result['status'] in ['success', 'test_success', 'skipped']:
            results['summary']['successful'] += 1
        else:
            results['summary']['failed'] += 1

        results['summary']['total_rows'] += table_result['migrated_count']

    # Verify if not test mode
    if verify and not test_mode:
        logger.info("Verifying migration...")
        for table in tables_to_migrate:
            try:
                verify_result = verify_migration(table)
                results['verification'].append(verify_result)
            except Exception as e:
                results['verification'].append({
                    'table': table,
                    'error': str(e)
                })

    # Overall status
    if results['summary']['failed'] == 0:
        results['status'] = 'success'
    elif results['summary']['successful'] > 0:
        results['status'] = 'partial'
    else:
        results['status'] = 'failed'

    results['completed_at'] = datetime.now().isoformat()

    return results


def print_results(results: Dict[str, Any]):
    """Pretty print migration results."""
    print("\n" + "=" * 60)
    print("MIGRATION RESULTS")
    print("=" * 60)

    print(f"\nStatus: {results['status'].upper()}")
    print(f"Started: {results['started_at']}")
    print(f"Completed: {results.get('completed_at', 'N/A')}")

    print(f"\nSummary:")
    print(f"  Tables: {results['summary']['total_tables']}")
    print(f"  Successful: {results['summary']['successful']}")
    print(f"  Failed: {results['summary']['failed']}")
    print(f"  Total rows: {results['summary']['total_rows']}")

    print("\nTable Details:")
    for table in results['tables']:
        status_icon = {
            'success': '+',
            'test_success': '~',
            'partial': '!',
            'error': 'X',
            'skipped': '-'
        }.get(table['status'], '?')

        print(f"  [{status_icon}] {table['table']}: "
              f"{table['migrated_count']}/{table['source_count']} rows")

        if table['errors']:
            for error in table['errors'][:3]:
                print(f"      Error: {error}")

    if results.get('verification'):
        print("\nVerification:")
        all_match = True
        for v in results['verification']:
            if 'error' in v:
                print(f"  [?] {v['table']}: {v['error']}")
                all_match = False
            else:
                match_icon = '+' if v['match'] else 'X'
                print(f"  [{match_icon}] {v['table']}: "
                      f"SQLite={v['sqlite_count']}, Supabase={v['supabase_count']}")
                if not v['match']:
                    all_match = False

        if all_match:
            print("\n  All tables verified successfully!")

    print("=" * 60 + "\n")


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(description="Migrate SQLite to Supabase")
    parser.add_argument("--test", action="store_true", help="Test mode (no writes)")
    parser.add_argument("--table", type=str, help="Migrate specific table only")
    parser.add_argument("--no-verify", action="store_true", help="Skip verification")
    args = parser.parse_args()

    tables = [args.table] if args.table else None

    results = run_migration(
        tables=tables,
        test_mode=args.test,
        verify=not args.no_verify
    )

    print_results(results)

    if results['status'] == 'failed':
        sys.exit(1)


if __name__ == "__main__":
    main()
