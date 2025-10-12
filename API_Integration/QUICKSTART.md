# Crossmark API Integration Quick-Start Guide

## Overview

This guide helps you integrate the improved Crossmark API functionality into your existing MCP server.

## Installation

```bash
# Install required dependencies
pip install httpx python-dateutil

# For development/testing
pip install pytest pytest-asyncio
```

## Quick Integration Steps

### Step 1: Update Your Existing MCP Server

If you have an existing `crossmark_mcp_server.py`, add these imports:

```python
from crossmark_improvements import (
    CrossmarkAPIClient,
    EventDatabase,
    EventType,
    ScheduledEvent,
    AuthenticationError,
    CrossmarkAPIError
)
```

### Step 2: Replace Basic Functions with Enhanced Versions

Replace your current authentication:

```python
# OLD WAY
async def authenticate(username: str, password: str):
    # Basic auth logic
    pass

# NEW WAY - with better error handling and session management
client = CrossmarkAPIClient()
await client.authenticate(username, password)
```

### Step 3: Add Full CRUD Support

```python
# CREATE - New event
new_event = await client.create_event(
    event_type=EventType.SCHEDULED_MPLAN,
    start="2025-10-15T09:00:00Z",
    end="2025-10-15T11:00:00Z",
    notes="Complete shelf reset",
    rep_mvid="156728",  # Your rep ID
    location_mvid="store-001",
    mplan_mvid="mplan-seasonal-reset"
)

# READ - Get specific event
event = await client.get_event(event_id="evt-12345")

# READ - Get filtered events
events = await client.get_all_events(
    start_date="2025-10-01T00:00:00Z",
    end_date="2025-10-31T23:59:59Z",
    event_type=EventType.SCHEDULED_MPLAN
)

# UPDATE - Modify event
updated = await client.update_event(
    event_id="evt-12345",
    notes="Updated notes",
    end="2025-10-15T12:00:00Z"  # Extended by 1 hour
)

# DELETE - Remove event
success = await client.delete_event(event_id="evt-12345")
```

## Common Use Cases

### Use Case 1: Sync Rep Schedule

```python
async def sync_rep_schedule(rep_id: str, days_ahead: int = 30):
    """
    Synchronize a rep's schedule from the API to local database
    """
    client = CrossmarkAPIClient()
    db = EventDatabase()
    
    # Authenticate
    await client.authenticate(
        os.getenv("CROSSMARK_USERNAME"),
        os.getenv("CROSSMARK_PASSWORD")
    )
    
    # Calculate date range
    from datetime import datetime, timedelta
    start = datetime.now()
    end = start + timedelta(days=days_ahead)
    
    # Fetch all event types for this rep
    for event_type in EventType:
        events = await client.get_all_events(
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            event_type=event_type
        )
        
        # Filter for specific rep (if applicable)
        rep_events = [
            e for e in events 
            if hasattr(e.data, 'rep_mvid') and e.data.rep_mvid == rep_id
        ]
        
        # Save to database
        for event in rep_events:
            db.save_event(event)
        
        print(f"Synced {len(rep_events)} {event_type.value} events")
    
    await client.close()
    return True

# Usage
await sync_rep_schedule("156728", days_ahead=30)
```

### Use Case 2: Create Bulk Work Schedule

```python
async def schedule_weekly_visits(
    rep_id: str,
    locations: List[str],  # List of location MVIDs
    week_start: str
):
    """
    Schedule a rep to visit multiple locations during a week
    """
    client = CrossmarkAPIClient()
    await client.authenticate(
        os.getenv("CROSSMARK_USERNAME"),
        os.getenv("CROSSMARK_PASSWORD")
    )
    
    from datetime import datetime, timedelta
    
    start_date = datetime.fromisoformat(week_start)
    
    events_to_create = []
    for i, location_id in enumerate(locations):
        # Schedule 2-hour visits, one per day
        visit_start = start_date + timedelta(days=i, hours=9)
        visit_end = visit_start + timedelta(hours=2)
        
        events_to_create.append({
            "Type": EventType.SCHEDULED_LOCATION.value,
            "Data": {
                "start": visit_start.isoformat() + "Z",
                "end": visit_end.isoformat() + "Z",
                "notes": f"Weekly visit to {location_id}",
                "rep_mvid": rep_id,
                "location_mvid": location_id
            }
        })
    
    # Create all events in batch
    result = await client.batch_create_events(events_to_create)
    
    print(f"Created {len(result['created'])} events")
    print(f"Failed: {len(result['failed'])} events")
    
    await client.close()
    return result

# Usage
await schedule_weekly_visits(
    rep_id="156728",
    locations=["loc-001", "loc-002", "loc-003", "loc-004", "loc-005"],
    week_start="2025-10-13"
)
```

### Use Case 3: Find Schedule Conflicts

