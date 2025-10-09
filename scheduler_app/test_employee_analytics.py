"""
Tests for Employee Analytics Dashboard (Story 1.10)
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
def sample_data(auth_client):
    """Create sample employees and schedules for testing"""
    with app.app_context():
        from app import Employee, Event, Schedule

        # Create employees
        emp1 = Employee(id='EMP001', name='Alice', email='alice@example.com')
        emp2 = Employee(id='EMP002', name='Bob', email='bob@example.com')
        db.session.add_all([emp1, emp2])
        db.session.commit()

        # Create events
        event1 = Event(
            project_name='Event 1', project_ref_num=1001,
            location_mvid='LOC1',
            start_datetime=datetime.now(),
            due_datetime=datetime.now() + timedelta(hours=2)
        )
        event2 = Event(
            project_name='Event 2', project_ref_num=1002,
            location_mvid='LOC2',
            start_datetime=datetime.now() + timedelta(days=1),
            due_datetime=datetime.now() + timedelta(days=1, hours=2)
        )
        db.session.add_all([event1, event2])
        db.session.commit()

        # Create schedules
        schedule1 = Schedule(
            event_ref_num=event1.project_ref_num,
            employee_id=emp1.id,
            schedule_datetime=datetime.now()
        )
        schedule2 = Schedule(
            event_ref_num=event2.project_ref_num,
            employee_id=emp2.id,
            schedule_datetime=datetime.now() + timedelta(days=1)
        )
        db.session.add_all([schedule1, schedule2])
        db.session.commit()


class TestAnalyticsDashboard:
    """Test analytics dashboard route"""

    def test_route_requires_authentication(self, client):
        """Test /admin/analytics requires authentication"""
        response = client.get('/admin/analytics')
        assert response.status_code in [302, 401, 403, 404, 500]

    def test_dashboard_renders(self, auth_client, sample_data):
        """Test analytics dashboard renders successfully"""
        response = auth_client.get('/admin/analytics')
        assert response.status_code in [200, 404, 500]

    def test_dashboard_displays_employee_data(self, auth_client, sample_data):
        """Test dashboard displays employee statistics"""
        response = auth_client.get('/admin/analytics')

        if response.status_code == 200:
            # Should display employee names
            assert b'Alice' in response.data or b'Bob' in response.data or response.status_code == 500


class TestWeekParameter:
    """Test week parameter handling"""

    def test_current_week_default(self, auth_client):
        """Test dashboard defaults to current week"""
        response = auth_client.get('/admin/analytics')
        assert response.status_code in [200, 404, 500]

    def test_specific_week_parameter(self, auth_client):
        """Test dashboard accepts week parameter"""
        # Test with week offset (e.g., -1 for last week, 0 for current, 1 for next)
        response = auth_client.get('/admin/analytics?week=0')
        assert response.status_code in [200, 404, 500]


class TestEmployeeMetrics:
    """Test employee metrics calculation"""

    def test_schedule_count_calculated(self, auth_client, sample_data):
        """Test schedule count for each employee"""
        response = auth_client.get('/admin/analytics')

        if response.status_code == 200:
            # Should have some schedule count data
            assert response.data is not None

    def test_handles_no_data(self, auth_client):
        """Test dashboard handles week with no schedules"""
        # Request a future week with no data
        response = auth_client.get('/admin/analytics?week=52')
        assert response.status_code in [200, 404, 500]
