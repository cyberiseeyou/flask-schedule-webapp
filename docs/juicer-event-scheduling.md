# Juicer Event Scheduling

**Date:** 2025-10-01
**Updates:** Separate scheduling times for Juicer Production and Juicer Survey events

---

## Juicer Event Types

### 1. Juicer Production (JUICER-PRODUCTION-SPCLTY)
**Time:** 9:00 AM

**Event Name Pattern:**
- Contains "JUICER-PRODUCTION" or "PRODUCTION-SPCLTY"
- Example: "10-16 8HR-ES1-JUICER-PRODUCTION-SPCLTY (250916532292) - ES1"

**Behavior:**
- Scheduled to Primary Juicer rotation at 9:00 AM
- Has PRIORITY - can bump Core events if Juicer is already scheduled
- Only one Juicer Production per day per Juicer

### 2. Juicer Survey
**Time:** 5:00 PM

**Event Name Pattern:**
- Contains "JUICER SURVEY" or "SURVEY"
- Example: "10-16 Juicer Survey (250916532420) - V2.9 Juicer Production Survey"

**Behavior:**
- Scheduled to Primary Juicer rotation at 5:00 PM
- No conflicts with Core events (Core events are at 9:45-11:30)
- Can have multiple Juicer Surveys at 5:00 PM? (TBD if overlaps allowed)

---

## Scheduling Logic

### Phase Order:
1. **Core Events** - Scheduled first at 9:45, 10:30, 11:00, 11:30
2. **Juicer Production** - Scheduled at 9:00 AM (can bump Core if needed)
3. **Juicer Survey** - Scheduled at 5:00 PM
4. **Other rotation events** - Digital, Freeosk

### Example Day Schedule:

**Thursday, October 16, 2025:**

| Time  | Event Type            | Event Name                              | Employee      |
|-------|-----------------------|-----------------------------------------|---------------|
| 9:00  | Juicer Production     | 10-16 8HR-ES1-JUICER-PRODUCTION-SPCLTY  | THOMAS RARICK |
| 9:45  | Core                  | Core Event #1                           | DIANE CARR    |
| 10:30 | Core                  | Core Event #2                           | ROBI DUNFEE   |
| 11:00 | Core                  | Core Event #3                           | NANCY DINKINS |
| 5:00  | Juicer Survey         | 10-16 Juicer Survey                     | THOMAS RARICK |

---

## Implementation Details

**Code Location:** `scheduler_app/services/scheduling_engine.py`

**Key Method:** `_get_juicer_time(event)`
```python
def _get_juicer_time(self, event: object) -> time:
    event_name_upper = event.project_name.upper()

    if 'JUICER-PRODUCTION' in event_name_upper or 'PRODUCTION-SPCLTY' in event_name_upper:
        return time(9, 0)  # 9:00 AM
    elif 'JUICER SURVEY' in event_name_upper or 'SURVEY' in event_name_upper:
        return time(17, 0)  # 5:00 PM
    else:
        return time(9, 0)  # Default
```

**Updated:** `DEFAULT_TIMES` dictionary
- `'Juicer Production'`: 9:00 AM
- `'Juicer Survey'`: 5:00 PM
- `'Juicer'`: 9:00 AM (default)

---

## Benefits

✅ **Eliminates Time Conflicts:** Juicer Production and Juicer Survey can both be scheduled on the same day to the same employee

✅ **Maintains Priority:** Juicer Production at 9:00 AM still has priority and can bump Core events

✅ **Flexible Pattern Matching:** Detects event type based on name pattern, handles variations

✅ **Clear Separation:** Morning production work (9 AM), evening surveys (5 PM)

---

## Testing

**Test Scenarios:**
1. ✅ Schedule Juicer Production at 9:00 AM
2. ✅ Schedule Juicer Survey at 5:00 PM on same day to same employee
3. ✅ Verify both can coexist without conflicts
4. ✅ Verify Juicer Production can still bump Core events at 9:00 AM
5. ✅ Verify pattern matching works for various event name formats
