# Employee Management Enhancement - Architecture

**Project:** flask-schedule-webapp
**Focus:** Manual Add + Crossmark API Import with Selective Import
**Author:** Elliot
**Date:** 2025-11-20
**Architecture Type:** Brownfield Enhancement

---

## Executive Summary

This architecture defines the solution design for fixing employee management functionality in the existing Flask scheduling webapp. The enhancement adds reliable manual employee creation and implements Crossmark API import with intelligent duplicate prevention and user-controlled selection. This unblocks the auto-scheduler by ensuring MV Retail employee numbers are properly captured from the Crossmark API.

**Architectural Approach:** Extend existing Flask patterns, reuse established integration layers, and add focused service logic for import operations. Minimal disruption to existing system with maximum reliability.

**Key Principles:**
- Reuse existing Flask blueprint structure and conventions
- Leverage existing Crossmark API session management
- Implement service layer for business logic separation
- Database-level duplicate detection for performance
- Atomic operations for data integrity

---

## Decision Summary

| Category | Decision | Version/Pattern | Affects FRs | Rationale |
|----------|----------|----------------|-------------|-----------|
| Route Structure | Extend existing /employees blueprint | app/routes/employees.py | FR1, FR9 | Keeps employee operations cohesive, brownfield-friendly |
| Database Schema | Add fields to Employee model | mv_retail_employee_number, crossmark_employee_id | FR28, FR37 | Direct fields simpler than separate table, faster queries |
| Service Layer | New employee_import_service.py | app/services/ | FR10-FR27 | Centralizes import logic, improves testability |
| Duplicate Detection | Database-level ILIKE query | SQLAlchemy func.lower() | FR5, FR13-FR16 | Leverages PostgreSQL, efficient, index-friendly |
| API Integration | Reuse existing session_api_service | app/integrations/external_api/ | FR10, FR38 | Proven integration layer, maintains consistency |
| Import UI | Server-rendered Jinja2 template | employees/import_select.html | FR18-FR24 | Consistent with existing UI patterns |
| Form Handling | WTForms for validation | Flask-WTF | FR1-FR8 | Matches existing form patterns, CSRF protection |
| Error Handling | Flask flash messages + logging | Existing pattern | FR32-FR36 | Consistent user feedback mechanism |
| Transaction Management | SQLAlchemy session with explicit commits | Existing pattern | NFR-R4 | Ensures atomic operations |
| API Response Parsing | Pydantic models for validation | Pydantic 2.x | FR12 | Type-safe API response handling |

---

## Project Structure

### Files to Create

```
flask-schedule-webapp/
├── app/
│   ├── services/
│   │   └── employee_import_service.py          # NEW - Import business logic
│   ├── routes/
│   │   └── employees.py                        # MODIFY - Add import routes
│   ├── models/
│   │   └── employee.py                         # MODIFY - Add new fields
│   ├── templates/
│   │   └── employees/
│   │       ├── import_select.html              # NEW - Selection interface
│   │       └── add_employee.html               # MODIFY - Fix manual add form
│   ├── static/
│   │   └── js/
│   │       └── employee_import.js              # NEW - Checkbox handling
│   └── integrations/
│       └── external_api/
│           └── session_api_service.py          # EXISTING - Reuse
├── migrations/
│   └── versions/
│       └── add_employee_import_fields.py       # NEW - Alembic migration
└── tests/
    ├── services/
    │   └── test_employee_import_service.py     # NEW - Service tests
    └── routes/
        └── test_employees.py                    # MODIFY - Add import tests
```

### Files to Modify

```
app/routes/employees.py
  - Add route: @bp.route('/import-crossmark', methods=['GET', 'POST'])
  - Add route: @bp.route('/import-crossmark/select', methods=['POST'])
  - Fix route: @bp.route('/add', methods=['GET', 'POST'])

app/models/employee.py
  - Add field: mv_retail_employee_number = Column(String(50), nullable=True)
  - Add field: crossmark_employee_id = Column(String(50), nullable=True, unique=True)
  - Add index: Index('ix_employee_name_lower', func.lower(name))

app/templates/employees/add_employee.html
  - Fix form validation
  - Add duplicate error display
  - Add tooltip for MV Retail # field
```

---

## FR Category to Architecture Mapping

