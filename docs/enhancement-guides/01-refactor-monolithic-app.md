# Enhancement #1: Refactor Monolithic app.py

**Priority**: 🔴 P0 - Critical
**Effort**: High (3-5 days)
**Impact**: High - Improves maintainability, testability, and developer velocity

---

## **Why This Enhancement Matters**

The current `app.py` contains **3,501 lines** of code in a single file. This creates several problems:

1. **Hard to Navigate**: Finding specific functionality takes time
2. **Merge Conflicts**: Multiple developers can't work on routes simultaneously
3. **Testing Difficulty**: Can't test components in isolation
4. **Cognitive Load**: Understanding the full context is overwhelming
5. **Violates Single Responsibility Principle**: One file does everything

**Goal**: Break the monolith into logical, focused modules using Flask Blueprints.

---

## **System Prompt for AI Agent**

```
You are refactoring a Flask application from a monolithic structure to a modular architecture using Flask Blueprints.

CRITICAL RULES:
1. NEVER delete the original app.py until the refactor is complete and tested
2. Create new files incrementally - one module at a time
3. Test after EACH file extraction to ensure nothing breaks
4. Preserve ALL existing functionality - this is a refactor, not a rewrite
5. Keep imports clean - avoid circular dependencies
6. Update imports in other files as you extract code

MOST IMPORTANT:
- Database models MUST be imported before routes that use them
- Flask app initialization order matters: config → db → blueprints → error handlers
- All route decorators must change from @app.route to @blueprint_name.route

IGNORE/REMOVE FROM CONTEXT:
- Migration scripts (migrate_*.py) - not relevant to refactoring
- Test files - will update later
- Documentation files - will update at the end
```

---

## **Step-by-Step Implementation Guide**

### **Phase 1: Setup and Preparation**

#### **Step 1.1: Create New Directory Structure**

**System Prompt:**
```
Create the new directory structure for modular Flask app.
Do NOT move any code yet - just create empty directories.
Verify the structure with ls commands after creation.
```

**Actions:**
```bash
cd scheduler_app

# Create new directory structure
mkdir -p models
mkdir -p routes
mkdir -p services
mkdir -p utils

# Verify structure
ls -la
```

**Expected Output:**
```
scheduler_app/
├── models/          # NEW - Database models
├── routes/          # NEW - Route blueprints
├── services/        # NEW - Business logic
├── utils/           # NEW - Helper functions
├── app.py           # EXISTING - Will refactor
├── config.py        # EXISTING - Keep as is
├── error_handlers.py # EXISTING - Keep as is
└── ...
```

**Why This Order:**
- Empty directories first = safe, no code breakage
- Verify before proceeding = catch filesystem issues early

---

#### **Step 1.2: Create __init__.py Files**

**System Prompt:**
```
Create __init__.py files in each new directory to make them Python packages.
Start with empty files - we'll populate them later.
```

**Actions:**
```bash
# Create empty __init__.py files
touch models/__init__.py
touch routes/__init__.py
touch services/__init__.py
touch utils/__init__.py
```

**Why:**
- Python requires `__init__.py` to treat directories as packages
- Empty files work fine - we import modules directly

---

### **Phase 2: Extract Database Models**

#### **Step 2.1: Extract Models to Separate Files**

**System Prompt:**
```
Extract database models from app.py to models/ directory.
Copy (don't cut) model classes - we'll remove from app.py later after testing.

Extract in this order (dependencies matter):
1. Base models with no foreign keys (Employee)
2. Models with foreign keys to #1 (Event, EmployeeWeeklyAvailability, EmployeeAvailability)
3. Models with foreign keys to #1 and #2 (Schedule, EmployeeTimeOff)

CRITICAL: Include ALL imports each model needs (db, datetime, etc.)
```

**Step 2.1a: Create models/__init__.py**

Create `scheduler_app/models/__init__.py`:

```python
"""
Database models for Flask Schedule Webapp
Centralizes all SQLAlchemy model imports
"""
from .employee import Employee
from .event import Event
from .schedule import Schedule
from .availability import (
    EmployeeWeeklyAvailability,
    EmployeeAvailability,
    EmployeeTimeOff
)

__all__ = [
    'Employee',
    'Event',
    'Schedule',
    'EmployeeWeeklyAvailability',
    'EmployeeAvailability',
    'EmployeeTimeOff'
]
```

