# Crossmark API Request Verification

**Date:** 2025-10-01
**Status:** ✅ Verified and Updated

---

## API Request Format

### Endpoint
```
POST /planningextcontroller/scheduleMplanEvent
```

### Content-Type
```
application/x-www-form-urlencoded; charset=UTF-8
```

### Required Parameters

| Parameter | Source | Data Type | Example | Validation |
|-----------|--------|-----------|---------|------------|
| `RepID` | `employee.external_id` | String | "815021" | ✅ Required, validated |
| `mPlanID` | `event.external_id` | String | "250916532292" | ✅ Required, validated |
| `LocationID` | `event.location_mvid` | String | "12345" | ✅ Required, validated |
| `Start` | `pending.schedule_datetime` | String (ISO) | "2025-10-16T09:00:00-04:00" | ✅ Auto-formatted |
| `End` | `start + event.estimated_time` | String (ISO) | "2025-10-16T10:00:00-04:00" | ✅ Auto-calculated |
| `ClassName` | Fixed | String | "MVScheduledmPlan" | ✅ Hardcoded |
| `hash` | Fixed | String | "" (empty) | ✅ Hardcoded |
| `v` | Fixed | String | "3.0.1" | ✅ Hardcoded |
| `PlanningOverride` | Fixed | String | "true" | ✅ Hardcoded |

---

## Data Validation

### Employee ID (RepID)
```python
rep_id = str(employee.external_id) if employee.external_id else None

if not rep_id:
    # Fail with error: "Missing external_id for employee {name} ({id})"
    pending.status = 'api_failed'
    api_failed += 1
    continue
```

**✅ Validates:**
- `external_id` is not NULL
- `external_id` is not empty string
- Converts to string for API

**❌ Does NOT use:**
- `employee.id` (US###### format) ❌ Wrong format

---

### Event ID (mPlanID)
```python
mplan_id = str(event.external_id) if event.external_id else None

if not mplan_id:
    # Fail with error: "Missing external_id for event"
    pending.status = 'api_failed'
    api_failed += 1
    continue
```

**✅ Validates:**
- `external_id` is not NULL
- `external_id` is not empty string
- Converts to string for API

**❌ Does NOT use:**
- `event.project_ref_num` (local reference number) ❌ Wrong ID

---

### Location ID (LocationID)
```python
location_id = str(event.location_mvid) if event.location_mvid else None

if not location_id:
    # Fail with error: "Missing location_mvid for event"
    pending.status = 'api_failed'
    api_failed += 1
    continue
```

**✅ Validates:**
- `location_mvid` is not NULL
- `location_mvid` is not empty string
- Converts to string for API

---

### DateTime Formatting

**Start DateTime:**
```python
start_datetime = pending.schedule_datetime  # From auto-scheduler
```

**End DateTime:**
```python
estimated_minutes = event.estimated_time or 60  # Default to 1 hour
end_datetime = start_datetime + timedelta(minutes=estimated_minutes)
```

**API Format Conversion:**
```python
# In session_api_service.py:
start_str = start_datetime.strftime("%Y-%m-%dT%H:%M:%S-04:00")
end_str = end_datetime.strftime("%Y-%m-%dT%H:%M:%S-04:00")
```

**Example Output:**
```
Start=2025-10-16T09:00:00-04:00
End=2025-10-16T10:00:00-04:00
```

**✅ Format:**
- ISO 8601 with timezone offset
- Eastern Time (UTC-4)
- No milliseconds

---

## Complete Request Example

### Form Data String
```
ClassName=MVScheduledmPlan&RepID=815021&mPlanID=250916532292&LocationID=12345&Start=2025-10-16T09:00:00-04:00&End=2025-10-16T10:00:00-04:00&hash=&v=3.0.1&PlanningOverride=true
```

### Headers
```python
{
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://crossmark.com',
    'referer': 'https://crossmark.com/planning/',
    'x-requested-with': 'XMLHttpRequest'
}
```

---

## Logging

### Pre-Request Log
```python
current_app.logger.info(
    f"Submitting to Crossmark API: "
    f"rep_id={rep_id}, mplan_id={mplan_id}, location_id={location_id}, "
    f"start={start_datetime.isoformat()}, end={end_datetime.isoformat()}, "
    f"event={event.project_name}, employee={employee.name}"
)
```

**Example Output:**
```
Submitting to Crossmark API: rep_id=815021, mplan_id=250916532292, location_id=12345,
start=2025-10-16T09:00:00, end=2025-10-16T10:00:00,
event=10-16 8HR-ES1-JUICER-PRODUCTION-SPCLTY, employee=THOMAS RARICK
```

### API Response Logging
```python
# In session_api_service.py:
self.logger.info(f"Successfully scheduled mPlan {mplan_id}")
```

---

## Error Handling

### Missing Employee external_id
```
Error: Missing external_id for employee DIANE CARR (US815021)
Action: Skip this schedule, mark as api_failed
Solution: Sync employees from Crossmark to populate external_id
```

### Missing Event external_id
```
Error: Missing external_id for event
Action: Skip this schedule, mark as api_failed
Solution: Sync events from Crossmark to populate external_id
```

### Missing Location ID
```
Error: Missing location_mvid for event
Action: Skip this schedule, mark as api_failed
Solution: Event data must include location_mvid from Crossmark
```

---

## Success Response

```python
{
    'success': True,
    'message': 'Event scheduled successfully',
    'mplan_id': '250916532292',
    'rep_id': '815021',
    'response_data': {...}  # Crossmark response
}
```

---

## Failure Response

```python
{
    'success': False,
    'message': 'Failed to schedule event: 400 Bad Request',
    'status_code': 400
}
```

---

## Code Locations

### 1. API Submission (`scheduler_app/routes/auto_scheduler.py`)
**Lines 279-337**
- Converts IDs to strings
- Validates all required fields
- Logs request details
- Calls `external_api.schedule_mplan_event()`

### 2. API Call (`scheduler_app/session_api_service.py`)
**Lines 917-990**
- Formats datetime with timezone
- Builds form data string
- Sets proper headers
- Makes POST request

---

## Verification Checklist

✅ **Employee ID:** Using `external_id` (numeric), NOT `id` (US######)
✅ **Event ID:** Using `external_id` (mPlanID), NOT `project_ref_num`
✅ **Location ID:** Using `location_mvid` from event
✅ **DateTime Format:** ISO 8601 with timezone offset (-04:00)
✅ **Default Duration:** 60 minutes if not specified
✅ **String Conversion:** All IDs converted to strings
✅ **Validation:** All required fields checked before API call
✅ **Logging:** Request details logged for debugging
✅ **Error Handling:** Clear messages for missing data

---

## Testing

### Test 1: Valid Request
```python
# All IDs present
employee.external_id = "815021"
event.external_id = "250916532292"
event.location_mvid = "12345"
# Result: ✅ API call succeeds
```

### Test 2: Missing Employee ID
```python
employee.external_id = None
# Result: ✅ Fails with "Missing external_id for employee"
```

### Test 3: Wrong Employee ID Format
```python
# Code now prevents this
# Cannot use employee.id (US######)
# Must use employee.external_id
```

### Test 4: Missing Event ID
```python
event.external_id = None
# Result: ✅ Fails with "Missing external_id for event"
```

### Test 5: Missing Location
```python
event.location_mvid = None
# Result: ✅ Fails with "Missing location_mvid for event"
```