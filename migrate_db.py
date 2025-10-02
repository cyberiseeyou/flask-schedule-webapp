#!/usr/bin/env python3
"""
Database migration script to add event_type column to existing events table.
"""

import os
import sys
import sqlite3

# Add the scheduler_app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scheduler_app'))

from app import app, db, Event

def migrate_database():
    """Add event_type column to events table and populate with detected types"""
    
    # Get database path
    basedir = os.path.dirname(__file__)
    db_path = os.path.join(basedir, 'scheduler_app', 'instance', 'scheduler.db')
    
    if not os.path.exists(db_path):
        print("Database file not found. Creating new database...")
        with app.app_context():
            db.create_all()
        return True
    
    print(f"Migrating database at: {db_path}")
    
    try:
        # Connect directly to SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if event_type column already exists
        cursor.execute("PRAGMA table_info(events)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'event_type' in columns:
            print("event_type column already exists.")
        else:
            print("Adding event_type column...")
            # Add the event_type column with default value 'Other'
            cursor.execute("ALTER TABLE events ADD COLUMN event_type VARCHAR(20) DEFAULT 'Other'")
            conn.commit()
            print("event_type column added successfully.")
        
        # Now use Flask-SQLAlchemy to detect and update event types
        with app.app_context():
            print("Detecting and updating event types...")
            events = Event.query.all()
            updated_count = 0
            
            for event in events:
                detected_type = event.detect_event_type()
                if event.event_type != detected_type:
                    event.event_type = detected_type
                    updated_count += 1
                    print(f"Updated '{event.project_name[:50]}...' to '{detected_type}'")
            
            db.session.commit()
            print(f"Updated {updated_count} events with detected event types.")
            
            # Show summary
            print("\nEvent type summary:")
            type_counts = db.session.query(Event.event_type, db.func.count(Event.id)).group_by(Event.event_type).all()
            for event_type, count in type_counts:
                print(f"  {event_type}: {count} events")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error during migration: {e}")
        return False

if __name__ == '__main__':
    print("Starting database migration...")
    success = migrate_database()
    if success:
        print("Database migration completed successfully!")
    else:
        print("Database migration failed!")
        sys.exit(1)