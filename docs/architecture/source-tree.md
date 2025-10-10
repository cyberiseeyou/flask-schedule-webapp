# Source Tree - Flask Schedule Webapp

## Overview

This document provides a comprehensive guide to the Flask Schedule Webapp directory structure, explaining the purpose and responsibility of each directory and key files.

## Project Root Structure

```
flask-schedule-webapp/
├── scheduler_app/          # Main application package
├── docs/                   # Project documentation
├── tests/                  # Test suite (unit, integration, fixtures)
├── instance/               # Instance-specific files (database, configs)
├── migrations/             # Alembic database migrations
├── static/                 # Static assets (CSS, JS, images)
├── templates/              # Jinja2 HTML templates
├── .bmad-core/             # BMAD configuration
├── .env                    # Environment variables (NOT committed)
├── .env.example            # Environment variable template
├── .gitignore              # Git ignore rules
├── requirements.txt        # Python dependencies
├── requirements-dev.txt    # Development dependencies
├── app.py                  # Application entry point
├── config.py               # Configuration classes
└── README.md               # Project overview
```

## scheduler_app/ - Main Application Package

The core application package containing all business logic, routes, models, and services.

```
scheduler_app/
├── __init__.py                     # Package initialization
├── app.py                          # Application factory (create_app)
├── config.py                       # Configuration management
├── error_handlers.py               # Global error handlers
├── routes/                         # Flask Blueprint route handlers
├── services/                       # Business logic services
├── models/                         # SQLAlchemy database models
├── edr/                            # EDR (Event Data Report) integration
├── walmart_api/                    # Walmart Retail Link API
├── utils/                          # Utility functions and helpers
└── static/                         # Application-specific static files
```

### scheduler_app/app.py

**Purpose**: Application factory pattern implementation

**Key Responsibilities**:
- Creates and configures Flask application instance
- Initializes extensions (SQLAlchemy, CSRF, Migrate)
- Registers blueprints from routes/
- Sets up error handlers
- Configures logging
- Applies CSRF exemptions (10 blueprints currently)

**Key Functions**:
- `create_app(config_name=None)` - Application factory function

**Dependencies**:
- config.py for configuration classes
- All blueprints from routes/
- error_handlers.py for error handling

### scheduler_app/config.py

**Purpose**: Environment-based configuration management

**Key Responsibilities**:
- Load environment variables using python-decouple
- Define configuration classes (Development, Production, Testing)
- Manage database URIs
- Store API credentials and settings
- Configure Flask extensions

**Configuration Classes**:
- `BaseConfig` - Shared settings
- `DevelopmentConfig` - Local development settings
- `ProductionConfig` - Production deployment settings
- `TestingConfig` - Testing environment settings

**Key Functions**:
- `get_config(config_name=None)` - Returns appropriate config class

**Security Note**: Contains hardcoded credentials (CRITICAL-01) - needs immediate fix

### scheduler_app/error_handlers.py

**Purpose**: Centralized error handling for HTTP errors and exceptions

**Key Responsibilities**:
- Handle 404 Not Found errors
- Handle 500 Internal Server errors
- Handle 403 Forbidden errors
- Log errors appropriately
- Return user-friendly error pages

**Error Handlers**:
- `handle_404(e)` - Not Found handler
- `handle_500(e)` - Internal Server Error handler
- `handle_403(e)` - Forbidden handler

## scheduler_app/routes/ - Blueprint Route Handlers

Flask Blueprints organizing API endpoints by feature area.

```
scheduler_app/routes/
├── __init__.py                     # Route package initialization
├── auth.py                         # Authentication routes
├── api.py                          # General API endpoints
├── scheduling.py                   # Schedule management routes
├── employees.py                    # Employee CRUD operations
├── rotations.py                    # Rotation assignment routes
├── auto_scheduler.py               # Auto-scheduler trigger routes
├── admin.py                        # Admin panel routes (30K+ tokens - needs refactor)
├── printing.py                     # Print/PDF generation routes
├── walmart_api.py                  # Walmart API webhook routes
└── edr_sync.py                     # EDR synchronization routes
```

### Blueprint Structure

Each route file follows this pattern:

```python
from flask import Blueprint, request, jsonify

# Create blueprint
blueprint_name = Blueprint('name', __name__, url_prefix='/prefix')

# Define routes
@blueprint_name.route('/endpoint', methods=['GET', 'POST'])
def route_handler():
    """Route docstring"""
    # Route logic
    return jsonify(response)
```

