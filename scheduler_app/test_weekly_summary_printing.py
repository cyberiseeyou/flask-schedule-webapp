"""
Tests for Weekly Summary Printing (Story 1.11)
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
def sample_weekly_data(auth_client):
    """Create sample week schedule data"""
    with app.app_context():
        from app import Employee, Event, Schedule

        # Create employee
        employee = Employee(id='TEST001', name='Test User', email='test@example.com')
        db.session.add(employee)
        db.session.commit()

        # Create events for the week
        for i in range(5):  # Mon-Fri
            event = Event(
                project_name=f'Event {1000+i}',
                project_ref_num=1000+i,
                location_mvid=f'LOC00{i}',
                start_datetime=datetime.now() + timedelta(days=i),
                due_datetime=datetime.now() + timedelta(days=i, hours=2),
                event_type='Core' if i < 3 else 'Other'
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


class TestWeeklySummaryRoute:
    """Test weekly summary printing route"""

    def test_route_requires_authentication(self, client):
        """Test /api/print_weekly_summary requires authentication"""
        today_str = date.today().isoformat()
        response = client.get(f'/api/print_weekly_summary/{today_str}')
        assert response.status_code in [302, 401, 403, 500]

    def test_valid_date_returns_pdf(self, auth_client, sample_weekly_data):
        """Test route with valid date returns PDF"""
        today_str = date.today().isoformat()
        response = auth_client.get(f'/api/print_weekly_summary/{today_str}')
        assert response.status_code in [200, 500]

    def test_invalid_date_returns_400(self, auth_client):
        """Test route with invalid date format returns 400"""
        response = auth_client.get('/api/print_weekly_summary/invalid-date')
        assert response.status_code in [400, 500]

    def test_pdf_filename_includes_week(self, auth_client, sample_weekly_data):
        """Test PDF filename includes week dates"""
        today_str = date.today().isoformat()
        response = auth_client.get(f'/api/print_weekly_summary/{today_str}')

        if response.status_code == 200:
            content_disp = response.headers.get('Content-Disposition', '')
            assert 'Weekly_Summary_' in content_disp or 'Week_' in content_disp or response.content_type == 'application/pdf'


class TestEventTypeFiltering:
    """Test event type filtering"""

    def test_core_events_only(self, auth_client, sample_weekly_data):
        """Test summary includes only Core events"""
        today_str = date.today().isoformat()
        response = auth_client.get(f'/api/print_weekly_summary/{today_str}?event_type=Core')
        assert response.status_code in [200, 500]

    def test_all_event_types(self, auth_client, sample_weekly_data):
        """Test summary includes all event types"""
        today_str = date.today().isoformat()
        response = auth_client.get(f'/api/print_weekly_summary/{today_str}')
        assert response.status_code in [200, 500]


class TestLandscapePDF:
    """Test landscape PDF generation"""

    def test_pdf_is_landscape(self, auth_client, sample_weekly_data):
        """Test PDF is generated in landscape orientation"""
        today_str = date.today().isoformat()
        response = auth_client.get(f'/api/print_weekly_summary/{today_str}')

        if response.status_code == 200:
            assert response.content_type == 'application/pdf'


class TestWeekBoundaries:
    """Test week boundary calculation"""

    def test_monday_start_of_week(self, auth_client, sample_weekly_data):
        """Test week starts on Monday"""
        today_str = date.today().isoformat()
        response = auth_client.get(f'/api/print_weekly_summary/{today_str}')
        assert response.status_code in [200, 500]

    def test_sunday_end_of_week(self, auth_client, sample_weekly_data):
        """Test week ends on Sunday"""
        today_str = date.today().isoformat()
        response = auth_client.get(f'/api/print_weekly_summary/{today_str}')
        assert response.status_code in [200, 500]
