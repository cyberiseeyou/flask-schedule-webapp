"""
Unit Tests for EDR Service
===========================

Tests for the EDRService class to verify:
- Authentication flow
- Session management
- EDR data retrieval
- PDF generation orchestration
- Error handling
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, date, timedelta
import tempfile
import os

# Import the service module
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scheduler_app'))

from scheduler_app.services.edr_service import EDRService, get_edr_service
from scheduler_app.utils.event_helpers import extract_event_number, validate_event_number


class TestEDRService(unittest.TestCase):
    """Test cases for EDRService"""

    def setUp(self):
        """Set up test fixtures"""
        self.service = EDRService()

        # Mock session
        self.mock_session = {}

        # Patch session
        self.session_patcher = patch('scheduler_app.services.edr_service.session', self.mock_session)
        self.session_patcher.start()

        # Patch environment variables
        self.env_patcher = patch.dict(os.environ, {
            'WALMART_USERNAME': 'test@example.com',
            'WALMART_PASSWORD': 'testpass',
            'WALMART_MFA_PHONE': '1234567890'
        })
        self.env_patcher.start()

    def tearDown(self):
        """Clean up after tests"""
        self.session_patcher.stop()
        self.env_patcher.stop()

    def test_initialization(self):
        """Test service initialization"""
        service = EDRService()
        self.assertIsNotNone(service)
        self.assertIsNotNone(service.logger)

    @patch('scheduler_app.services.edr_service.EDRReportGenerator')
    def test_initialize_edr_authenticator(self, mock_generator_class):
        """Test EDR authenticator initialization"""
        mock_auth = Mock()
        mock_generator_class.return_value = mock_auth

        auth = self.service.initialize_edr_authenticator()

        # Verify credentials were set
        self.assertEqual(auth.username, 'test@example.com')
        self.assertEqual(auth.password, 'testpass')
        self.assertEqual(auth.mfa_credential_id, '1234567890')

    @patch('scheduler_app.services.edr_service.EDRReportGenerator')
    def test_request_mfa_code_success(self, mock_generator_class):
        """Test successful MFA code request"""
        # Setup mocks
        mock_auth = Mock()
        mock_auth.step1_submit_password.return_value = True
        mock_auth.step2_request_mfa_code.return_value = True
        mock_auth.session.cookies = {'cookie1': 'value1'}
        mock_generator_class.return_value = mock_auth

        # Execute
        result = self.service.request_mfa_code()

        # Verify
        self.assertTrue(result)
        self.assertTrue(self.mock_session.get('edr_auth_pending'))
        self.assertIn('edr_auth_session', self.mock_session)

    @patch('scheduler_app.services.edr_service.EDRReportGenerator')
    def test_request_mfa_code_password_failure(self, mock_generator_class):
        """Test MFA request failure at password step"""
        # Setup mocks
        mock_auth = Mock()
        mock_auth.step1_submit_password.return_value = False
        mock_generator_class.return_value = mock_auth

        # Execute
        result = self.service.request_mfa_code()

        # Verify
        self.assertFalse(result)

    @patch('scheduler_app.services.edr_service.EDRReportGenerator')
    def test_complete_authentication_success(self, mock_generator_class):
        """Test successful authentication completion"""
        # Setup session with pending auth
        self.mock_session['edr_auth_pending'] = True
        self.mock_session['edr_auth_session'] = {
            'cookies': {'cookie1': 'value1'},
            'username': 'test@example.com',
            'password': 'testpass',
            'mfa_credential_id': '1234567890'
        }

        # Setup mocks
        mock_auth = Mock()
        mock_auth.step3_validate_mfa_code.return_value = True
        mock_auth.step4_register_page_access.return_value = True
        mock_auth.step5_navigate_to_event_management.return_value = True
        mock_auth.step6_authenticate_event_management.return_value = True
        mock_auth.auth_token = 'test_token_12345'
        mock_auth.session.cookies = {'cookie1': 'value1', 'auth': 'token'}
        mock_generator_class.return_value = mock_auth

        # Execute
        result = self.service.complete_authentication('123456')

        # Verify
        self.assertTrue(result)
        self.assertTrue(self.mock_session.get('edr_authenticated'))
        self.assertEqual(self.mock_session.get('edr_auth_token'), 'test_token_12345')
        self.assertNotIn('edr_auth_pending', self.mock_session)

    @patch('scheduler_app.services.edr_service.EDRReportGenerator')
    def test_complete_authentication_no_pending(self, mock_generator_class):
        """Test authentication completion without pending auth"""
        result = self.service.complete_authentication('123456')

        # Should fail if no pending auth
        self.assertFalse(result)

    @patch('scheduler_app.services.edr_service.EDRReportGenerator')
    def test_get_authenticated_client_success(self, mock_generator_class):
        """Test getting authenticated client from session"""
        # Setup authenticated session
        self.mock_session['edr_authenticated'] = True
        self.mock_session['edr_auth_session'] = {
            'auth_token': 'test_token',
            'cookies': {'auth': 'token'},
            'username': 'test@example.com',
            'password': 'testpass',
            'mfa_credential_id': '1234567890'
        }

        # Setup mock
        mock_auth = Mock()
        mock_auth.session.cookies = {}
        mock_generator_class.return_value = mock_auth

        # Execute
        client = self.service.get_authenticated_client()

        # Verify
        self.assertIsNotNone(client)
        self.assertEqual(client.auth_token, 'test_token')

    def test_get_authenticated_client_not_authenticated(self):
        """Test getting client when not authenticated"""
        client = self.service.get_authenticated_client()

        # Should return None
        self.assertIsNone(client)

    def test_is_authenticated(self):
        """Test authentication status check"""
        # Initially not authenticated
        self.assertFalse(self.service.is_authenticated())

        # After setting authenticated flag
        self.mock_session['edr_authenticated'] = True
        self.assertTrue(self.service.is_authenticated())

    def test_clear_authentication(self):
        """Test clearing authentication"""
        # Setup authenticated session
        self.mock_session['edr_authenticated'] = True
        self.mock_session['edr_auth_token'] = 'token'
        self.mock_session['edr_auth_session'] = {}

        # Clear
        self.service.clear_authentication()

        # Verify all auth data removed
        self.assertNotIn('edr_authenticated', self.mock_session)
        self.assertNotIn('edr_auth_token', self.mock_session)
        self.assertNotIn('edr_auth_session', self.mock_session)

    @patch('scheduler_app.services.edr_service.db')
    def test_get_events_for_date(self, mock_db):
        """Test retrieving events for a specific date"""
        # Create mock query result
        mock_schedule = Mock()
        mock_event = Mock()
        mock_event.event_type = 'Core'
        mock_employee = Mock()

        mock_query = Mock()
        mock_query.query.return_value.join.return_value.join.return_value.filter.return_value.order_by.return_value.all.return_value = [
            (mock_schedule, mock_event, mock_employee)
        ]
        mock_db.session = mock_query

        # Execute
        result = self.service.get_events_for_date('2025-10-05')

        # Verify
        self.assertEqual(len(result), 1)

    def test_singleton_pattern(self):
        """Test singleton service instance"""
        service1 = get_edr_service()
        service2 = get_edr_service()

        # Should be same instance
        self.assertIs(service1, service2)


class TestEventHelpers(unittest.TestCase):
    """Test event helper functions"""

    def test_extract_event_number_standard_format(self):
        """Test extracting event number from standard format"""
        result = extract_event_number('606034-JJSF-Super Pretzel')
        self.assertEqual(result, '606034')

    def test_extract_event_number_no_number(self):
        """Test extraction when no event number present"""
        result = extract_event_number('No Event Number Here')
        self.assertIsNone(result)

    def test_extract_event_number_middle_of_string(self):
        """Test extraction when number is in middle"""
        result = extract_event_number('Event 123456 Sample')
        self.assertEqual(result, '123456')

    def test_validate_event_number_valid(self):
        """Test validation of valid event number"""
        self.assertTrue(validate_event_number('123456'))
        self.assertTrue(validate_event_number('606034'))

    def test_validate_event_number_invalid(self):
        """Test validation of invalid event numbers"""
        self.assertFalse(validate_event_number('12345'))  # Too short
        self.assertFalse(validate_event_number('1234567'))  # Too long
        self.assertFalse(validate_event_number('abc123'))  # Contains letters
        self.assertFalse(validate_event_number(''))  # Empty
        self.assertFalse(validate_event_number(None))  # None


class TestEDRServiceIntegration(unittest.TestCase):
    """Integration tests for EDR service"""

    def setUp(self):
        """Set up integration test fixtures"""
        self.service = EDRService()

    @patch('scheduler_app.services.edr_service.session')
    @patch('scheduler_app.services.edr_service.EDRReportGenerator')
    @patch('scheduler_app.services.edr_service.EDRPDFGenerator')
    def test_generate_single_edr_pdf_success(self, mock_pdf_gen_class, mock_auth_class, mock_session):
        """Test successful single EDR PDF generation"""
        # Setup authenticated session
        mock_session.__getitem__.side_effect = lambda key: {
            'edr_authenticated': True,
            'edr_auth_session': {
                'auth_token': 'test_token',
                'cookies': {},
                'username': 'test@example.com',
                'password': 'testpass',
                'mfa_credential_id': '1234567890'
            }
        }.get(key)
        mock_session.get.side_effect = lambda key, default=None: {
            'edr_authenticated': True,
            'edr_auth_session': {
                'auth_token': 'test_token',
                'cookies': {},
                'username': 'test@example.com',
                'password': 'testpass',
                'mfa_credential_id': '1234567890'
            }
        }.get(key, default)

        # Setup mock authenticator
        mock_auth = Mock()
        mock_auth.auth_token = 'test_token'
        mock_auth.session.cookies = {}
        mock_auth.get_edr_report.return_value = {
            'demoId': '606034',
            'demoName': 'Test Event',
            'demoDate': '2025-10-05',
            'demoClassCode': '3',
            'demoStatusCode': '2',
            'demoLockInd': 'Y',
            'itemDetails': []
        }
        mock_auth_class.return_value = mock_auth

        # Setup mock PDF generator
        mock_pdf_gen = Mock()
        mock_pdf_gen.generate_pdf.return_value = True
        mock_pdf_gen_class.return_value = mock_pdf_gen

        # Patch environment variables
        with patch.dict(os.environ, {
            'WALMART_USERNAME': 'test@example.com',
            'WALMART_PASSWORD': 'testpass',
            'WALMART_MFA_PHONE': '1234567890'
        }):
            # Execute
            result = self.service.generate_single_edr_pdf('606034', 'John Doe')

        # Verify
        self.assertIsNotNone(result)
        self.assertIsInstance(result, bytes)


if __name__ == '__main__':
    unittest.main()
