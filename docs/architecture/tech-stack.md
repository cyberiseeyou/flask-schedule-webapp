# Technology Stack - Flask Schedule Webapp

## Overview
This document provides a comprehensive overview of all technologies, frameworks, libraries, and tools used in the Flask Schedule Webapp project.

**Last Updated**: 2025-01-09
**Python Version**: 3.11+
**Flask Version**: 3.0.0

---

## Table of Contents
- [Core Framework](#core-framework)
- [Database](#database)
- [API Integration](#api-integration)
- [PDF Generation](#pdf-generation)
- [Security](#security)
- [Task Queue](#task-queue)
- [Testing](#testing)
- [Development Tools](#development-tools)
- [External Services](#external-services)
- [Technology Decision Rationale](#technology-decision-rationale)

---

## Core Framework

### Flask 3.0.0
**Purpose**: Web application framework
**Why Flask?**
- Lightweight and flexible
- Excellent for small to medium applications
- Rich ecosystem of extensions
- Easy integration with SQLAlchemy

**Key Extensions**:
```python
Flask==3.0.0                    # Core web framework
Flask-SQLAlchemy==3.1.1        # Database ORM integration
Flask-Migrate==4.0.5           # Database migrations (Alembic wrapper)
Flask-WTF==1.2.1               # Form handling and CSRF protection
```

**Configuration**:
- Environment-based config (Development, Testing, Production)
- Blueprint-based route organization
- Application factory pattern

**Resources**:
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Flask Patterns](https://flask.palletsprojects.com/en/2.3.x/patterns/)

---

## Database

### SQLite (Development) / PostgreSQL (Production Recommended)
**Purpose**: Relational database management
**Current**: SQLite for development and lightweight deployments
**Recommended for Production**: PostgreSQL 14+

**ORM**: SQLAlchemy 2.0+
```python
Flask-SQLAlchemy==3.1.1         # Flask integration
alembic==1.16.5                 # Database migrations
```

**Why SQLAlchemy?**
- **Powerful ORM**: Pythonic database access
- **Migration Support**: Version-controlled schema changes via Alembic
- **Database Agnostic**: Easy to switch between SQLite and PostgreSQL
- **Query Flexibility**: Raw SQL when needed, ORM for most cases

**Database Models**:
- `Employee`: Staff member information and constraints
- `Event`: Schedulable events from external system
- `Schedule`: Assignment of employees to events
- `EmployeeWeeklyAvailability`: Recurring weekly availability
- `EmployeeTimeOff`: Specific date range unavailability
- `RotationAssignment`: Rotation-based scheduling (Juicer, Leads)
- `PendingSchedule`: Auto-scheduler proposals
- `SchedulerRunHistory`: Auto-scheduler execution logs
- `ScheduleException`: Schedule override rules
- `SystemSetting`: Application configuration storage

**Migrations**:
```bash
# Create migration
flask db migrate -m "Add new table"

# Apply migration
flask db upgrade

# Rollback migration
flask db downgrade
```

---

## API Integration

### Requests 2.31.0
**Purpose**: HTTP client for external API communication
**Usage**:
- Crossmark Session API integration
- Walmart Retail Link EDR API
- Third-party service communication

**Features Used**:
- Session management for authentication
- Timeout configuration
- Retry logic
- SSL certificate verification

**Example**:
```python
import requests

session = requests.Session()
response = session.post(
    'https://api.example.com/endpoint',
    json=data,
    timeout=30,
    headers={'Authorization': f'Bearer {token}'}
)
```

### Python Decouple 3.8
**Purpose**: Configuration management
**Why Decouple?**
- Separates config from code (12-Factor App)
- Environment variable management
- Type casting (string → int, bool, etc.)
- Default values support

**Usage**:
```python
from decouple import config

SECRET_KEY = config('SECRET_KEY')
DATABASE_URL = config('DATABASE_URL', default='sqlite:///app.db')
DEBUG = config('DEBUG', default=False, cast=bool)
TIMEOUT = config('API_TIMEOUT', default=30, cast=int)
```

---

## PDF Generation

### ReportLab 4.0.7
**Purpose**: PDF creation from scratch
**Usage**:
- Daily schedule printing
- Item number lists with barcodes
- Custom formatted reports

**Why ReportLab?**
- Programmatic PDF generation
- Full control over layout
- Barcode generation support
- Table formatting

**Example**:
```python
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph
from reportlab.lib.pagesizes import letter

doc = SimpleDocTemplate("report.pdf", pagesize=letter)
elements = [
    Paragraph("Daily Schedule", title_style),
    Table(data, colWidths=[2*inch, 3*inch, 1*inch])
]
doc.build(elements)
```

### PyPDF2 3.0.1
**Purpose**: PDF manipulation and merging
**Usage**:
- Merging multiple PDFs into daily paperwork package
- Extracting pages
- PDF metadata manipulation

**Example**:
```python
from PyPDF2 import PdfMerger

merger = PdfMerger()
merger.append('schedule.pdf')
merger.append('edr_report.pdf')
merger.append('checklist.pdf')
merger.write('daily_paperwork.pdf')
```

### xhtml2pdf >= 0.2.11
**Purpose**: HTML to PDF conversion
**Usage**:
- Converting EDR HTML reports to PDF
- Print-optimized styling

**Why xhtml2pdf?**
- Converts HTML/CSS directly to PDF
- Preserves styling
- No browser dependencies

**Example**:
```python
from xhtml2pdf import pisa
from io import BytesIO

def html_to_pdf(html_string):
    pdf_buffer = BytesIO()
    pisa.CreatePDF(BytesIO(html_string.encode('utf-8')), dest=pdf_buffer)
    return pdf_buffer.getvalue()
```

---

## Security

### Cryptography >= 41.0.0
**Purpose**: Encryption and secure storage
**Usage**:
- Encrypting sensitive settings in database
- Password hashing
- Token generation

**Why Cryptography?**
- Industry-standard library
- FIPS compliant
- Well-maintained
- Comprehensive crypto primitives

**Example**:
```python
from cryptography.fernet import Fernet

# Generate key
key = Fernet.generate_key()

# Encrypt
cipher = Fernet(key)
encrypted = cipher.encrypt(b"sensitive_data")

# Decrypt
decrypted = cipher.decrypt(encrypted)
```

### Flask-WTF 1.2.1
**Purpose**: CSRF protection and form handling
**Usage**:
- CSRF token generation
- Form validation
- Secure form rendering

**Features**:
- Automatic CSRF token injection
- Session-based token storage
- Configurable exemptions

**Example**:
```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

# In templates
<form method="POST">
    {{ csrf_token() }}
    <!-- form fields -->
</form>
```

---

## Task Queue

### Celery 5.3.4
**Purpose**: Asynchronous task processing
**Usage**:
- Background sync operations
- Scheduled tasks
- Long-running operations

**Why Celery?**
- Production-proven
- Distributed task execution
- Retry and error handling
- Flexible scheduling

**Example**:
```python
from celery import Celery

celery = Celery('scheduler_app', broker='redis://localhost:6379')

@celery.task
def sync_events_from_external_api():
    """Background task to sync events."""
    # Long-running operation
    pass

# Schedule task
sync_events_from_external_api.delay()
```

### Redis 5.0.1
**Purpose**: Message broker and caching
**Usage**:
- Celery message broker
- Session storage (recommended for production)
- Caching frequently accessed data

**Why Redis?**
- Fast in-memory operations
- Pub/Sub support for Celery
- TTL support for cache expiration
- Persistence options

---

## Testing

### Pytest >= 7.4.3
**Purpose**: Testing framework
**Why Pytest?**
- Simple and intuitive syntax
- Powerful fixtures
- Excellent plugin ecosystem
- Better assertions than unittest

**Plugins** (Recommended):
```python
pytest==7.4.3
pytest-cov==4.1.0              # Coverage reporting
pytest-flask==1.3.0            # Flask-specific helpers
pytest-mock==3.12.0            # Mocking support
faker==20.1.0                  # Fake data generation
factory-boy==3.3.0             # Test data factories
freezegun==1.4.0               # Time mocking
```

**Example**:
```python
def test_schedule_event(db_session):
    """Test event scheduling."""
    employee = EmployeeFactory()
    event = EventFactory()

    result = schedule_event(event, employee, datetime.now())

    assert result is True
    schedule = Schedule.query.first()
    assert schedule.employee_id == employee.id
```

---

## Development Tools

### Code Quality
```bash
# Linting
flake8==7.0.0                  # Style checker
pylint==3.0.3                  # Advanced linting
black==23.12.1                 # Code formatter
isort==5.13.2                  # Import organizer

# Type Checking
mypy==1.8.0                    # Static type checker

# Security
bandit==1.7.6                  # Security linter
safety==2.3.5                  # Dependency vulnerability scanner
```

### Documentation
```bash
sphinx==7.2.6                  # Documentation generator
sphinx-rtd-theme==2.0.0        # Read the Docs theme
```

### Version Control
- **Git**: Source control
- **GitHub**: Repository hosting
- **Git Flow**: Branching strategy

---

## External Services

### Crossmark Session API
**Purpose**: Event and employee data synchronization
**Base URL**: `https://crossmark.mvretail.com`
**Authentication**: Session-based with username/password
**Features**:
- Event retrieval
- Schedule submission
- Employee data sync

**Configuration**:
```python
EXTERNAL_API_BASE_URL = 'https://crossmark.mvretail.com'
EXTERNAL_API_USERNAME = config('EXTERNAL_API_USERNAME')
EXTERNAL_API_PASSWORD = config('EXTERNAL_API_PASSWORD')
EXTERNAL_API_TIMEOUT = 30
```

### Walmart Retail Link EDR API
**Purpose**: Event Detail Report generation
**Base URL**: `https://retaillink2.wal-mart.com/EventManagement`
**Authentication**: Multi-factor authentication (MFA)
**Features**:
- Event browsing
- EDR report retrieval
- Item data caching

**Configuration**:
```python
WALMART_EDR_USERNAME = config('WALMART_EDR_USERNAME')
WALMART_EDR_PASSWORD = config('WALMART_EDR_PASSWORD')
WALMART_EDR_MFA_CREDENTIAL_ID = config('WALMART_EDR_MFA_CREDENTIAL_ID')
```

---

## Technology Decision Rationale

### Why Flask Over Django?
**Decision**: Flask
**Reasoning**:
- ✅ Lightweight - don't need Django's batteries-included approach
- ✅ Flexible - can add only what we need
- ✅ Simple - easier to understand for small team
- ✅ Fast development - quicker to prototype
- ❌ Less built-in features - have to add extensions

### Why SQLite for Development?
**Decision**: SQLite (dev) → PostgreSQL (prod)
**Reasoning**:
- ✅ Zero configuration for development
- ✅ File-based - easy to reset
- ✅ Fast for small datasets
- ⚠️ Limited concurrency
- ⚠️ Not for production at scale

**Production Migration Path**:
```python
# Development
DATABASE_URL = 'sqlite:///instance/scheduler.db'

# Production
DATABASE_URL = 'postgresql://user:pass@host:5432/scheduler_db'
```

### Why Celery for Background Tasks?
**Decision**: Celery + Redis
**Reasoning**:
- ✅ Production-proven at scale
- ✅ Distributed task execution
- ✅ Retry logic and error handling
- ✅ Flexible scheduling
- ❌ Requires Redis/RabbitMQ infrastructure

**Alternatives Considered**:
- **APScheduler**: Simpler but limited to single process
- **RQ**: Simpler but less features than Celery
- **Huey**: Lightweight but less community support

### Why Requests Over urllib?
**Decision**: Requests library
**Reasoning**:
- ✅ Much more intuitive API
- ✅ Session management built-in
- ✅ Better error handling
- ✅ Industry standard
- ❌ External dependency (vs stdlib urllib)

---

## Deployment Stack (Production)

### Recommended Production Setup

```
┌─────────────────────────────────────┐
│         Nginx (Reverse Proxy)       │
└───────────────┬─────────────────────┘
                │
        ┌───────▼────────┐
        │   Gunicorn     │ (WSGI Server)
        │   Workers: 4   │
        └───────┬────────┘
                │
        ┌───────▼────────┐
        │  Flask App     │
        └───────┬────────┘
                │
        ┌───────▼────────┐
        │  PostgreSQL    │
        │    Database    │
        └────────────────┘
```

**Components**:
```bash
# Web Server
nginx==1.24+                   # Reverse proxy

# WSGI Server
gunicorn==21.2.0              # Production WSGI server

# Database
postgresql==14+                # Production database

# Cache/Queue
redis==7.2+                    # Caching and task queue

# Process Manager
supervisor==4.2+               # Process monitoring
# OR
systemd                        # System service management
```

**Gunicorn Configuration**:
```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "sync"
timeout = 120
accesslog = "/var/log/scheduler/access.log"
errorlog = "/var/log/scheduler/error.log"
```

---

## Infrastructure & DevOps

### Containerization
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scheduler_app/ ./scheduler_app/
COPY migrations/ ./migrations/

CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
```

### Environment Variables (Required)
```bash
# Flask
FLASK_ENV=production
SECRET_KEY=<random-secret-key>

# Database
DATABASE_URL=postgresql://user:pass@host:5432/scheduler

# External APIs
EXTERNAL_API_USERNAME=<crossmark-username>
EXTERNAL_API_PASSWORD=<crossmark-password>
WALMART_EDR_USERNAME=<walmart-username>
WALMART_EDR_PASSWORD=<walmart-password>
WALMART_EDR_MFA_CREDENTIAL_ID=<mfa-id>

# Redis
REDIS_URL=redis://localhost:6379/0

# Encryption
SETTINGS_ENCRYPTION_KEY=<fernet-key>
```

---

## Monitoring & Observability (Recommended)

### Application Performance Monitoring
- **New Relic** or **DataDog**: Application metrics
- **Sentry**: Error tracking
- **ELK Stack**: Log aggregation

### Health Checks
```python
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({
        'status': 'healthy',
        'database': check_database_connection(),
        'redis': check_redis_connection(),
        'version': '1.0.0'
    })
```

---

## Version Compatibility Matrix

| Component | Minimum | Tested | Recommended |
|-----------|---------|--------|-------------|
| Python | 3.11 | 3.11 | 3.11+ |
| Flask | 3.0.0 | 3.0.0 | 3.0+ |
| SQLAlchemy | 2.0 | 2.0 | 2.0+ |
| PostgreSQL | 12 | 14 | 14+ |
| Redis | 5.0 | 7.0 | 7.0+ |
| Node.js (frontend tools) | 18 | 18 | 18 LTS |

---

## Dependency Management

### Production Dependencies
```bash
# Install production dependencies only
pip install -r requirements.txt
```

### Development Dependencies
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Includes: pytest, flake8, black, mypy, etc.
```

### Security Updates
```bash
# Check for security vulnerabilities
pip install safety
safety check

# Update dependencies
pip-review --auto

# Freeze updated versions
pip freeze > requirements.txt
```

---

## Future Considerations

### Technology Upgrades Planned
- [ ] **Flask 3.1+**: Adopt async views when available
- [ ] **SQLAlchemy 2.1+**: Performance improvements
- [ ] **PostgreSQL 15+**: Better JSON support
- [ ] **Pydantic**: Data validation layer

### New Technologies to Evaluate
- [ ] **FastAPI**: Consider for API-only services
- [ ] **GraphQL**: Alternative to REST API
- [ ] **Docker**: Containerization
- [ ] **Kubernetes**: Orchestration for scaling
- [ ] **TimescaleDB**: Time-series data for analytics

---

## References

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [ReportLab User Guide](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- [12-Factor App Methodology](https://12factor.net/)

---

**Document Ownership**: Dev Team + PM
**Review Cycle**: Quarterly
**Last Reviewed**: 2025-01-09
**Next Review**: 2025-04-09
