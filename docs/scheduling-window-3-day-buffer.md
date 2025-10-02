# 3-Day Scheduling Buffer

**Date:** 2025-10-01
**Feature:** Auto-scheduler will not schedule events within 3 days from today

---

## Overview

The auto-scheduler now implements a **3-day scheduling buffer**. This means:

- **Looks at:** ALL unscheduled/unstaffed events in the database
- **Schedules for:** Only dates that are 3+ days from today

This prevents the auto-scheduler from changing schedules that employees have already reviewed.

---

## Example

**Today:** October 1, 2025

### Events Processed:

| Event | Start Date | Earliest Schedule Date | Scheduled? |
|-------|-----------|----------------------|------------|
| Event A | Sept 25 (past) | Oct 4 (3 days out) | ✅ Yes, scheduled for Oct 4+ |
| Event B | Oct 2 (tomorrow) | Oct 4 (3 days out) | ✅ Yes, scheduled for Oct 4+ |
| Event C | Oct 4 (3 days out) | Oct 4 (3 days out) | ✅ Yes, scheduled for Oct 4+ |
| Event D | Oct 10 (future) | Oct 10 (event start) | ✅ Yes, scheduled for Oct 10+ |

**Key Points:**
- Event A started in the past but can still be scheduled for Oct 4+
- Event B starts tomorrow but won't be scheduled until Oct 4+
- Event C can be scheduled starting Oct 4
- Event D respects its original start date (Oct 10)

---

## Implementation

### Helper Method

**Location:** `scheduler_app/services/scheduling_engine.py` (lines 220-244)

```python
def _get_earliest_schedule_date(self, event: object) -> datetime:
    """
    Get the earliest date this event can be scheduled

    The earliest date is the later of:
    1. Event's start_datetime
    2. Today + SCHEDULING_WINDOW_DAYS (3 days from today)

    This ensures the auto-scheduler doesn't schedule events within the 3-day buffer.

    Args:
        event: Event object

    Returns:
        datetime: Earliest date this event can be scheduled
    """
    today = datetime.now().date()
    earliest_allowed = today + timedelta(days=self.SCHEDULING_WINDOW_DAYS)
    earliest_allowed_datetime = datetime.combine(earliest_allowed, time(0, 0))

    # Return the later of the two dates
    if event.start_datetime >= earliest_allowed_datetime:
        return event.start_datetime
    else:
        return earliest_allowed_datetime
```

### Updated Methods

All scheduling methods now use `_get_earliest_schedule_date(event)` instead of `event.start_datetime`:

1. **`_schedule_juicer_event()`** (line 321)
   ```python
   current_date = self._get_earliest_schedule_date(event)
   ```

2. **`_schedule_primary_lead_event()`** (line 490)
   ```python
   current_date = self._get_earliest_schedule_date(event)
   ```

3. **`_schedule_secondary_lead_event()`** (line 538)
   ```python
   current_date = self._get_earliest_schedule_date(event)
   ```

4. **`_schedule_core_event()`** (line 592)
   ```python
   current_date = self._get_earliest_schedule_date(event)
   ```

### Query Filter

**Location:** `scheduler_app/services/scheduling_engine.py` (lines 180-201)

```python
def _get_unscheduled_events(self) -> List[object]:
    """
    Get ALL unscheduled/unstaffed events

    Returns all unscheduled events regardless of start date.
    The scheduling logic will ensure the earliest assignment date is 3 days from today.

    Returns:
        List of Event objects that are unscheduled/unstaffed
    """
    events = self.db.query(self.Event).filter(
        and_(
            self.Event.is_scheduled == False,  # Only unscheduled events
            self.Event.condition == 'Unstaffed'  # Only unstaffed events
        )
    ).all()

    return events
```

---

## Benefits

✅ **Employee Schedule Stability:** Employees can safely review schedules for the next 3 days without changes from auto-scheduler

✅ **Handles Past Events:** Events with past start dates can still be scheduled (useful for flexible/rolling events)

✅ **Clear Buffer Zone:** 3-day window gives time for manual adjustments before auto-scheduler takes over

✅ **Respects Event Start Dates:** If an event naturally starts beyond 3 days, it respects that date

---

## Configuration

**Constant:** `SCHEDULING_WINDOW_DAYS` (line 30)

```python
SCHEDULING_WINDOW_DAYS = 3  # 3 days ahead
```

To change the buffer, simply update this constant:
- `SCHEDULING_WINDOW_DAYS = 1` → Schedule events 1+ days out
- `SCHEDULING_WINDOW_DAYS = 7` → Schedule events 7+ days out
- `SCHEDULING_WINDOW_DAYS = 0` → No buffer (schedule immediately)

---

## Supervisor Events

**Note:** Supervisor events are auto-paired with Core events and scheduled on the **same date as the Core event**, regardless of the Supervisor event's start date.

This means if a Core event is scheduled for Oct 4, the paired Supervisor event will also be scheduled for Oct 4 (at noon), even if the Supervisor event's start date is different.

---

## Testing

**Test Scenarios:**

1. ✅ Event starting yesterday → Should be scheduled for 3 days from today
2. ✅ Event starting tomorrow → Should be scheduled for 3 days from today
3. ✅ Event starting 3 days from today → Should be scheduled for that date
4. ✅ Event starting 10 days from today → Should be scheduled for that date (not earlier)
5. ✅ Event due before 3 days out → Should not be scheduled (cannot meet due date)

---

## Edge Cases

### Event Due Before Buffer Period

If an event's `due_datetime` is before the 3-day buffer:
- The event will NOT be scheduled
- The while loop condition `current_date < event.due_datetime` will be false immediately
- No pending schedule will be created

**Example:**
- Today: Oct 1
- Event due: Oct 2
- Earliest schedule date: Oct 4
- Result: Cannot schedule (Oct 4 > Oct 2)

**Recommendation:** These urgent events should be manually scheduled or have their due dates extended.

### Event Window Too Short

If an event has a very short window (start to due):
- Example: Event starts Oct 4, due Oct 4
- Earliest schedule: Oct 4
- Result: Will attempt to schedule on Oct 4 only

---

## Future Enhancements

**Potential Improvements:**

1. **User-Configurable Buffer:** Allow users to set buffer via UI settings
2. **Event-Type Specific Buffers:** Different buffers for Core vs Digital events
3. **Warning for Skipped Events:** Notify when events are skipped due to buffer constraints
4. **Manual Override:** Allow admin to bypass buffer for specific scheduler runs
