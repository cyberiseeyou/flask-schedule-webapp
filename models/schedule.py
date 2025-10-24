"""
Schedule model - links events to employees with specific datetime
"""
from datetime import datetime


def create_schedule_model(db):
    """Factory function to create Schedule model with db instance"""

    class Schedule(db.Model):
        """
        Schedule model representing an event assigned to an employee

        This is the core scheduling entity that links Events and Employees
        with a specific datetime for when the work should be performed.
        """
        __tablename__ = 'schedules'

        id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        event_ref_num = db.Column(db.Integer, db.ForeignKey('events.project_ref_num'), nullable=False)
        employee_id = db.Column(db.String(50), db.ForeignKey('employees.id'), nullable=False)
        schedule_datetime = db.Column(db.DateTime, nullable=False)

        # Sync fields for API integration
        external_id = db.Column(db.String(100), unique=True)
        last_synced = db.Column(db.DateTime)
        sync_status = db.Column(db.String(20), default='pending')

        __table_args__ = (
            db.Index('idx_schedules_date', 'schedule_datetime'),
        )

        # Relationships
        employee = db.relationship('Employee', backref='schedules', lazy=True)
        event = db.relationship('Event', foreign_keys=[event_ref_num],
                               primaryjoin="Schedule.event_ref_num==Event.project_ref_num",
                               backref='schedules', lazy=True)

        def __repr__(self):
            return f'<Schedule {self.id}: Event {self.event_ref_num} -> Employee {self.employee_id}>'

    return Schedule
