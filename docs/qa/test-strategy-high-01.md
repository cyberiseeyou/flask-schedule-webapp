# Test Strategy: HIGH-01 - Unit Test Coverage Implementation

**Ticket**: HIGH-01
**Created By**: Quinn (QA Agent)
**Date**: 2025-01-09
**Status**: Ready for Development

---

## Executive Summary

This document provides a comprehensive test strategy for implementing unit test coverage across critical service modules. The strategy is risk-based, prioritizing high-value tests that provide maximum protection against regression bugs while maintaining developer velocity.

**Target Coverage**: 80% for service layer
**Estimated Effort**: 24-30 hours
**Priority**: HIGH (within 2 weeks)

---

## Testing Philosophy

### Core Principles

1. **Risk-Based Testing**: Focus on critical paths and complex logic first
2. **AAA Pattern**: All tests follow Arrange-Act-Assert structure
3. **Test Independence**: Each test runs in isolation with clean state
4. **Fast Feedback**: Unit tests execute in <2 minutes total
5. **Maintainable Tests**: Tests are as readable as production code

### Test Pyramid Strategy

```
    /\
   /E2E\      ← 5% (Critical user journeys only)
  /------\
 /Integr-\    ← 15% (API endpoints, database interactions)
/----------\
/   UNIT   \  ← 80% (Service layer, business logic)
------------
```

**Focus Area**: Unit tests for service layer business logic

---

## Service Module Priority Matrix

### Critical Priority (Test First)

| Service | Complexity | Risk | Business Impact | Test Priority |
|---------|-----------|------|-----------------|---------------|
| `scheduling_engine.py` | HIGH | HIGH | CRITICAL | 🔴 P0 |
| `constraint_validator.py` | HIGH | HIGH | CRITICAL | 🔴 P0 |
| `conflict_resolver.py` | MEDIUM | HIGH | HIGH | 🟡 P1 |
| `rotation_manager.py` | MEDIUM | MEDIUM | HIGH | 🟡 P1 |

### High Priority (Test Second)

| Service | Complexity | Risk | Business Impact | Test Priority |
|---------|-----------|------|-----------------|---------------|
| `edr_service.py` | MEDIUM | MEDIUM | MEDIUM | 🟢 P2 |
| `daily_paperwork_generator.py` | LOW | LOW | MEDIUM | 🟢 P2 |

---

## Detailed Test Strategy by Service

### 1. Scheduling Engine (`scheduling_engine.py`)

**Complexity**: HIGH
**Risk Level**: CRITICAL
**Estimated Tests**: 25-30
**Effort**: 6 hours

#### Test Categories

##### 1.1 Event Retrieval & Filtering
```python
# Test scenarios
- test_get_unscheduled_events_excludes_scheduled()
- test_get_unscheduled_events_filters_by_date_range()
- test_get_unscheduled_events_empty_result()
```

**Priority**: P0
**Risk**: Data integrity - scheduling wrong events

##### 1.2 Event Prioritization Logic
```python
# Test scenarios
- test_sort_events_by_due_date_ascending()
- test_sort_events_priority_core_over_juicer()
- test_sort_events_multiple_criteria_combination()
- test_sort_events_handles_null_dates()
```

**Priority**: P0
**Risk**: Business logic - wrong event scheduling order

##### 1.3 Scheduling Window Calculation
```python
# Test scenarios
- test_earliest_schedule_date_respects_minimum_window()
- test_earliest_schedule_date_for_past_events()
- test_earliest_schedule_date_timezone_handling()
```

**Priority**: P0
**Risk**: Scheduling too early/late violates business rules

##### 1.4 Core Event Scheduling
```python
# Test scenarios
- test_schedule_core_event_assigns_lead_employee()
- test_schedule_core_event_respects_rotation()
- test_schedule_core_event_checks_availability()
- test_schedule_core_event_creates_pending_schedule()
- test_schedule_core_event_no_available_employees()
- test_schedule_core_event_employee_on_time_off()
```

**Priority**: P0
**Risk**: Core business logic - incorrect assignments

##### 1.5 Juicer Event Scheduling
```python
# Test scenarios
- test_get_juicer_time_production_morning()
- test_get_juicer_time_survey_afternoon()
- test_get_juicer_time_other_morning()
- test_schedule_juicer_event_correct_time()
- test_schedule_juicer_event_correct_employee_type()
```

**Priority**: P1
**Risk**: Business logic - wrong time assignments

##### 1.6 Employee Availability Logic
```python
# Test scenarios
- test_check_employee_available_on_date()
- test_check_employee_unavailable_time_off()
- test_check_employee_unavailable_already_scheduled()
- test_check_employee_available_different_event_type()
```

