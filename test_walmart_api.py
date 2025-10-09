"""
Test script for Walmart API endpoints
"""
import sys
import os

# Add scheduler_app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scheduler_app.app import app

def test_health_endpoint():
    """Test the health check endpoint"""
    print("Testing Walmart API health endpoint...")
    with app.test_client() as client:
        response = client.get('/api/walmart/health')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.get_json()}")
        assert response.status_code == 200
        assert response.get_json()['status'] == 'healthy'
        print("[PASS] Health endpoint test passed!")

def test_session_status_without_auth():
    """Test session status without authentication"""
    print("\nTesting session status without auth...")
    with app.test_client() as client:
        response = client.get('/api/walmart/auth/session-status')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.get_json()}")
        # Should get 401 since not authenticated
        assert response.status_code == 401
        print("[PASS] Session status (no auth) test passed!")

def test_blueprint_registration():
    """Test that blueprint is properly registered"""
    print("\nTesting blueprint registration...")
    blueprints = [bp.name for bp in app.blueprints.values()]
    print(f"Registered blueprints: {blueprints}")
    assert 'walmart_api' in blueprints
    print("[PASS] Blueprint registration test passed!")

if __name__ == '__main__':
    print("=" * 60)
    print("Walmart API Integration Tests")
    print("=" * 60)

    try:
        test_blueprint_registration()
        test_health_endpoint()
        test_session_status_without_auth()

        print("\n" + "=" * 60)
        print("All tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
