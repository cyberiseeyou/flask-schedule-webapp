"""
Test script to verify Crossmark API connection and authentication
"""
import sys
import os

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scheduler_app.app import app, external_api

def test_api_connection():
    """Test the external API connection and authentication"""

    with app.app_context():
        print("=" * 60)
        print("CROSSMARK API CONNECTION TEST")
        print("=" * 60)

        # Display configuration
        print("\n1. Configuration:")
        print(f"   Base URL: {app.config.get('EXTERNAL_API_BASE_URL')}")
        print(f"   Username: {app.config.get('EXTERNAL_API_USERNAME')}")
        print(f"   Password: {'*' * len(app.config.get('EXTERNAL_API_PASSWORD', ''))}")
        print(f"   Timeout: {app.config.get('EXTERNAL_API_TIMEOUT')}s")

        # Test authentication
        print("\n2. Testing Authentication:")
        print("   Attempting to login...")

        try:
            success = external_api.login()

            if success:
                print("   [SUCCESS] Authentication SUCCESSFUL")
                print(f"   Session ID: {external_api.phpsessid[:8] + '...' if external_api.phpsessid else 'None'}")
                print(f"   Authenticated: {external_api.authenticated}")
                print(f"   Last Login: {external_api.last_login}")

                # Test a simple API call
                print("\n3. Testing API Call:")
                print("   Fetching user info...")
                user_info = external_api._get_user_info()

                if user_info:
                    print("   [SUCCESS] API call SUCCESSFUL")
                    print(f"   User: {user_info.get('username', 'Unknown')}")
                else:
                    print("   [FAILED] API call FAILED (no user info returned)")

                # Test health check
                print("\n4. Health Check:")
                health = external_api.health_check()
                print(f"   Status: {health.get('status')}")
                print(f"   Message: {health.get('message')}")

                return True
            else:
                print("   [FAILED] Authentication FAILED")
                print("   Possible reasons:")
                print("   - Incorrect username/password")
                print("   - Network connectivity issues")
                print("   - API endpoint changed")
                return False

        except Exception as e:
            print(f"   [ERROR] Exception during authentication: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            print("\n" + "=" * 60)

if __name__ == '__main__':
    success = test_api_connection()
    sys.exit(0 if success else 1)
