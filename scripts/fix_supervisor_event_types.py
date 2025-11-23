"""
Script to fix event_type for supervisor events that were incorrectly classified as 'Other'
"""
from app import app
from flask import current_app

def fix_supervisor_event_types():
    """Update event_type for supervisor events"""
    with app.app_context():
        db = current_app.extensions['sqlalchemy']
        Event = current_app.config['Event']

        # Find all "Other" type events that should be "Supervisor"
        other_events = Event.query.filter(Event.event_type == 'Other').all()

        updated_count = 0
        for event in other_events:
            if not event.project_name:
                continue

            project_name_upper = event.project_name.upper()

            # Check if this should be a Supervisor event
            if ('V2-SUPER' in project_name_upper or
                'SUPERVISO' in project_name_upper or
                'SUPERVISOR' in project_name_upper):

                print(f"Updating event {event.id}: {event.project_name}")
                print(f"  Old type: {event.event_type}")
                event.event_type = 'Supervisor'
                print(f"  New type: {event.event_type}\n")
                updated_count += 1

        if updated_count > 0:
            db.session.commit()
            print(f"\nSuccessfully updated {updated_count} events to Supervisor type")
        else:
            print("No events needed to be updated")

if __name__ == '__main__':
    fix_supervisor_event_types()
