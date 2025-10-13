"""
Mock Crossmark API Service for Testing
=======================================

This mock service simulates the Crossmark API for testing CORE-Supervisor pairing
without requiring actual API credentials or network access.

Usage:
    from scheduler_app.tests.mock_crossmark_api import MockCrossmarkAPI

    # In test setup
    mock_api = MockCrossmarkAPI()
    app.config['TESTING'] = True
    app.config['USE_MOCK_API'] = True

    # Replace the real API with mock
    import session_api_service
    session_api_service.session_api = mock_api
"""

import logging
from datetime import datetime
from typing import Dict, Optional


class MockCrossmarkAPI:
    """
    Mock implementation of Crossmark API for testing.

    Simulates all API methods used by the scheduler application
    without making actual network requests.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.authenticated = True
        self.last_login = datetime.utcnow()
        self.phpsessid = "MOCK_SESSION_12345"
        self.user_info = {
            'username': 'test_user',
            'email': 'test@example.com'
        }

        # Track API calls for testing assertions
        self.call_log = []

        # Simulate API responses
        self.scheduled_events = {}  # {schedule_id: event_data}
        self.next_schedule_id = 10000

        # Control API behavior
        self.should_fail = False
        self.fail_message = "Mock API failure"
        self.fail_on_next_call = False

    def _log_call(self, method: str, **kwargs):
        """Log API call for testing assertions"""
        call_record = {
            'method': method,
            'timestamp': datetime.utcnow(),
            **kwargs
        }
        self.call_log.append(call_record)
        self.logger.info(f"Mock API call: {method} - {kwargs}")

    def clear_call_log(self):
        """Clear call log for fresh test"""
        self.call_log = []

    def get_calls_for_method(self, method: str):
        """Get all logged calls for a specific method"""
        return [call for call in self.call_log if call['method'] == method]

    def set_should_fail(self, should_fail: bool, message: str = "Mock API failure"):
        """Configure API to fail on next call"""
        self.should_fail = should_fail
        self.fail_message = message

    def fail_next_call(self, message: str = "Mock API failure"):
        """Configure API to fail on next call only"""
        self.fail_on_next_call = True
        self.fail_message = message

    def _check_failure(self):
        """Check if API should fail this call"""
        if self.should_fail or self.fail_on_next_call:
            if self.fail_on_next_call:
                self.fail_on_next_call = False  # Reset after one failure
            return True
        return False

    # =========================================================================
    # Authentication Methods
    # =========================================================================

    def login(self) -> bool:
        """Mock login - always succeeds unless configured to fail"""
        self._log_call('login')

        if self._check_failure():
            self.logger.warning(f"Mock login failed: {self.fail_message}")
            return False

        self.authenticated = True
        self.last_login = datetime.utcnow()
        self.logger.info("Mock login successful")
        return True

    def is_session_valid(self) -> bool:
        """Mock session validation - always valid"""
        return self.authenticated

    def ensure_authenticated(self) -> bool:
        """Mock authentication check"""
        if not self.authenticated:
            return self.login()
        return True

    # =========================================================================
    # Schedule Management Methods (Core Functionality)
    # =========================================================================

    def schedule_mplan_event(
        self,
        rep_id: str,
        mplan_id: str,
        location_id: str,
        start_datetime: datetime,
        end_datetime: datetime,
        planning_override: bool = True
    ) -> Dict:
        """
        Mock schedule event - simulates successful API call

        Args:
            rep_id: Employee ID
            mplan_id: Event ID (project_ref_num)
            location_id: Location ID
            start_datetime: Start datetime
            end_datetime: End datetime
            planning_override: Override planning constraints

        Returns:
            dict: {'success': bool, 'message': str, ...}
        """
        self._log_call(
            'schedule_mplan_event',
            rep_id=rep_id,
            mplan_id=mplan_id,
            location_id=location_id,
            start_datetime=start_datetime.isoformat(),
            end_datetime=end_datetime.isoformat(),
            planning_override=planning_override
        )

        # Check if should fail
        if self._check_failure():
            self.logger.warning(f"Mock schedule_mplan_event failed: {self.fail_message}")
            return {
                'success': False,
                'message': self.fail_message,
                'status_code': 500
            }

        # Simulate successful scheduling
        schedule_id = str(self.next_schedule_id)
        self.next_schedule_id += 1

        self.scheduled_events[schedule_id] = {
            'schedule_id': schedule_id,
            'rep_id': rep_id,
            'mplan_id': mplan_id,
            'location_id': location_id,
            'start_datetime': start_datetime,
            'end_datetime': end_datetime,
            'planning_override': planning_override,
            'scheduled_at': datetime.utcnow()
        }

        self.logger.info(
            f"Mock: Scheduled mPlan {mplan_id} for Rep {rep_id} "
            f"from {start_datetime} to {end_datetime}"
        )

        return {
            'success': True,
            'message': 'Event scheduled successfully (mock)',
            'mplan_id': mplan_id,
            'rep_id': rep_id,
            'schedule_id': schedule_id,
            'response_data': {
                'scheduleId': schedule_id,
                'status': 'Scheduled'
            }
        }

    def unschedule_mplan_event(self, schedule_id: str) -> Dict:
        """
        Mock unschedule event - simulates successful API call

        Args:
            schedule_id: The schedule ID to unschedule

        Returns:
            dict: {'success': bool, 'message': str}
        """
        self._log_call('unschedule_mplan_event', schedule_id=schedule_id)

        # Check if should fail
        if self._check_failure():
            self.logger.warning(f"Mock unschedule_mplan_event failed: {self.fail_message}")
            return {
                'success': False,
                'message': self.fail_message,
                'status_code': 500
            }

        # Check if schedule exists
        if schedule_id in self.scheduled_events:
            event_data = self.scheduled_events.pop(schedule_id)
            self.logger.info(f"Mock: Unscheduled event {schedule_id} (mPlan: {event_data['mplan_id']})")
        else:
            self.logger.warning(f"Mock: Schedule ID {schedule_id} not found in mock data")

        return {
            'success': True,
            'message': 'Event unscheduled successfully (mock)',
            'schedule_id': schedule_id,
            'response_data': {
                'status': 'Unstaffed'
            }
        }

    # =========================================================================
    # Alias Methods for Compatibility
    # =========================================================================

    def delete_schedule(self, schedule_id: str, reason: str = None, notify_rep: bool = True) -> Dict:
        """Alias for unschedule_mplan_event"""
        return self.unschedule_mplan_event(schedule_id)

    def unschedule_event(self, schedule_id: str) -> Dict:
        """Alias for unschedule_mplan_event"""
        return self.unschedule_mplan_event(schedule_id)

    # =========================================================================
    # Health Check
    # =========================================================================

    def health_check(self) -> Dict:
        """Mock health check - always healthy"""
        return {
            'status': 'healthy',
            'message': 'Mock API is operational',
            'session_id': self.phpsessid,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'mock': True
        }

    # =========================================================================
    # Testing Utilities
    # =========================================================================

    def get_scheduled_event(self, schedule_id: str) -> Optional[Dict]:
        """Get a scheduled event from mock storage"""
        return self.scheduled_events.get(schedule_id)

    def get_all_scheduled_events(self) -> Dict:
        """Get all scheduled events from mock storage"""
        return self.scheduled_events.copy()

    def reset(self):
        """Reset mock API to initial state"""
        self.call_log = []
        self.scheduled_events = {}
        self.next_schedule_id = 10000
        self.should_fail = False
        self.fail_on_next_call = False
        self.authenticated = True
        self.logger.info("Mock API reset")

    def __repr__(self):
        return f"<MockCrossmarkAPI calls={len(self.call_log)} scheduled={len(self.scheduled_events)}>"


# ============================================================================
# Testing Helper Functions
# ============================================================================

def enable_mock_api(app):
    """
    Enable mock API for testing.

    Usage in tests:
        from scheduler_app.tests.mock_crossmark_api import enable_mock_api

        def setUp(self):
            self.app = create_app('testing')
            self.mock_api = enable_mock_api(self.app)
            self.client = self.app.test_client()
    """
    from scheduler_app import session_api_service

    mock_api = MockCrossmarkAPI()

    # Replace the global session_api instance
    session_api_service.session_api = mock_api

    # Also patch it in the app config for easy access
    app.config['MOCK_API'] = mock_api
    app.config['USE_MOCK_API'] = True

    return mock_api


def assert_api_called(mock_api: MockCrossmarkAPI, method: str, times: int = None):
    """
    Assert that a mock API method was called.

    Args:
        mock_api: The MockCrossmarkAPI instance
        method: The method name (e.g., 'schedule_mplan_event')
        times: Expected number of calls (None = at least once)

    Example:
        assert_api_called(mock_api, 'schedule_mplan_event', times=2)
    """
    calls = mock_api.get_calls_for_method(method)

    if times is None:
        assert len(calls) > 0, f"Expected {method} to be called at least once, but it was not called"
    else:
        assert len(calls) == times, f"Expected {method} to be called {times} time(s), but it was called {len(calls)} time(s)"


def assert_api_not_called(mock_api: MockCrossmarkAPI, method: str):
    """
    Assert that a mock API method was NOT called.

    Args:
        mock_api: The MockCrossmarkAPI instance
        method: The method name

    Example:
        assert_api_not_called(mock_api, 'unschedule_mplan_event')
    """
    calls = mock_api.get_calls_for_method(method)
    assert len(calls) == 0, f"Expected {method} to not be called, but it was called {len(calls)} time(s)"


def get_api_call_args(mock_api: MockCrossmarkAPI, method: str, call_index: int = 0) -> Dict:
    """
    Get the arguments from a specific API call.

    Args:
        mock_api: The MockCrossmarkAPI instance
        method: The method name
        call_index: Which call to get (0 = first call)

    Returns:
        dict: The arguments passed to that call

    Example:
        args = get_api_call_args(mock_api, 'schedule_mplan_event', 0)
        assert args['rep_id'] == '101'
    """
    calls = mock_api.get_calls_for_method(method)
    assert len(calls) > call_index, f"Expected at least {call_index + 1} call(s) to {method}, but only {len(calls)} found"

    # Remove 'method' and 'timestamp' from the returned dict
    call_args = calls[call_index].copy()
    call_args.pop('method', None)
    call_args.pop('timestamp', None)

    return call_args


# ============================================================================
# Example Usage in Tests
# ============================================================================

"""
Example test using mock API:

