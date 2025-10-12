# Crossmark API Implementation Analysis & Improvement Suggestions

## API Overview

The Crossmark/Movista API (v2.1) provides access to scheduling information for retail representatives. The API is hosted at `https://{subdomain}.mvretail.com/api`.

### Current Scheduling Endpoint: `/scheduledevent`

The API provides a single unified endpoint that handles 4 different types of scheduled items:

1. **ScheduledEvent** - Basic events with start/end times and notes
2. **ScheduledAvailability** - Rep availability with Rep reference
3. **ScheduledLocation** - Location visits with Rep and Location references  
4. **ScheduledmPlan** - Planned merchandising work with Rep, Location, and mPlan references

### Available Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/scheduledevent` | Get all scheduled events (supports filtering) |
| POST | `/scheduledevent` | Create a new scheduled event |
| GET | `/scheduledevent/{SchedulingID}` | Get a specific event by ID |
| PUT | `/scheduledevent/{SchedulingID}` | Update an existing event |
| DELETE | `/scheduledevent/{SchedulingID}` | Delete a scheduled event |

### Data Structure

All responses use the MVID (Movista ID) identifier system:

```json
{
  "MVID": "unique-identifier",
  "Type": "ScheduledEvent|ScheduledAvailability|ScheduledLocation|ScheduledmPlan",
  "Data": {
    "Start": "ISO8601 timestamp",
    "End": "ISO8601 timestamp",
    "Notes": "string",
    // Additional fields based on Type
  }
}
```

## Current Implementation Analysis

### Existing Tools in Crossmark MCP

Your current implementation has these tools:

1. **authenticate** - Login with username/password
2. **fetch_events** - Retrieve events for a date range
3. **save_events_to_db** - Store events in local SQLite database
4. **query_events** - Query stored events from database
5. **get_session_status** - Check if authenticated

### Current Implementation Strengths ✅

- ✅ **Authentication handling** - Proper session management
- ✅ **Date range filtering** - Can fetch events by date range
- ✅ **Local caching** - SQLite database for offline access
- ✅ **Basic querying** - Can filter by event type and condition

### Missing/Limited Functionality ⚠️

Based on the API documentation, here's what's missing or could be improved:

## Improvement Recommendations

### 1. **Expand CRUD Operations** 🔧

**Current State:** Only implements READ operations (fetching)

**Suggested Additions:**

```python
# crossmark_mcp_improvements.py

async def create_event(
    event_type: str,  # ScheduledEvent, ScheduledAvailability, etc.
    start_time: str,
    end_time: str,
    notes: str = "",
    rep_mvid: str = None,
    location_mvid: str = None,
    mplan_mvid: str = None
) -> dict:
    """
    Create a new scheduled event
    
    Args:
        event_type: Type of event to create
        start_time: ISO8601 start timestamp
        end_time: ISO8601 end timestamp
        notes: Optional notes
        rep_mvid: Required for Availability, Location, mPlan events
        location_mvid: Required for Location and mPlan events
        mplan_mvid: Required for mPlan events
    """
    pass

async def update_event(
    event_id: str,
    updates: dict
) -> dict:
    """
    Update an existing scheduled event
    
    Args:
        event_id: MVID of the event to update
        updates: Dictionary of fields to update
    """
    pass

async def delete_event(event_id: str) -> dict:
    """
    Delete a scheduled event
    
    Args:
        event_id: MVID of the event to delete
    """
    pass
```

### 2. **Enhanced Filtering & Querying** 🔍

**Current State:** Basic filtering by event type and condition

**Suggested Improvements:**

```python
async def fetch_events_advanced(
    start_date: str = None,
    end_date: str = None,
    event_types: list = None,  # Multiple types
    rep_ids: list = None,       # Filter by specific reps
    location_ids: list = None,   # Filter by locations
    mplan_ids: list = None,      # Filter by mPlans
    include_completed: bool = True,
    sort_by: str = "start_time",
    sort_order: str = "asc"
) -> list:
    """
    Advanced event fetching with multiple filter options
    """
    pass

async def search_events(
    search_term: str,
    search_fields: list = ["notes", "location_name"]
) -> list:
    """
    Full-text search across event data
    """
    pass
```

