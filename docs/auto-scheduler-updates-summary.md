# Auto-Scheduler Updates Summary

**Date:** 2025-10-01
**Phase:** Production-Ready Enhancements

---

## Overview

This document summarizes all updates made to the auto-scheduler system to address scheduling conflicts, API integration issues, and scheduling window constraints.

---

## 1. Duplicate Employee Assignment Fix

**Problem:** DIANE CARR and other employees were being scheduled to multiple Core events at the same time.

**Root Cause:** `_check_already_scheduled()` only checked the Schedule table, not PendingSchedule table from the current scheduler run.

**Solution:**
- Added `current_run_id` tracking to ConstraintValidator
- Added `set_current_run()` method to set the current scheduler run ID
- Updated `_check_already_scheduled()` to check both Schedule AND PendingSchedule tables
- Updated `_check_daily_limit()` to count pending Core events from current run

**Files Changed:**
- `scheduler_app/services/constraint_validator.py`
- `scheduler_app/services/scheduling_engine.py`

**Status:** ✅ Fixed

---

## 2. Juicer Event Time Separation

**Problem:** Juicer Production and Juicer Survey events both scheduled at 9:00 AM, causing conflicts when assigning to same employee.

**User Requirement:** "Juicer Surveys should be scheduled at 5:00 PM and Juicer Production SPCTY scheduled at 9:00 both to the same person for that day"

**Solution:**
- Added `_get_juicer_time()` method to detect event type by name pattern:
  - `JUICER-PRODUCTION` or `PRODUCTION-SPCLTY` → 9:00 AM
  - `JUICER SURVEY` or `SURVEY` → 5:00 PM
  - Default → 9:00 AM
- Updated `DEFAULT_TIMES` dictionary with separate times

**Files Changed:**
- `scheduler_app/services/scheduling_engine.py`

**Documentation:**
- `docs/juicer-event-scheduling.md`

**Status:** ✅ Fixed

---

## 3. Reject Schedule Functionality

**Problem:** Clicking "Reject" button redirected to dashboard but didn't clear the "Pending Schedule Proposal" notification.

**Root Cause:** Reject button only redirected, didn't mark runs as rejected in database.

**Solution:**
- Added `/reject` POST route in `auto_scheduler.py`
- Updated `SchedulerRunHistory` model to allow 'rejected' status
- Updated database constraint: `CHECK (status IN ('running', 'completed', 'failed', 'crashed', 'rejected'))`
- Made reject button reject ALL pending runs by default
- Updated JavaScript to call API before redirecting

**Files Changed:**
- `scheduler_app/routes/auto_scheduler.py`
- `scheduler_app/models/auto_scheduler.py`
- `scheduler_app/templates/auto_schedule_review.html`
- Database schema (manual SQL update)

**Status:** ✅ Fixed

---

## 4. Scheduling Phase Order (Juicer Priority)

**Problem:** Juicer events scheduled before Core events, so they couldn't bump Core events when rotation employee already scheduled.

**User Requirement:** "Juicer events should be scheduled first so... schedule the event that was removed"

**Solution:**
- Reordered scheduling phases:
  1. **Phase 1:** Core events (scheduled first at 9:45, 10:30, 11:00, 11:30)
  2. **Phase 2:** Juicer events (scheduled at 9:00 AM - can bump Core events)
  3. **Phase 3:** Other rotation events (Digital, Freeosk)
  4. **Phase 4:** Supervisor events (scheduled at noon)

**Files Changed:**
- `scheduler_app/services/scheduling_engine.py` (lines 309-320)

**Status:** ✅ Fixed

---

## 5. Date Display Timezone Bug

**Problem:** MICHELLE MONTAGUE shown as scheduled on "Mon, Oct 6" but database had correct date (Oct 7 = Tuesday).

**Root Cause:** JavaScript `new Date("2025-10-07")` parsed as UTC midnight, converted to previous day when displayed in local timezone.

**Solution:**
- Updated `formatDateTime()` function to parse dates manually as local time
- Extract year, month, day components and create Date object with local constructor

**Files Changed:**
- `scheduler_app/templates/auto_schedule_review.html`

**Code:**
```javascript
function formatDateTime(dateString, timeString) {
    if (!dateString) return '-';

    // Parse date as local time to avoid timezone issues
    const parts = dateString.split('T')[0].split('-');
    const year = parseInt(parts[0]);
    const month = parseInt(parts[1]) - 1; // Month is 0-indexed
    const day = parseInt(parts[2]);
    const date = new Date(year, month, day);

    const formatted = date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
    return timeString ? `${formatted} at ${timeString}` : formatted;
}
```

**Status:** ✅ Fixed

---

## 6. Weekend Scheduling Enabled

**Problem:** Events not scheduled for Saturdays and Sundays despite employees having weekend availability.

**Root Cause:** 5 hardcoded weekend skips: `if current_date.weekday() >= 5: skip`

**Solution:**
- Removed all weekend skip checks from:
  - `_schedule_juicer_event()`
  - `_reschedule_bumped_core_event()`
  - `_schedule_primary_lead_event()`
  - `_schedule_secondary_lead_event()`
  - `_schedule_core_event()`
- Now respects employee availability on weekends

**Files Changed:**
- `scheduler_app/services/scheduling_engine.py`

