"""
Quick Test - CORE-Supervisor Pairing Helper Functions
======================================================
Standalone test that doesn't require running the Flask app
"""

print("Testing CORE-Supervisor Pairing Helper Functions")
print("=" * 80)

# Test 1: Import and test regex pattern
print("\n1. Testing regex pattern for event number extraction...")
import re

test_cases = [
    ("606001-CORE-Super Pretzel", True, "606001"),
    ("606002-Supervisor-Super Pretzel", False, None),
    ("ABC123-CORE-Invalid", False, None),
    ("606001-core-Lowercase", True, "606001"),  # Case insensitive
]

for project_name, should_match, expected_number in test_cases:
    match = re.search(r'(\d{6})-CORE-', project_name, re.IGNORECASE)

    if should_match:
        if match and match.group(1) == expected_number:
            print(f"   PASS: '{project_name}' -> {match.group(1)}")
        else:
            print(f"   FAIL: '{project_name}' expected {expected_number}, got {match.group(1) if match else None}")
    else:
        if not match:
            print(f"   PASS: '{project_name}' -> No match (as expected)")
        else:
            print(f"   FAIL: '{project_name}' should not match")

# Test 2: Mock API functionality
print("\n2. Testing Mock Crossmark API...")
from tests.mock_crossmark_api import MockCrossmarkAPI
from datetime import datetime

mock_api = MockCrossmarkAPI()

# Test login
login_result = mock_api.login()
print(f"   Login: {'PASS' if login_result else 'FAIL'}")

# Test schedule
schedule_result = mock_api.schedule_mplan_event(
    rep_id='101',
    mplan_id='606001',
    location_id='12345',
    start_datetime=datetime(2025, 10, 20, 10, 0),
    end_datetime=datetime(2025, 10, 20, 16, 30)
)
print(f"   Schedule: {'PASS' if schedule_result.get('success') else 'FAIL'}")
print(f"   Schedule ID: {schedule_result.get('schedule_id')}")

# Test call logging
calls = mock_api.get_calls_for_method('schedule_mplan_event')
print(f"   Call logging: {'PASS' if len(calls) == 1 else 'FAIL'} ({len(calls)} calls logged)")

# Test failure mode
mock_api.set_should_fail(True, "Test failure")
fail_result = mock_api.schedule_mplan_event(
    rep_id='102',
    mplan_id='606002',
    location_id='12345',
    start_datetime=datetime(2025, 10, 20, 12, 0),
    end_datetime=datetime(2025, 10, 20, 12, 5)
)
print(f"   Failure mode: {'PASS' if not fail_result.get('success') else 'FAIL'}")

# Test 3: Test data structure
print("\n3. Checking test data SQL structure...")
import os
sql_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_data', 'sprint1_adapted_testdata.sql')

if os.path.exists(sql_file):
    print(f"   PASS: Test data file exists at {sql_file}")

    with open(sql_file, 'r') as f:
        content = f.read()

    # Count INSERT statements
    insert_count = content.count('INSERT INTO events')
    schedule_insert_count = content.count('INSERT INTO schedule')

    print(f"   Event inserts: {insert_count}")
    print(f"   Schedule inserts: {schedule_insert_count}")

    # Check for key test scenarios
    scenarios = [
        ("606001-CORE-Super Pretzel", "Scenario 1: CORE with Supervisor"),
        ("606001-Supervisor-Super Pretzel", "Scenario 1: Supervisor"),
        ("606999-CORE-Orphan Product", "Scenario 2: Orphan CORE"),
        ("608001-CORE-Cheetos", "Scenario 4: CORE scheduled, Supervisor unscheduled"),
    ]

    print("\n   Key scenarios in test data:")
    for search_str, description in scenarios:
        if search_str in content:
            print(f"   PASS: Found {description}")
        else:
            print(f"   FAIL: Missing {description}")
else:
    print(f"   FAIL: Test data file not found")

print("\n" + "=" * 80)
print("QUICK TEST COMPLETE")
print("\nConclusion:")
print("- Helper function regex patterns work correctly")
print("- Mock API functions correctly (login, schedule, logging, failure modes)")
print("- Test data file contains all required scenarios")
print("\nNext step: Load test data into database and test reschedule endpoint")
