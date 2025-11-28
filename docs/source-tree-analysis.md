# Source Tree Analysis

**Project:** Flask Schedule Webapp
**Generated:** 2025-11-20
**Repository Type:** Monolith

## Project Structure

```
flask-schedule-webapp/
├── app/                              # Main application package
│   ├── __init__.py                  # ⚡ Application factory (create_app)
│   ├── config.py                    # Configuration classes (Dev/Test/Prod)
│   ├── extensions.py                # Flask extensions initialization
│   ├── constants.py                 # Application-wide constants
│   │
│   ├── models/                      # 📊 Database Models (SQLAlchemy)
│   │   ├── __init__.py             # Model factory and registry
│   │   ├── employee.py             # Employee model
│   │   ├── event.py                # Event model
│   │   ├── schedule.py             # Schedule assignments
│   │   ├── availability.py         # Employee availability patterns
│   │   ├── auto_scheduler.py      # Auto-scheduler related models
│   │   ├── employee_attendance.py  # Attendance tracking
│   │   ├── system_setting.py       # System configuration
│   │   ├── audit.py                # Audit logging
│   │   ├── paperwork_template.py   # PDF templates
│   │   ├── user_session.py         # Session management
│   │   └── registry.py             # Model registry pattern
│   │
│   ├── routes/                      # 🛣️  Flask Blueprints (Controllers)
│   │   ├── __init__.py             # Blueprint registration
│   │   ├── main.py                 # Dashboard and main views
│   │   ├── scheduling.py           # Event scheduling operations
│   │   ├── api.py                  # Core API endpoints
│   │   ├── employees.py            # Employee management
│   │   ├── auto_scheduler.py       # Auto-scheduler interface
│   │   ├── auth.py                 # Authentication
│   │   ├── admin.py                # Administrative functions
│   │   ├── printing.py             # Report generation
│   │   ├── dashboard.py            # Dashboard views
│   │   ├── rotations.py            # Rotation management
│   │   ├── edr_sync.py             # EDR data synchronization
│   │   ├── health.py               # Health check endpoints
│   │   ├── help.py                 # Help pages
│   │   ├── ai_routes.py            # AI assistant API
│   │   ├── api_attendance.py       # Attendance API
│   │   ├── api_auto_scheduler_settings.py  # Scheduler settings API
│   │   ├── api_availability_overrides.py   # Availability override API
│   │   ├── api_employee_termination.py     # Termination API
│   │   ├── api_notifications.py    # Notifications API
│   │   ├── api_paperwork_templates.py      # Template management API
│   │   ├── api_suggest_employees.py        # Employee suggestions API
│   │   └── api_validate_schedule.py        # Schedule validation API
│   │
│   ├── services/                    # 💼 Business Logic Layer
│   │   ├── __init__.py
│   │   ├── scheduling_engine.py    # Core scheduling algorithms
│   │   ├── conflict_resolver.py    # Scheduling conflict detection
│   │   ├── conflict_validation.py  # Constraint validation
│   │   ├── constraint_validator.py # Business rule enforcement
│   │   ├── schedule_verification.py # Schedule quality checks
│   │   ├── rotation_manager.py     # Daily rotation assignments
│   │   ├── workload_analytics.py   # Performance metrics
│   │   ├── validation_types.py     # Validation data structures
│   │   ├── daily_audit_checker.py  # Daily validation audits
│   │   ├── daily_paperwork_generator.py    # PDF generation
│   │   ├── edr_generator.py        # EDR report generation
│   │   ├── edr_service.py          # EDR business logic
│   │   ├── sync_service.py         # External API sync coordination
│   │   ├── event_time_settings.py  # Time configuration management
│   │   ├── ai_assistant.py         # AI natural language interface
│   │   └── ai_tools.py             # AI tool definitions
│   │
│   ├── integrations/                # 🔌 External System Integrations
│   │   ├── external_api/           # Crossmark API (crossmark.mvretail.com)
│   │   │   ├── session_api_service.py     # Session-based authentication
│   │   │   └── sync_engine.py      # Event synchronization engine
│   │   │
│   │   ├── walmart_api/            # Walmart Retail Link
│   │   │   ├── authenticator.py    # OAuth authentication
│   │   │   ├── session_manager.py  # Session management
│   │   │   ├── routes.py           # API routes
│   │   │   ├── README.md           # Integration documentation
│   │   │   └── CURRENT_STATUS.md   # Implementation status
│   │   │
│   │   └── edr/                    # EDR Data Integration
│   │       ├── db_manager.py       # Database operations
│   │       ├── pdf_generator.py    # PDF creation
│   │       ├── pdf_generator_base.py  # Base PDF class
│   │       ├── report_generator.py # Report assembly
│   │       └── CACHING_README.md   # Caching strategy docs
│   │
│   ├── utils/                       # 🔧 Utility Functions
│   │   ├── __init__.py
│   │   ├── validators.py           # Input validation helpers
│   │   ├── encryption.py           # Data encryption utilities
│   │   ├── event_helpers.py        # Event manipulation helpers
│   │   └── db_helpers.py           # Database query helpers
│   │
│   ├── error_handlers/              # ⚠️  Error Handling & Logging
│   │   ├── __init__.py             # Error handler registration
│   │   ├── decorators.py           # Error handling decorators
│   │   ├── exceptions.py           # Custom exception classes
│   │   └── logging.py              # Logging configuration
│   │
│   ├── static/                      # 🎨 Frontend Assets
│   │   ├── css/                    # Stylesheets
│   │   │   ├── style.css           # Main styles
│   │   │   ├── login.css           # Login page styles
│   │   │   ├── help.css            # Help page styles
│   │   │   ├── validation.css      # Validation widget styles
│   │   │   ├── responsive.css      # Mobile responsiveness
│   │   │   ├── modals.css          # Modal dialog styles
│   │   │   ├── pages/              # Page-specific styles
│   │   │   └── components/         # Component-specific styles
│   │   │
│   │   ├── js/                     # JavaScript
│   │   │   ├── main.js             # Main application logic
│   │   │   ├── navigation.js       # Navigation handling
│   │   │   ├── csrf_helper.js      # CSRF token management
│   │   │   ├── employees.js        # Employee management UI
│   │   │   ├── login.js            # Login form handling
│   │   │   ├── search.js           # Search functionality
│   │   │   ├── notifications.js    # Notification system
│   │   │   ├── user_dropdown.js    # User menu interactions
│   │   │   ├── database-refresh.js # Data refresh utilities
│   │   │   ├── components/         # Reusable UI components
│   │   │   ├── pages/              # Page-specific JavaScript
│   │   │   ├── modules/            # JavaScript modules
│   │   │   └── utils/              # JavaScript utilities
│   │   │
│   │   └── img/                    # Images and icons
│   │
│   └── templates/                   # 📄 Jinja2 HTML Templates
│       ├── base.html               # Base template with navbar/footer
│       ├── index.html              # Landing page
│       ├── login.html              # Login page
│       ├── dashboard.html          # Deprecated (redirects to daily_view)
│       ├── daily_view.html         # Daily schedule dashboard
│       ├── calendar.html           # Calendar view
│       ├── schedule.html           # Event scheduling form
│       ├── schedule_verification.html  # Validation dashboard
│       ├── employees.html          # Employee management
│       ├── employee_analytics.html # Employee performance metrics
│       ├── auto_scheduler_main.html    # Auto-scheduler interface
│       ├── auto_schedule_review.html   # Review auto-assignments
│       ├── rotations.html          # Rotation management
│       ├── printing.html           # Print preview
│       ├── attendance.html         # Attendance tracking
│       ├── api_tester.html         # API testing interface
│       ├── settings.html           # System settings
│       ├── sync_admin.html         # Sync administration
│       ├── components/             # Reusable template components
│       │   ├── floating_verification_widget.html
│       │   └── ...
│       ├── dashboard/              # Dashboard components
│       └── help/                   # Help pages
│
├── tests/                           # 🧪 Test Suite
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures
│   ├── unit/                       # Unit tests
│   └── integration/                # Integration tests
│
├── migrations/                      # 📦 Database Migrations (Alembic)
│   ├── alembic.ini                 # Alembic configuration
│   ├── env.py                      # Migration environment
│   └── versions/                   # Migration scripts
│       ├── 1bc16a06f62e_initial_database_schema.py
│       ├── 62eca6d029af_add_auto_scheduler_tables_and_event_.py
│       └── 0be04acd9951_add_system_settings_table.py
│
├── scripts/                         # 🛠️  Utility Scripts
│   ├── update_db.py                # Database management
│   └── list_routes.py              # Route debugging
│
├── docs/                            # 📚 Documentation
│   ├── architecture/               # Architecture documentation
│   ├── deployment/                 # Deployment guides
│   ├── operations/                 # Operations procedures
│   ├── testing/                    # Test reports
│   └── templates/                  # Document templates
│
├── deployment/                      # 🚀 Deployment Configurations
│   ├── docker/                     # Docker setup
│   │   ├── Dockerfile              # Production image
│   │   ├── Dockerfile.dev          # Development image
│   │   ├── docker-compose.yml      # Production compose
│   │   └── docker-compose.dev.yml  # Development compose
│   │
│   ├── nginx/                      # Nginx reverse proxy
│   └── systemd/                    # System service files
│
├── data/                            # 💾 Application Data (gitignored)
│   ├── paperwork/                  # Generated PDFs
│   ├── barcodes/                   # Generated barcodes
│   └── uploads/                    # User uploads
│
├── instance/                        # 🔒 Instance-Specific Files (gitignored)
│   └── scheduler.db                # SQLite database (dev)
│
├── logs/                            # 📋 Application Logs (gitignored)
│
├── .bmad/                           # 🤖 BMad Method Files
│   ├── bmm/                        # BMad Method Module
│   └── core/                       # Core BMad infrastructure
│
├── .claude/                         # 🤖 Claude Code Configuration
│   ├── agents/                     # Custom agents
│   ├── commands/                   # Slash commands
│   └── skills/                     # Skills
│
├── .context/                        # 📋 Project Context Files
│   ├── project_structure.md
│   ├── overall_project_status.md
│   ├── feature_checklist.md
│   ├── identified_issues.md
│   └── recommendations.md
│
├── wsgi.py                          # ⚡ WSGI Entry Point (Gunicorn)
├── celery_worker.py                 # ⚡ Celery Worker Entry Point
├── gunicorn_config.py               # Gunicorn configuration
├── requirements.txt                 # Python dependencies
├── requirements_ai.txt              # AI assistant dependencies
├── .env.example                     # Environment template
├── .env                             # Environment variables (gitignored)
├── .gitignore                       # Git ignore rules
├── README.md                        # Project documentation
├── Makefile                         # Make commands
├── setup.sh                         # Setup script (Linux/Mac)
└── setup.bat                        # Setup script (Windows)
```

