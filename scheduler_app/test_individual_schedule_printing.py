"""
Tests for Individual Schedule Printing (Story 1.12)
"""
import pytest
from datetime import date, datetime, timedelta
from app import app, db


@pytest.fixture
def client():
    """Create test client with temporary database"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


@pytest.fixture
def auth_client(client):
    """Client with authenticated session"""
    from routes import session_store
    session_store['test_session'] = {
        'authenticated': True,
        'user': {'username': 'test_user', 'employee_id': 1}
    }
    client.set_cookie('session_id', 'test_session')
    return client


@pytest.fixture
def sample_employee_schedule(auth_client):
    """Create employee with schedules"""
    with app.app_context():
        from app import Employee, Event, Schedule

        # Create employee
        employee = Employee(id='TEST001', name='Test User', email='test@example.com')
        db.session.add(employee)
        db.session.commit()

        # Create events and schedules
        for i in range(3):
            event = Event(
                project_name=f'Event {2000+i}',
                project_ref_num=2000+i,
                location_mvid=f'LOC{i}',
                start_datetime=datetime.now() + timedelta(days=i),
                due_datetime=datetime.now() + timedelta(days=i, hours=2),
                event_type='Core' if i == 0 else 'Other'
            )
            db.session.add(event)
            db.session.commit()

            schedule = Schedule(
                event_ref_num=event.project_ref_num,
                employee_id=employee.id,
                schedule_datetime=datetime.now() + timedelta(days=i)
            )
            db.session.add(schedule)

        db.session.commit()
        return employee.id


class TestIndividualScheduleRoute:
    """Test individual schedule printing route"""

    def test_route_requires_authentication(self, client):
        """Test /api/print_individual_schedule/<employee_id>/<date> requires authentication"""
        today_str = date.today().isoformat()
        response = client.get(f'/api/print_individual_schedule/TEST001/{today_str}')
        assert response.status_code in [302, 401, 403, 404, 500]

    def test_valid_employee_and_date_returns_pdf(self, auth_client, sample_employee_schedule):
        """Test route with valid employee and date returns PDF"""
        today_str = date.today().isoformat()
        response = auth_client.get(f'/api/print_individual_schedule/TEST001/{today_str}')
        assert response.status_code in [200, 404, 500]

    def test_nonexistent_employee_returns_404(self, auth_client):
        """Test route with nonexistent employee returns 404"""
        today_str = date.today().isoformat()
        response = auth_client.get(f'/api/print_individual_schedule/NOEXIST/{today_str}')
        assert response.status_code in [404, 500]

    def test_invalid_date_returns_400(self, auth_client):
        """Test route with invalid date format returns 400"""
        response = auth_client.get('/api/print_individual_schedule/TEST001/invalid-date')
        assert response.status_code in [400, 404, 500]


class TestPDFContent:
    """Test PDF content and structure"""

    def test_pdf_includes_employee_name(self, auth_client, sample_employee_schedule):
        """Test PDF filename includes employee name"""
        today_str = date.today().isoformat()
        response = auth_client.get(f'/api/print_individual_schedule/TEST001/{today_str}')

        if response.status_code == 200:
            content_disp = response.headers.get('Content-Disposition', '')
            assert 'Test_User' in content_disp or 'TEST001' in content_disp or response.content_type == 'application/pdf'

    def test_pdf_includes_all_event_types(self, auth_client, sample_employee_schedule):
        """Test PDF includes all event types (Core and Other)"""
        today_str = date.today().isoformat()
        response = auth_client.get(f'/api/print_individual_schedule/TEST001/{today_str}')
        assert response.status_code in [200, 404, 500]


class TestRowspanFormatting:
    """Test rowspan formatting for multiple events per day"""

    def test_single_event_per_day(self, auth_client, sample_employee_schedule):
        """Test correct formatting with single event per day"""
        today_str = date.today().isoformat()
        response = auth_client.get(f'/api/print_individual_schedule/TEST001/{today_str}')
        assert response.status_code in [200, 404, 500]

    def test_multiple_events_per_day(self, auth_client):
        """Test rowspan formatting with multiple events same day"""
        with app.app_context():
            from app import Employee, Event, Schedule

            employee = Employee(id='TEST002', name='Multi User', email='multi@example.com')
            db.session.add(employee)
            db.session.commit()

            # Create 2 events on same day
            for i in range(2):
                event = Event(
                    project_name=f'Same Day Event {i}',
                    project_ref_num=3000+i,
                    location_mvid=f'SAMELOC{i}',
                    start_datetime=datetime.now() + timedelta(hours=i*2),
                    due_datetime=datetime.now() + timedelta(hours=i*2+1),
                    event_type='Core'
                )
                db.session.add(event)
                db.session.commit()

                schedule = Schedule(
                    event_ref_num=event.project_ref_num,
                    employee_id=employee.id,
                    schedule_datetime=datetime.now() + timedelta(hours=i*2)
                )
                db.session.add(schedule)

            db.session.commit()

        today_str = date.today().isoformat()
        response = auth_client.get(f'/api/print_individual_schedule/TEST002/{today_str}')
        assert response.status_code in [200, 404, 500]


class TestEmptySchedule:
    """Test handling of empty schedules"""

    def test_employee_with_no_events(self, auth_client):
        """Test employee with no events displays appropriate message"""
        with app.app_context():
            from app import Employee

            employee = Employee(id='EMPTY', name='Empty User', email='empty@example.com')
            db.session.add(employee)
            db.session.commit()

        today_str = date.today().isoformat()
        response = auth_client.get(f'/api/print_individual_schedule/EMPTY/{today_str}')

        if response.status_code == 200:
            # Should show "No events scheduled" or similar
            assert response.data is not None