import unittest
from scheduler_app import create_app
from scheduler_app.tests.mock_crossmark_api import enable_mock_api, assert_api_called, get_api_call_args


class TestCORESupervisorPairing(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.mock_api = enable_mock_api(self.app)
        self.client = self.app.test_client()

        # Load test data
        with open('test_data/sprint1_adapted_testdata.sql') as f:
            # Execute SQL...
            pass

    def tearDown(self):
        self.mock_api.reset()

    def test_reschedule_core_event_with_supervisor(self):
        '''Test that rescheduling CORE event also reschedules Supervisor'''

        # Arrange: CORE event 606001 and Supervisor 606001 both scheduled on 2025-10-15

        # Act: Reschedule CORE event to 2025-10-20
        response = self.client.post('/api/reschedule', json={
            'schedule_id': 2001,  # CORE event schedule
            'new_date': '2025-10-20',
            'new_time': '10:00',
            'employee_id': 101
        })

        # Assert: Both API calls were made
        assert_api_called(self.mock_api, 'schedule_mplan_event', times=2)

        # Get the second call (Supervisor)
        supervisor_call = get_api_call_args(self.mock_api, 'schedule_mplan_event', 1)
        assert '606001-Supervisor' in supervisor_call['mplan_id']
        assert '2025-10-20' in supervisor_call['start_datetime']

        # Assert: Both local database records updated
        # ... database assertions ...

    def test_api_failure_rolls_back_transaction(self):
        '''Test that transaction rolls back if API fails'''

        # Arrange: Configure mock to fail on second call (Supervisor)
        self.mock_api.set_should_fail(True, "Network error")

        # Act: Attempt to reschedule CORE event
        response = self.client.post('/api/reschedule', json={
            'schedule_id': 2001,
            'new_date': '2025-10-20',
            'new_time': '10:00',
            'employee_id': 101
        })

        # Assert: Transaction rolled back, both events still on original date
        # ... database assertions ...
"""
