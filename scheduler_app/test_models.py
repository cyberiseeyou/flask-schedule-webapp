import pytest
import os
import tempfile
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TESTING'] = True

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

    __table_args__ = (
        db.Index('idx_schedules_date', 'schedule_datetime'),
    )

@pytest.fixture
def client():
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

class TestEmployeeModel:
    def test_employee_creation(self, client):
        with app.app_context():
            employee = Employee(id='EMP001', name='John Doe')
            db.session.add(employee)
            db.session.commit()
            
            retrieved = Employee.query.filter_by(id='EMP001').first()
            assert retrieved is not None
            assert retrieved.name == 'John Doe'

class TestEventModel:
    def test_event_creation(self, client):
        with app.app_context():
            event = Event(
                project_name='Test Project',
                project_ref_num=12345,
                location_mvid='LOC001',
                store_number=100,
                store_name='Test Store',
                start_datetime=datetime(2023, 1, 1, 9, 0),
                due_datetime=datetime(2023, 1, 2, 17, 0),
                estimated_time=480,
                is_scheduled=False
            )
            db.session.add(event)
            db.session.commit()
            
            retrieved = Event.query.filter_by(project_ref_num=12345).first()
            assert retrieved is not None
            assert retrieved.project_name == 'Test Project'
            assert retrieved.is_scheduled == False

    def test_event_unique_project_ref_num(self, client):
        with app.app_context():
            event1 = Event(
                project_name='Test Project 1',
                project_ref_num=12345,
                start_datetime=datetime(2023, 1, 1, 9, 0),
                due_datetime=datetime(2023, 1, 2, 17, 0)
            )
            event2 = Event(
                project_name='Test Project 2',
                project_ref_num=12345,
                start_datetime=datetime(2023, 1, 3, 9, 0),
                due_datetime=datetime(2023, 1, 4, 17, 0)
            )
            
            db.session.add(event1)
            db.session.commit()
            
            db.session.add(event2)
            with pytest.raises(Exception):
                db.session.commit()

class TestScheduleModel:
    def test_schedule_creation(self, client):
        with app.app_context():
            employee = Employee(id='EMP001', name='John Doe')
            event = Event(
                project_name='Test Project',
                project_ref_num=12345,
                start_datetime=datetime(2023, 1, 1, 9, 0),
                due_datetime=datetime(2023, 1, 2, 17, 0)
            )
            db.session.add(employee)
            db.session.add(event)
            db.session.commit()
            
            schedule = Schedule(
                event_ref_num=12345,
                employee_id='EMP001',
                schedule_datetime=datetime(2023, 1, 1, 10, 0)
            )
            db.session.add(schedule)
            db.session.commit()
            
            retrieved = Schedule.query.first()
            assert retrieved is not None
            assert retrieved.event_ref_num == 12345
            assert retrieved.employee_id == 'EMP001'

class TestDatabaseSchema:
    def test_tables_created(self, client):
        with app.app_context():
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            assert 'employees' in tables
            assert 'events' in tables
            assert 'schedules' in tables
    
    def test_indexes_created(self, client):
        with app.app_context():
            inspector = db.inspect(db.engine)
            indexes = inspector.get_indexes('schedules')
            
            index_names = [idx['name'] for idx in indexes]
            assert 'idx_schedules_date' in index_names