"""
Constraint Validator Service
Validates scheduling assignments against business rules
"""
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from scheduler_app.services.validation_types import (
    ValidationResult,
    ConstraintViolation,
    ConstraintType,
    ConstraintSeverity
)


class ConstraintValidator:
    """
    Validates proposed schedule assignments against all constraints

    Handles:
    - Availability window checking
    - Time-off request validation
    - Role-based event restrictions
    - Daily event limits
    - Already-scheduled conflicts
    """

    # Event types requiring Lead or Supervisor
    LEAD_ONLY_EVENT_TYPES = ['Freeosk', 'Digitals', 'Digital Setup', 'Digital Refresh', 'Digital Teardown', 'Other']

    # Max core events per employee per day
    MAX_CORE_EVENTS_PER_DAY = 1

    def __init__(self, db_session: Session, models: dict):
        """
        Initialize ConstraintValidator

        Args:
            db_session: SQLAlchemy database session
            models: Dictionary of model classes from app.config
        """
        self.db = db_session
        self.Employee = models['Employee']
        self.Event = models['Event']
        self.Schedule = models['Schedule']
        self.EmployeeTimeOff = models['EmployeeTimeOff']
        self.EmployeeAvailability = models.get('EmployeeAvailability')
        self.EmployeeWeeklyAvailability = models.get('EmployeeWeeklyAvailability')
        self.PendingSchedule = models.get('PendingSchedule')
        self.current_run_id = None  # Track current scheduler run

    def set_current_run(self, run_id: int) -> None:
        """
        Set the current scheduler run ID to check pending schedules

        Args:
            run_id: The scheduler run ID to track pending assignments
        """
        self.current_run_id = run_id

    def validate_assignment(self, event: object, employee: object,
                           schedule_datetime: datetime) -> ValidationResult:
        """
        Validate a proposed schedule assignment against all constraints

        Args:
            event: Event model instance
            employee: Employee model instance
            schedule_datetime: Proposed datetime for the event

        Returns:
            ValidationResult with is_valid flag and list of violations
        """
        result = ValidationResult(is_valid=True)

        # Check all constraints
        self._check_time_off(employee, schedule_datetime, result)
        self._check_availability(employee, schedule_datetime, result)
        self._check_role_requirements(event, employee, result)
        self._check_daily_limit(employee, schedule_datetime, result)
        self._check_already_scheduled(employee, schedule_datetime, result)
        self._check_due_date(event, schedule_datetime, result)

        return result

    def _check_time_off(self, employee: object, schedule_datetime: datetime,
                       result: ValidationResult) -> None:
        """Check if employee has requested time off"""
        target_date = schedule_datetime.date()

        time_off = self.db.query(self.EmployeeTimeOff).filter(
            self.EmployeeTimeOff.employee_id == employee.id,
            self.EmployeeTimeOff.start_date <= target_date,
            self.EmployeeTimeOff.end_date >= target_date
        ).first()

        if time_off:
            result.add_violation(ConstraintViolation(
                constraint_type=ConstraintType.TIME_OFF,
                message=f"Employee {employee.name} has requested time off on {target_date}",
                severity=ConstraintSeverity.HARD,
                details={'time_off_id': time_off.id, 'date': str(target_date)}
            ))

    def _check_availability(self, employee: object, schedule_datetime: datetime,
                           result: ValidationResult) -> None:
        """Check if schedule_datetime falls within employee's availability window"""
        # Check weekly availability pattern
        if self.EmployeeWeeklyAvailability:
            day_of_week = schedule_datetime.weekday()  # 0=Monday, 6=Sunday

            # Map day_of_week to column name
            day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            day_column = day_names[day_of_week]

            weekly_avail = self.db.query(self.EmployeeWeeklyAvailability).filter_by(
                employee_id=employee.id
            ).first()

            if weekly_avail:
                # Check if employee is available on this day
                is_available = getattr(weekly_avail, day_column, True)

                if not is_available:
                    result.add_violation(ConstraintViolation(
                        constraint_type=ConstraintType.AVAILABILITY,
                        message=f"Employee {employee.name} not available on {day_column.capitalize()}",
                        severity=ConstraintSeverity.HARD,
                        details={'day_of_week': day_of_week, 'day_name': day_column}
                    ))

    def _check_role_requirements(self, event: object, employee: object,
                                 result: ValidationResult) -> None:
        """Check if employee's role is authorized for this event type"""
        # Juicer events require Juicer Barista role
        if event.event_type == 'Juicer':
            if employee.job_title != 'Juicer Barista':
                result.add_violation(ConstraintViolation(
                    constraint_type=ConstraintType.ROLE,
                    message=f"Employee {employee.name} is not a Juicer Barista",
                    severity=ConstraintSeverity.HARD,
                    details={'event_type': event.event_type, 'employee_role': employee.job_title}
                ))

        # Lead-only event types
        if event.event_type in self.LEAD_ONLY_EVENT_TYPES:
            if employee.job_title not in ['Lead Event Specialist', 'Club Supervisor']:
                result.add_violation(ConstraintViolation(
                    constraint_type=ConstraintType.ROLE,
                    message=f"Event type '{event.event_type}' requires Lead or Supervisor role",
                    severity=ConstraintSeverity.HARD,
                    details={'event_type': event.event_type, 'employee_role': employee.job_title}
                ))

        # Club Supervisor should not be scheduled to regular events
        if employee.job_title == 'Club Supervisor' and event.event_type not in ['Supervisor', 'Digitals', 'Freeosk']:
            result.add_violation(ConstraintViolation(
                constraint_type=ConstraintType.ROLE,
                message="Club Supervisor should not be assigned to regular events",
                severity=ConstraintSeverity.SOFT,  # Soft constraint
                details={'event_type': event.event_type}
            ))

    def _check_daily_limit(self, employee: object, schedule_datetime: datetime,
                          result: ValidationResult) -> None:
        """Check if employee already has max core events for this day"""
        target_date = schedule_datetime.date()

        # Count existing core events for this employee on this day
        core_events_count = self.db.query(func.count(self.Schedule.id)).join(
            self.Event, self.Schedule.event_ref_num == self.Event.project_ref_num
        ).filter(
            self.Schedule.employee_id == employee.id,
            func.date(self.Schedule.schedule_datetime) == target_date,
            self.Event.event_type == 'Core'
        ).scalar()

        # Also count pending core events from current run
        if self.current_run_id and self.PendingSchedule:
            pending_core_count = self.db.query(func.count(self.PendingSchedule.id)).join(
                self.Event, self.PendingSchedule.event_ref_num == self.Event.project_ref_num
            ).filter(
                self.PendingSchedule.scheduler_run_id == self.current_run_id,
                self.PendingSchedule.employee_id == employee.id,
                func.date(self.PendingSchedule.schedule_datetime) == target_date,
                self.Event.event_type == 'Core'
            ).scalar()

            core_events_count += pending_core_count

        if core_events_count >= self.MAX_CORE_EVENTS_PER_DAY:
            result.add_violation(ConstraintViolation(
                constraint_type=ConstraintType.DAILY_LIMIT,
                message=f"Employee {employee.name} already has {core_events_count} core event(s) on {target_date}",
                severity=ConstraintSeverity.HARD,
                details={'date': str(target_date), 'current_count': core_events_count}
            ))

    def _check_already_scheduled(self, employee: object, schedule_datetime: datetime,
                                 result: ValidationResult) -> None:
        """Check if employee already has a schedule at this exact datetime"""
        # Check existing schedules
        existing = self.db.query(self.Schedule).filter_by(
            employee_id=employee.id,
            schedule_datetime=schedule_datetime
        ).first()

        if existing:
            result.add_violation(ConstraintViolation(
                constraint_type=ConstraintType.ALREADY_SCHEDULED,
                message=f"Employee {employee.name} already scheduled at {schedule_datetime}",
                severity=ConstraintSeverity.HARD,
                details={'schedule_id': existing.id, 'datetime': str(schedule_datetime)}
            ))
            return

        # Check pending schedules from current run
        if self.current_run_id and self.PendingSchedule:
            pending = self.db.query(self.PendingSchedule).filter_by(
                scheduler_run_id=self.current_run_id,
                employee_id=employee.id,
                schedule_datetime=schedule_datetime
            ).first()

            if pending:
                result.add_violation(ConstraintViolation(
                    constraint_type=ConstraintType.ALREADY_SCHEDULED,
                    message=f"Employee {employee.name} already assigned at {schedule_datetime} in this run",
                    severity=ConstraintSeverity.HARD,
                    details={'pending_schedule_id': pending.id, 'datetime': str(schedule_datetime)}
                ))

    def _check_due_date(self, event: object, schedule_datetime: datetime,
                       result: ValidationResult) -> None:
        """Check if scheduled date is before the due date"""
        if schedule_datetime.date() >= event.due_datetime.date():
            result.add_violation(ConstraintViolation(
                constraint_type=ConstraintType.DUE_DATE,
                message=f"Event must be scheduled before due date {event.due_datetime.date()}",
                severity=ConstraintSeverity.HARD,
                details={
                    'due_date': str(event.due_datetime.date()),
                    'proposed_date': str(schedule_datetime.date())
                }
            ))

    def get_available_employees(self, event: object, schedule_datetime: datetime) -> List[object]:
        """
        Get list of employees who can be assigned to this event at this time

        Filters by:
        - Role requirements
        - Time off
        - Daily limits
        - Availability

        Args:
            event: Event to schedule
            schedule_datetime: Proposed datetime

        Returns:
            List of Employee objects who pass all constraints
        """
        # Start with all employees
        all_employees = self.db.query(self.Employee).all()

        available = []
        for employee in all_employees:
            validation = self.validate_assignment(event, employee, schedule_datetime)
            if validation.is_valid:
                available.append(employee)

        return available

    def get_available_employee_ids(self, event: object, schedule_datetime: datetime) -> List[str]:
        """
        Get list of employee IDs who can be assigned to this event

        Args:
            event: Event to schedule
            schedule_datetime: Proposed datetime

        Returns:
            List of employee ID strings
        """
        employees = self.get_available_employees(event, schedule_datetime)
        return [emp.id for emp in employees]
