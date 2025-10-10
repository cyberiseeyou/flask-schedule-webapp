# CRITICAL-03: Create Missing Architecture Documentation

## Priority
🔴 **CRITICAL** - Immediate Action Required

## Status
🟢 Complete

## Type
📚 Documentation

## Assigned To
**PM Agent (John)** with support from **Dev Agent (James)**

## Description
Critical architecture documentation files are missing, making onboarding and maintenance difficult. The `core-config.yaml` references these files in `devLoadAlwaysFiles`, but they don't exist.

### Missing Files
- `docs/architecture/coding-standards.md` ❌
- `docs/architecture/tech-stack.md` ❌
- `docs/architecture/source-tree.md` ❌

### Reference in core-config.yaml
```yaml
devLoadAlwaysFiles:
  - docs/architecture/coding-standards.md
  - docs/architecture/tech-stack.md
  - docs/architecture/source-tree.md
```

## Impact
- **Developers** have no standard coding conventions to follow
- **Onboarding** is slow without architecture overview
- **Dev Agent (James)** cannot load critical context during activation
- **Code consistency** suffers without documented standards

## Acceptance Criteria
- [x] Create `docs/architecture/coding-standards.md` with Python/Flask conventions
- [x] Create `docs/architecture/tech-stack.md` with technology choices and rationale
- [x] Create `docs/architecture/source-tree.md` with directory structure explanation
- [x] All files follow consistent markdown formatting
- [x] Include examples and code snippets where appropriate
- [x] Get review from Dev Agent (James) for technical accuracy
- [x] Link documents to main README

## Implementation

### File 1: coding-standards.md

**Template**:
```markdown
# Coding Standards - Flask Schedule Webapp

## Python Style Guide

### General Conventions
- **PEP 8** compliance required
- **Line length**: 100 characters (relaxed from PEP 8's 79)
- **Indentation**: 4 spaces (no tabs)
- **Encoding**: UTF-8

### Naming Conventions
- **Classes**: `PascalCase` (e.g., `SchedulingEngine`)
- **Functions/Methods**: `snake_case` (e.g., `schedule_event`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_TIMEOUT`)
- **Private methods**: Prefix with `_` (e.g., `_internal_helper`)

### Docstrings
- **Required** for all public modules, classes, and functions
- Use **Google style** docstrings
- Example:
```python
def schedule_event(event_id: int, employee_id: str, datetime: datetime) -> bool:
    """
    Schedule an event for an employee.

    Args:
        event_id: Unique identifier for the event
        employee_id: Employee identifier
        datetime: Scheduled datetime

    Returns:
        bool: True if scheduling successful, False otherwise

    Raises:
        ValueError: If event_id or employee_id is invalid
        SchedulingConflictError: If employee already scheduled
    """
```

### Type Hints
- Use type hints for all function parameters and return values
- Use `from typing import List, Dict, Optional, Union` as needed
- Example:
```python
from typing import List, Optional
from datetime import datetime

def get_available_employees(
    event_type: str,
    target_date: datetime,
    exclude_ids: Optional[List[str]] = None
) -> List[Employee]:
    """Get available employees for event type on target date."""
    ...
```

### Error Handling
- Use **custom exceptions** over generic `Exception`
- Always log errors before raising
- Example:
```python
class SchedulingError(Exception):
    """Base exception for scheduling errors"""
    pass

def validate_schedule(schedule):
    if not schedule.employee_id:
        logger.error(f"Schedule {schedule.id} missing employee")
        raise SchedulingError("Employee ID required")
```

### Database Queries
- Use **SQLAlchemy ORM** (avoid raw SQL)
- Always use **sessions properly** (context managers or explicit close)
- **Filter on indexes** for performance
- Example:
```python
# GOOD
schedules = db.session.query(Schedule).filter(
    Schedule.schedule_datetime >= start_date,
    Schedule.schedule_datetime < end_date
).order_by(Schedule.schedule_datetime).all()

# BAD - raw SQL
db.session.execute("SELECT * FROM schedules WHERE ...")
```

### Flask Routes
- Use **blueprints** for organization
- **One blueprint per feature area**
- Route naming: `/noun/verb` (e.g., `/schedule/create`)
- Use **decorators** for auth/validation

