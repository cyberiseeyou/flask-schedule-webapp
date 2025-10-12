"""
Comparison Test: Production vs API_Integration implementations
Tests which implementation is more suitable for your needs
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 70)
print("CROSSMARK API IMPLEMENTATION COMPARISON TEST")
print("=" * 70)

# Test 1: Import Test
print("\n[TEST 1] Import Check")
print("-" * 70)

try:
    from crossmark_improvements import CrossmarkAPIClient, EventType, EventDatabase
    print("[OK] API_Integration imports successful")
    api_integration_ok = True
except Exception as e:
    print(f"[FAIL] API_Integration import failed: {e}")
    api_integration_ok = False

try:
    from scheduler_app.session_api_service import SessionAPIService
    print("[OK] Production (SessionAPIService) imports successful")
    production_ok = True
except Exception as e:
    print(f"[FAIL] Production import failed: {e}")
    production_ok = False

# Test 2: Feature Comparison
print("\n[TEST 2] Feature Comparison")
print("-" * 70)

features_matrix = {
    "Type-safe dataclasses": {
        "api_integration": True,
        "production": False
    },
    "Enhanced database schema": {
        "api_integration": True,
        "production": False
    },
    "Custom exception hierarchy": {
        "api_integration": True,
        "production": True  # Has SessionError
    },
    "Flask integration": {
        "api_integration": False,
        "production": True
    },
    "PHPSESSID authentication": {
        "api_integration": False,
        "production": True
    },
    "Planning controller APIs": {
        "api_integration": False,
        "production": True
    },
    "mPlan scheduling": {
        "api_integration": False,
        "production": True
    },
    "Batch operations": {
        "api_integration": True,
        "production": True
    },
    "Rep availability APIs": {
        "api_integration": False,
        "production": True
    },
    "MCP server tools": {
        "api_integration": True,
        "production": False
    }
}

print(f"{'Feature':<30} {'API_Integration':<18} {'Production':<18}")
print("-" * 70)
for feature, support in features_matrix.items():
    api_mark = "[YES]" if support["api_integration"] else "[NO] "
    prod_mark = "[YES]" if support["production"] else "[NO] "
    print(f"{feature:<30} {api_mark:<18} {prod_mark:<18}")

# Test 3: Code Complexity
print("\n[TEST 3] Code Complexity")
print("-" * 70)

if api_integration_ok:
    # Count methods in CrossmarkAPIClient
    api_methods = [m for m in dir(CrossmarkAPIClient) if not m.startswith('_')]
    print(f"API_Integration methods: {len(api_methods)}")

if production_ok:
    # Count methods in SessionAPIService
    prod_methods = [m for m in dir(SessionAPIService) if not m.startswith('_')]
    print(f"Production methods: {len(prod_methods)}")

# Test 4: Database Schema Comparison
print("\n[TEST 4] Database Schema")
print("-" * 70)

if api_integration_ok:
    print("\n API_Integration Schema:")
    print("  - scheduled_events (main table)")
    print("  - event_reps (relationships)")
    print("  - event_locations (relationships)")
    print("  - event_mplans (relationships)")
    print("  -> Total: 4 tables (relational)")

print("\n Production Schema:")
print("  -> Database structure not visible from session_api_service.py")
print("  -> Likely managed elsewhere in the Flask app")

# Test 5: Recommendations
print("\n[TEST 5] RECOMMENDATIONS")
print("=" * 70)

print("\n>>> BEST APPROACH: Hybrid Solution")
print("-" * 70)
print("1. KEEP production SessionAPIService as the foundation")
print("   * It has proven authentication")
print("   * It has comprehensive API coverage")
print("   * It's integrated with Flask")
print()
print("2. ADD features from API_Integration:")
print("   * Type-safe dataclasses (ScheduledEvent, etc.)")
print("   * Enhanced database schema with relationships")
print("   * Custom exception types")
print("   * EventDatabase abstraction class")
print()
print("3. CREATE new file: scheduler_app/crossmark_models.py")
print("   -> Define all the dataclasses")
print("   -> Define custom exceptions")
print()
print("4. CREATE new file: scheduler_app/crossmark_database.py")
print("   -> Implement EventDatabase with 4-table schema")
print()
print("5. UPDATE session_api_service.py:")
print("   -> Import and use the new models")
print("   -> Return typed objects instead of dicts")

print("\n>>> NEXT STEPS:")
print("-" * 70)
print("1. Run this comparison test")
print("2. Try authentication with BOTH implementations")
print("3. Cherry-pick best features into hybrid solution")
print("4. Write integration tests")

# Test 6: Authentication Test (if credentials available)
print("\n[TEST 6] Authentication Test")
print("-" * 70)

username = os.getenv("CROSSMARK_USERNAME")
password = os.getenv("CROSSMARK_PASSWORD")

if not (username and password):
    print("[SKIP] Set CROSSMARK_USERNAME and CROSSMARK_PASSWORD to test authentication")
else:
    print(f"Testing authentication with username: {username}")

    # Test Production
    if production_ok:
        print("\nTesting Production (SessionAPIService)...")
        try:
            session_api = SessionAPIService()
            session_api.base_url = "https://crossmark.mvretail.com"
            session_api.username = username
            session_api.password = password
            session_api.timezone = "America/Indiana/Indianapolis"
            session_api.timeout = 30
            session_api.max_retries = 3
            session_api.retry_delay = 1
            session_api.session_refresh_interval = 3600
            session_api._setup_session()

            if session_api.login():
                print("[OK] Production authentication SUCCESSFUL")
                print(f"   Session ID: {session_api.phpsessid[:8] + '...' if session_api.phpsessid else 'None'}")
            else:
                print("[FAIL] Production authentication FAILED")
        except Exception as e:
            print(f"[FAIL] Production authentication ERROR: {e}")

    # Test API_Integration
    if api_integration_ok:
        print("\nTesting API_Integration (CrossmarkAPIClient)...")
        async def test_auth():
            try:
                client = CrossmarkAPIClient()
                await client.authenticate(username, password)
                if client.is_authenticated():
                    print("[OK] API_Integration authentication SUCCESSFUL")
                else:
                    print("[FAIL] API_Integration authentication FAILED")
                await client.close()
            except Exception as e:
                print(f"[FAIL] API_Integration authentication ERROR: {e}")

        asyncio.run(test_auth())

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
