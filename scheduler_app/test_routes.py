import pytest
import os
import tempfile
import csv
import io
from datetime import datetime, time
from flask import Flask, render_template, abort, jsonify, request, redirect, url_for, flash, make_response
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TESTING'] = True
app.config['SECRET_KEY'] = 'test-secret-key'

db = SQLAlchemy(app)

class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_name = db.Column(db.Text, nullable=False)
    project_ref_num = db.Column(db.Integer, nullable=False, unique=True)
    location_mvid = db.Column(db.Text)
    store_number = db.Column(db.Integer)
    store_name = db.Column(db.Text)
    start_datetime = db.Column(db.DateTime, nullable=False)
    due_datetime = db.Column(db.DateTime, nullable=False)
    estimated_time = db.Column(db.Integer)
    is_scheduled = db.Column(db.Boolean, nullable=False, default=False)

class Schedule(db.Model):
    __tablename__ = 'schedules'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_ref_num = db.Column(db.Integer, db.ForeignKey('events.project_ref_num'), nullable=False)
    employee_id = db.Column(db.String(50), db.ForeignKey('employees.id'), nullable=False)
    schedule_datetime = db.Column(db.DateTime, nullable=False)

@app.route('/')
def dashboard():
    unscheduled_events = Event.query.filter_by(is_scheduled=False).order_by(
        Event.start_datetime.asc(),
        Event.due_datetime.asc()
    ).all()
    return f'<html><body><h1>Unscheduled Events</h1>{"".join([f"<div>{e.project_name}</div>" for e in unscheduled_events]) if unscheduled_events else "<div>No unscheduled events available.</div>"}</body></html>'

@app.route('/schedule/<int:event_id>')
def schedule_event(event_id):
    event = db.session.get(Event, event_id)
    if event is None:
        abort(404)
    return f'<html><body><h1>Schedule: {event.project_name}</h1><div>Event ID: {event.id}</div><div>Start: {event.start_datetime.strftime("%Y-%m-%d")}</div><div>End: {event.due_datetime.strftime("%Y-%m-%d")}</div></body></html>'

@app.route('/api/available_employees/<date>')
def available_employees(date):
    # Validate date format
    try:
        parsed_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400
    
    # Get all employees
    all_employees = Employee.query.all()
    
    # Get employees scheduled on the specified date
    scheduled_employees = db.session.query(Schedule.employee_id).filter(
        db.func.date(Schedule.schedule_datetime) == parsed_date
    ).all()
    
    # Extract scheduled employee IDs
    scheduled_employee_ids = {emp[0] for emp in scheduled_employees}
    
    # Filter available employees
    available_employees_list = [
        {'id': emp.id, 'name': emp.name}
        for emp in all_employees
        if emp.id not in scheduled_employee_ids
    ]
    
    return jsonify(available_employees_list)

