"""
Test script to verify all refactored imports work correctly
"""
import sys
import traceback

def test_import(module_name, import_statement):
    """Test a single import"""
    try:
        exec(import_statement)
        print(f"[OK] {module_name}")
        return True
    except Exception as e:
        print(f"[FAIL] {module_name}: {str(e)}")
        traceback.print_exc()
        return False

print("=" * 60)
print("Testing Refactored Imports")
print("=" * 60)

tests = [
    ("Constants module", "from scheduler_app import constants"),
    ("EDR module", "from scheduler_app.edr import EDRReportGenerator, EDRPDFGenerator"),
    ("Walmart API PDF Generator", "from scheduler_app.walmart_api.pdf_generator import EDRPDFGenerator"),
    ("EDR Service", "from scheduler_app.services.edr_service import EDRService"),
    ("Printing routes", "from scheduler_app.routes.printing import printing_bp"),
]

results = []
for test_name, import_stmt in tests:
    results.append(test_import(test_name, import_stmt))

print("\n" + "=" * 60)
print(f"Results: {sum(results)}/{len(results)} tests passed")
print("=" * 60)

if all(results):
    print("\nAll imports successful! Refactoring complete.")
    sys.exit(0)
else:
    print("\nSome imports failed. Please review errors above.")
    sys.exit(1)
