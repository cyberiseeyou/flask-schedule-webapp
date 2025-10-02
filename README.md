# Interactive Scheduling Assistant

A Flask-based web application for automating employee scheduling and availability management. This local application eliminates manual cross-referencing of schedules, prevents double-bookings, and provides a centralized view of all scheduling activities.

## Features

- **Dashboard View**: Prioritized list of unscheduled events sorted by urgency
- **Interactive Scheduling**: Dynamic form with date constraints and employee availability checking
- **CSV Import/Export**: Bulk operations for WorkBankVisits.csv import and CalendarSchedule.csv export
- **Availability Management**: Automatic employee availability checking to prevent conflicts
- **Data Validation**: Comprehensive input validation and error handling
- **Responsive Design**: Clean, task-oriented interface optimized for efficiency

## Quick Start

### Prerequisites

- Python 3.13+ 
- pip package manager

### Installation

1. Clone or navigate to the project directory:
```bash
cd flask-schedule-webapp/scheduler_app
```

2. Create and activate a virtual environment:
```bash
python -m venv ../venv
source ../venv/bin/activate  # Linux/Mac
# or
../venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open your browser to: http://localhost:5000

The SQLite database will be automatically created on first run.

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
scheduler_app/
├── app.py                    # Main Flask application (342 lines)
├── requirements.txt          # Python dependencies
├── instance/
│   └── scheduler.db         # SQLite database (auto-created)
├── static/
│   ├── css/style.css        # Design system (378 lines)
│   └── js/main.js           # Frontend logic (162 lines)
├── templates/
│   ├── index.html           # Dashboard template
│   └── schedule.html        # Scheduling form
├── test_models.py           # Database model tests
└── test_routes.py           # Route and integration tests
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
| Runtime | Python | 3.13+ | Application runtime |
| Framework | Flask | 3.0.0 | Web framework |
| Database | SQLAlchemy | 2.0.36 | ORM and database management |
| Extension | Flask-SQLAlchemy | 3.1.1 | Flask-SQLAlchemy integration |
| Storage | SQLite | Built-in | Local database |
| Testing | pytest | 7.4.3 | Test framework |
| Frontend | Vanilla JS | ES6+ | Dynamic functionality |
| Styling | Custom CSS | - | Responsive design |

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

- **Architecture**: See `docs/brownfield-architecture.md` for complete system documentation
- **Stories**: Individual story documentation in `docs/stories/`
- **QA Gates**: Quality assurance results in `docs/qa/gates/`
- **PRD**: Product requirements in `PRD.md`

## License

Internal project - see organization policies for usage guidelines.

---

**Status**: Epic 1 Complete - Core scheduling functionality fully implemented and tested
**Next Phase**: Epic 2 - Administration interface and API integration capabilities