# Auto-Scheduler Time Slot Updates

**Date:** 2025-10-01
**Changes:** Updated time slots for Digital events and excluded Club Supervisor from Core events

---

## Changes Made

### 1. Club Supervisor Exclusion from Core Events

**Previous Behavior:**
- Club Supervisor could be assigned to Core events

**New Behavior:**
- Club Supervisor is **excluded** from Core event assignments
- Club Supervisor can still be assigned to:
  - Supervisor events (priority #1)
  - Digital Setup/Refresh/Freeosk events
  - Digital Teardown events

**Implementation:**
```python
# For Core events, only get Lead Event Specialists (exclude Club Supervisor)
if event.event_type == 'Core':
    leads = self.db.query(self.Employee).filter(
        self.Employee.job_title == 'Lead Event Specialist',
        self.Employee.is_active == True
    ).all()
else:
    # For other event types, include Club Supervisor
    leads = self.db.query(self.Employee).filter(
        self.Employee.job_title.in_(['Lead Event Specialist', 'Club Supervisor']),
        self.Employee.is_active == True
    ).all()
```

---

### 2. Freeosk Event Time Change

**Previous:** 10:00 AM
**New:** 9:00 AM

Freeosk events now scheduled at the same time as Juicer events.

---

### 3. Digital Setup & Digital Refresh - 15 Minute Intervals

**Previous:** Fixed times (9:00 AM or 10:00 AM)
**New:** Rotating 15-minute intervals starting at 9:15 AM

**Time Slots:**
```
9:15 AM
9:30 AM
9:45 AM
10:00 AM
10:15 AM
10:30 AM
10:45 AM
11:00 AM
11:15 AM
11:30 AM
11:45 AM
12:00 PM
```

**Logic:**
- First Digital Setup/Refresh event on a day: 9:15 AM
- Second event: 9:30 AM
- Third event: 9:45 AM
- Continues cycling through all 12 slots
- After 12:00 PM, cycles back to 9:15 AM

---

### 4. Digital Teardown - 15 Minute Intervals Starting at 5 PM

**Previous:** Fixed at 3:00 PM (15:00)
**New:** Rotating 15-minute intervals starting at 5:00 PM (17:00)

**Time Slots:**
```
5:00 PM (17:00)
5:15 PM (17:15)
5:30 PM (17:30)
5:45 PM (17:45)
6:00 PM (18:00)
6:15 PM (18:15)
6:30 PM (18:30)
6:45 PM (18:45)
```

**Logic:**
- First Digital Teardown event on a day: 5:00 PM
- Second event: 5:15 PM
- Third event: 5:30 PM
- Continues cycling through all 8 slots
- After 6:45 PM, cycles back to 5:00 PM

---

## Complete Time Schedule Summary

### Morning Schedule (9:00 AM - 12:00 PM)

| Time  | Event Types                           |
|-------|---------------------------------------|
| 9:00  | Juicer, Freeosk                       |
| 9:15  | Digital Setup/Refresh (slot 1)        |
| 9:30  | Digital Setup/Refresh (slot 2)        |
| 9:45  | Core (Primary Lead), Digital S/R (3)  |
| 10:00 | Digital Setup/Refresh (slot 4)        |
| 10:15 | Digital Setup/Refresh (slot 5)        |
| 10:30 | Core (rotating slot 2), Digital S/R   |
| 10:45 | Digital Setup/Refresh (slot 7)        |
| 11:00 | Core (rotating slot 3), Digital S/R   |
| 11:15 | Digital Setup/Refresh (slot 9)        |
| 11:30 | Core (rotating slot 4), Digital S/R   |
| 11:45 | Digital Setup/Refresh (slot 11)       |
| 12:00 | Supervisor, Digital S/R (slot 12)     |

### Afternoon/Evening Schedule (5:00 PM - 7:00 PM)

| Time  | Event Types                    |
|-------|--------------------------------|
| 5:00  | Digital Teardown (slot 1)      |
| 5:15  | Digital Teardown (slot 2)      |
| 5:30  | Digital Teardown (slot 3)      |
| 5:45  | Digital Teardown (slot 4)      |
| 6:00  | Digital Teardown (slot 5)      |
| 6:15  | Digital Teardown (slot 6)      |
| 6:30  | Digital Teardown (slot 7)      |
| 6:45  | Digital Teardown (slot 8)      |

---

## Example Day Schedule

**Monday, October 7, 2025:**

| Time  | Event Type          | Event Name           | Employee          | Role              |
|-------|---------------------|----------------------|-------------------|-------------------|
| 9:00  | Juicer              | Juice Production     | THOMAS RARICK     | Juicer Barista    |
| 9:00  | Freeosk             | Freeosk Demo         | Jane Doe          | Lead              |
| 9:15  | Digital Setup       | Digital Setup #1     | Bob Wilson        | Lead (Primary)    |
| 9:30  | Digital Refresh     | Digital Refresh #1   | Bob Wilson        | Lead (Primary)    |
| 9:45  | Core                | Core Event #1        | Bob Wilson        | Lead (Primary)    |
| 9:45  | Digital Setup       | Digital Setup #2     | Sarah Johnson     | Lead              |
| 10:30 | Core                | Core Event #2        | John Smith        | Event Specialist  |
| 10:30 | Digital Refresh     | Digital Refresh #2   | Alice Cooper      | Lead              |
| 11:00 | Core                | Core Event #3        | Mike Brown        | Event Specialist  |
| 11:30 | Core                | Core Event #4        | Tom Hardy         | Lead              |
| 12:00 | Supervisor          | Supervisor #1        | Mat Conder        | Club Supervisor   |
| 5:00  | Digital Teardown    | Teardown #1          | Sarah Johnson     | Lead (Secondary)  |
| 5:15  | Digital Teardown    | Teardown #2          | Sarah Johnson     | Lead (Secondary)  |

---

## Code Changes

**File Modified:** `scheduler_app/services/scheduling_engine.py`

**Changes:**
1. Updated `DEFAULT_TIMES` dictionary:
   - Freeosk: 10:00 → 9:00
   - Digital Setup: 9:00 → 9:15
   - Digital Refresh: 10:00 → 9:15
   - Digital Teardown: 15:00 → 17:00

2. Added new time slot arrays:
   - `DIGITAL_TIME_SLOTS`: 12 slots from 9:15 to 12:00 (15-min intervals)
   - `TEARDOWN_TIME_SLOTS`: 8 slots from 17:00 to 18:45 (15-min intervals)

3. Added time slot tracking:
   - `self.digital_time_slot_index = {}`
   - `self.teardown_time_slot_index = {}`

4. Added helper methods:
   - `_get_next_digital_time_slot(date_obj)`: Returns next Digital Setup/Refresh slot
   - `_get_next_teardown_time_slot(date_obj)`: Returns next Digital Teardown slot

5. Updated `_schedule_primary_lead_event()`:
   - Digital Setup/Refresh events use rotating 15-min slots
   - Freeosk events use fixed 9:00 AM time

6. Updated `_schedule_secondary_lead_event()`:
   - Digital Teardown events use rotating 15-min slots starting at 5:00 PM

7. Updated `_get_available_leads()`:
   - Core events: Only Lead Event Specialists (exclude Club Supervisor)
   - Other events: Lead Event Specialists + Club Supervisor

---

## Benefits

**Better Time Distribution:**
- Digital events spread across 15-minute intervals
- Reduces clustering of events at single time slots
- More efficient use of employee time

**Role Specialization:**
- Club Supervisor reserved for Supervisor events
- Lead Event Specialists handle Core events
- Clear separation of responsibilities

**Flexibility:**
- Can schedule up to 12 Digital Setup/Refresh events per day
- Can schedule up to 8 Digital Teardown events per day
- Time slots cycle automatically for unlimited events

---

## Testing Recommendations

**Test Cases:**
1. Schedule 15+ Digital Setup events on one day - verify cycling through all slots
2. Schedule 10+ Digital Teardown events - verify 5 PM start and 15-min intervals
3. Assign Core event to Club Supervisor - should fail validation
4. Schedule Freeosk event - verify 9:00 AM time
5. Schedule mixed Digital Setup and Digital Refresh - verify they share time slots
6. Check time slot independence per day - Monday slot 1, Tuesday also slot 1

---

**Updated by:** Auto-Scheduler Time Slot Configuration
**Completion Date:** 2025-10-01