### Route Responsibilities

**auth.py** - Authentication & Authorization
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `GET /auth/status` - Check authentication status

**api.py** - General API Endpoints
- Various utility endpoints
- Data retrieval operations
- Contains duplicate authentication logic (HIGH-02)

**scheduling.py** - Schedule Management
- `GET /api/schedules` - List schedules
- `POST /api/schedules` - Create schedule
- `PUT /api/schedules/<id>` - Update schedule
- `DELETE /api/schedules/<id>` - Delete schedule

**employees.py** - Employee Operations
- `GET /api/employees` - List employees
- `POST /api/employees` - Create employee
- `PUT /api/employees/<id>` - Update employee
- `DELETE /api/employees/<id>` - Delete employee
- Employee availability management
- Time-off request handling

**rotations.py** - Rotation Management
- `GET /api/rotations` - List rotation assignments
- `POST /api/rotations` - Create rotation
- `PUT /api/rotations/<id>` - Update rotation
- `DELETE /api/rotations/<id>` - Delete rotation

**auto_scheduler.py** - Automated Scheduling
- `POST /api/auto-schedule` - Trigger auto-scheduler
- `GET /api/auto-schedule/status` - Check scheduler status
- `GET /api/auto-schedule/history` - View scheduling history

**admin.py** - Administration (⚠️ CRITICAL-04)
- **SIZE**: 30,538 tokens (exceeds 25K limit)
- **STATUS**: Needs refactoring into smaller modules
- Settings management
- EDR sync operations
- System configuration
- Analytics and reporting

**printing.py** - Print & PDF Operations
- `GET /api/print/schedule/<id>` - Generate schedule PDF
- `GET /api/print/daily-paperwork/<date>` - Generate daily paperwork
- Barcode generation
- PDF assembly

**walmart_api.py** - Walmart Integration
- `POST /api/walmart/webhook` - External webhook (CSRF-exempt)
- Walmart Retail Link event processing

**edr_sync.py** - EDR Synchronization
- `POST /api/edr/sync` - Manual EDR sync trigger
- `GET /api/edr/cache/stats` - Cache statistics
- `POST /api/edr/cache/clear` - Clear cache
- Bulk data synchronization

### CSRF Protection Status

**Currently ALL blueprints are CSRF-exempt** (CRITICAL-02):
```python
# app.py lines 110-177
csrf.exempt(auth_bp)
csrf.exempt(scheduling_bp)
csrf.exempt(employees_bp)
csrf.exempt(api_bp)
csrf.exempt(rotations_bp)
csrf.exempt(auto_scheduler_bp)
csrf.exempt(admin_bp)
csrf.exempt(printing_bp)
csrf.exempt(walmart_bp)
csrf.exempt(edr_sync_bp)
```

**Action Required**: Review and implement CSRF protection (see CRITICAL-02 ticket)

## scheduler_app/services/ - Business Logic Services

Service layer containing core business logic, separated from route handlers.

```
scheduler_app/services/
├── __init__.py                         # Service package initialization
├── scheduling_engine.py                # Core auto-scheduler logic
├── rotation_manager.py                 # Employee rotation management
├── constraint_validator.py             # Scheduling constraint validation
├── conflict_resolver.py                # Schedule conflict resolution
├── edr_service.py                      # EDR integration service
├── daily_paperwork_generator.py        # Daily paperwork PDF generation (733 lines)
└── validation_types.py                 # Validation result types
```

### Service Descriptions

**scheduling_engine.py** - Auto-Scheduler Core
- **Responsibilities**:
  - Retrieve unscheduled events
  - Sort events by priority (due date, event type)
  - Assign employees based on rotation and availability
  - Handle Core, Juicer, and other event types
  - Create pending schedules for approval
- **Key Classes**:
  - `SchedulingEngine` - Main scheduler orchestrator
- **Key Methods**:
  - `run_auto_scheduler()` - Execute scheduling algorithm
  - `_schedule_core_event()` - Handle Core event logic
  - `_schedule_juicer_event()` - Handle Juicer event logic
  - `_get_available_employees()` - Find available staff
- **Dependencies**: RotationManager, ConstraintValidator, ConflictResolver
- **Status**: No unit tests (HIGH-01)

