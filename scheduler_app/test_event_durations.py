"""
Test default event duration functionality
"""
from datetime import datetime, timedelta
from models.event import create_event_model
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Create a test Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Create Event model
Event = create_event_model(db)

# Create tables
with app.app_context():
    db.create_all()

    # Test 1: Core event should have 6.5 hours (390 minutes)
    core_event = Event(
        project_name='CORE Test Event',
        project_ref_num=100001,
        start_datetime=datetime.now(),
        due_datetime=datetime.now() + timedelta(days=1)
    )
    core_event.event_type = core_event.detect_event_type()
    core_event.set_default_duration()
    assert core_event.event_type == 'Core', f"Expected 'Core', got {core_event.event_type}"
    assert core_event.estimated_time == 390, f"Expected 390 minutes, got {core_event.estimated_time}"
    print("[PASS] Test 1: Core event has 390 minutes (6.5 hours)")

    # Test 2: Juicer event should have 9 hours (540 minutes)
    juicer_event = Event(
        project_name='JUICER Production Event',
        project_ref_num=100002,
        start_datetime=datetime.now(),
        due_datetime=datetime.now() + timedelta(days=1)
    )
    juicer_event.event_type = juicer_event.detect_event_type()
    juicer_event.set_default_duration()
    assert juicer_event.event_type == 'Juicer', f"Expected 'Juicer', got {juicer_event.event_type}"
    assert juicer_event.estimated_time == 540, f"Expected 540 minutes, got {juicer_event.estimated_time}"
    print("[PASS] Test 2: Juicer event has 540 minutes (9 hours)")

    # Test 3: Supervisor event should have 5 minutes
    supervisor_event = Event(
        project_name='SUPERVISOR Event',
        project_ref_num=100003,
        start_datetime=datetime.now(),
        due_datetime=datetime.now() + timedelta(days=1)
    )
    supervisor_event.event_type = supervisor_event.detect_event_type()
    supervisor_event.set_default_duration()
    assert supervisor_event.event_type == 'Supervisor', f"Expected 'Supervisor', got {supervisor_event.event_type}"
    assert supervisor_event.estimated_time == 5, f"Expected 5 minutes, got {supervisor_event.estimated_time}"
    print("[PASS] Test 3: Supervisor event has 5 minutes")

    # Test 4: Digital event should have 15 minutes
    digital_event = Event(
        project_name='DIGITAL Setup Event',
        project_ref_num=100004,
        start_datetime=datetime.now(),
        due_datetime=datetime.now() + timedelta(days=1)
    )
    digital_event.event_type = digital_event.detect_event_type()
    digital_event.set_default_duration()
    assert digital_event.event_type == 'Digitals', f"Expected 'Digitals', got {digital_event.event_type}"
    assert digital_event.estimated_time == 15, f"Expected 15 minutes, got {digital_event.estimated_time}"
    print("[PASS] Test 4: Digital event has 15 minutes")

    # Test 5: Freeosk event should have 5 minutes
    freeosk_event = Event(
        project_name='FREEOSK Event',
        project_ref_num=100005,
        start_datetime=datetime.now(),
        due_datetime=datetime.now() + timedelta(days=1)
    )
    freeosk_event.event_type = freeosk_event.detect_event_type()
    freeosk_event.set_default_duration()
    assert freeosk_event.event_type == 'Freeosk', f"Expected 'Freeosk', got {freeosk_event.event_type}"
    assert freeosk_event.estimated_time == 5, f"Expected 5 minutes, got {freeosk_event.estimated_time}"
    print("[PASS] Test 5: Freeosk event has 5 minutes")

    # Test 6: Other event should have 15 minutes
    other_event = Event(
        project_name='Some Random Event',
        project_ref_num=100006,
        start_datetime=datetime.now(),
        due_datetime=datetime.now() + timedelta(days=1)
    )
    other_event.event_type = other_event.detect_event_type()
    other_event.set_default_duration()
    assert other_event.event_type == 'Other', f"Expected 'Other', got {other_event.event_type}"
    assert other_event.estimated_time == 15, f"Expected 15 minutes, got {other_event.estimated_time}"
    print("[PASS] Test 6: Other event has 15 minutes")

    # Test 7: calculate_end_datetime should work correctly
    start_time = datetime(2025, 10, 8, 10, 0)  # 10:00 AM
    end_time = core_event.calculate_end_datetime(start_time)
    expected_end = start_time + timedelta(minutes=390)  # 4:30 PM
    assert end_time == expected_end, f"Expected {expected_end}, got {end_time}"
    print("[PASS] Test 7: calculate_end_datetime works correctly")

    # Test 8: Don't override existing estimated_time
    custom_event = Event(
        project_name='CORE Test Event with Custom Time',
        project_ref_num=100007,
        start_datetime=datetime.now(),
        due_datetime=datetime.now() + timedelta(days=1),
        estimated_time=120  # 2 hours
    )
    custom_event.event_type = custom_event.detect_event_type()
    custom_event.set_default_duration()
    assert custom_event.estimated_time == 120, f"Expected 120 minutes (custom), got {custom_event.estimated_time}"
    print("[PASS] Test 8: Custom estimated_time is preserved")

    print("\n[SUCCESS] All tests passed!")
