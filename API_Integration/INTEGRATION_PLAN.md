# Crossmark API Integration Plan - Hybrid Approach

## 🎯 Objective
Combine the best features from both implementations:
- **Production** (`session_api_service.py`): Proven authentication & comprehensive API coverage
- **API_Integration** (`crossmark_improvements.py`): Type safety & better architecture

---

## 📋 Phase 1: Add Type-Safe Models (Week 1)

### Step 1.1: Create `scheduler_app/crossmark_models.py`

```python
"""
Type-safe models for Crossmark API data structures
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List
from enum import Enum


class EventType(str, Enum):
    """Valid event types in Crossmark API"""
    SCHEDULED_EVENT = "ScheduledEvent"
    SCHEDULED_AVAILABILITY = "ScheduledAvailability"
    SCHEDULED_LOCATION = "ScheduledLocation"
    SCHEDULED_MPLAN = "ScheduledmPlan"


class EventCondition(str, Enum):
    """Event conditions/statuses"""
    UNSTAFFED = "Unstaffed"
    SCHEDULED = "Scheduled"
    STAFFED = "Staffed"
    CANCELED = "Canceled"
    IN_PROGRESS = "In Progress"
    PAUSED = "Paused"
    REISSUED = "Reissued"
    EXPIRED = "Expired"
    SUBMITTED = "Submitted"


@dataclass
class CrossmarkEvent:
    """Base class for Crossmark events"""
    id: str
    mplan_id: str
    location_id: str
    start_date: str
    end_date: str
    condition: EventCondition
    rep_ids: List[str] = None

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_api_response(cls, data: dict) -> 'CrossmarkEvent':
        """Parse API response into CrossmarkEvent"""
        return cls(
            id=data.get('id'),
            mplan_id=data.get('mPlanID'),
            location_id=data.get('storeID'),
            start_date=data.get('startDate'),
            end_date=data.get('endDate'),
            condition=EventCondition(data.get('condition', 'Unstaffed')),
            rep_ids=data.get('staffedReps', [])
        )


# Add more models as needed
```

### Step 1.2: Update `session_api_service.py`

Add import at top:
```python
from .crossmark_models import CrossmarkEvent, EventType, EventCondition
```

Update methods to return typed objects:
```python
def get_all_planning_events(self, ...) -> Optional[List[CrossmarkEvent]]:
    """..."""
    events_data = self._safe_json(response)
    if events_data and 'records' in events_data:
        return [CrossmarkEvent.from_api_response(record)
                for record in events_data['records']]
    return []
```

---

## 📋 Phase 2: Add Enhanced Exceptions (Week 1-2)

### Step 2.1: Create `scheduler_app/crossmark_exceptions.py`

```python
"""
Custom exceptions for Crossmark API operations
"""

class CrossmarkAPIError(Exception):
    """Base exception for Crossmark API errors"""
    def __init__(self, message: str, response=None):
        self.message = message
        self.response = response
        super().__init__(self.message)


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


class SchedulingConflictError(CrossmarkAPIError):
    """Scheduling conflict detected"""
    pass
```

### Step 2.2: Update exception handling in `session_api_service.py`

Replace:
```python
except Exception as e:
    self.logger.error(f"Error: {str(e)}")
    return None
```

With:
```python
from .crossmark_exceptions import (
    AuthenticationError, NotFoundError,
    ValidationError, CrossmarkAPIError
)

except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        raise AuthenticationError("Session expired", response=e.response)
    elif e.response.status_code == 404:
        raise NotFoundError(f"Resource not found", response=e.response)
    else:
        raise CrossmarkAPIError(f"API error: {str(e)}", response=e.response)
```

---

## 📋 Phase 3: Enhanced Database (Week 2-3)

### Step 3.1: Create `scheduler_app/crossmark_database.py`