### 3. **Better Type Support** 📋

**Current State:** Treats all events generically

**Suggested Approach:**

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class ScheduledEventBase:
    """Base class for all scheduled events"""
    mvid: str
    start: datetime
    end: datetime
    notes: str
    type: str

@dataclass
class ScheduledAvailability(ScheduledEventBase):
    """Rep availability event"""
    rep_mvid: str
    rep_name: str = ""

@dataclass
class ScheduledLocation(ScheduledAvailability):
    """Location visit event"""
    location_mvid: str
    location_name: str = ""
    location_address: str = ""

@dataclass
class ScheduledmPlan(ScheduledLocation):
    """mPlan work event"""
    mplan_mvid: str
    mplan_name: str = ""
    mplan_status: str = ""

# Parser function
def parse_event(event_data: dict) -> ScheduledEventBase:
    """Parse API response into appropriate event type"""
    event_type = event_data.get("Type")
    
    if event_type == "ScheduledmPlan":
        return ScheduledmPlan(**event_data["Data"])
    elif event_type == "ScheduledLocation":
        return ScheduledLocation(**event_data["Data"])
    elif event_type == "ScheduledAvailability":
        return ScheduledAvailability(**event_data["Data"])
    else:
        return ScheduledEventBase(**event_data["Data"])
```

### 4. **Database Schema Improvements** 🗄️

**Current Issues:**
- May not fully capture all event types
- Missing relationships between events and reps/locations/mplans

**Suggested Schema:**

```sql
-- Main events table
CREATE TABLE IF NOT EXISTS scheduled_events (
    mvid TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    synced_at DATETIME,
    is_deleted BOOLEAN DEFAULT 0
);

-- Rep references
CREATE TABLE IF NOT EXISTS event_reps (
    event_mvid TEXT,
    rep_mvid TEXT,
    rep_name TEXT,
    FOREIGN KEY (event_mvid) REFERENCES scheduled_events(mvid),
    PRIMARY KEY (event_mvid, rep_mvid)
);

-- Location references
CREATE TABLE IF NOT EXISTS event_locations (
    event_mvid TEXT,
    location_mvid TEXT,
    location_name TEXT,
    location_address TEXT,
    FOREIGN KEY (event_mvid) REFERENCES scheduled_events(mvid),
    PRIMARY KEY (event_mvid, location_mvid)
);