**rotation_manager.py** - Rotation Logic
- **Responsibilities**:
  - Manage employee rotation assignments
  - Determine primary/secondary leads by date
  - Handle rotation schedules
  - Track rotation history
- **Key Classes**:
  - `RotationManager`
- **Key Methods**:
  - `get_rotation_employee(date, rotation_type)` - Get assigned employee
  - `create_rotation_assignment()` - Create new rotation
  - `update_rotation_assignment()` - Update existing rotation
- **Status**: No unit tests (HIGH-01)

**constraint_validator.py** - Validation Rules
- **Responsibilities**:
  - Validate employee availability
  - Check time-off conflicts
  - Enforce Core event one-per-day rule
  - Validate weekly availability
  - Check job title requirements
- **Key Classes**:
  - `ConstraintValidator`
- **Key Methods**:
  - `validate_assignment(event, employee, datetime)` - Validate assignment
  - `_check_time_off()` - Time-off validation
  - `_check_availability()` - Weekly availability check
  - `_check_existing_schedules()` - Conflict detection
- **Returns**: `ValidationResult` with violations list
- **Status**: No unit tests (HIGH-01)

**conflict_resolver.py** - Conflict Resolution
- **Responsibilities**:
  - Detect scheduling conflicts
  - Suggest alternative times/employees
  - Resolve double-booking
  - Handle overlapping events
- **Key Classes**:
  - `ConflictResolver`
- **Status**: No unit tests (HIGH-01)

**edr_service.py** - EDR Integration
- **Responsibilities**:
  - Authenticate with Walmart Retail Link
  - Fetch event data from EDR API
  - Cache report data
  - Handle MFA authentication flow
- **Key Functions**:
  - `authenticate(username, password, mfa_code)` - Login to EDR
  - `fetch_event_data(event_id)` - Retrieve event data
  - `get_cached_report(event_id)` - Get cached report
- **External Dependencies**: Walmart Retail Link API
- **Status**: No unit tests (HIGH-01), no circuit breaker (HIGH-03)

**daily_paperwork_generator.py** - PDF Generation (733 lines)
- **Responsibilities**:
  - Generate consolidated daily paperwork packages
  - Fetch EDR reports for scheduled events
  - Create schedule sheets
  - Generate item lists with barcodes
  - Assemble multi-page PDFs
- **Key Functions**:
  - `generate_daily_paperwork(date)` - Main generation function
  - `_fetch_edr_reports()` - Get EDR PDFs
  - `_generate_schedule_sheet()` - Create schedule page
  - `_generate_barcode()` - Create barcode images
  - `_assemble_pdf()` - Combine all pages
- **Libraries Used**: ReportLab, PyPDF2, xhtml2pdf
- **Status**: No unit tests (HIGH-01)

**validation_types.py** - Type Definitions
- **Responsibilities**:
  - Define validation result types
  - Constraint violation types
  - Type hints for service layer
- **Key Types**:
  - `ValidationResult` - Validation outcome with violations
  - `ConstraintViolation` - Individual constraint violation

## scheduler_app/models/ - Database Models

SQLAlchemy ORM models representing database tables.

```
scheduler_app/models/
├── __init__.py                         # Model package initialization
├── employee.py                         # Employee model
├── event.py                            # Event model
├── schedule.py                         # Schedule model
├── rotation_assignment.py              # Rotation assignment model
├── scheduler_run_history.py            # Scheduler execution history
├── pending_schedule.py                 # Pending schedule approvals
├── employee_time_off.py                # Employee time-off requests
├── employee_weekly_availability.py     # Weekly availability patterns
└── system_setting.py                   # System configuration settings
```

### Model Descriptions

**employee.py** - Employee Model
```python
class Employee(db.Model):
    __tablename__ = 'employees'

    id = Column(String(50), primary_key=True)  # Employee ID
    name = Column(String(200), nullable=False)
    email = Column(String(200), unique=True)
    job_title = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_supervisor = Column(Boolean, default=False)
    adult_beverage_trained = Column(Boolean, default=False)
    hire_date = Column(Date)
    termination_date = Column(Date)

    # Relationships
    schedules = relationship('Schedule', back_populates='employee')
    time_off_requests = relationship('EmployeeTimeOff', back_populates='employee')
    weekly_availability = relationship('EmployeeWeeklyAvailability', back_populates='employee')
```

