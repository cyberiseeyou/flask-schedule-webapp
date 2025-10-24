# Flask Schedule Webapp

A comprehensive Flask-based web application for automating employee scheduling, availability management, and event coordination with Walmart Retail Link integration. Features intelligent auto-scheduling, EDR reporting, attendance tracking, and comprehensive workload analytics.

## Features

### Core Scheduling
- **Auto Scheduler**: Intelligent automated event assignment based on skills, availability, and workload
- **Interactive Scheduling**: Manual scheduling with real-time conflict detection
- **Rotation Management**: Automated daily rotation assignments for Juicers and Primary Leads
- **Time Off Management**: Employee time-off requests and availability overrides
- **Schedule Validation**: Real-time validation warnings and conflict resolution

### Integration & Reporting
- **Walmart Retail Link Integration**: Automatic event synchronization from Crossmark API
- **EDR Sync**: Sales data integration for event-specific paperwork generation
- **Attendance Tracking**: QR code-based and manual attendance logging
- **Comprehensive Reporting**: Daily, weekly, and employee-specific schedule generation
- **PDF Paperwork**: Automated generation of event documentation with EDR data

### Analytics & Monitoring
- **Daily Validation Dashboard**: Real-time schedule monitoring with validation warnings
- **Workload Analytics**: Team performance metrics and capacity planning
- **Attendance Reports**: Employee attendance tracking and unreported event management
- **Performance Metrics**: KPIs for scheduling efficiency and employee utilization

## Quick Start

### Docker Deployment (Recommended)

**Prerequisites:**
- Docker 20.10+
- Docker Compose 2.0+

**Deploy:**
```bash
# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run deployment script
bash scripts/setup/deploy.sh
```

**Access:** http://localhost

See [Docker Deployment Guide](docs/deployment/DOCKER_DEPLOYMENT.md) for detailed instructions.

### Local Development

**Prerequisites:**
- Python 3.11+
- pip package manager

**Setup:**
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run application
cd scheduler_app
python app.py
```

**Access:** http://localhost:5000

## Usage

### Basic Workflow

1. **View Events**: Dashboard displays all unscheduled events
2. **Schedule Event**: Click "Schedule" to open the scheduling form
3. **Select Date**: Date picker enforces event date constraints
4. **Choose Employee**: Dropdown shows only available employees for selected date
5. **Set Time**: Enter start time and save the schedule
6. **Export**: Download scheduled events as CSV when ready

### CSV Operations

**Import Events**:
- Use "Import Events" button on dashboard
- Upload WorkBankVisits.csv with required headers:
  ```
  Project Name, Project Reference Number, Location MVID,
  Store Number, Store Name, Start Date/Time, Due Date/Time,
  Estimated Time, Employee ID, Rep Name
  ```

**Export Schedule**:
- Click "Export Schedule" to download CalendarSchedule.csv
- Contains all scheduled events with employee assignments

## Development

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run specific test file
python -m pytest test_routes.py -v
```

### Test Coverage

Current test suite includes 34 tests covering:
- Dashboard and scheduling routes (8 tests)
- Employee availability API (7 tests) 
- Schedule saving logic (9 tests)
- CSV import/export functionality (10 tests)

### Project Structure

```
flask-schedule-webapp/
├── scheduler_app/              # Main application
│   ├── app.py                 # Flask application entry point
│   ├── models/                # Database models (10 models)
│   ├── routes/                # Route handlers (21 blueprints)
│   ├── services/              # Business logic (13 services)
│   ├── static/                # Frontend assets (CSS/JS)
│   ├── templates/             # Jinja2 templates
│   ├── migrations/            # Alembic database migrations
│   └── instance/              # Runtime data & SQLite database
│
├── scripts/                    # Utility & maintenance scripts
│   ├── migrations/            # Database migration utilities
│   ├── testing/               # Test scripts
│   ├── verification/          # Verification scripts
│   ├── data/                  # Data management scripts
│   └── setup/                 # Setup and deployment scripts
│
├── docs/                       # Documentation
│   ├── deployment/            # Deployment guides
│   ├── implementation/        # Implementation documentation
│   ├── epics/                 # Epic summaries
│   ├── architecture/          # Architecture documentation
│   └── archived/              # Historical documentation
│
├── docker/                     # Docker configuration
│   ├── Dockerfile             # Production container image
│   ├── docker-compose.yml     # Multi-container setup
│   ├── entrypoint.sh          # Container initialization
│   └── nginx.conf             # Nginx reverse proxy config
│
├── backups/                    # Database backups
├── archived/                   # Obsolete code and files
├── tests/                      # Test suite
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
└── README.md                   # This file
```

## Database Schema

### Tables

**employees**
- `id` (String, Primary Key) - Employee identifier
- `name` (String, NOT NULL) - Employee display name