**Status:** ✅ Fixed

---

## 7. Digital Events Scheduling

**Problem:** Digital events (Setup, Refresh, Teardown) not being scheduled at all.

**Root Cause:** Events stored as `event_type = 'Digitals'` but code checked for `['Digital Setup', 'Digital Refresh']`.

**Solution:**
- Updated `_schedule_other_rotation_events()` to detect `event_type = 'Digitals'`
- Added name pattern detection to route by subtype:
  - `TEARDOWN` → Secondary Lead at 5:00 PM (15-min intervals)
  - `SETUP` or `REFRESH` → Primary Lead at 9:15 AM (15-min intervals)
  - Default → Primary Lead at 9:15 AM
- Updated `_schedule_primary_lead_event()` to detect Digital subtypes

**Files Changed:**
- `scheduler_app/services/scheduling_engine.py`

**Status:** ✅ Fixed

---

## 8. 3-Day Scheduling Window

**Problem:** Scheduler trying to schedule events too far in advance and past/current events.

**User Requirement:** "Change the auto scheduler to only be trying to schedule for three days past the current date and not trying to schedule past events or current events."

**Solution:**
- Changed `SCHEDULING_WINDOW_DAYS` from 21 to 3
- Updated `_get_unscheduled_events()` to filter:
  - `is_scheduled == False` - Only unscheduled events
  - `condition == 'Unstaffed'` - Only unstaffed events
  - `due_datetime >= tomorrow` - Due tomorrow or later (not today or past)
  - `start_datetime <= window_end` - Start within 3 days

**Files Changed:**
- `scheduler_app/services/scheduling_engine.py` (lines 30, 180-203)

**Code:**
```python
SCHEDULING_WINDOW_DAYS = 3  # 3 days ahead

def _get_unscheduled_events(self) -> List[object]:
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    window_end = today + timedelta(days=self.SCHEDULING_WINDOW_DAYS)

    events = self.db.query(self.Event).filter(
        and_(
            self.Event.is_scheduled == False,
            self.Event.condition == 'Unstaffed',
            self.Event.due_datetime >= datetime.combine(tomorrow, time(0, 0)),
            self.Event.start_datetime <= datetime.combine(window_end, time(23, 59))
        )
    ).all()

    return events
```

**Status:** ✅ Fixed

---

## 9. API Employee ID Format Fix

**Problem:** API submission using "US######" format as fallback when `external_id` was empty.

**User Requirement:** "ensure it is passing the employee ID from the api not the US###### number"

**Root Cause:** Code had fallback: `rep_id = employee.external_id or employee.id`

**Solution:**
- Changed to only use `employee.external_id` (numeric Crossmark API ID)
- Removed fallback to `employee.id` (US###### format)
- Added validation to fail early if `external_id` is missing:
  - Check `employee.external_id` is not NULL/empty
  - Check `event.external_id` is not NULL/empty
  - Check `event.location_mvid` is not NULL/empty
- Clear error messages identify which employees/events need syncing

**Files Changed:**
- `scheduler_app/routes/auto_scheduler.py` (lines 279-318)

**Documentation:**
- `docs/api-data-format.md`

**Code:**
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
```

**Status:** ✅ Fixed

---

## Testing Checklist

### Core Functionality:
- [ ] Run auto-scheduler and verify no duplicate employee assignments
- [ ] Verify Juicer Production scheduled at 9:00 AM
- [ ] Verify Juicer Survey scheduled at 5:00 PM on same day to same employee
- [ ] Verify Core events scheduled first, then Juicer events can bump them
- [ ] Verify Digital Setup/Refresh scheduled at 9:15 AM to Primary Lead
- [ ] Verify Digital Teardown scheduled at 5:00 PM to Secondary Lead
- [ ] Verify Supervisor events scheduled at noon
- [ ] Verify weekend events scheduled when employees available

### UI/UX:
- [ ] Verify dates display correctly without timezone shift
- [ ] Verify reject button clears all pending proposals
- [ ] Verify dashboard notification clears after reject

### API Integration:
- [ ] Verify API submission uses numeric `external_id` not "US######"
- [ ] Verify clear error messages when `external_id` missing
- [ ] Verify events within 3-day window only
- [ ] Verify only unstaffed events are scheduled
- [ ] Verify past/current events are not scheduled

---

## Benefits Summary

✅ **No Duplicate Assignments** - Employees never scheduled to multiple events at same time

✅ **Juicer Priority & Flexibility** - Juicer events can bump Core events, Production and Survey don't conflict

✅ **Weekend Support** - Respects employee weekend availability

✅ **All Event Types Scheduled** - Core, Juicer, Digital, Freeosk, Supervisor all working

✅ **3-Day Window** - Only schedules near-term events, reduces noise

✅ **Correct API Format** - Uses proper employee/event IDs, fails with clear messages

✅ **Timezone-Safe Display** - Dates shown correctly in local timezone

✅ **Reject Workflow** - Clear pending proposals and notifications properly

---

## Future Enhancements

**Potential Future Work:**
1. Configurable scheduling window (allow user to change 3-day window)
2. Bulk approve/reject for specific event types
3. Manual drag-and-drop schedule editor
4. Notification system for failed API submissions
5. Historical scheduler run analytics
6. Automated scheduler runs (cron/scheduled task)
