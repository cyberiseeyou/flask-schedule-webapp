"""
Employee availability models
Tracks when employees can/cannot work
"""
from datetime import datetime


def create_availability_models(db):
    """Factory function to create availability models with db instance"""

    class EmployeeWeeklyAvailability(db.Model):
        """
        Weekly availability pattern for employees
        Defines which days of the week an employee typically works
        """
        __tablename__ = 'employee_weekly_availability'

        id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        employee_id = db.Column(db.String(50), db.ForeignKey('employees.id'), nullable=False)
        monday = db.Column(db.Boolean, nullable=False, default=True)
        tuesday = db.Column(db.Boolean, nullable=False, default=True)
        wednesday = db.Column(db.Boolean, nullable=False, default=True)
        thursday = db.Column(db.Boolean, nullable=False, default=True)
        friday = db.Column(db.Boolean, nullable=False, default=True)
        saturday = db.Column(db.Boolean, nullable=False, default=True)
        sunday = db.Column(db.Boolean, nullable=False, default=True)

        __table_args__ = (
            db.UniqueConstraint('employee_id', name='unique_employee_weekly_availability'),
        )

        def __repr__(self):
            return f'<EmployeeWeeklyAvailability {self.employee_id}>'

    class EmployeeAvailability(db.Model):
        """
        Specific date availability for employees
        Overrides weekly pattern for specific dates
        """
        __tablename__ = 'employee_availability'

        id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        employee_id = db.Column(db.String(50), db.ForeignKey('employees.id'), nullable=False)
        date = db.Column(db.Date, nullable=False)
        is_available = db.Column(db.Boolean, nullable=False, default=True)
        reason = db.Column(db.String(200))  # Optional reason for unavailability

        __table_args__ = (
            db.UniqueConstraint('employee_id', 'date', name='unique_employee_date_availability'),
        )

        def __repr__(self):
            status = "available" if self.is_available else "unavailable"
            return f'<EmployeeAvailability {self.employee_id} on {self.date}: {status}>'

    class EmployeeTimeOff(db.Model):
        """
        Time off requests and scheduled absences
        Employees are unavailable during these date ranges
        """
        __tablename__ = 'employee_time_off'

        id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        employee_id = db.Column(db.String(50), db.ForeignKey('employees.id'), nullable=False)
        start_date = db.Column(db.Date, nullable=False)
        end_date = db.Column(db.Date, nullable=False)
        reason = db.Column(db.String(200))
        created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

        __table_args__ = (
            db.Index('idx_employee_time_off_dates', 'employee_id', 'start_date', 'end_date'),
        )

        def __repr__(self):
            return f'<EmployeeTimeOff {self.employee_id}: {self.start_date} to {self.end_date}>'

    return EmployeeWeeklyAvailability, EmployeeAvailability, EmployeeTimeOff