| FR Category | Architecture Components | Implementation Location |
|-------------|------------------------|------------------------|
| **Manual Employee Addition (FR1-FR8)** | Route handler, WTForm, duplicate check service method | `app/routes/employees.py:add_employee()`<br>`app/services/employee_import_service.py:check_duplicate_name()` |
| **Crossmark API Import (FR9-FR27)** | Import service, API client wrapper, selection UI | `app/services/employee_import_service.py`<br>`app/integrations/external_api/session_api_service.py`<br>`app/templates/employees/import_select.html` |
| **Data Integrity (FR28-FR31)** | Employee model fields, database constraints | `app/models/employee.py`<br>Database migration |
| **Error Handling & Feedback (FR32-FR36)** | Flash messages, exception handling, logging | Flask flash()<br>`app/routes/employees.py` error handlers |
| **System Integration (FR37-FR40)** | Existing blueprint registration, model registry | Existing Flask infrastructure |

---

## Technology Stack Details

### Core Technologies (Existing - Reuse)

| Technology | Version | Purpose |
|------------|---------|---------|
| Flask | 3.0.3 | Web framework |
| SQLAlchemy | 3.1.1 | ORM and database operations |
| Alembic | Latest | Database migrations |
| Jinja2 | Latest (Flask bundled) | Server-side templating |
| PostgreSQL | Latest stable | Production database |
| SQLite | Latest | Development database |
| Python | 3.11+ | Runtime |

### New Dependencies to Add

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Pydantic | 2.x (latest) | API response validation | Type-safe parsing of Crossmark API responses |
| Flask-WTF | Latest | Form handling | If not already installed - CSRF + validation |

### Verification Commands

```bash
# Verify current versions
python --version  # Should be 3.11+
flask --version   # Should be 3.0.3
pip show sqlalchemy  # Should be 3.1.1

# Install new dependencies (if needed)
pip install pydantic>=2.0
pip install flask-wtf  # If not present
```

---

## Integration Points

### 1. Crossmark API Integration

**Endpoint:** `POST https://crossmark.mvretail.com/schedulingcontroller/getAvailableReps`

**Request Format:**
```python
# multipart/form-data
{
    "project": "MM/DD/YYYY HH:MM:SS,MM/DD/YYYY HH:MM:SS"  # Date range
}
```

**Response Format (Pydantic Model):**
```python
from pydantic import BaseModel
from typing import Optional

class CrossmarkEmployee(BaseModel):
    id: str                          # MV Retail employee number (repId)
    repId: str                       # Also MV Retail number (use this as primary)
    employeeId: str                  # Crossmark employee ID
    repMvid: str                     # Same as employeeId
    title: str                       # Full employee name
    lastName: str
    nameSort: str
    availableHoursPerDay: str
    scheduledHours: str
    visitCount: str
    role: Optional[str] = None
```

**Integration Layer:**
```python
# Use existing: app/integrations/external_api/session_api_service.py
# Add method: fetch_available_employees(date_range) -> List[CrossmarkEmployee]
```

### 2. Database Integration

**Employee Model Extensions:**
```python
class Employee(db.Model):
    __tablename__ = 'employees'

    # Existing fields...
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    role = db.Column(db.String(50))
    status = db.Column(db.String(20))

    # NEW FIELDS
    mv_retail_employee_number = db.Column(db.String(50), nullable=True, index=True)
    crossmark_employee_id = db.Column(db.String(50), nullable=True, unique=True)

    # Existing availability fields...

    # Index for case-insensitive name lookups
    __table_args__ = (
        db.Index('ix_employee_name_lower', func.lower(name)),
    )
```

### 3. UI Integration

**Manual Add Form Flow:**
```
Employees Page → "Add Employee" button
  → employees/add (GET) → Render form
  → employees/add (POST) → Validate → Check duplicate → Save or Error
  → Redirect to Employees list with flash message
```

**Import Flow:**
```
Employees Page → "Import from Crossmark" button
  → /employees/import-crossmark (GET) → Fetch API → Filter duplicates
  → /employees/import-crossmark/select (POST with selections)
  → Render import_select.html template
  → User checks boxes → Submit
  → /employees/import-crossmark/select (POST) → Bulk import
  → Redirect to Employees list with success count
```

---

## Implementation Patterns

### Naming Conventions

**Routes:**
- Manual add: `/employees/add` (existing, fix)
- Import initiate: `/employees/import-crossmark` (new)
- Import execute: `/employees/import-crossmark/import` (new POST endpoint)