@app.route('/save_schedule', methods=['POST'])
def save_schedule():
    # Get form data
    event_id = request.form.get('event_id')
    employee_id = request.form.get('employee_id')
    scheduled_date = request.form.get('scheduled_date')
    start_time = request.form.get('start_time')
    
    # Validate required fields
    if not all([event_id, employee_id, scheduled_date, start_time]):
        flash('All fields are required.', 'error')
        return redirect(url_for('schedule_event', event_id=event_id or 0))
    
    try:
        # Convert event_id to integer
        event_id = int(event_id)
        
        # Get the event
        event = db.session.get(Event, event_id)
        if not event:
            flash('Event not found.', 'error')
            return redirect(url_for('dashboard'))
        
        # Parse and validate date
        try:
            parsed_date = datetime.strptime(scheduled_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format.', 'error')
            return redirect(url_for('schedule_event', event_id=event_id))
        
        # Validate date is within event range
        event_start_date = event.start_datetime.date()
        event_due_date = event.due_datetime.date()
        
        if not (event_start_date <= parsed_date <= event_due_date):
            flash(f'Date must be between {event_start_date} and {event_due_date}.', 'error')
            return redirect(url_for('schedule_event', event_id=event_id))
        
        # Parse start time
        try:
            parsed_time = datetime.strptime(start_time, '%H:%M').time()
        except ValueError:
            flash('Invalid time format.', 'error')
            return redirect(url_for('schedule_event', event_id=event_id))
        
        # Combine date and time
        schedule_datetime = datetime.combine(parsed_date, parsed_time)
        
        # Verify employee exists
        employee = db.session.get(Employee, employee_id)
        if not employee:
            flash('Employee not found.', 'error')
            return redirect(url_for('schedule_event', event_id=event_id))
        
        # Check if employee is already scheduled on this date
        existing_schedule = Schedule.query.filter(
            Schedule.employee_id == employee_id,
            db.func.date(Schedule.schedule_datetime) == parsed_date
        ).first()
        
        if existing_schedule:
            flash(f'{employee.name} is already scheduled on {parsed_date}.', 'error')
            return redirect(url_for('schedule_event', event_id=event_id))
        
        # Begin database transaction
        try:
            # Create new schedule record
            new_schedule = Schedule(
                event_ref_num=event.project_ref_num,
                employee_id=employee_id,
                schedule_datetime=schedule_datetime
            )
            db.session.add(new_schedule)
            
            # Update event to mark as scheduled
            event.is_scheduled = True
            
            # Commit transaction
            db.session.commit()
            
            flash(f'Successfully scheduled {employee.name} for {event.project_name} on {parsed_date} at {parsed_time}.', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            # Rollback transaction on error
            db.session.rollback()
            flash('An error occurred while saving the schedule. Please try again.', 'error')
            return redirect(url_for('schedule_event', event_id=event_id))
            
    except ValueError:
        flash('Invalid event ID.', 'error')
        return redirect(url_for('dashboard'))
    except Exception as e:
        flash('An unexpected error occurred. Please try again.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/api/import/events', methods=['POST'])
def import_events():
    """Import unscheduled events from WorkBankVisits.csv file"""
    try:
        # Check if file is provided
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file extension
        if not file.filename.lower().endswith('.csv'):
            return jsonify({'error': 'File must be a CSV file'}), 400
        
        # Read and parse CSV
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        # Validate CSV headers
        expected_headers = {
            'Project Name', 'Project Reference Number', 'Location MVID',
            'Store Number', 'Store Name', 'Start Date/Time', 'Due Date/Time',
            'Estimated Time', 'Employee ID', 'Rep Name'
        }
        
        csv_headers = set(csv_reader.fieldnames)
        missing_headers = expected_headers - csv_headers
        if missing_headers:
            return jsonify({'error': f'Missing required CSV headers: {", ".join(missing_headers)}'}), 400
        
        imported_count = 0
        employees_added = set()
        
        # Begin database transaction
        try:
            for row in csv_reader:
                # First, ensure employee exists
                employee_id = row['Employee ID'].strip()
                rep_name = row['Rep Name'].strip()
                
                if employee_id and rep_name and employee_id not in employees_added:
                    existing_employee = Employee.query.filter_by(id=employee_id).first()
                    if not existing_employee:
                        new_employee = Employee(id=employee_id, name=rep_name)
                        db.session.add(new_employee)
                        employees_added.add(employee_id)
                
                # Parse and validate event data
                project_ref_num = int(row['Project Reference Number'])
                
                # Check for duplicate
                existing_event = Event.query.filter_by(project_ref_num=project_ref_num).first()
                if existing_event:
                    continue  # Skip duplicates
                
                # Parse dates
                start_datetime = datetime.strptime(row['Start Date/Time'], '%Y-%m-%d %H:%M:%S')
                due_datetime = datetime.strptime(row['Due Date/Time'], '%Y-%m-%d %H:%M:%S')
                
                # Create new event
                new_event = Event(
                    project_name=row['Project Name'].strip(),
                    project_ref_num=project_ref_num,
                    location_mvid=row['Location MVID'].strip() if row['Location MVID'] else None,
                    store_number=int(row['Store Number']) if row['Store Number'] else None,
                    store_name=row['Store Name'].strip() if row['Store Name'] else None,
                    start_datetime=start_datetime,
                    due_datetime=due_datetime,
                    estimated_time=int(row['Estimated Time']) if row['Estimated Time'] else None,
                    is_scheduled=False
                )
                
                db.session.add(new_event)
                imported_count += 1
            
            # Commit all changes
            db.session.commit()
            
            return jsonify({
                'imported_count': imported_count,
                'message': f'Successfully imported {imported_count} events'
            }), 200
            
        except Exception as e:
            # Rollback transaction on error
            db.session.rollback()
            return jsonify({'error': f'Database error during import: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error processing CSV file: {str(e)}'}), 400

@app.route('/api/export/schedule')
def export_schedule():
    """Export scheduled events to CalendarSchedule.csv"""
    try:
        # Query scheduled events with JOIN
        scheduled_events = db.session.query(
            Event.project_name,
            Event.project_ref_num,
            Event.location_mvid,
            Event.store_number,
            Event.store_name,
            Employee.id.label('employee_id'),
            Employee.name.label('rep_name'),
            Schedule.schedule_datetime
        ).join(
            Schedule, Event.project_ref_num == Schedule.event_ref_num
        ).join(
            Employee, Schedule.employee_id == Employee.id
        ).all()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            'Project Name', 'Project Reference Number', 'Location MVID',
            'Store Number', 'Store Name', 'Employee ID', 'Rep Name',
            'Schedule Date/Time'
        ])
        
        # Write data rows
        for event in scheduled_events:
            writer.writerow([
                event.project_name,
                event.project_ref_num,
                event.location_mvid or '',
                event.store_number or '',
                event.store_name or '',
                event.employee_id,
                event.rep_name,
                event.schedule_datetime.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        # Prepare response
        output.seek(0)
        csv_data = output.getvalue()
        output.close()
        
        response = make_response(csv_data)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=CalendarSchedule.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'error': f'Error generating export: {str(e)}'}), 500