**Priority**: P0
**Risk**: Scheduling conflicts, employee overload

#### Boundary Conditions to Test

- Empty event list
- Single event
- 100+ events (performance)
- Events with same priority
- Null/missing fields
- Past due dates
- Future dates beyond scheduling window

#### Mocking Strategy

```python
# Mock database queries
@pytest.fixture
def mock_db_session(mocker):
    return mocker.MagicMock()

# Mock models
@pytest.fixture
def mock_event():
    return Event(
        project_ref_num=123456,
        event_type='Core',
        due_datetime=datetime.now() + timedelta(days=7),
        is_scheduled=False
    )

# Mock rotation assignments
@pytest.fixture
def mock_rotation_manager(mocker):
    manager = mocker.MagicMock()
    manager.get_rotation_employee.return_value = mock_employee
    return manager
```

---

### 2. Constraint Validator (`constraint_validator.py`)

**Complexity**: HIGH
**Risk Level**: CRITICAL
**Estimated Tests**: 20-25
**Effort**: 5 hours

#### Test Categories

##### 2.1 Time-Off Validation
```python
# Test scenarios
- test_validate_employee_available_no_time_off()
- test_validate_employee_unavailable_on_time_off()
- test_validate_employee_time_off_boundary_start_date()
- test_validate_employee_time_off_boundary_end_date()
- test_validate_employee_time_off_overlapping_ranges()
```

**Priority**: P0
**Risk**: Scheduling employees when unavailable

##### 2.2 Scheduling Constraints (One Core Per Day)
```python
# Test scenarios
- test_validate_core_event_one_per_day_no_existing()
- test_validate_core_event_one_per_day_violation()
- test_validate_core_event_allows_multiple_juicer_same_day()
- test_validate_core_event_different_days_allowed()
```

**Priority**: P0
**Risk**: Business rule violation

##### 2.3 Weekly Availability Validation
```python
# Test scenarios
- test_validate_employee_available_on_weekday()
- test_validate_employee_unavailable_on_weekday()
- test_validate_employee_no_availability_set_defaults_available()
```

**Priority**: P1
**Risk**: Scheduling outside availability windows

##### 2.4 Conflict Detection
```python
# Test scenarios
- test_detect_schedule_conflict_same_time()
- test_detect_schedule_conflict_overlapping_time()
- test_detect_no_conflict_different_time()
- test_detect_no_conflict_different_day()
```

**Priority**: P0
**Risk**: Double-booking employees

##### 2.5 Employee Qualifications
```python
# Test scenarios
- test_validate_lead_required_for_core_event()
- test_validate_non_lead_rejected_for_core_event()
- test_validate_adult_beverage_training_requirement()
```

**Priority**: P0
**Risk**: Assigning unqualified employees

#### Given-When-Then Scenarios

```gherkin
Scenario: Employee with time-off should be rejected
  Given an employee has time-off from 2025-01-15 to 2025-01-17
  When validating assignment for 2025-01-16
  Then validation should fail
  And violation should include "employee has time-off"

Scenario: Employee can work multiple Juicer events same day
  Given an employee is scheduled for Juicer event at 9:00 AM
  When validating Juicer assignment for 5:00 PM same day
  Then validation should pass
  And no conflicts detected

Scenario: Employee cannot work multiple Core events same day
  Given an employee is scheduled for Core event at 9:00 AM
  When validating Core assignment for 2:00 PM same day
  Then validation should fail
  And violation should include "one Core event per day"
```

---

### 3. Conflict Resolver (`conflict_resolver.py`)

**Complexity**: MEDIUM
**Risk Level**: HIGH
**Estimated Tests**: 15-20
**Effort**: 3 hours

#### Test Categories

##### 3.1 Conflict Detection
```python
# Test scenarios
- test_find_conflicts_no_conflicts()
- test_find_conflicts_time_overlap()
- test_find_conflicts_same_employee_same_time()
- test_find_conflicts_multiple_conflicts()
```

##### 3.2 Conflict Resolution Strategies
```python
# Test scenarios
- test_resolve_by_priority_core_over_juicer()
- test_resolve_by_date_earlier_takes_precedence()
- test_resolve_by_employee_availability()
- test_resolve_cannot_resolve_logs_warning()
```

##### 3.3 Schedule Adjustment
```python
# Test scenarios
- test_adjust_schedule_to_next_available_slot()
- test_adjust_schedule_respects_constraints()
- test_adjust_schedule_no_available_slot_returns_none()
```

---

### 4. Rotation Manager (`rotation_manager.py`)

**Complexity**: MEDIUM
**Risk Level**: MEDIUM
**Estimated Tests**: 12-15
**Effort**: 3 hours

