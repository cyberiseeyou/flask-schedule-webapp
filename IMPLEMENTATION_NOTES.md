# Implementation Notes - Calendar Redesign Sprint 2

**Date:** 2025-10-12
**Status:** Sprint 2 Implementation Started - Schema Differences Identified

---

## 🔍 Schema & Implementation Differences

During Sprint 2 kickoff, I discovered significant differences between the QA test plan assumptions and the actual codebase implementation.

### Database Schema Differences

**QA Test Plan Assumed:**
```sql
events (
    event_id INT PRIMARY KEY,
    project_name TEXT,
    event_type VARCHAR,
    condition VARCHAR,
    is_scheduled BOOLEAN,
    estimated_hours FLOAT,
    start_datetime DATETIME,
    due_datetime DATETIME
)

schedule (
    schedule_id INT PRIMARY KEY,
    event_id INT FOREIGN KEY,
    employee_id INT,
    start_datetime DATETIME
)
```

**Actual Schema:**
```sql
events (
    id INT PRIMARY KEY AUTOINCREMENT,
    project_ref_num INT UNIQUE NOT NULL,    -- ⚠️ Different identifier!
    project_name TEXT,
    event_type VARCHAR(20),
    condition VARCHAR(20),
    is_scheduled BOOLEAN,
    estimated_time INT,                     -- ⚠️ Minutes, not hours!
    start_datetime DATETIME,
    due_datetime DATETIME,
    external_id VARCHAR(100),               -- ⚠️ Crossmark API integration
    last_synced DATETIME,
    sync_status VARCHAR(20),
    parent_event_ref_num INT                -- ⚠️ For supervisor links
)

schedule (
    id INT PRIMARY KEY,
    event_ref_num INT,                      -- ⚠️ Links to project_ref_num!
    employee_id INT,
    schedule_datetime DATETIME,
    external_id VARCHAR(100)                -- ⚠️ Crossmark API integration
)
```

### API Integration Complexity

**Discovery:** The codebase already has extensive integration with **Crossmark API** for:
- Scheduling events (`schedule_mplan_event`)
- Unscheduling events (`unschedule_mplan_event`)
- Authentication (`ensure_authenticated`)

**Impact:**
- Every reschedule/unschedule operation must call Crossmark API BEFORE updating local database
- If API call fails, local database is not updated (rollback)
- This adds complexity to transaction handling

**Current Endpoints:**
1. `/api/reschedule` (line 276 in api.py) - JSON/FormData handler
2. `/api/reschedule_event` (line 414 in api.py) - Similar functionality
3. `/api/unschedule/<schedule_id>` (line 133 in api.py) - DELETE method

---

## ✅ What Was Completed

### 1. Helper Functions (COMPLETED)

Added CORE-Supervisor pairing functions to `scheduler_app/utils/event_helpers.py`:

- ✅ `get_supervisor_event(core_event)` - Find paired Supervisor
- ✅ `get_supervisor_status(core_event)` - Get detailed status
- ✅ `is_core_event_redesign(event)` - Check if CORE event (by project_name)
- ✅ `is_supervisor_event(event)` - Check if Supervisor event
- ✅ `validate_event_pairing(core, supervisor)` - Validate pairing

**Note:** Functions use regex to extract 6-digit event number from project_name (e.g., "606001-CORE-Product" → "606001-Supervisor-Product")

---

## 🔄 Adapted Implementation Strategy

Given the schema differences and API integration, here's the adapted approach:

### Phase 1: Test Data Adaptation (IMMEDIATE)

**Problem:** Test data in `test_data/sprint1_minimal_testdata.sql` uses incompatible schema.

**Solution:** Create adapted test data that matches actual schema:

```sql
-- ADAPTED: Uses project_ref_num instead of event_id
INSERT INTO events (
    id,
    project_ref_num,     -- Changed from event_id
    project_name,
    event_type,
    condition,
    is_scheduled,
    estimated_time,       -- Changed from estimated_hours (minutes not hours)
    start_datetime,
    due_datetime,
    external_id,          -- Added for Crossmark integration
    sync_status           -- Added for Crossmark integration
) VALUES
(1001, 606001, '606001-CORE-Super Pretzel', 'Core', 'Scheduled', TRUE, 390, '2025-10-15 10:00:00', '2025-10-15', 'CM_606001', 'synced'),
(1002, 606002, '606001-Supervisor-Super Pretzel', 'Supervisor', 'Scheduled', TRUE, 5, '2025-10-15 12:00:00', '2025-10-15', 'CM_606002', 'synced');

INSERT INTO schedule (
    id,
    event_ref_num,        -- Changed from event_id
    employee_id,
    schedule_datetime     -- Changed from start_datetime
) VALUES
(2001, 606001, 101, '2025-10-15 10:00:00'),
(2002, 606002, 102, '2025-10-15 12:00:00');
```

### Phase 2: Transaction Handling (NEXT)

**Challenge:** Must integrate with existing Crossmark API calls.

**Strategy:** Wrap entire operation (API call + database update) in try/except with rollback:

```python
@api_bp.route('/reschedule', methods=['POST'])
def reschedule():
    try:
        # BEGIN NESTED TRANSACTION
        with db.session.begin_nested():  # Savepoint
            # 1. Call Crossmark API first (existing code)
            api_result = external_api.schedule_mplan_event(...)

            if not api_result.get('success'):
                raise Exception(f"API failed: {api_result.get('message')}")

            # 2. Update CORE event in local database
            schedule.schedule_datetime = new_datetime

            # 3. NEW: Check if CORE event and reschedule Supervisor
            if is_core_event_redesign(event):
                supervisor = get_supervisor_event(event)
                if supervisor and supervisor.condition == 'Scheduled':
                    supervisor_schedule = Schedule.query.filter_by(
                        event_ref_num=supervisor.project_ref_num
                    ).first()

                    if supervisor_schedule:
                        # Calculate supervisor time (2 hours after CORE)
                        supervisor_datetime = new_datetime + timedelta(hours=2)

                        # Call API for supervisor too
                        supervisor_api_result = external_api.schedule_mplan_event(
                            rep_id=supervisor_schedule.employee_id,
                            ...
                        )

                        if not supervisor_api_result.get('success'):
                            raise Exception("Supervisor API call failed")

                        # Update supervisor schedule
                        supervisor_schedule.schedule_datetime = supervisor_datetime

                        logger.info(f"✅ Auto-rescheduled Supervisor {supervisor.project_ref_num}")

        # COMMIT TRANSACTION
        db.session.commit()
        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Reschedule failed: {e}")
        return jsonify({'error': str(e)}), 500
```

### Phase 3: Unschedule Handling (AFTER RESCHEDULE)

Similar approach for unschedule endpoint - wrap API call + database deletes in transaction.

---

## 🚧 Blockers & Decisions Needed

### Blocker 1: Test Data Incompatibility

**Issue:** QA test data doesn't match actual schema.

**Options:**
1. ✅ **RECOMMENDED**: Create adapted test data matching actual schema
2. ❌ Modify schema to match test data (risky, breaks existing functionality)

**Decision:** Proceed with Option 1 (adapted test data).

### Blocker 2: Crossmark API Integration

**Issue:** Cannot fully test without Crossmark API credentials or mock.

**Options:**
1. ✅ **RECOMMENDED**: Create mock Crossmark API for testing
2. Test only with actual API (requires credentials)
3. Skip API integration testing (not recommended)

**Decision:** Create mock API service for testing.

### Blocker 3: Supervisor API Calls

**Issue:** Supervisor events may also need Crossmark API calls when rescheduled.

**Question:** Should we call Crossmark API for both CORE and Supervisor?

**Implications:**
- If YES: 2x API calls per reschedule (slower, but maintains sync)
- If NO: Supervisor may be out of sync with external system

**Recommendation:** YES - call API for both to maintain sync.

---

## 📋 Updated Task List

### Week 1 - Sprint 2

**Day 1:**
- [x] Create helper functions for CORE-Supervisor pairing
- [ ] Create adapted test data matching actual schema
- [ ] Create mock Crossmark API service
- [ ] Update reschedule endpoint with CORE-Supervisor logic
- [ ] Test reschedule with mocked API