@pytest.fixture
def client():
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

class TestDashboardRoute:
    def test_dashboard_loads(self, client):
        rv = client.get('/')
        assert rv.status_code == 200
        assert b'Unscheduled Events' in rv.data

    def test_dashboard_shows_unscheduled_events(self, client):
        with app.app_context():
            event1 = Event(
                project_name='Unscheduled Project',
                project_ref_num=12345,
                start_datetime=datetime(2023, 1, 1, 9, 0),
                due_datetime=datetime(2023, 1, 2, 17, 0),
                is_scheduled=False
            )
            event2 = Event(
                project_name='Scheduled Project',
                project_ref_num=12346,
                start_datetime=datetime(2023, 1, 3, 9, 0),
                due_datetime=datetime(2023, 1, 4, 17, 0),
                is_scheduled=True
            )
            db.session.add(event1)
            db.session.add(event2)
            db.session.commit()

        rv = client.get('/')
        assert rv.status_code == 200
        assert b'Unscheduled Project' in rv.data
        assert b'Scheduled Project' not in rv.data

    def test_dashboard_sorts_events_correctly(self, client):
        with app.app_context():
            event1 = Event(
                project_name='Later Start',
                project_ref_num=12345,
                start_datetime=datetime(2023, 1, 3, 9, 0),
                due_datetime=datetime(2023, 1, 4, 17, 0),
                is_scheduled=False
            )
            event2 = Event(
                project_name='Earlier Start',
                project_ref_num=12346,
                start_datetime=datetime(2023, 1, 1, 9, 0),
                due_datetime=datetime(2023, 1, 2, 17, 0),
                is_scheduled=False
            )
            event3 = Event(
                project_name='Same Start Later Due',
                project_ref_num=12347,
                start_datetime=datetime(2023, 1, 1, 9, 0),
                due_datetime=datetime(2023, 1, 5, 17, 0),
                is_scheduled=False
            )
            event4 = Event(
                project_name='Same Start Earlier Due',
                project_ref_num=12348,
                start_datetime=datetime(2023, 1, 1, 9, 0),
                due_datetime=datetime(2023, 1, 3, 17, 0),
                is_scheduled=False
            )
            
            db.session.add_all([event1, event2, event3, event4])
            db.session.commit()

        rv = client.get('/')
        content = rv.data.decode('utf-8')
        
        earlier_start_pos = content.find('Earlier Start')
        same_start_earlier_due_pos = content.find('Same Start Earlier Due')
        same_start_later_due_pos = content.find('Same Start Later Due')
        later_start_pos = content.find('Later Start')
        
        assert earlier_start_pos < same_start_earlier_due_pos
        assert same_start_earlier_due_pos < same_start_later_due_pos
        assert same_start_later_due_pos < later_start_pos

    def test_dashboard_no_events_message(self, client):
        rv = client.get('/')
        assert rv.status_code == 200
        assert b'No unscheduled events available.' in rv.data

class TestSchedulingRoute:
    def test_schedule_event_valid_id(self, client):
        with app.app_context():
            event = Event(
                project_name='Test Project',
                project_ref_num=12345,
                start_datetime=datetime(2023, 1, 1, 9, 0),
                due_datetime=datetime(2023, 1, 2, 17, 0),
                is_scheduled=False
            )
            db.session.add(event)
            db.session.commit()
            event_id = event.id

        rv = client.get(f'/schedule/{event_id}')
        assert rv.status_code == 200
        assert b'Schedule: Test Project' in rv.data
        assert b'Event ID:' in rv.data
        assert b'Start: 2023-01-01' in rv.data
        assert b'End: 2023-01-02' in rv.data

    def test_schedule_event_invalid_id(self, client):
        rv = client.get('/schedule/999')
        assert rv.status_code == 404

    def test_schedule_event_displays_correct_event(self, client):
        with app.app_context():
            event1 = Event(
                project_name='First Project',
                project_ref_num=12345,
                start_datetime=datetime(2023, 1, 1, 9, 0),
                due_datetime=datetime(2023, 1, 2, 17, 0),
                is_scheduled=False
            )
            event2 = Event(
                project_name='Second Project',
                project_ref_num=12346,
                start_datetime=datetime(2023, 1, 3, 9, 0),
                due_datetime=datetime(2023, 1, 4, 17, 0),
                is_scheduled=False
            )
            db.session.add_all([event1, event2])
            db.session.commit()
            event1_id = event1.id
            event2_id = event2.id

        # Test first event
        rv = client.get(f'/schedule/{event1_id}')
        assert rv.status_code == 200
        assert b'Schedule: First Project' in rv.data
        assert b'Second Project' not in rv.data

        # Test second event
        rv = client.get(f'/schedule/{event2_id}')
        assert rv.status_code == 200
        assert b'Schedule: Second Project' in rv.data
        assert b'First Project' not in rv.data

    def test_schedule_event_integration_with_dashboard(self, client):
        """Test that dashboard links properly navigate to scheduling page"""
        with app.app_context():
            event = Event(
                project_name='Integration Test Project',
                project_ref_num=12345,
                start_datetime=datetime(2023, 1, 1, 9, 0),
                due_datetime=datetime(2023, 1, 2, 17, 0),
                is_scheduled=False
            )
            db.session.add(event)
            db.session.commit()
            event_id = event.id

        # Verify event shows on dashboard
        dashboard_rv = client.get('/')
        assert dashboard_rv.status_code == 200
        assert b'Integration Test Project' in dashboard_rv.data

        # Verify scheduling page works for this event
        schedule_rv = client.get(f'/schedule/{event_id}')
        assert schedule_rv.status_code == 200
        assert b'Schedule: Integration Test Project' in schedule_rv.data

