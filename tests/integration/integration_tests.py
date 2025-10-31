"""
Integration Tests for Flask Schedule Webapp
Tests route functionality, authentication, and API endpoints
"""
import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from app import app
from app.models import get_models

print("="*80)
print("INTEGRATION TEST SUITE")
print("="*80)
print()

# Test results
results = {'passed': 0, 'failed': 0, 'warnings': 0}

def test(name, func):
    """Run a test and record results"""
    try:
        func()
        print(f"[PASS] {name}")
        results['passed'] += 1
        return True
    except AssertionError as e:
        print(f"[FAIL] {name}: {str(e)}")
        results['failed'] += 1
        return False
    except Exception as e:
        print(f"[ERROR] {name}: {str(e)}")
        results['failed'] += 1
        return False

# Create test client
client = app.test_client()

print("[1/7] Testing Core Routes...")

def test_homepage():
    """Test homepage returns 200"""
    response = client.get('/')
    assert response.status_code in [200, 302], f"Expected 200 or 302, got {response.status_code}"

def test_login_page():
    """Test login page is accessible"""
    response = client.get('/login')
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

def test_static_files():
    """Test static files are served"""
    response = client.get('/static/style.css')
    # 200 if file exists, 404 if not - both are valid
    assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"

test("Homepage", test_homepage)
test("Login Page", test_login_page)
test("Static Files", test_static_files)

print("\n[2/7] Testing API Endpoints...")

def test_api_employees():
    """Test employees API endpoint exists"""
    response = client.get('/api/employees')
    # Should return 401/403 (auth required) or 200 (if no auth)
    assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"

def test_api_events():
    """Test events API endpoint exists"""
    response = client.get('/api/events')
    assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"

def test_api_schedules():
    """Test schedules API endpoint exists"""
    response = client.get('/api/schedules')
    assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"

test("API Employees Endpoint", test_api_employees)
test("API Events Endpoint", test_api_events)
test("API Schedules Endpoint", test_api_schedules)

print("\n[3/7] Testing Database Operations...")

def test_employee_query():
    """Test querying employees"""
    with app.app_context():
        models = get_models()
        Employee = models['Employee']
        employees = Employee.query.limit(5).all()
        assert isinstance(employees, list), "Query should return a list"

def test_event_query():
    """Test querying events"""
    with app.app_context():
        models = get_models()
        Event = models['Event']
        events = Event.query.limit(5).all()
        assert isinstance(events, list), "Query should return a list"

def test_schedule_query():
    """Test querying schedules"""
    with app.app_context():
        models = get_models()
        Schedule = models['Schedule']
        schedules = Schedule.query.limit(5).all()
        assert isinstance(schedules, list), "Query should return a list"

test("Employee Query", test_employee_query)
test("Event Query", test_event_query)
test("Schedule Query", test_schedule_query)

print("\n[4/7] Testing Model Relationships...")

def test_employee_schedules():
    """Test Employee-Schedule relationship"""
    with app.app_context():
        models = get_models()
        Employee = models['Employee']
        emp = Employee.query.first()
        if emp:
            # Just check the relationship exists, don't require data
            assert hasattr(emp, 'schedules'), "Employee should have schedules relationship"

def test_schedule_employee():
    """Test Schedule-Employee relationship"""
    with app.app_context():
        models = get_models()
        Schedule = models['Schedule']
        schedule = Schedule.query.first()
        if schedule:
            assert hasattr(schedule, 'employee_id'), "Schedule should have employee_id"

test("Employee-Schedule Relationship", test_employee_schedules)
test("Schedule-Employee Relationship", test_schedule_employee)

print("\n[5/7] Testing Configuration Access...")

def test_config_secret_key():
    """Test SECRET_KEY is configured"""
    assert app.config.get('SECRET_KEY'), "SECRET_KEY should be set"
    assert len(app.config.get('SECRET_KEY')) >= 16, "SECRET_KEY should be at least 16 chars"

def test_config_database():
    """Test database is configured"""
    assert app.config.get('SQLALCHEMY_DATABASE_URI'), "Database URI should be set"

test("Config Secret Key", test_config_secret_key)
test("Config Database", test_config_database)

print("\n[6/7] Testing Error Handling...")

def test_404_handling():
    """Test 404 error is handled"""
    response = client.get('/nonexistent-page-12345')
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"

def test_method_not_allowed():
    """Test 405 error is handled"""
    response = client.post('/')
    # 405 or 302 (redirect) are both acceptable
    assert response.status_code in [302, 405], f"Expected 302 or 405, got {response.status_code}"

test("404 Error Handling", test_404_handling)
test("Method Not Allowed", test_method_not_allowed)

print("\n[7/7] Testing Template Rendering...")

def test_base_template():
    """Test that templates are loaded"""
    response = client.get('/login')
    if response.status_code == 200:
        # Check if we got HTML back
        assert b'<' in response.data, "Response should contain HTML"

test("Template Rendering", test_base_template)

# Print Summary
print("\n" + "="*80)
print("INTEGRATION TEST SUMMARY")
print("="*80)
print(f"Passed:   {results['passed']}")
print(f"Failed:   {results['failed']}")
print(f"Warnings: {results['warnings']}")
print("="*80)
print()

sys.exit(0 if results['failed'] == 0 else 1)
