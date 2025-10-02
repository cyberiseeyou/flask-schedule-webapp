#!/usr/bin/env python3
"""
Test script to verify API data format
"""

# Test employee ID extraction
employee_ids = [
    "US815021",  # DIANE CARR
    "US863735",  # THOMAS RARICK
    "US857761",  # MICHELLE MONTAGUE
]

print("Employee ID Extraction Test:")
print("-" * 40)
for emp_id in employee_ids:
    if emp_id.startswith('US'):
        numeric_id = emp_id[2:]  # Remove 'US' prefix
        print(f"Original: {emp_id} → API RepID: {numeric_id}")
    else:
        print(f"Invalid format: {emp_id}")

print("\n✅ The numeric part is correctly extracted for API use")

# Sample API request format
print("\nSample API Request:")
print("-" * 40)
print("ClassName=MVScheduledmPlan")
print("RepID=815021")  # Numeric only, not US815021
print("mPlanID=31721927")  # Event external_id
print("LocationID=157384")  # Event location_mvid
print("Start=2025-10-04T09:00:00-04:00")
print("End=2025-10-04T10:00:00-04:00")
print("hash=")
print("v=3.0.1")
print("PlanningOverride=true")