**Functions:**
```python
# Service layer
def fetch_crossmark_employees() -> List[CrossmarkEmployee]:
def filter_duplicate_employees(api_employees: List[CrossmarkEmployee], existing_employees: List[Employee]) -> List[CrossmarkEmployee]:
def check_duplicate_name(name: str) -> Optional[Employee]:
def bulk_import_employees(selected_employees: List[CrossmarkEmployee]) -> int:

# Route handlers
@employees_bp.route('/add', methods=['GET', 'POST'])
def add_employee():

@employees_bp.route('/import-crossmark', methods=['GET'])
def import_crossmark_init():

@employees_bp.route('/import-crossmark/import', methods=['POST'])
def import_crossmark_execute():
```

**Database Fields:**
- Snake_case: `mv_retail_employee_number`, `crossmark_employee_id`
- Follow existing Employee model conventions

**Template Names:**
- `employees/import_select.html` (new selection interface)
- `employees/add_employee.html` (existing, modify)

### Code Organization Patterns

**Service Layer Pattern:**
```python
# app/services/employee_import_service.py
from typing import List, Optional
from app.models import Employee
from app.integrations.external_api.session_api_service import SessionAPIService
from pydantic import BaseModel
from sqlalchemy import func
from app import db

class EmployeeImportService:
    """Handles employee import and duplicate detection logic."""

    @staticmethod
    def check_duplicate_name(name: str) -> Optional[Employee]:
        """Check if employee name exists (case-insensitive)."""
        return Employee.query.filter(
            func.lower(Employee.name) == func.lower(name)
        ).first()

    @staticmethod
    def fetch_crossmark_employees() -> List[CrossmarkEmployee]:
        """Fetch employees from Crossmark API."""
        # Implementation using session_api_service
        pass

    @staticmethod
    def filter_duplicate_employees(
        api_employees: List[CrossmarkEmployee],
        existing_employees: List[Employee]
    ) -> tuple[List[CrossmarkEmployee], List[Employee]]:
        """
        Filter out duplicates, identify name casing updates.
        Returns: (new_employees, employees_to_update_casing)
        """
        pass

    @staticmethod
    def bulk_import_employees(selected_employees: List[CrossmarkEmployee]) -> int:
        """Import selected employees with default values."""
        pass
```

**Route Handler Pattern:**
```python
# app/routes/employees.py
from app.services.employee_import_service import EmployeeImportService
from flask import render_template, redirect, url_for, flash, request

@employees_bp.route('/import-crossmark', methods=['GET'])
@login_required
def import_crossmark_init():
    """Fetch employees from Crossmark and show selection interface."""
    try:
        # Fetch from API
        api_employees = EmployeeImportService.fetch_crossmark_employees()

        # Filter duplicates
        new_employees, _ = EmployeeImportService.filter_duplicate_employees(
            api_employees,
            Employee.query.all()
        )

        if not new_employees:
            flash('No new employees to import. All Crossmark employees are already in your roster.', 'info')
            return redirect(url_for('employees.index'))

        # Render selection template
        return render_template(
            'employees/import_select.html',
            employees=new_employees,
            count=len(new_employees)
        )

    except Exception as e:
        current_app.logger.error(f"Import fetch failed: {str(e)}")
        flash('Failed to fetch employees from Crossmark. Please try again.', 'error')
        return redirect(url_for('employees.index'))
```

### Error Handling Pattern

**Consistent Error Handling:**
```python
# All route handlers follow this pattern
try:
    # Business logic
    result = service_method()
    flash('Success message', 'success')
    return redirect(url_for('target'))

except APIAuthenticationError as e:
    current_app.logger.error(f"Auth error: {str(e)}")
    flash('Session expired. Please log in again.', 'error')
    return redirect(url_for('auth.login'))

except APINetworkError as e:
    current_app.logger.error(f"Network error: {str(e)}")
    flash('Unable to connect to Crossmark API. Please try again.', 'error')
    return redirect(url_for('employees.index'))

except Exception as e:
    current_app.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
    flash('An unexpected error occurred. Please contact support.', 'error')
    return redirect(url_for('employees.index'))
```

### Duplicate Detection Pattern

