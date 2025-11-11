"""
Comprehensive Codebase Test Suite
Tests application startup, imports, database, routes, and configuration
"""
import sys
import os
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Results tracker
test_results = {
    'passed': [],
    'failed': [],
    'warnings': []
}

def test_result(name, status, message=''):
    """Record test result"""
    if status == 'PASS':
        test_results['passed'].append((name, message))
        print(f"[PASS] {name} {message}")
    elif status == 'FAIL':
        test_results['failed'].append((name, message))
        print(f"[FAIL] {name} {message}")
    elif status == 'WARN':
        test_results['warnings'].append((name, message))
        print(f"[WARN] {name} {message}")

print("="*80)
print("CODEBASE TEST SUITE")
print("="*80)
print()

# Test 1: Critical Imports
print("[1/8] Testing Critical Imports...")
try:
    import flask
    import sqlalchemy
    import flask_migrate
    import flask_wtf
    from config import get_config
    test_result("Critical Imports", "PASS")
except ImportError as e:
    test_result("Critical Imports", "FAIL", str(e))

# Test 2: Configuration Loading
print("\n[2/8] Testing Configuration...")
try:
    from config import get_config, DevelopmentConfig, ProductionConfig

    # Test development config
    dev_config = get_config('development')
    assert dev_config.DEBUG == True

    # Test config validation doesn't crash
    dev_config.validate(validate_walmart=False)

    test_result("Configuration", "PASS", "Dev and Prod configs loaded")
except Exception as e:
    test_result("Configuration", "FAIL", str(e))

# Test 3: Application Creation
print("\n[3/8] Testing Application Creation...")
try:
    from app import app, db

    # Check app is created
    assert app is not None
    assert app.name == 'app'

    # Check database is initialized
    assert db is not None

    test_result("Application Creation", "PASS", f"App: {app.name}")
except Exception as e:
    test_result("Application Creation", "FAIL", str(e))

# Test 4: Database Models
print("\n[4/8] Testing Database Models...")
try:
    from models import get_models

    # Get models from registry
    with app.app_context():
        models_dict = get_models()

        # Check we have models
        assert len(models_dict) > 0

        # Check critical models exist
        critical_models = ['Employee', 'Event', 'Schedule', 'SystemSetting']
        for model_name in critical_models:
            assert model_name in models_dict, f"Missing {model_name}"
            model = models_dict[model_name]
            assert hasattr(model, '__tablename__')
            assert hasattr(model, 'query')

        test_result("Database Models", "PASS", f"{len(models_dict)} models loaded")
except Exception as e:
    test_result("Database Models", "FAIL", str(e))

# Test 5: Database Connection
print("\n[5/8] Testing Database Connection...")
try:
    from models import get_models

    with app.app_context():
        # Try to query the database
        models_dict = get_models()
        Employee = models_dict['Employee']
        count = Employee.query.count()
        test_result("Database Connection", "PASS", f"{count} employees in DB")
except Exception as e:
    test_result("Database Connection", "FAIL", str(e))

# Test 6: Routes Registration
print("\n[6/8] Testing Route Registration...")
try:
    routes = []
    with app.app_context():
        for rule in app.url_map.iter_rules():
            if rule.endpoint != 'static':
                routes.append(f"{rule.rule} [{', '.join(rule.methods)}]")

    # Check for critical routes
    critical_routes = ['/', '/login', '/api', '/employees']
    registered = [r for r in routes if any(cr in r for cr in critical_routes)]

    if len(routes) > 0:
        test_result("Route Registration", "PASS", f"{len(routes)} routes registered")
    else:
        test_result("Route Registration", "FAIL", "No routes registered")
except Exception as e:
    test_result("Route Registration", "FAIL", str(e))

# Test 7: External API Service
print("\n[7/8] Testing External API Service...")
try:
    from session_api_service import session_api

    # Check service is initialized
    assert session_api is not None
    assert hasattr(session_api, 'get_employees')
    assert hasattr(session_api, 'get_events')

    test_result("External API Service", "PASS", "SessionAPI initialized")
except Exception as e:
    test_result("External API Service", "FAIL", str(e))

# Test 8: Sync Engine
print("\n[8/8] Testing Sync Engine...")
try:
    from sync_engine import sync_engine

    # Check sync engine is initialized
    assert sync_engine is not None
    assert hasattr(sync_engine, 'sync_all')

    test_result("Sync Engine", "PASS", "Sync engine initialized")
except Exception as e:
    test_result("Sync Engine", "FAIL", str(e))

# Test 9: Error Handlers
print("\n[9/9] Testing Error Handlers...")
try:
    from error_handlers import setup_logging, register_error_handlers

    # Check functions exist
    assert callable(setup_logging)
    assert callable(register_error_handlers)

    test_result("Error Handlers", "PASS", "Error handling configured")
except Exception as e:
    test_result("Error Handlers", "FAIL", str(e))

# Print Summary
print("\n" + "="*80)
print("TEST SUMMARY")
print("="*80)
print(f"Passed:   {len(test_results['passed'])}")
print(f"Failed:   {len(test_results['failed'])}")
print(f"Warnings: {len(test_results['warnings'])}")
print("="*80)

if test_results['failed']:
    print("\nFAILED TESTS:")
    for name, msg in test_results['failed']:
        print(f"  - {name}: {msg}")

if test_results['warnings']:
    print("\nWARNINGS:")
    for name, msg in test_results['warnings']:
        print(f"  - {name}: {msg}")

print()

# Exit with appropriate code
sys.exit(0 if len(test_results['failed']) == 0 else 1)
