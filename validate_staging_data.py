#!/usr/bin/env python3
"""
Validate staging test data for CORE-Supervisor pairing.

This script tests the helper functions against the test data
to ensure they work correctly before testing the full endpoints.
"""

import os
import sys

# Add the scheduler_app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scheduler_app'))

from app import app, db

def validate_helper_functions():
    """Test helper functions with staging data"""

    with app.app_context():
        # Get models from app config
        Event = app.config.get('Event')
        Schedule = app.config.get('Schedule')

        if not Event or not Schedule:
            print("[ERROR] Models not found in app.config")
            return False

        # Import helper functions
        from utils.event_helpers import (
            is_core_event_redesign,
            get_supervisor_event,
            get_supervisor_status
        )

        print("\nCORE-Supervisor Pairing - Helper Function Validation")
        print("=" * 70)

        all_tests_passed = True

        # Test Scenario 1: CORE with scheduled Supervisor
        print("\n[Test 1] CORE with Scheduled Supervisor")
        print("-" * 70)

        core1 = Event.query.filter_by(project_ref_num=606001).first()
        if not core1:
            print("[ERROR] CORE event 606001 not found")
            return False

        # Test is_core_event_redesign
        is_core = is_core_event_redesign(core1)
        print(f"is_core_event_redesign(606001): {is_core}")
        if not is_core:
            print("[FAIL] Should detect as CORE event")
            all_tests_passed = False
        else:
            print("[PASS] Correctly identified as CORE event")

        # Test get_supervisor_event
        supervisor1 = get_supervisor_event(core1)
        if not supervisor1:
            print("[FAIL] Should find Supervisor event 606002")
            all_tests_passed = False
        else:
            print(f"[PASS] Found Supervisor: {supervisor1.project_name}")
            print(f"       project_ref_num: {supervisor1.project_ref_num}")

        # Test get_supervisor_status
        status1 = get_supervisor_status(core1)
        print(f"\nget_supervisor_status(606001):")
        print(f"  exists: {status1['exists']}")
        print(f"  is_scheduled: {status1['is_scheduled']}")
        print(f"  start_datetime: {status1['start_datetime']}")

        if not status1['exists']:
            print("[FAIL] Supervisor should exist")
            all_tests_passed = False
        elif not status1['is_scheduled']:
            print("[FAIL] Supervisor should be scheduled")
            all_tests_passed = False
        else:
            print("[PASS] Supervisor status correct")

        # Verify schedule exists
        schedule1 = Schedule.query.filter_by(event_ref_num=606002).first()
        if schedule1:
            print(f"[PASS] Supervisor schedule exists: {schedule1.schedule_datetime}")
        else:
            print("[FAIL] Supervisor schedule not found")
            all_tests_passed = False

        # Test Scenario 2: Orphan CORE
        print("\n[Test 2] Orphan CORE (No Supervisor)")
        print("-" * 70)

        core2 = Event.query.filter_by(project_ref_num=606999).first()
        if not core2:
            print("[ERROR] CORE event 606999 not found")
            return False

        is_core2 = is_core_event_redesign(core2)
        print(f"is_core_event_redesign(606999): {is_core2}")
        if not is_core2:
            print("[FAIL] Should detect as CORE event")
            all_tests_passed = False
        else:
            print("[PASS] Correctly identified as CORE event")

        supervisor2 = get_supervisor_event(core2)
        if supervisor2:
            print(f"[FAIL] Should NOT find Supervisor for orphan CORE")
            print(f"       Found: {supervisor2.project_name}")
            all_tests_passed = False
        else:
            print("[PASS] Correctly returned None for orphan CORE")

        status2 = get_supervisor_status(core2)
        print(f"\nget_supervisor_status(606999):")
        print(f"  exists: {status2['exists']}")
        print(f"  is_scheduled: {status2['is_scheduled']}")

        if status2['exists']:
            print("[FAIL] Supervisor should not exist")
            all_tests_passed = False
        else:
            print("[PASS] Supervisor status correct (does not exist)")

        # Test Scenario 3: CORE with unscheduled Supervisor
        print("\n[Test 3] CORE with Unscheduled Supervisor")
        print("-" * 70)

        core3 = Event.query.filter_by(project_ref_num=608001).first()
        if not core3:
            print("[ERROR] CORE event 608001 not found")
            return False

        is_core3 = is_core_event_redesign(core3)
        print(f"is_core_event_redesign(608001): {is_core3}")
        if not is_core3:
            print("[FAIL] Should detect as CORE event")
            all_tests_passed = False
        else:
            print("[PASS] Correctly identified as CORE event")

        supervisor3 = get_supervisor_event(core3)
        if not supervisor3:
            print("[FAIL] Should find Supervisor event 608002")
            all_tests_passed = False
        else:
            print(f"[PASS] Found Supervisor: {supervisor3.project_name}")
            print(f"       project_ref_num: {supervisor3.project_ref_num}")
            print(f"       is_scheduled: {supervisor3.is_scheduled}")

        status3 = get_supervisor_status(core3)
        print(f"\nget_supervisor_status(608001):")
        print(f"  exists: {status3['exists']}")
        print(f"  is_scheduled: {status3['is_scheduled']}")

        if not status3['exists']:
            print("[FAIL] Supervisor should exist")
            all_tests_passed = False
        elif status3['is_scheduled']:
            print("[FAIL] Supervisor should NOT be scheduled")
            all_tests_passed = False
        else:
            print("[PASS] Supervisor status correct (exists but not scheduled)")

        # Verify no schedule exists for Supervisor
        schedule3 = Schedule.query.filter_by(event_ref_num=608002).first()
        if schedule3:
            print(f"[FAIL] Supervisor should NOT have schedule record")
            all_tests_passed = False
        else:
            print("[PASS] Supervisor has no schedule record")

        # Summary
        print("\n" + "=" * 70)
        if all_tests_passed:
            print("[OK] All helper function tests PASSED!")
            print("=" * 70)
            print("\nHelper functions are working correctly.")
            print("Ready to test full reschedule/unschedule endpoints.")
            return True
        else:
            print("[ERROR] Some tests FAILED!")
            print("=" * 70)
            print("\nPlease review the failures above.")
            return False


if __name__ == '__main__':
    print("\nValidating CORE-Supervisor Pairing Helper Functions")
    print("=" * 70)

    success = validate_helper_functions()

    if success:
        print("\n[OK] Validation complete - All tests passed!")
        sys.exit(0)
    else:
        print("\n[ERROR] Validation failed - See errors above")
        sys.exit(1)
