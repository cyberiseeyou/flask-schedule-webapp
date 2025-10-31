# Flask Schedule Webapp - Project Structure

**Last Updated:** 2025-10-31
**Analysis Date:** 2025-10-31
**Branch:** refactor/project-structure-reorganization

## Directory Tree Overview

```
flask-schedule-webapp/
├── .context/                        # Analysis and context files
├── .claude/                         # Claude AI configuration
├── app/                             # Main application package (NEW)
│   ├── __init__.py                 # Application factory (create_app)
│   ├── extensions.py               # Flask extensions initialization
│   ├── config.py                   # Configuration classes
│   ├── constants.py                # Application constants
│   │
│   ├── error_handlers/             # Error handling (4 files)
│   │   ├── __init__.py            # Error handler registration
│   │   ├── decorators.py          # Error handling decorators
│   │   ├── exceptions.py          # Custom exceptions
│   │   └── logging.py             # Logging configuration
│   │
│   ├── integrations/               # External integrations
│   │   ├── edr/                   # EDR reporting (6 files)
│   │   │   ├── __init__.py
│   │   │   ├── CACHING_README.md
│   │   │   ├── db_manager.py
│   │   │   ├── pdf_generator.py
│   │   │   ├── pdf_generator_base.py
│   │   │   └── report_generator.py
│   │   │
│   │   ├── external_api/          # Crossmark API sync (2 files)
│   │   │   ├── session_api_service.py
│   │   │   └── sync_engine.py
│   │   │
│   │   └── walmart_api/           # Walmart Retail Link (6 files)
│   │       ├── __init__.py
│   │       ├── authenticator.py
│   │       ├── CURRENT_STATUS.md
│   │       ├── README.md
│   │       ├── routes.py
│   │       └── session_manager.py
│   │
│   ├── models/                     # Database models (12 files)
│   │   ├── __init__.py
│   │   ├── audit.py               # Audit logging
│   │   ├── auto_scheduler.py     # Auto-scheduler models
│   │   ├── availability.py       # Employee availability
│   │   ├── employee.py           # Employee records
│   │   ├── employee_attendance.py
│   │   ├── event.py              # Event scheduling
│   │   ├── paperwork_template.py
│   │   ├── registry.py           # Model registry pattern
│   │   ├── schedule.py           # Schedule assignments
│   │   ├── system_setting.py     # System configuration
│   │   └── user_session.py       # User sessions
│   │
│   ├── routes/                     # Flask blueprints (22 files)
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── api.py                # Main API routes
│   │   ├── api_attendance.py
│   │   ├── api_auto_scheduler_settings.py
│   │   ├── api_availability_overrides.py
│   │   ├── api_employee_termination.py
│   │   ├── api_notifications.py
│   │   ├── api_paperwork_templates.py
│   │   ├── api_suggest_employees.py
│   │   ├── api_validate_schedule.py
│   │   ├── auth.py               # Authentication
│   │   ├── auto_scheduler.py
│   │   ├── dashboard.py
│   │   ├── edr_sync.py
│   │   ├── employees.py
│   │   ├── health.py
│   │   ├── help.py
│   │   ├── main.py
│   │   ├── printing.py
│   │   ├── rotations.py
│   │   └── scheduling.py
│   │
│   ├── services/                   # Business logic (12 files)
│   │   ├── __init__.py
│   │   ├── conflict_resolver.py
│   │   ├── conflict_validation.py
│   │   ├── constraint_validator.py
│   │   ├── daily_audit_checker.py
│   │   ├── daily_paperwork_generator.py
│   │   ├── edr_generator.py
│   │   ├── edr_service.py
│   │   ├── rotation_manager.py
│   │   ├── scheduling_engine.py
│   │   ├── sync_service.py
│   │   ├── validation_types.py
│   │   └── workload_analytics.py
│   │
│   ├── static/                     # Frontend assets
│   │   ├── css/                   # Stylesheets (12 files)
│   │   │   ├── components/        # Component styles
│   │   │   ├── pages/             # Page-specific styles
│   │   │   └── *.css              # Global styles
│   │   │
│   │   ├── img/                   # Images (7 files)
│   │   │
│   │   └── js/                    # JavaScript (29 files)
│   │       ├── components/        # UI components
│   │       ├── modules/           # JavaScript modules
│   │       ├── pages/             # Page-specific JS
│   │       └── utils/             # Utility functions
│   │
│   ├── templates/                  # Jinja2 templates (32 files)
│   │   ├── dashboard/
│   │   ├── help/                  # Help documentation
│   │   └── *.html                 # Page templates
│   │
│   └── utils/                      # Utility functions (5 files)
│       ├── __init__.py
│       ├── db_helpers.py
│       ├── encryption.py
│       ├── event_helpers.py
│       └── validators.py
│
├── deployment/                     # Deployment configurations
│   ├── docker/                    # Docker files (4 files)
│   │   ├── Dockerfile
│   │   ├── Dockerfile.dev
│   │   ├── docker-compose.yml
│   │   └── docker-compose.dev.yml
│   │
│   ├── nginx/                     # Nginx configuration
│   │   └── nginx.conf
│   │
│   └── systemd/                   # Systemd service
│       └── scheduler.service
│
├── docs/                          # Documentation
│   ├── architecture/              # Architecture docs (3 files)
│   │   ├── ARCHITECTURAL_OPTIMIZATIONS.md
│   │   ├── OPTIMIZATIONS_COMPLETED.md
│   │   └── PROJECT_ROOT_REFACTOR.md
│   │
│   ├── deployment/                # Deployment guides (3 files)
│   │   ├── DEPLOYMENT.md
│   │   ├── DOCKER.md
│   │   └── PRODUCTION_CHECKLIST.md
│   │
│   ├── operations/                # Operations guides (1 file)
│   │   └── RESTART_APP.md
│   │
│   ├── templates/                 # PDF templates (3 files)
│   │   ├── Daily_Task_Checkoff_Sheet.pdf
│   │   ├── Event_Table_Activity_Log.pdf
│   │   └── new_activety_log.pdf
│   │
│   └── testing/                   # Test documentation (1 file)
│       └── TEST_REPORT.md
│
├── migrations/                    # Alembic database migrations
│   ├── versions/                  # Active migrations (4 files)
│   └── versions_backup/           # Historical migrations (9 files)
│
├── scripts/                       # Utility scripts (8 files)
│   ├── Club_8135_Scheduling_Rulebook.py
│   ├── convert_pdfs_to_jpg.py
│   ├── fix_supervisor_event_types.py
│   ├── generate_barcodes.py
│   ├── list_routes.py
│   ├── modify_activity_log.py
│   ├── scheduling_constants.py
│   └── update_db.py
│
├── tests/                         # Test suite
│   ├── integration/               # Integration tests
│   │   └── integration_tests.py
│   ├── test.py                    # Unit tests
│   ├── test_edr_cache.db         # Test database
│   └── test_edr_report_from_cache.html
│
├── data/                          # Application data (gitignored)
│   ├── paperwork/                 # Generated paperwork
│   ├── barcodes/                  # Generated barcodes
│   ├── uploads/                   # User uploads
│   └── reports/                   # Generated reports
│
├── instance/                      # Instance-specific files (gitignored)
│   └── scheduler.db               # SQLite database
│
├── logs/                          # Application logs (gitignored)
│   └── app.log
│
├── venv/                          # Virtual environment (gitignored)
│
├── wsgi.py                        # WSGI entry point
├── celery_worker.py               # Celery worker entry point
├── gunicorn_config.py             # Gunicorn configuration
├── requirements.txt               # Python dependencies
├── Makefile                       # Build commands
├── README.md                      # Main documentation
├── IMPORT_UPDATES_REPORT.md       # Import refactoring report
└── [configuration files]          # .env, .gitignore, etc.
```