**event.py** - Event Model
```python
class Event(db.Model):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    project_name = Column(String(500), nullable=False)
    project_ref_num = Column(Integer, unique=True, nullable=False)
    event_type = Column(String(50))  # Core, Juicer, etc.
    start_datetime = Column(DateTime, nullable=False)
    due_datetime = Column(DateTime, nullable=False)
    is_scheduled = Column(Boolean, default=False)
    store_number = Column(String(10))
    store_name = Column(String(200))

    # Relationships
    schedules = relationship('Schedule', back_populates='event')
```

**schedule.py** - Schedule Model
```python
class Schedule(db.Model):
    __tablename__ = 'schedules'

    id = Column(Integer, primary_key=True)
    event_ref_num = Column(Integer, ForeignKey('events.project_ref_num'))
    employee_id = Column(String(50), ForeignKey('employees.id'))
    schedule_datetime = Column(DateTime, nullable=False)
    role = Column(String(50))  # Lead, Support, etc.
    status = Column(String(20), default='scheduled')  # scheduled, completed, cancelled

    # Relationships
    event = relationship('Event', back_populates='schedules')
    employee = relationship('Employee', back_populates='schedules')
```

**rotation_assignment.py** - Rotation Assignment Model
```python
class RotationAssignment(db.Model):
    __tablename__ = 'rotation_assignments'

    id = Column(Integer, primary_key=True)
    rotation_type = Column(String(50))  # primary_lead, secondary_lead, etc.
    employee_id = Column(String(50), ForeignKey('employees.id'))
    rotation_date = Column(Date, nullable=False)

    # Relationships
    employee = relationship('Employee')
```

**scheduler_run_history.py** - Scheduler History
```python
class SchedulerRunHistory(db.Model):
    __tablename__ = 'scheduler_run_history'

    id = Column(Integer, primary_key=True)
    run_type = Column(String(20))  # manual, automatic
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    status = Column(String(20))  # running, completed, failed
    events_processed = Column(Integer, default=0)
    events_scheduled = Column(Integer, default=0)
    events_failed = Column(Integer, default=0)
    error_message = Column(Text)
```

**pending_schedule.py** - Pending Approvals
```python
class PendingSchedule(db.Model):
    __tablename__ = 'pending_schedules'

    id = Column(Integer, primary_key=True)
    event_ref_num = Column(Integer, ForeignKey('events.project_ref_num'))
    employee_id = Column(String(50), ForeignKey('employees.id'))
    proposed_datetime = Column(DateTime, nullable=False)
    proposed_by = Column(String(100))  # 'auto_scheduler' or user ID
    created_at = Column(DateTime, default=datetime.utcnow)
    approved = Column(Boolean)
    approved_by = Column(String(100))
    approved_at = Column(DateTime)
```

**employee_time_off.py** - Time-Off Requests
```python
class EmployeeTimeOff(db.Model):
    __tablename__ = 'employee_time_off'

    id = Column(Integer, primary_key=True)
    employee_id = Column(String(50), ForeignKey('employees.id'))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(String(200))
    approved = Column(Boolean, default=False)

    # Relationships
    employee = relationship('Employee', back_populates='time_off_requests')
```

**employee_weekly_availability.py** - Availability Patterns
```python
class EmployeeWeeklyAvailability(db.Model):
    __tablename__ = 'employee_weekly_availability'

    id = Column(Integer, primary_key=True)
    employee_id = Column(String(50), ForeignKey('employees.id'))
    day_of_week = Column(Integer)  # 0=Monday, 6=Sunday
    start_time = Column(Time)
    end_time = Column(Time)
    is_available = Column(Boolean, default=True)

    # Relationships
    employee = relationship('Employee', back_populates='weekly_availability')
```

**system_setting.py** - System Settings
```python
class SystemSetting(db.Model):
    __tablename__ = 'system_settings'

    id = Column(Integer, primary_key=True)
    setting_key = Column(String(100), unique=True, nullable=False)
    setting_value = Column(Text)
    encrypted = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow)
```

### Model Status

**Missing Tests**: All models lack unit tests (HIGH-01)

**Recommended Enhancements**:
- Add indexes on frequently queried columns (MEDIUM-03)
- Add cascade delete rules
- Implement soft delete patterns
- Add created_at/updated_at timestamps consistently
- Add validation methods

