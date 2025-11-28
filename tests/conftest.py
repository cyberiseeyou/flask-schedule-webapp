"""
Pytest configuration and fixtures for Flask Schedule Webapp tests
"""
import pytest
from sqlalchemy import event
from app import create_app, db as _db


@pytest.fixture(scope='session')
def app():
    """Create and configure a test application instance"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use in-memory for tests
    app.config['WTF_CSRF_ENABLED'] = False

    # Create application context
    ctx = app.app_context()
    ctx.push()

    # Create all database tables
    _db.create_all()

    yield app

    # Cleanup
    _db.session.remove()
    _db.drop_all()
    ctx.pop()


@pytest.fixture(scope='session')
def db(app):
    """Provide database for tests"""
    return _db


@pytest.fixture(scope='function', autouse=True)
def cleanup_db(db):
    """Clean up database after each test to ensure test isolation"""
    yield
    # Clean up after each test
    db.session.rollback()
    # Clear all data from tables
    for table in reversed(db.metadata.sorted_tables):
        db.session.execute(table.delete())
    db.session.commit()