## File Statistics

### Code Files
- **Python Files:** ~200+ files (32,496 total lines)
- **JavaScript Files:** 29 files
- **HTML Templates:** 32 files
- **CSS Files:** 12 files

### Organization Breakdown
| Directory | Files | Purpose |
|-----------|-------|---------|
| app/models/ | 12 | Database models |
| app/routes/ | 22 | Flask blueprints |
| app/services/ | 12 | Business logic |
| app/integrations/ | 14 | External API integrations |
| app/static/ | 48 | Frontend assets |
| app/templates/ | 32 | HTML templates |
| deployment/ | 6 | Deployment configs |
| docs/ | 11 | Documentation |
| scripts/ | 8 | Utility scripts |
| tests/ | 3+ | Test suite |

## Recent Structural Changes (2025-10-31)

### Major Refactoring Completed
The project underwent a comprehensive reorganization following Flask 2025 best practices:

1. **Application Factory Pattern Implemented**
   - Created `app/__init__.py` with `create_app()` factory
   - Moved from monolithic `app.py` to modular structure

2. **Directory Reorganization**
   - Consolidated all application code under `app/` package
   - Moved integrations to `app/integrations/`
   - Organized documentation into `docs/` hierarchy
   - Moved deployment files to `deployment/`
   - Created `scripts/` for utility scripts
   - Established `tests/` directory structure