**events**
- `id` (Integer, Primary Key) - Auto-increment ID
- `project_name` (Text, NOT NULL) - Project/event name
- `project_ref_num` (Integer, NOT NULL, UNIQUE) - Business identifier
- `location_mvid` (Text) - Location identifier
- `store_number` (Integer) - Store identifier
- `store_name` (Text) - Store name
- `start_datetime` (DateTime, NOT NULL) - Earliest schedule date
- `due_datetime` (DateTime, NOT NULL) - Latest schedule date
- `estimated_time` (Integer) - Duration in minutes
- `is_scheduled` (Boolean, NOT NULL, Default: False) - Status flag

**schedules**
- `id` (Integer, Primary Key) - Auto-increment ID
- `event_ref_num` (Integer, Foreign Key) - Links to events table
- `employee_id` (String, Foreign Key) - Links to employees table
- `schedule_datetime` (DateTime, NOT NULL) - Scheduled date and time

## API Endpoints

### Core Routes
- `GET /` - Dashboard with unscheduled events
- `GET /schedule/<event_id>` - Event scheduling form
- `POST /save_schedule` - Save schedule assignment

### AJAX Endpoints
- `GET /api/available_employees/<date>` - Get available employees for date
- `POST /api/import/events` - Import events from CSV
- `GET /api/export/schedule` - Export scheduled events to CSV

## Technology Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Runtime | Python | 3.11+ | Application runtime |
| Framework | Flask | 3.0.0 | Web framework |
| Database | SQLAlchemy | 2.0.36 | ORM |
| Migrations | Alembic | Latest | Database versioning |
| Storage | SQLite | Built-in | Local database |
| Testing | pytest | Latest | Test framework |
| Frontend | Vanilla JS | ES6+ | Dynamic functionality |
| Styling | Custom CSS | - | Responsive design |
| PDF Generation | ReportLab | 4.0.7 | PDF creation |
| Deployment | Docker | 20.10+ | Containerization |
| Web Server | Nginx | Alpine | Reverse proxy |

## Quality Assurance

This project follows comprehensive quality standards:

- **100% Test Coverage**: All functionality covered with edge cases
- **Story-Driven Development**: Features implemented through complete user stories
- **QA Gate Approval**: All stories pass rigorous quality review
- **Error Handling**: Comprehensive validation and user feedback
- **Transaction Integrity**: Database rollback on errors

### Development Quality Scores
- Story 1.1 (Project Setup): 85/100
- Story 1.2 (Interactive Forms): 90/100
- Story 1.3 (Employee API): 95/100
- Story 1.4 (Schedule Saving): 100/100
- Story 1.5 (CSV Operations): 100/100

## Troubleshooting

### Common Issues

**Database not found**: Run `python app.py` once to auto-create the database

**Import errors**: Ensure virtual environment is activated with `source ../venv/bin/activate`

**Test failures**: Database is automatically managed by test fixtures

**CSV import issues**: Verify file has all required headers and proper date format (`YYYY-MM-DD HH:MM:SS`)

### Debug Mode

The application runs in debug mode during development, providing:
- Detailed error pages
- Automatic reloading on code changes
- Console logging of requests and errors

## Contributing

This project uses the BMad development methodology with:
- Story-driven development (Stories 1.1-1.5 completed)
- Comprehensive QA review process
- Complete test coverage requirements
- Quality gate approval system

## Documentation

- **Docker Deployment**: [docs/deployment/DOCKER_DEPLOYMENT.md](docs/deployment/DOCKER_DEPLOYMENT.md)
- **Quick Start**: [docs/deployment/QUICK_START.md](docs/deployment/QUICK_START.md)
- **Architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Implementation Guides**: [docs/implementation/](docs/implementation/)
- **Epic Documentation**: [docs/epics/](docs/epics/)
- **User Stories**: [docs/stories/](docs/stories/)

## Maintenance

### Database Backup

```bash
python scripts/setup/backup_database.py
```

Backups are stored in `backups/` with timestamps and checksums.

### Running Scripts

All utility scripts are organized in `scripts/`:
- **Migrations**: `scripts/migrations/` - Database migration utilities
- **Testing**: `scripts/testing/` - Test and validation scripts
- **Verification**: `scripts/verification/` - System verification tools
- **Data Management**: `scripts/data/` - Data manipulation utilities

### Deployment

See [Docker Deployment Guide](docs/deployment/DOCKER_DEPLOYMENT.md) for:
- Production deployment
- Environment configuration
- Backup and restore procedures
- Troubleshooting
- Maintenance operations

## Support

For issues and questions:
- Check [Docker Deployment Guide](docs/deployment/DOCKER_DEPLOYMENT.md)
- Review logs: `docker-compose logs -f web` (Docker) or check `logs/` directory
- Consult implementation guides in `docs/implementation/`

## License

Internal project - see organization policies for usage guidelines.

---

**Status**: Production-ready with comprehensive feature set
**Latest**: Docker deployment, organized codebase, comprehensive documentation