## Key Directories

### Critical Application Paths

**Entry Points:**
- `wsgi.py` - WSGI application entry for Gunicorn
- `celery_worker.py` - Background task worker
- `app/__init__.py` - Application factory (create_app function)

**Configuration:**
- `app/config.py` - Environment-specific configuration classes
- `.env` - Environment variables (credentials, API keys)
- `gunicorn_config.py` - Production server configuration

**Core Business Logic:**
- `app/services/` - Business logic layer (16 service modules)
- `app/routes/` - API and view controllers (23 blueprints)
- `app/models/` - Data models and database schema (16 models)

**External Integrations:**
- `app/integrations/external_api/` - Crossmark API sync (crossmark.mvretail.com)
- `app/integrations/walmart_api/` - Walmart Retail Link integration
- `app/integrations/edr/` - EDR data and report generation

**Frontend:**
- `app/templates/` - Jinja2 HTML templates
- `app/static/css/` - Stylesheets
- `app/static/js/` - JavaScript modules

## Integration Points

**External APIs:**
1. **Crossmark API** (`crossmark.mvretail.com`)
   - Location: `app/integrations/external_api/`
   - Purpose: Event synchronization
   - Authentication: Session-based

2. **Walmart Retail Link**
   - Location: `app/integrations/walmart_api/`
   - Purpose: EDR sales data
   - Authentication: OAuth + MFA