3. **Import Pattern Updates**
   - Updated 20+ files to use `app.` prefix
   - Implemented relative imports within packages
   - All imports verified and tested

4. **Root Directory Cleanup**
   - Reduced from 20+ files to 12 essential files
   - Professional, clean structure
   - Gitignored data and runtime files properly

## Key Design Patterns

### Application Factory
- **Location:** `app/__init__.py`
- **Entry Point:** `create_app()` function
- **Benefits:** Multiple configurations, testability

### Blueprint Architecture
- **17 Blueprints registered**
- Modular route organization
- Clean separation of concerns

### Model Registry Pattern
- **Location:** `app/models/registry.py`
- Centralized model management
- Flask extension pattern

### Service Layer
- **Location:** `app/services/`
- Business logic separated from routes
- Reusable components

## Configuration

### Environment Files
- `.env` - Local environment variables
- `.env.docker` - Docker-specific config
- `.env.example` - Template for new setups
- `settings.local.json` - Local settings

### Configuration Classes
- **Location:** `app/config.py`
- Development, Testing, Production configs
- Environment-specific settings

## Entry Points

### Development
```bash
python wsgi.py
```

### Production
```bash
gunicorn --config gunicorn_config.py wsgi:app
```

### Celery Worker
```bash
python celery_worker.py
```

### Database Migrations
```bash
flask db upgrade
```

## New Files Since Last Analysis

The following significant files were created during the recent reorganization:

1. `app/__init__.py` - Application factory implementation
2. `app/extensions.py` - Flask extensions module
3. `IMPORT_UPDATES_REPORT.md` - Import refactoring documentation
4. Reorganized all existing files into new structure

## Architecture Highlights

### Core Application
- **Framework:** Flask 3.0.3
- **Database:** SQLAlchemy 3.1.1 with Alembic migrations
- **WSGI:** Gunicorn 21.2.0
- **Task Queue:** Celery 5.3.6 with Redis
- **Security:** Flask-WTF CSRF, cryptography, rate limiting

### External Integrations
1. **EDR Reporting** - `app/integrations/edr/`
2. **Walmart Retail Link** - `app/integrations/walmart_api/`
3. **Crossmark API** - `app/integrations/external_api/`

### Frontend Architecture
- **Templates:** Jinja2 (32 templates)
- **CSS:** Component-based styling (12 files)
- **JavaScript:** Modular ES6 (29 files)
- **Components:** Reusable UI components

## Notes

- All paths are relative to project root
- Gitignored directories (data/, instance/, logs/, venv/) not tracked
- Virtual environment required for development
- Database migrations managed through Alembic
- Application follows Flask application factory pattern
- Structure optimized for scalability and maintainability
