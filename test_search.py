"""
Test suite for the universal event search functionality
Tests fuzzy search capabilities, filtering, and context-based searching
"""
import pytest
from datetime import datetime, timedelta
from flask import Flask, json, request, jsonify
from flask_sqlalchemy import SQLAlchemy

# Create test app and database
app = Flask(__name__)
app.config['TESTING'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'test-secret-key'

db = SQLAlchemy(app)


# Define models
class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    job_title = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    is_supervisor = db.Column(db.Boolean, default=False)


class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    external_id = db.Column(db.String(100))
    project_name = db.Column(db.Text, nullable=False)
    project_ref_num = db.Column(db.Integer, nullable=False, unique=True)
    location_mvid = db.Column(db.Text)
    store_name = db.Column(db.Text)
    event_type = db.Column(db.String(50))
    is_scheduled = db.Column(db.Boolean, nullable=False, default=False)
    condition = db.Column(db.String(50))
    start_datetime = db.Column(db.DateTime, nullable=False)
    due_datetime = db.Column(db.DateTime, nullable=False)
    last_synced = db.Column(db.DateTime)
    sync_status = db.Column(db.String(50))


class Schedule(db.Model):
    __tablename__ = 'schedules'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_ref_num = db.Column(db.Integer, db.ForeignKey('events.project_ref_num'), nullable=False)
    employee_id = db.Column(db.String(50), db.ForeignKey('employees.id'), nullable=False)
    schedule_datetime = db.Column(db.DateTime, nullable=False)
    external_id = db.Column(db.String(100))
    last_synced = db.Column(db.DateTime)
    sync_status = db.Column(db.String(50))


# Define the universal search API endpoint
@app.route('/api/universal_search')
def universal_search():
    """Universal search endpoint for events, employees, and schedules"""
    query = request.args.get('q', '').strip()
    context = request.args.get('context', 'all')  # all, scheduling, tracking, reporting
    filters = request.args.getlist('filters')  # Additional filters

    if not query:
        return jsonify({
            'results': [],
            'total': 0,
            'query': query,
            'context': context
        })

    results = {
        'events': [],
        'employees': [],
        'schedules': [],
        'total': 0
    }

    # Search Events
    if context in ['all', 'scheduling', 'tracking']:
        # Search by event name, project ref number, store name, or location
        event_query = Event.query.filter(
            db.or_(
                Event.project_name.ilike(f'%{query}%'),
                Event.project_ref_num == query if query.isdigit() else False,
                Event.store_name.ilike(f'%{query}%') if Event.store_name else False,
                Event.location_mvid.ilike(f'%{query}%') if Event.location_mvid else False
            )
        )

        # Apply context-specific filters
        if context == 'scheduling':
            event_query = event_query.filter_by(is_scheduled=False)

        # Apply additional filters
        if 'event_type' in [f.split(':')[0] for f in filters]:
            event_type = next(f.split(':')[1] for f in filters if f.startswith('event_type:'))
            event_query = event_query.filter_by(event_type=event_type)

        if 'status' in [f.split(':')[0] for f in filters]:
            status = next(f.split(':')[1] for f in filters if f.startswith('status:'))
            if status == 'scheduled':
                event_query = event_query.filter_by(is_scheduled=True)
            elif status == 'unscheduled':
                event_query = event_query.filter_by(is_scheduled=False)

        events = event_query.order_by(Event.start_datetime.asc()).limit(20).all()

        for event in events:
            # Calculate priority (days until deadline)
            days_remaining = (event.due_datetime.date() - datetime.now().date()).days
            if days_remaining <= 1:
                priority = 'critical'
                priority_color = 'red'
            elif days_remaining <= 7:
                priority = 'urgent'
                priority_color = 'yellow'
            else:
                priority = 'normal'
                priority_color = 'green'

            results['events'].append({
                'id': event.id,
                'project_ref_num': event.project_ref_num,
                'project_name': event.project_name,
                'store_name': event.store_name,
                'location_mvid': event.location_mvid,
                'start_datetime': event.start_datetime.isoformat(),
                'due_datetime': event.due_datetime.isoformat(),
                'event_type': event.event_type,
                'is_scheduled': event.is_scheduled,
                'priority': priority,
                'priority_color': priority_color,
                'days_remaining': days_remaining
            })

    # Search Employees
    if context in ['all', 'scheduling']:
        employee_query = Employee.query.filter(
            db.and_(
                Employee.is_active == True,
                db.or_(
                    Employee.name.ilike(f'%{query}%'),
                    Employee.id.ilike(f'%{query}%'),
                    Employee.email.ilike(f'%{query}%') if Employee.email else False
                )
            )
        )

        employees = employee_query.limit(20).all()

        for emp in employees:
            results['employees'].append({
                'id': emp.id,
                'name': emp.name,
                'email': emp.email,
                'job_title': emp.job_title,
                'is_supervisor': emp.is_supervisor
            })

    # Search Schedules (when tracking specific assignments)
    if context in ['all', 'tracking']:
        try:
            # Try searching by project ref number or employee ID
            schedule_query = db.session.query(Schedule, Event, Employee).join(
                Event, Schedule.event_ref_num == Event.project_ref_num
            ).join(
                Employee, Schedule.employee_id == Employee.id
            ).filter(
                db.or_(
                    Event.project_name.ilike(f'%{query}%'),
                    Event.project_ref_num == query if query.isdigit() else False,
                    Employee.name.ilike(f'%{query}%'),
                    Employee.id.ilike(f'%{query}%')
                )
            )

            schedules = schedule_query.limit(20).all()

            for schedule, event, employee in schedules:
                results['schedules'].append({
                    'id': schedule.id,
                    'event_ref_num': event.project_ref_num,
                    'event_name': event.project_name,
                    'employee_id': employee.id,
                    'employee_name': employee.name,
                    'schedule_datetime': schedule.schedule_datetime.isoformat(),
                    'event_type': event.event_type
                })
        except Exception as e:
            print(f"Error searching schedules: {e}")

    results['total'] = len(results['events']) + len(results['employees']) + len(results['schedules'])
    results['query'] = query
    results['context'] = context

    return jsonify(results)


@pytest.fixture
def setup_test_data():
    """Create test app with test database"""
    with app.app_context():
        db.create_all()

        # Create test employees
        emp1 = Employee(
            id='US123456',
            name='John Smith',
            email='john.smith@test.com',
            job_title='Field Specialist',
            is_active=True,
            is_supervisor=False
        )
        emp2 = Employee(
            id='US789012',
            name='Jane Doe',
            email='jane.doe@test.com',
            job_title='Supervisor',
            is_active=True,
            is_supervisor=True
        )
        db.session.add(emp1)
        db.session.add(emp2)

        # Create test events with various characteristics
        events_data = [
            {
                'external_id': 'evt_001',
                'project_name': '123456 Core Reset - Walmart Store',
                'project_ref_num': 123456,
                'location_mvid': '157384',
                'store_name': 'Walmart Supercenter #1234',
                'event_type': 'Core',
                'is_scheduled': False,
                'condition': 'Unstaffed'
            },
            {
                'external_id': 'evt_002',
                'project_name': 'Freeosk Maintenance - Target Store',
                'project_ref_num': 234567,
                'location_mvid': '157385',
                'store_name': 'Target Store #5678',
                'event_type': 'Freeosk',
                'is_scheduled': True,
                'condition': 'Staffed'
            },
            {
                'external_id': 'evt_003',
                'project_name': 'Digitals Update - Kroger',
                'project_ref_num': 345678,
                'location_mvid': '157386',
                'store_name': 'Kroger #9012',
                'event_type': 'Digitals',
                'is_scheduled': False,
                'condition': 'Unstaffed'
            },
            {
                'external_id': 'evt_004',
                'project_name': '456789 Supervisor Visit - Walmart',
                'project_ref_num': 456789,
                'location_mvid': '157387',
                'store_name': 'Walmart #3456',
                'event_type': 'Supervisor',
                'is_scheduled': True,
                'condition': 'Staffed'
            },
            {
                'external_id': 'evt_005',
                'project_name': 'Other Event - Special Project',
                'project_ref_num': 567890,
                'location_mvid': '157388',
                'store_name': 'Special Location',
                'event_type': 'Other',
                'is_scheduled': False,
                'condition': 'Unstaffed'
            }
        ]

        now = datetime.utcnow()
        for i, event_data in enumerate(events_data):
            event = Event(
                **event_data,
                start_datetime=now + timedelta(days=i),
                due_datetime=now + timedelta(days=i + 7),
                last_synced=now,
                sync_status='synced'
            )
            db.session.add(event)

        # Create schedules for scheduled events
        schedule1 = Schedule(
            event_ref_num=234567,
            employee_id='US123456',
            schedule_datetime=now + timedelta(days=1, hours=10),
            external_id='sch_001',
            last_synced=now,
            sync_status='synced'
        )
        schedule2 = Schedule(
            event_ref_num=456789,
            employee_id='US789012',
            schedule_datetime=now + timedelta(days=3, hours=12),
            external_id='sch_002',
            last_synced=now,
            sync_status='synced'
        )
        db.session.add(schedule1)
        db.session.add(schedule2)

        db.session.commit()

        yield

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(setup_test_data):
    """Create test client"""
    return app.test_client()


class TestUniversalSearch:
    """Test universal search functionality"""

    def test_search_by_project_name_exact(self, client):
        """Test searching by exact project name"""
        response = client.get('/api/universal_search?q=Core Reset')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['total'] > 0
        assert len(data['events']) > 0
        assert any('Core Reset' in event['project_name'] for event in data['events'])

    def test_search_by_project_name_fuzzy(self, client):
        """Test fuzzy search by partial project name"""
        # Should match "Core Reset", "Freeosk", etc.
        response = client.get('/api/universal_search?q=Core')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['total'] > 0
        assert any('Core' in event['project_name'] for event in data['events'])

    def test_search_case_insensitive(self, client):
        """Test case-insensitive search"""
        response = client.get('/api/universal_search?q=walmart')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['total'] > 0
        # Should find events with "Walmart" (capital W)
        assert any('Walmart' in event['store_name'] or 'Walmart' in event['project_name']
                  for event in data['events'])

    def test_search_by_project_ref_num(self, client):
        """Test searching by project reference number"""
        response = client.get('/api/universal_search?q=123456')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['total'] > 0
        assert any(event['project_ref_num'] == 123456 for event in data['events'])

    def test_search_by_store_name(self, client):
        """Test searching by store name"""
        response = client.get('/api/universal_search?q=Target')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['total'] > 0
        assert any('Target' in event['store_name'] for event in data['events'])

    def test_search_by_location_mvid(self, client):
        """Test searching by location MVID"""
        response = client.get('/api/universal_search?q=157384')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['total'] > 0
        assert any(event['location_mvid'] == '157384' for event in data['events'])

    def test_search_by_employee_name(self, client):
        """Test searching by employee name"""
        response = client.get('/api/universal_search?q=John Smith')
        assert response.status_code == 200
        data = json.loads(response.data)

        # Should find employee
        assert len(data['employees']) > 0
        assert any(emp['name'] == 'John Smith' for emp in data['employees'])

    def test_search_by_employee_id(self, client):
        """Test searching by employee ID"""
        response = client.get('/api/universal_search?q=US123456')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert len(data['employees']) > 0
        assert any(emp['id'] == 'US123456' for emp in data['employees'])

    def test_search_empty_query(self, client):
        """Test search with empty query"""
        response = client.get('/api/universal_search?q=')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['total'] == 0
        # Empty query returns minimal structure
        assert 'query' in data
        assert 'context' in data

    def test_search_no_results(self, client):
        """Test search with no matching results"""
        response = client.get('/api/universal_search?q=NonexistentXYZ123')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['total'] == 0
        assert len(data['events']) == 0

    def test_context_filter_all(self, client):
        """Test search with 'all' context"""
        response = client.get('/api/universal_search?q=Walmart&context=all')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['context'] == 'all'
        assert data['total'] > 0

    def test_context_filter_scheduling(self, client):
        """Test search with 'scheduling' context (unscheduled only)"""
        response = client.get('/api/universal_search?q=Core&context=scheduling')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['context'] == 'scheduling'
        # Should only return unscheduled events
        assert all(not event['is_scheduled'] for event in data['events'])

    def test_context_filter_tracking(self, client):
        """Test search with 'tracking' context"""
        response = client.get('/api/universal_search?q=Walmart&context=tracking')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['context'] == 'tracking'
        assert data['total'] > 0

    def test_filter_by_event_type(self, client):
        """Test filtering by event type"""
        response = client.get('/api/universal_search?q=Walmart&filters=event_type:Core')
        assert response.status_code == 200
        data = json.loads(response.data)

        # All returned events should be Core type
        assert all(event['event_type'] == 'Core' for event in data['events'])

    def test_filter_by_status_unscheduled(self, client):
        """Test filtering by unscheduled status"""
        response = client.get('/api/universal_search?q=Event&filters=status:unscheduled')
        assert response.status_code == 200
        data = json.loads(response.data)

        # All returned events should be unscheduled
        assert all(not event['is_scheduled'] for event in data['events'])

    def test_filter_by_status_scheduled(self, client):
        """Test filtering by scheduled status"""
        response = client.get('/api/universal_search?q=Walmart&filters=status:scheduled')
        assert response.status_code == 200
        data = json.loads(response.data)

        # All returned events should be scheduled
        assert all(event['is_scheduled'] for event in data['events'])

    def test_priority_calculation(self, client):
        """Test that priority is calculated correctly"""
        response = client.get('/api/universal_search?q=Event')
        assert response.status_code == 200
        data = json.loads(response.data)

        # Check that events have priority fields
        for event in data['events']:
            assert 'priority' in event
            assert 'priority_color' in event
            assert 'days_remaining' in event
            assert event['priority'] in ['critical', 'urgent', 'normal']

    def test_search_schedules(self, client):
        """Test searching schedules by event or employee"""
        response = client.get('/api/universal_search?q=John&context=tracking')
        assert response.status_code == 200
        data = json.loads(response.data)

        # Should find schedules associated with John Smith
        # Note: This depends on the schedule having the employee
        assert data['total'] > 0

    def test_multiple_filters(self, client):
        """Test applying multiple filters at once"""
        response = client.get('/api/universal_search?q=Walmart&filters=event_type:Core&filters=status:unscheduled')
        assert response.status_code == 200
        data = json.loads(response.data)

        # Should only return Core events that are unscheduled
        for event in data['events']:
            assert event['event_type'] == 'Core'
            assert not event['is_scheduled']

    def test_result_limit(self, client):
        """Test that results are limited to prevent overwhelming response"""
        response = client.get('/api/universal_search?q=e')  # Very broad search
        assert response.status_code == 200
        data = json.loads(response.data)

        # Should be limited to 20 results per category
        assert len(data['events']) <= 20
        assert len(data['employees']) <= 20
        assert len(data['schedules']) <= 20

    def test_partial_match_fuzzy(self, client):
        """Test fuzzy matching with partial words"""
        # Search for partial word
        response = client.get('/api/universal_search?q=Digit')
        assert response.status_code == 200
        data = json.loads(response.data)

        # Should match "Digitals"
        assert data['total'] > 0
        assert any('Digit' in event['project_name'] for event in data['events'])

    def test_search_response_structure(self, client):
        """Test that search response has correct structure"""
        response = client.get('/api/universal_search?q=Walmart')
        assert response.status_code == 200
        data = json.loads(response.data)

        # Verify response structure
        assert 'events' in data
        assert 'employees' in data
        assert 'schedules' in data
        assert 'total' in data
        assert 'query' in data
        assert 'context' in data

        # Verify event structure
        if len(data['events']) > 0:
            event = data['events'][0]
            assert 'id' in event
            assert 'project_ref_num' in event
            assert 'project_name' in event
            assert 'store_name' in event
            assert 'event_type' in event
            assert 'is_scheduled' in event
            assert 'priority' in event
            assert 'days_remaining' in event


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