```python
async def find_scheduling_conflicts(rep_id: str, date_range: tuple):
    """
    Find overlapping events in a rep's schedule
    """
    db = EventDatabase()
    
    # Get all events for the rep in the date range
    events = db.query_events(
        rep_mvid=rep_id,
        start_date=date_range[0],
        end_date=date_range[1]
    )
    
    # Sort by start time
    events.sort(key=lambda e: e['start_time'])
    
    # Find overlaps
    conflicts = []
    for i in range(len(events) - 1):
        current_end = datetime.fromisoformat(events[i]['end_time'])
        next_start = datetime.fromisoformat(events[i+1]['start_time'])
        
        if next_start < current_end:
            conflicts.append({
                "event1": events[i],
                "event2": events[i+1],
                "overlap_minutes": (current_end - next_start).total_seconds() / 60
            })
    
    return conflicts

# Usage
conflicts = await find_scheduling_conflicts(
    rep_id="156728",
    date_range=("2025-10-01", "2025-10-31")
)

if conflicts:
    print(f"Found {len(conflicts)} scheduling conflicts:")
    for conflict in conflicts:
        print(f"  - {conflict['event1']['mvid']} overlaps with {conflict['event2']['mvid']}")
        print(f"    Overlap: {conflict['overlap_minutes']:.0f} minutes")
```

### Use Case 4: Generate Weekly Report

```python
async def generate_weekly_report(rep_id: str, week_start: str):
    """
    Generate a report of completed work for a week
    """
    from datetime import datetime, timedelta
    
    db = EventDatabase()
    client = CrossmarkAPIClient()
    
    await client.authenticate(
        os.getenv("CROSSMARK_USERNAME"),
        os.getenv("CROSSMARK_PASSWORD")
    )
    
    # Calculate week dates
    start = datetime.fromisoformat(week_start)
    end = start + timedelta(days=7)
    
    # Get events from API (freshest data)
    events = await client.get_all_events(
        start_date=start.isoformat() + "Z",
        end_date=end.isoformat() + "Z"
    )
    
    # Filter for this rep
    rep_events = [
        e for e in events 
        if hasattr(e.data, 'rep_mvid') and e.data.rep_mvid == rep_id
    ]
    
    # Categorize by type
    report = {
        "week": week_start,
        "rep_id": rep_id,
        "summary": {
            "total_events": len(rep_events),
            "by_type": {}
        },
        "details": []
    }
    
    for event_type in EventType:
        type_events = [e for e in rep_events if e.event_type == event_type]
        report["summary"]["by_type"][event_type.value] = len(type_events)
        
        # Calculate total hours
        total_hours = sum([
            (datetime.fromisoformat(e.data.end.rstrip('Z')) - 
             datetime.fromisoformat(e.data.start.rstrip('Z'))).total_seconds() / 3600
            for e in type_events
        ])
        
        if type_events:
            report["details"].append({
                "type": event_type.value,
                "count": len(type_events),
                "total_hours": round(total_hours, 2),
                "events": [
                    {
                        "mvid": e.mvid,
                        "start": e.data.start,
                        "end": e.data.end,
                        "location": getattr(e.data, 'location_name', 'N/A')
                    }
                    for e in type_events
                ]
            })
    
    await client.close()
    
    # Save report
    import json
    report_file = f"report_{rep_id}_{week_start}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Report saved to {report_file}")
    return report

# Usage
report = await generate_weekly_report(
    rep_id="156728",
    week_start="2025-10-06"
)

print(f"\nWeek of {report['week']}:")
print(f"Total events: {report['summary']['total_events']}")
for event_type, count in report['summary']['by_type'].items():
    print(f"  {event_type}: {count}")
```

### Use Case 5: Reschedule Due to Conflict

```python
async def reschedule_event(
    event_id: str,
    new_start: str,
    reason: str
):
    """
    Reschedule an event and update notes with reason
    """
    client = CrossmarkAPIClient()
    
    await client.authenticate(
        os.getenv("CROSSMARK_USERNAME"),
        os.getenv("CROSSMARK_PASSWORD")
    )
    
    # Get current event
    event = await client.get_event(event_id)
    
    # Calculate new end time (preserve duration)
    from datetime import datetime
    old_start = datetime.fromisoformat(event.data.start.rstrip('Z'))
    old_end = datetime.fromisoformat(event.data.end.rstrip('Z'))
    duration = old_end - old_start
    
    new_start_dt = datetime.fromisoformat(new_start.rstrip('Z'))
    new_end_dt = new_start_dt + duration
    
    # Update with reason in notes
    updated_notes = f"{event.data.notes}\n\nRescheduled: {reason}"
    
    updated_event = await client.update_event(
        event_id,
        start=new_start_dt.isoformat() + "Z",
        end=new_end_dt.isoformat() + "Z",
        notes=updated_notes
    )
    
    await client.close()
    
    print(f"Event {event_id} rescheduled from {event.data.start} to {new_start}")
    return updated_event

# Usage
await reschedule_event(
    event_id="evt-12345",
    new_start="2025-10-16T10:00:00Z",
    reason="Store requested different time"
)
```

