#!/usr/bin/env python3
"""
Create test data for staging validation of CORE-Supervisor pairing.

This script creates test CORE and Supervisor events with schedules
for validating the Sprint 2 feature.
"""

import os
import sys
from datetime import datetime, timedelta

# Add the scheduler_app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scheduler_app'))

from app import app, db
from models import Event, Schedule, Employee

def create_test_data():
    """Create test CORE-Supervisor event pairs with schedules"""

    with app.app_context():
        print("Creating test data for CORE-Supervisor pairing validation...")
        print("=" * 70)

        # Check if test data already exists
        existing_core = Event.query.filter(Event.project_name.like('%-CORE-%')).first()
        if existing_core:
            print("\n[WARNING] Test CORE events already exist in database.")
            response = input("Delete existing test data and recreate? (y/n): ")
            if response.lower() != 'y':
                print("Aborted.")
                return False

            # Delete existing test events
            test_events = Event.query.filter(
                (Event.project_name.like('%-CORE-%')) |
                (Event.project_name.like('%-Supervisor-%'))
            ).all()

            for event in test_events:
                # Delete schedules first
                schedules = Schedule.query.filter_by(event_ref_num=event.project_ref_num).all()
                for schedule in schedules:
                    db.session.delete(schedule)
                db.session.delete(event)

            db.session.commit()
            print("[OK] Deleted existing test data")

        # Get a test employee
        employee = Employee.query.first()
        if not employee:
            print("\n[ERROR] No employees found in database. Cannot create schedules.")
            return False

        print(f"\n[OK] Using employee: {employee.name} (ID: {employee.id})")

        # Test Scenario 1: CORE with scheduled Supervisor (Happy Path)
        print("\n[1/3] Creating Test Scenario 1: CORE with scheduled Supervisor")
        print("-" * 70)

        core1_start = datetime(2025, 10, 20, 10, 0, 0)
        supervisor1_start = core1_start + timedelta(hours=2)

        core1 = Event(
            project_name="606001-CORE-Super Pretzel King Size",
            project_ref_num=606001,
            location_mvid="LOC_001",
            store_number=1234,
            store_name="Test Store 1",
            start_datetime=core1_start,
            due_datetime=core1_start + timedelta(hours=6, minutes=30),
            estimated_time=390,  # 6.5 hours in minutes
            is_scheduled=True,
            event_type="Core",
            external_id="CM_EV_606001",
            sync_status="synced"
        )

        supervisor1 = Event(
            project_name="606001-Supervisor-Super Pretzel King Size",
            project_ref_num=606002,
            location_mvid="LOC_001",
            store_number=1234,
            store_name="Test Store 1",
            start_datetime=supervisor1_start,
            due_datetime=supervisor1_start + timedelta(hours=2),
            estimated_time=120,  # 2 hours in minutes
            is_scheduled=True,
            event_type="Supervisor",
            external_id="CM_EV_606002",
            sync_status="synced"
        )

        db.session.add(core1)
        db.session.add(supervisor1)
        db.session.flush()  # Get IDs

        # Create schedules
        core1_schedule = Schedule(
            event_ref_num=606001,
            employee_id=employee.id,
            schedule_datetime=core1_start,
            external_id="CM_SCH_606001"
        )

        supervisor1_schedule = Schedule(
            event_ref_num=606002,
            employee_id=employee.id,
            schedule_datetime=supervisor1_start,
            external_id="CM_SCH_606002"
        )

        db.session.add(core1_schedule)
        db.session.add(supervisor1_schedule)

        print(f"  CORE Event:       {core1.project_name}")
        print(f"    - project_ref_num: {core1.project_ref_num}")
        print(f"    - start_datetime:  {core1_start}")
        print(f"    - external_id:     {core1.external_id}")
        print(f"  Supervisor Event: {supervisor1.project_name}")
        print(f"    - project_ref_num: {supervisor1.project_ref_num}")
        print(f"    - start_datetime:  {supervisor1_start} (2 hours after CORE)")
        print(f"    - external_id:     {supervisor1.external_id}")

        # Test Scenario 2: Orphan CORE (No Supervisor)
        print("\n[2/3] Creating Test Scenario 2: Orphan CORE (No Supervisor)")
        print("-" * 70)

        core2_start = datetime(2025, 10, 21, 11, 0, 0)

        core2 = Event(
            project_name="606999-CORE-Test Product Orphan",
            project_ref_num=606999,
            location_mvid="LOC_002",
            store_number=5678,
            store_name="Test Store 2",
            start_datetime=core2_start,
            due_datetime=core2_start + timedelta(hours=6, minutes=30),
            estimated_time=390,
            is_scheduled=True,
            event_type="Core",
            external_id="CM_EV_606999",
            sync_status="synced"
        )

        db.session.add(core2)
        db.session.flush()

        core2_schedule = Schedule(
            event_ref_num=606999,
            employee_id=employee.id,
            schedule_datetime=core2_start,
            external_id="CM_SCH_606999"
        )

        db.session.add(core2_schedule)

        print(f"  CORE Event:       {core2.project_name}")
        print(f"    - project_ref_num: {core2.project_ref_num}")
        print(f"    - start_datetime:  {core2_start}")
        print(f"    - No Supervisor event (orphan scenario)")

        # Test Scenario 3: CORE scheduled, Supervisor unscheduled
        print("\n[3/3] Creating Test Scenario 3: CORE with Unscheduled Supervisor")
        print("-" * 70)

        core3_start = datetime(2025, 10, 22, 9, 0, 0)

        core3 = Event(
            project_name="608001-CORE-Product With Unscheduled Supervisor",
            project_ref_num=608001,
            location_mvid="LOC_003",
            store_number=9012,
            store_name="Test Store 3",
            start_datetime=core3_start,
            due_datetime=core3_start + timedelta(hours=6, minutes=30),
            estimated_time=390,
            is_scheduled=True,
            event_type="Core",
            external_id="CM_EV_608001",
            sync_status="synced"
        )

        supervisor3 = Event(
            project_name="608001-Supervisor-Product With Unscheduled Supervisor",
            project_ref_num=608002,
            location_mvid="LOC_003",
            store_number=9012,
            store_name="Test Store 3",
            start_datetime=datetime(2025, 10, 22, 0, 0, 0),  # Placeholder datetime
            due_datetime=datetime(2025, 10, 22, 2, 0, 0),
            estimated_time=120,
            is_scheduled=False,  # NOT SCHEDULED
            event_type="Supervisor",
            sync_status="pending"
        )

        db.session.add(core3)
        db.session.add(supervisor3)
        db.session.flush()

        # Only create schedule for CORE, not Supervisor
        core3_schedule = Schedule(
            event_ref_num=608001,
            employee_id=employee.id,
            schedule_datetime=core3_start,
            external_id="CM_SCH_608001"
        )

        db.session.add(core3_schedule)

        print(f"  CORE Event:       {core3.project_name}")
        print(f"    - project_ref_num: {core3.project_ref_num}")
        print(f"    - start_datetime:  {core3_start}")
        print(f"    - is_scheduled:    True")
        print(f"  Supervisor Event: {supervisor3.project_name}")
        print(f"    - project_ref_num: {supervisor3.project_ref_num}")
        print(f"    - is_scheduled:    False (not scheduled)")
        print(f"    - No schedule record created")

        # Commit all changes
        db.session.commit()

        print("\n" + "=" * 70)
        print("[OK] Test data created successfully!")
        print("=" * 70)

        # Summary
        print("\nTest Data Summary:")
        print("-" * 70)
        print("Scenario 1: CORE (606001) + Supervisor (606002) - Both scheduled")
        print("            Use for: Reschedule together, Unschedule together")
        print()
        print("Scenario 2: CORE (606999) - Orphan (no Supervisor)")
        print("            Use for: Reschedule orphan, Unschedule orphan")
        print()
        print("Scenario 3: CORE (608001) + Supervisor (608002) - Only CORE scheduled")
        print("            Use for: Reschedule with unscheduled Supervisor")
        print()

        # Verification queries
        print("\nVerification Queries:")
        print("-" * 70)
        print("-- View all test CORE events:")
        print("SELECT project_ref_num, project_name, is_scheduled FROM events")
        print("WHERE project_name LIKE '%-CORE-%';")
        print()
        print("-- View all test Supervisor events:")
        print("SELECT project_ref_num, project_name, is_scheduled FROM events")
        print("WHERE project_name LIKE '%-Supervisor-%';")
        print()
        print("-- View all test schedules:")
        print("SELECT s.id, s.event_ref_num, s.schedule_datetime, e.project_name")
        print("FROM schedules s JOIN events e ON s.event_ref_num = e.project_ref_num")
        print("WHERE e.project_ref_num IN (606001, 606002, 606999, 608001, 608002);")

        return True


if __name__ == '__main__':
    print("\nCORE-Supervisor Pairing - Test Data Generator")
    print("=" * 70)
    print("This script creates test events for staging validation.")
    print("It will create 3 test scenarios with CORE and Supervisor events.")
    print()

    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Aborted.")
        sys.exit(0)

    success = create_test_data()
    if success:
        print("\n[OK] Ready for staging validation!")
        print("Next step: Follow STAGING_DEPLOYMENT_CHECKLIST.md")
        sys.exit(0)
    else:
        print("\n[ERROR] Failed to create test data")
        sys.exit(1)