**Why This Structure:**
- Explicit imports = clear dependencies
- `__all__` = controls `from models import *`
- Grouped by domain = easier to find related models

---

**Step 2.1b: Create models/employee.py**

**System Prompt:**
```
Read app.py and extract the Employee class and related code.
Include: class definition, all columns, all methods.
Import db from parent app - we'll fix imports later.
```

Create `scheduler_app/models/employee.py`:

```python
"""
Employee model and related database schema
Represents staff members who can be scheduled for events
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# This will be injected by the app
db = None

def init_db(database):
    """Initialize database instance for models"""
    global db
    db = database


class Employee(db.Model):
    """
    Employee model representing schedulable staff members

    Attributes:
        id: Unique employee identifier (external system ID)
        name: Employee full name
        email: Contact email
        phone: Contact phone number
        is_active: Whether employee is currently active
        is_supervisor: Whether employee has supervisor privileges
        job_title: Employee's job role
        adult_beverage_trained: Required for certain event types
        external_id: ID in external scheduling system
        last_synced: Last successful sync timestamp
        sync_status: Current sync state (pending/synced/failed)
    """
    __tablename__ = 'employees'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_supervisor = db.Column(db.Boolean, nullable=False, default=False)
    job_title = db.Column(db.String(50), nullable=False, default='Event Specialist')
    adult_beverage_trained = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Sync fields for API integration
    external_id = db.Column(db.String(100), unique=True)
    last_synced = db.Column(db.DateTime)
    sync_status = db.Column(db.String(20), default='pending')

    def can_work_event_type(self, event_type):
        """
        Check if employee can work events of the given type based on job title

        Business Rules:
        - Supervisor, Freeosk, Digitals: Requires Club Supervisor or Lead Event Specialist
        - Juicer: Requires Club Supervisor or Juicer Barista
        - Core, Other: All employees can work these

        Args:
            event_type (str): Type of event to check

        Returns:
            bool: True if employee is qualified for this event type
        """
        # Restricted event types that require specific roles
        if event_type in ['Supervisor', 'Freeosk', 'Digitals']:
            return self.job_title in ['Club Supervisor', 'Lead Event Specialist']
        elif event_type == 'Juicer':
            return self.job_title in ['Club Supervisor', 'Juicer Barista']

        # All employees can work other event types (Core, Other)
        return True

    def __repr__(self):
        return f'<Employee {self.id}: {self.name}>'
```

**Why This Structure:**
- Docstrings = self-documenting code
- Business logic methods stay with the model
- `init_db()` pattern = avoid circular imports (db created in app.py)

---

**Step 2.1c: Create models/event.py**

**System Prompt:**
```
Extract Event model from app.py to models/event.py.
Include the detect_event_type() method - it's business logic tied to the model.
Use the same init_db pattern as employee.py.
```

Create `scheduler_app/models/event.py`:

