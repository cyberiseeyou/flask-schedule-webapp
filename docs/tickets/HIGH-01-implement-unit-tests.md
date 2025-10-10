# HIGH-01: Implement Unit Test Coverage for Services

## Priority
🟡 **HIGH** - Within 2 Weeks

## Status
🟡 Open

## Type
🧪 Testing / Quality Assurance

## Assigned To
**Dev Agent (James)** with **QA Agent (Quinn)** for test strategy

## Description
Currently, the codebase lacks comprehensive unit test coverage for critical service modules. This creates risks for regression bugs and makes refactoring difficult.

### Missing Test Coverage
- `services/scheduling_engine.py` - Core auto-scheduler logic
- `services/rotation_manager.py` - Employee rotation logic
- `services/constraint_validator.py` - Scheduling validation
- `services/conflict_resolver.py` - Conflict resolution
- `services/edr_service.py` - EDR integration
- `services/daily_paperwork_generator.py` - PDF generation

## Impact
- **Regression risk**: Changes can break existing functionality
- **Refactoring difficulty**: No safety net for code changes
- **Bug detection**: Issues found late in production
- **Code confidence**: Developers hesitant to modify complex logic

## Acceptance Criteria
- [ ] Unit tests for all service modules
- [ ] Test coverage > 80% for services
- [ ] Tests follow AAA pattern (Arrange, Act, Assert)
- [ ] Fixtures for common test data
- [ ] Mocking external dependencies
- [ ] CI/CD integration
- [ ] Test documentation

## Test Strategy

### Testing Framework Stack
```python
# requirements-dev.txt
pytest==7.4.3
pytest-cov==4.1.0
pytest-mock==3.12.0
pytest-flask==1.3.0
faker==20.1.0
factory-boy==3.3.0
freezegun==1.4.0
```

### Project Structure
```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures
├── unit/
│   ├── services/
│   │   ├── test_scheduling_engine.py
│   │   ├── test_rotation_manager.py
│   │   ├── test_constraint_validator.py
│   │   ├── test_conflict_resolver.py
│   │   ├── test_edr_service.py
│   │   └── test_daily_paperwork_generator.py
│   └── models/
│       ├── test_employee.py
│       ├── test_event.py
│       └── test_schedule.py
├── integration/
│   ├── test_api_routes.py
│   ├── test_scheduling_routes.py
│   └── test_admin_routes.py
└── fixtures/
    ├── employees.py
    ├── events.py
    └── schedules.py
```

## Implementation Plan

### Phase 1: Setup Testing Infrastructure (4 hours)

#### 1.1 Install Dependencies
```bash
pip install pytest pytest-cov pytest-mock pytest-flask faker factory-boy freezegun
pip freeze > requirements-dev.txt
```

#### 1.2 Create conftest.py
```python
# tests/conftest.py
"""
Shared pytest fixtures for all tests
"""
import pytest
from datetime import datetime, timedelta
from app import create_app
from models import db as _db
from models import Employee, Event, Schedule

@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    app = create_app('testing')
    return app

@pytest.fixture(scope='session')
def db(app):
    """Create database for testing"""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.drop_all()

@pytest.fixture(scope='function')
def session(db):
    """Create a new database session for each test"""
    connection = db.engine.connect()
    transaction = connection.begin()

    options = dict(bind=connection, binds={})
    session = db.create_scoped_session(options=options)

    db.session = session

    yield session

    transaction.rollback()
    connection.close()
    session.remove()

@pytest.fixture
def sample_employee(session):
    """Create a sample employee for testing"""
    employee = Employee(
        id='EMP001',
        name='John Doe',
        email='john@example.com',
        job_title='Event Specialist',
        is_active=True
    )
    session.add(employee)
    session.commit()
    return employee

@pytest.fixture
def sample_event(session):
    """Create a sample event for testing"""
    event = Event(
        project_name='Test Event 123456',
        project_ref_num=123456,
        event_type='Core',
        start_datetime=datetime.now(),
        due_datetime=datetime.now() + timedelta(days=7),
        is_scheduled=False
    )
    session.add(event)
    session.commit()
    return event
```