## scheduler_app/edr/ - EDR Integration

EDR (Event Data Report) integration with Walmart Retail Link system.

```
scheduler_app/edr/
├── __init__.py                         # EDR package initialization
├── report_generator.py                 # Main EDR report fetcher (1,685 lines)
├── authentication.py                   # EDR authentication handler
└── cache_manager.py                    # Report caching system
```

### EDR Module Details

**report_generator.py** (1,685 lines)
- **Responsibilities**:
  - Authenticate with Walmart Retail Link EDR
  - Navigate EDR web interface
  - Download event reports as PDFs
  - Cache reports for offline access
  - Handle bulk synchronization
- **Key Functions**:
  - `get_edr_report(event_ref_num)` - Fetch single report
  - `bulk_sync_events(event_list)` - Sync multiple events
  - `get_cached_report(event_ref_num)` - Retrieve from cache
- **Authentication Flow**:
  1. Login with username/password
  2. Handle MFA challenge
  3. Extract authentication tokens
  4. Maintain session
- **Caching Strategy**:
  - Cache reports in `scheduler_app/edr/cache/`
  - Store metadata in `cached_reports` table
  - Invalidate cache after 7 days
- **External Dependencies**:
  - Walmart Retail Link EDR API
  - Selenium WebDriver (for JavaScript-heavy pages)
  - requests library for API calls
- **Security Issues**:
  - Hardcoded credentials in config.py (CRITICAL-01)
  - No circuit breaker for API failures (HIGH-03)

**authentication.py**
- **Responsibilities**:
  - Handle EDR login flow
  - Manage MFA authentication
  - Store and refresh authentication tokens
  - Handle session expiration
- **Key Functions**:
  - `authenticate(username, password, mfa_code)` - Complete auth flow
  - `refresh_token()` - Refresh expired tokens
  - `is_authenticated()` - Check auth status

**cache_manager.py**
- **Responsibilities**:
  - Manage report cache storage
  - Track cache expiration
  - Clean up old cache entries
  - Provide cache statistics
- **Key Functions**:
  - `cache_report(event_ref_num, pdf_data)` - Store report
  - `get_cached_report(event_ref_num)` - Retrieve report
  - `clear_old_cache(days=7)` - Remove old entries
  - `get_cache_stats()` - Cache usage statistics

## scheduler_app/walmart_api/ - Walmart API Integration

Integration with Walmart-specific APIs and webhooks.

```
scheduler_app/walmart_api/
├── __init__.py                         # Package initialization
├── webhook_handler.py                  # Process incoming webhooks
└── client.py                           # Walmart API client
```

### Walmart API Details

**webhook_handler.py**
- **Responsibilities**:
  - Receive Walmart event notifications
  - Validate webhook signatures
  - Process event updates
  - Trigger schedule updates
- **Endpoints**:
  - `POST /api/walmart/webhook` - Webhook receiver
- **Security**: CSRF-exempt (external webhook)

**client.py**
- **Responsibilities**:
  - Make API calls to Walmart services
  - Handle authentication
  - Format requests/responses
- **Status**: Needs circuit breaker (HIGH-03)

## scheduler_app/utils/ - Utility Functions

Shared utility functions and helpers.

```
scheduler_app/utils/
├── __init__.py                         # Utils package initialization
├── date_helpers.py                     # Date/time utilities
├── validation.py                       # Input validation functions
├── formatters.py                       # Data formatting helpers
└── decorators.py                       # Custom decorators
```

### Utility Modules

**date_helpers.py**
- Date parsing and formatting
- Timezone conversion
- Business day calculations
- Date range generation

**validation.py**
- Input validation functions
- Email validation
- Phone number formatting
- Data sanitization

**formatters.py**
- JSON response formatting
- Error message formatting
- Data serialization helpers

**decorators.py**
- Custom route decorators
- Authentication decorators (duplicate logic - HIGH-02)
- Rate limiting decorators
- Logging decorators

## docs/ - Documentation

Project documentation organized by type.

