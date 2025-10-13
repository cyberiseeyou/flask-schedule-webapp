"""
pytest fixtures for scheduler_app tests
=========================================

This module provides reusable fixtures for testing the scheduler application.
"""

import pytest
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope='session')
def app():
    """
    Create Flask app for testing.

    This fixture creates the app without starting background threads.
    """
    # Temporarily disable background threads
    os.environ['TESTING'] = '1'
    os.environ['DISABLE_BACKGROUND_THREADS'] = '1'

    # Import app components (after setting env vars)
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    from flask_wtf.csrf import CSRFProtect
    import tempfile

    # Create minimal app without background threads
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory DB
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize database
    db = SQLAlchemy(app)

    # Store db in app for fixtures
    app.db = db

    # Initialize models
    from models import init_models
    models = init_models(db)

    # Store models in app config
    for model_name, model_class in models.items():
        app.config[model_name] = model_class

    # Create tables
    with app.app_context():
        db.create_all()

    yield app

    # Cleanup
    with app.app_context():
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """
    Create test client for making requests.
    """
    return app.test_client()


@pytest.fixture(scope='function')
def db(app):
    """
    Provide database session for tests.

    This fixture provides a fresh database session for each test.
    Changes are rolled back after each test.
    """
    db = app.db

    with app.app_context():
        # Create fresh tables
        db.create_all()

        yield db

        # Cleanup - rollback any uncommitted changes
        db.session.rollback()

        # Drop all tables to ensure clean state
        db.drop_all()


@pytest.fixture(scope='function')
def mock_api(app):
    """
    Enable mock Crossmark API for testing.

    This fixture replaces the real API with a mock for testing.
    """
    from scheduler_app.tests.mock_crossmark_api import MockCrossmarkAPI

    mock_api = MockCrossmarkAPI()

    # Store in app config for access in routes
    app.config['MOCK_API'] = mock_api
    app.config['USE_MOCK_API'] = True

    # TODO: Patch session_api_service to use mock
    # This requires modifying routes to check for MOCK_API in config

    yield mock_api

    # Reset mock after test
    mock_api.reset()


@pytest.fixture(scope='function')
def sample_employees(app, db):
    """
    Create sample employees for testing.
    """
    Employee = app.config['Employee']

    with app.app_context():
        employees = [
            Employee(
                id='101',
                name='John Smith',
                email='john.smith@example.com',
                external_id='EXT_101',
                is_active=True
            ),
            Employee(
                id='102',
                name='Jane Doe',
                email='jane.doe@example.com',
                external_id='EXT_102',
                is_active=True
            ),
            Employee(
                id='103',
                name='Bob Johnson',
                email='bob.johnson@example.com',
                external_id='EXT_103',
                is_active=True
            ),
        ]

        for emp in employees:
            db.session.add(emp)

        db.session.commit()

        yield employees


@pytest.fixture(scope='function')
def core_supervisor_pair(app, db, sample_employees):
    """
    Create a CORE event with paired Supervisor (Scenario 1).

    Returns tuple: (core_event, supervisor_event, core_schedule, supervisor_schedule)
    """
    Event = app.config['Event']
    Schedule = app.config['Schedule']

    with app.app_context():
        # Create CORE event
        core_event = Event(
            id=1001,
            project_ref_num=606001,
            project_name='606001-CORE-Super Pretzel',
            event_type='Core',
            condition='Scheduled',
            is_scheduled=True,
            estimated_time=390,  # 6.5 hours in minutes
            start_datetime=datetime(2025, 10, 15, 10, 0, 0),
            due_datetime=datetime(2025, 10, 15),
            external_id='CM_606001',
            sync_status='synced',
            location_mvid='LOC_001'
        )

        # Create Supervisor event
        supervisor_event = Event(
            id=1002,
            project_ref_num=606002,
            project_name='606001-Supervisor-Super Pretzel',
            event_type='Supervisor',
            condition='Scheduled',
            is_scheduled=True,
            estimated_time=5,  # 5 minutes
            start_datetime=datetime(2025, 10, 15, 12, 0, 0),
            due_datetime=datetime(2025, 10, 15),
            external_id='CM_606002',
            sync_status='synced',
            location_mvid='LOC_001'
        )

        db.session.add(core_event)
        db.session.add(supervisor_event)
        db.session.flush()

        # Create schedules
        core_schedule = Schedule(
            id=2001,
            event_ref_num=606001,
            employee_id='101',
            schedule_datetime=datetime(2025, 10, 15, 10, 0, 0),
            external_id='CM_SCH_2001'
        )

        supervisor_schedule = Schedule(
            id=2002,
            event_ref_num=606002,
            employee_id='102',
            schedule_datetime=datetime(2025, 10, 15, 12, 0, 0),
            external_id='CM_SCH_2002'
        )

        db.session.add(core_schedule)
        db.session.add(supervisor_schedule)
        db.session.commit()

        yield (core_event, supervisor_event, core_schedule, supervisor_schedule)


