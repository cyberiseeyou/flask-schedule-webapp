# mcp_server_integration.py
"""
Example of how to integrate the improved Crossmark functionality
into your existing MCP server.

This shows how to add the new tools to your MCP server's tool list.
"""

from typing import Any
import os
from dotenv import load_dotenv

from crossmark_improvements import (
    CrossmarkAPIClient,
    EventDatabase,
    EventType,
    AuthenticationError,
    CrossmarkAPIError,
    NotFoundError,
    ValidationError
)

# Load environment variables
load_dotenv()

# Global instances
api_client: CrossmarkAPIClient = None
event_db: EventDatabase = None


# ============================================================================
# MCP TOOL FUNCTIONS
# ============================================================================

async def crossmark_authenticate(username: str, password: str) -> dict:
    """
    Authenticate with Crossmark API
    
    Args:
        username: Crossmark username
        password: Crossmark password
        
    Returns:
        {"success": bool, "message": str}
    """
    global api_client
    
    try:
        if api_client is None:
            api_client = CrossmarkAPIClient()
        
        await api_client.authenticate(username, password)
        
        return {
            "success": True,
            "message": "Successfully authenticated"
        }
    except AuthenticationError as e:
        return {
            "success": False,
            "message": f"Authentication failed: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


async def crossmark_get_session_status() -> dict:
    """
    Check if authenticated session is active
    
    Returns:
        {"authenticated": bool, "message": str}
    """
    global api_client
    
    if api_client is None:
        return {
            "authenticated": False,
            "message": "No session initialized"
        }
    
    is_auth = api_client.is_authenticated()
    
    return {
        "authenticated": is_auth,
        "message": "Session active" if is_auth else "Session expired or not authenticated"
    }


async def crossmark_fetch_events(
    start_date: str,
    end_date: str,
    event_type: str = None,
    save_to_db: bool = True
) -> dict:
    """
    Fetch events from Crossmark API
    
    Args:
        start_date: Start date in ISO8601 format
        end_date: End date in ISO8601 format
        event_type: Optional filter by event type (ScheduledEvent, ScheduledAvailability, etc.)
        save_to_db: Whether to save fetched events to local database
        
    Returns:
        {"success": bool, "events": list, "count": int}
    """
    global api_client, event_db
    
    try:
        if not api_client or not api_client.is_authenticated():
            return {
                "success": False,
                "message": "Not authenticated. Please call crossmark_authenticate first."
            }
        
        # Convert event type string to enum if provided
        event_type_enum = None
        if event_type:
            try:
                event_type_enum = EventType(event_type)
            except ValueError:
                return {
                    "success": False,
                    "message": f"Invalid event type. Must be one of: {[t.value for t in EventType]}"
                }
        
        # Fetch events
        events = await api_client.get_all_events(
            start_date=start_date,
            end_date=end_date,
            event_type=event_type_enum
        )
        
        # Save to database if requested
        if save_to_db:
            if event_db is None:
                event_db = EventDatabase()
            
            for event in events:
                event_db.save_event(event)
        
        # Convert events to dict format for MCP response
        events_data = [
            {
                "mvid": event.mvid,
                "type": event.event_type.value,
                "start": event.data.start,
                "end": event.data.end,
                "notes": event.data.notes,
                # Include type-specific fields
                **({
                    "rep_mvid": event.data.rep_mvid,
                    "rep_name": getattr(event.data, 'rep_name', '')
                } if hasattr(event.data, 'rep_mvid') else {}),
                **({
                    "location_mvid": event.data.location_mvid,
                    "location_name": getattr(event.data, 'location_name', '')
                } if hasattr(event.data, 'location_mvid') else {}),
                **({
                    "mplan_mvid": event.data.mplan_mvid,
                    "mplan_name": getattr(event.data, 'mplan_name', '')
                } if hasattr(event.data, 'mplan_mvid') else {})
            }
            for event in events
        ]
        
        return {
            "success": True,
            "count": len(events),
            "events": events_data,
            "saved_to_db": save_to_db
        }
        
    except CrossmarkAPIError as e:
        return {
            "success": False,
            "message": f"API error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


async def crossmark_create_event(
    event_type: str,
    start: str,
    end: str,
    notes: str = "",
    rep_mvid: str = None,
    location_mvid: str = None,
    mplan_mvid: str = None
) -> dict:
    """
    Create a new scheduled event
    
    Args:
        event_type: Type of event (ScheduledEvent, ScheduledAvailability, ScheduledLocation, ScheduledmPlan)
        start: Start timestamp in ISO8601 format
        end: End timestamp in ISO8601 format
        notes: Optional notes
        rep_mvid: Rep MVID (required for Availability, Location, mPlan events)
        location_mvid: Location MVID (required for Location and mPlan events)
        mplan_mvid: mPlan MVID (required for mPlan events)
        
    Returns:
        {"success": bool, "event": dict}
    """
    global api_client
    
    try:
        if not api_client or not api_client.is_authenticated():
            return {
                "success": False,
                "message": "Not authenticated. Please call crossmark_authenticate first."
            }
        
        # Convert event type string to enum
        try:
            event_type_enum = EventType(event_type)
        except ValueError:
            return {
                "success": False,
                "message": f"Invalid event type. Must be one of: {[t.value for t in EventType]}"
            }
        
        # Create event
        event = await api_client.create_event(
            event_type=event_type_enum,
            start=start,
            end=end,
            notes=notes,
            rep_mvid=rep_mvid,
            location_mvid=location_mvid,
            mplan_mvid=mplan_mvid
        )
        
        return {
            "success": True,
            "event": {
                "mvid": event.mvid,
                "type": event.event_type.value,
                "start": event.data.start,
                "end": event.data.end,
                "notes": event.data.notes
            },
            "message": f"Event created successfully: {event.mvid}"
        }
        
    except ValidationError as e:
        return {
            "success": False,
            "message": f"Validation error: {str(e)}"
        }
    except CrossmarkAPIError as e:
        return {
            "success": False,
            "message": f"API error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


async def crossmark_update_event(event_id: str, **updates) -> dict:
    """
    Update an existing scheduled event
    
    Args:
        event_id: MVID of the event to update
        **updates: Fields to update (start, end, notes, etc.)
        
    Returns:
        {"success": bool, "event": dict}
    """
    global api_client
    
    try:
        if not api_client or not api_client.is_authenticated():
            return {
                "success": False,
                "message": "Not authenticated. Please call crossmark_authenticate first."
            }
        
        # Update event
        event = await api_client.update_event(event_id, **updates)
        
        return {
            "success": True,
            "event": {
                "mvid": event.mvid,
                "type": event.event_type.value,
                "start": event.data.start,
                "end": event.data.end,
                "notes": event.data.notes
            },
            "message": f"Event updated successfully: {event_id}"
        }
        
    except NotFoundError as e:
        return {
            "success": False,
            "message": f"Event not found: {str(e)}"
        }
    except CrossmarkAPIError as e:
        return {
            "success": False,
            "message": f"API error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


async def crossmark_delete_event(event_id: str) -> dict:
    """
    Delete a scheduled event
    
    Args:
        event_id: MVID of the event to delete
        
    Returns:
        {"success": bool, "message": str}
    """
    global api_client
    
    try:
        if not api_client or not api_client.is_authenticated():
            return {
                "success": False,
                "message": "Not authenticated. Please call crossmark_authenticate first."
            }
        
        # Delete event
        await api_client.delete_event(event_id)
        
        return {
            "success": True,
            "message": f"Event deleted successfully: {event_id}"
        }
        
    except NotFoundError as e:
        return {
            "success": False,
            "message": f"Event not found: {str(e)}"
        }
    except CrossmarkAPIError as e:
        return {
            "success": False,
            "message": f"API error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


async def crossmark_query_events(
    event_type: str = None,
    start_date: str = None,
    end_date: str = None,
    rep_mvid: str = None,
    location_mvid: str = None,
    limit: int = 100
) -> dict:
    """
    Query events from local database
    
    Args:
        event_type: Filter by event type
        start_date: Filter events starting after this date
        end_date: Filter events ending before this date
        rep_mvid: Filter by rep MVID
        location_mvid: Filter by location MVID
        limit: Maximum results to return
        
    Returns:
        {"success": bool, "events": list, "count": int}
    """
    global event_db
    
    try:
        if event_db is None:
            event_db = EventDatabase()
        
        # Convert event type string to enum if provided
        event_type_enum = None
        if event_type:
            try:
                event_type_enum = EventType(event_type)
            except ValueError:
                return {
                    "success": False,
                    "message": f"Invalid event type. Must be one of: {[t.value for t in EventType]}"
                }
        
        # Query events
        events = event_db.query_events(
            event_type=event_type_enum,
            start_date=start_date,
            end_date=end_date,
            rep_mvid=rep_mvid,
            location_mvid=location_mvid,
            limit=limit
        )
        
        return {
            "success": True,
            "count": len(events),
            "events": events
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error querying database: {str(e)}"
        }


async def crossmark_sync_events(
    start_date: str,
    end_date: str,
    event_types: list = None
) -> dict:
    """
    Sync events between API and local database
    
    Args:
        start_date: Start date for sync range
        end_date: End date for sync range
        event_types: Optional list of event types to sync
        
    Returns:
        {"success": bool, "synced": int, "summary": dict}
    """
    global api_client, event_db
    
    try:
        if not api_client or not api_client.is_authenticated():
            return {
                "success": False,
                "message": "Not authenticated. Please call crossmark_authenticate first."
            }
        
        if event_db is None:
            event_db = EventDatabase()
        
        # Determine which event types to sync
        types_to_sync = event_types if event_types else [t.value for t in EventType]
        
        total_synced = 0
        summary = {}
        
        # Sync each event type
        for event_type_str in types_to_sync:
            try:
                event_type = EventType(event_type_str)
                
                # Fetch from API
                events = await api_client.get_all_events(
                    start_date=start_date,
                    end_date=end_date,
                    event_type=event_type
                )
                
                # Save to database
                for event in events:
                    event_db.save_event(event)
                
                summary[event_type.value] = len(events)
                total_synced += len(events)
                
            except ValueError:
                continue  # Skip invalid event types
        
        return {
            "success": True,
            "synced": total_synced,
            "summary": summary,
            "message": f"Successfully synced {total_synced} events"
        }
        
    except CrossmarkAPIError as e:
        return {
            "success": False,
            "message": f"API error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


# ============================================================================
# MCP SERVER TOOL DEFINITIONS
# ============================================================================

# Add these to your MCP server's tools list

CROSSMARK_TOOLS = [
    {
        "name": "crossmark_authenticate",
        "description": "Authenticate with Crossmark API using username and password",
        "parameters": {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "Crossmark username"
                },
                "password": {
                    "type": "string",
                    "description": "Crossmark password"
                }
            },
            "required": ["username", "password"]
        }
    },
    {
        "name": "crossmark_get_session_status",
        "description": "Check if authenticated session is active",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "crossmark_fetch_events",
        "description": "Fetch scheduled events from Crossmark API for a date range",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date in ISO8601 format (e.g., '2025-10-01T00:00:00Z')"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in ISO8601 format (e.g., '2025-10-31T23:59:59Z')"
                },
                "event_type": {
                    "type": "string",
                    "description": "Optional event type filter: ScheduledEvent, ScheduledAvailability, ScheduledLocation, or ScheduledmPlan"
                },
                "save_to_db": {
                    "type": "boolean",
                    "description": "Whether to save fetched events to local database (default: true)"
                }
            },
            "required": ["start_date", "end_date"]
        }
    },
    {
        "name": "crossmark_create_event",
        "description": "Create a new scheduled event in Crossmark",
        "parameters": {
            "type": "object",
            "properties": {
                "event_type": {
                    "type": "string",
                    "description": "Event type: ScheduledEvent, ScheduledAvailability, ScheduledLocation, or ScheduledmPlan"
                },
                "start": {
                    "type": "string",
                    "description": "Start timestamp in ISO8601 format"
                },
                "end": {
                    "type": "string",
                    "description": "End timestamp in ISO8601 format"
                },
                "notes": {
                    "type": "string",
                    "description": "Optional notes for the event"
                },
                "rep_mvid": {
                    "type": "string",
                    "description": "Rep MVID (required for Availability, Location, and mPlan events)"
                },
                "location_mvid": {
                    "type": "string",
                    "description": "Location MVID (required for Location and mPlan events)"
                },
                "mplan_mvid": {
                    "type": "string",
                    "description": "mPlan MVID (required for mPlan events)"
                }
            },
            "required": ["event_type", "start", "end"]
        }
    },
    {
        "name": "crossmark_update_event",
        "description": "Update an existing scheduled event",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "MVID of the event to update"
                },
                "start": {
                    "type": "string",
                    "description": "New start timestamp"
                },
                "end": {
                    "type": "string",
                    "description": "New end timestamp"
                },
                "notes": {
                    "type": "string",
                    "description": "Updated notes"
                }
            },
            "required": ["event_id"]
        }
    },
    {
        "name": "crossmark_delete_event",
        "description": "Delete a scheduled event",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "MVID of the event to delete"
                }
            },
            "required": ["event_id"]
        }
    },
    {
        "name": "crossmark_query_events",
        "description": "Query events from local database with flexible filtering",
        "parameters": {
            "type": "object",
            "properties": {
                "event_type": {
                    "type": "string",
                    "description": "Filter by event type"
                },
                "start_date": {
                    "type": "string",
                    "description": "Filter events starting after this date"
                },
                "end_date": {
                    "type": "string",
                    "description": "Filter events ending before this date"
                },
                "rep_mvid": {
                    "type": "string",
                    "description": "Filter by rep MVID"
                },
                "location_mvid": {
                    "type": "string",
                    "description": "Filter by location MVID"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results to return (default: 100)"
                }
            }
        }
    },
    {
        "name": "crossmark_sync_events",
        "description": "Sync events between API and local database for a date range",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date for sync range"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date for sync range"
                },
                "event_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of event types to sync"
                }
            },
            "required": ["start_date", "end_date"]
        }
    }
]


# ============================================================================
# EXAMPLE USAGE IN MCP SERVER
# ============================================================================

"""
To integrate into your existing MCP server:

1. Import this module:
   from mcp_server_integration import (
       crossmark_authenticate,
       crossmark_fetch_events,
       crossmark_create_event,
       crossmark_update_event,
       crossmark_delete_event,
       crossmark_query_events,
       crossmark_sync_events,
       crossmark_get_session_status,
       CROSSMARK_TOOLS
   )

2. Add tools to your MCP server's tool list:
   server.tools.extend(CROSSMARK_TOOLS)

3. Add tool handlers:
   @server.tool_handler("crossmark_authenticate")
   async def handle_authenticate(username: str, password: str):
       return await crossmark_authenticate(username, password)
   
   @server.tool_handler("crossmark_fetch_events")
   async def handle_fetch_events(start_date: str, end_date: str, ...):
       return await crossmark_fetch_events(start_date, end_date, ...)
   
   # ... add handlers for other tools
"""
