"""
Test automatic supervisor event scheduling when CORE events are scheduled
"""
from datetime import datetime, timedelta, date, time
from models.event import create_event_model
from models.schedule import create_schedule_model
from models.employee import create_employee_model
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Create a test Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Create models
Event = create_event_model(db)
Schedule = create_schedule_model(db)
Employee = create_employee_model(db)

# Import the auto_schedule_supervisor_event function
from routes.scheduling import auto_schedule_supervisor_event

# Create tables and run tests
with app.app_context():
    db.create_all()

    # Create test employees
    lead1 = Employee(
        id='LEAD001',
        name='John Lead',
        job_title='Lead Event Specialist',
        is_active=True,
        is_supervisor=True,
        adult_beverage_trained=True
    )

    lead2 = Employee(
        id='LEAD002',
        name='Jane Lead',
        job_title='Lead Event Specialist',
        is_active=True,
        is_supervisor=True,
        adult_beverage_trained=True
    )

    specialist = Employee(
        id='SPEC001',
        name='Bob Specialist',
        job_title='Event Specialist',
        is_active=True,
        is_supervisor=False,
        adult_beverage_trained=False
    )

    supervisor = Employee(
        id='SUP001',
        name='Alice Supervisor',
        job_title='Club Supervisor',
        is_active=True,
        is_supervisor=True,
        adult_beverage_trained=True
    )

    db.session.add_all([lead1, lead2, specialist, supervisor])
    db.session.commit()

    test_date = date(2025, 10, 15)

    # Test 1: CORE event scheduled to a Lead - Supervisor should go to that Lead
    print("\n=== Test 1: CORE event to Lead ===")
    core_event1 = Event(
        project_name='606001-CORE-Test Product',
        project_ref_num=606001,
        start_datetime=datetime.combine(test_date, time(9, 0)),
        due_datetime=datetime.combine(test_date, time(17, 0)),
        event_type='Core',
        is_scheduled=False
    )

    supervisor_event1 = Event(
        project_name='606001-Supervisor-Test Product',  # Same 6-digit number
        project_ref_num=606101,  # Different ref number
        start_datetime=datetime.combine(test_date, time(9, 0)),
        due_datetime=datetime.combine(test_date, time(17, 0)),
        event_type='Supervisor',
        is_scheduled=False
    )

    db.session.add_all([core_event1, supervisor_event1])
    db.session.commit()

    # Schedule CORE event to lead1
    core_schedule1 = Schedule(
        event_ref_num=606001,
        employee_id='LEAD001',
        schedule_datetime=datetime.combine(test_date, time(10, 0))
    )
    db.session.add(core_schedule1)
    db.session.commit()

    # Auto-schedule supervisor event
    success, event_name = auto_schedule_supervisor_event(
        db, Event, Schedule, Employee,
        606001,
        test_date,
        'LEAD001'
    )
    db.session.commit()

    assert success, "Supervisor event should be scheduled"
    supervisor_schedule1 = Schedule.query.filter_by(event_ref_num=606101).first()
    assert supervisor_schedule1 is not None, "Supervisor schedule should exist"
    assert supervisor_schedule1.employee_id == 'LEAD001', "Supervisor should be assigned to the Lead who has the CORE event"
    assert supervisor_schedule1.schedule_datetime.hour == 12, "Supervisor should be at noon"
    print(f"[PASS] Test 1: Supervisor event assigned to {lead1.name} (same Lead as CORE)")

    # Test 2: CORE event scheduled to a Specialist - Supervisor should go to a Lead with CORE or Club Supervisor
    print("\n=== Test 2: CORE event to Specialist (Lead already has CORE) ===")
    test_date2 = date(2025, 10, 16)

    core_event2a = Event(
        project_name='606002-CORE-Another Product',
        project_ref_num=606002,
        start_datetime=datetime.combine(test_date2, time(9, 0)),
        due_datetime=datetime.combine(test_date2, time(17, 0)),
        event_type='Core',
        is_scheduled=False
    )

    core_event2b = Event(
        project_name='606003-CORE-Yet Another Product',
        project_ref_num=606003,
        start_datetime=datetime.combine(test_date2, time(9, 0)),
        due_datetime=datetime.combine(test_date2, time(17, 0)),
        event_type='Core',
        is_scheduled=False
    )

    supervisor_event2 = Event(
        project_name='606003-Supervisor-Yet Another Product',  # Same 6-digit number
        project_ref_num=606103,  # Different ref number
        start_datetime=datetime.combine(test_date2, time(9, 0)),
        due_datetime=datetime.combine(test_date2, time(17, 0)),
        event_type='Supervisor',
        is_scheduled=False
    )

    db.session.add_all([core_event2a, core_event2b, supervisor_event2])
    db.session.commit()

    # Schedule first CORE to lead2
    core_schedule2a = Schedule(
        event_ref_num=606002,
        employee_id='LEAD002',
        schedule_datetime=datetime.combine(test_date2, time(10, 0))
    )
    db.session.add(core_schedule2a)

    # Schedule second CORE to specialist
    core_schedule2b = Schedule(
        event_ref_num=606003,
        employee_id='SPEC001',
        schedule_datetime=datetime.combine(test_date2, time(11, 0))
    )
    db.session.add(core_schedule2b)
    db.session.commit()

    # Auto-schedule supervisor event for the specialist's CORE
    success2, event_name2 = auto_schedule_supervisor_event(
        db, Event, Schedule, Employee,
        606003,
        test_date2,
        'SPEC001'
    )
    db.session.commit()

    assert success2, "Supervisor event should be scheduled"
    supervisor_schedule2 = Schedule.query.filter_by(event_ref_num=606103).first()
    assert supervisor_schedule2 is not None, "Supervisor schedule should exist"
    assert supervisor_schedule2.employee_id == 'LEAD002', "Supervisor should be assigned to the Lead who has a CORE event"
    assert supervisor_schedule2.schedule_datetime.hour == 12, "Supervisor should be at noon"
    print(f"[PASS] Test 2: Supervisor event assigned to {lead2.name} (Lead with CORE event on that day)")

    # Test 3: CORE event scheduled to Specialist, no Lead has CORE - Supervisor should go to Club Supervisor
    print("\n=== Test 3: CORE event to Specialist (no Lead has CORE) ===")
    test_date3 = date(2025, 10, 17)

    core_event3 = Event(
        project_name='606004-CORE-Product Four',
        project_ref_num=606004,
        start_datetime=datetime.combine(test_date3, time(9, 0)),
        due_datetime=datetime.combine(test_date3, time(17, 0)),
        event_type='Core',
        is_scheduled=False
    )

    supervisor_event3 = Event(
        project_name='606004-Supervisor-Product Four',  # Same 6-digit number
        project_ref_num=606104,  # Different ref number
        start_datetime=datetime.combine(test_date3, time(9, 0)),
        due_datetime=datetime.combine(test_date3, time(17, 0)),
        event_type='Supervisor',
        is_scheduled=False
    )

    db.session.add_all([core_event3, supervisor_event3])
    db.session.commit()

    # Schedule CORE to specialist (no Lead has CORE on this day)
    core_schedule3 = Schedule(
        event_ref_num=606004,
        employee_id='SPEC001',
        schedule_datetime=datetime.combine(test_date3, time(10, 0))
    )
    db.session.add(core_schedule3)
    db.session.commit()

    # Auto-schedule supervisor event
    success3, event_name3 = auto_schedule_supervisor_event(
        db, Event, Schedule, Employee,
        606004,
        test_date3,
        'SPEC001'
    )
    db.session.commit()

    assert success3, "Supervisor event should be scheduled"
    supervisor_schedule3 = Schedule.query.filter_by(event_ref_num=606104).first()
    assert supervisor_schedule3 is not None, "Supervisor schedule should exist"
    assert supervisor_schedule3.employee_id == 'SUP001', "Supervisor should be assigned to Club Supervisor"
    assert supervisor_schedule3.schedule_datetime.hour == 12, "Supervisor should be at noon"
    print(f"[PASS] Test 3: Supervisor event assigned to {supervisor.name} (Club Supervisor as fallback)")

    # Test 4: Verify supervisor events are scheduled at noon
    print("\n=== Test 4: Verify all supervisors scheduled at noon ===")
    all_supervisor_schedules = Schedule.query.join(
        Event, Schedule.event_ref_num == Event.project_ref_num
    ).filter(
        Event.event_type == 'Supervisor'
    ).all()

    for sched in all_supervisor_schedules:
        assert sched.schedule_datetime.hour == 12, f"Supervisor should be at noon, got {sched.schedule_datetime.hour}"
        assert sched.schedule_datetime.minute == 0, f"Supervisor should be at noon, got {sched.schedule_datetime.minute}"

    print(f"[PASS] Test 4: All {len(all_supervisor_schedules)} supervisor events scheduled at 12:00 PM")

    print("\n[SUCCESS] All supervisor auto-scheduling tests passed!")
