#!/usr/bin/env python3
"""
Database migration script to add performance indexes for CORE-Supervisor pairing.

This script adds three indexes to optimize query performance:
1. idx_events_project_name - For LIKE queries matching CORE/Supervisor patterns
2. idx_events_project_ref_num - For event lookups by reference number
3. idx_schedule_event_ref_num - For schedule lookups by event reference

Sprint 2 - Calendar Redesign
Migration: add_indexes_for_core_supervisor_pairing
"""

import os
import sys
import sqlite3

def apply_index_migration():
    """Add performance indexes to events and schedule tables"""

    # Get database path
    basedir = os.path.dirname(__file__)
    db_path = os.path.join(basedir, 'scheduler.db')

    if not os.path.exists(db_path):
        print(f"ERROR: Database file not found at: {db_path}")
        return False

    print(f"Applying index migration to: {db_path}")
    print("=" * 70)

    try:
        # Connect to SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check existing indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        existing_indexes = [row[0] for row in cursor.fetchall()]

        print("\nExisting indexes:")
        for idx in existing_indexes:
            print(f"  - {idx}")

        print("\n" + "=" * 70)
        print("Creating new indexes...")
        print("=" * 70)

        indexes_created = 0

        # Index 1: events.project_name (for LIKE queries)
        if 'idx_events_project_name' not in existing_indexes:
            print("\n[1/3] Creating idx_events_project_name...")
            print("      Optimizes: Event.query.filter(Event.project_name.ilike('...'))")
            cursor.execute("""
                CREATE INDEX idx_events_project_name ON events(project_name)
            """)
            print("      [OK] Created successfully")
            indexes_created += 1
        else:
            print("\n[1/3] idx_events_project_name already exists - skipping")

        # Index 2: events.project_ref_num (for event lookups)
        if 'idx_events_project_ref_num' not in existing_indexes:
            print("\n[2/3] Creating idx_events_project_ref_num (UNIQUE)...")
            print("      Optimizes: Event.query.filter_by(project_ref_num=...)")
            cursor.execute("""
                CREATE UNIQUE INDEX idx_events_project_ref_num ON events(project_ref_num)
            """)
            print("      [OK] Created successfully")
            indexes_created += 1
        else:
            print("\n[2/3] idx_events_project_ref_num already exists - skipping")

        # Index 3: schedules.event_ref_num (for schedule lookups)
        if 'idx_schedules_event_ref_num' not in existing_indexes:
            print("\n[3/3] Creating idx_schedules_event_ref_num...")
            print("      Optimizes: Schedule.query.filter_by(event_ref_num=...)")
            cursor.execute("""
                CREATE INDEX idx_schedules_event_ref_num ON schedules(event_ref_num)
            """)
            print("      [OK] Created successfully")
            indexes_created += 1
        else:
            print("\n[3/3] idx_schedules_event_ref_num already exists - skipping")

        # Commit changes
        conn.commit()

        print("\n" + "=" * 70)
        print(f"Migration complete: {indexes_created} new index(es) created")
        print("=" * 70)

        # Verify indexes were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        all_indexes = [row[0] for row in cursor.fetchall()]

        print("\nAll indexes after migration:")
        for idx in sorted(all_indexes):
            if idx.startswith('idx_'):
                print(f"  [OK] {idx}")
            else:
                print(f"  - {idx}")

        # Get database stats
        cursor.execute("SELECT COUNT(*) FROM events")
        event_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM schedules")
        schedule_count = cursor.fetchone()[0]

        print(f"\nDatabase statistics:")
        print(f"  Events: {event_count}")
        print(f"  Schedules: {schedule_count}")

        # Estimate index sizes
        page_size = 4096  # SQLite default page size
        cursor.execute("PRAGMA page_count")
        total_pages = cursor.fetchone()[0]
        db_size_kb = (total_pages * page_size) / 1024

        print(f"  Database size: {db_size_kb:.1f} KB")
        print(f"  Estimated index overhead: ~{(event_count * 150 + schedule_count * 50) / 1024:.1f} KB")

        conn.close()

        print("\n" + "=" * 70)
        print("[OK] Migration completed successfully!")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Test reschedule/unschedule operations")
        print("2. Monitor query performance")
        print("3. Check application logs for improvements")

        return True

    except sqlite3.IntegrityError as e:
        print(f"\n[ERROR] ERROR: Integrity constraint violation: {e}")
        print("\nThis may indicate:")
        print("  - Duplicate values in project_ref_num (should be unique)")
        print("  - Run this query to check:")
        print("    SELECT project_ref_num, COUNT(*) FROM events GROUP BY project_ref_num HAVING COUNT(*) > 1")
        return False

    except Exception as e:
        print(f"\n[ERROR] ERROR during migration: {e}")
        import traceback
        traceback.print_exc()
        return False


def rollback_migration():
    """Remove indexes created by this migration"""

    basedir = os.path.dirname(__file__)
    db_path = os.path.join(basedir, 'scheduler.db')

    if not os.path.exists(db_path):
        print(f"ERROR: Database file not found at: {db_path}")
        return False

    print(f"Rolling back index migration from: {db_path}")
    print("=" * 70)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        indexes_to_remove = [
            'idx_events_project_name',
            'idx_events_project_ref_num',
            'idx_schedules_event_ref_num'
        ]

        indexes_removed = 0
        for index_name in indexes_to_remove:
            try:
                print(f"Dropping {index_name}...")
                cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
                print(f"  [OK] Dropped")
                indexes_removed += 1
            except Exception as e:
                print(f"  [WARNING]  Error: {e}")

        conn.commit()
        conn.close()

        print(f"\n[OK] Rollback complete: {indexes_removed} index(es) removed")
        return True

    except Exception as e:
        print(f"[ERROR] ERROR during rollback: {e}")
        return False


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Apply or rollback index migration')
    parser.add_argument('--rollback', action='store_true',
                       help='Rollback the migration (remove indexes)')

    args = parser.parse_args()

    if args.rollback:
        print("\nROLLBACK MODE")
        print("=" * 70)
        success = rollback_migration()
    else:
        print("\nAPPLYING MIGRATION")
        print("=" * 70)
        success = apply_index_migration()

    if success:
        sys.exit(0)
    else:
        print("\nMigration failed!")
        sys.exit(1)
