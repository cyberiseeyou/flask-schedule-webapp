#!/usr/bin/env python3
"""
Database migration script to add sync-related columns
"""
from app import app, db
from sqlalchemy import text

def add_sync_columns():
    """Add sync-related columns to existing tables"""
    with app.app_context():
        try:
            # Add columns to employees table
            print("Adding sync columns to employees table...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE employees ADD COLUMN external_id TEXT;"))
                conn.execute(text("ALTER TABLE employees ADD COLUMN last_synced TIMESTAMP;"))
                conn.execute(text("ALTER TABLE employees ADD COLUMN sync_status TEXT DEFAULT 'pending';"))
                conn.commit()
            print("✓ Employee sync columns added")

            # Add columns to events table
            print("Adding sync columns to events table...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE events ADD COLUMN external_id TEXT;"))
                conn.execute(text("ALTER TABLE events ADD COLUMN last_synced TIMESTAMP;"))
                conn.execute(text("ALTER TABLE events ADD COLUMN sync_status TEXT DEFAULT 'pending';"))
                conn.commit()
            print("✓ Event sync columns added")

            # Add columns to schedules table
            print("Adding sync columns to schedules table...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE schedules ADD COLUMN external_id TEXT;"))
                conn.execute(text("ALTER TABLE schedules ADD COLUMN last_synced TIMESTAMP;"))
                conn.execute(text("ALTER TABLE schedules ADD COLUMN sync_status TEXT DEFAULT 'pending';"))
                conn.commit()
            print("✓ Schedule sync columns added")

            # Add sales_tools_url column to events table
            print("Adding sales_tools_url column to events table...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE events ADD COLUMN sales_tools_url TEXT;"))
                conn.commit()
            print("✓ Sales tools URL column added")

            print("Database migration completed successfully!")

        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("Columns already exist, skipping...")
            else:
                print(f"Error during migration: {e}")
                raise

if __name__ == '__main__':
    add_sync_columns()