## Error Handling Best Practices

```python
async def safe_api_operation():
    """Example of proper error handling"""
    client = CrossmarkAPIClient()
    
    try:
        # Try to authenticate
        await client.authenticate(username, password)
        
        # Perform operations
        events = await client.get_all_events()
        
    except AuthenticationError as e:
        print(f"Authentication failed: {e}")
        print("Please check your credentials")
        return None
        
    except NotFoundError as e:
        print(f"Resource not found: {e}")
        return None
        
    except RateLimitError as e:
        print(f"Rate limit exceeded: {e}")
        print("Waiting 60 seconds before retry...")
        await asyncio.sleep(60)
        # Retry logic here
        
    except CrossmarkAPIError as e:
        print(f"API error: {e}")
        return None
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
        
    finally:
        # Always close the client
        await client.close()
    
    return events
```

## Environment Configuration

Create a `.env` file:

```bash
# Crossmark API Configuration
CROSSMARK_USERNAME=your_username
CROSSMARK_PASSWORD=your_password
CROSSMARK_BASE_URL=https://crossmark.mvretail.com/api
CROSSMARK_TIMEOUT=30

# Database
CROSSMARK_DB_PATH=./crossmark_events.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=./crossmark.log
```

Load in your code:

```python
from dotenv import load_dotenv
import os

load_dotenv()

client = CrossmarkAPIClient(
    base_url=os.getenv("CROSSMARK_BASE_URL"),
    timeout=int(os.getenv("CROSSMARK_TIMEOUT", 30))
)
```

## Testing

Create `test_crossmark.py`:

```python
import pytest
from crossmark_improvements import CrossmarkAPIClient, EventType

@pytest.mark.asyncio
async def test_authenticate():
    """Test authentication"""
    client = CrossmarkAPIClient()
    
    # Should fail with bad credentials
    with pytest.raises(AuthenticationError):
        await client.authenticate("bad_user", "bad_pass")
    
    await client.close()

@pytest.mark.asyncio
async def test_create_event():
    """Test event creation"""
    client = CrossmarkAPIClient()
    
    # Authenticate with valid credentials
    await client.authenticate(
        os.getenv("TEST_USERNAME"),
        os.getenv("TEST_PASSWORD")
    )
    
    # Create test event
    event = await client.create_event(
        event_type=EventType.SCHEDULED_EVENT,
        start="2025-12-01T10:00:00Z",
        end="2025-12-01T11:00:00Z",
        notes="Test event - please delete"
    )
    
    assert event.mvid is not None
    assert event.event_type == EventType.SCHEDULED_EVENT
    
    # Clean up
    await client.delete_event(event.mvid)
    await client.close()

# Run tests
# pytest test_crossmark.py -v
```

## Performance Tips

1. **Batch Operations**: Use `batch_create_events()` for creating multiple events
2. **Caching**: Store frequently accessed events in the local database
3. **Pagination**: When fetching large datasets, use date ranges to limit results
4. **Connection Pooling**: Reuse the same `CrossmarkAPIClient` instance when possible

```python
# GOOD - Reuse client
client = CrossmarkAPIClient()
await client.authenticate(username, password)

for date_range in date_ranges:
    events = await client.get_all_events(**date_range)
    # Process events

await client.close()

# BAD - Creating new client each time
for date_range in date_ranges:
    client = CrossmarkAPIClient()
    await client.authenticate(username, password)
    events = await client.get_all_events(**date_range)
    await client.close()  # Inefficient
```

## Next Steps

1. ✅ Review the `crossmark_improvements.py` file
2. ✅ Test authentication with your credentials
3. ✅ Try creating a simple event
4. ✅ Integrate the enhanced database schema
5. ✅ Implement one of the use cases above
6. ✅ Add proper logging and error handling
7. ✅ Write tests for your specific use cases

## Additional Resources

- API Documentation: https://crossmark.mvretail.com/apidocs/
- MVID System Guide: See API docs for details on unique identifiers
- Event Types Reference: See `EventType` enum in `crossmark_improvements.py`

## Getting Help

If you encounter issues:

1. Check the API documentation
2. Verify your authentication credentials
3. Review error messages in logs
4. Check for scheduling conflicts in the database
5. Ensure date/time formats are ISO8601 compliant

## Support

For questions about this implementation, refer to:
- `crossmark_api_analysis.md` for detailed analysis
- `crossmark_improvements.py` for code examples
- This guide for practical usage patterns