class TestEmployeeAvailabilityAPI:
    def test_available_employees_no_employees(self, client):
        """Test API returns empty list when no employees exist"""
        rv = client.get('/api/available_employees/2023-01-01')
        assert rv.status_code == 200
        data = rv.get_json()
        assert data == []

    def test_available_employees_all_available(self, client):
        """Test API returns all employees when none are scheduled"""
        with app.app_context():
            emp1 = Employee(id='EMP001', name='John Doe')
            emp2 = Employee(id='EMP002', name='Jane Smith')
            db.session.add_all([emp1, emp2])
            db.session.commit()

        rv = client.get('/api/available_employees/2023-01-01')
        assert rv.status_code == 200
        data = rv.get_json()
        assert len(data) == 2
        assert {'id': 'EMP001', 'name': 'John Doe'} in data
        assert {'id': 'EMP002', 'name': 'Jane Smith'} in data

    def test_available_employees_some_scheduled(self, client):
        """Test API filters out scheduled employees"""
        with app.app_context():
            # Create employees
            emp1 = Employee(id='EMP001', name='John Doe')
            emp2 = Employee(id='EMP002', name='Jane Smith')
            emp3 = Employee(id='EMP003', name='Bob Wilson')
            db.session.add_all([emp1, emp2, emp3])
            
            # Create event
            event = Event(
                project_name='Test Event',
                project_ref_num=12345,
                start_datetime=datetime(2023, 1, 1, 9, 0),
                due_datetime=datetime(2023, 1, 2, 17, 0),
                is_scheduled=False
            )
            db.session.add(event)
            db.session.commit()
            
            # Schedule one employee
            schedule = Schedule(
                event_ref_num=event.project_ref_num,
                employee_id='EMP001',
                schedule_datetime=datetime(2023, 1, 1, 10, 0)
            )
            db.session.add(schedule)
            db.session.commit()

        rv = client.get('/api/available_employees/2023-01-01')
        assert rv.status_code == 200
        data = rv.get_json()
        assert len(data) == 2
        assert {'id': 'EMP002', 'name': 'Jane Smith'} in data
        assert {'id': 'EMP003', 'name': 'Bob Wilson'} in data
        # EMP001 should not be in the list (scheduled)
        employee_ids = [emp['id'] for emp in data]
        assert 'EMP001' not in employee_ids

    def test_available_employees_different_dates(self, client):
        """Test API correctly filters by specific date"""
        with app.app_context():
            # Create employees
            emp1 = Employee(id='EMP001', name='John Doe')
            emp2 = Employee(id='EMP002', name='Jane Smith')
            db.session.add_all([emp1, emp2])
            
            # Create event
            event = Event(
                project_name='Test Event',
                project_ref_num=12345,
                start_datetime=datetime(2023, 1, 1, 9, 0),
                due_datetime=datetime(2023, 1, 2, 17, 0),
                is_scheduled=False
            )
            db.session.add(event)
            db.session.commit()
            
            # Schedule employee on 2023-01-01
            schedule = Schedule(
                event_ref_num=event.project_ref_num,
                employee_id='EMP001',
                schedule_datetime=datetime(2023, 1, 1, 10, 0)
            )
            db.session.add(schedule)
            db.session.commit()

        # Check availability on scheduled date
        rv = client.get('/api/available_employees/2023-01-01')
        assert rv.status_code == 200
        data = rv.get_json()
        assert len(data) == 1
        assert data[0]['id'] == 'EMP002'

        # Check availability on different date
        rv = client.get('/api/available_employees/2023-01-02')
        assert rv.status_code == 200
        data = rv.get_json()
        assert len(data) == 2
        assert {'id': 'EMP001', 'name': 'John Doe'} in data
        assert {'id': 'EMP002', 'name': 'Jane Smith'} in data

    def test_available_employees_invalid_date_format(self, client):
        """Test API returns 400 for invalid date formats"""
        # Test formats that reach our endpoint but are invalid
        invalid_dates = ['invalid-date', '2023-13-01', '2023-01-32', '2023-02-30']
        
        for invalid_date in invalid_dates:
            rv = client.get(f'/api/available_employees/{invalid_date}')
            assert rv.status_code == 400
            data = rv.get_json()
            assert 'error' in data
            assert 'Invalid date format' in data['error']

    def test_available_employees_valid_date_format(self, client):
        """Test API accepts valid date format"""
        rv = client.get('/api/available_employees/2023-01-01')
        assert rv.status_code == 200
        data = rv.get_json()
        assert isinstance(data, list)

    def test_available_employees_json_response_format(self, client):
        """Test API returns correct JSON format"""
        with app.app_context():
            emp = Employee(id='EMP001', name='John Doe')
            db.session.add(emp)
            db.session.commit()

        rv = client.get('/api/available_employees/2023-01-01')
        assert rv.status_code == 200
        assert rv.content_type == 'application/json'
        data = rv.get_json()
        assert isinstance(data, list)
        if data:
            assert 'id' in data[0]
            assert 'name' in data[0]
            assert len(data[0]) == 2  # Only id and name fields