```python
"""
Enhanced database operations for Crossmark events
"""
import sqlite3
from datetime import datetime
from typing import List, Optional
from .crossmark_models import CrossmarkEvent, EventType, EventCondition


class CrossmarkEventDatabase:
    """Database manager for Crossmark events with relational schema"""

    def __init__(self, db_path: str = "./data/crossmark_events.db"):
        self.db_path = db_path
        self._initialize_schema()

    def _initialize_schema(self):
        """Create enhanced relational schema"""
        conn = sqlite3.connect(self.db_path)

        # Main events table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS crossmark_events (
                id TEXT PRIMARY KEY,
                mplan_id TEXT NOT NULL,
                mplan_name TEXT,
                location_id TEXT NOT NULL,
                location_name TEXT,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                condition TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                synced_at TEXT,
                UNIQUE(mplan_id, location_id)
            )
        """)

        # Rep assignments (many-to-many)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS event_rep_assignments (
                event_id TEXT,
                rep_id TEXT,
                rep_name TEXT,
                assigned_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (event_id) REFERENCES crossmark_events(id),
                PRIMARY KEY (event_id, rep_id)
            )
        """)

        # Sync history
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sync_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_type TEXT,
                start_time TEXT,
                end_time TEXT,
                events_synced INTEGER,
                status TEXT,
                error_message TEXT
            )
        """)

        # Indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_condition ON crossmark_events(condition)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_dates ON crossmark_events(start_date, end_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_mplan ON crossmark_events(mplan_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_location ON crossmark_events(location_id)")

        conn.commit()
        conn.close()

    def save_event(self, event: CrossmarkEvent):
        """Save a Crossmark event to database"""
        conn = sqlite3.connect(self.db_path)

        try:
            # Insert or update main event
            conn.execute("""
                INSERT OR REPLACE INTO crossmark_events
                (id, mplan_id, location_id, start_date, end_date, condition, updated_at, synced_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.id,
                event.mplan_id,
                event.location_id,
                event.start_date,
                event.end_date,
                event.condition.value,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

            # Save rep assignments
            if event.rep_ids:
                # Clear existing assignments
                conn.execute("DELETE FROM event_rep_assignments WHERE event_id = ?", (event.id,))

                # Insert new assignments
                for rep_id in event.rep_ids:
                    conn.execute("""
                        INSERT INTO event_rep_assignments (event_id, rep_id)
                        VALUES (?, ?)
                    """, (event.id, rep_id))

            conn.commit()

        finally:
            conn.close()

    def save_events_bulk(self, events: List[CrossmarkEvent]):
        """Bulk save events for efficiency"""
        conn = sqlite3.connect(self.db_path)

        try:
            for event in events:
                conn.execute("""
                    INSERT OR REPLACE INTO crossmark_events
                    (id, mplan_id, location_id, start_date, end_date, condition, updated_at, synced_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.id, event.mplan_id, event.location_id,
                    event.start_date, event.end_date, event.condition.value,
                    datetime.now().isoformat(), datetime.now().isoformat()
                ))

            conn.commit()

        finally:
            conn.close()

    def query_events(
        self,
        condition: Optional[EventCondition] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        mplan_id: Optional[str] = None,
        location_id: Optional[str] = None,
        rep_id: Optional[str] = None,
        limit: int = 100
    ) -> List[dict]:
        """Query events with flexible filtering"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        query = "SELECT * FROM crossmark_events WHERE 1=1"
        params = []

        if condition:
            query += " AND condition = ?"
            params.append(condition.value)

        if start_date:
            query += " AND start_date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND end_date <= ?"
            params.append(end_date)

        if mplan_id:
            query += " AND mplan_id = ?"
            params.append(mplan_id)

        if location_id:
            query += " AND location_id = ?"
            params.append(location_id)

        if rep_id:
            query += " AND id IN (SELECT event_id FROM event_rep_assignments WHERE rep_id = ?)"
            params.append(rep_id)

        query += " ORDER BY start_date LIMIT ?"
        params.append(limit)

        cursor = conn.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results
```

---

## 📋 Phase 4: Integration Testing (Week 3-4)

### Step 4.1: Create comprehensive integration tests

```python
# scheduler_app/tests/test_crossmark_integration.py
import pytest
from scheduler_app.session_api_service import SessionAPIService
from scheduler_app.crossmark_database import CrossmarkEventDatabase
from scheduler_app.crossmark_models import CrossmarkEvent, EventCondition

def test_authentication():
    """Test that authentication works"""
    service = SessionAPIService()
    # Configure service
    assert service.login() == True

def test_fetch_and_store():
    """Test fetching events and storing in database"""
    service = SessionAPIService()
    db = CrossmarkEventDatabase()

    service.login()
    events = service.get_all_planning_events()

    # Should return typed objects now
    assert all(isinstance(e, CrossmarkEvent) for e in events)

    # Save to database
    for event in events:
        db.save_event(event)

    # Query back from database
    stored_events = db.query_events(condition=EventCondition.UNSTAFFED)
    assert len(stored_events) > 0
```

---

## 📋 Phase 5: Gradual Rollout (Week 4-5)

### Step 5.1: Update route handlers

```python
# scheduler_app/routes/edr_sync.py

from scheduler_app.crossmark_models import CrossmarkEvent, EventCondition
from scheduler_app.crossmark_exceptions import AuthenticationError, CrossmarkAPIError
from scheduler_app.crossmark_database import CrossmarkEventDatabase

@bp.route('/sync/crossmark', methods=['POST'])
def sync_crossmark_events():
    """Sync events from Crossmark API"""
    try:
        db = CrossmarkEventDatabase()

        # Use session_api which now returns typed objects
        events = session_api.get_all_planning_events()

        # Save to enhanced database
        db.save_events_bulk(events)

        return jsonify({
            'success': True,
            'events_synced': len(events)
        })

    except AuthenticationError as e:
        return jsonify({
            'success': False,
            'error': 'Authentication failed'
        }), 401

    except CrossmarkAPIError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

---

## ✅ Testing Checklist

- [ ] Run `test_comparison.py` to understand current state
- [ ] Test authentication with both implementations
- [ ] Create `crossmark_models.py` with type-safe models
- [ ] Create `crossmark_exceptions.py` with custom exceptions
- [ ] Create `crossmark_database.py` with enhanced schema
- [ ] Update `session_api_service.py` to use new models
- [ ] Write integration tests
- [ ] Update route handlers to use typed objects
- [ ] Test end-to-end sync workflow
- [ ] Monitor production for issues
- [ ] Document new architecture

---

## 🎓 Benefits of Hybrid Approach

1. **Type Safety**: Catch errors at development time
2. **Better Architecture**: Separation of concerns
3. **Enhanced Database**: Relational schema for complex queries
4. **Maintainability**: Clear data models and exceptions
5. **Proven Foundation**: Keep working authentication & API methods
6. **Gradual Migration**: No big-bang rewrite risk

---

## ⚠️ What NOT To Do

- ❌ Don't replace `session_api_service.py` entirely
- ❌ Don't throw away proven authentication code
- ❌ Don't migrate everything at once
- ❌ Don't skip testing phases
- ❌ Don't forget to backup database before schema changes

---

## 📞 Questions for Product Owner

1. What's the timeline for this integration?
2. Can we do a phased rollout?
3. What's the priority: type safety or new features?
4. Do we need backward compatibility with old database?
5. What's the acceptance criteria for each phase?