**Case-Insensitive Name Matching:**
```python
# PostgreSQL: Use ILIKE or func.lower()
def check_duplicate_name(name: str) -> Optional[Employee]:
    """Check if employee name exists (case-insensitive)."""
    return db.session.query(Employee).filter(
        func.lower(Employee.name) == func.lower(name)
    ).first()

# Usage in manual add
existing = EmployeeImportService.check_duplicate_name(form.name.data)
if existing:
    flash(f"Employee '{form.name.data}' already exists", 'error')
    return render_template('employees/add_employee.html', form=form)

# Usage in import filtering
def filter_duplicate_employees(api_employees, existing_employees):
    # Build lowercase name map for O(n) lookup
    existing_names_lower = {e.name.lower(): e for e in existing_employees}

    new_employees = []
    employees_to_update = []

    for api_emp in api_employees:
        api_name_lower = api_emp.title.lower()

        if api_name_lower in existing_names_lower:
            existing_emp = existing_names_lower[api_name_lower]
            # Check if casing differs
            if existing_emp.name != api_emp.title:
                employees_to_update.append((existing_emp, api_emp.title))
        else:
            new_employees.append(api_emp)

    return new_employees, employees_to_update
```

### Transaction Pattern

**Atomic Bulk Import:**
```python
def bulk_import_employees(selected_employees: List[CrossmarkEmployee]) -> int:
    """Import selected employees atomically."""
    try:
        imported_count = 0

        for api_emp in selected_employees:
            employee = Employee(
                name=api_emp.title,
                mv_retail_employee_number=api_emp.repId,
                crossmark_employee_id=api_emp.employeeId,
                role='Event Specialist',
                status='Inactive',
                # Availability defaults to None/empty
            )
            db.session.add(employee)
            imported_count += 1

        # Commit all or nothing
        db.session.commit()
        return imported_count

    except Exception as e:
        db.session.rollback()
        raise ImportError(f"Failed to import employees: {str(e)}")
```

---

## Consistency Rules

### 1. Flash Message Categories
```python
# Success
flash('7 employees imported successfully', 'success')

# Error
flash("Employee 'John Smith' already exists", 'error')

# Info
flash('No new employees to import', 'info')

# Warning
flash('Some employees could not be imported', 'warning')
```

### 2. Logging Format
```python
# Use current_app.logger with consistent format
current_app.logger.info(f"Importing {count} employees from Crossmark")
current_app.logger.error(f"Import failed: {error_message}", exc_info=True)
current_app.logger.warning(f"Duplicate detected: {employee_name}")
```

### 3. Date/Time Handling
```python
# Use existing timezone settings (America/Indiana/Indianapolis)
# Format for Crossmark API: "MM/DD/YYYY HH:MM:SS"
from datetime import datetime, timedelta

def get_crossmark_date_range():
    """Get date range for Crossmark API request."""
    now = datetime.now()
    week_ahead = now + timedelta(days=7)
    return f"{now.strftime('%m/%d/%Y %H:%M:%S')},{week_ahead.strftime('%m/%d/%Y %H:%M:%S')}"
```

### 4. Form Validation Messages
```python
# WTForms validators
from wtforms import StringField, validators

name = StringField('Name', [
    validators.DataRequired(message='Name is required'),
    validators.Length(min=2, max=200, message='Name must be between 2 and 200 characters')
])
```

### 5. Template Variable Naming
```python
# Route handlers pass consistent variable names to templates
return render_template(
    'employees/import_select.html',
    employees=new_employees,          # List of employees
    count=len(new_employees),         # Integer count
    form=form                         # WTForm instance (if applicable)
)
```

---

## Data Architecture

### Database Migration

**Alembic Migration Script:**
```python
# migrations/versions/XXXX_add_employee_import_fields.py
"""Add MV Retail and Crossmark ID fields to employees

Revision ID: <generated>
Revises: <previous>
Create Date: 2025-11-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import func

revision = '<generated>'
down_revision = '<previous>'
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns
    op.add_column('employees',
        sa.Column('mv_retail_employee_number', sa.String(50), nullable=True))
    op.add_column('employees',
        sa.Column('crossmark_employee_id', sa.String(50), nullable=True))

    # Add index for case-insensitive name lookups
    op.create_index(
        'ix_employee_name_lower',
        'employees',
        [sa.text('lower(name)')],
        unique=False
    )

    # Add unique constraint on crossmark_employee_id
    op.create_index(
        'ix_employee_crossmark_id',
        'employees',
        ['crossmark_employee_id'],
        unique=True
    )

def downgrade():
    op.drop_index('ix_employee_crossmark_id', table_name='employees')
    op.drop_index('ix_employee_name_lower', table_name='employees')
    op.drop_column('employees', 'crossmark_employee_id')
    op.drop_column('employees', 'mv_retail_employee_number')
```

