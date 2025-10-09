"""
Daily Schedule Report API with Pydantic validation
Provides type-safe interface to Walmart Retail Link Event Management
"""
import requests
from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field, validator


# Request Models
class DailyScheduleRequest(BaseModel):
    """Request model for daily schedule report"""
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    event_types: List[int] = Field(default_factory=lambda: list(range(1, 58)), description="Event type IDs (1-57)")
    club_numbers: List[int] = Field(..., description="List of club/store numbers")
    walmart_week_year: str = Field(default="", description="Walmart week year filter")

    @validator('start_date', 'end_date')
    def validate_date_format(cls, v):
        """Validate date format is YYYY-MM-DD"""
        try:
            # Try to parse the date to ensure it's valid
            from datetime import datetime
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError(f"Date must be in YYYY-MM-DD format, got: {v}")

    @validator('event_types')
    def validate_event_types(cls, v):
        """Ensure event types are in valid range (1-57)"""
        for event_type in v:
            if not 1 <= event_type <= 57:
                raise ValueError(f"Event type must be between 1 and 57, got: {event_type}")
        return v

    class Config:
        schema_extra = {
            "example": {
                "start_date": "2025-09-01",
                "end_date": "2025-10-04",
                "event_types": [1, 3, 4, 5],
                "club_numbers": [8135],
                "walmart_week_year": ""
            }
        }


# Response Models
class EventItem(BaseModel):
    """Individual event item in the schedule"""
    event_id: Optional[int] = Field(None, alias="eventId")
    event_number: Optional[str] = Field(None, alias="eventNumber")
    event_name: Optional[str] = Field(None, alias="eventName")
    event_type: Optional[int] = Field(None, alias="eventType")
    event_date: Optional[str] = Field(None, alias="eventDate")
    club_number: Optional[int] = Field(None, alias="clubNumber")
    club_name: Optional[str] = Field(None, alias="clubName")
    employee_name: Optional[str] = Field(None, alias="employeeName")
    employee_id: Optional[str] = Field(None, alias="employeeId")
    status: Optional[str] = None

    class Config:
        populate_by_name = True  # Allow both snake_case and camelCase


class DailyScheduleResponse(BaseModel):
    """Response model for daily schedule report"""
    events: List[EventItem] = Field(default_factory=list)
    total_count: Optional[int] = Field(None, alias="totalCount")
    success: Optional[bool] = True

    class Config:
        populate_by_name = True


# API Client
class DailyScheduleReportClient:
    """Type-safe client for Daily Schedule Report API"""

    BASE_URL = "https://retaillink2.wal-mart.com/EventManagement"

    def __init__(self, auth_token: str, session: Optional[requests.Session] = None):
        """
        Initialize the client

        Args:
            auth_token: Bearer token for authorization
            session: Optional requests.Session object (recommended for reusing connections)
        """
        self.auth_token = auth_token
        self.session = session or requests.Session()

    def _get_headers(self) -> dict:
        """Get standard headers for API requests"""
        return {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "authorization": f"Bearer {self.auth_token}",
            "content-type": "application/json",
            "referer": f"{self.BASE_URL}/daily-scheduled-report",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        }

    def get_daily_schedule_report(
        self,
        start_date: str,
        end_date: str,
        club_numbers: List[int],
        event_types: Optional[List[int]] = None,
        walmart_week_year: str = ""
    ) -> DailyScheduleResponse:
        """
        Get daily schedule report with type validation

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            club_numbers: List of club/store numbers
            event_types: List of event type IDs (1-57), defaults to all types
            walmart_week_year: Optional Walmart week year filter

        Returns:
            DailyScheduleResponse: Validated response object

        Raises:
            ValidationError: If request parameters are invalid
            HTTPError: If API request fails
        """
        # Create and validate request
        request_data = DailyScheduleRequest(
            start_date=start_date,
            end_date=end_date,
            club_numbers=club_numbers,
            event_types=event_types or list(range(1, 58)),
            walmart_week_year=walmart_week_year
        )

        # Prepare payload (convert to API format)
        payload = {
            "startDate": request_data.start_date,
            "endDate": request_data.end_date,
            "eventType": request_data.event_types,
            "clubList": request_data.club_numbers,
            "walmartWeekYear": request_data.walmart_week_year
        }

        # Make API request
        url = f"{self.BASE_URL}/api/store-event/daily-schedule-report"
        response = self.session.post(url, headers=self._get_headers(), json=payload)
        response.raise_for_status()

        # Parse and validate response
        response_data = response.json()

        # Handle different response formats
        if isinstance(response_data, dict):
            return DailyScheduleResponse(**response_data)
        elif isinstance(response_data, list):
            # If API returns a list directly, wrap it
            return DailyScheduleResponse(events=response_data)
        else:
            return DailyScheduleResponse()


# Convenience functions for backward compatibility
def get_daily_schedule_report(auth_token: str, cookies: Optional[dict] = None) -> dict:
    """
    Legacy function for backward compatibility

    Args:
        auth_token: Bearer token for authorization
        cookies: Optional cookies dict

    Returns:
        dict: Raw JSON response
    """
    url = "https://retaillink2.wal-mart.com/EventManagement/api/store-event/daily-schedule-report"

    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "authorization": f"Bearer {auth_token}",
        "content-type": "application/json",
        "referer": "https://retaillink2.wal-mart.com/EventManagement/daily-scheduled-report",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    }

    payload = {
        "startDate": "2025-09-01",
        "endDate": "2025-10-04",
        "eventType": list(range(1, 58)),
        "clubList": [8135],
        "walmartWeekYear": ""
    }

    if cookies:
        response = requests.post(url, headers=headers, json=payload, cookies=cookies)
    else:
        response = requests.post(url, headers=headers, json=payload)

    response.raise_for_status()
    return response.json()


# Example usage
if __name__ == "__main__":
    # Example with type-safe client
    auth_token = "your-auth-token-here"

    # Create client
    client = DailyScheduleReportClient(auth_token)

    # Get report with validation
    try:
        report = client.get_daily_schedule_report(
            start_date="2025-09-01",
            end_date="2025-10-04",
            club_numbers=[8135],
            event_types=[1, 3, 4, 5]  # Optional: specify event types
        )

        print(f"Found {len(report.events)} events")
        for event in report.events:
            print(f"  - {event.event_name} at {event.club_name}")

    except ValueError as e:
        print(f"Validation error: {e}")
    except requests.HTTPError as e:
        print(f"API error: {e}")