import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, timedelta
from typing import Optional, Union, Mapping, Any


logger = logging.getLogger(__name__)


class CrossmarkSession(requests.Session):
    """
    A custom session class for the Crossmark API.
    Inherits from requests.Session and provides authentication methods.
    """

    def __init__(
        self,
        timezone: str = "America/Indiana/Indianapolis",
        request_timeout: float = 15.0,
    ):
        """
        Initialize the CrossmarkSession as a requests.Session.

        Args:
            timezone (str): The timezone (defaults to America/Indiana/Indianapolis)
            request_timeout (float): Default timeout in seconds for HTTP requests
        """
        super().__init__()
        self.username = None
        self.password = None
        self.timezone = timezone
        self.base_url = "https://crossmark.mvretail.com"
        self.authenticated = False
        self.user_info = None
        self.request_timeout = request_timeout

        # Minimal default headers appropriate for API usage
        self.headers.update(
            {
                "accept": "application/json",
                "user-agent": "crossmark-webapp/0.1 (+requests)",
            }
        )

        # Configure retries/backoff for transient errors
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=(
                "GET",
                "POST",
                "PUT",
                "DELETE",
                "PATCH",
                "HEAD",
                "OPTIONS",
            ),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.mount("https://", adapter)
        self.mount("http://", adapter)

    def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate with the Crossmark API using provided credentials.

        Args:
            username (str): The username for authentication
            password (str): The password for authentication

        Returns:
            bool: True if authentication was successful, False otherwise
        """
        self.username = username
        self.password = password

        if self._authenticate():
            self.user_info = self._get_user_info()
            return True
        else:
            self.user_info = None
            return False

    def _authenticate(self) -> bool:
        """
        Perform authentication with the Crossmark API.

        Returns:
            bool: True if authentication was successful, False otherwise
        """
        if not self.username or not self.password:
            print("No credentials provided for authentication")
            return False

        auth_url = f"{self.base_url}/login/authenticate"

        # Prepare authentication data
        auth_data = {
            "UserType": "MVEntityUser",
            "UserID": self.username,
            "Password": self.password,
            "Timezone": self.timezone,
        }

        try:
            # Set flag to bypass authentication check during authentication
            self._authenticating = True
            response = self.post(auth_url, json=auth_data)

            if 200 <= response.status_code < 300:
                self.authenticated = True
                logger.info("Successfully authenticated as %s", self.username)
                return True
            else:
                logger.warning(
                    "Authentication failed: %s %s",
                    response.status_code,
                    response.text[:300],
                )
                return False

        except requests.exceptions.RequestException as e:
            logger.error("Authentication error: %s", e)
            return False
        finally:
            # Clear the flag
            self._authenticating = False

    def is_authenticated(self) -> bool:
        """
        Check if the session is authenticated.

        Returns:
            bool: True if authenticated, False otherwise
        """
        return self.authenticated

    def _get_user_info(self) -> Optional[dict]:
        """
        Retrieve user information after successful authentication.

        Returns:
            dict or None: User information if successful, None otherwise
        """
        user_info_url = f"{self.base_url}/users/getUserInfo"

        try:
            # This should work now since we're authenticated
            response = self.get(user_info_url)

            if 200 <= response.status_code < 300:
                user_data = self._safe_json(response)
                if user_data is None:
                    return None
                logger.info(
                    "Retrieved user info for: %s",
                    user_data.get("username", "Unknown User"),
                )
                return user_data
            else:
                logger.warning(
                    "Failed to get user info: %s %s",
                    response.status_code,
                    response.text[:300],
                )
                return None

        except requests.exceptions.RequestException as e:
            logger.error("Error getting user info: %s", e)
            return None

    def get_user_info(self) -> Optional[dict]:
        """
        Get cached user information or retrieve it if not cached.

        Returns:
            dict or None: User information if available, None otherwise
        """
        if self.user_info is None and self.authenticated:
            self.user_info = self._get_user_info()

        return self.user_info

    def get_scheduled_events(
        self,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
    ) -> Optional[Mapping[str, Any]]:
        """
        Get scheduled events from Crossmark API.

        Args:
            start_date (str, optional): Start date in MM/DD/YYYY format.
                                      Defaults to 2 weeks before today.
            end_date (str, optional): End date in MM/DD/YYYY format.
                                    Defaults to 1 month from today.

        Returns:
            dict or None: Scheduled events data if successful, None otherwise
        """
        # Calculate default date range if not provided
        if start_date is None:
            start_dt = datetime.now() - timedelta(weeks=2)
            start_date = start_dt.strftime("%m/%d/%Y")
        else:
            start_date = self._format_date(start_date)

        if end_date is None:
            end_dt = datetime.now() + timedelta(days=30)  # Approximately 1 month
            end_date = end_dt.strftime("%m/%d/%Y")
        else:
            end_date = self._format_date(end_date)

        # Format the project parameter as required by the API
        project_param = f"{start_date} 00:00:00,{end_date} 23:59:59"

        # Prepare multipart form data
        files = {
            "project": (None, project_param),
            "priorities": (None, ""),
            "projectsDropdownCustomSearchValues": (None, ""),
            "repsDropdownCustomSearchValues": (None, ""),
        }

        # Minimal headers (let requests set multipart content-type)
        headers = {"accept": "application/json"}

        scheduled_events_url = (
            f"{self.base_url}/schedulingcontroller/getScheduledEvents"
        )

        try:
            # Make POST request with multipart form data
            response = self.post(scheduled_events_url, files=files, headers=headers)

            if 200 <= response.status_code < 300:
                events_data = self._safe_json(response)
                if events_data is None:
                    return None
                logger.info(
                    "Retrieved scheduled events from %s to %s", start_date, end_date
                )
                return events_data
            else:
                logger.warning(
                    "Failed to get scheduled events: %s %s",
                    response.status_code,
                    response.text[:300],
                )
                return None

        except requests.exceptions.RequestException as e:
            logger.error("Error getting scheduled events: %s", e)
            return None

    def get_unscheduled_events(
        self,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
    ) -> Optional[Mapping[str, Any]]:
        """
        Get unscheduled events (non-scheduled visits) from Crossmark API.

        Args:
            start_date (str, optional): Start date in MM/DD/YYYY format.
                                      Defaults to 2 weeks before today.
            end_date (str, optional): End date in MM/DD/YYYY format.
                                    Defaults to 1 month from today.

        Returns:
            dict or None: Unscheduled events data if successful, None otherwise
        """
        # Calculate default date range if not provided
        if start_date is None:
            start_dt = datetime.now() - timedelta(weeks=2)
            start_date = start_dt.strftime("%m/%d/%Y")
        else:
            start_date = self._format_date(start_date)

        if end_date is None:
            end_dt = datetime.now() + timedelta(days=30)  # Approximately 1 month
            end_date = end_dt.strftime("%m/%d/%Y")
        else:
            end_date = self._format_date(end_date)

        # Format the project parameter as required by the API (note: different format than scheduled events)
        project_param = f"{start_date},{end_date}"

        # Prepare multipart form data
        files = {
            "project": (None, project_param),
            "priorities": (None, ""),
            "projectsDropdownCustomSearchValues": (None, ""),
        }

        headers = {"accept": "application/json"}

        unscheduled_events_url = (
            f"{self.base_url}/schedulingcontroller/getNonScheduledVisits"
        )

        try:
            # Make POST request with multipart form data
            response = self.post(unscheduled_events_url, files=files, headers=headers)

            if 200 <= response.status_code < 300:
                events_data = self._safe_json(response)
                if events_data is None:
                    return None
                logger.info(
                    "Retrieved unscheduled events from %s to %s", start_date, end_date
                )
                return events_data
            else:
                logger.warning(
                    "Failed to get unscheduled events: %s %s",
                    response.status_code,
                    response.text[:300],
                )
                return None

        except requests.exceptions.RequestException as e:
            logger.error("Error getting unscheduled events: %s", e)
            return None

    def request(self, method, url, *args, **kwargs):
        """
        Override the request method to ensure we're authenticated.
        """
        # Skip authentication check during the authentication process itself
        if hasattr(self, "_authenticating") and self._authenticating:
            return super().request(method, url, *args, **kwargs)

        if not self.authenticated:
            logger.info("Session not authenticated. Attempting to re-authenticate...")
            if not self._authenticate():
                raise requests.exceptions.RequestException("Authentication failed")
        kwargs.setdefault("timeout", self.request_timeout)
        return super().request(method, url, *args, **kwargs)

    def _safe_json(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
        try:
            return response.json()
        except ValueError:
            logger.warning("Non-JSON response: %s", response.text[:300])
            return None

    def _format_date(self, value: Union[str, datetime]) -> str:
        if isinstance(value, datetime):
            return value.strftime("%m/%d/%Y")
        return value
