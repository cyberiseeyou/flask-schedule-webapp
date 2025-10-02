# Other Events and Digital Fallback Scheduling

**Date:** 2025-10-01
**Feature:** Club Supervisor scheduling for Other events and Digital fallbacks

---

## Overview

Two major scheduling rules have been implemented:

1. **Other Events** → Always scheduled to Club Supervisor at Noon
2. **Digital Events** → Fallback to Club Supervisor if no leads available

---

## 1. Other Event Scheduling

### Rule
All events with `event_type = 'Other'` are scheduled to the Club Supervisor at noon (12:00 PM) on the event's start date.

### Implementation
- **Location:** `scheduler_app/services/scheduling_engine.py`
- **Method:** `_schedule_other_event()`

### Key Points:
- Scheduled at **12:00 PM (Noon)** on the event's start date
- Only Club Supervisor is considered (no other employees)
- **Time conflicts are IGNORED** - multiple Other events can overlap at noon
- Only checks:
  - Time off
  - Weekly availability
  - Does NOT check scheduling conflicts

### Example:
```python
Event: "Other Special Task"
Start Date: October 15, 2025
→ Scheduled to: Club Supervisor
→ Time: October 15, 2025 at 12:00 PM
```

---

## 2. Digital Event Fallback to Club Supervisor

### Rule
If no Lead Event Specialists are available for Digital events, the system automatically falls back to the Club Supervisor.

### Affected Event Types:
- **Digital Setup** (9:15 AM slots) → Primary Lead → Club Supervisor
- **Digital Refresh** (9:15 AM slots) → Primary Lead → Club Supervisor
- **Digital Teardown** (5:00 PM slots) → Secondary Lead → Club Supervisor

### Implementation
Updated two methods to include Club Supervisor fallback:
- `_schedule_primary_lead_event()` - For Setup/Refresh
- `_schedule_secondary_lead_event()` - For Teardown

### Scheduling Priority:
1. **First:** Try rotation-assigned Lead (Primary or Secondary)
2. **Second:** Try other available Leads
3. **Third:** Fallback to Club Supervisor

### Example:
```python
Event: "09.01-DD-P&G-TideLiquid Digital Refresh"
No Primary Lead available on October 15
No other Leads available
→ Scheduled to: Club Supervisor at 9:15 AM
```

---

## 3. API Format Verification

### URL Encoding
The datetime values in API requests are now properly URL-encoded to match the exact curl format:

**Before:** `Start=2025-10-02T12:00:00-04:00`
**After:** `Start=2025-10-02T12%3A00%3A00-04%3A00`

### Changes Made:
```python
# URL-encode the datetime colons to match exact curl format
from urllib.parse import quote
start_str_encoded = quote(start_str, safe='')
end_str_encoded = quote(end_str, safe='')
```

### Complete Request Format:
```
ClassName=MVScheduledmPlan
RepID=152052
mPlanID=31779576
LocationID=157384
Start=2025-10-02T12%3A00%3A00-04%3A00
End=2025-10-02T12%3A05%3A00-04%3A00
hash=
v=3.0.1
PlanningOverride=true
```

---

## 4. Files Modified

### `scheduler_app/services/scheduling_engine.py`
- Added `_schedule_other_event()` method
- Updated `_schedule_other_rotation_events()` to handle Other events
- Updated `_schedule_primary_lead_event()` with Club Supervisor fallback
- Updated `_schedule_secondary_lead_event()` with Club Supervisor fallback
- Added `from flask import current_app` import

### `scheduler_app/session_api_service.py`
- Added URL encoding for datetime values in API requests
- Import `quote` from `urllib.parse`

---

## 5. Logging

The system logs when Club Supervisor is used as a fallback:

```
"Scheduled Other event 12345 to Club Supervisor at noon"
"Scheduled Digital event 31721927 to Club Supervisor (no leads available)"
"Scheduled Digital Teardown 31721927 to Club Supervisor (no secondary lead available)"
```

---

## 6. Who is Club Supervisor?

The Club Supervisor is identified by:
```python
club_supervisor = db.query(Employee).filter_by(
    job_title='Club Supervisor',
    is_active=True
).first()
```

Currently, the Club Supervisor role is typically assigned to employees with managerial responsibilities who can handle overflow scheduling.

---

## 7. Testing Checklist

### Other Events:
- [ ] Verify Other events schedule to Club Supervisor at noon
- [ ] Verify multiple Other events can be scheduled at same time
- [ ] Verify Club Supervisor time off is respected
- [ ] Verify Club Supervisor weekly availability is checked

### Digital Fallback:
- [ ] Schedule Digital Setup with no Primary Lead available → Goes to Club Supervisor
- [ ] Schedule Digital Refresh with no leads → Goes to Club Supervisor
- [ ] Schedule Digital Teardown with no Secondary Lead → Goes to Club Supervisor
- [ ] Verify Club Supervisor gets correct time slots (9:15 AM for Setup, 5:00 PM for Teardown)

### API Format:
- [ ] Verify datetime colons are URL-encoded as `%3A`
- [ ] Verify successful API submission with encoded format
- [ ] Check logs show properly encoded datetime strings

---

## 8. Benefits

✅ **No Failed Schedules:** Other events and Digital events always have a fallback option

✅ **Flexible Supervisor Scheduling:** Club Supervisor can handle multiple overlapping events

✅ **Clear Hierarchy:** Leads get priority, Club Supervisor handles overflow

✅ **API Compatibility:** Exact match with Crossmark's expected URL encoding format

---

## 9. Notes

- **Time Conflicts:** Club Supervisor can have unlimited events at the same time
- **Availability:** Club Supervisor's time off and weekly availability are still respected
- **Priority:** Club Supervisor is always the last resort after trying all qualified leads
- **Other Events:** Always go directly to Club Supervisor (no other employees considered)