```
docs/
├── architecture/                       # Architecture documentation
│   ├── coding-standards.md             # Python/Flask coding standards
│   ├── tech-stack.md                   # Technology stack details
│   └── source-tree.md                  # This file
├── tickets/                            # Implementation tickets
│   ├── README.md                       # Ticket tracker
│   ├── CRITICAL-01-remove-hardcoded-credentials.md
│   ├── CRITICAL-02-review-csrf-exemptions.md
│   ├── CRITICAL-03-create-architecture-docs.md
│   ├── CRITICAL-04-refactor-admin-routes.md
│   ├── HIGH-01-implement-unit-tests.md
│   ├── HIGH-02-extract-duplicate-auth-logic.md
│   ├── HIGH-03-implement-circuit-breaker.md
│   ├── HIGH-04-add-comprehensive-docstrings.md
│   └── _BATCH_REMAINING_TICKETS.md
├── setup/                              # Setup guides
│   └── environment-variables.md        # Env var configuration
├── api/                                # API documentation
│   └── endpoints.md                    # API endpoint reference
└── QUALITY_REVIEW_SUMMARY.md           # QA review summary
```

### Documentation Standards

**Format**: GitHub-flavored Markdown
**Style**: Clear headings, code examples, links
**Required Sections**:
- Overview
- Purpose
- Implementation details
- Examples
- References

## tests/ - Test Suite

Test suite organized by test type (to be created - HIGH-01).

```
tests/
├── __init__.py                         # Test package initialization
├── conftest.py                         # Shared pytest fixtures
├── unit/                               # Unit tests
│   ├── services/                       # Service layer tests
│   │   ├── test_scheduling_engine.py
│   │   ├── test_rotation_manager.py
│   │   ├── test_constraint_validator.py
│   │   └── test_edr_service.py
│   └── models/                         # Model tests
│       ├── test_employee.py
│       ├── test_event.py
│       └── test_schedule.py
├── integration/                        # Integration tests
│   ├── test_api_routes.py
│   ├── test_scheduling_routes.py
│   └── test_admin_routes.py
└── fixtures/                           # Test data factories
    ├── employees.py                    # Employee factories
    ├── events.py                       # Event factories
    └── schedules.py                    # Schedule factories
```

### Test Organization

**Framework**: pytest with pytest-cov, pytest-mock, pytest-flask

**Test Types**:
- **Unit Tests**: Test individual functions/classes in isolation
- **Integration Tests**: Test API endpoints and database interactions
- **Fixtures**: Reusable test data using factory_boy

**Coverage Goal**: > 80% code coverage for services

**Status**: Not yet implemented (HIGH-01)

## migrations/ - Database Migrations

Alembic database migration scripts.

```
migrations/
├── alembic.ini                         # Alembic configuration
├── env.py                              # Migration environment
├── script.py.mako                      # Migration template
└── versions/                           # Migration versions
    ├── 001_initial_schema.py
    ├── 002_add_rotation_assignments.py
    ├── 003_add_employee_availability.py
    └── ...
```

### Migration Management

**Commands**:
```bash
# Create new migration
flask db migrate -m "description"

# Apply migrations
flask db upgrade

# Rollback migration
flask db downgrade

# View migration history
flask db history
```

## static/ - Static Assets

Frontend static files (CSS, JavaScript, images).

```
static/
├── css/                                # Stylesheets
│   ├── main.css                        # Main stylesheet
│   ├── schedule.css                    # Schedule page styles
│   └── admin.css                       # Admin panel styles
├── js/                                 # JavaScript files
│   ├── main.js                         # Core JavaScript
│   ├── schedule.js                     # Schedule management
│   ├── employees.js                    # Employee management
│   └── csrf_helper.js                  # CSRF token helper (to be added)
├── images/                             # Image assets
│   ├── logo.png
│   └── icons/
└── fonts/                              # Custom fonts
```

### Static Asset Status

**Missing**: CSRF helper JavaScript (CRITICAL-02)
**Recommendation**: Consider UX/UI review (MEDIUM-02)

## templates/ - HTML Templates

Jinja2 template files.

```
templates/
├── base.html                           # Base template
├── layout.html                         # Common layout
├── index.html                          # Home page
├── auth/                               # Authentication templates
│   ├── login.html
│   └── logout.html
├── schedule/                           # Schedule templates
│   ├── list.html
│   ├── create.html
│   └── edit.html
├── employees/                          # Employee templates
│   ├── list.html
│   ├── create.html
│   └── edit.html
├── admin/                              # Admin templates
│   ├── dashboard.html
│   ├── settings.html
│   └── edr_sync.html
└── errors/                             # Error pages
    ├── 404.html
    ├── 500.html
    └── 403.html
```