### Employee Model Relationships

**No new relationships needed** - Enhancement adds fields to existing Employee model but doesn't change relationships with:
- Assignments
- Availability
- TimeOff
- Attendance
- Events (through assignments)

---

## API Contracts

### Internal API: Employee Import Service

```python
class EmployeeImportService:
    """
    Service for managing employee import operations.

    Methods:
        check_duplicate_name(name: str) -> Optional[Employee]
        fetch_crossmark_employees() -> List[CrossmarkEmployee]
        filter_duplicate_employees(...) -> tuple[List, List]
        bulk_import_employees(...) -> int
    """

    @staticmethod
    def check_duplicate_name(name: str) -> Optional[Employee]:
        """
        Check if employee name exists (case-insensitive).

        Args:
            name: Employee name to check

        Returns:
            Employee instance if duplicate found, None otherwise
        """
        pass

    @staticmethod
    def fetch_crossmark_employees() -> List[CrossmarkEmployee]:
        """
        Fetch employees from Crossmark API for current time range.

        Returns:
            List of CrossmarkEmployee instances

        Raises:
            APIAuthenticationError: If session invalid
            APINetworkError: If network failure
        """
        pass

    @staticmethod
    def filter_duplicate_employees(
        api_employees: List[CrossmarkEmployee],
        existing_employees: List[Employee]
    ) -> tuple[List[CrossmarkEmployee], List[tuple[Employee, str]]]:
        """
        Filter out duplicate employees, identify casing updates.

        Args:
            api_employees: Employees from Crossmark API
            existing_employees: Current employees in database

        Returns:
            Tuple of (new_employees, employees_needing_casing_update)
        """
        pass

    @staticmethod
    def bulk_import_employees(selected_employees: List[CrossmarkEmployee]) -> int:
        """
        Import selected employees with default values.

        Args:
            selected_employees: Employees to import

        Returns:
            Count of successfully imported employees

        Raises:
            ImportError: If transaction fails
        """
        pass
```

### External API: Crossmark Integration

```python
# Add to: app/integrations/external_api/session_api_service.py

def fetch_available_reps(self, date_range: str) -> dict:
    """
    Fetch available employees from Crossmark API.

    Args:
        date_range: "MM/DD/YYYY HH:MM:SS,MM/DD/YYYY HH:MM:SS"

    Returns:
        JSON response as dict

    Raises:
        requests.exceptions.RequestException: Network errors
        ValueError: Invalid response format
    """
    endpoint = f"{self.base_url}/schedulingcontroller/getAvailableReps"

    # Use multipart/form-data
    data = {'project': date_range}

    response = self.session.post(endpoint, data=data)
    response.raise_for_status()

    return response.json()
```

---

## Security Architecture

### Authentication
- **Reuse existing:** Flask-Login session management
- **Requirement:** All import/add endpoints require `@login_required` decorator
- **Session validation:** Crossmark API calls use existing session from `session_api_service`

### Authorization
- **Current pattern:** Role-based access (existing in system)
- **No changes needed:** Employee management already restricted to authenticated users

### CSRF Protection
```python
# WTForms provides CSRF protection automatically
from flask_wtf import FlaskForm

class AddEmployeeForm(FlaskForm):
    # CSRF token automatically included
    name = StringField('Name', validators=[DataRequired()])
    # ... other fields
```

### Data Protection
- **In transit:** HTTPS enforced (existing configuration)
- **At rest:** Database encryption (existing PostgreSQL configuration)
- **API credentials:** Environment variables (existing pattern in `.env`)

### Input Validation
```python
# Server-side validation ALWAYS enforced
# Client-side validation for UX only

# Manual add form
if form.validate_on_submit():
    # Validation passed
    pass
else:
    # Show errors from form.errors

# API response validation
try:
    employees = [CrossmarkEmployee(**emp) for emp in api_response]
except ValidationError as e:
    # Pydantic validation failed
    raise ValueError(f"Invalid API response: {str(e)}")
```

---