@pytest.fixture(scope='function')
def orphan_core(app, db, sample_employees):
    """
    Create orphan CORE event (no Supervisor) for testing (Scenario 2).

    Returns tuple: (core_event, core_schedule)
    """
    Event = app.config['Event']
    Schedule = app.config['Schedule']

    with app.app_context():
        # Create orphan CORE event
        core_event = Event(
            id=1003,
            project_ref_num=606999,
            project_name='606999-CORE-Orphan Product',
            event_type='Core',
            condition='Scheduled',
            is_scheduled=True,
            estimated_time=300,  # 5 hours
            start_datetime=datetime(2025, 10, 15, 11, 0, 0),
            due_datetime=datetime(2025, 10, 15),
            external_id='CM_606999',
            sync_status='synced',
            location_mvid='LOC_002'
        )

        db.session.add(core_event)
        db.session.flush()

        # Create schedule
        core_schedule = Schedule(
            id=2003,
            event_ref_num=606999,
            employee_id='101',
            schedule_datetime=datetime(2025, 10, 15, 11, 0, 0),
            external_id='CM_SCH_2003'
        )

        db.session.add(core_schedule)
        db.session.commit()

        yield (core_event, core_schedule)


@pytest.fixture(scope='function')
def core_with_unscheduled_supervisor(app, db, sample_employees):
    """
    Create CORE event with unscheduled Supervisor (Scenario 4).

    Returns tuple: (core_event, supervisor_event, core_schedule)
    """
    Event = app.config['Event']
    Schedule = app.config['Schedule']

    with app.app_context():
        # Create CORE event
        core_event = Event(
            id=1006,
            project_ref_num=608001,
            project_name='606003-CORE-Cheetos',
            event_type='Core',
            condition='Scheduled',
            is_scheduled=True,
            estimated_time=420,  # 7 hours
            start_datetime=datetime(2025, 10, 15, 9, 0, 0),
            due_datetime=datetime(2025, 10, 15),
            external_id='CM_608001',
            sync_status='synced',
            location_mvid='LOC_003'
        )

        # Create unscheduled Supervisor event
        supervisor_event = Event(
            id=1007,
            project_ref_num=608002,
            project_name='606003-Supervisor-Cheetos',
            event_type='Supervisor',
            condition='Unstaffed',
            is_scheduled=False,
            estimated_time=5,
            start_datetime=datetime(2025, 10, 15, 0, 0, 0),  # Placeholder datetime
            due_datetime=datetime(2025, 10, 15),
            sync_status='pending',
            location_mvid='LOC_003'
        )

        db.session.add(core_event)
        db.session.add(supervisor_event)
        db.session.flush()

        # Create schedule for CORE only
        core_schedule = Schedule(
            id=2004,
            event_ref_num=608001,
            employee_id='101',
            schedule_datetime=datetime(2025, 10, 15, 9, 0, 0),
            external_id='CM_SCH_2004'
        )

        db.session.add(core_schedule)
        db.session.commit()

        yield (core_event, supervisor_event, core_schedule)


@pytest.fixture(autouse=True)
def reset_test_environment():
    """
    Reset test environment before each test.
    """
    # Clear any cached imports
    yield

    # Cleanup after test
    pass
