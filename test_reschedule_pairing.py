"""
Test Script for CORE-Supervisor Pairing - Reschedule Endpoint
==============================================================

This script tests the reschedule endpoint's CORE-Supervisor pairing functionality
using the adapted test data and mock Crossmark API.

Test Cases:
- TC-033: Reschedule CORE with scheduled Supervisor (both should move)
- TC-034: Reschedule orphan CORE (only CORE should move)
- TC-036: Transaction rollback on API failure (both should remain unchanged)
"""

import sys
import os
from datetime import datetime, timedelta

# Add scheduler_app to path
base_dir = os.path.dirname(os.path.abspath(__file__))
scheduler_dir = os.path.join(base_dir, 'scheduler_app')
sys.path.insert(0, scheduler_dir)
sys.path.insert(0, base_dir)

from app import app, db
from models import init_models
from tests.mock_crossmark_api import enable_mock_api, assert_api_called, get_api_call_args

# Initialize models
models = init_models(db)
Employee = models['Employee']
Event = models['Event']
Schedule = models['Schedule']

def load_test_data():
    """Load adapted test data from SQL file."""
    print("\n" + "="*80)
    print("LOADING TEST DATA")
    print("="*80)

    with app.app_context():
        # Read and execute SQL file
        sql_file = os.path.join(os.path.dirname(__file__), 'test_data', 'sprint1_adapted_testdata.sql')

        with open(sql_file, 'r') as f:
            sql_content = f.read()

        # Split by semicolons and execute each statement
        statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]

        for statement in statements:
            if statement:
                try:
                    db.session.execute(db.text(statement))
                except Exception as e:
                    # Skip if record already exists or statement is comment
                    if 'UNIQUE constraint failed' not in str(e) and 'DELETE' not in statement:
                        print(f"Warning: {e}")

        db.session.commit()
        print("✅ Test data loaded successfully")

        # Verify data
        events_count = db.session.query(Event).filter(Event.id >= 1000).count()
        schedules_count = db.session.query(Schedule).filter(Schedule.id >= 2000).count()

        print(f"   - Events loaded: {events_count}")
        print(f"   - Schedules loaded: {schedules_count}")

def verify_pairing():
    """Verify CORE-Supervisor pairs are set up correctly."""
    print("\n" + "="*80)
    print("VERIFYING CORE-SUPERVISOR PAIRING")
    print("="*80)

    with app.app_context():
        # Find all CORE events
        core_events = db.session.query(Event).filter(
            Event.project_name.like('%-CORE-%'),
            Event.id >= 1000
        ).all()

        print(f"\nFound {len(core_events)} CORE events:")

        for core in core_events:
            # Extract event number
            import re
            match = re.search(r'(\d{6})-CORE-', core.project_name, re.IGNORECASE)

            if match:
                event_number = match.group(1)

                # Find supervisor
                supervisor = db.session.query(Event).filter(
                    Event.project_name.ilike(f'{event_number}-Supervisor-%')
                ).first()

                if supervisor:
                    print(f"  ✅ {core.project_name} → {supervisor.project_name}")
                else:
                    print(f"  ⚠️  {core.project_name} → No Supervisor found (orphan)")
            else:
                print(f"  ❌ {core.project_name} → Invalid event number format")

def test_tc033_reschedule_core_with_supervisor():
    """
    TC-033: Reschedule CORE with Scheduled Supervisor

    Expected: Both CORE and Supervisor rescheduled to new date
    """
    print("\n" + "="*80)
    print("TEST TC-033: Reschedule CORE with Scheduled Supervisor")
    print("="*80)

    with app.app_context():
        # Get CORE event 606001 and Supervisor 606002
        core_event = db.session.query(Event).filter_by(project_ref_num=606001).first()
        supervisor_event = db.session.query(Event).filter_by(project_ref_num=606002).first()
        core_schedule = db.session.query(Schedule).filter_by(event_ref_num=606001).first()
        supervisor_schedule = db.session.query(Schedule).filter_by(event_ref_num=606002).first()

        if not all([core_event, supervisor_event, core_schedule, supervisor_schedule]):
            print("❌ Test data not found")
            return

        print(f"\nBefore reschedule:")
        print(f"  CORE: {core_event.project_name}")
        print(f"    Scheduled: {core_schedule.schedule_datetime}")
        print(f"  Supervisor: {supervisor_event.project_name}")
        print(f"    Scheduled: {supervisor_schedule.schedule_datetime}")

        # Enable mock API
        mock_api = enable_mock_api(app)
        mock_api.reset()

        # Prepare reschedule data
        new_date = datetime(2025, 10, 20, 10, 0, 0)

        # Simulate reschedule API call
        from routes.api import api_bp
        test_client = app.test_client()

        response = test_client.post('/api/reschedule', json={
            'schedule_id': core_schedule.id,
            'new_date': new_date.strftime('%Y-%m-%d'),
            'new_time': new_date.strftime('%H:%M'),
            'employee_id': core_schedule.employee_id
        })

        print(f"\nAPI Response: {response.status_code}")
        print(f"  {response.get_json()}")

        # Verify both events rescheduled
        db.session.refresh(core_schedule)
        db.session.refresh(supervisor_schedule)

        print(f"\nAfter reschedule:")
        print(f"  CORE: {core_schedule.schedule_datetime}")
        print(f"  Supervisor: {supervisor_schedule.schedule_datetime}")

        # Verify API calls
        try:
            assert_api_called(mock_api, 'schedule_mplan_event', times=2)
            print("\n✅ TEST PASSED: Both CORE and Supervisor API calls made")

            # Verify dates match
            core_date = core_schedule.schedule_datetime.date()
            supervisor_date = supervisor_schedule.schedule_datetime.date()

            if core_date == supervisor_date:
                print("✅ TEST PASSED: CORE and Supervisor on same date")
            else:
                print(f"❌ TEST FAILED: Dates don't match (CORE: {core_date}, Supervisor: {supervisor_date})")

        except AssertionError as e:
            print(f"❌ TEST FAILED: {e}")