```python
"""
Event model and related database schema
Represents scheduled work/visits that need to be assigned to employees
"""
from datetime import datetime

# Database instance injected by app
db = None

def init_db(database):
    """Initialize database instance for models"""
    global db
    db = database


class Event(db.Model):
    """
    Event model representing work visits/tasks to be scheduled

    Events are imported from external systems and scheduled to employees.
    They have date constraints (start_datetime to due_datetime) and specific
    requirements (event_type) that determine which employees can work them.
    """
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_name = db.Column(db.Text, nullable=False)
    project_ref_num = db.Column(db.Integer, nullable=False, unique=True)
    location_mvid = db.Column(db.Text)
    store_number = db.Column(db.Integer)
    store_name = db.Column(db.Text)
    start_datetime = db.Column(db.DateTime, nullable=False)
    due_datetime = db.Column(db.DateTime, nullable=False)
    estimated_time = db.Column(db.Integer)  # Duration in minutes
    is_scheduled = db.Column(db.Boolean, nullable=False, default=False)
    event_type = db.Column(db.String(20), nullable=False, default='Other')
    condition = db.Column(db.String(20), default='Unstaffed')

    # Sync fields for API integration
    external_id = db.Column(db.String(100), unique=True)
    last_synced = db.Column(db.DateTime)
    sync_status = db.Column(db.String(20), default='pending')

    # Sales tools document URL for Core events
    sales_tools_url = db.Column(db.Text)

    def detect_event_type(self):
        """
        Automatically detect event type based on project name

        Event types determine which employees can be assigned:
        - Core: Standard events, all employees
        - Digitals: Digital displays, requires supervisor/lead
        - Juicer: Juice bar events, requires juicer barista
        - Supervisor: Requires supervisor/lead
        - Freeosk: Kiosk events, requires supervisor/lead
        - Other: Catch-all for unclassified events

        Returns:
            str: Detected event type
        """
        if not self.project_name:
            return 'Other'

        project_name_upper = self.project_name.upper()

        if 'CORE' in project_name_upper:
            return 'Core'
        elif 'DIGITAL' in project_name_upper:
            return 'Digitals'
        elif 'JUICER' in project_name_upper:
            return 'Juicer'
        elif 'SUPERVISOR' in project_name_upper:
            return 'Supervisor'
        elif 'FREEOSK' in project_name_upper:
            return 'Freeosk'
        else:
            return 'Other'

    def __repr__(self):
        return f'<Event {self.project_ref_num}: {self.project_name}>'
```

---

**Step 2.1d: Create models/schedule.py**

Create `scheduler_app/models/schedule.py`:

```python
"""
Schedule model - links events to employees with specific datetime
"""
from datetime import datetime

db = None

def init_db(database):
    global db
    db = database


class Schedule(db.Model):
    """
    Schedule model representing an event assigned to an employee

    This is the core scheduling entity that links Events and Employees
    with a specific datetime for when the work should be performed.
    """
    __tablename__ = 'schedules'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_ref_num = db.Column(db.Integer, db.ForeignKey('events.project_ref_num'), nullable=False)
    employee_id = db.Column(db.String(50), db.ForeignKey('employees.id'), nullable=False)
    schedule_datetime = db.Column(db.DateTime, nullable=False)

    # Sync fields for API integration
    external_id = db.Column(db.String(100), unique=True)
    last_synced = db.Column(db.DateTime)
    sync_status = db.Column(db.String(20), default='pending')

    __table_args__ = (
        db.Index('idx_schedules_date', 'schedule_datetime'),
    )

    def __repr__(self):
        return f'<Schedule {self.id}: Event {self.event_ref_num} -> Employee {self.employee_id}>'
```

---

**Step 2.1e: Create models/availability.py**

Create `scheduler_app/models/availability.py`:

```python
"""
Employee availability models
Tracks when employees can/cannot work
"""
from datetime import datetime

db = None

def init_db(database):
    global db
    db = database


class EmployeeWeeklyAvailability(db.Model):
    """
    Weekly availability pattern for employees
    Defines which days of the week an employee typically works
    """
    __tablename__ = 'employee_weekly_availability'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_id = db.Column(db.String(50), db.ForeignKey('employees.id'), nullable=False)
    monday = db.Column(db.Boolean, nullable=False, default=True)
    tuesday = db.Column(db.Boolean, nullable=False, default=True)
    wednesday = db.Column(db.Boolean, nullable=False, default=True)
    thursday = db.Column(db.Boolean, nullable=False, default=True)
    friday = db.Column(db.Boolean, nullable=False, default=True)
    saturday = db.Column(db.Boolean, nullable=False, default=True)
    sunday = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        db.UniqueConstraint('employee_id', name='unique_employee_weekly_availability'),
    )

    def __repr__(self):
        return f'<EmployeeWeeklyAvailability {self.employee_id}>'


class EmployeeAvailability(db.Model):
    """
    Specific date availability for employees
    Overrides weekly pattern for specific dates
    """
    __tablename__ = 'employee_availability'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_id = db.Column(db.String(50), db.ForeignKey('employees.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    is_available = db.Column(db.Boolean, nullable=False, default=True)
    reason = db.Column(db.String(200))  # Optional reason for unavailability

    __table_args__ = (
        db.UniqueConstraint('employee_id', 'date', name='unique_employee_date_availability'),
    )

    def __repr__(self):
        status = "available" if self.is_available else "unavailable"
        return f'<EmployeeAvailability {self.employee_id} on {self.date}: {status}>'


class EmployeeTimeOff(db.Model):
    """
    Time off requests and scheduled absences
    Employees are unavailable during these date ranges
    """
    __tablename__ = 'employee_time_off'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_id = db.Column(db.String(50), db.ForeignKey('employees.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.Index('idx_employee_time_off_dates', 'employee_id', 'start_date', 'end_date'),
    )

    def __repr__(self):
        return f'<EmployeeTimeOff {self.employee_id}: {self.start_date} to {self.end_date}>'
```

