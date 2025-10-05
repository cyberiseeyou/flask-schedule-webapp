"""
Database Models for EDR Downloader Application.

This module defines SQLAlchemy database models for the EDR Downloader application.
The models represent the core entities in the scheduling system:
    - Events: Work assignments at retail locations
    - Schedules: Assignment of events to employees with specific dates/times
    - Employees: Staff members who perform the work

These models are shared with the main scheduler application and provide read access
to event and employee data for EDR report generation.

Database:
    SQLite database located at: instance/scheduler.db

Author: Schedule Management System
Version: 1.0
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize SQLAlchemy instance
# This will be initialized with the Flask app in app.py using db.init_app(app)
db = SQLAlchemy()


class Event(db.Model):
    """
    Event model representing scheduled work assignments at retail locations.

    Events are work visits to be performed at specific store locations, typically
    involving product demonstrations, sampling, or other promotional activities.
    Each event has a reference number from the external system and can be scheduled
    to multiple employees across different dates.

    Attributes:
        id (int): Auto-incrementing primary key
        project_name (str): Descriptive name of the event/project
        project_ref_num (int): Unique reference number from external system
        location_mvid (str): Multi-view ID for the store location
        store_number (int): Walmart store number
        store_name (str): Name/description of the store
        start_datetime (datetime): Earliest date/time the event can be performed
        due_datetime (datetime): Latest date/time the event must be completed
        estimated_time (int): Estimated duration in minutes
        is_scheduled (bool): Whether the event has been assigned to an employee
        event_type (str): Type/category of event (e.g., 'Core', 'Demo', 'Other')
        external_id (str): Optional ID from external system for sync
        last_synced (datetime): Last time data was synchronized with external system
        sync_status (str): Current sync status ('pending', 'synced', 'error')
        sales_tools_url (str): URL to sales tools documentation for this event

    Relationships:
        schedules: List of Schedule objects associating this event with employees

    Example:
        # Query all CORE events scheduled for a specific date
        core_events = Event.query.join(Schedule).filter(
            Event.event_type == 'Core',
            db.func.date(Schedule.schedule_datetime) == target_date
        ).all()
    """
    __tablename__ = 'events'

    # Primary identifier
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Event details
    project_name = db.Column(db.Text, nullable=False)  # Full event name/description
    project_ref_num = db.Column(db.Integer, nullable=False, unique=True)  # Unique reference number

    # Location information
    location_mvid = db.Column(db.Text)  # Multi-view ID for location
    store_number = db.Column(db.Integer)  # Walmart store number
    store_name = db.Column(db.Text)  # Store name and address

    # Scheduling constraints
    start_datetime = db.Column(db.DateTime, nullable=False)  # Earliest start time
    due_datetime = db.Column(db.DateTime, nullable=False)  # Must complete by this time
    estimated_time = db.Column(db.Integer)  # Estimated duration in minutes

    # Status flags
    is_scheduled = db.Column(db.Boolean, nullable=False, default=False)  # Has been assigned?
    event_type = db.Column(db.String(20), default='Other')  # Event category (Core, Demo, etc.)

    # External system synchronization fields
    external_id = db.Column(db.Text)  # ID in external scheduling system
    last_synced = db.Column(db.DateTime)  # Timestamp of last sync operation
    sync_status = db.Column(db.Text, default='pending')  # Sync state: pending/synced/error

    # Supporting documentation
    sales_tools_url = db.Column(db.Text)  # URL to sales tools/instructions document

    def __repr__(self):
        """String representation for debugging and logging."""
        return f'<Event {self.project_ref_num}: {self.project_name}>'


class Schedule(db.Model):
    """
    Schedule model representing the assignment of events to employees.

    A schedule is the many-to-many relationship between Events and Employees,
    with an additional schedule_datetime field indicating when the employee
    is scheduled to perform the event. Multiple schedules can exist for the
    same event (different employees or different dates).

    Attributes:
        id (int): Auto-incrementing primary key
        event_ref_num (int): Foreign key to events.project_ref_num
        employee_id (str): Foreign key to employees.id
        schedule_datetime (datetime): Date and time when employee is scheduled
        external_id (str): Optional ID from external system for sync
        last_synced (datetime): Last time data was synchronized
        sync_status (str): Current sync status ('pending', 'synced', 'error')

    Relationships:
        event: Reference to the Event object being scheduled

    Example:
        # Get all schedules for a specific date
        schedules = Schedule.query.filter(
            db.func.date(Schedule.schedule_datetime) == target_date
        ).all()

        # Get employee name for a schedule
        schedule = Schedule.query.get(schedule_id)
        employee = Employee.query.get(schedule.employee_id)
        print(f"{employee.name} scheduled for {schedule.event.project_name}")
    """
    __tablename__ = 'schedules'

    # Primary identifier
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign keys establishing the event-employee relationship
    event_ref_num = db.Column(db.Integer, db.ForeignKey('events.project_ref_num'), nullable=False)
    employee_id = db.Column(db.String(50), nullable=False)  # References employees.id

    # Scheduled date and time
    schedule_datetime = db.Column(db.DateTime, nullable=False)

    # External system synchronization fields
    external_id = db.Column(db.Text)  # ID in external scheduling system
    last_synced = db.Column(db.DateTime)  # Timestamp of last sync operation
    sync_status = db.Column(db.Text, default='pending')  # Sync state: pending/synced/error

    # Relationship to Event model
    # Creates a 'schedules' backref on Event model to access all schedules for an event
    event = db.relationship('Event', backref='schedules', foreign_keys=[event_ref_num])

    def __repr__(self):
        """String representation for debugging and logging."""
        return f'<Schedule {self.id}: Event {self.event_ref_num} on {self.schedule_datetime}>'


class Employee(db.Model):
    """
    Employee model representing staff members who perform scheduled work.

    Employees are the people who perform the events at store locations. Each employee
    has qualifications, contact information, and status flags that determine their
    availability for different types of events.

    Attributes:
        id (str): Unique employee identifier (primary key, from external system)
        name (str): Full name of the employee
        email (str): Email address (unique, optional)
        phone (str): Phone number for contact
        is_active (bool): Whether the employee is currently active/available
        is_supervisor (bool): Whether the employee has supervisor privileges
        job_title (str): Job title/role of the employee
        adult_beverage_trained (bool): Whether certified for alcohol-related events
        created_at (datetime): When the employee record was created
        external_id (str): Unique ID in external HR/scheduling system
        last_synced (datetime): Last time data was synchronized
        sync_status (str): Current sync status ('pending', 'synced', 'error')

    Business Rules:
        - Only active employees (is_active=True) can be assigned to new schedules
        - Adult beverage events require adult_beverage_trained=True
        - Email addresses must be unique across all employees

    Example:
        # Find all active employees available for scheduling
        active_employees = Employee.query.filter_by(is_active=True).all()

        # Find employees qualified for adult beverage events
        qualified = Employee.query.filter_by(
            is_active=True,
            adult_beverage_trained=True
        ).all()

        # Get employee for a specific schedule
        schedule = Schedule.query.get(schedule_id)
        employee = Employee.query.get(schedule.employee_id)
        print(f"Employee: {employee.name} ({employee.email})")
    """
    __tablename__ = 'employees'

    # Primary identifier (from external system, not auto-increment)
    id = db.Column(db.String(50), primary_key=True)

    # Personal information
    name = db.Column(db.String(100), nullable=False)  # Full name
    email = db.Column(db.String(120), unique=True)  # Email address (must be unique)
    phone = db.Column(db.String(20))  # Contact phone number

    # Status and role flags
    is_active = db.Column(db.Boolean, nullable=False)  # Currently employed/available?
    is_supervisor = db.Column(db.Boolean, nullable=False)  # Has supervisor role?

    # Job classification
    job_title = db.Column(db.String(50), nullable=False)  # Job title/position

    # Training and certifications
    adult_beverage_trained = db.Column(db.Boolean, nullable=False)  # Certified for alcohol events?

    # Record metadata
    created_at = db.Column(db.DateTime, nullable=False)  # When record was created

    # External system synchronization fields
    external_id = db.Column(db.String(100), unique=True)  # ID in external HR system
    last_synced = db.Column(db.DateTime)  # Timestamp of last sync operation
    sync_status = db.Column(db.String(20))  # Sync state: pending/synced/error

    def __repr__(self):
        """String representation for debugging and logging."""
        return f'<Employee {self.id}: {self.name}>'
