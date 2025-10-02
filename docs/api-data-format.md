# Crossmark API Data Format Requirements

**Date:** 2025-10-01
**Updates:** Corrected employee ID format and added validation for required API fields

---

## Overview

The auto-scheduler submits approved schedules to the Crossmark API. This document describes the required data format and validation rules.

---

## Employee ID Format

### ❌ **INCORRECT:**
```python
rep_id = employee.id  # "US815021" format - NOT accepted by API
```

### ✅ **CORRECT:**
```python
rep_id = employee.external_id  # Numeric ID from Crossmark API (e.g., "815021")
```

### Database Fields:
- `employee.id` (Primary Key): Local identifier in "US######" format (e.g., "US815021")
- `employee.external_id`: Numeric ID from Crossmark API (e.g., "815021")

**Why:** The Crossmark API expects the numeric employee ID (`external_id`), not the local "US######" format.

---

## Event ID Format

### ❌ **INCORRECT:**
```python
mplan_id = str(event.project_ref_num)  # Local reference number
```

### ✅ **CORRECT:**
```python
mplan_id = event.external_id  # mPlan ID from Crossmark API
```

### Database Fields:
- `event.project_ref_num` (Primary Key): Local project reference number
- `event.external_id`: mPlan ID from Crossmark API

**Why:** The Crossmark API scheduling endpoint expects the `mPlanID` from their system, not our local reference number.

---

## Required API Fields Validation

Before submitting to Crossmark API, the following fields are validated:

1. **rep_id** (employee.external_id)
   - Must not be NULL or empty
   - Failure reason: "Missing external_id for employee {name} ({id})"

2. **mplan_id** (event.external_id)
   - Must not be NULL or empty
   - Failure reason: "Missing external_id for event"

3. **location_id** (event.location_mvid)
   - Must not be NULL or empty
   - Failure reason: "Missing location_mvid for event"

If any required field is missing, the schedule is marked as `api_failed` and details are logged.

---

## API Request Format

**Endpoint:** `/planningextcontroller/scheduleMplanEvent`

**Method:** POST

**Content-Type:** `application/x-www-form-urlencoded`

**Form Data:**
```
ClassName=MVScheduledmPlan
RepID={employee.external_id}
mPlanID={event.external_id}
LocationID={event.location_mvid}
Start={start_datetime in format: YYYY-MM-DDTHH:MM:SS-04:00}
End={end_datetime in format: YYYY-MM-DDTHH:MM:SS-04:00}
hash=
v=3.0.1
PlanningOverride=true
```

### DateTime Format:
- Format: `YYYY-MM-DDTHH:MM:SS-04:00`
- Example: `2025-10-16T09:00:00-04:00`
- Timezone: Eastern Time (UTC-4)

---

## Code Location

**File:** `scheduler_app/routes/auto_scheduler.py`

**Function:** `approve_schedule()` (lines 279-318)

**Updated Code:**
```python
# Prepare data for Crossmark API
# IMPORTANT: Use external_id (numeric API ID), NOT employee.id (US###### format)
rep_id = employee.external_id
mplan_id = event.external_id
location_id = event.location_mvid

# Validate required API fields
if not rep_id:
    failed_details.append({
        'event_ref_num': pending.event_ref_num,
        'event_name': event.project_name,
        'employee_name': employee.name,
        'reason': f'Missing external_id for employee {employee.name} ({employee.id})'
    })
    pending.status = 'api_failed'
    pending.api_error_details = 'Missing employee external_id'
    api_failed += 1
    continue

if not mplan_id:
    failed_details.append({
        'event_ref_num': pending.event_ref_num,
        'event_name': event.project_name,
        'reason': 'Missing external_id for event'
    })
    pending.status = 'api_failed'
    pending.api_error_details = 'Missing event external_id'
    api_failed += 1
    continue

if not location_id:
    failed_details.append({
        'event_ref_num': pending.event_ref_num,
        'event_name': event.project_name,
        'reason': 'Missing location_mvid for event'
    })
    pending.status = 'api_failed'
    pending.api_error_details = 'Missing location_mvid'
    api_failed += 1
    continue

# Submit to Crossmark API
api_result = external_api.schedule_mplan_event(
    rep_id=rep_id,
    mplan_id=mplan_id,
    location_id=location_id,
    start_datetime=start_datetime,
    end_datetime=end_datetime,
    planning_override=True
)
```

---

## Data Sync Process

Employees and events are synced from the Crossmark API via `scheduler_app/sync_engine.py`.

### Employee Sync:
- Downloads employees from Crossmark API
- Sets `employee.external_id` = Crossmark employee ID
- Sets `employee.id` = Local "US######" format

### Event Sync:
- Downloads events from Crossmark Planning API
- Sets `event.external_id` = Crossmark mPlan ID
- Sets `event.project_ref_num` = Local reference number

**If external_id fields are missing:** Events and employees cannot be scheduled via the API until they are synced properly.

---

## Benefits

✅ **Correct API Format:** Only sends numeric IDs that Crossmark API expects

✅ **Early Validation:** Catches missing external_id fields before API submission

✅ **Clear Error Messages:** Users can identify which employees/events need to be synced

✅ **No Fallback to Wrong Format:** Prevents sending "US######" format which would fail

---

## Testing

**Test Scenarios:**
1. ✅ Employee with `external_id` set → Schedule submits successfully
2. ✅ Employee with NULL `external_id` → Fails with clear error message
3. ✅ Event with `external_id` set → Schedule submits successfully
4. ✅ Event with NULL `external_id` → Fails with clear error message
5. ✅ Event with NULL `location_mvid` → Fails with clear error message