## Performance Considerations

### NFR-P1: Manual Add (<2 seconds)
**Strategy:**
- Single database query for duplicate check
- Immediate commit (no batch processing needed)
- Index on `func.lower(name)` for fast duplicate lookup

### NFR-P2: API Fetch (<10 seconds)
**Strategy:**
- Existing Crossmark integration handles timeout
- No additional optimization needed
- Loading spinner provides user feedback during wait

### NFR-P3: Selection UI (1000 employees responsive)
**Strategy:**
- Server-side rendering (no heavy client JavaScript)
- Simple table with checkboxes
- "Select All" uses vanilla JS `querySelectorAll`
- No pagination needed for 1000 rows (acceptable for admin interface)

### NFR-P4: Bulk Import (<5 seconds for 100 employees)
**Strategy:**
- Single transaction with bulk insert
- SQLAlchemy `session.add_all()` for batch efficiency
- No individual commits per employee

### NFR-P5: Duplicate Detection (<500ms for 10k employees)
**Strategy:**
- Database index on `lower(name)` enables fast lookups
- In-memory filtering during import uses hash map (O(n) complexity)
- PostgreSQL query optimizer handles efficiently

**Performance Monitoring:**
```python
import time

def bulk_import_employees(selected_employees):
    start_time = time.time()

    try:
        # Import logic
        db.session.commit()

        elapsed = time.time() - start_time
        current_app.logger.info(f"Imported {count} employees in {elapsed:.2f}s")

        return count
    except Exception as e:
        db.session.rollback()
        raise
```

---

## Deployment Architecture

### Database Migration Steps

```bash
# 1. Create migration
flask db migrate -m "Add MV Retail and Crossmark ID fields to employees"

# 2. Review generated migration script
# Check: migrations/versions/XXXX_add_mv_retail_and_crossmark_id_fields.py

# 3. Apply migration
flask db upgrade

# 4. Verify
flask shell
>>> from app.models import Employee
>>> from sqlalchemy import inspect
>>> inspector = inspect(Employee)
>>> [c.name for c in inspector.columns]
# Should include: 'mv_retail_employee_number', 'crossmark_employee_id'
```

### Deployment Checklist

1. **Pre-deployment:**
   - [ ] Review and test migration script locally
   - [ ] Back up production database
   - [ ] Test import flow on staging with real Crossmark API

2. **Deployment:**
   - [ ] Deploy code changes
   - [ ] Run `flask db upgrade` on production
   - [ ] Restart Flask application (Gunicorn workers)
   - [ ] Verify employee model has new fields

3. **Post-deployment:**
   - [ ] Test manual employee add
   - [ ] Test Crossmark import with small batch
   - [ ] Monitor logs for errors
   - [ ] Verify auto-scheduler can access MV Retail numbers

### Rollback Plan

```bash
# If issues occur, rollback database migration
flask db downgrade -1

# Redeploy previous code version
git checkout <previous-commit>

# Restart application
sudo systemctl restart flask-scheduler
```

---

## Development Environment

### Prerequisites

```bash
# Existing prerequisites (already installed)
- Python 3.11+
- PostgreSQL (production) or SQLite (development)
- Redis (for Celery background tasks)
- Git

# New dependencies (if not present)
pip install pydantic>=2.0
pip install flask-wtf  # If not already installed
```

### Local Development Setup

```bash
# 1. Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate      # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run migration
flask db upgrade

# 4. Start development server
python wsgi.py

# 5. Access application
http://localhost:5000
```

### Testing Strategy

**Unit Tests:**
```python
# tests/services/test_employee_import_service.py
import pytest
from app.services.employee_import_service import EmployeeImportService
from app.models import Employee

class TestEmployeeImportService:
    def test_check_duplicate_name_case_insensitive(self, db_session):
        # Create employee with mixed case
        employee = Employee(name="John Smith")
        db_session.add(employee)
        db_session.commit()

        # Check with different case
        duplicate = EmployeeImportService.check_duplicate_name("JOHN SMITH")
        assert duplicate is not None
        assert duplicate.name == "John Smith"

    def test_filter_duplicate_employees(self, db_session):
        # Test filtering logic
        pass

    def test_bulk_import_employees_atomic(self, db_session):
        # Test rollback on failure
        pass
```