**Database:**
- Development: SQLite (`instance/scheduler.db`)
- Production: PostgreSQL (configured via DATABASE_URL)
- Migrations: `migrations/versions/`

**Task Queue:**
- Celery worker for async tasks
- Redis backend for task queue
- Entry point: `celery_worker.py`

## Code Organization Patterns

**Application Factory Pattern:**
- `create_app(config_name)` in `app/__init__.py`
- Enables multiple app instances with different configs
- Used for testing with in-memory databases

**Blueprint Pattern:**
- 23 blueprints for modular route organization
- Each blueprint handles a specific domain (scheduling, employees, API, etc.)
- Registered in `app/__init__.py`

**Service Layer Pattern:**
- Business logic separated from routes
- Services in `app/services/` directory
- Routes call services, services manipulate models

**Model Registry Pattern:**
- Models created via factory functions
- Central registry for model access: `get_models()`
- Enables dynamic model instantiation

**Repository Pattern:**
- Database operations abstracted in services
- `app/utils/db_helpers.py` provides query utilities

## Asset Organization

**CSS Structure:**
- `style.css` - Main application styles
- `pages/` - Page-specific styles
- `components/` - Component-specific styles
- `responsive.css` - Mobile-first responsive design

**JavaScript Structure:**
- `modules/` - Reusable JavaScript modules
- `pages/` - Page-specific logic
- `components/` - UI component scripts
- `utils/` - Utility functions

## Testing Structure

**Test Organization:**
- `tests/unit/` - Isolated unit tests
- `tests/integration/` - Integration tests with database
- `tests/conftest.py` - Shared pytest fixtures

**Test Coverage:**
- Unit tests for services and utilities
- Integration tests for API endpoints
- Pytest with coverage reporting

## Deployment Structure

**Docker:**
- Production: `deployment/docker/Dockerfile`
- Development: `deployment/docker/Dockerfile.dev`
- Multi-stage builds for optimized images
- Nginx reverse proxy configuration

**Scripts:**
- `setup.sh` / `setup.bat` - Automated setup
- `scripts/update_db.py` - Database utilities
- `Makefile` - Common development commands

## File Naming Conventions

- **Python modules:** lowercase_with_underscores
- **Classes:** PascalCase
- **Functions:** lowercase_with_underscores
- **Constants:** UPPERCASE_WITH_UNDERSCORES
- **Templates:** lowercase_with_underscores.html
- **Static files:** lowercase-with-hyphens.css/js

## Notes

- All source code uses UTF-8 encoding
- Python 3.11+ required
- Line endings: LF (Unix-style)
- Indentation: 4 spaces (Python), 2 spaces (HTML/CSS/JS)
- Max line length: 120 characters (PEP 8 relaxed)