def test_tc034_reschedule_orphan_core():
    """
    TC-034: Reschedule Orphan CORE (no Supervisor)

    Expected: Only CORE rescheduled
    """
    print("\n" + "="*80)
    print("TEST TC-034: Reschedule Orphan CORE (No Supervisor)")
    print("="*80)

    with app.app_context():
        # Get orphan CORE event 606999
        core_event = db.session.query(Event).filter_by(project_ref_num=606999).first()
        core_schedule = db.session.query(Schedule).filter_by(event_ref_num=606999).first()

        if not all([core_event, core_schedule]):
            print("❌ Test data not found")
            return

        print(f"\nBefore reschedule:")
        print(f"  CORE: {core_event.project_name}")
        print(f"    Scheduled: {core_schedule.schedule_datetime}")

        # Enable mock API
        mock_api = enable_mock_api(app)
        mock_api.reset()

        # Prepare reschedule data
        new_date = datetime(2025, 10, 22, 11, 0, 0)

        # Simulate reschedule API call
        test_client = app.test_client()

        response = test_client.post('/api/reschedule', json={
            'schedule_id': core_schedule.id,
            'new_date': new_date.strftime('%Y-%m-%d'),
            'new_time': new_date.strftime('%H:%M'),
            'employee_id': core_schedule.employee_id
        })

        print(f"\nAPI Response: {response.status_code}")
        print(f"  {response.get_json()}")

        # Verify only CORE rescheduled
        db.session.refresh(core_schedule)

        print(f"\nAfter reschedule:")
        print(f"  CORE: {core_schedule.schedule_datetime}")

        # Verify only 1 API call (CORE only)
        try:
            assert_api_called(mock_api, 'schedule_mplan_event', times=1)
            print("\n✅ TEST PASSED: Only CORE API call made (no Supervisor)")
        except AssertionError as e:
            print(f"❌ TEST FAILED: {e}")

def test_tc036_transaction_rollback():
    """
    TC-036: Transaction Rollback on API Failure

    Expected: Both CORE and Supervisor remain unchanged after API failure
    """
    print("\n" + "="*80)
    print("TEST TC-036: Transaction Rollback on API Failure")
    print("="*80)

    with app.app_context():
        # Get CORE event 608001 and Supervisor 608002
        core_event = db.session.query(Event).filter_by(project_ref_num=608001).first()
        supervisor_event = db.session.query(Event).filter_by(project_ref_num=608002).first()
        core_schedule = db.session.query(Schedule).filter_by(event_ref_num=608001).first()

        # Note: Supervisor is unscheduled in this scenario, so we test CORE API failure only

        if not all([core_event, core_schedule]):
            print("❌ Test data not found")
            return

        print(f"\nBefore reschedule attempt:")
        print(f"  CORE: {core_event.project_name}")
        print(f"    Scheduled: {core_schedule.schedule_datetime}")

        original_datetime = core_schedule.schedule_datetime

        # Enable mock API and configure to fail
        mock_api = enable_mock_api(app)
        mock_api.reset()
        mock_api.set_should_fail(True, "Simulated API failure for testing")

        # Prepare reschedule data
        new_date = datetime(2025, 10, 25, 14, 0, 0)

        # Simulate reschedule API call (should fail)
        test_client = app.test_client()

        response = test_client.post('/api/reschedule', json={
            'schedule_id': core_schedule.id,
            'new_date': new_date.strftime('%Y-%m-%d'),
            'new_time': new_date.strftime('%H:%M'),
            'employee_id': core_schedule.employee_id
        })

        print(f"\nAPI Response: {response.status_code}")
        print(f"  {response.get_json()}")

        # Verify schedule unchanged
        db.session.refresh(core_schedule)

        print(f"\nAfter failed reschedule:")
        print(f"  CORE: {core_schedule.schedule_datetime}")

        # Verify rollback worked
        if core_schedule.schedule_datetime == original_datetime:
            print("\n✅ TEST PASSED: Transaction rolled back, schedule unchanged")
        else:
            print(f"❌ TEST FAILED: Schedule changed despite API failure")

def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("CORE-SUPERVISOR PAIRING TEST SUITE")
    print("Sprint 2 - Calendar Redesign")
    print("="*80)

    # Load test data
    load_test_data()

    # Verify pairing setup
    verify_pairing()

    # Run tests
    test_tc033_reschedule_core_with_supervisor()
    test_tc034_reschedule_orphan_core()
    test_tc036_transaction_rollback()

    print("\n" + "="*80)
    print("TEST SUITE COMPLETE")
    print("="*80)

if __name__ == '__main__':
    main()
