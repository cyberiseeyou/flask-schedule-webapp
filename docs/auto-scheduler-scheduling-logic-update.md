# Auto-Scheduler Scheduling Logic Updates

**Date:** 2025-10-01
**Changes:** Updated scheduling times and Supervisor event linking

---

## Changes Made

### 1. Updated Scheduling Times

**Juicer Events:**
- Changed from 8:00 AM to **9:00 AM**

**Core Events:**
- **Primary Lead**: 9:45 AM (first priority)
- **Everyone else**: Rotating through 10:30, 11:00, 11:30, then back to 9:45

**Time Slot Rotation Logic:**
```python
CORE_TIME_SLOTS = [
    time(9, 45),   # Primary Lead slot
    time(10, 30),  # First rotation slot
    time(11, 0),   # Second rotation slot
    time(11, 30)   # Third rotation slot
]
```

### 2. Core Event Scheduling Algorithm

**New Logic:**
1. Check if Primary Lead (from rotation) is available at 9:45 AM
2. If yes and no conflicts, assign Primary Lead at 9:45 AM
3. If no, get next available time slot (10:30, 11:00, 11:30, cycling)
4. Try to assign Lead Event Specialists first
5. Fall back to Event Specialists
6. If no one available, attempt conflict resolution

**Time Slot Tracking:**
- Each date maintains a counter for which time slot to use next
- Counter increments after each assignment
- Cycles through all 4 slots: 9:45 → 10:30 → 11:00 → 11:30 → 9:45 → ...

### 3. Supervisor Event Linking

**Changed from:** Using `parent_event_ref_num` field
**Changed to:** Extracting first 6 digits from event name

**Algorithm:**
```python
def _extract_event_number(event_name: str) -> str:
    """Extract first 6 digits from event name"""
    match = re.search(r'\d{6}', event_name)
    return match.group(0) if match else None
```

**Linking Process:**
1. Extract 6-digit event number from Supervisor event name
2. Search all Core events for matching 6-digit number
3. Link Supervisor event to matching Core event
4. Schedule Supervisor event on same date as Core event at Noon (12:00 PM)

**Assignment Priority:**
1. Club Supervisor (if available)
2. Lead Event Specialist who has the Core event

### 4. Bug Fixes Applied

**Fixed Issues:**
- ✅ Juicer rotation filter (changed from `adult_beverage_trained` to `job_title == 'Juicer Barista'`)
- ✅ Weekend rotation support (days 0-6 instead of 0-4)
- ✅ Database constraints updated for Saturday/Sunday
- ✅ EmployeeWeeklyAvailability lookup (using day columns instead of day_of_week)
- ✅ PendingSchedule nullable columns (allows NULL for failed events)
- ✅ Review page JavaScript (removed invalid success check)

---

## Example Scheduling

**Monday, October 7, 2025:**

| Time  | Event           | Employee          | Role              |
|-------|-----------------|-------------------|-------------------|
| 9:00  | Juicer Event    | THOMAS RARICK     | Juicer Barista    |
| 9:45  | Core Event #1   | Jane Doe          | Lead (Primary)    |
| 10:30 | Core Event #2   | John Smith        | Event Specialist  |
| 11:00 | Core Event #3   | Sarah Johnson     | Lead              |
| 11:30 | Core Event #4   | Mike Brown        | Event Specialist  |
| 12:00 | Supervisor #1   | Mat Conder        | Club Supervisor   |

**Tuesday, October 8, 2025:**

| Time  | Event           | Employee          | Role              |
|-------|-----------------|-------------------|-------------------|
| 9:00  | Juicer Event    | CODY WEAVER       | Juicer Barista    |
| 9:45  | Core Event #5   | Bob Wilson        | Lead (Primary)    |
| 10:30 | Core Event #6   | Alice Cooper      | Event Specialist  |
| 11:00 | Core Event #7   | Tom Hardy         | Lead              |
| 12:00 | Supervisor #5   | Mat Conder        | Club Supervisor   |

---

## Code Changes

**Files Modified:**
1. `scheduler_app/services/scheduling_engine.py`
   - Updated DEFAULT_TIMES
   - Added CORE_TIME_SLOTS array
   - Added daily_time_slot_index tracker
   - Rewrote _schedule_core_event() logic
   - Added _get_next_time_slot() method
   - Added _extract_event_number() method
   - Rewrote _schedule_supervisor_events() logic

2. `scheduler_app/routes/rotations.py`
   - Fixed juicer filter to use job_title

3. `scheduler_app/services/constraint_validator.py`
   - Fixed role requirement check for Juicers
   - Fixed EmployeeWeeklyAvailability day lookup

4. `scheduler_app/services/rotation_manager.py`
   - Removed weekend skip logic
   - Updated day_of_week validation to 0-6

5. `scheduler_app/models/auto_scheduler.py`
   - Updated day_of_week constraint to 0-6
   - Made employee_id, schedule_datetime, schedule_time nullable

6. `scheduler_app/templates/auto_schedule_review.html`
   - Fixed JavaScript success check

---

## Testing Recommendations

**Test Cases:**
1. Schedule 10+ Core events on same day - verify time slot rotation
2. Assign Primary Lead at 9:45 - verify no one else gets that slot
3. Schedule Supervisor event - verify it links to correct Core event by event number
4. Schedule events on Saturday/Sunday - verify rotation assignments work
5. Test with no Juicer Baristas available - verify failure tracking
6. Test with Primary Lead unavailable - verify fallback to rotation

---

## Future Enhancements

**Potential Improvements:**
1. Make time slots configurable in admin settings
2. Add priority override for urgent events
3. Implement "preferred time" per employee
4. Add capacity limits per time slot
5. Support custom rotation schedules per week
6. Add holiday handling (skip certain dates)

---

**Updated by:** Auto-Scheduler Phase 3 Enhancements
**Completion Date:** 2025-10-01
