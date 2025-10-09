"""
Test script to verify the new project structure works correctly
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
print("Testing New Project Structure")
print("scheduler_app/ is now the root directory")
print("=" * 60)

tests = [
    ("Constants module", "import constants"),
    ("EDR module", "from edr import EDRReportGenerator, EDRPDFGenerator"),
    ("Walmart API PDF Generator", "from walmart_api.pdf_generator import EDRPDFGenerator"),
    ("Models", "from models import init_models"),
    ("Config", "from config import get_config"),
    ("Routes - Auth", "from routes import auth_bp"),
    ("Routes - Main", "from routes.main import main_bp"),
    ("Routes - Printing", "from routes.printing import printing_bp"),
    ("Services - EDR", "from services import edr_service"),
    ("Utils", "from utils.event_helpers import extract_event_number"),
]

results = []
for test_name, import_stmt in tests:
    results.append(test_import(test_name, import_stmt))

print("\n" + "=" * 60)
print(f"Results: {sum(results)}/{len(results)} tests passed")
print("=" * 60)

if all(results):
    print("\nAll imports successful! New structure working correctly.")
    sys.exit(0)
else:
    print("\nSome imports failed. Please review errors above.")
    sys.exit(1)