#### 1.3 Create Factory Classes
```python
# tests/fixtures/employees.py
"""
Employee test factories using factory_boy
"""
import factory
from models import Employee
from faker import Faker

fake = Faker()

class EmployeeFactory(factory.Factory):
    class Meta:
        model = Employee

    id = factory.Sequence(lambda n: f'EMP{n:03d}')
    name = factory.LazyFunction(fake.name)
    email = factory.LazyAttribute(lambda obj: f'{obj.name.lower().replace(" ", ".")}@example.com')
    job_title = 'Event Specialist'
    is_active = True
    is_supervisor = False
    adult_beverage_trained = False

class LeadEmployeeFactory(EmployeeFactory):
    job_title = 'Lead Event Specialist'

class SupervisorFactory(EmployeeFactory):
    job_title = 'Club Supervisor'
    is_supervisor = True
```

### Phase 2: Service Unit Tests (12 hours)

#### 2.1 Scheduling Engine Tests
```python
# tests/unit/services/test_scheduling_engine.py
"""
Unit tests for SchedulingEngine service
"""
import pytest
from datetime import datetime, timedelta, time
from services.scheduling_engine import SchedulingEngine
from tests.fixtures.employees import EmployeeFactory, LeadEmployeeFactory
from tests.fixtures.events import EventFactory

class TestSchedulingEngine:
    """Test suite for SchedulingEngine"""

    @pytest.fixture
    def engine(self, session):
        """Create SchedulingEngine instance"""
        models = {
            'Event': Event,
            'Schedule': Schedule,
            'Employee': Employee,
            'SchedulerRunHistory': SchedulerRunHistory,
            'PendingSchedule': PendingSchedule,
            'EmployeeTimeOff': EmployeeTimeOff,
            'EmployeeWeeklyAvailability': EmployeeWeeklyAvailability
        }
        return SchedulingEngine(session, models)

    def test_get_unscheduled_events(self, engine, session):
        """Test retrieving unscheduled events"""
        # Arrange
        scheduled_event = EventFactory(is_scheduled=True)
        unscheduled_event = EventFactory(is_scheduled=False)
        session.add_all([scheduled_event, unscheduled_event])
        session.commit()

        # Act
        result = engine._get_unscheduled_events()

        # Assert
        assert len(result) == 1
        assert result[0].id == unscheduled_event.id

    def test_sort_events_by_priority(self, engine):
        """Test event sorting by due date and type"""
        # Arrange
        today = datetime.now()
        events = [
            EventFactory(
                due_datetime=today + timedelta(days=10),
                event_type='Core'
            ),
            EventFactory(
                due_datetime=today + timedelta(days=5),
                event_type='Juicer'
            ),
            EventFactory(
                due_datetime=today + timedelta(days=5),
                event_type='Core'
            ),
        ]

        # Act
        sorted_events = engine._sort_events_by_priority(events)

        # Assert
        assert sorted_events[0].event_type == 'Juicer'  # Earlier date, higher priority type
        assert sorted_events[1].event_type == 'Core'    # Earlier date
        assert sorted_events[2].due_datetime == today + timedelta(days=10)

    def test_get_earliest_schedule_date(self, engine):
        """Test earliest schedule date calculation"""
        # Arrange
        today = datetime.now().date()
        event = EventFactory(
            start_datetime=datetime.combine(today, time(0, 0))
        )

        # Act
        earliest = engine._get_earliest_schedule_date(event)

        # Assert
        expected = today + timedelta(days=3)  # SCHEDULING_WINDOW_DAYS = 3
        assert earliest.date() >= expected

    def test_schedule_core_event_success(self, engine, session):
        """Test successful Core event scheduling"""
        # Arrange
        lead = LeadEmployeeFactory()
        event = EventFactory(event_type='Core', is_scheduled=False)
        session.add_all([lead, event])
        session.commit()

        run = SchedulerRunHistory(run_type='manual', status='running')
        session.add(run)
        session.commit()

        # Act
        engine._schedule_core_event(run, event)

        # Assert
        assert run.events_scheduled == 1
        pending = session.query(PendingSchedule).filter_by(
            event_ref_num=event.project_ref_num
        ).first()
        assert pending is not None

    @pytest.mark.parametrize('event_type,expected_time', [
        ('Juicer Production', time(9, 0)),
        ('Juicer Survey', time(17, 0)),
        ('Juicer Other', time(9, 0)),
    ])
    def test_get_juicer_time(self, engine, event_type, expected_time):
        """Test Juicer event time determination"""
        # Arrange
        event = EventFactory(
            project_name=f'{event_type} Event',
            event_type='Juicer'
        )

        # Act
        result = engine._get_juicer_time(event)

        # Assert
        assert result == expected_time
```

