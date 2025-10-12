"""
Database models for Flask Schedule Webapp
Centralizes all SQLAlchemy model imports using factory pattern
"""
from .employee import create_employee_model
from .event import create_event_model
from .schedule import create_schedule_model
from .availability import create_availability_models
from .auto_scheduler import create_auto_scheduler_models
from .system_setting import create_system_setting_model
from .audit import create_audit_models


def init_models(db):
    """
    Initialize all models with the database instance

    Args:
        db: SQLAlchemy database instance

    Returns:
        dict: Dictionary containing all model classes
    """
    Employee = create_employee_model(db)
    Event = create_event_model(db)
    Schedule = create_schedule_model(db)
    EmployeeWeeklyAvailability, EmployeeAvailability, EmployeeTimeOff = create_availability_models(db)
    RotationAssignment, PendingSchedule, SchedulerRunHistory, ScheduleException = create_auto_scheduler_models(db)
    SystemSetting = create_system_setting_model(db)
    AuditLog, AuditNotificationSettings = create_audit_models(db)

    return {
        'Employee': Employee,
        'Event': Event,
        'Schedule': Schedule,
        'EmployeeWeeklyAvailability': EmployeeWeeklyAvailability,
        'EmployeeAvailability': EmployeeAvailability,
        'EmployeeTimeOff': EmployeeTimeOff,
        'RotationAssignment': RotationAssignment,
        'PendingSchedule': PendingSchedule,
        'SchedulerRunHistory': SchedulerRunHistory,
        'ScheduleException': ScheduleException,
        'SystemSetting': SystemSetting,
        'AuditLog': AuditLog,
        'AuditNotificationSettings': AuditNotificationSettings
    }


__all__ = [
    'init_models',
    'create_employee_model',
    'create_event_model',
    'create_schedule_model',
    'create_availability_models',
    'create_auto_scheduler_models',
    'create_system_setting_model',
    'create_audit_models'
]
