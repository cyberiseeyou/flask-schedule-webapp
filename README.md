# Flask Schedule Webapp

A comprehensive Flask-based web application for automating employee scheduling, availability management, and event coordination with Walmart Retail Link integration. Features intelligent auto-scheduling, AI-powered assistance, EDR reporting, attendance tracking, and comprehensive workload analytics.

## Features

### Core Scheduling
- **Auto Scheduler**: Intelligent automated event assignment based on skills, availability, and workload
- **Interactive Scheduling**: Manual scheduling with real-time conflict detection
- **Rotation Management**: Automated daily rotation assignments for Juicers and Primary Leads
- **Time Off Management**: Employee time-off requests and availability overrides
- **Schedule Validation**: Real-time validation warnings and conflict resolution
- **Company Holidays**: Company-wide closed days management

### AI-Powered Assistant
- **Intelligent Chat Interface**: Natural language scheduling assistance
- **Smart Suggestions**: AI-driven employee recommendations for events
- **Schedule Verification**: Automated schedule analysis and optimization suggestions
- **Conflict Resolution**: AI-assisted conflict detection and resolution

### Integration and Reporting
- **Walmart Retail Link Integration**: Automatic event synchronization from Crossmark API
- **EDR Sync**: Sales data integration for event-specific paperwork generation
- **Attendance Tracking**: QR code-based and manual attendance logging
- **Comprehensive Reporting**: Daily, weekly, and employee-specific schedule generation
- **PDF Paperwork**: Automated generation of event documentation with EDR data

### Analytics and Monitoring
- **Daily Validation Dashboard**: Real-time schedule monitoring with validation warnings
- **Workload Analytics**: Team performance metrics and capacity planning
- **Attendance Reports**: Employee attendance tracking and unreported event management
- **Performance Metrics**: KPIs for scheduling efficiency and employee utilization

## Quick Start

### Docker Deployment (Recommended)

The easiest way to get started! Just clone and run the setup script.

**Linux/Mac:**
\`\`\`bash
git clone https://github.com/cyberiseeyou/flask-schedule-webapp.git
cd flask-schedule-webapp
chmod +x setup.sh
./setup.sh
\`\`\`

**Windows:**
\`\`\`cmd
git clone https://github.com/cyberiseeyou/flask-schedule-webapp.git
cd flask-schedule-webapp
setup.bat
\`\`\`

**Access:**
- Production: http://localhost:8000
- Development: http://localhost:5000 (use ./setup.sh dev or setup.bat dev)

The setup script automatically:
- Checks Docker installation
- Generates secure secrets
- Configures the database
- Builds and starts all containers
- Runs database migrations

See [DOCKER.md](docs/deployment/DOCKER.md) for detailed Docker deployment guide.

### Local Development

**Prerequisites:**
- Python 3.11+
- pip package manager

**Setup:**
\`\`\`bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run application
python wsgi.py
# or use Gunicorn for production
gunicorn --config gunicorn_config.py wsgi:app
\`\`\`

**Access:** http://localhost:5000

## Technology Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Runtime | Python | 3.11+ | Application runtime |
| Framework | Flask | 3.0.3 | Web framework |
| Database | SQLAlchemy | 3.1.1 | ORM |
| Migrations | Alembic | 1.16.5 | Database versioning |
| Task Queue | Celery | 5.3.6 | Background tasks |
| Cache | Redis | 5.0.3 | Caching and task broker |
| PDF Generation | ReportLab | 4.2.5 | PDF creation |
| Security | Cryptography | 42.0.5 | Encryption |
| Testing | pytest | 8.1.1 | Test framework |
| Deployment | Docker | 20.10+ | Containerization |
| Web Server | Gunicorn | 21.2.0 | WSGI server |

## Database Models

The application uses 17 database models:

| Model | Description |
|-------|-------------|
| Employee | Employee profiles and settings |
| Event | Projects and events from Crossmark |
| Schedule | Event-employee assignments |
| EmployeeWeeklyAvailability | Weekly availability patterns |
| EmployeeAvailability | Daily availability |
| EmployeeTimeOff | Time-off requests |
| EmployeeAvailabilityOverride | Availability exceptions |
| RotationAssignment | Daily rotation assignments |
| PendingSchedule | Auto-scheduler queue |
| SchedulerRunHistory | Scheduler execution logs |
| ScheduleException | Scheduling exceptions |
| EventSchedulingOverride | Event-specific overrides |
| SystemSetting | Application configuration |
| AuditLog | Change tracking |
| EmployeeAttendance | Attendance records |
| PaperworkTemplate | Document templates |
| UserSession | Authentication sessions |
| CompanyHoliday | Company-wide holidays |

## API Endpoints

### Core Routes
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | / | Dashboard with unscheduled events |
| GET | /daily-view | Daily schedule view |
| GET | /schedule/event_id | Event scheduling form |
| POST | /save_schedule | Save schedule assignment |

### API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/available_employees/date | Available employees for date |
| GET | /api/suggest_employees | AI-powered employee suggestions |
| POST | /api/validate_schedule | Validate schedule conflicts |
| GET | /api/schedule-verification | Schedule verification data |

### AI Assistant
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /ai/chat | AI chat interface |
| GET | /ai/suggestions | AI scheduling suggestions |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /admin/settings | System settings |
| POST | /admin/company-holidays | Manage holidays |

## Development

### Running Tests

\`\`\`bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run with coverage
python -m pytest --cov=app
\`\`\`

### Database Migrations

\`\`\`bash
# Create migration
flask db migrate -m "Description"

# Apply migrations
flask db upgrade

# Rollback
flask db downgrade
\`\`\`

## Environment Configuration

Create a `.env` file based on `.env.example`:

\`\`\`env
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///instance/scheduler.db
CROSSMARK_API_KEY=your-api-key
REDIS_URL=redis://localhost:6379/0
\`\`\`

The setup script automatically generates secure secrets and configures the database connection.

## Database Backup

The application includes comprehensive backup scripts for both Linux/Mac and Windows.

**Linux/Mac:**
\`\`\`bash
chmod +x backup.sh

# Interactive mode
./backup.sh

# Run backup immediately
./backup.sh --now

# Set up scheduled backups (cron)
./backup.sh --schedule

# Restore from backup
./backup.sh --restore backups/scheduler_backup_postgresql_20231215_020000.sql.gz

# List available backups
./backup.sh --list
\`\`\`

**Windows:**
\`\`\`cmd
REM Interactive mode
backup.bat

REM Run backup immediately
backup.bat --now

REM Set up scheduled backups (Windows Task Scheduler)
backup.bat --schedule

REM Restore from backup
backup.bat --restore backups\scheduler_backup_postgresql_20231215_020000.sql

REM List available backups
backup.bat --list
\`\`\`

The backup scripts support:
- PostgreSQL (Docker and native)
- SQLite databases
- Automatic compression
- Scheduled backups with customizable frequency
- Retention policy configuration
- Interactive restore functionality

## Documentation

- [Docker Deployment Guide](docs/deployment/DOCKER.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)

## License

Internal project - see organization policies for usage guidelines.

---

**Status**: Production-ready with AI-powered scheduling assistance