**Integration Tests:**
```python
# tests/routes/test_employees.py
def test_import_crossmark_route(client, auth):
    # Login
    auth.login()

    # Access import route
    response = client.get('/employees/import-crossmark')
    assert response.status_code == 200 or response.status_code == 302

    # Verify API call was made
    # (Mock Crossmark API for test)
```

**Manual Testing Checklist:**
```
Manual Add:
[ ] Add employee with unique name → Success
[ ] Add employee with duplicate name (exact case) → Error
[ ] Add employee with duplicate name (different case) → Error
[ ] Add employee with only Name field → Success
[ ] Add employee with all fields → Success

Import:
[ ] Import with no duplicates → Show all employees
[ ] Import with all duplicates → Show "no new employees" message
[ ] Import with mixed duplicates → Show only new employees
[ ] Select some employees → Import count matches selection
[ ] Select all → Import all
[ ] Deselect all → Button disabled
[ ] API network failure → Graceful error message
[ ] Session expired → Redirect to login
```

---

## Architecture Decision Records (ADRs)

### ADR-001: Extend Existing Employees Blueprint

**Context:** Need to add import functionality to employee management system.

**Decision:** Extend existing `app/routes/employees.py` blueprint rather than creating separate blueprint.

**Rationale:**
- Employee import is closely related to employee management
- Keeps all employee operations in one place
- Simpler for developers to find related code
- Brownfield enhancement - minimal structural changes

**Consequences:**
- `employees.py` file grows slightly larger
- All employee routes remain under `/employees` prefix
- Future employee features follow same pattern

---

### ADR-002: Database-Level Duplicate Detection

**Context:** Need efficient case-insensitive name matching for duplicate detection.

**Decision:** Use SQLAlchemy `func.lower()` with database index for duplicate checking.

**Rationale:**
- Leverages PostgreSQL's efficient string matching
- Database index on `lower(name)` provides fast lookups
- Meets NFR-P5 (<500ms for 10k employees)
- Database-agnostic approach (works with SQLite in dev too)

**Consequences:**
- Additional database index (minimal storage overhead)
- Consistent performance regardless of dataset size
- Standard SQL pattern, maintainable

---

### ADR-003: Service Layer for Business Logic

**Context:** Import logic involves multiple steps: API fetch, duplicate filtering, bulk insert.

**Decision:** Create dedicated `EmployeeImportService` class with static methods.

**Rationale:**
- Separates business logic from route handlers
- Improves testability (unit test service without HTTP)
- Reusable methods (duplicate check used by both manual add and import)
- Aligns with existing service layer pattern in codebase

**Consequences:**
- New file: `app/services/employee_import_service.py`
- Route handlers become thinner, easier to read
- Service methods can be tested independently

---

### ADR-004: Pydantic for API Response Validation

**Context:** Crossmark API returns complex JSON with multiple fields, some optional.

**Decision:** Use Pydantic models to validate and parse API responses.

**Rationale:**
- Type-safe parsing with automatic validation
- Self-documenting (model shows expected structure)
- Catches API contract changes early
- Modern Python best practice

**Consequences:**
- New dependency: `pydantic>=2.0`
- API response validation errors caught before processing
- Clear error messages if API structure changes

---

### ADR-005: Atomic Bulk Import with Rollback

**Context:** Importing multiple employees must be reliable (NFR-R4: atomic operations).

**Decision:** Use single SQLAlchemy transaction for all imports with explicit rollback on failure.

**Rationale:**
- Ensures data integrity - either all employees import or none
- Prevents partial imports that corrupt employee roster
- Meets NFR-R4 requirement
- Standard database transaction pattern

**Consequences:**
- Failure during import rolls back entire batch
- User sees clear "import failed" message, can retry
- No cleanup needed after failures

---

### ADR-006: Server-Rendered Selection Interface

**Context:** Users need to select employees from import list (FR18-FR24).

**Decision:** Use Jinja2 template with vanilla JavaScript for checkbox handling.

**Rationale:**
- Consistent with existing UI patterns (no frontend framework)
- Simple checkbox interactions don't require React/Vue
- Fast initial render with server-side templating
- Meets NFR-P3 (responsive with 1000 employees)

**Consequences:**
- New template: `employees/import_select.html`
- Simple JavaScript file for "Select All" functionality
- No build step or bundler needed

---

_Generated by BMAD Decision Architecture Workflow_
_Date: 2025-11-20_
_For: Elliot_