### Template Standards

**Base Template**: All pages extend `base.html`
**CSRF Tokens**: Must be added to all forms (CRITICAL-02)
**Status**: UX/UI review recommended (MEDIUM-02)

## instance/ - Instance Files

Instance-specific files (not committed to version control).

```
instance/
├── scheduler.db                        # SQLite database (development)
└── config.py                           # Instance-specific config overrides
```

**Note**: Production should use PostgreSQL, not SQLite

## .bmad-core/ - BMAD Configuration

BMAD (Blueprint Multi-Agent Development) configuration.

```
.bmad-core/
└── core-config.yaml                    # Agent configuration
```

**Key Configuration**:
```yaml
devLoadAlwaysFiles:
  - docs/architecture/coding-standards.md
  - docs/architecture/tech-stack.md
  - docs/architecture/source-tree.md
```

## Configuration Files

### .env (Not Committed)

Environment variables for local development.

**Location**: Project root
**Status**: Must be created from `.env.example`
**Contents**: Database URLs, API credentials, secrets

### .env.example (Template)

Template for environment variables.

**Location**: Project root
**Status**: Should be committed to repo
**Purpose**: Guide developers on required environment variables

### .gitignore

Git ignore rules.

**Key Entries**:
```
.env
*.env
.env.local
instance/
__pycache__/
*.pyc
*.pyo
*.db
venv/
.vscode/
.idea/
```

### requirements.txt

Python package dependencies for production.

**Key Dependencies**:
- Flask 3.0.0
- Flask-SQLAlchemy 3.1.1
- Flask-Migrate 4.0.5
- Flask-WTF 1.2.1
- requests 2.31.0
- ReportLab 4.0.7
- cryptography 41.0.0+

### requirements-dev.txt

Development dependencies (to be created - HIGH-01).

**Should Include**:
- pytest 7.4.3
- pytest-cov 4.1.0
- pytest-mock 3.12.0
- pytest-flask 1.3.0
- black (code formatter)
- flake8 (linter)
- mypy (type checker)

## Key File Locations

### Entry Points

| File | Purpose | Location |
|------|---------|----------|
| `app.py` | Application entry point | Project root |
| `scheduler_app/app.py` | Application factory | scheduler_app/ |
| `config.py` | Configuration | scheduler_app/ |

### Critical Files

| File | Purpose | Status |
|------|---------|--------|
| `scheduler_app/config.py` | Configuration | ⚠️ Contains hardcoded credentials |
| `scheduler_app/routes/admin.py` | Admin routes | ⚠️ 30K+ tokens - needs refactor |
| `scheduler_app/edr/report_generator.py` | EDR integration | ⚠️ No tests, no circuit breaker |
| `scheduler_app/services/scheduling_engine.py` | Auto-scheduler | ⚠️ No tests |

### Documentation Files

| File | Purpose | Status |
|------|---------|--------|
| `docs/architecture/coding-standards.md` | Coding conventions | ✅ Created |
| `docs/architecture/tech-stack.md` | Technology stack | ✅ Created |
| `docs/architecture/source-tree.md` | Directory structure | ✅ This file |
| `docs/QUALITY_REVIEW_SUMMARY.md` | QA review | ✅ Created |
| `docs/tickets/README.md` | Ticket tracker | ✅ Created |

## Navigation Guide

### For New Developers

**Start Here**:
1. Read `README.md` in project root
2. Review `docs/architecture/tech-stack.md` for technology overview
3. Read `docs/architecture/coding-standards.md` for conventions
4. Review this file (`source-tree.md`) for structure
5. Set up environment using `docs/setup/environment-variables.md`

### Finding Specific Code

**Routes/Endpoints**: Look in `scheduler_app/routes/<feature>.py`
**Business Logic**: Look in `scheduler_app/services/<feature>.py`
**Database Models**: Look in `scheduler_app/models/<model>.py`
**API Integration**: Look in `scheduler_app/edr/` or `scheduler_app/walmart_api/`
**Utilities**: Look in `scheduler_app/utils/<category>.py`

### Finding Documentation

**Architecture**: `docs/architecture/`
**Tickets/Issues**: `docs/tickets/`
**Setup Guides**: `docs/setup/`
**API Reference**: `docs/api/`

