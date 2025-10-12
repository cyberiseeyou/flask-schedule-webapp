# crossmark_improvements.py
"""
Enhanced Crossmark API implementation with full CRUD operations,
better error handling, and advanced features.

This builds on the existing crossmark MCP server to add missing functionality.
"""

import httpx
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Literal
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class EventType(str, Enum):
    """Valid event types in the Crossmark API"""
    SCHEDULED_EVENT = "ScheduledEvent"
    SCHEDULED_AVAILABILITY = "ScheduledAvailability"
    SCHEDULED_LOCATION = "ScheduledLocation"
    SCHEDULED_MPLAN = "ScheduledmPlan"


class EventCondition(str, Enum):
    """Event conditions/statuses"""
    SCHEDULED = "Scheduled"
    UNSCHEDULED = "Unscheduled"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class ScheduledEventData:
    """Base data for all scheduled events"""
    start: str  # ISO8601 timestamp
    end: str    # ISO8601 timestamp
    notes: str = ""
    
    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ScheduledAvailabilityData(ScheduledEventData):
    """Data for rep availability events"""
    rep_mvid: str = None
    rep_name: str = ""


@dataclass
class ScheduledLocationData(ScheduledAvailabilityData):
    """Data for location visit events"""
    location_mvid: str = None
    location_name: str = ""
    location_address: str = ""


@dataclass
class ScheduledmPlanData(ScheduledLocationData):
    """Data for mPlan work events"""
    mplan_mvid: str = None
    mplan_name: str = ""
    mplan_status: str = ""


@dataclass
class ScheduledEvent:
    """Complete scheduled event with MVID"""
    mvid: str
    event_type: EventType
    data: ScheduledEventData
    
    @classmethod
    def from_api_response(cls, response: dict) -> 'ScheduledEvent':
        """Parse API response into ScheduledEvent object"""
        event_type = EventType(response.get("Type"))
        
        # Parse data based on event type
        data_dict = response.get("Data", {})
        
        if event_type == EventType.SCHEDULED_MPLAN:
            data = ScheduledmPlanData(**data_dict)
        elif event_type == EventType.SCHEDULED_LOCATION:
            data = ScheduledLocationData(**data_dict)
        elif event_type == EventType.SCHEDULED_AVAILABILITY:
            data = ScheduledAvailabilityData(**data_dict)
        else:
            data = ScheduledEventData(**data_dict)
        
        return cls(
            mvid=response.get("MVID"),
            event_type=event_type,
            data=data
        )
    
    def to_api_format(self) -> dict:
        """Convert to API format for POST/PUT requests"""
        return {
            "MVID": self.mvid,
            "Type": self.event_type.value,
            "Data": self.data.to_dict()
        }


# ============================================================================
# EXCEPTIONS
# ============================================================================

class CrossmarkAPIError(Exception):
    """Base exception for Crossmark API errors"""
    pass


class AuthenticationError(CrossmarkAPIError):
    """Authentication failed or session expired"""
    pass


class NotFoundError(CrossmarkAPIError):
    """Resource not found"""
    pass


class ValidationError(CrossmarkAPIError):
    """Invalid input data"""
    pass


class RateLimitError(CrossmarkAPIError):
    """API rate limit exceeded"""
    pass


# ============================================================================
# API CLIENT WITH IMPROVED ERROR HANDLING
# ============================================================================