#### 2.2 Rotation Manager Tests
```python
# tests/unit/services/test_rotation_manager.py
"""
Unit tests for RotationManager service
"""
import pytest
from datetime import datetime, timedelta
from services.rotation_manager import RotationManager
from models import RotationAssignment

class TestRotationManager:
    """Test suite for RotationManager"""

    @pytest.fixture
    def manager(self, session):
        """Create RotationManager instance"""
        models = {
            'Employee': Employee,
            'RotationAssignment': RotationAssignment
        }
        return RotationManager(session, models)

    def test_get_rotation_employee_primary_lead(self, manager, session):
        """Test retrieving primary lead for a date"""
        # Arrange
        lead = LeadEmployeeFactory()
        session.add(lead)
        session.commit()

        target_date = datetime.now() + timedelta(days=5)
        assignment = RotationAssignment(
            rotation_type='primary_lead',
            employee_id=lead.id,
            rotation_date=target_date.date()
        )
        session.add(assignment)
        session.commit()

        # Act
        result = manager.get_rotation_employee(target_date, 'primary_lead')

        # Assert
        assert result.id == lead.id

    def test_get_rotation_employee_no_assignment(self, manager):
        """Test handling when no rotation assignment exists"""
        # Arrange
        target_date = datetime.now() + timedelta(days=10)

        # Act
        result = manager.get_rotation_employee(target_date, 'primary_lead')

        # Assert
        assert result is None
```

#### 2.3 Constraint Validator Tests
```python
# tests/unit/services/test_constraint_validator.py
"""
Unit tests for ConstraintValidator service
"""
import pytest
from datetime import datetime, timedelta
from services.constraint_validator import ConstraintValidator
from services.validation_types import ValidationResult

class TestConstraintValidator:
    """Test suite for ConstraintValidator"""

    @pytest.fixture
    def validator(self, session):
        """Create ConstraintValidator instance"""
        models = {
            'Employee': Employee,
            'Schedule': Schedule,
            'EmployeeTimeOff': EmployeeTimeOff,
            'EmployeeWeeklyAvailability': EmployeeWeeklyAvailability,
            'PendingSchedule': PendingSchedule
        }
        return ConstraintValidator(session, models)

    def test_validate_assignment_success(self, validator, session):
        """Test valid employee assignment"""
        # Arrange
        employee = EmployeeFactory()
        event = EventFactory(event_type='Core')
        schedule_datetime = datetime.now() + timedelta(days=5)
        session.add_all([employee, event])
        session.commit()

        # Act
        result = validator.validate_assignment(event, employee, schedule_datetime)

        # Assert
        assert result.is_valid is True
        assert len(result.violations) == 0

    def test_validate_assignment_time_off(self, validator, session):
        """Test rejection when employee has time off"""
        # Arrange
        employee = EmployeeFactory()
        event = EventFactory()
        schedule_date = datetime.now() + timedelta(days=5)

        time_off = EmployeeTimeOff(
            employee_id=employee.id,
            start_date=schedule_date.date(),
            end_date=schedule_date.date()
        )
        session.add_all([employee, event, time_off])
        session.commit()

        # Act
        result = validator.validate_assignment(event, employee, schedule_date)

        # Assert
        assert result.is_valid is False
        assert 'time_off' in str(result.violations[0]).lower()

    def test_validate_assignment_core_event_one_per_day(self, validator, session):
        """Test Core event one-per-day constraint"""
        # Arrange
        employee = EmployeeFactory()
        event1 = EventFactory(event_type='Core')
        event2 = EventFactory(event_type='Core')
        schedule_datetime = datetime.now() + timedelta(days=5)

        # Employee already scheduled for Core event that day
        existing_schedule = Schedule(
            event_ref_num=event1.project_ref_num,
            employee_id=employee.id,
            schedule_datetime=schedule_datetime
        )

        session.add_all([employee, event1, event2, existing_schedule])
        session.commit()

        # Act
        result = validator.validate_assignment(event2, employee, schedule_datetime)

        # Assert
        assert result.is_valid is False
        assert 'core' in str(result.violations[0]).lower()
```