## File Naming Conventions

### Python Files

- **Modules**: `lowercase_with_underscores.py`
- **Classes**: Defined inside modules, use PascalCase
- **Tests**: `test_<module_name>.py`

### Documentation Files

- **Markdown**: `kebab-case-with-hyphens.md`
- **Tickets**: `PRIORITY-NN-short-description.md`

### Templates

- **HTML**: `lowercase.html`
- **Subdirectories**: Group by feature

### Static Files

- **CSS**: `lowercase.css`
- **JavaScript**: `lowercase.js`
- **Images**: `lowercase-with-hyphens.png/jpg`

## Import Patterns

### Absolute Imports (Preferred)

```python
# From routes
from scheduler_app.services.scheduling_engine import SchedulingEngine
from scheduler_app.models.employee import Employee

# From services
from scheduler_app.models.event import Event
from scheduler_app.utils.date_helpers import parse_date
```

### Relative Imports (Use Sparingly)

```python
# Within same package
from .rotation_manager import RotationManager
from ..models.schedule import Schedule
```

## Database Schema Location

**Schema Definition**: Defined in `scheduler_app/models/*.py` files
**Migrations**: Stored in `migrations/versions/`
**Database File** (dev): `instance/scheduler.db`

**View Schema**:
```bash
# Using Flask shell
flask shell
>>> from scheduler_app.models import db
>>> db.metadata.tables.keys()
```

## Common Development Tasks

### Adding a New Feature

1. **Create Model** (if needed): `scheduler_app/models/new_model.py`
2. **Create Migration**: `flask db migrate -m "Add new_model"`
3. **Create Service** (if needed): `scheduler_app/services/new_service.py`
4. **Create Routes**: `scheduler_app/routes/new_feature.py`
5. **Create Templates**: `templates/new_feature/*.html`
6. **Add Tests**: `tests/unit/services/test_new_service.py`
7. **Update Documentation**: Update relevant docs

### Debugging

**Application Logs**: Check console output or configured log files
**Database**: Use Flask shell or SQLite browser
**Routes**: Use `flask routes` command to list all endpoints
**Configuration**: Use `flask shell` and check `app.config`

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/services/test_scheduling_engine.py

# Run with coverage
pytest --cov=scheduler_app --cov-report=html
```

## Known Issues

### Critical Issues

1. **CRITICAL-01**: Hardcoded credentials in `scheduler_app/config.py:36-38`
2. **CRITICAL-02**: All blueprints CSRF-exempt in `scheduler_app/app.py:110-177`
3. **CRITICAL-03**: Architecture docs were missing (now complete)
4. **CRITICAL-04**: `scheduler_app/routes/admin.py` exceeds 30K tokens

### High Priority Issues

1. **HIGH-01**: No unit tests for services
2. **HIGH-02**: Duplicate authentication logic in `scheduler_app/routes/api.py`
3. **HIGH-03**: No circuit breaker for external APIs
4. **HIGH-04**: 100+ functions missing docstrings

**See**: `docs/tickets/README.md` for complete issue list

## Future Structure Improvements

### Recommended Changes

1. **Split admin.py**: Create `scheduler_app/routes/admin/` package with submodules
2. **Add tests/**: Implement complete test suite structure
3. **Add Repository Layer**: Create `scheduler_app/repositories/` for data access
4. **Add API Versioning**: Create `scheduler_app/routes/api/v1/` structure
5. **Add Celery Tasks**: Create `scheduler_app/tasks/` for background jobs
6. **Add Middleware**: Create `scheduler_app/middleware/` for custom middleware

### Scalability Considerations

**Current Structure**: Suitable for small-to-medium applications

**For Larger Scale**:
- Split services into domain-driven modules
- Implement CQRS pattern for read/write separation
- Add event sourcing for audit trails
- Implement API gateway pattern
- Add message queue for async processing

## References

- [Flask Project Layout](https://flask.palletsprojects.com/en/2.3.x/tutorial/layout/)
- [SQLAlchemy Models](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)
- [Blueprint Organization](https://flask.palletsprojects.com/en/2.3.x/blueprints/)
- [Test Structure](https://docs.pytest.org/en/stable/goodpractices.html)

---

**Last Updated**: 2025-01-09
**Maintained By**: Development Team
**Contact**: See project README for contact information