---

#### **Step 2.2: Test Model Extraction**

**System Prompt:**
```
Test that the extracted models work correctly before proceeding.
Create a minimal test script that imports models and creates tables.
DO NOT modify app.py yet - this is just validation.
```

Create `scheduler_app/test_model_extraction.py`:

```python
"""
Temporary test script to validate model extraction
DELETE THIS FILE after refactoring is complete
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Initialize Flask and database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Initialize models with database instance
from models import employee, event, schedule, availability

employee.init_db(db)
event.init_db(db)
schedule.init_db(db)
availability.init_db(db)

# Import model classes
from models import (
    Employee, Event, Schedule,
    EmployeeWeeklyAvailability, EmployeeAvailability, EmployeeTimeOff
)

# Test database creation
with app.app_context():
    db.create_all()
    print("✅ Database tables created successfully")

    # Test model creation
    emp = Employee(id='TEST001', name='Test Employee')
    db.session.add(emp)
    db.session.commit()
    print(f"✅ Created employee: {emp}")

    # Test query
    found = Employee.query.filter_by(id='TEST001').first()
    print(f"✅ Retrieved employee: {found}")

    # Test method
    can_work = found.can_work_event_type('Core')
    print(f"✅ Method call successful: can_work_event_type('Core') = {can_work}")

print("\n🎉 All model extraction tests passed!")
```

**Run the test:**
```bash
cd scheduler_app
python test_model_extraction.py
```

**Expected Output:**
```
✅ Database tables created successfully
✅ Created employee: <Employee TEST001: Test Employee>
✅ Retrieved employee: <Employee TEST001: Test Employee>
✅ Method call successful: can_work_event_type('Core') = True

🎉 All model extraction tests passed!
```

**If tests pass:**
- ✅ Models are correctly extracted
- ✅ Imports work properly
- ✅ Database operations function
- ✅ Methods are accessible

**If tests fail:**
- Check import paths
- Verify `init_db()` was called
- Check for typos in model definitions

---

### **Phase 3: Extract Route Blueprints**

#### **Step 3.1: Create Blueprint Structure**

**System Prompt:**
```
Extract routes from app.py into Flask Blueprints.
Group routes by functionality:
- auth_bp: Login/logout/authentication
- main_bp: Dashboard, calendar views
- events_bp: Event management (schedule, unscheduled)
- employees_bp: Employee management CRUD
- api_bp: All /api/* endpoints
- admin_bp: Sync admin, API testing

Create blueprints one at a time and test each before proceeding.
```

**Step 3.1a: Create routes/auth.py**

**System Prompt:**
```
Read app.py and find all authentication-related routes:
- /login (GET and POST)
- /logout
- Any session management functions

Extract these to routes/auth.py as a Blueprint.
```

Create `scheduler_app/routes/auth.py`:

```python
"""
Authentication routes blueprint
Handles user login, logout, and session management
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# Session store (will be moved to proper session management later)
session_store = {}


def is_authenticated():
    """Check if current user is authenticated"""
    return session.get('authenticated', False)


def require_authentication():
    """Decorator to require authentication for routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not is_authenticated():
                return redirect(url_for('auth.login_page'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@auth_bp.route('/login', methods=['GET'])
def login_page():
    """Display login page"""
    return render_template('login.html')


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Handle login form submission

    For now, this is a simple password check.
    TODO: Implement proper authentication with external API
    """
    username = request.form.get('username')
    password = request.form.get('password')

    # Simple authentication check (replace with proper auth)
    if username and password:
        session['authenticated'] = True
        session['username'] = username
        session_store[session.sid] = {
            'username': username,
            'authenticated': True
        }
        logger.info(f"User {username} logged in successfully")
        return redirect(url_for('main.index'))
    else:
        flash('Invalid username or password', 'error')
        return redirect(url_for('auth.login_page'))


@auth_bp.route('/logout', methods=['POST', 'GET'])
def logout():
    """Handle user logout"""
    username = session.get('username', 'Unknown')
    session.clear()
    logger.info(f"User {username} logged out")
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('auth.login_page'))


@auth_bp.route('/api/auth/status', methods=['GET'])
def auth_status():
    """Check authentication status (AJAX endpoint)"""
    return jsonify({
        'authenticated': is_authenticated(),
        'username': session.get('username')
    })
```