### Phase 3: Test Coverage & Reporting (2 hours)

#### 3.1 Configure pytest.ini
```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --cov=scheduler_app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

#### 3.2 Run Tests
```bash
# Run all tests with coverage
pytest --cov=scheduler_app --cov-report=html

# Run only unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/services/test_scheduling_engine.py -v

# Run with coverage report
pytest --cov=scheduler_app/services --cov-report=term-missing
```

### Phase 4: CI/CD Integration (2 hours)

#### 4.1 GitHub Actions Workflow
```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run tests with coverage
      run: |
        pytest --cov=scheduler_app --cov-report=xml --cov-report=term

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
```

## Testing Best Practices

### AAA Pattern (Arrange, Act, Assert)
```python
def test_example():
    # Arrange - Set up test data
    employee = EmployeeFactory()

    # Act - Execute the code being tested
    result = some_function(employee)

    # Assert - Verify the result
    assert result is not None
```

### Use Fixtures for Reusability
```python
@pytest.fixture
def common_test_setup(session):
    """Setup used by multiple tests"""
    # Setup code
    yield data
    # Teardown code
```

### Mock External Dependencies
```python
def test_with_mock(mocker):
    """Test with mocked external service"""
    mock_api = mocker.patch('services.external_api.call')
    mock_api.return_value = {'status': 'success'}

    result = my_function()

    assert mock_api.called
    assert result['status'] == 'success'
```

### Parametrize Tests
```python
@pytest.mark.parametrize('input,expected', [
    ('Core', True),
    ('Juicer', True),
    ('Invalid', False),
])
def test_event_type(input, expected):
    result = validate_event_type(input)
    assert result == expected
```

## Dependencies
- None (standalone task)

## Estimated Effort
⏱️ **24-30 hours** (3-4 days)
- Test infrastructure setup: 4 hours
- Scheduling engine tests: 6 hours
- Rotation manager tests: 3 hours
- Constraint validator tests: 3 hours
- Conflict resolver tests: 3 hours
- EDR service tests: 3 hours
- CI/CD integration: 2 hours
- Documentation: 2 hours

## Success Metrics
- [ ] Test coverage > 80% for all services
- [ ] All tests passing in CI/CD
- [ ] Test execution time < 2 minutes
- [ ] Zero flaky tests
- [ ] Code coverage badge in README

## Future Enhancements
- Integration tests for API endpoints
- End-to-end tests for critical workflows
- Performance benchmarking tests
- Load testing for scheduling engine
- Mutation testing with mutpy

---
**Created**: 2025-01-09
**Last Updated**: 2025-01-09
**Reporter**: Quinn (QA Agent)
