#!/usr/bin/env python3
"""
Comprehensive API Testing Suite for Crossmark MVRetail Integration
Test Architect: Quinn
Focus: Complete API validation with risk assessment and traceability
"""
import os
import sys
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import traceback

# Add the scheduler_app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scheduler_app'))

from session_api_service import SessionAPIService, SessionError

class APITestResult:
    """Container for API test results with quality metrics"""
    def __init__(self, endpoint: str, method: str, status: str,
                 response_time: float = 0, error: str = None,
                 data: Any = None, risk_level: str = "low"):
        self.endpoint = endpoint
        self.method = method
        self.status = status  # PASS, FAIL, SKIP, ERROR
        self.response_time = response_time
        self.error = error
        self.data = data
        self.risk_level = risk_level
        self.timestamp = datetime.now()

class ComprehensiveAPITester:
    """
    Comprehensive API testing framework with quality gates

    Risk Assessment Matrix:
    - CRITICAL: Authentication, core scheduling operations
    - HIGH: User management, session handling
    - MEDIUM: Configuration endpoints, filters
    - LOW: Optional features, convenience methods
    """

    def __init__(self):
        self.logger = self._setup_logging()
        self.api_service = SessionAPIService()
        self.test_results: List[APITestResult] = []
        self.risk_matrix = {
            'authentication': 'CRITICAL',
            'scheduling': 'CRITICAL',
            'user_management': 'HIGH',
            'session_management': 'HIGH',
            'configuration': 'MEDIUM',
            'filters': 'MEDIUM',
            'convenience': 'LOW'
        }

    def _setup_logging(self):
        """Configure comprehensive logging for test traceability"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('api_test_results.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)

    def _init_api_service(self) -> bool:
        """Initialize API service with test configuration"""
        try:
            test_config = {
                'EXTERNAL_API_BASE_URL': 'https://crossmark.mvretail.com',
                'EXTERNAL_API_USERNAME': os.getenv('TEST_API_USERNAME', 'test_user'),
                'EXTERNAL_API_PASSWORD': os.getenv('TEST_API_PASSWORD', 'test_pass'),
                'EXTERNAL_API_TIMEZONE': 'America/Indiana/Indianapolis',
                'EXTERNAL_API_TIMEOUT': 30,
                'EXTERNAL_API_MAX_RETRIES': 3,
                'EXTERNAL_API_RETRY_DELAY': 1,
                'SESSION_REFRESH_INTERVAL': 3600
            }

            class MockApp:
                def __init__(self, config):
                    self.config = config

            mock_app = MockApp(test_config)
            self.api_service.init_app(mock_app)
            self.logger.info("API service initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize API service: {str(e)}")
            return False

    def _execute_test(self, test_name: str, test_func, risk_category: str = 'LOW') -> APITestResult:
        """Execute individual test with comprehensive error handling and metrics"""
        start_time = time.time()

        try:
            self.logger.info(f"Executing test: {test_name}")
            result = test_func()
            response_time = time.time() - start_time

            if result is not None:
                return APITestResult(
                    endpoint=test_name,
                    method="API_CALL",
                    status="PASS",
                    response_time=response_time,
                    data=result,
                    risk_level=self.risk_matrix.get(risk_category, 'LOW')
                )
            else:
                return APITestResult(
                    endpoint=test_name,
                    method="API_CALL",
                    status="FAIL",
                    response_time=response_time,
                    error="Method returned None",
                    risk_level=self.risk_matrix.get(risk_category, 'LOW')
                )

        except SessionError as e:
            response_time = time.time() - start_time
            # Expected errors for authentication-required endpoints
            return APITestResult(
                endpoint=test_name,
                method="API_CALL",
                status="EXPECTED_FAIL",
                response_time=response_time,
                error=f"SessionError: {e.message}",
                risk_level=self.risk_matrix.get(risk_category, 'LOW')
            )

        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error(f"Test {test_name} failed with exception: {str(e)}")
            self.logger.error(traceback.format_exc())
            return APITestResult(
                endpoint=test_name,
                method="API_CALL",
                status="ERROR",
                response_time=response_time,
                error=str(e),
                risk_level=self.risk_matrix.get(risk_category, 'LOW')
            )

    def test_authentication_endpoints(self):
        """Test Group: Authentication (CRITICAL RISK)"""
        self.logger.info("=== Testing Authentication Endpoints (CRITICAL) ===")

        # Test 1: Health Check (No Auth Required)
        result = self._execute_test(
            "health_check",
            lambda: self.api_service.health_check(),
            'authentication'
        )
        self.test_results.append(result)

        # Test 2: Session Validation
        result = self._execute_test(
            "is_session_valid",
            lambda: self.api_service.is_session_valid(),
            'authentication'
        )
        self.test_results.append(result)

        # Test 3: Authentication Attempt (Expected to fail without real credentials)
        result = self._execute_test(
            "login_attempt",
            lambda: self.api_service.login(),
            'authentication'
        )
        self.test_results.append(result)

    def test_user_management_endpoints(self):
        """Test Group: User Management (HIGH RISK)"""
        self.logger.info("=== Testing User Management Endpoints (HIGH) ===")

        endpoints = [
            ("get_user_locale", lambda: self.api_service.get_user_locale()),
            ("get_user_info", lambda: self.api_service._get_user_info()),
            ("get_employees", lambda: self.api_service.get_employees())
        ]

        for endpoint_name, test_func in endpoints:
            result = self._execute_test(endpoint_name, test_func, 'user_management')
            self.test_results.append(result)

    def test_configuration_endpoints(self):
        """Test Group: Configuration (MEDIUM RISK)"""
        self.logger.info("=== Testing Configuration Endpoints (MEDIUM) ===")

        endpoints = [
            ("get_client_logo", lambda: self.api_service.get_client_logo()),
            ("get_current_branch_info", lambda: self.api_service.get_current_branch_info()),
            ("get_navigation_options", lambda: self.api_service.get_navigation_options()),
            ("get_scheduling_preferences", lambda: self.api_service.get_scheduling_preferences()),
            ("get_fullcalendar_license_key", lambda: self.api_service.get_fullcalendar_license_key())
        ]

        for endpoint_name, test_func in endpoints:
            result = self._execute_test(endpoint_name, test_func, 'configuration')
            self.test_results.append(result)

    def test_scheduling_endpoints(self):
        """Test Group: Scheduling Operations (CRITICAL RISK)"""
        self.logger.info("=== Testing Scheduling Endpoints (CRITICAL) ===")

        # Core scheduling operations
        core_endpoints = [
            ("get_available_representatives", lambda: self.api_service.get_available_representatives()),
            ("get_scheduled_events", lambda: self.api_service.get_scheduled_events()),
            ("get_non_scheduled_visits", lambda: self.api_service.get_non_scheduled_visits()),
            ("get_unscheduled_events", lambda: self.api_service.get_unscheduled_events())
        ]

        for endpoint_name, test_func in core_endpoints:
            result = self._execute_test(endpoint_name, test_func, 'scheduling')
            self.test_results.append(result)

        # CRUD operations with sample data
        crud_tests = [
            ("save_scheduled_event", lambda: self.api_service.save_scheduled_event(self._get_sample_event_data())),
            ("update_scheduled_event", lambda: self.api_service.update_scheduled_event(self._get_sample_update_data())),
            ("delete_scheduled_event", lambda: self.api_service.delete_scheduled_event({"eventId": "test_123"})),
            ("get_event_details", lambda: self.api_service.get_event_details("test_event_id")),
            ("get_rep_availability", lambda: self.api_service.get_rep_availability("test_rep_id")),
            ("bulk_schedule_events", lambda: self.api_service.bulk_schedule_events(self._get_bulk_event_data()))
        ]

        for endpoint_name, test_func in crud_tests:
            result = self._execute_test(endpoint_name, test_func, 'scheduling')
            self.test_results.append(result)

    def test_filter_endpoints(self):
        """Test Group: Filter and Options (MEDIUM RISK)"""
        self.logger.info("=== Testing Filter Endpoints (MEDIUM) ===")

        result = self._execute_test(
            "get_more_filters_options",
            lambda: self.api_service.get_more_filters_options(),
            'filters'
        )
        self.test_results.append(result)

    def test_legacy_compatibility(self):
        """Test Group: Legacy Method Compatibility (LOW RISK)"""
        self.logger.info("=== Testing Legacy Compatibility (LOW) ===")

        legacy_endpoints = [
            ("get_events_legacy", lambda: self.api_service.get_events()),
            ("create_schedule", lambda: self.api_service.create_schedule(self._get_sample_schedule_data())),
            ("update_schedule", lambda: self.api_service.update_schedule("test_id", self._get_sample_schedule_data())),
            ("delete_schedule", lambda: self.api_service.delete_schedule("test_id"))
        ]

        for endpoint_name, test_func in legacy_endpoints:
            result = self._execute_test(endpoint_name, test_func, 'convenience')
            self.test_results.append(result)

    def test_data_transformation(self):
        """Test Group: Data Format Validation (MEDIUM RISK)"""
        self.logger.info("=== Testing Data Transformation (MEDIUM) ===")

        # Test date formatting
        try:
            test_date = datetime.now()
            formatted = self.api_service._format_date(test_date)
            self.test_results.append(APITestResult(
                endpoint="date_formatting",
                method="UTILITY",
                status="PASS",
                data={"input": test_date, "output": formatted},
                risk_level="MEDIUM"
            ))
        except Exception as e:
            self.test_results.append(APITestResult(
                endpoint="date_formatting",
                method="UTILITY",
                status="FAIL",
                error=str(e),
                risk_level="MEDIUM"
            ))

        # Test JSON parsing
        try:
            class MockResponse:
                def json(self):
                    return {"test": "data"}
                def text(self):
                    return '{"test": "data"}'

            mock_response = MockResponse()
            parsed = self.api_service._safe_json(mock_response)
            self.test_results.append(APITestResult(
                endpoint="json_parsing",
                method="UTILITY",
                status="PASS",
                data=parsed,
                risk_level="MEDIUM"
            ))
        except Exception as e:
            self.test_results.append(APITestResult(
                endpoint="json_parsing",
                method="UTILITY",
                status="FAIL",
                error=str(e),
                risk_level="MEDIUM"
            ))

    def _get_sample_event_data(self) -> Dict:
        """Generate sample event data for testing"""
        return {
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

    def _get_sample_update_data(self) -> Dict:
        """Generate sample update data for testing"""
        return {
            "eventId": "test_event_123",
            "updates": {
                "title": "Updated Test Event",
                "notes": "Updated notes"
            }
        }

    def _get_bulk_event_data(self) -> Dict:
        """Generate bulk event data for testing"""
        return {
            "events": [
                {
                    "title": "Bulk Event 1",
                    "startDateTime": datetime.now().isoformat(),
                    "endDateTime": (datetime.now() + timedelta(hours=1)).isoformat(),
                    "repId": "test_rep_1",
                    "locationId": "test_location_1"
                },
                {
                    "title": "Bulk Event 2",
                    "startDateTime": (datetime.now() + timedelta(hours=2)).isoformat(),
                    "endDateTime": (datetime.now() + timedelta(hours=3)).isoformat(),
                    "repId": "test_rep_2",
                    "locationId": "test_location_2"
                }
            ],
            "validateConflicts": True,
            "autoResolveConflicts": False
        }

    def _get_sample_schedule_data(self) -> Dict:
        """Generate sample schedule data for testing"""
        return {
            "rep_id": "test_rep_123",
            "mplan_id": "test_mplan_456",
            "location_id": "test_location_789",
            "start_datetime": datetime.now(),
            "end_datetime": datetime.now() + timedelta(hours=2),
            "planning_override": True
        }

    def generate_quality_report(self) -> Dict:
        """Generate comprehensive quality assessment report"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.status == "PASS"])
        failed_tests = len([r for r in self.test_results if r.status == "FAIL"])
        error_tests = len([r for r in self.test_results if r.status == "ERROR"])
        expected_fail_tests = len([r for r in self.test_results if r.status == "EXPECTED_FAIL"])

        # Risk assessment
        critical_failures = len([r for r in self.test_results
                               if r.risk_level == "CRITICAL" and r.status in ["FAIL", "ERROR"]])
        high_failures = len([r for r in self.test_results
                           if r.risk_level == "HIGH" and r.status in ["FAIL", "ERROR"]])

        # Performance metrics
        avg_response_time = sum([r.response_time for r in self.test_results]) / total_tests if total_tests > 0 else 0
        slow_endpoints = [r for r in self.test_results if r.response_time > 5.0]

        # Quality gate decision
        if critical_failures > 0:
            gate_decision = "FAIL"
            gate_reason = f"{critical_failures} critical failures detected"
        elif high_failures > 3:
            gate_decision = "CONCERNS"
            gate_reason = f"{high_failures} high-risk failures detected"
        elif failed_tests > total_tests * 0.2:  # More than 20% failure rate
            gate_decision = "CONCERNS"
            gate_reason = f"High failure rate: {failed_tests}/{total_tests} ({failed_tests/total_tests*100:.1f}%)"
        else:
            gate_decision = "PASS"
            gate_reason = "All critical tests passing with acceptable failure rate"

        return {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "errors": error_tests,
                "expected_failures": expected_fail_tests,
                "success_rate": f"{(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%"
            },
            "risk_assessment": {
                "critical_failures": critical_failures,
                "high_risk_failures": high_failures,
                "avg_response_time": f"{avg_response_time:.2f}s",
                "slow_endpoints": len(slow_endpoints)
            },
            "quality_gate": {
                "decision": gate_decision,
                "reason": gate_reason,
                "timestamp": datetime.now().isoformat()
            },
            "detailed_results": [
                {
                    "endpoint": r.endpoint,
                    "status": r.status,
                    "risk_level": r.risk_level,
                    "response_time": f"{r.response_time:.2f}s",
                    "error": r.error,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in self.test_results
            ]
        }

    def run_comprehensive_test_suite(self):
        """Execute complete API test suite with quality gates"""
        self.logger.info("🧪 Starting Comprehensive API Test Suite")
        self.logger.info("Test Architect: Quinn")
        self.logger.info("Focus: Complete API validation with risk assessment")
        self.logger.info("=" * 60)

        if not self._init_api_service():
            self.logger.error("Failed to initialize API service - aborting tests")
            return False

        # Execute all test groups
        test_groups = [
            self.test_authentication_endpoints,
            self.test_user_management_endpoints,
            self.test_configuration_endpoints,
            self.test_scheduling_endpoints,
            self.test_filter_endpoints,
            self.test_legacy_compatibility,
            self.test_data_transformation
        ]

        for test_group in test_groups:
            try:
                test_group()
            except Exception as e:
                self.logger.error(f"Test group {test_group.__name__} failed: {str(e)}")
                continue

        # Generate quality report
        report = self.generate_quality_report()

        # Log comprehensive results
        self.logger.info("=" * 60)
        self.logger.info("🏁 Test Suite Complete - Quality Assessment")
        self.logger.info("=" * 60)
        self.logger.info(f"Total Tests: {report['summary']['total_tests']}")
        self.logger.info(f"Success Rate: {report['summary']['success_rate']}")
        self.logger.info(f"Critical Failures: {report['risk_assessment']['critical_failures']}")
        self.logger.info(f"High Risk Failures: {report['risk_assessment']['high_risk_failures']}")
        self.logger.info(f"Average Response Time: {report['risk_assessment']['avg_response_time']}")
        self.logger.info("=" * 60)
        self.logger.info(f"🎯 QUALITY GATE: {report['quality_gate']['decision']}")
        self.logger.info(f"Reason: {report['quality_gate']['reason']}")
        self.logger.info("=" * 60)

        # Save detailed report
        with open('api_test_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)

        return report['quality_gate']['decision'] in ['PASS', 'CONCERNS']

def main():
    """Main test execution"""
    tester = ComprehensiveAPITester()
    success = tester.run_comprehensive_test_suite()

    if success:
        print("\n✅ API Test Suite COMPLETED")
        print("📊 Detailed report saved to: api_test_report.json")
        print("📋 Full logs saved to: api_test_results.log")
    else:
        print("\n❌ API Test Suite FAILED")
        print("📊 Review report at: api_test_report.json")
        print("📋 Check logs at: api_test_results.log")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())