-- mPlan references
CREATE TABLE IF NOT EXISTS event_mplans (
    event_mvid TEXT,
    mplan_mvid TEXT,
    mplan_name TEXT,
    mplan_status TEXT,
    FOREIGN KEY (event_mvid) REFERENCES scheduled_events(mvid),
    PRIMARY KEY (event_mvid, mplan_mvid)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_events_type ON scheduled_events(type);
CREATE INDEX IF NOT EXISTS idx_events_start ON scheduled_events(start_time);
CREATE INDEX IF NOT EXISTS idx_events_end ON scheduled_events(end_time);
CREATE INDEX IF NOT EXISTS idx_events_sync ON scheduled_events(synced_at);
```

### 5. **Sync & Conflict Resolution** 🔄

**Current State:** One-way sync (API → Database)

**Suggested Two-Way Sync:**

```python
async def sync_events(
    direction: str = "both",  # "pull", "push", "both"
    force: bool = False
) -> dict:
    """
    Bidirectional sync between local DB and API
    
    Returns statistics about sync operation
    """
    stats = {
        "pulled": 0,
        "pushed": 0,
        "conflicts": 0,
        "errors": []
    }
    
    if direction in ["pull", "both"]:
        # Fetch from API, update local DB
        remote_events = await fetch_events_from_api()
        for event in remote_events:
            # Check for conflicts
            local_event = get_local_event(event["mvid"])
            if local_event and not force:
                if needs_conflict_resolution(local_event, event):
                    stats["conflicts"] += 1
                    continue
            
            save_to_db(event)
            stats["pulled"] += 1
    
    if direction in ["push", "both"]:
        # Push local changes to API
        local_changes = get_unsynced_changes()
        for change in local_changes:
            try:
                if change["operation"] == "create":
                    await create_event(**change["data"])
                elif change["operation"] == "update":
                    await update_event(change["mvid"], change["data"])
                elif change["operation"] == "delete":
                    await delete_event(change["mvid"])
                
                mark_as_synced(change["mvid"])
                stats["pushed"] += 1
            except Exception as e:
                stats["errors"].append(str(e))
    
    return stats
```

### 6. **Error Handling & Retry Logic** ⚠️

**Suggested Additions:**

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import httpx

class CrossmarkAPIError(Exception):
    """Base exception for API errors"""
    pass

class AuthenticationError(CrossmarkAPIError):
    """Authentication failed"""
    pass

class RateLimitError(CrossmarkAPIError):
    """API rate limit exceeded"""
    pass

@retry(
    retry=retry_if_exception_type((httpx.HTTPError, RateLimitError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def api_request_with_retry(
    method: str,
    endpoint: str,
    **kwargs
) -> dict:
    """
    Make API request with automatic retry on transient failures
    """
    try:
        response = await make_api_request(method, endpoint, **kwargs)
        
        # Handle API-specific error codes
        if response.status_code == 401:
            raise AuthenticationError("Session expired")
        elif response.status_code == 429:
            raise RateLimitError("Rate limit exceeded")
        elif response.status_code >= 400:
            error_msg = response.json().get("message", "Unknown error")
            raise CrossmarkAPIError(f"API error: {error_msg}")
        
        return response.json()
        
    except httpx.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        raise
```

### 7. **Caching Strategy** 💾

**Suggested Implementation:**

```python
from functools import lru_cache
from datetime import datetime, timedelta
import pickle

class EventCache:
    """In-memory cache for frequently accessed events"""
    
    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.ttl = timedelta(seconds=ttl_seconds)
    
    def get(self, key: str):
        """Get cached value if not expired"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value):
        """Cache a value with timestamp"""
        self.cache[key] = (value, datetime.now())
    
    def invalidate(self, key: str = None):
        """Clear cache for specific key or all"""
        if key:
            self.cache.pop(key, None)
        else:
            self.cache.clear()

# Global cache instance
event_cache = EventCache(ttl_seconds=300)

async def get_event_cached(event_id: str) -> dict:
    """Get event with caching"""
    cached = event_cache.get(event_id)
    if cached:
        return cached
    
    event = await fetch_event_from_api(event_id)
    event_cache.set(event_id, event)
    return event
```

### 8. **Batch Operations** 📦

**Suggested for Efficiency:**

```python
async def batch_create_events(events: list[dict]) -> dict:
    """
    Create multiple events in a single API call
    
    Uses the Batch API mentioned in documentation
    """
    results = {
        "created": [],
        "failed": [],
        "total": len(events)
    }
    
    # API supports batch operations
    try:
        response = await api_request_with_retry(
            "POST",
            "/scheduledevent/batch",
            json={"events": events}
        )
        
        for result in response.get("results", []):
            if result.get("success"):
                results["created"].append(result["mvid"])
            else:
                results["failed"].append({
                    "data": result.get("data"),
                    "error": result.get("error")
                })
                
    except Exception as e:
        logger.error(f"Batch create failed: {e}")
        results["error"] = str(e)
    
    return results

async def batch_delete_events(event_ids: list[str]) -> dict:
    """Delete multiple events efficiently"""
    # Similar implementation
    pass
```

### 9. **Webhook/Notification Support** 🔔

**If API supports webhooks:**

```python
from fastapi import FastAPI, Request
import hmac
import hashlib

app = FastAPI()

@app.post("/webhooks/crossmark/events")
async def handle_event_webhook(request: Request):
    """
    Handle incoming webhooks from Crossmark API
    
    Allows real-time updates without polling
    """
    # Verify webhook signature
    signature = request.headers.get("X-Crossmark-Signature")
    body = await request.body()
    
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected_signature):
        return {"error": "Invalid signature"}, 401
    
    payload = await request.json()
    
    # Handle different webhook events
    event_type = payload.get("event")
    
    if event_type == "event.created":
        await handle_event_created(payload["data"])
    elif event_type == "event.updated":
        await handle_event_updated(payload["data"])
    elif event_type == "event.deleted":
        await handle_event_deleted(payload["data"])
    
    return {"status": "processed"}
```

### 10. **Analytics & Reporting** 📊

**Suggested Analytics Functions:**

```python
async def get_rep_utilization(
    rep_id: str,
    start_date: str,
    end_date: str
) -> dict:
    """
    Calculate rep utilization metrics
    
    Returns:
        - Total scheduled hours
        - Breakdown by event type
        - Gaps in schedule
        - Average visit duration
    """
    events = await fetch_events_advanced(
        start_date=start_date,
        end_date=end_date,
        rep_ids=[rep_id]
    )
    
    metrics = {
        "total_hours": 0,
        "by_type": {},
        "gaps": [],
        "locations_visited": set(),
        "mplans_completed": 0
    }
    
    # Calculate metrics
    for event in sorted(events, key=lambda e: e["start"]):
        duration = calculate_duration(event["start"], event["end"])
        metrics["total_hours"] += duration
        
        event_type = event["type"]
        metrics["by_type"][event_type] = \
            metrics["by_type"].get(event_type, 0) + duration
        
        if event_type == "ScheduledLocation":
            metrics["locations_visited"].add(event["location_mvid"])
        elif event_type == "ScheduledmPlan":
            metrics["mplans_completed"] += 1
    
    metrics["locations_visited"] = len(metrics["locations_visited"])
    
    return metrics

async def get_location_visit_frequency(
    location_id: str,
    days_back: int = 90
) -> dict:
    """
    Analyze how often a location is visited
    """
    pass

async def get_mplan_completion_rate(
    mplan_id: str = None,
    date_range: tuple = None
) -> dict:
    """
    Calculate mPlan completion statistics
    """
    pass
```

## Implementation Priority

### Phase 1: Core Improvements (Week 1-2)
1. ✅ Add CREATE, UPDATE, DELETE operations
2. ✅ Improve database schema for proper relationships
3. ✅ Implement proper error handling and retries
4. ✅ Add type-safe data models

### Phase 2: Enhanced Features (Week 3-4)
1. ✅ Advanced filtering and search
2. ✅ Bidirectional sync with conflict resolution
3. ✅ Caching layer for performance
4. ✅ Batch operations support

### Phase 3: Advanced Features (Week 5-6)
1. ✅ Analytics and reporting functions
2. ✅ Webhook support (if available)
3. ✅ Comprehensive logging and monitoring
4. ✅ API rate limiting handling

## Code Structure Suggestion

```
crossmark_mcp/
├── __init__.py
├── server.py              # MCP server entry point
├── models/
│   ├── __init__.py
│   ├── events.py          # Event data models
│   └── references.py      # Rep, Location, mPlan models
├── api/
│   ├── __init__.py
│   ├── client.py          # API client with retry logic
│   ├── auth.py            # Authentication handling
│   └── endpoints/
│       ├── scheduling.py  # Scheduling endpoint methods
│       └── batch.py       # Batch operation methods
├── database/
│   ├── __init__.py
│   ├── schema.py          # Database schema
│   ├── queries.py         # Query functions
│   └── sync.py            # Sync logic
├── cache/
│   ├── __init__.py
│   └── manager.py         # Cache management
├── utils/
│   ├── __init__.py
│   ├── datetime.py        # Date/time utilities
│   └── validation.py      # Input validation
├── analytics/
│   ├── __init__.py
│   └── reports.py         # Analytics functions
└── tests/
    ├── test_api.py
    ├── test_database.py
    └── test_sync.py
```

## Testing Recommendations

```python
# tests/test_scheduling.py
import pytest
from crossmark_mcp.api.endpoints import scheduling
from crossmark_mcp.models.events import ScheduledEvent

@pytest.mark.asyncio
async def test_create_event():
    """Test event creation"""
    event_data = {
        "type": "ScheduledEvent",
        "start": "2025-10-11T09:00:00Z",
        "end": "2025-10-11T10:00:00Z",
        "notes": "Test event"
    }
    
    result = await scheduling.create_event(**event_data)
    
    assert result["success"]
    assert "mvid" in result
    assert result["type"] == "ScheduledEvent"

@pytest.mark.asyncio
async def test_fetch_events_with_filter():
    """Test filtered event retrieval"""
    events = await scheduling.fetch_events_advanced(
        event_types=["ScheduledmPlan"],
        start_date="2025-10-01",
        end_date="2025-10-31"
    )
    
    assert isinstance(events, list)
    assert all(e["type"] == "ScheduledmPlan" for e in events)
```

## Configuration Management

```python
# config.py
from pydantic import BaseSettings

class CrossmarkConfig(BaseSettings):
    """Configuration for Crossmark MCP"""
    
    # API Settings
    api_base_url: str = "https://crossmark.mvretail.com/api"
    api_timeout: int = 30
    api_retry_attempts: int = 3
    
    # Database Settings
    db_path: str = "./crossmark_events.db"
    db_pool_size: int = 5
    
    # Cache Settings
    cache_ttl_seconds: int = 300
    cache_max_size: int = 1000
    
    # Sync Settings
    sync_interval_minutes: int = 15
    sync_batch_size: int = 100
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "./crossmark.log"
    
    class Config:
        env_prefix = "CROSSMARK_"
        env_file = ".env"

config = CrossmarkConfig()
```

## Documentation Improvements

Add comprehensive docstrings with examples:

```python
async def fetch_events(
    start_date: str,
    end_date: str,
    event_types: list[str] = None,
    rep_ids: list[str] = None
) -> list[dict]:
    """
    Fetch scheduled events from the Crossmark API.
    
    Args:
        start_date: ISO8601 start date (e.g., "2025-10-01T00:00:00Z")
        end_date: ISO8601 end date (e.g., "2025-10-31T23:59:59Z")
        event_types: Optional list of event types to filter by.
                     Valid values: ["ScheduledEvent", "ScheduledAvailability", 
                                   "ScheduledLocation", "ScheduledmPlan"]
        rep_ids: Optional list of rep MVIDs to filter by
    
    Returns:
        List of event dictionaries, each containing:
        - mvid: Unique identifier
        - type: Event type
        - data: Event-specific data including start, end, notes
        
    Raises:
        AuthenticationError: If session has expired
        CrossmarkAPIError: If API returns an error
        
    Example:
        >>> events = await fetch_events(
        ...     start_date="2025-10-01T00:00:00Z",
        ...     end_date="2025-10-31T23:59:59Z",
        ...     event_types=["ScheduledmPlan"],
        ...     rep_ids=["rep-12345"]
        ... )
        >>> print(f"Found {len(events)} events")
        Found 42 events
    """
    pass
```

## Summary

The current implementation is a good starting point, but adding these improvements will make it:

1. **More Complete** - Full CRUD operations instead of just reading
2. **More Reliable** - Better error handling and retry logic
3. **More Performant** - Caching and batch operations
4. **More Maintainable** - Type-safe models and better structure
5. **More Useful** - Analytics and advanced querying capabilities
6. **Production-Ready** - Proper testing, logging, and configuration

Would you like me to implement any of these specific improvements as working code examples?