#### Test Categories

##### 4.1 Rotation Assignment Retrieval
```python
# Test scenarios
- test_get_rotation_employee_primary_lead()
- test_get_rotation_employee_backup_lead()
- test_get_rotation_employee_no_assignment_returns_none()
- test_get_rotation_employee_date_boundary_start()
- test_get_rotation_employee_date_boundary_end()
```

##### 4.2 Rotation Exception Handling
```python
# Test scenarios
- test_get_rotation_with_exception_returns_override()
- test_get_rotation_exception_date_specific()
- test_get_rotation_no_exception_returns_regular()
```

##### 4.3 Rotation Schedule Generation
```python
# Test scenarios
- test_generate_rotation_schedule_weekly()
- test_generate_rotation_schedule_respects_availability()
- test_generate_rotation_schedule_skips_time_off()
```

---

### 5. EDR Service (`edr_service.py`)

**Complexity**: MEDIUM
**Risk Level**: MEDIUM
**Estimated Tests**: 10-12
**Effort**: 3 hours

#### Test Categories

##### 5.1 Authentication (Mocked)
```python
# Test scenarios
- test_authenticate_success_with_valid_credentials()
- test_authenticate_failure_invalid_credentials()
- test_authenticate_mfa_challenge_handling()
- test_authenticate_session_token_stored()
```

**Note**: Mock external API calls - don't hit real Walmart EDR

##### 5.2 Report Fetching
```python
# Test scenarios
- test_fetch_report_success()
- test_fetch_report_not_found_404()
- test_fetch_report_authentication_expired()
- test_fetch_report_retry_on_timeout()
```

##### 5.3 Data Parsing
```python
# Test scenarios
- test_parse_edr_html_extracts_report_data()
- test_parse_edr_html_handles_malformed_html()
- test_parse_edr_html_empty_report()
```

---

### 6. Daily Paperwork Generator (`daily_paperwork_generator.py`)

**Complexity**: LOW
**Risk Level**: LOW
**Estimated Tests**: 8-10
**Effort**: 2 hours

#### Test Categories

##### 6.1 PDF Generation
```python
# Test scenarios
- test_generate_paperwork_creates_pdf()
- test_generate_paperwork_includes_all_events()
- test_generate_paperwork_formats_dates_correctly()
- test_generate_paperwork_handles_no_events()
```

##### 6.2 Report Merging
```python
# Test scenarios
- test_merge_pdfs_combines_multiple_files()
- test_merge_pdfs_preserves_order()
- test_merge_pdfs_handles_single_file()
- test_merge_pdfs_empty_list_returns_none()
```

---

## Test Infrastructure Setup

### Phase 1: Foundation (4 hours)

#### 1.1 Install Dependencies
```bash
pip install pytest pytest-cov pytest-mock pytest-flask faker factory-boy freezegun
```

#### 1.2 Configure pytest.ini
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --cov=scheduler_app/services
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
    --strict-markers
markers =
    slow: marks tests as slow (>1 second)
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    smoke: marks tests as smoke tests for quick validation
```

#### 1.3 Create conftest.py
```python
# tests/conftest.py
"""Shared pytest fixtures for all tests"""

import pytest
from datetime import datetime, timedelta
from app import create_app
from models import db as _db

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
```

#### 1.4 Create Test Factories
```python
# tests/fixtures/factories.py
"""Factory classes for test data generation"""

import factory
from datetime import datetime, timedelta
from faker import Faker
from models import Employee, Event, Schedule

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

class LeadEmployeeFactory(EmployeeFactory):
    job_title = 'Lead Event Specialist'

class EventFactory(factory.Factory):
    class Meta:
        model = Event

    project_ref_num = factory.Sequence(lambda n: 100000 + n)
    project_name = factory.LazyAttribute(lambda obj: f'Event {obj.project_ref_num}')
    event_type = 'Core'
    start_datetime = factory.LazyFunction(lambda: datetime.now() + timedelta(days=7))
    due_datetime = factory.LazyAttribute(lambda obj: obj.start_datetime + timedelta(days=7))
    is_scheduled = False
```

---

## Test Execution Strategy

### Development Workflow

```bash
# 1. Run all tests
pytest

# 2. Run specific service tests
pytest tests/unit/services/test_scheduling_engine.py

# 3. Run tests with coverage report
pytest --cov=scheduler_app/services --cov-report=html

# 4. Run only unit tests (fast)
pytest -m unit

# 5. Run tests in parallel (requires pytest-xdist)
pytest -n auto
```

### CI/CD Integration

```yaml
# .github/workflows/tests.yml
name: Unit Tests

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
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run unit tests
      run: |
        pytest tests/unit/ --cov=scheduler_app/services --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