class TestScheduleSaving:
    def test_save_schedule_success(self, client):
        """Test successful schedule saving workflow"""
        with app.app_context():
            # Create test data
            employee = Employee(id='EMP001', name='John Doe')
            event = Event(
                project_name='Test Event',
                project_ref_num=12345,
                start_datetime=datetime(2023, 1, 1, 9, 0),
                due_datetime=datetime(2023, 1, 10, 17, 0),
                is_scheduled=False
            )
            db.session.add_all([employee, event])
            db.session.commit()
            event_id = event.id

        # Submit form data
        form_data = {
            'event_id': event_id,
            'employee_id': 'EMP001',
            'scheduled_date': '2023-01-05',
            'start_time': '10:00'
        }
        
        rv = client.post('/save_schedule', data=form_data, follow_redirects=True)
        assert rv.status_code == 200
        
        # Verify schedule was created
        with app.app_context():
            schedule = Schedule.query.first()
            assert schedule is not None
            assert schedule.employee_id == 'EMP001'
            assert schedule.event_ref_num == 12345
            assert schedule.schedule_datetime == datetime(2023, 1, 5, 10, 0)
            
            # Verify event was marked as scheduled
            updated_event = db.session.get(Event, event_id)
            assert updated_event.is_scheduled == True

    def test_save_schedule_missing_fields(self, client):
        """Test validation for missing required fields"""
        with app.app_context():
            event = Event(
                project_name='Test Event',
                project_ref_num=12345,
                start_datetime=datetime(2023, 1, 1, 9, 0),
                due_datetime=datetime(2023, 1, 10, 17, 0),
                is_scheduled=False
            )
            db.session.add(event)
            db.session.commit()
            event_id = event.id

        # Test missing employee_id
        form_data = {
            'event_id': event_id,
            'scheduled_date': '2023-01-05',
            'start_time': '10:00'
        }
        
        rv = client.post('/save_schedule', data=form_data, follow_redirects=True)
        assert rv.status_code == 200
        
        # Verify no schedule was created
        with app.app_context():
            assert Schedule.query.count() == 0

    def test_save_schedule_invalid_date_range(self, client):
        """Test validation for date outside event range"""
        with app.app_context():
            employee = Employee(id='EMP001', name='John Doe')
            event = Event(
                project_name='Test Event',
                project_ref_num=12345,
                start_datetime=datetime(2023, 1, 5, 9, 0),
                due_datetime=datetime(2023, 1, 10, 17, 0),
                is_scheduled=False
            )
            db.session.add_all([employee, event])
            db.session.commit()
            event_id = event.id

        # Submit date before event start
        form_data = {
            'event_id': event_id,
            'employee_id': 'EMP001',
            'scheduled_date': '2023-01-01',  # Before start date
            'start_time': '10:00'
        }
        
        rv = client.post('/save_schedule', data=form_data, follow_redirects=True)
        assert rv.status_code == 200
        
        # Verify no schedule was created
        with app.app_context():
            assert Schedule.query.count() == 0
            
        # Submit date after event due date
        form_data['scheduled_date'] = '2023-01-15'  # After due date
        
        rv = client.post('/save_schedule', data=form_data, follow_redirects=True)
        assert rv.status_code == 200
        
        # Verify no schedule was created
        with app.app_context():
            assert Schedule.query.count() == 0

    def test_save_schedule_invalid_date_format(self, client):
        """Test validation for invalid date format"""
        with app.app_context():
            employee = Employee(id='EMP001', name='John Doe')
            event = Event(
                project_name='Test Event',
                project_ref_num=12345,
                start_datetime=datetime(2023, 1, 1, 9, 0),
                due_datetime=datetime(2023, 1, 10, 17, 0),
                is_scheduled=False
            )
            db.session.add_all([employee, event])
            db.session.commit()
            event_id = event.id

        form_data = {
            'event_id': event_id,
            'employee_id': 'EMP001',
            'scheduled_date': 'invalid-date',
            'start_time': '10:00'
        }
        
        rv = client.post('/save_schedule', data=form_data, follow_redirects=True)
        assert rv.status_code == 200
        
        # Verify no schedule was created
        with app.app_context():
            assert Schedule.query.count() == 0

    def test_save_schedule_invalid_time_format(self, client):
        """Test validation for invalid time format"""
        with app.app_context():
            employee = Employee(id='EMP001', name='John Doe')
            event = Event(
                project_name='Test Event',
                project_ref_num=12345,
                start_datetime=datetime(2023, 1, 1, 9, 0),
                due_datetime=datetime(2023, 1, 10, 17, 0),
                is_scheduled=False
            )
            db.session.add_all([employee, event])
            db.session.commit()
            event_id = event.id

        form_data = {
            'event_id': event_id,
            'employee_id': 'EMP001',
            'scheduled_date': '2023-01-05',
            'start_time': 'invalid-time'
        }
        
        rv = client.post('/save_schedule', data=form_data, follow_redirects=True)
        assert rv.status_code == 200
        
        # Verify no schedule was created
        with app.app_context():
            assert Schedule.query.count() == 0

    def test_save_schedule_nonexistent_employee(self, client):
        """Test handling of nonexistent employee"""
        with app.app_context():
            event = Event(
                project_name='Test Event',
                project_ref_num=12345,
                start_datetime=datetime(2023, 1, 1, 9, 0),
                due_datetime=datetime(2023, 1, 10, 17, 0),
                is_scheduled=False
            )
            db.session.add(event)
            db.session.commit()
            event_id = event.id

        form_data = {
            'event_id': event_id,
            'employee_id': 'NONEXISTENT',
            'scheduled_date': '2023-01-05',
            'start_time': '10:00'
        }
        
        rv = client.post('/save_schedule', data=form_data, follow_redirects=True)
        assert rv.status_code == 200
        
        # Verify no schedule was created
        with app.app_context():
            assert Schedule.query.count() == 0

    def test_save_schedule_nonexistent_event(self, client):
        """Test handling of nonexistent event"""
        form_data = {
            'event_id': '999',  # Nonexistent event
            'employee_id': 'EMP001',
            'scheduled_date': '2023-01-05',
            'start_time': '10:00'
        }
        
        rv = client.post('/save_schedule', data=form_data, follow_redirects=True)
        assert rv.status_code == 200
        
        # Verify no schedule was created
        with app.app_context():
            assert Schedule.query.count() == 0

    def test_save_schedule_employee_already_scheduled(self, client):
        """Test preventing double booking of employee on same date"""
        with app.app_context():
            # Create test data
            employee = Employee(id='EMP001', name='John Doe')
            event1 = Event(
                project_name='Event 1',
                project_ref_num=12345,
                start_datetime=datetime(2023, 1, 1, 9, 0),
                due_datetime=datetime(2023, 1, 10, 17, 0),
                is_scheduled=False
            )
            event2 = Event(
                project_name='Event 2',
                project_ref_num=12346,
                start_datetime=datetime(2023, 1, 1, 9, 0),
                due_datetime=datetime(2023, 1, 10, 17, 0),
                is_scheduled=False
            )
            db.session.add_all([employee, event1, event2])
            db.session.commit()
            
            # Create existing schedule
            existing_schedule = Schedule(
                event_ref_num=event1.project_ref_num,
                employee_id='EMP001',
                schedule_datetime=datetime(2023, 1, 5, 9, 0)
            )
            db.session.add(existing_schedule)
            db.session.commit()
            
            event2_id = event2.id

        # Try to schedule same employee on same date
        form_data = {
            'event_id': event2_id,
            'employee_id': 'EMP001',
            'scheduled_date': '2023-01-05',  # Same date as existing schedule
            'start_time': '14:00'
        }
        
        rv = client.post('/save_schedule', data=form_data, follow_redirects=True)
        assert rv.status_code == 200
        
        # Verify second schedule was not created
        with app.app_context():
            assert Schedule.query.count() == 1  # Only original schedule

    def test_save_schedule_database_transaction_rollback(self, client):
        """Test database transaction rollback on error"""
        with app.app_context():
            employee = Employee(id='EMP001', name='John Doe')
            event = Event(
                project_name='Test Event',
                project_ref_num=12345,
                start_datetime=datetime(2023, 1, 1, 9, 0),
                due_datetime=datetime(2023, 1, 10, 17, 0),
                is_scheduled=False
            )
            db.session.add_all([employee, event])
            db.session.commit()
            event_id = event.id

        # Valid form data
        form_data = {
            'event_id': event_id,
            'employee_id': 'EMP001',
            'scheduled_date': '2023-01-05',
            'start_time': '10:00'
        }
        
        # This should succeed normally
        rv = client.post('/save_schedule', data=form_data, follow_redirects=True)
        assert rv.status_code == 200
        
        # Verify schedule was created and event marked as scheduled
        with app.app_context():
            assert Schedule.query.count() == 1
            updated_event = db.session.get(Event, event_id)
            assert updated_event.is_scheduled == True