### Testing
- **Unit tests** for all business logic
- **Integration tests** for API endpoints
- **Test file naming**: `test_<module_name>.py`
- **Pytest** as test framework
- Example:
```python
def test_schedule_event_success():
    """Test successful event scheduling"""
    event = create_test_event()
    employee = create_test_employee()
    result = schedule_event(event.id, employee.id, datetime.now())
    assert result is True
```

### Security
- **Never** hardcode credentials
- Use environment variables for secrets
- **Always validate** user input
- Use **parameterized queries** (SQLAlchemy handles this)
- **CSRF protection** on all state-changing endpoints

### Logging
- Use **Python logging module**
- Log levels:
  - `DEBUG`: Detailed diagnostic info
  - `INFO`: General information
  - `WARNING`: Warning messages
  - `ERROR`: Error messages
  - `CRITICAL`: Critical errors
- Example:
```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"Scheduling event {event_id} for employee {employee_id}")
logger.error(f"Failed to schedule event: {str(e)}")
```

### Comments
- Code should be **self-documenting**
- Add comments for **complex logic only**
- Use `TODO:`, `FIXME:`, `NOTE:` tags
- Example:
```python
# TODO: Refactor this function - too complex
# FIXME: Handle timezone conversion properly
# NOTE: This uses rotation algorithm from scheduling_engine
```

## Flask-Specific Standards

### Application Factory Pattern
- Use `create_app()` function
- Initialize extensions within factory
- Example:
```python
def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    db.init_app(app)
    csrf.init_app(app)
    # ...

    return app
```

### Blueprint Registration
- Register blueprints in `app.py`
- Use URL prefixes for namespacing
- Document which endpoints are CSRF-exempt and why

### Configuration
- Use `config.py` with environment-based classes
- Load secrets from environment variables
- Never commit `.env` files

## Code Review Checklist
- [ ] Follows PEP 8 style guide
- [ ] Has type hints
- [ ] Has docstrings
- [ ] Has unit tests
- [ ] No hardcoded credentials
- [ ] Proper error handling
- [ ] Logged appropriately
- [ ] No security vulnerabilities

## Tools
- **Linter**: `flake8` or `pylint`
- **Formatter**: `black` (line length 100)
- **Type checker**: `mypy`
- **Test runner**: `pytest`

## References
- [PEP 8 - Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Flask Best Practices](https://flask.palletsprojects.com/en/2.3.x/patterns/)
```

### File 2: tech-stack.md

Create comprehensive technology stack documentation with versions, rationale, and alternatives.

### File 3: source-tree.md

Document complete directory structure with purpose of each folder/file.

## Task Breakdown

### For PM Agent (John)
1. **Create document structure** (2 hours)
   - Set up all three markdown files
   - Create initial outline for each
   - Define sections and subsections

2. **Write business context** (2 hours)
   - Explain architectural decisions
   - Document technology choices rationale
   - Add diagrams where helpful

3. **Review with stakeholders** (1 hour)
   - Get feedback on structure
   - Validate completeness

### For Dev Agent (James)
1. **Add technical details** (4 hours)
   - Fill in coding conventions from codebase analysis
   - Document actual tech stack versions
   - Map source tree accurately

2. **Add code examples** (2 hours)
   - Extract real examples from codebase
   - Create snippets for best practices
   - Add anti-patterns to avoid

3. **Technical review** (1 hour)
   - Verify accuracy
   - Check for completeness
   - Test code examples

## Dependencies
- None (standalone task)

## Estimated Effort
⏱️ **12-16 hours** (1.5-2 days)
- PM Agent (John): 5 hours
- Dev Agent (James): 7 hours
- Review & revisions: 2-4 hours

## Success Metrics
- [ ] Dev Agent successfully loads files on activation
- [ ] New developers can onboard using these docs
- [ ] Code reviews reference standards consistently
- [ ] Tech stack is clear to all stakeholders

## Future Enhancements
- Add ADR (Architecture Decision Records) section
- Create visual architecture diagrams
- Document API design standards
- Add database schema documentation

---
**Created**: 2025-01-09
**Last Updated**: 2025-01-09
**Reporter**: Quinn (QA Agent)