**Why This Structure:**
- Blueprint keeps auth separate from other routes
- Decorator pattern for protecting routes
- Session management centralized
- Ready for future enhancement (OAuth, API auth, etc.)

---

**Step 3.1b: Create routes/main.py**

Create `scheduler_app/routes/main.py`:

```python
"""
Main application routes blueprint
Handles dashboard, calendar, and primary UI views
"""
from flask import Blueprint, render_template, request
from models import Event, Employee, Schedule
from routes.auth import require_authentication
import logging

logger = logging.getLogger(__name__)

# Create blueprint
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@require_authentication()
def index():
    """
    Dashboard view showing unscheduled events

    Displays prioritized list of events that need scheduling,
    sorted by start date then due date.
    """
    unscheduled_events = Event.query.filter_by(is_scheduled=False)\
        .order_by(Event.start_datetime, Event.due_datetime)\
        .all()

    logger.info(f"Dashboard loaded with {len(unscheduled_events)} unscheduled events")

    return render_template('index.html', events=unscheduled_events)


@main_bp.route('/calendar')
@require_authentication()
def calendar():
    """
    Calendar view of all scheduled events

    Shows monthly calendar with scheduled events.
    Allows navigation between months and quick event details.
    """
    # Get all scheduled events
    schedules = Schedule.query.all()

    # TODO: Add month filtering based on query params
    # month = request.args.get('month', datetime.now().month)
    # year = request.args.get('year', datetime.now().year)

    logger.info(f"Calendar view accessed with {len(schedules)} scheduled events")

    return render_template('calendar.html', schedules=schedules)


@main_bp.route('/unscheduled')
@require_authentication()
def unscheduled():
    """
    Detailed view of unscheduled events

    Similar to dashboard but with additional filtering and sorting options.
    """
    # Get filter parameters
    event_type = request.args.get('event_type')
    store_name = request.args.get('store')

    query = Event.query.filter_by(is_scheduled=False)

    if event_type:
        query = query.filter_by(event_type=event_type)
    if store_name:
        query = query.filter(Event.store_name.like(f'%{store_name}%'))

    events = query.order_by(Event.start_datetime, Event.due_datetime).all()

    logger.info(f"Unscheduled view: {len(events)} events (filters: type={event_type}, store={store_name})")

    return render_template('unscheduled.html', events=events)
```

---

**Step 3.1c: Create routes/events.py**

Create `scheduler_app/routes/events.py`:

