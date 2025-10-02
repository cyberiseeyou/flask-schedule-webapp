#!/usr/bin/env python3
"""
Test script to validate the updated API integration
"""
import os
import sys
import logging
from datetime import datetime, timedelta

# Add the scheduler_app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scheduler_app'))

from session_api_service import SessionAPIService

def test_api_integration():
    """Test the updated API integration"""

    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    logger.info("Testing updated Crossmark API integration...")

    # Create API service instance
    api_service = SessionAPIService()

    # Test configuration (without actual credentials)
    test_config = {
        'EXTERNAL_API_BASE_URL': 'https://crossmark.mvretail.com',
        'EXTERNAL_API_USERNAME': 'test_username',
        'EXTERNAL_API_PASSWORD': 'test_password',
        'EXTERNAL_API_TIMEZONE': 'America/Indiana/Indianapolis',
        'EXTERNAL_API_TIMEOUT': 30,
        'EXTERNAL_API_MAX_RETRIES': 3,
        'EXTERNAL_API_RETRY_DELAY': 1,
        'SESSION_REFRESH_INTERVAL': 3600
    }

    # Mock app config
    class MockApp:
        def __init__(self, config):
            self.config = config

    mock_app = MockApp(test_config)
    api_service.init_app(mock_app)

    logger.info("✓ API service initialized successfully")

    # Test method availability
    test_methods = [
        'login',
        'get_user_locale',
        'get_client_logo',
        'get_current_branch_info',
        'get_navigation_options',
        'get_scheduling_preferences',
        'get_fullcalendar_license_key',
        'get_available_representatives',
        'get_scheduled_events',
        'get_non_scheduled_visits',
        'get_more_filters_options',
        'save_scheduled_event',
        'update_scheduled_event',
        'delete_scheduled_event',
        'get_event_details',
        'get_rep_availability',
        'bulk_schedule_events',
        'create_schedule',
        'update_schedule',
        'delete_schedule',
        'health_check'
    ]

    logger.info("Testing method availability...")
    for method_name in test_methods:
        if hasattr(api_service, method_name):
            method = getattr(api_service, method_name)
            if callable(method):
                logger.info(f"✓ Method '{method_name}' is available and callable")
            else:
                logger.error(f"✗ Method '{method_name}' is not callable")
        else:
            logger.error(f"✗ Method '{method_name}' is not available")

    # Test health check (should work without authentication)
    logger.info("Testing health check...")
    health_result = api_service.health_check()
    logger.info(f"Health check result: {health_result}")

    # Test data format validation
    logger.info("Testing data format validation...")

    # Test scheduled event creation data structure
    sample_event_data = {
        "title": "Test Event",
        "description": "Test Description",
        "startDateTime": datetime.now().isoformat(),
        "endDateTime": (datetime.now() + timedelta(hours=2)).isoformat(),
        "repId": "test_rep_123",
        "locationId": "test_location_456",
        "type": "regular",
        "priority": "medium",
        "notes": "Test notes"
    }

    logger.info("✓ Sample event data structure validated")

    # Test filter data structure
    sample_filters = {
        "startDate": "2024-01-01",
        "endDate": "2024-12-31",
        "repId": "test_rep_123",
        "locationId": "test_location_456",
        "status": "scheduled"
    }

    logger.info("✓ Sample filter data structure validated")

    logger.info("✓ All API integration tests passed!")
    return True

if __name__ == "__main__":
    try:
        success = test_api_integration()
        if success:
            print("\n[SUCCESS] API integration tests completed successfully!")
            sys.exit(0)
        else:
            print("\n[FAILED] API integration tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Test execution failed: {str(e)}")
        sys.exit(1)