```

---

## Coverage Goals & Metrics

### Target Coverage by Module

| Module | Target Coverage | Rationale |
|--------|----------------|-----------|
| `scheduling_engine.py` | 90% | Critical business logic |
| `constraint_validator.py` | 90% | Critical validation logic |
| `conflict_resolver.py` | 85% | Important but less complex |
| `rotation_manager.py` | 80% | Standard coverage |
| `edr_service.py` | 75% | External dependency, mocked |
| `daily_paperwork_generator.py` | 70% | PDF generation, hard to test |

### Overall Target: 80% service layer coverage

### Coverage Exceptions (Acceptable to Skip)

- Logging statements
- Trivial getters/setters
- `__repr__` methods
- External API error handling (when mocked)
- PDF rendering internals (ReportLab specifics)

---

## Test Quality Checklist

### For Each Test

- [ ] Follows AAA pattern (Arrange, Act, Assert)
- [ ] Has descriptive name (test_verb_expected_result)
- [ ] Tests one thing only
- [ ] Independent (doesn't rely on other tests)
- [ ] Fast (<100ms for unit tests)
- [ ] Uses fixtures for setup
- [ ] Has clear assertion messages
- [ ] Cleans up resources

### For Each Test Suite

- [ ] Tests happy path
- [ ] Tests error conditions
- [ ] Tests boundary conditions
- [ ] Tests edge cases
- [ ] Uses parametrize for similar scenarios
- [ ] Mocks external dependencies
- [ ] Has clear organization (nested classes)

---

## Risk-Based Testing Priority

### P0: Must Test Before Deployment (Critical Path)

1. Scheduling engine event prioritization
2. Constraint validator time-off check
3. Constraint validator one-core-per-day rule
4. Employee availability validation
5. Conflict detection

**Rationale**: These are core business rules. Failures cause scheduling errors.

### P1: Should Test Soon (High Value)

1. Rotation manager assignment retrieval
2. Conflict resolution strategies
3. Juicer event time determination
4. Employee qualification validation

**Rationale**: Important but have manual verification paths.

### P2: Nice to Have (Lower Risk)

1. EDR service (mostly integration)
2. PDF generation (visual QA possible)
3. Edge case handling

**Rationale**: Lower complexity or alternative verification methods.

---

## Success Metrics

### Quantitative Metrics

- [ ] 80% overall service coverage achieved
- [ ] All tests pass in CI/CD
- [ ] Test execution time < 2 minutes
- [ ] Zero flaky tests over 10 runs
- [ ] Code coverage badge in README

### Qualitative Metrics

- [ ] Developers feel confident refactoring with tests
- [ ] Tests catch real bugs during development
- [ ] Tests are easy to understand and maintain
- [ ] New developers can write tests following examples

---

## Timeline & Milestones

### Week 1: Foundation + Critical Services

**Days 1-2** (8 hours):
- Set up test infrastructure
- Create conftest.py and factories
- Implement scheduling_engine tests (P0)

**Days 3-4** (8 hours):
- Implement constraint_validator tests (P0)
- Implement conflict_resolver tests (P1)

### Week 2: Remaining Services + CI/CD

**Days 5-6** (8 hours):
- Implement rotation_manager tests (P1)
- Implement edr_service tests (P2)

**Day 7** (4 hours):
- Implement daily_paperwork_generator tests (P2)
- CI/CD integration
- Documentation

**Total**: 28 hours (within 24-30 hour estimate)

---

## Maintenance Strategy

### Test Ownership

- **Service owner** maintains tests for their service
- **QA Agent (Quinn)** reviews test coverage in PRs
- **Dev Agent (James)** ensures tests run in CI/CD

### Test Updates

- Update tests when business rules change
- Add tests when bugs are found (regression tests)
- Refactor tests when they become hard to maintain
- Remove obsolete tests

### Coverage Monitoring

- Weekly coverage reports
- Alert if coverage drops below 75%
- Review uncovered code quarterly

---

## References

- [Pytest Documentation](https://docs.pytest.org/)
- [Effective Python Testing](https://effectivepython.com/)
- [Test-Driven Development by Example](https://www.oreilly.com/library/view/test-driven-development/0321146530/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)

---

**Document Status**: Ready for Implementation
**Next Action**: Dev Agent (James) to implement Phase 1 (test infrastructure)
**Estimated Start**: After CRITICAL-04 completion
**Target Completion**: Within 2 weeks of start

---

**Created By**: Quinn (QA Agent)
**Review Date**: 2025-01-09
**Next Review**: After implementation complete
