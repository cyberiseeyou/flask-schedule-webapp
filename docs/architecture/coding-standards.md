# Coding Standards - Flask Schedule Webapp

## Overview
This document defines coding conventions and best practices for the Flask Schedule Webapp project. All contributors must follow these standards to maintain code quality and consistency.

**Last Updated**: 2025-01-09
**Version**: 1.0

---

## Table of Contents
- [Python Style Guide](#python-style-guide)
- [Naming Conventions](#naming-conventions)
- [Documentation](#documentation)
- [Type Hints](#type-hints)
- [Error Handling](#error-handling)
- [Database Practices](#database-practices)
- [Flask-Specific Standards](#flask-specific-standards)
- [Security](#security)
- [Testing](#testing)
- [Code Review Checklist](#code-review-checklist)

---

## Python Style Guide

### General Conventions
- **PEP 8 Compliance**: All code must follow [PEP 8](https://peps.python.org/pep-0008/)
- **Line Length**: Maximum 100 characters (relaxed from PEP 8's 79 for readability)
- **Indentation**: 4 spaces (no tabs)
- **Encoding**: UTF-8 with BOM for all Python files
- **Imports**: Organized using `isort` - stdlib, third-party, local

**Import Order Example**:
```python
# Standard library imports
import os
import sys
from datetime import datetime, timedelta

# Third-party imports
from flask import Flask, jsonify, request
from sqlalchemy import Column, Integer, String

# Local application imports
from models import Employee, Event
from services.scheduling_engine import SchedulingEngine
```

### Line Breaks and Whitespace
```python
# GOOD: Clear spacing
def schedule_event(event_id: int, employee_id: str) -> bool:
    """Schedule an event for an employee."""
    if not event_id:
        return False

    result = create_schedule(event_id, employee_id)
    return result

# BAD: Cramped code
def schedule_event(event_id:int,employee_id:str)->bool:
    if not event_id:return False
    result=create_schedule(event_id,employee_id)
    return result
```

---

## Naming Conventions

### Classes
- **Style**: `PascalCase`
- **Example**: `SchedulingEngine`, `EmployeeRepository`, `ValidationResult`

```python
class SchedulingEngine:
    """Core auto-scheduler orchestrator."""
    pass

class EDRReportGenerator:
    """Generates Event Detail Reports."""
    pass
```

### Functions and Methods
- **Style**: `snake_case`
- **Verb-based**: Start with action verbs
- **Example**: `schedule_event`, `validate_assignment`, `get_employee_by_id`

```python
def schedule_event(event: Event, employee: Employee) -> bool:
    """Schedule an event for an employee."""
    pass

def get_available_employees(date: datetime, event_type: str) -> List[Employee]:
    """Get all employees available for given date and event type."""
    pass
```

### Variables
- **Style**: `snake_case`
- **Descriptive**: Clear purpose
- **Example**: `schedule_datetime`, `employee_list`, `validation_result`

```python
# GOOD: Descriptive names
schedule_datetime = datetime.now()
available_employees = get_employees()
validation_result = validator.check()

# BAD: Unclear abbreviations
sched_dt = datetime.now()
emp_lst = get_emp()
val_res = vldtr.chk()
```

### Constants
- **Style**: `UPPER_SNAKE_CASE`
- **Module level**: Define at top of file
- **Example**: `DEFAULT_TIMEOUT`, `MAX_RETRIES`, `SCHEDULING_WINDOW_DAYS`

```python
# constants.py or at module top
SCHEDULING_WINDOW_DAYS = 3
MAX_RETRY_ATTEMPTS = 3
DEFAULT_EVENT_DURATION_MINUTES = 60
CORE_TIME_SLOTS = [time(9, 45), time(10, 30), time(11, 0), time(11, 30)]
```

### Private/Internal
- **Style**: Prefix with single underscore `_`
- **Usage**: Internal helpers, not part of public API
- **Example**: `_internal_helper`, `_validate_input`

```python
class SchedulingEngine:
    def schedule_event(self, event):
        """Public method."""
        return self._internal_schedule(event)

    def _internal_schedule(self, event):
        """Private helper - not called externally."""
        pass
```

### File Names
- **Style**: `snake_case.py`
- **Descriptive**: Clear purpose
- **Example**: `scheduling_engine.py`, `constraint_validator.py`, `edr_report_generator.py`

---

## Documentation

### Module-Level Docstrings
**Required** for all Python files.

```python
"""
Employee model and related database schema.

This module defines the Employee model representing schedulable staff members,
including their job titles, availability, and scheduling constraints.

Classes:
    Employee: Main employee model with SQLAlchemy ORM

Functions:
    create_employee_model: Factory function for Employee model
"""
```

### Class Docstrings
**Required** for all classes.

```python
class SchedulingEngine:
    """
    Core auto-scheduler orchestrator.

    Handles automatic scheduling of events to employees based on:
    - Employee availability and time off
    - Event type constraints (role-based)
    - Rotation assignments
    - Scheduling priority rules

    Process:
        1. Filter events within scheduling window
        2. Sort by priority (due date, event type)
        3. Schedule Core events (Leads → Specialists)
        4. Schedule rotation events (Juicer, Digital, Freeosk)
        5. Auto-pair Supervisor events

    Attributes:
        db: SQLAlchemy database session
        models: Dictionary of model classes
        rotation_manager: RotationManager instance
        validator: ConstraintValidator instance

    Example:
        >>> engine = SchedulingEngine(db_session, models)
        >>> run = engine.run_auto_scheduler('manual')
        >>> print(f"Scheduled {run.events_scheduled} events")
    """
```

### Function Docstrings
**Required** for all public functions and methods. Use **Google style**.

```python
def schedule_event(event_id: int, employee_id: str, datetime: datetime) -> bool:
    """
    Schedule an event for an employee at specified datetime.

    This function validates the employee can work the event type,
    checks for scheduling conflicts, and creates a schedule record
    in the database. For Core events, it enforces the one-per-day
    constraint.

    Args:
        event_id: Unique identifier for the event to schedule
        employee_id: Employee identifier (e.g., 'EMP001')
        datetime: Scheduled datetime for the event

    Returns:
        bool: True if scheduling successful, False otherwise

    Raises:
        ValueError: If event_id or employee_id is invalid
        SchedulingConflictError: If employee already scheduled at that time
        DatabaseError: If database operation fails

    Example:
        >>> success = schedule_event(123456, 'EMP001', datetime(2025, 1, 15, 10, 0))
        >>> if success:
        ...     print("Event scheduled successfully")

    Note:
        - Core events: Limited to one per employee per day
        - Supervisor events: Can overlap with other events
        - Rotation events: Follow rotation assignments
    """
    # Implementation
```

### Inline Comments
- Use **sparingly** - code should be self-documenting
- Explain **why**, not **what**
- Use for complex logic only

```python
# GOOD: Explains reasoning
# Use rotation manager for Juicer events to ensure proper load distribution
# across certified Juicer Baristas per business requirements (Jan 2025)
employee = rotation_manager.get_juicer_employee(date)

# BAD: States the obvious
# Get employee
employee = rotation_manager.get_juicer_employee(date)
```

### TODO/FIXME Tags
```python
# TODO: Implement timezone handling for multi-location support
# FIXME: Race condition when multiple auto-schedulers run simultaneously
# NOTE: This uses legacy rotation algorithm - migrate to new system by Q2 2025
# HACK: Temporary workaround for EDR API timeout issue - remove when fixed
```

---

## Type Hints

**Required** for all function parameters and return values (Python 3.11+).

```python
from typing import List, Dict, Optional, Union, Tuple
from datetime import datetime

def get_available_employees(
    event_type: str,
    target_date: datetime,
    exclude_ids: Optional[List[str]] = None
) -> List[Employee]:
    """Get available employees for event type on target date."""
    if exclude_ids is None:
        exclude_ids = []
    # Implementation

def validate_assignment(
    event: Event,
    employee: Employee,
    schedule_datetime: datetime
) -> Tuple[bool, List[str]]:
    """
    Validate if employee can be assigned to event.

    Returns:
        Tuple of (is_valid, list of violation reasons)
    """
    return True, []
```

### Complex Types
```python
from typing import TypeAlias, NewType

# Type aliases for clarity
EmployeeID: TypeAlias = str
EventID: TypeAlias = int
ScheduleData: TypeAlias = Dict[str, Union[str, int, datetime]]

# NewType for stronger type checking
class ValidationResult:
    """Result of validation with violations."""
    is_valid: bool
    violations: List[str]
```

---

## Error Handling

### Use Custom Exceptions
**Don't** raise generic `Exception` - create specific exception types.

```python
# exceptions.py
class SchedulerException(Exception):
    """Base exception for scheduler errors."""
    pass

class SchedulingConflictError(SchedulerException):
    """Raised when employee cannot be scheduled due to conflict."""
    pass

class ValidationError(SchedulerException):
    """Raised when validation fails."""
    pass

class AuthenticationError(SchedulerException):
    """Raised when authentication fails."""
    pass

class ExternalAPIError(SchedulerException):
    """Raised when external API calls fail."""
    def __init__(self, message: str, api_name: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.api_name = api_name
        self.status_code = status_code
```

### Exception Handling Pattern
```python
import logging
logger = logging.getLogger(__name__)

def schedule_event(event: Event, employee: Employee) -> bool:
    """Schedule an event with proper error handling."""
    try:
        # Validate inputs
        if not event or not employee:
            raise ValueError("Event and employee are required")

        # Check constraints
        validation = validator.validate_assignment(event, employee, datetime.now())
        if not validation.is_valid:
            raise SchedulingConflictError(
                f"Cannot schedule: {', '.join(validation.violations)}"
            )

        # Create schedule
        schedule = Schedule(event_ref_num=event.id, employee_id=employee.id)
        db.session.add(schedule)
        db.session.commit()

        logger.info(f"Scheduled event {event.id} for employee {employee.id}")
        return True

    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        raise
    except SchedulingConflictError as e:
        logger.warning(f"Scheduling conflict: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error scheduling event: {e}", exc_info=True)
        db.session.rollback()
        raise SchedulerException(f"Failed to schedule event: {e}") from e
```

### Logging Levels
```python
import logging
logger = logging.getLogger(__name__)

# DEBUG: Detailed diagnostic info (development only)
logger.debug(f"Checking availability for {len(employees)} employees")

# INFO: General information about operations
logger.info(f"Scheduled event {event.id} for employee {employee.name}")

# WARNING: Unexpected but recoverable situations
logger.warning(f"Employee {employee.id} has conflicting schedule, skipping")

# ERROR: Error that prevents operation
logger.error(f"Failed to connect to Crossmark API: {e}")

# CRITICAL: Critical error requiring immediate attention
logger.critical(f"Database connection lost, cannot process schedules")
```

---

## Database Practices

### Use SQLAlchemy ORM
**Always** use SQLAlchemy ORM - avoid raw SQL.

```python
# GOOD: SQLAlchemy ORM
schedules = db.session.query(Schedule).filter(
    Schedule.schedule_datetime >= start_date,
    Schedule.schedule_datetime < end_date,
    Schedule.employee_id == employee_id
).order_by(Schedule.schedule_datetime).all()

# BAD: Raw SQL (unless absolutely necessary)
db.session.execute(
    "SELECT * FROM schedules WHERE schedule_datetime >= ? AND employee_id = ?",
    (start_date, employee_id)
)
```

### Session Management
```python
from contextlib import contextmanager

# GOOD: Context manager for transactions
@contextmanager
def transaction_scope():
    """Provide a transactional scope around operations."""
    session = db.session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# Usage
with transaction_scope() as session:
    schedule = Schedule(...)
    session.add(schedule)
    # Automatic commit on success, rollback on error
```

### Query Performance
```python
# GOOD: Filter on indexed columns
schedules = Schedule.query.filter_by(
    employee_id=emp_id  # Indexed column
).all()

# GOOD: Use join() for relationships
schedules = db.session.query(Schedule, Event, Employee).join(
    Event, Schedule.event_ref_num == Event.project_ref_num
).join(
    Employee, Schedule.employee_id == Employee.id
).all()

# BAD: N+1 query problem
for schedule in Schedule.query.all():
    event = Event.query.get(schedule.event_ref_num)  # N queries!
    print(event.name)

# GOOD: Eager loading
schedules = Schedule.query.options(
    joinedload(Schedule.event),
    joinedload(Schedule.employee)
).all()
```

---

## Flask-Specific Standards

### Blueprint Organization
```python
# routes/scheduling.py
from flask import Blueprint

scheduling_bp = Blueprint('scheduling', __name__, url_prefix='/api/schedule')

@scheduling_bp.route('/create', methods=['POST'])
def create_schedule():
    """Create a new schedule."""
    pass
```

### Route Naming
- **URL**: `/noun/verb` pattern
- **Function**: Verb-based, descriptive
- **Examples**:
  - `/schedule/create` → `create_schedule()`
  - `/employee/update/<id>` → `update_employee(id)`
  - `/event/delete/<id>` → `delete_event(id)`

```python
@api_bp.route('/schedule/create', methods=['POST'])
def create_schedule():
    """Create a new schedule entry."""
    pass

@api_bp.route('/employee/<employee_id>/availability', methods=['GET'])
def get_employee_availability(employee_id: str):
    """Get availability for specific employee."""
    pass
```

### Request Validation
```python
from flask import request, jsonify

@api_bp.route('/schedule/create', methods=['POST'])
def create_schedule():
    """Create schedule with input validation."""
    # Validate content type
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400

    data = request.get_json()

    # Validate required fields
    required_fields = ['event_id', 'employee_id', 'datetime']
    missing = [f for f in required_fields if f not in data]
    if missing:
        return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400

    # Validate data types
    try:
        event_id = int(data['event_id'])
        employee_id = str(data['employee_id'])
        schedule_datetime = datetime.fromisoformat(data['datetime'])
    except (ValueError, TypeError) as e:
        return jsonify({'error': f'Invalid data format: {e}'}), 400

    # Business logic
    result = schedule_service.create(event_id, employee_id, schedule_datetime)
    return jsonify({'success': True, 'schedule_id': result.id}), 201
```

### Response Format
```python
# SUCCESS: 200/201
return jsonify({
    'success': True,
    'data': {
        'schedule_id': 123,
        'event_name': 'Core Event',
        'employee_name': 'John Doe'
    }
}), 201

# ERROR: 4xx/5xx
return jsonify({
    'success': False,
    'error': 'Validation failed',
    'details': ['Employee not available', 'Event outside date range']
}), 400
```

---

## Security

### Never Hardcode Credentials
```python
# BAD: Hardcoded credentials
WALMART_USERNAME = 'user@example.com'
WALMART_PASSWORD = 'password123'

# GOOD: Environment variables
from decouple import config
WALMART_USERNAME = config('WALMART_EDR_USERNAME')  # No default!
WALMART_PASSWORD = config('WALMART_EDR_PASSWORD')  # Will raise if not set
```

### Input Validation
```python
# GOOD: Validate and sanitize all inputs
def get_employee(employee_id: str):
    # Validate format
    if not re.match(r'^EMP\d{3}$', employee_id):
        raise ValueError("Invalid employee ID format")

    employee = Employee.query.get(employee_id)
    if not employee:
        raise ValueError("Employee not found")

    return employee
```

### SQL Injection Prevention
```python
# GOOD: SQLAlchemy handles parameterization
Employee.query.filter_by(id=employee_id).first()

# BAD: String formatting (vulnerable to SQL injection)
db.session.execute(f"SELECT * FROM employees WHERE id = '{employee_id}'")
```

### CSRF Protection
```python
# Require CSRF tokens for state-changing operations
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

# Only exempt specific routes that truly need it
@auth_bp.route('/login', methods=['POST'])
@csrf.exempt  # Login can't have token before auth
def login():
    pass
```

---

## Testing

### Test File Structure
```
tests/
├── unit/
│   ├── services/
│   │   └── test_scheduling_engine.py
│   └── models/
│       └── test_employee.py
└── integration/
    └── test_api_routes.py
```

### Test Naming
```python
# test_scheduling_engine.py
class TestSchedulingEngine:
    """Test suite for SchedulingEngine service."""

    def test_schedule_core_event_success(self):
        """Test successful Core event scheduling."""
        pass

    def test_schedule_core_event_conflict(self):
        """Test Core event scheduling with conflict."""
        pass

    def test_schedule_juicer_event_bumps_core(self):
        """Test Juicer event bumping Core event when needed."""
        pass
```

### AAA Pattern
```python
def test_schedule_event_success():
    """Test successful event scheduling."""
    # Arrange - Set up test data
    employee = EmployeeFactory(job_title='Event Specialist')
    event = EventFactory(event_type='Core')
    schedule_datetime = datetime.now() + timedelta(days=5)

    # Act - Execute the code being tested
    result = schedule_event(event, employee, schedule_datetime)

    # Assert - Verify the result
    assert result is True
    schedule = Schedule.query.filter_by(event_ref_num=event.id).first()
    assert schedule is not None
    assert schedule.employee_id == employee.id
```

---

## Code Review Checklist

Before submitting code for review, verify:

### General
- [ ] Code follows PEP 8 style guide
- [ ] Line length ≤ 100 characters
- [ ] No unused imports or variables
- [ ] Consistent naming conventions

### Documentation
- [ ] Module docstring present
- [ ] All classes have docstrings
- [ ] All public functions have docstrings (Google style)
- [ ] Complex logic has inline comments

### Type Safety
- [ ] All function parameters have type hints
- [ ] All return values have type hints
- [ ] No `Any` types without justification

### Error Handling
- [ ] Custom exceptions used (not generic Exception)
- [ ] Errors logged appropriately
- [ ] Database transactions have rollback on error

### Security
- [ ] No hardcoded credentials
- [ ] Input validation present
- [ ] CSRF protection on state-changing routes
- [ ] SQL injection prevented (using ORM)

### Testing
- [ ] Unit tests written for new code
- [ ] Tests follow AAA pattern
- [ ] Edge cases covered
- [ ] Test coverage ≥ 80%

### Performance
- [ ] Database queries optimized
- [ ] No N+1 query problems
- [ ] Indexed columns used in filters

---

## Tools & Automation

### Linting
```bash
# Install tools
pip install flake8 pylint black isort mypy

# Run linter
flake8 scheduler_app/ --max-line-length=100

# Check types
mypy scheduler_app/

# Format code
black scheduler_app/ --line-length=100

# Sort imports
isort scheduler_app/
```

### Pre-commit Hook
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        args: [--line-length=100]

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=100]
```

---

## References

- [PEP 8 - Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Flask Best Practices](https://flask.palletsprojects.com/en/2.3.x/patterns/)
- [SQLAlchemy ORM Tutorial](https://docs.sqlalchemy.org/en/20/orm/tutorial.html)
- [Type Hints (PEP 484)](https://peps.python.org/pep-0484/)

---

**Document Ownership**: Dev Team
**Review Cycle**: Quarterly
**Last Reviewed**: 2025-01-09
