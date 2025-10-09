# Supervisor Event Auto-Scheduling

## Overview
When a CORE event is scheduled, the system automatically schedules the corresponding Supervisor event to ensure proper oversight and resource allocation.

## Features

### Automatic Scheduling
- **Trigger**: Whenever a CORE event is scheduled (manually, via auto-scheduler, or CSV import)
- **Time**: Supervisor events are always scheduled at **12:00 PM (noon)** on the same day as the CORE event
- **Duration**: 5 minutes (as per event type defaults)

### Assignment Logic
The system follows this priority order to determine who gets assigned the Supervisor event:

1. **Lead assigned to CORE event**
   - If the CORE event is assigned to a Lead Event Specialist, that Lead gets the Supervisor event

2. **Other Lead with CORE event that day**
   - If the CORE event is assigned to a non-Lead (e.g., Event Specialist), the system checks if any Lead Event Specialist has a CORE event scheduled that day
   - If found, that Lead gets the Supervisor event

3. **Club Supervisor (fallback)**
   - If no Lead Event Specialists have CORE events on that day, the Supervisor event is assigned to the Club Supervisor

### Business Rules
- **Full Day Guarantee**: Leads only receive Supervisor, Digital, or Freeosk events if they already have a CORE event that day
- **Reason**: Ensures Leads get a full day's work (6.5 hours from CORE) rather than just a short event (5-15 minutes)
- **Supervisor Availability**: This guarantees oversight is available since a Lead or Club Supervisor will be on-site

## Event Relationship
- CORE and Supervisor events are matched by the **6-digit event number** in their project names
- Both events share the same 6-digit event number at the start of their names:
  - CORE: `606001-CORE-Product Name`
  - Supervisor: `606001-Supervisor-Product Name`
- The system uses `extract_event_number()` from `utils/event_helpers.py` to extract and match these numbers
- Each event has its own unique `project_ref_num` in the database

## Implementation Details

### Function Location
`routes/scheduling.py::auto_schedule_supervisor_event()`

### Integration Points
1. **Manual Scheduling** (`routes/scheduling.py::save_schedule()`)
   - Called after successful CORE event scheduling
   - User sees confirmation: "Supervisor event '<name>' was automatically scheduled"

2. **Auto-Scheduler** (`routes/auto_scheduler.py::approve_scheduler_run()`)
   - Called after each CORE event is successfully submitted to the API
   - Logged for audit trail

3. **CSV Import** (`routes/api.py::import_scheduled_csv()`)
   - Called when CORE events are imported from CSV
   - Processes in bulk during import

### Error Handling
- If supervisor event scheduling fails, the CORE event scheduling still succeeds
- Errors are logged but don't block the main operation
- Returns success status and event name for confirmation messaging

## Example Scenarios

### Scenario 1: Lead Scheduled for CORE
```
CORE Event: 606001-CORE-Super Pretzel
  - Scheduled to: John Lead (Lead Event Specialist)
  - Date: 2025-10-15 at 10:00 AM

Result:
  Supervisor Event: 606001-Supervisor-Super Pretzel
  - Automatically scheduled to: John Lead
  - Date: 2025-10-15 at 12:00 PM
```

### Scenario 2: Specialist Scheduled for CORE (Lead Already Working)
```
CORE Event A: 606002-CORE-Product A
  - Scheduled to: Jane Lead (Lead Event Specialist)
  - Date: 2025-10-16 at 9:00 AM

CORE Event B: 606003-CORE-Product B
  - Scheduled to: Bob Specialist (Event Specialist)
  - Date: 2025-10-16 at 11:00 AM

Result:
  Supervisor Event B: 606003-Supervisor-Product B
  - Automatically scheduled to: Jane Lead (has CORE that day)
  - Date: 2025-10-16 at 12:00 PM
```

### Scenario 3: No Lead Working That Day
```
CORE Event: 606004-CORE-Product C
  - Scheduled to: Bob Specialist (Event Specialist)
  - Date: 2025-10-17 at 10:00 AM
  - No Leads have CORE events this day

Result:
  Supervisor Event: 606004-Supervisor-Product C
  - Automatically scheduled to: Alice Supervisor (Club Supervisor)
  - Date: 2025-10-17 at 12:00 PM
```

## Testing
Run automated tests with:
```bash
python test_supervisor_auto_scheduling.py
```

Tests verify:
- Lead with CORE gets the Supervisor event
- Another Lead with CORE gets the Supervisor when CORE goes to non-Lead
- Club Supervisor gets it when no Leads have CORE events
- All Supervisor events scheduled at 12:00 PM

## Event Durations
As of the latest update:
- **CORE events**: 390 minutes (6.5 hours)
- **Supervisor events**: 5 minutes
- **Juicer events**: 540 minutes (9 hours)
- **Digital events**: 15 minutes
- **Freeosk events**: 5 minutes
- **Other events**: 15 minutes
