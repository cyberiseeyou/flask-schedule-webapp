#!/usr/bin/env python3
"""
Script to update existing events with their detected event types.
Run this after adding the event_type column to migrate existing data.
"""

import os
import sys

# Add the scheduler_app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scheduler_app'))

from app import app, db, Event

def update_event_types():
    """Update all existing events with their detected event types"""
    with app.app_context():
        # Get all events
        events = Event.query.all()
        updated_count = 0
        
        print(f"Found {len(events)} events to process...")
        
        for event in events:
            # Detect the event type
            detected_type = event.detect_event_type()
            
            # Update if different from current (or if current is empty/None)
            if event.event_type != detected_type:
                old_type = event.event_type or 'None'
                event.event_type = detected_type
                updated_count += 1
                print(f"Updated event '{event.project_name[:50]}...' from '{old_type}' to '{detected_type}'")
        
        # Commit changes
        try:
            db.session.commit()
            print(f"\nSuccessfully updated {updated_count} events!")
            
            # Show summary by event type
            print("\nEvent type summary:")
            type_counts = db.session.query(Event.event_type, db.func.count(Event.id)).group_by(Event.event_type).all()
            for event_type, count in type_counts:
                print(f"  {event_type}: {count} events")
                
        except Exception as e:
            db.session.rollback()
            print(f"Error updating events: {e}")
            return False
        
        return True

if __name__ == '__main__':
    print("Updating event types for existing events...")
    success = update_event_types()
    if success:
        print("Event type update completed successfully!")
    else:
        print("Event type update failed!")
        sys.exit(1)