**Day 2:**
- [ ] Update unschedule endpoint with CORE-Supervisor logic
- [ ] Test unschedule with mocked API
- [ ] Add database indexes
- [ ] Configure structured logging

**Day 3-4:**
- [ ] Execute critical tests with adapted test data
- [ ] Document test results

**Day 5:**
- [ ] Code review
- [ ] Update documentation
- [ ] Tag release

---

## 🔧 Technical Notes

### Regex Pattern for Event Matching

The helper functions use this regex to extract event numbers:

```python
# Extract 6-digit event number from CORE event
match = re.search(r'(\d{6})-CORE-', core_event.project_name, re.IGNORECASE)
event_number = match.group(1)  # e.g., "606001"

# Find matching Supervisor
supervisor_event = Event.query.filter(
    Event.project_name.ilike(f'{event_number}-Supervisor-%')
).first()
```

**Works with:**
- `"606001-CORE-Super Pretzel"` → `"606001-Supervisor-Super Pretzel"`
- `"606001-core-Lowercase"` → `"606001-supervisor-Lowercase"` (case-insensitive)

**Fails gracefully with:**
- `"ABC123-CORE-Invalid"` → Returns None (logged as warning)
- `"No-Number-CORE-Event"` → Returns None

### External API Integration Points

All API calls go through `session_api_service.py`:

1. **Authentication:** `external_api.ensure_authenticated()`
2. **Schedule Event:** `external_api.schedule_mplan_event(rep_id, mplan_id, location_id, start_datetime, end_datetime, planning_override=True)`
3. **Unschedule Event:** `external_api.unschedule_mplan_event(schedule_external_id)`

**Required Fields:**
- `rep_id`: Employee external_id (Crossmark employee ID)
- `mplan_id`: Event external_id (Crossmark event ID)
- `location_id`: Event location_mvid (Crossmark location ID)

**Error Handling:**
- API returns `{'success': bool, 'message': str}`
- If `success=False`, rollback local changes
- Log all API errors with context

---

## 🎯 Success Criteria (Adapted)

### Sprint 2 Week 1 Exit Criteria

- [ ] Helper functions tested with actual schema
- [ ] Adapted test data created and validated
- [ ] Mock API service created for testing
- [ ] Reschedule endpoint updated with CORE-Supervisor pairing
- [ ] Unschedule endpoint updated with CORE-Supervisor pairing
- [ ] Transaction handling tested (rollback scenarios)
- [ ] Database indexes added
- [ ] Structured logging configured
- [ ] Critical tests passing (TC-033, TC-036, TC-041)

### Definition of Done

A CORE-Supervisor pair reschedule is successful when:
1. ✅ Crossmark API called successfully for CORE event
2. ✅ Crossmark API called successfully for Supervisor event (if scheduled)
3. ✅ CORE schedule updated in local database
4. ✅ Supervisor schedule updated in local database (if scheduled)
5. ✅ Both events have same date (but different times)
6. ✅ Transaction committed
7. ✅ Audit log entry created
8. ✅ No orphaned events (verified by queries)

If ANY step fails → ROLLBACK entire transaction.

---

## 📝 Next Steps

1. **IMMEDIATE:** Create adapted test data SQL script
2. **NEXT:** Create mock Crossmark API service for testing
3. **THEN:** Update reschedule endpoint with CORE-Supervisor logic
4. **FINALLY:** Test and validate

**Estimated Time:** 2-3 days for Phase 1-2 (assuming no API credential issues)

---

## 🤝 Questions for Team

1. **API Credentials:** Do we have test/staging Crossmark API credentials?
2. **Supervisor API Calls:** Confirmed - should we call API for Supervisor events too?
3. **Schema Migration:** Is there a migration system in place (Flask-Migrate, Alembic)?
4. **Testing Strategy:** Should we test against staging database or local SQLite?

---

**Last Updated:** 2025-10-12
**Author:** Development Team
**Status:** In Progress - Phase 1