```python
"""
Event management routes blueprint
Handles scheduling, event details, and event operations
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models import Event, Employee, Schedule, EmployeeTimeOff, EmployeeAvailability
from routes.auth import require_authentication
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

# Create blueprint
events_bp = Blueprint('events', __name__, url_prefix='/events')


@events_bp.route('/schedule/<int:event_id>')
@require_authentication()
def schedule_event(event_id):
    """
    Display scheduling form for a specific event

    Shows event details and interactive form to assign employee and datetime.
    Form includes:
    - Date picker (constrained to event start/due dates)
    - Employee dropdown (dynamically filtered by availability)
    - Time picker
    """
    event = Event.query.get_or_404(event_id)

    if event.is_scheduled:
        flash('This event has already been scheduled', 'warning')
        return redirect(url_for('main.index'))

    logger.info(f"Scheduling form opened for event {event.project_ref_num}")

    return render_template('schedule.html', event=event)


@events_bp.route('/save_schedule', methods=['POST'])
@require_authentication()
def save_schedule():
    """
    Save a new schedule assignment

    Validates:
    - Event exists and is unscheduled
    - Date is within event constraints
    - Employee is available
    - No conflicts exist

    On success:
    - Creates Schedule record
    - Marks Event as scheduled
    - Updates event condition
    """
    try:
        event_id = request.form.get('event_id')
        employee_id = request.form.get('employee_id')
        schedule_date = request.form.get('scheduled_date')
        start_time = request.form.get('start_time')

        # Validate inputs
        if not all([event_id, employee_id, schedule_date, start_time]):
            flash('All fields are required', 'error')
            return redirect(url_for('events.schedule_event', event_id=event_id))

        # Get event
        event = Event.query.get(event_id)
        if not event:
            flash('Event not found', 'error')
            return redirect(url_for('main.index'))

        if event.is_scheduled:
            flash('Event is already scheduled', 'error')
            return redirect(url_for('main.index'))

        # Combine date and time
        schedule_datetime = datetime.strptime(f'{schedule_date} {start_time}', '%Y-%m-%d %H:%M')

        # Validate date is within event constraints
        if not (event.start_datetime.date() <= schedule_datetime.date() <= event.due_datetime.date()):
            flash('Schedule date must be between event start and due dates', 'error')
            return redirect(url_for('events.schedule_event', event_id=event_id))

        # Check employee availability
        employee = Employee.query.get(employee_id)
        if not employee or not employee.is_active:
            flash('Invalid or inactive employee', 'error')
            return redirect(url_for('events.schedule_event', event_id=event_id))

        # Check for conflicts
        existing_schedule = Schedule.query.filter_by(
            employee_id=employee_id,
            schedule_datetime=schedule_datetime
        ).first()

        if existing_schedule:
            flash('Employee is already scheduled at this time', 'error')
            return redirect(url_for('events.schedule_event', event_id=event_id))

        # Create schedule
        schedule = Schedule(
            event_ref_num=event.project_ref_num,
            employee_id=employee_id,
            schedule_datetime=schedule_datetime
        )

        # Update event status
        event.is_scheduled = True
        event.condition = 'Scheduled'

        # Save to database
        from flask import current_app
        db = current_app.extensions['sqlalchemy']
        db.session.add(schedule)
        db.session.commit()

        logger.info(f"Event {event.project_ref_num} scheduled to {employee_id} at {schedule_datetime}")
        flash('Event scheduled successfully', 'success')

        return redirect(url_for('main.index'))

    except Exception as e:
        logger.error(f"Error saving schedule: {str(e)}")
        db.session.rollback()
        flash('An error occurred while saving the schedule', 'error')
        return redirect(url_for('events.schedule_event', event_id=event_id))
```

---

**Step 3.1d: Create routes/api.py**

**System Prompt:**
```
Extract all /api/* routes from app.py into routes/api.py.
These are AJAX endpoints that return JSON.
Include: available_employees, import/export, sync operations.
```

Create `scheduler_app/routes/api.py`:

