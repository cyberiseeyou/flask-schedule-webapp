"""
Event model and related database schema
Represents scheduled work/visits that need to be assigned to employees
"""
from datetime import datetime


def create_event_model(db):
    """Factory function to create Event model with db instance"""

    class Event(db.Model):
        """
        Event model representing work visits/tasks to be scheduled

        Events are imported from external systems and scheduled to employees.
        They have date constraints (start_datetime to due_datetime) and specific
        requirements (event_type) that determine which employees can work them.
        """
        __tablename__ = 'events'

        # Default durations (in minutes) for each event type
        DEFAULT_DURATIONS = {
            'Core': 390,        # 6.5 hours
            'Juicer': 540,      # 9 hours
            'Supervisor': 5,    # 5 minutes
            'Digitals': 15,     # 15 minutes
            'Freeosk': 5,       # 5 minutes
            'Other': 15         # 15 minutes
        }

        id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        project_name = db.Column(db.Text, nullable=False)
        project_ref_num = db.Column(db.Integer, nullable=False, unique=True)
        location_mvid = db.Column(db.Text)
        store_number = db.Column(db.Integer)
        store_name = db.Column(db.Text)
        start_datetime = db.Column(db.DateTime, nullable=False)
        due_datetime = db.Column(db.DateTime, nullable=False)
        estimated_time = db.Column(db.Integer)  # Duration in minutes
        is_scheduled = db.Column(db.Boolean, nullable=False, default=False)
        event_type = db.Column(db.String(20), nullable=False, default='Other')
        condition = db.Column(db.String(20), default='Unstaffed')

        # Sync fields for API integration
        external_id = db.Column(db.String(100), unique=True)
        last_synced = db.Column(db.DateTime)
        sync_status = db.Column(db.String(20), default='pending')

        # Sales tools document URL for Core events
        sales_tools_url = db.Column(db.Text)

        # Auto-scheduler: Link supervisor events to their corresponding core event
        parent_event_ref_num = db.Column(
            db.Integer,
            db.ForeignKey('events.project_ref_num'),
            nullable=True
        )

        def detect_event_type(self):
            """
            Automatically detect event type based on project name

            Event types determine which employees can be assigned:
            - Core: Standard events, all employees
            - Digitals: Digital displays, requires supervisor/lead
            - Juicer: Juice bar events, requires juicer barista
            - Supervisor: Requires supervisor/lead
            - Freeosk: Kiosk events, requires supervisor/lead
            - Other: Catch-all for unclassified events

            Returns:
                str: Detected event type
            """
            if not self.project_name:
                return 'Other'

            project_name_upper = self.project_name.upper()

            if 'CORE' in project_name_upper:
                return 'Core'
            elif 'DIGITAL' in project_name_upper:
                return 'Digitals'
            elif 'JUICER' in project_name_upper:
                return 'Juicer'
            elif 'SUPERVISOR' in project_name_upper:
                return 'Supervisor'
            elif 'FREEOSK' in project_name_upper:
                return 'Freeosk'
            else:
                return 'Other'

        @classmethod
        def get_default_duration(cls, event_type):
            """
            Get the default duration in minutes for a given event type

            Args:
                event_type (str): The event type

            Returns:
                int: Duration in minutes
            """
            return cls.DEFAULT_DURATIONS.get(event_type, 15)

        def set_default_duration(self):
            """
            Set the estimated_time field to the default duration for this event's type

            This should be called when creating new events or when event_type changes.
            Only sets the duration if estimated_time is not already set.
            """
            if not self.estimated_time:
                self.estimated_time = self.get_default_duration(self.event_type)

        def calculate_end_datetime(self, start_datetime):
            """
            Calculate the end datetime based on start datetime and estimated duration

            Args:
                start_datetime (datetime): The start datetime of the event

            Returns:
                datetime: The calculated end datetime
            """
            from datetime import timedelta
            duration_minutes = self.estimated_time or self.get_default_duration(self.event_type)
            return start_datetime + timedelta(minutes=duration_minutes)

        def __repr__(self):
            return f'<Event {self.project_ref_num}: {self.project_name}>'

    return Event