class CrossmarkAPIClient:
    """
    Enhanced API client for Crossmark with proper error handling,
    authentication, and retry logic.
    """
    
    def __init__(
        self,
        base_url: str = "https://crossmark.mvretail.com/api",
        timeout: int = 30
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session_token: Optional[str] = None
        self.session_expires: Optional[datetime] = None
        
        self.client = httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True
        )
    
    async def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate with the API and store session token.
        
        Args:
            username: Crossmark username
            password: Crossmark password
            
        Returns:
            True if authentication successful
            
        Raises:
            AuthenticationError: If credentials are invalid
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/auth/login",
                json={"username": username, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.session_token = data.get("token")
                # Assume 24 hour session expiry if not specified
                expires_in = data.get("expires_in", 86400)
                self.session_expires = datetime.now() + timedelta(seconds=expires_in)
                logger.info("Authentication successful")
                return True
            elif response.status_code == 401:
                raise AuthenticationError("Invalid credentials")
            else:
                raise AuthenticationError(f"Authentication failed: {response.status_code}")
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during authentication: {e}")
            raise AuthenticationError(f"Network error: {e}")
    
    def is_authenticated(self) -> bool:
        """Check if current session is valid"""
        if not self.session_token:
            return False
        if self.session_expires and datetime.now() >= self.session_expires:
            return False
        return True
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make an authenticated API request with error handling.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments for httpx request
            
        Returns:
            Parsed JSON response
            
        Raises:
            AuthenticationError: If session invalid or expired
            CrossmarkAPIError: For other API errors
        """
        if not self.is_authenticated():
            raise AuthenticationError("Not authenticated or session expired")
        
        # Add authentication header
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {self.session_token}"
        kwargs["headers"] = headers
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = await self.client.request(method, url, **kwargs)
            
            # Handle different status codes
            if response.status_code == 200 or response.status_code == 201:
                return response.json()
            elif response.status_code == 401:
                raise AuthenticationError("Session expired")
            elif response.status_code == 404:
                raise NotFoundError(f"Resource not found: {endpoint}")
            elif response.status_code == 429:
                raise RateLimitError("API rate limit exceeded")
            elif response.status_code >= 400:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("message", f"HTTP {response.status_code}")
                raise CrossmarkAPIError(f"API error: {error_msg}")
            
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            raise CrossmarkAPIError(f"Network error: {e}")
    
    # ========================================================================
    # SCHEDULING ENDPOINTS - FULL CRUD
    # ========================================================================
    
    async def get_all_events(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[ScheduledEvent]:
        """
        Get all scheduled events with optional filtering.
        
        Args:
            start_date: Filter events starting after this date (ISO8601)
            end_date: Filter events ending before this date (ISO8601)
            event_type: Filter by specific event type
            limit: Maximum number of events to return
            
        Returns:
            List of ScheduledEvent objects
        """
        params = {"limit": limit}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        if event_type:
            params["type"] = event_type.value
        
        response = await self._request("GET", "/scheduledevent", params=params)
        
        events = []
        for event_data in response.get("events", []):
            events.append(ScheduledEvent.from_api_response(event_data))
        
        return events
    
    async def get_event(self, event_id: str) -> ScheduledEvent:
        """
        Get a specific scheduled event by ID.
        
        Args:
            event_id: MVID of the event
            
        Returns:
            ScheduledEvent object
            
        Raises:
            NotFoundError: If event doesn't exist
        """
        response = await self._request("GET", f"/scheduledevent/{event_id}")
        return ScheduledEvent.from_api_response(response)
    
    async def create_event(
        self,
        event_type: EventType,
        start: str,
        end: str,
        notes: str = "",
        rep_mvid: Optional[str] = None,
        location_mvid: Optional[str] = None,
        mplan_mvid: Optional[str] = None,
        **additional_fields
    ) -> ScheduledEvent:
        """
        Create a new scheduled event.
        
        Args:
            event_type: Type of event to create
            start: Start timestamp (ISO8601)
            end: End timestamp (ISO8601)
            notes: Optional notes
            rep_mvid: Rep MVID (required for Availability, Location, mPlan)
            location_mvid: Location MVID (required for Location, mPlan)
            mplan_mvid: mPlan MVID (required for mPlan)
            **additional_fields: Any additional fields for the event
            
        Returns:
            Created ScheduledEvent object
            
        Raises:
            ValidationError: If required fields are missing
        """
        # Validate required fields based on event type
        if event_type in [EventType.SCHEDULED_AVAILABILITY, EventType.SCHEDULED_LOCATION, EventType.SCHEDULED_MPLAN]:
            if not rep_mvid:
                raise ValidationError(f"{event_type.value} requires rep_mvid")
        
        if event_type in [EventType.SCHEDULED_LOCATION, EventType.SCHEDULED_MPLAN]:
            if not location_mvid:
                raise ValidationError(f"{event_type.value} requires location_mvid")
        
        if event_type == EventType.SCHEDULED_MPLAN:
            if not mplan_mvid:
                raise ValidationError(f"{event_type.value} requires mplan_mvid")
        
        # Build data object
        data = {
            "start": start,
            "end": end,
            "notes": notes,
            **additional_fields
        }
        
        if rep_mvid:
            data["rep_mvid"] = rep_mvid
        if location_mvid:
            data["location_mvid"] = location_mvid
        if mplan_mvid:
            data["mplan_mvid"] = mplan_mvid
        
        # Create request body
        request_body = {
            "Type": event_type.value,
            "Data": data
        }
        
        response = await self._request(
            "POST",
            "/scheduledevent",
            json=request_body
        )
        
        return ScheduledEvent.from_api_response(response)
    
    async def update_event(
        self,
        event_id: str,
        **updates
    ) -> ScheduledEvent:
        """
        Update an existing scheduled event.
        
        Args:
            event_id: MVID of the event to update
            **updates: Fields to update (start, end, notes, etc.)
            
        Returns:
            Updated ScheduledEvent object
        """
        # Get current event to build update request
        current_event = await self.get_event(event_id)
        
        # Update the data
        current_data = current_event.data.to_dict()
        current_data.update(updates)
        
        request_body = {
            "Type": current_event.event_type.value,
            "Data": current_data
        }
        
        response = await self._request(
            "PUT",
            f"/scheduledevent/{event_id}",
            json=request_body
        )
        
        return ScheduledEvent.from_api_response(response)
    
    async def delete_event(self, event_id: str) -> bool:
        """
        Delete a scheduled event.
        
        Args:
            event_id: MVID of the event to delete
            
        Returns:
            True if deletion successful
        """
        await self._request("DELETE", f"/scheduledevent/{event_id}")
        return True
    
    # ========================================================================
    # BATCH OPERATIONS
    # ========================================================================
    
    async def batch_create_events(
        self,
        events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create multiple events in a single API call.
        
        Args:
            events: List of event dictionaries with type and data
            
        Returns:
            Dictionary with created events and any failures
        """
        request_body = {"events": events}
        
        try:
            response = await self._request(
                "POST",
                "/scheduledevent/batch",
                json=request_body
            )
            
            return {
                "created": [
                    ScheduledEvent.from_api_response(e) 
                    for e in response.get("created", [])
                ],
                "failed": response.get("failed", []),
                "total": len(events)
            }
        except CrossmarkAPIError as e:
            logger.error(f"Batch create failed: {e}")
            return {
                "created": [],
                "failed": events,
                "total": len(events),
                "error": str(e)
            }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# ============================================================================
# ENHANCED DATABASE OPERATIONS
# ============================================================================

class EventDatabase:
    """
    Enhanced database manager with proper schema for all event types
    and relationship tracking.
    """
    
    def __init__(self, db_path: str = "./crossmark_events.db"):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Create database schema if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        # Main events table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_events (
                mvid TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                synced_at TEXT,
                is_deleted INTEGER DEFAULT 0
            )
        """)
        
        # Rep references
        conn.execute("""
            CREATE TABLE IF NOT EXISTS event_reps (
                event_mvid TEXT,
                rep_mvid TEXT,
                rep_name TEXT,
                FOREIGN KEY (event_mvid) REFERENCES scheduled_events(mvid),
                PRIMARY KEY (event_mvid, rep_mvid)
            )
        """)
        
        # Location references
        conn.execute("""
            CREATE TABLE IF NOT EXISTS event_locations (
                event_mvid TEXT,
                location_mvid TEXT,
                location_name TEXT,
                location_address TEXT,
                FOREIGN KEY (event_mvid) REFERENCES scheduled_events(mvid),
                PRIMARY KEY (event_mvid, location_mvid)
            )
        """)
        
        # mPlan references
        conn.execute("""
            CREATE TABLE IF NOT EXISTS event_mplans (
                event_mvid TEXT,
                mplan_mvid TEXT,
                mplan_name TEXT,
                mplan_status TEXT,
                FOREIGN KEY (event_mvid) REFERENCES scheduled_events(mvid),
                PRIMARY KEY (event_mvid, mplan_mvid)
            )
        """)
        
        # Create indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON scheduled_events(type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_start ON scheduled_events(start_time)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_end ON scheduled_events(end_time)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_sync ON scheduled_events(synced_at)")
        
        conn.commit()
        conn.close()
    
    def save_event(self, event: ScheduledEvent):
        """
        Save an event to the database with all its relationships.
        
        Args:
            event: ScheduledEvent object to save
        """
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Insert/update main event
            conn.execute("""
                INSERT OR REPLACE INTO scheduled_events 
                (mvid, type, start_time, end_time, notes, updated_at, synced_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                event.mvid,
                event.event_type.value,
                event.data.start,
                event.data.end,
                event.data.notes,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            # Save rep reference if applicable
            if hasattr(event.data, 'rep_mvid') and event.data.rep_mvid:
                conn.execute("""
                    INSERT OR REPLACE INTO event_reps
                    (event_mvid, rep_mvid, rep_name)
                    VALUES (?, ?, ?)
                """, (
                    event.mvid,
                    event.data.rep_mvid,
                    getattr(event.data, 'rep_name', '')
                ))
            
            # Save location reference if applicable
            if hasattr(event.data, 'location_mvid') and event.data.location_mvid:
                conn.execute("""
                    INSERT OR REPLACE INTO event_locations
                    (event_mvid, location_mvid, location_name, location_address)
                    VALUES (?, ?, ?, ?)
                """, (
                    event.mvid,
                    event.data.location_mvid,
                    getattr(event.data, 'location_name', ''),
                    getattr(event.data, 'location_address', '')
                ))
            
            # Save mPlan reference if applicable
            if hasattr(event.data, 'mplan_mvid') and event.data.mplan_mvid:
                conn.execute("""
                    INSERT OR REPLACE INTO event_mplans
                    (event_mvid, mplan_mvid, mplan_name, mplan_status)
                    VALUES (?, ?, ?, ?)
                """, (
                    event.mvid,
                    event.data.mplan_mvid,
                    getattr(event.data, 'mplan_name', ''),
                    getattr(event.data, 'mplan_status', '')
                ))
            
            conn.commit()
            
        finally:
            conn.close()
    
    def query_events(
        self,
        event_type: Optional[EventType] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        rep_mvid: Optional[str] = None,
        location_mvid: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query events from the database with flexible filtering.
        
        Args:
            event_type: Filter by event type
            start_date: Events starting after this date
            end_date: Events ending before this date
            rep_mvid: Filter by rep MVID
            location_mvid: Filter by location MVID
            limit: Maximum results to return
            
        Returns:
            List of event dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        query = "SELECT * FROM scheduled_events WHERE is_deleted = 0"
        params = []
        
        if event_type:
            query += " AND type = ?"
            params.append(event_type.value)
        
        if start_date:
            query += " AND start_time >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND end_time <= ?"
            params.append(end_date)
        
        if rep_mvid:
            query += " AND mvid IN (SELECT event_mvid FROM event_reps WHERE rep_mvid = ?)"
            params.append(rep_mvid)
        
        if location_mvid:
            query += " AND mvid IN (SELECT event_mvid FROM event_locations WHERE location_mvid = ?)"
            params.append(location_mvid)
        
        query += " ORDER BY start_time LIMIT ?"
        params.append(limit)
        
        cursor = conn.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

async def main():
    """Example usage of the enhanced Crossmark API client"""
    
    # Initialize client
    client = CrossmarkAPIClient()
    
    try:
        # Authenticate
        await client.authenticate("username", "password")
        
        # Create a simple event
        event = await client.create_event(
            event_type=EventType.SCHEDULED_EVENT,
            start="2025-10-11T09:00:00Z",
            end="2025-10-11T10:00:00Z",
            notes="Team meeting"
        )
        print(f"Created event: {event.mvid}")
        
        # Create a location visit
        location_event = await client.create_event(
            event_type=EventType.SCHEDULED_LOCATION,
            start="2025-10-11T14:00:00Z",
            end="2025-10-11T16:00:00Z",
            notes="Store visit",
            rep_mvid="rep-12345",
            location_mvid="loc-67890"
        )
        print(f"Created location event: {location_event.mvid}")
        
        # Get all events for a date range
        events = await client.get_all_events(
            start_date="2025-10-01T00:00:00Z",
            end_date="2025-10-31T23:59:59Z",
            event_type=EventType.SCHEDULED_LOCATION
        )
        print(f"Found {len(events)} location events in October")
        
        # Update an event
        updated = await client.update_event(
            event.mvid,
            notes="Team meeting - RESCHEDULED"
        )
        print(f"Updated event notes")
        
        # Save to database
        db = EventDatabase()
        for evt in events:
            db.save_event(evt)
        print(f"Saved {len(events)} events to database")
        
        # Query from database
        stored_events = db.query_events(
            event_type=EventType.SCHEDULED_LOCATION,
            start_date="2025-10-01"
        )
        print(f"Retrieved {len(stored_events)} events from database")
        
        # Delete an event
        await client.delete_event(event.mvid)
        print(f"Deleted event: {event.mvid}")
        
    except AuthenticationError as e:
        print(f"Auth error: {e}")
    except CrossmarkAPIError as e:
        print(f"API error: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
