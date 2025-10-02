"""
Session-based API service for external system integration
Handles PHP session authentication with PHPSESSID cookie management
"""
import requests
import logging
import time
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from flask import current_app
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class SessionError(Exception):
    """Custom exception for session-related errors"""
    def __init__(self, message: str, response=None):
        self.message = message
        self.response = response
        super().__init__(self.message)


class SessionAPIService:
    """Service class for Crossmark API integration"""

    def __init__(self, app=None):
        self.app = app
        self.logger = logging.getLogger(__name__)
        self.session = None
        self.last_login = None
        self.authenticated = False
        self.user_info = None
        self.phpsessid = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the API service with Flask app"""
        self.app = app
        self.base_url = app.config.get('EXTERNAL_API_BASE_URL', 'https://crossmark.mvretail.com')
        self.username = app.config.get('EXTERNAL_API_USERNAME', '')
        self.password = app.config.get('EXTERNAL_API_PASSWORD', '')
        self.timezone = app.config.get('EXTERNAL_API_TIMEZONE', 'America/Indiana/Indianapolis')
        self.timeout = app.config.get('EXTERNAL_API_TIMEOUT', 30)
        self.max_retries = app.config.get('EXTERNAL_API_MAX_RETRIES', 3)
        self.retry_delay = app.config.get('EXTERNAL_API_RETRY_DELAY', 1)
        self.session_refresh_interval = app.config.get('SESSION_REFRESH_INTERVAL', 3600)

        # Initialize session with retry strategy
        self._setup_session()

    def _setup_session(self):
        """Setup requests session with retry strategy and cookie persistence"""
        self.session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
            backoff_factor=1
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set common headers (matching Crossmark requirements)
        self.session.headers.update({
            "accept": "application/json",
            "user-agent": "flask-scheduler-crossmark/1.0 (+requests)",
        })

    def login(self) -> bool:
        """
        Authenticate with the Crossmark API using provided credentials.
        Returns True if authentication successful, False otherwise
        """
        if not all([self.base_url, self.username, self.password]):
            self.logger.warning("Login credentials not configured")
            return False

        auth_url = f"{self.base_url}/login/authenticate"

        # Prepare authentication data (matching actual curl command format)
        auth_data = {
            "UserType": "MVEntityUser",
            "UserID": self.username,
            "Password": self.password,
            "Timezone": "America/Indianapolis"
        }

        # Set headers according to actual curl command
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/login",
            "Sec-CH-UA": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
        }

        try:
            # Set flag to bypass authentication check during authentication
            self._authenticating = True

            # Debug logging
            self.logger.info(f"Authentication URL: {auth_url}")
            self.logger.info(f"Authentication headers: {headers}")
            self.logger.info(f"Authentication data: {auth_data}")

            response = self.session.post(auth_url, json=auth_data, headers=headers, timeout=self.timeout)

            if response.status_code == 200:
                # Parse authentication response according to HAR file analysis
                content_type = response.headers.get('content-type', '').lower()

                # Check if response is HTML (indicates successful authentication per HAR file)
                if 'text/html' in content_type and 'Scheduling' in response.text:
                    self.authenticated = True
                    self.last_login = datetime.utcnow()
                    self.logger.info("Successfully authenticated user: %s (HTML response with Scheduling page)", self.username)
                else:
                    # Try to parse as JSON for other response types
                    try:
                        auth_response = response.json()

                        # Check for redirect URL (indicates successful authentication)
                        if 'redirectUrl' in auth_response:
                            self.authenticated = True
                            self.last_login = datetime.utcnow()
                            self.logger.info("Successfully authenticated user: %s (redirect: %s)", self.username, auth_response['redirectUrl'])
                        elif auth_response.get('success', False):
                            self.authenticated = True
                            self.last_login = datetime.utcnow()

                            # Extract session info from response
                            session_id = auth_response.get('sessionId')
                            user_id = auth_response.get('userId')

                            self.logger.info("Successfully authenticated user: %s (session: %s)", user_id or self.username, session_id or 'N/A')
                        else:
                            self.logger.warning("Authentication failed: %s", auth_response)
                            return False
                    except ValueError:
                        # Non-JSON response - treat as successful if we got here
                        self.authenticated = True
                        self.last_login = datetime.utcnow()
                        self.logger.info("Authentication successful (non-JSON response)")

                # Extract PHPSESSID from cookies
                self.phpsessid = response.cookies.get('PHPSESSID')
                if not self.phpsessid:
                    # Try to get from session cookies
                    self.phpsessid = self.session.cookies.get('PHPSESSID')

                if self.phpsessid:
                    self.logger.info("PHPSESSID obtained: %s...", self.phpsessid[:8])

                # Get user info after successful authentication
                self.user_info = self._get_user_info()
                return True
            elif response.status_code == 401:
                self.logger.warning("Authentication failed: Invalid credentials")
                return False
            else:
                self.logger.warning(
                    "Authentication failed: %s %s",
                    response.status_code,
                    response.text[:300],
                )
                return False

        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            return False
        finally:
            # Clear the flag
            self._authenticating = False

    def is_session_valid(self) -> bool:
        """Check if current session is still valid"""
        if not self.authenticated or not self.last_login:
            return False

        # Check if session has expired
        session_age = (datetime.utcnow() - self.last_login).total_seconds()
        if session_age > self.session_refresh_interval:
            self.logger.info("Session expired, need to re-login")
            self.authenticated = False
            self.phpsessid = None
            return False

        return True

    def ensure_authenticated(self) -> bool:
        """Ensure we have a valid authenticated session"""
        if self.is_session_valid():
            return True

        self.logger.info("Session invalid, attempting login...")
        return self.login()

    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make authenticated request with automatic session management
        """
        if not self.ensure_authenticated():
            raise SessionError("Failed to authenticate session")

        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        # Ensure PHPSESSID cookie is set
        if self.phpsessid:
            self.session.cookies.set('PHPSESSID', self.phpsessid)

        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )

            # Log the request
            self.logger.info(f"{method} {url} - Status: {response.status_code}")

            # Check if session expired (common indicators)
            if (response.status_code == 401 or
                response.status_code == 403 or
                'login' in response.url.lower() or
                'authentication' in response.text.lower()):

                self.logger.warning("Session appears to have expired, attempting re-login")
                if self.login() and self.phpsessid:
                    self.session.cookies.set('PHPSESSID', self.phpsessid)
                    # Retry the request
                    response = self.session.request(
                        method=method,
                        url=url,
                        timeout=self.timeout,
                        **kwargs
                    )

            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {method} {url} - {str(e)}")
            raise SessionError(f"Request failed: {str(e)}", response=getattr(e, 'response', None))

    def request(self, method, url, *args, **kwargs):
        """
        Override the request method to ensure we're authenticated.
        """
        # Skip authentication check during the authentication process itself
        if hasattr(self, "_authenticating") and self._authenticating:
            kwargs.setdefault("timeout", self.timeout)
            return self.session.request(method, url, *args, **kwargs)

        if not self.authenticated:
            self.logger.info("Session not authenticated. Attempting to re-authenticate...")
            if not self.login():
                raise SessionError("Authentication failed")

        kwargs.setdefault("timeout", self.timeout)
        return self.session.request(method, url, *args, **kwargs)

    def _get_user_info(self) -> Optional[Dict]:
        """
        Retrieve user information after successful authentication.
        Returns dict or None: User information if successful, None otherwise
        """
        try:
            # According to API spec, both GET and POST are supported
            response = self.make_request('POST', '/users/getUserInfo')

            if 200 <= response.status_code < 300:
                user_data = self._safe_json(response)
                if user_data is None:
                    return None
                self.logger.info(
                    "Retrieved user info for: %s",
                    user_data.get("username", "Unknown User"),
                )
                return user_data
            else:
                self.logger.warning(
                    "Failed to get user info: %s %s",
                    response.status_code,
                    response.text[:300],
                )
                return None

        except Exception as e:
            self.logger.error("Error getting user info: %s", e)
            return None

    def _safe_json(self, response: requests.Response) -> Optional[Dict]:
        """Safely parse JSON response"""
        try:
            return response.json()
        except ValueError:
            self.logger.warning("Non-JSON response: %s", response.text[:300])
            return None

    def _format_date(self, value) -> str:
        """Format date for Crossmark API (MM/DD/YYYY format)"""
        if isinstance(value, datetime):
            return value.strftime("%m/%d/%Y")
        return str(value)

    def health_check(self) -> Dict:
        """Check session and API connectivity"""
        if not self.base_url:
            return {
                'status': 'disabled',
                'message': 'External API not configured'
            }

        try:
            if self.ensure_authenticated():
                return {
                    'status': 'healthy',
                    'message': 'Session authenticated successfully',
                    'session_id': self.phpsessid[:8] + '...' if self.phpsessid else 'None',
                    'last_login': self.last_login.isoformat() if self.last_login else None
                }
            else:
                return {
                    'status': 'unhealthy',
                    'message': 'Failed to authenticate session',
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Health check failed: {str(e)}'
            }

    # API Methods according to specification

    def get_user_locale(self) -> Optional[Dict]:
        """Get user locale preferences"""
        try:
            response = self.make_request('POST', '/users/getUserLocale')
            if response.status_code == 200:
                return self._safe_json(response)
            return None
        except Exception as e:
            self.logger.error(f"Error getting user locale: {str(e)}")
            return None

    def get_client_logo(self) -> Optional[Dict]:
        """Get client logo for branding"""
        try:
            response = self.make_request('POST', '/miscextcontroller/getClientLogo')
            if response.status_code == 200:
                return self._safe_json(response)
            return None
        except Exception as e:
            self.logger.error(f"Error getting client logo: {str(e)}")
            return None

    def get_current_branch_info(self) -> Optional[Dict]:
        """Get current deployment branch/environment info"""
        try:
            response = self.make_request('POST', '/miscextcontroller/getCurrentBranchInfo')
            if response.status_code == 200:
                return self._safe_json(response)
            return None
        except Exception as e:
            self.logger.error(f"Error getting branch info: {str(e)}")
            return None

    def get_navigation_options(self) -> Optional[Dict]:
        """Get navigation menu configuration"""
        try:
            response = self.make_request('POST', '/navUtils/getNavOptions')
            if response.status_code == 200:
                return self._safe_json(response)
            return None
        except Exception as e:
            self.logger.error(f"Error getting navigation options: {str(e)}")
            return None

    def get_scheduling_preferences(self) -> Optional[Dict]:
        """Get scheduling preferences and configuration"""
        try:
            response = self.make_request('POST', '/schedulingcontroller/getSchedulingPrefs')
            if response.status_code == 200:
                return self._safe_json(response)
            return None
        except Exception as e:
            self.logger.error(f"Error getting scheduling preferences: {str(e)}")
            return None

    def get_fullcalendar_license_key(self) -> Optional[Dict]:
        """Get FullCalendar license key"""
        try:
            response = self.make_request('POST', '/schedulingcontroller/getFullCalendarLicenseKey')
            if response.status_code == 200:
                return self._safe_json(response)
            return None
        except Exception as e:
            self.logger.error(f"Error getting FullCalendar license: {str(e)}")
            return None

    def get_available_representatives(self, filters: Dict = None) -> Optional[Dict]:
        """Get available representatives for scheduling"""
        try:
            data = filters or {}
            response = self.make_request('POST', '/schedulingcontroller/getAvailableReps', json=data)
            if response.status_code == 200:
                return self._safe_json(response)
            return None
        except Exception as e:
            self.logger.error(f"Error getting available representatives: {str(e)}")
            return None

    # Crossmark API specific methods

    def get_scheduled_events(self, start_date: datetime = None, end_date: datetime = None, filters: Dict = None) -> Optional[Dict]:
        """
        Get scheduled events from Crossmark API according to specification.
        Args:
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            filters: Optional filters (repId, locationId, status)
        Returns:
            dict or None: Scheduled events data if successful, None otherwise
        """
        try:
            # Prepare request body according to API spec
            request_data = {}

            if start_date:
                request_data['startDate'] = start_date.strftime('%Y-%m-%d') if isinstance(start_date, datetime) else start_date
            if end_date:
                request_data['endDate'] = end_date.strftime('%Y-%m-%d') if isinstance(end_date, datetime) else end_date

            # Add optional filters
            if filters:
                if 'repId' in filters:
                    request_data['repId'] = filters['repId']
                if 'locationId' in filters:
                    request_data['locationId'] = filters['locationId']
                if 'status' in filters:
                    request_data['status'] = filters['status']

            response = self.make_request(
                'POST',
                '/schedulingcontroller/getScheduledEvents',
                json=request_data
            )

            if response.status_code == 200:
                events_data = self._safe_json(response)
                if events_data:
                    self.logger.info("Retrieved scheduled events successfully")
                    return events_data
                return None
            else:
                self.logger.warning(
                    "Failed to get scheduled events: %s %s",
                    response.status_code,
                    response.text[:300],
                )
                return None

        except Exception as e:
            self.logger.error("Error getting scheduled events: %s", e)
            return None

    def get_unscheduled_events(self, start_date: datetime = None, end_date: datetime = None) -> Optional[Dict]:
        """
        Get unscheduled events (unstaffed mplans) from Crossmark API using the planning controller.
        Args:
            start_date: Start date (defaults to 2 weeks before today)
            end_date: End date (defaults to 6 months from today)
        Returns:
            dict or None: Unscheduled events data if successful, None otherwise
        """
        # Calculate default date range if not provided
        if start_date is None:
            start_dt = datetime.now() - timedelta(weeks=2)
            start_date = start_dt.strftime("%Y-%m-%d")
        else:
            start_date = start_date.strftime("%Y-%m-%d") if isinstance(start_date, datetime) else start_date

        if end_date is None:
            end_dt = datetime.now() + timedelta(days=180)  # 6 months out
            end_date = end_dt.strftime("%Y-%m-%d")
        else:
            end_date = end_date.strftime("%Y-%m-%d") if isinstance(end_date, datetime) else end_date

        # Prepare query parameters based on the curl command
        params = {
            '_dc': str(int(time.time() * 1000)),  # Timestamp
            'intervalStart': start_date,
            'intervalEnd': end_date,
            'showAllActive': 'false',
            'searchFields': '{"searchTerms":{"condition":{"name":"condition","title":"Conditions","items":[{"id":1,"value":["Unstaffed"],"displayValue":["Unstaffed"],"exactmatch":true,"allActive":false}]}}}',
            'searchFilter': '',
            'page': '1',
            'start': '0',
            'limit': '50',
            'sort': '[{"property":"staffedReps","direction":"ASC"}]'
        }

    def get_all_planning_events(self, start_date: datetime = None, end_date: datetime = None, limit: int = 1000) -> Optional[Dict]:
        """
        Get all planning events (all statuses) from Crossmark API for comprehensive database refresh.
        This method fetches events from 1 month before to 1 month after current date by default.
        Args:
            start_date: Start date (defaults to 1 month before today)
            end_date: End date (defaults to 1 month after today)
            limit: Maximum number of records to fetch (defaults to 1000)
        Returns:
            dict or None: All planning events data if successful, None otherwise
        """
        # Calculate default date range: 1 month before to 1 month after
        if start_date is None:
            start_dt = datetime.now() - timedelta(days=30)  # 1 month before
            start_date = start_dt.strftime("%Y-%m-%d")
        else:
            start_date = start_date.strftime("%Y-%m-%d") if isinstance(start_date, datetime) else start_date

        if end_date is None:
            end_dt = datetime.now() + timedelta(days=30)  # 1 month after
            end_date = end_dt.strftime("%Y-%m-%d")
        else:
            end_date = end_date.strftime("%Y-%m-%d") if isinstance(end_date, datetime) else end_date

        # Complete search fields with all statuses - based on your curl command
        search_fields = {
            "searchTerms": {
                "condition": {
                    "name": "condition",
                    "title": "Conditions",
                    "items": [{
                        "id": 11,
                        "value": ["Unstaffed", "Scheduled", "Staffed", "Canceled", "In Progress", "Paused", "Reissued", "Expired", "Submitted"],
                        "displayValue": ["Unstaffed", "Scheduled", "Staffed", "Canceled", "In Progress", "Paused", "Reissued", "Expired", "Submitted"],
                        "exactmatch": True,
                        "allActive": False
                    }]
                }
            }
        }

        # Prepare query parameters matching your curl command exactly
        params = {
            '_dc': str(int(time.time() * 1000)),  # Timestamp
            'intervalStart': start_date,
            'intervalEnd': end_date,
            'showAllActive': 'false',
            'searchFields': json.dumps(search_fields),
            'searchFilter': '',
            'page': '1',
            'start': '0',
            'limit': str(limit),
            'sort': '[{"property":"startDate","direction":"ASC"}]'
        }

        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "referer": f"{self.base_url}/planning/",
            "x-requested-with": "XMLHttpRequest"
        }

        try:
            self.logger.info(f"Fetching all planning events from {start_date} to {end_date}")
            response = self.make_request(
                'GET',
                '/planningextcontroller/getPlanningMplans',
                params=params,
                headers=headers
            )

            if 200 <= response.status_code < 300:
                events_data = self._safe_json(response)
                if events_data is None:
                    return None

                self.logger.info(
                    f"Retrieved all planning events from {start_date} to {end_date} - Total: {events_data.get('total', 0)}"
                )

                return events_data
            else:
                self.logger.warning(
                    f"Failed to get all planning events: {response.status_code} {response.text[:300]}"
                )
                return None

        except Exception as e:
            self.logger.error(f"Error getting all planning events: {str(e)}")
            return None

        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "referer": f"{self.base_url}/planning/",
            "x-requested-with": "XMLHttpRequest"
        }

        try:
            response = self.make_request(
                'GET',
                '/planningextcontroller/getPlanningMplans',
                params=params,
                headers=headers
            )

            if 200 <= response.status_code < 300:
                events_data = self._safe_json(response)
                if events_data is None:
                    return None

                self.logger.info(
                    "Retrieved unscheduled events from %s to %s", start_date, end_date
                )

                # Log the structure for debugging
                if events_data and isinstance(events_data, dict):
                    total = events_data.get('total', 0)
                    records = events_data.get('records', [])
                    self.logger.info(f"Found {total} total unscheduled events, retrieved {len(records)} records")

                return events_data
            else:
                self.logger.warning(
                    "Failed to get unscheduled events: %s %s",
                    response.status_code,
                    response.text[:300],
                )
                return None

        except Exception as e:
            self.logger.error("Error getting unscheduled events: %s", e)
            return None

    def get_all_planning_events(self, start_date: datetime = None, end_date: datetime = None, limit: int = 1000) -> Optional[Dict]:
        """
        Get all planning events (all statuses) from Crossmark API for comprehensive database refresh.
        This method fetches events from 1 month before to 1 month after current date by default.
        Args:
            start_date: Start date (defaults to 1 month before today)
            end_date: End date (defaults to 1 month after today)
            limit: Maximum number of records to fetch (defaults to 1000)
        Returns:
            dict or None: All planning events data if successful, None otherwise
        """
        # Calculate default date range: 1 month before to 1 month after
        if start_date is None:
            start_dt = datetime.now() - timedelta(days=30)  # 1 month before
            start_date = start_dt.strftime("%Y-%m-%d")
        else:
            start_date = start_date.strftime("%Y-%m-%d") if isinstance(start_date, datetime) else start_date

        if end_date is None:
            end_dt = datetime.now() + timedelta(days=30)  # 1 month after
            end_date = end_dt.strftime("%Y-%m-%d")
        else:
            end_date = end_date.strftime("%Y-%m-%d") if isinstance(end_date, datetime) else end_date

        # Complete search fields with all statuses - based on your curl command
        search_fields = {
            "searchTerms": {
                "condition": {
                    "name": "condition",
                    "title": "Conditions",
                    "items": [{
                        "id": 11,
                        "value": ["Unstaffed", "Scheduled", "Staffed", "Canceled", "In Progress", "Paused", "Reissued", "Expired", "Submitted"],
                        "displayValue": ["Unstaffed", "Scheduled", "Staffed", "Canceled", "In Progress", "Paused", "Reissued", "Expired", "Submitted"],
                        "exactmatch": True,
                        "allActive": False
                    }]
                }
            }
        }

        # Prepare query parameters matching your curl command exactly
        params = {
            '_dc': str(int(time.time() * 1000)),  # Timestamp
            'intervalStart': start_date,
            'intervalEnd': end_date,
            'showAllActive': 'false',
            'searchFields': json.dumps(search_fields),
            'searchFilter': '',
            'page': '1',
            'start': '0',
            'limit': str(limit),
            'sort': '[{"property":"startDate","direction":"ASC"}]'
        }

        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "referer": f"{self.base_url}/planning/",
            "x-requested-with": "XMLHttpRequest"
        }

        try:
            self.logger.info(f"Fetching all planning events from {start_date} to {end_date}")
            response = self.make_request(
                'GET',
                '/planningextcontroller/getPlanningMplans',
                params=params,
                headers=headers
            )

            if 200 <= response.status_code < 300:
                events_data = self._safe_json(response)
                if events_data is None:
                    return None

                self.logger.info(
                    f"Retrieved all planning events from {start_date} to {end_date} - Total: {events_data.get('total', 0)}"
                )

                return events_data
            else:
                self.logger.warning(
                    f"Failed to get all planning events: {response.status_code} {response.text[:300]}"
                )
                return None

        except Exception as e:
            self.logger.error(f"Error getting all planning events: {str(e)}")
            return None

    def get_non_scheduled_visits(self) -> Optional[Dict]:
        """Get visits that need to be scheduled according to API spec"""
        try:
            response = self.make_request('POST', '/schedulingcontroller/getNonScheduledVisits')
            if response.status_code == 200:
                return self._safe_json(response)
            return None
        except Exception as e:
            self.logger.error(f"Error getting non-scheduled visits: {str(e)}")
            return None

    def get_more_filters_options(self) -> Optional[Dict]:
        """Get additional filter options for scheduling interface"""
        try:
            response = self.make_request('POST', '/schedulingcontroller/getMoreFiltersOptions')
            if response.status_code == 200:
                return self._safe_json(response)
            return None
        except Exception as e:
            self.logger.error(f"Error getting filter options: {str(e)}")
            return None

    def save_scheduled_event(self, event_data: Dict) -> Optional[Dict]:
        """Create a new scheduled event according to API spec"""
        try:
            response = self.make_request('POST', '/schedulingcontroller/saveScheduledEvent', json=event_data)
            if response.status_code == 200:
                return self._safe_json(response)
            return None
        except Exception as e:
            self.logger.error(f"Error saving scheduled event: {str(e)}")
            return None

    def update_scheduled_event(self, event_data: Dict) -> Optional[Dict]:
        """Update existing scheduled event according to API spec"""
        try:
            response = self.make_request('POST', '/schedulingcontroller/updateScheduledEvent', json=event_data)
            if response.status_code == 200:
                return self._safe_json(response)
            return None
        except Exception as e:
            self.logger.error(f"Error updating scheduled event: {str(e)}")
            return None

    def delete_scheduled_event(self, event_data: Dict) -> Optional[Dict]:
        """Delete scheduled event according to API spec"""
        try:
            response = self.make_request('POST', '/schedulingcontroller/deleteScheduledEvent', json=event_data)
            if response.status_code == 200:
                return self._safe_json(response)
            return None
        except Exception as e:
            self.logger.error(f"Error deleting scheduled event: {str(e)}")
            return None

    def get_event_details(self, event_id: str) -> Optional[Dict]:
        """Get detailed information about a specific event"""
        try:
            request_data = {"eventId": event_id}
            response = self.make_request('POST', '/schedulingcontroller/getEventDetails', json=request_data)
            if response.status_code == 200:
                return self._safe_json(response)
            return None
        except Exception as e:
            self.logger.error(f"Error getting event details: {str(e)}")
            return None

    def get_qualified_reps_for_scheduling(self, mplan_id: str, store_id: str) -> Optional[Dict]:
        """
        Get qualified representatives for scheduling a specific mPlan
        Args:
            mplan_id: The mPlan ID
            store_id: The store/location ID
        Returns:
            dict: List of qualified reps with their IDs and names
        """
        try:
            params = {
                '_dc': str(int(time.time() * 1000)),  # timestamp
                'mPlanID': mplan_id,
                'storeID': store_id,
                'page': 1,
                'start': 0,
                'limit': 100,  # Get more reps
                'sort': '[{"property":"LastName","direction":"ASC"}]'
            }

            response = self.make_request('GET', '/planningextcontroller/getQualifiedRepsForScheduling', params=params)
            if 200 <= response.status_code < 300:
                return self._safe_json(response)
            return None
        except Exception as e:
            self.logger.error(f"Error getting qualified reps: {str(e)}")
            return None

    def get_rep_availability(self, rep_id: str, start_date: str = None, end_date: str = None) -> Optional[Dict]:
        """Check availability for a specific representative"""
        try:
            request_data = {"repId": rep_id}
            if start_date:
                request_data["startDate"] = start_date
            if end_date:
                request_data["endDate"] = end_date

            response = self.make_request('POST', '/schedulingcontroller/getRepAvailability', json=request_data)
            if response.status_code == 200:
                return self._safe_json(response)
            return None
        except Exception as e:
            self.logger.error(f"Error getting rep availability: {str(e)}")
            return None

    def bulk_schedule_events(self, events_data: Dict) -> Optional[Dict]:
        """Create multiple scheduled events in a single request"""
        try:
            response = self.make_request('POST', '/schedulingcontroller/bulkScheduleEvents', json=events_data)
            if response.status_code == 200:
                return self._safe_json(response)
            return None
        except Exception as e:
            self.logger.error(f"Error bulk scheduling events: {str(e)}")
            return None

    # Legacy method names for compatibility
    def get_events(self, start_date: datetime = None, end_date: datetime = None) -> List[Dict]:
        """Compatibility wrapper for get_unscheduled_events"""
        result = self.get_unscheduled_events(start_date, end_date)
        return result if result else []

    def get_employees(self) -> List[Dict]:
        """
        Get employee list. The API doesn't have a dedicated employees endpoint,
        so we use available representatives as a proxy for employees.
        """
        try:
            # Try to get available representatives as a substitute for employees
            reps_data = self.get_available_representatives()
            if reps_data and 'representatives' in reps_data:
                employees = []
                for rep in reps_data['representatives']:
                    employee = {
                        'id': rep.get('repId'),
                        'name': rep.get('name'),
                        'email': rep.get('email'),
                        'phone': rep.get('phone'),
                        'skills': rep.get('skills', []),
                        'availability': rep.get('availability', {}),
                        'currentLoad': rep.get('currentLoad', 0),
                        'maxCapacity': rep.get('maxCapacity', 40),
                        'external_source': 'crossmark'
                    }
                    employees.append(employee)
                return employees

            # Fallback to authenticated user info
            if self.user_info:
                return [{
                    'id': self.username,
                    'name': self.user_info.get('username', self.username),
                    'email': self.user_info.get('email'),
                    'external_source': 'crossmark'
                }]

            return []
        except Exception as e:
            self.logger.error(f"Error getting employees: {str(e)}")
            return []

    def schedule_mplan_event(self, rep_id: str, mplan_id: str, location_id: str, start_datetime: datetime, end_datetime: datetime, planning_override: bool = True) -> Dict:
        """
        Schedule an mPlan event in Crossmark system using the actual API endpoint.
        Args:
            rep_id: Representative ID (employee ID in Crossmark)
            mplan_id: mPlan ID (event ID in Crossmark)
            location_id: Location ID
            start_datetime: Start datetime for the scheduled event
            end_datetime: End datetime for the scheduled event
            planning_override: Whether to override planning constraints (default: True)
        Returns:
            dict: Result of scheduling operation
        """
        try:
            # Format datetime with timezone offset (assuming Eastern Time)
            start_str = start_datetime.strftime("%Y-%m-%dT%H:%M:%S-04:00")
            end_str = end_datetime.strftime("%Y-%m-%dT%H:%M:%S-04:00")

            # URL-encode the datetime colons to match exact curl format
            from urllib.parse import quote
            start_str_encoded = quote(start_str, safe='')
            end_str_encoded = quote(end_str, safe='')

            # Prepare form data as URL-encoded string to match exact curl command
            form_data = f'ClassName=MVScheduledmPlan&RepID={rep_id}&mPlanID={mplan_id}&LocationID={location_id}&Start={start_str_encoded}&End={end_str_encoded}&hash=&v=3.0.1&PlanningOverride=true'

            headers = {
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'origin': self.base_url,
                'priority': 'u=1, i',
                'referer': f'{self.base_url}/planning/',
                'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
                'x-requested-with': 'XMLHttpRequest'
            }

            self.logger.info(f"Scheduling mPlan {mplan_id} for Rep {rep_id} at Location {location_id} from {start_str} to {end_str}")
            self.logger.info(f"PHPSESSID being used: {self.phpsessid[:8] + '...' if self.phpsessid else 'None'}")
            self.logger.info(f"Form data: {form_data}")

            response = self.make_request(
                'POST',
                '/planningextcontroller/scheduleMplanEvent',
                data=form_data,
                headers=headers
            )

            if 200 <= response.status_code < 300:
                result_data = self._safe_json(response)
                self.logger.info(f"Successfully scheduled mPlan {mplan_id}")
                return {
                    'success': True,
                    'message': 'Event scheduled successfully',
                    'mplan_id': mplan_id,
                    'rep_id': rep_id,
                    'response_data': result_data
                }
            else:
                error_msg = f"Failed to schedule event: {response.status_code} {response.text[:300]}"
                self.logger.warning(error_msg)
                return {
                    'success': False,
                    'message': error_msg,
                    'status_code': response.status_code
                }

        except Exception as e:
            error_msg = f"Error scheduling mPlan event: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg
            }

    def get_mplan_by_id(self, mplan_id: str) -> Optional[Dict]:
        """
        Get a specific mplan by ID from the planning API
        Args:
            mplan_id: The mPlan ID to fetch
        Returns:
            dict or None: mPlan data if successful, None otherwise
        """
        params = {
            '_dc': str(int(time.time() * 1000)),  # Timestamp
            'searchFields': f'{{"searchTerms":{{"mPlanID":{{"name":"mPlanID","title":"mPlan ID","items":[{{"id":1,"value":["{mplan_id}"],"displayValue":["{mplan_id}"],"exactmatch":true,"allActive":false}}]}}}}}}',
            'searchFilter': '',
            'page': '1',
            'start': '0',
            'limit': '1'
        }

        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "referer": f"{self.base_url}/planning/",
            "x-requested-with": "XMLHttpRequest"
        }

        try:
            response = self.make_request(
                'GET',
                '/planningextcontroller/getPlanningMplans',
                params=params,
                headers=headers
            )

            if 200 <= response.status_code < 300:
                data = self._safe_json(response)
                if data and 'records' in data and data['records']:
                    self.logger.info(f"Retrieved mplan data for ID: {mplan_id}")
                    return data['records'][0]  # Return first (and should be only) match
                else:
                    self.logger.warning(f"No mplan found for ID: {mplan_id}")
                    return None
            else:
                self.logger.warning(
                    f"Failed to get mplan {mplan_id}: {response.status_code} {response.text[:300]}"
                )
                return None

        except Exception as e:
            self.logger.error(f"Error fetching mplan {mplan_id}: {str(e)}")
            return None

    def get_mplan_bulk_print(self, mplan_location_pairs: List[Dict[str, str]]) -> Optional[Dict]:
        """
        Get mplan data using bulk print endpoint which includes attachments/salesTools
        Args:
            mplan_location_pairs: List of dicts with mPlanID and storeID
        Returns:
            dict or None: Bulk mplan data if successful, None otherwise
        """
        import json
        import urllib.parse

        # Format the data as expected by the API
        mplan_data = json.dumps(mplan_location_pairs)
        data = {
            'mplanLocationIDs': mplan_data,
            'includeAttachment': 'true'
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{self.base_url}/planning/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
        }

        try:
            response = self.make_request(
                'POST',
                '/planningextcontroller/bulkPrintMplanLocations',
                data=data,
                headers=headers
            )

            if 200 <= response.status_code < 300:
                data_result = self._safe_json(response)
                if data_result:
                    self.logger.info(f"Retrieved bulk mplan data for {len(mplan_location_pairs)} items")
                    return data_result
                else:
                    self.logger.warning("No data in bulk mplan response")
                    return None
            else:
                self.logger.warning(
                    f"Failed to get bulk mplan data: {response.status_code} {response.text[:300]}"
                )
                return None

        except Exception as e:
            self.logger.error(f"Error fetching bulk mplan data: {str(e)}")
            return None

    def create_schedule(self, schedule_data: Dict) -> Dict:
        """
        Create schedule using the API specification endpoints.
        First tries the standard saveScheduledEvent endpoint, falls back to mplan scheduling if needed.
        """
        try:
            # Try using the standard API endpoint first
            result = self.save_scheduled_event(schedule_data)
            if result and result.get('success'):
                return {
                    'success': True,
                    'message': 'Event created successfully',
                    'eventId': result.get('eventId'),
                    'data': result
                }

            # Fallback to mplan scheduling if the data suggests it's an mplan
            if all(key in schedule_data for key in ['rep_id', 'mplan_id', 'location_id']):
                return self.schedule_mplan_event(
                    rep_id=schedule_data['rep_id'],
                    mplan_id=schedule_data['mplan_id'],
                    location_id=schedule_data['location_id'],
                    start_datetime=schedule_data['start_datetime'],
                    end_datetime=schedule_data['end_datetime'],
                    planning_override=schedule_data.get('planning_override', True)
                )

            return {
                'success': False,
                'message': 'Failed to create schedule using available methods'
            }

        except KeyError as e:
            return {
                'success': False,
                'message': f'Missing required field: {str(e)}'
            }

    def update_schedule(self, schedule_id: str, schedule_data: Dict) -> Dict:
        """Update schedule using API specification endpoint"""
        try:
            # Add the event ID to the update data
            update_data = {
                "eventId": schedule_id,
                "updates": schedule_data
            }

            result = self.update_scheduled_event(update_data)
            if result and result.get('success'):
                return {
                    'success': True,
                    'message': result.get('message', 'Event updated successfully'),
                    'updatedFields': result.get('updatedFields', [])
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to update schedule'
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error updating schedule: {str(e)}'
            }

    def delete_schedule(self, schedule_id: str, reason: str = None, notify_rep: bool = True) -> Dict:
        """
        Delete schedule using API specification endpoint with fallback to mplan deletion.
        Args:
            schedule_id: The scheduled event ID to delete
            reason: Optional reason for deletion
            notify_rep: Whether to notify the representative
        Returns:
            dict: Result of the delete operation
        """
        try:
            # Try using the standard API endpoint first
            delete_data = {
                "eventId": schedule_id,
                "notifyRep": notify_rep
            }
            if reason:
                delete_data["reason"] = reason

            result = self.delete_scheduled_event(delete_data)
            if result and result.get('success'):
                return {
                    'success': True,
                    'message': result.get('message', 'Event deleted successfully')
                }

            # Fallback to mplan deletion method
            self.logger.info(f"Standard deletion failed, trying mplan deletion for {schedule_id}")
            return self.unschedule_mplan_event(schedule_id)

        except Exception as e:
            error_msg = f"Error deleting scheduled event: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg
            }

    def unschedule_mplan_event(self, schedule_id: str) -> Dict:
        """
        Fallback method for unscheduling mplan events
        """
        try:
            # Prepare form data - only needs the scheduled event ID
            form_data = {
                'id': str(schedule_id)
            }

            headers = {
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9',
                'cache-control': 'no-cache',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'origin': self.base_url,
                'pragma': 'no-cache',
                'referer': f'{self.base_url}/planning/',
                'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'x-requested-with': 'XMLHttpRequest'
            }

            self.logger.info(f"Deleting/unscheduling mPlan event with ID: {schedule_id}")

            response = self.make_request(
                'POST',
                '/planningextcontroller/deleteScheduledMplanEvent',
                data=form_data,
                headers=headers
            )

            if 200 <= response.status_code < 300:
                result_data = self._safe_json(response)
                self.logger.info(f"Successfully deleted/unscheduled mPlan event {schedule_id}")
                return {
                    'success': True,
                    'message': 'Event unscheduled successfully - moved back to unstaffed status',
                    'schedule_id': schedule_id,
                    'response_data': result_data
                }
            else:
                error_msg = f"Failed to delete schedule: {response.status_code} {response.text[:300]}"
                self.logger.warning(error_msg)
                return {
                    'success': False,
                    'message': error_msg,
                    'status_code': response.status_code
                }

        except Exception as e:
            error_msg = f"Error deleting scheduled event: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg
            }

    def unschedule_event(self, schedule_id: str) -> Dict:
        """Alias for delete_schedule - more descriptive name"""
        return self.delete_schedule(schedule_id)

    def logout(self) -> bool:
        """Logout and clear session"""
        try:
            if self.session and self.phpsessid:
                # Attempt to logout gracefully
                logout_url = f"{self.base_url.rstrip('/')}/logout"  # Adjust as needed
                try:
                    self.session.get(logout_url, timeout=self.timeout)
                except:
                    pass  # Ignore logout errors

            # Clear session data
            self.authenticated = False
            self.phpsessid = None
            self.last_login = None
            self.user_info = None
            if self.session:
                self.session.cookies.clear()

            self.logger.info("Session logged out")
            return True
        except Exception as e:
            self.logger.error(f"Logout failed: {str(e)}")
            return False


# Global instance
session_api = SessionAPIService()