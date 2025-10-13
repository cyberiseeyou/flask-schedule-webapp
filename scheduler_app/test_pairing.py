"""
Test Script for CORE-Supervisor Pairing - Reschedule Endpoint
==============================================================
"""

import os
import sys
from datetime import datetime, timedelta

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db

# Use models from app config (already initialized)
Employee = app.config['Employee']
Event = app.config['Event']
Schedule = app.config['Schedule']

def load_test_data():
    """Load adapted test data from SQL file."""
    print("\n" + "="*80)
    print("LOADING TEST DATA")
    print("="*80)

    with app.app_context():
        # First, check if test data already exists
        existing_events = db.session.query(Event).filter(Event.id >= 1000).count()
        if existing_events > 0:
            print(f"WARNING: Test data already loaded ({existing_events} events found)")
            print("   Skipping data load. To reload, run: DELETE FROM events WHERE id >= 1000;")
            return

        # Read SQL file
        sql_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_data', 'sprint1_adapted_testdata.sql')

        print(f"Reading: {sql_file}")

        with open(sql_file, 'r') as f:
            sql_content = f.read()

        # Execute INSERT statements only
        lines = sql_content.split('\n')
        current_statement = []

        for line in lines:
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('--'):
                continue

            current_statement.append(line)

            # Execute when we hit a semicolon
            if line.endswith(';'):
                statement = ' '.join(current_statement)

                if statement.upper().startswith('INSERT'):
                    try:
                        db.session.execute(db.text(statement))
                    except Exception as e:
                        if 'UNIQUE constraint' not in str(e):
                            print(f"Error: {e}")

                current_statement = []

        db.session.commit()

        # Verify data
        events_count = db.session.query(Event).filter(Event.id >= 1000).count()
        schedules_count = db.session.query(Schedule).filter(Schedule.id >= 2000).count()

        print(f"PASS: Test data loaded successfully")
        print(f"   - Events: {events_count}")
        print(f"   - Schedules: {schedules_count}")

def verify_pairing():
    """Verify CORE-Supervisor pairs."""
    print("\n" + "="*80)
    print("VERIFYING CORE-SUPERVISOR PAIRING")
    print("="*80)

    with app.app_context():
        import re

        # Find CORE events
        core_events = db.session.query(Event).filter(
            Event.project_name.like('%-CORE-%'),
            Event.id >= 1000
        ).all()

        print(f"\nFound {len(core_events)} CORE events:\n")

        for core in core_events:
            match = re.search(r'(\d{6})-CORE-', core.project_name, re.IGNORECASE)

            if match:
                event_number = match.group(1)
                supervisor = db.session.query(Event).filter(
                    Event.project_name.ilike(f'{event_number}-Supervisor-%')
                ).first()

                if supervisor:
                    core_sched = db.session.query(Schedule).filter_by(event_ref_num=core.project_ref_num).first()
                    sup_sched = db.session.query(Schedule).filter_by(event_ref_num=supervisor.project_ref_num).first()

                    print(f"  {core.project_ref_num}: {core.project_name}")
                    print(f"    Schedule: {core_sched.schedule_datetime if core_sched else 'Not scheduled'}")
                    print(f"  {supervisor.project_ref_num}: {supervisor.project_name}")
                    print(f"    Schedule: {sup_sched.schedule_datetime if sup_sched else 'Not scheduled'}")
                    print()
                else:
                    print(f"  WARNING: {core.project_ref_num}: {core.project_name} -> No Supervisor (orphan)")
                    print()

def test_helper_functions():
    """Test the helper functions for CORE-Supervisor pairing."""
    print("\n" + "="*80)
    print("TESTING HELPER FUNCTIONS")
    print("="*80)

    with app.app_context():
        from utils.event_helpers import (
            is_core_event_redesign,
            get_supervisor_event,
            get_supervisor_status
        )

        # Get CORE event 606001
        core_event = db.session.query(Event).filter_by(project_ref_num=606001).first()

        if not core_event:
            print("FAIL: CORE event 606001 not found")
            return

        print(f"\nTesting with: {core_event.project_name}")

        # Test is_core_event_redesign
        is_core = is_core_event_redesign(core_event)
        print(f"\n1. is_core_event_redesign(): {is_core}")

        if is_core:
            print("   PASS: Correctly identified as CORE event")
        else:
            print("   FAIL: Should be CORE event")

        # Test get_supervisor_event
        supervisor = get_supervisor_event(core_event)
        print(f"\n2. get_supervisor_event():")

        if supervisor:
            print(f"   Found: {supervisor.project_name} (ref: {supervisor.project_ref_num})")
            print("   PASS: Supervisor found")
        else:
            print("   FAIL: Supervisor not found")

        # Test get_supervisor_status
        status = get_supervisor_status(core_event)
        print(f"\n3. get_supervisor_status():")
        print(f"   Exists: {status['exists']}")
        print(f"   Scheduled: {status['is_scheduled']}")
        print(f"   Condition: {status.get('condition', 'N/A')}")

        if status['exists'] and status['is_scheduled']:
            print("   PASS: Supervisor exists and is scheduled")
        else:
            print("   INFO: Supervisor may not be scheduled")

def test_mock_api():
    """Test the mock Crossmark API."""
    print("\n" + "="*80)
    print("TESTING MOCK CROSSMARK API")
    print("="*80)

    with app.app_context():
        from tests.mock_crossmark_api import MockCrossmarkAPI

        mock_api = MockCrossmarkAPI()

        # Test login
        print("\n1. Testing login()...")
        result = mock_api.login()
        print(f"   Result: {result}")
        print(f"   PASS: Login successful" if result else "   FAIL: Login failed")

        # Test schedule_mplan_event
        print("\n2. Testing schedule_mplan_event()...")
        result = mock_api.schedule_mplan_event(
            rep_id='101',
            mplan_id='606001',
            location_id='12345',
            start_datetime=datetime(2025, 10, 20, 10, 0),
            end_datetime=datetime(2025, 10, 20, 16, 30)
        )
        print(f"   Success: {result.get('success')}")
        print(f"   Schedule ID: {result.get('schedule_id')}")
        print(f"   PASS: Event scheduled" if result.get('success') else "   FAIL: Scheduling failed")

        # Test call logging
        print("\n3. Testing call logging...")
        calls = mock_api.get_calls_for_method('schedule_mplan_event')
        print(f"   Calls logged: {len(calls)}")
        print(f"   PASS: Call logging works" if len(calls) == 1 else "   FAIL: Call logging not working")

        # Test failure mode
        print("\n4. Testing failure mode...")
        mock_api.set_should_fail(True, "Test failure")
        result = mock_api.schedule_mplan_event(
            rep_id='102',
            mplan_id='606002',
            location_id='12345',
            start_datetime=datetime(2025, 10, 20, 12, 0),
            end_datetime=datetime(2025, 10, 20, 12, 5)
        )
        print(f"   Success: {result.get('success')}")
        print(f"   Message: {result.get('message')}")
        print(f"   PASS: Failure mode works" if not result.get('success') else "   FAIL: Should have failed")

def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("CORE-SUPERVISOR PAIRING TEST SUITE")
    print("Sprint 2 - Calendar Redesign")
    print("="*80)

    load_test_data()
    verify_pairing()
    test_helper_functions()
    test_mock_api()

    print("\n" + "="*80)
    print("TEST SUITE COMPLETE")
    print("="*80)
    print("\nNext Steps:")
    print("1. Test actual reschedule endpoint with Flask test client")
    print("2. Verify transaction rollback on API failure")
    print("3. Test unschedule endpoint (not yet implemented)")

if __name__ == '__main__':
    main()