```python
"""
API routes blueprint
Handles all AJAX/JSON API endpoints
"""
from flask import Blueprint, jsonify, request, send_file, current_app
from models import Employee, Event, Schedule, EmployeeTimeOff, EmployeeAvailability
from datetime import datetime, date
import csv
import io
import logging

logger = logging.getLogger(__name__)

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/available_employees/<date_str>')
def available_employees(date_str):
    """
    Get list of available employees for a specific date

    Returns employees who:
    - Are active
    - Don't have another event scheduled on this date
    - Aren't on time off
    - Match weekly availability pattern

    Args:
        date_str: Date in YYYY-MM-DD format

    Returns:
        JSON list of available employees with id and name
    """
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Get all scheduled employee IDs for this date
        scheduled_employees = db.session.query(Schedule.employee_id)\
            .filter(db.func.date(Schedule.schedule_datetime) == target_date)\
            .all()
        scheduled_ids = [emp[0] for emp in scheduled_employees]

        # Get employees on time off
        time_off_employees = db.session.query(EmployeeTimeOff.employee_id)\
            .filter(
                EmployeeTimeOff.start_date <= target_date,
                EmployeeTimeOff.end_date >= target_date
            ).all()
        time_off_ids = [emp[0] for emp in time_off_employees]

        # Combine unavailable IDs
        unavailable_ids = set(scheduled_ids + time_off_ids)

        # Get available employees
        available = Employee.query.filter(
            Employee.is_active == True,
            ~Employee.id.in_(unavailable_ids)
        ).all()

        result = [{'id': emp.id, 'name': emp.name} for emp in available]

        logger.info(f"Available employees for {date_str}: {len(result)} found")

        return jsonify(result)

    except ValueError:
        logger.error(f"Invalid date format: {date_str}")
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        logger.error(f"Error fetching available employees: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/import/events', methods=['POST'])
def import_events():
    """
    Import events from WorkBankVisits.csv file

    Expected CSV format:
    - Project Name
    - Project Reference Number
    - Location MVID
    - Store Number
    - Store Name
    - Start Date/Time
    - Due Date/Time
    - Estimated Time

    Returns:
        JSON with import statistics
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'File must be a CSV'}), 400

        # Read CSV
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)

        imported = 0
        skipped = 0
        errors = []

        for row in csv_reader:
            try:
                # Check if event already exists
                ref_num = int(row['Project Reference Number'])
                existing = Event.query.filter_by(project_ref_num=ref_num).first()

                if existing:
                    skipped += 1
                    continue

                # Create new event
                event = Event(
                    project_name=row['Project Name'],
                    project_ref_num=ref_num,
                    location_mvid=row.get('Location MVID'),
                    store_number=int(row['Store Number']) if row.get('Store Number') else None,
                    store_name=row.get('Store Name'),
                    start_datetime=datetime.strptime(row['Start Date/Time'], '%Y-%m-%d %H:%M:%S'),
                    due_datetime=datetime.strptime(row['Due Date/Time'], '%Y-%m-%d %H:%M:%S'),
                    estimated_time=int(row['Estimated Time']) if row.get('Estimated Time') else None
                )

                # Auto-detect event type
                event.event_type = event.detect_event_type()

                db.session.add(event)
                imported += 1

            except Exception as e:
                errors.append(f"Row {csv_reader.line_num}: {str(e)}")
                logger.error(f"Error importing row: {str(e)}")

        db.session.commit()

        logger.info(f"CSV import complete: {imported} imported, {skipped} skipped, {len(errors)} errors")

        return jsonify({
            'success': True,
            'imported': imported,
            'skipped': skipped,
            'errors': errors
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"CSV import failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/export/schedule', methods=['GET'])
def export_schedule():
    """
    Export scheduled events to CalendarSchedule.csv

    Returns CSV with all scheduled events including:
    - Event details
    - Employee assignment
    - Schedule datetime
    """
    try:
        # Query all schedules with joined data
        schedules = db.session.query(Schedule, Event, Employee)\
            .join(Event, Schedule.event_ref_num == Event.project_ref_num)\
            .join(Employee, Schedule.employee_id == Employee.id)\
            .all()

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'Project Name',
            'Project Reference Number',
            'Location MVID',
            'Store Number',
            'Store Name',
            'Schedule Date/Time',
            'Estimated Time',
            'Employee ID',
            'Rep Name'
        ])

        # Write data
        for schedule, event, employee in schedules:
            writer.writerow([
                event.project_name,
                event.project_ref_num,
                event.location_mvid,
                event.store_number,
                event.store_name,
                schedule.schedule_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                event.estimated_time,
                employee.id,
                employee.name
            ])

        # Create file response
        output.seek(0)

        logger.info(f"Exported {len(schedules)} scheduled events to CSV")

        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name='CalendarSchedule.csv'
        )

    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        return jsonify({'error': str(e)}), 500
```

---

**CONTINUE IN NEXT MESSAGE - This is Part 1 of the refactoring guide**

**Current Status:**
✅ Phase 1: Directory structure created
✅ Phase 2: Models extracted and tested
⏳ Phase 3: Routes extraction in progress (auth, main, events, api complete)
⬜ Phase 4: Services extraction
⬜ Phase 5: Update app.py to use new structure
⬜ Phase 6: Testing and validation
⬜ Phase 7: Cleanup

**Next Steps:**
1. Complete remaining blueprints (employees, admin)
2. Extract services layer
3. Update app.py initialization
4. Run comprehensive tests
5. Remove old code from app.py
6. Delete test files