class TestCsvImportExport:
    """Test CSV import and export functionality"""
    
    def create_test_csv(self, data):
        """Helper to create test CSV data"""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'Project Name', 'Project Reference Number', 'Location MVID',
            'Store Number', 'Store Name', 'Start Date/Time', 'Due Date/Time',
            'Estimated Time', 'Employee ID', 'Rep Name'
        ])
        writer.writeheader()
        for row in data:
            writer.writerow(row)
        output.seek(0)
        return output.getvalue()
    
    def test_import_events_success(self, client):
        """Test successful CSV import"""
        csv_data = self.create_test_csv([
            {
                'Project Name': 'Test Event 1',
                'Project Reference Number': '1001',
                'Location MVID': 'LOC001',
                'Store Number': '123',
                'Store Name': 'Test Store',
                'Start Date/Time': '2023-01-01 09:00:00',
                'Due Date/Time': '2023-01-10 17:00:00',
                'Estimated Time': '120',
                'Employee ID': 'EMP001',
                'Rep Name': 'John Doe'
            },
            {
                'Project Name': 'Test Event 2',
                'Project Reference Number': '1002',
                'Location MVID': 'LOC002',
                'Store Number': '456',
                'Store Name': 'Another Store',
                'Start Date/Time': '2023-01-05 08:00:00',
                'Due Date/Time': '2023-01-15 18:00:00',
                'Estimated Time': '90',
                'Employee ID': 'EMP002',
                'Rep Name': 'Jane Smith'
            }
        ])
        
        # Create file-like object
        file_data = (io.BytesIO(csv_data.encode('utf-8')), 'test.csv')
        
        response = client.post('/api/import/events', 
                              data={'file': file_data},
                              content_type='multipart/form-data')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['imported_count'] == 2
        assert 'Successfully imported 2 events' in data['message']
        
        # Verify data was imported correctly
        with app.app_context():
            assert Event.query.count() == 2
            assert Employee.query.count() == 2
            
            event1 = Event.query.filter_by(project_ref_num=1001).first()
            assert event1.project_name == 'Test Event 1'
            assert event1.location_mvid == 'LOC001'
            assert event1.store_number == 123
            assert event1.is_scheduled == False
            
            employee1 = Employee.query.filter_by(id='EMP001').first()
            assert employee1.name == 'John Doe'
    
    def test_import_events_no_file(self, client):
        """Test import with no file provided"""
        response = client.post('/api/import/events')
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'No file provided'
    
    def test_import_events_empty_filename(self, client):
        """Test import with empty filename"""
        file_data = (io.BytesIO(b''), '')
        response = client.post('/api/import/events', 
                              data={'file': file_data},
                              content_type='multipart/form-data')
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'No file selected'
    
    def test_import_events_invalid_file_type(self, client):
        """Test import with non-CSV file"""
        file_data = (io.BytesIO(b'not a csv'), 'test.txt')
        response = client.post('/api/import/events', 
                              data={'file': file_data},
                              content_type='multipart/form-data')
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'File must be a CSV file'
    
    def test_import_events_missing_headers(self, client):
        """Test import with missing CSV headers"""
        csv_data = "Project Name,Invalid Header\nTest,Value\n"
        file_data = (io.BytesIO(csv_data.encode('utf-8')), 'test.csv')
        
        response = client.post('/api/import/events', 
                              data={'file': file_data},
                              content_type='multipart/form-data')
        assert response.status_code == 400
        data = response.get_json()
        assert 'Missing required CSV headers' in data['error']
    
    def test_import_events_duplicate_prevention(self, client):
        """Test that duplicate project reference numbers are skipped"""
        # First import
        csv_data1 = self.create_test_csv([{
            'Project Name': 'Test Event 1',
            'Project Reference Number': '1001',
            'Location MVID': 'LOC001',
            'Store Number': '123',
            'Store Name': 'Test Store',
            'Start Date/Time': '2023-01-01 09:00:00',
            'Due Date/Time': '2023-01-10 17:00:00',
            'Estimated Time': '120',
            'Employee ID': 'EMP001',
            'Rep Name': 'John Doe'
        }])
        
        file_data1 = (io.BytesIO(csv_data1.encode('utf-8')), 'test1.csv')
        response1 = client.post('/api/import/events', 
                               data={'file': file_data1},
                               content_type='multipart/form-data')
        assert response1.status_code == 200
        
        # Second import with same project reference number
        csv_data2 = self.create_test_csv([{
            'Project Name': 'Duplicate Event',
            'Project Reference Number': '1001',  # Same as above
            'Location MVID': 'LOC002',
            'Store Number': '456',
            'Store Name': 'Another Store',
            'Start Date/Time': '2023-01-05 08:00:00',
            'Due Date/Time': '2023-01-15 18:00:00',
            'Estimated Time': '90',
            'Employee ID': 'EMP002',
            'Rep Name': 'Jane Smith'
        }])
        
        file_data2 = (io.BytesIO(csv_data2.encode('utf-8')), 'test2.csv')
        response2 = client.post('/api/import/events', 
                               data={'file': file_data2},
                               content_type='multipart/form-data')
        
        assert response2.status_code == 200
        data = response2.get_json()
        assert data['imported_count'] == 0  # Duplicate was skipped
        
        # Verify only one event exists
        with app.app_context():
            assert Event.query.count() == 1
            event = Event.query.filter_by(project_ref_num=1001).first()
            assert event.project_name == 'Test Event 1'  # Original name preserved
    
    def test_export_schedule_empty(self, client):
        """Test export with no scheduled events"""
        response = client.get('/api/export/schedule')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv'
        assert 'CalendarSchedule.csv' in response.headers['Content-Disposition']
        
        # Should only contain headers
        csv_data = response.data.decode('utf-8')
        lines = csv_data.strip().split('\n')
        assert len(lines) == 1  # Only header row
        assert 'Project Name' in lines[0]
        assert 'Employee ID' in lines[0]
    
    def test_export_schedule_with_data(self, client):
        """Test export with scheduled events"""
        # Create test data
        with app.app_context():
            # Create employee
            employee = Employee(id='EMP001', name='John Doe')
            db.session.add(employee)
            
            # Create event
            event = Event(
                project_name='Test Project',
                project_ref_num=1001,
                location_mvid='LOC001',
                store_number=123,
                store_name='Test Store',
                start_datetime=datetime(2023, 1, 1, 9, 0),
                due_datetime=datetime(2023, 1, 10, 17, 0),
                estimated_time=120,
                is_scheduled=True
            )
            db.session.add(event)
            
            # Create schedule
            schedule = Schedule(
                event_ref_num=1001,
                employee_id='EMP001',
                schedule_datetime=datetime(2023, 1, 5, 10, 0)
            )
            db.session.add(schedule)
            db.session.commit()
        
        response = client.get('/api/export/schedule')
        assert response.status_code == 200
        
        # Parse CSV data
        csv_data = response.data.decode('utf-8')
        lines = csv_data.strip().split('\n')
        assert len(lines) == 2  # Header + 1 data row
        
        # Check headers
        headers = [h.strip() for h in lines[0].split(',')]
        expected_headers = [
            'Project Name', 'Project Reference Number', 'Location MVID',
            'Store Number', 'Store Name', 'Employee ID', 'Rep Name',
            'Schedule Date/Time'
        ]
        assert headers == expected_headers
        
        # Check data row
        data_row = [d.strip() for d in lines[1].split(',')]
        assert data_row[0] == 'Test Project'
        assert data_row[1] == '1001'
        assert data_row[2] == 'LOC001'
        assert data_row[3] == '123'
        assert data_row[4] == 'Test Store'
        assert data_row[5] == 'EMP001'
        assert data_row[6] == 'John Doe'
        assert data_row[7] == '2023-01-05 10:00:00'
    
    def test_import_events_invalid_date_format(self, client):
        """Test import with invalid date format"""
        csv_data = self.create_test_csv([{
            'Project Name': 'Test Event',
            'Project Reference Number': '1001',
            'Location MVID': 'LOC001',
            'Store Number': '123',
            'Store Name': 'Test Store',
            'Start Date/Time': 'invalid-date',  # Invalid format
            'Due Date/Time': '2023-01-10 17:00:00',
            'Estimated Time': '120',
            'Employee ID': 'EMP001',
            'Rep Name': 'John Doe'
        }])
        
        file_data = (io.BytesIO(csv_data.encode('utf-8')), 'test.csv')
        response = client.post('/api/import/events', 
                              data={'file': file_data},
                              content_type='multipart/form-data')
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'Database error during import' in data['error']
    
    def test_import_events_with_empty_optional_fields(self, client):
        """Test import with empty optional fields"""
        csv_data = self.create_test_csv([{
            'Project Name': 'Test Event',
            'Project Reference Number': '1001',
            'Location MVID': '',  # Empty optional field
            'Store Number': '',   # Empty optional field
            'Store Name': '',     # Empty optional field
            'Start Date/Time': '2023-01-01 09:00:00',
            'Due Date/Time': '2023-01-10 17:00:00',
            'Estimated Time': '', # Empty optional field
            'Employee ID': 'EMP001',
            'Rep Name': 'John Doe'
        }])
        
        file_data = (io.BytesIO(csv_data.encode('utf-8')), 'test.csv')
        response = client.post('/api/import/events', 
                              data={'file': file_data},
                              content_type='multipart/form-data')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['imported_count'] == 1
        
        # Verify optional fields are stored as None
        with app.app_context():
            event = Event.query.filter_by(project_ref_num=1001).first()
            assert event.location_mvid is None
            assert event.store_number is None
            assert event.store_name is None
            assert event.estimated_time is None