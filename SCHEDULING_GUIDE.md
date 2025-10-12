# Comprehensive Scheduling Guide

## Table of Contents
1. [System Overview](#system-overview)
2. [Employee Roles and Qualifications](#employee-roles-and-qualifications)
3. [Event Types and Requirements](#event-types-and-requirements)
4. [Scheduling Constraints](#scheduling-constraints)
5. [Auto-Scheduler Methodology](#auto-scheduler-methodology)
6. [Rotation System](#rotation-system)
7. [Time Slot Assignments](#time-slot-assignments)
8. [Conflict Resolution and Bumping](#conflict-resolution-and-bumping)
9. [Manual Scheduling Guidelines](#manual-scheduling-guidelines)
10. [Special Cases and Edge Cases](#special-cases-and-edge-cases)

---

## System Overview

This scheduling system manages event assignments for retail/promotional work across multiple locations. The system assigns employees to events based on:
- Employee qualifications and job titles
- Event type requirements
- Employee availability (time off, weekly patterns)
- Date constraints (start dates, due dates)
- Workload balancing

### Core Components
- **Events**: Work visits/tasks that need employee assignments
- **Employees**: Staff members with specific roles and qualifications
- **Schedules**: Links between events and employees with specific datetimes
- **Rotations**: Recurring weekly assignments for specialized roles
- **Constraints**: Business rules that must be satisfied

### Scheduling Window
- **Auto-scheduler looks ahead**: 3 days from today
- **Earliest assignment date**: The later of (event start date) or (today + 3 days)
- **Latest assignment date**: Event due date (events must be scheduled before due date)

---

## Employee Roles and Qualifications

### Job Titles and Capabilities

#### 1. Event Specialist
- **Standard role** for most event work
- **Can work**: Core events, Other events (with limitations)
- **Cannot work**: Juicer events, Supervisor events, Digitals, Freeosk
- **Typical workload**: 1 Core event per day maximum

#### 2. Lead Event Specialist
- **Senior role** with expanded capabilities
- **Can work**: Core events, Digitals (Setup/Refresh/Teardown), Freeosk, Other events
- **Priority assignment**: Gets first pick of Core events on their available days
- **Rotation role**: Can be assigned as "Primary Lead" for specific weekdays
- **Special privileges**:
  - Prioritized for Core events in Wave 2.1
  - Required for Freeosk and Digital events
  - Fallback for Other events if Club Supervisor unavailable

#### 3. Juicer Barista
- **Specialized role** for juice bar events
- **Can work**: Juicer events (exclusive), Core events (when not juicing that day)
- **Rotation role**: Can be assigned as rotation Juicer for specific weekdays
- **Scheduling priority**: Juicer events take precedence (Wave 1)
- **Secondary assignment**: Available for Core events on non-juicing days (Wave 2.2)

#### 4. Club Supervisor
- **Management role** with special scheduling rules
- **Can work**: Supervisor events (primary), Other events, Digitals, Freeosk
- **Cannot work**: Core events (explicitly excluded)
- **Special rules**:
  - Can have unlimited overlapping Supervisor events at noon
  - Time conflicts are ignored (can be double/triple booked)
  - Only day-level availability is checked (time off, weekly pattern)
- **Fallback role**: Last resort for Digitals, Freeosk, and Other events

### Employee Attributes
- **is_active**: Only active employees are considered for scheduling
- **adult_beverage_trained**: Required for certain event types (future use)
- **external_id**: Links to external HR/scheduling systems

---

## Event Types and Requirements

### Event Type Hierarchy

#### 1. Core Events
- **Duration**: 6.5 hours (390 minutes)
- **Default times**: 9:45 AM (Primary Lead), then rotating 10:30 AM, 11:00 AM, 11:30 AM
- **Eligible employees**:
  - Lead Event Specialists (priority)
  - Juicer Baristas (when not juicing that day)
  - Event Specialists
- **Constraints**:
  - Maximum 1 Core event per employee per day
  - Club Supervisor explicitly excluded
- **Scheduling wave**: Wave 2 (3 subwaves)
- **Identification**: Project name contains "CORE"

#### 2. Juicer Events
- **Duration**: 9 hours (540 minutes)
- **Times**:
  - Juicer Production (JUICER-PRODUCTION-SPCLTY): 9:00 AM
  - Juicer Survey: 5:00 PM
  - Other Juicer events: 9:00 AM (default)
- **Eligible employees**: Juicer Baristas ONLY
- **Constraints**: Assigned via rotation system
- **Scheduling wave**: Wave 1 (highest priority)
- **Flexibility**: Can move to next day if rotation Juicer has time off
- **Identification**: Project name contains "JUICER"

#### 3. Supervisor Events
- **Duration**: 5 minutes (administrative/check-in)
- **Time**: Noon (12:00 PM) - matches paired Core event date
- **Eligible employees**:
  1. Club Supervisor (priority, can have unlimited at same time)
  2. Primary Lead (rotation-based, fallback)
- **Pairing logic**:
  - Linked to Core events by matching first 6 digits of event name
  - Scheduled on same date as corresponding Core event
  - If Core event fails to schedule, Supervisor event also fails
- **Special rules**: Time conflicts ignored (multiple can overlap)
- **Scheduling wave**: Wave 3
- **Identification**: Project name contains "SUPERVISOR"

#### 4. Digital Events (Digitals, Digital Setup, Digital Refresh, Digital Teardown)
- **Duration**: 15 minutes
- **Times**:
  - Setup/Refresh: 9:15 AM - 12:00 PM (15-min intervals)
  - Teardown: 5:00 PM - 6:45 PM (15-min intervals)
- **Eligible employees**:
  1. Primary Lead (rotation-based, Setup/Refresh)
  2. Secondary Lead (any other Lead, Teardown)
  3. Other Lead Event Specialists
  4. Club Supervisor (fallback)
- **Date constraint**: MUST be scheduled on event start date (no flexibility)
- **Special rules**:
  - Time conflicts checked for Leads
  - Time conflicts ignored for Club Supervisor
  - Only day-level availability checked (time off, weekly pattern)
- **Scheduling wave**: Wave 4
- **Identification**: Project name contains "DIGITAL", "SETUP", "REFRESH", "TEARDOWN"

#### 5. Freeosk Events
- **Duration**: 15 minutes
- **Time**: 9:00 AM
- **Eligible employees**:
  1. Primary Lead (rotation-based)
  2. Other Lead Event Specialists
  3. Club Supervisor (fallback)
- **Date constraint**: MUST be scheduled on event start date
- **Special rules**: Same as Digital events
- **Scheduling wave**: Wave 4
- **Identification**: Project name contains "FREEOSK"

#### 6. Other Events
- **Duration**: 15 minutes
- **Time**: Noon (12:00 PM)
- **Eligible employees**:
  1. Club Supervisor (priority)
  2. ANY Lead Event Specialist (fallback)
- **Special rules**: Time conflicts ignored
- **Scheduling wave**: Wave 5 (lowest priority)
- **Identification**: Catch-all for events not matching other types

### Event Attributes
- **project_ref_num**: Unique identifier (6+ digits)
- **project_name**: Descriptive name (used for type detection)
- **start_datetime**: Earliest date event can be scheduled
- **due_datetime**: Latest date event can be scheduled (deadline)
- **estimated_time**: Duration in minutes
- **is_scheduled**: Boolean flag indicating if assigned
- **condition**: Status (Unstaffed, Staffed, etc.)
- **store_number/store_name**: Location information
- **sales_tools_url**: Reference materials for Core events

---

## Scheduling Constraints

### Hard Constraints (MUST be satisfied)

#### 1. Time Off Constraint
- **Rule**: Employee cannot be scheduled during time-off periods
- **Check**: Compare schedule date against EmployeeTimeOff table
- **Violation**: Schedule is invalid if employee has time off
- **Model**: `EmployeeTimeOff` (start_date, end_date ranges)

#### 2. Weekly Availability Constraint
- **Rule**: Employee must be available on the specific day of week
- **Check**: Match schedule day (Monday-Sunday) against EmployeeWeeklyAvailability
- **Default**: All days available if no record exists
- **Violation**: Schedule is invalid if day marked as unavailable
- **Model**: `EmployeeWeeklyAvailability` (boolean columns for each day)

#### 3. Role Requirements Constraint
- **Rule**: Employee job title must match event type requirements
- **Checks**:
  - Juicer events → Juicer Barista only
  - Digitals/Freeosk/Other → Lead Event Specialist or Club Supervisor
  - Core events → Event Specialist, Lead, or Juicer (not Club Supervisor)
  - Supervisor events → Club Supervisor or Primary Lead
- **Violation**: Schedule is invalid if role doesn't match
- **Method**: `Employee.can_work_event_type(event_type)`

#### 4. Daily Limit Constraint
- **Rule**: Maximum 1 Core event per employee per day
- **Check**: Count existing Core schedules for employee on target date
- **Includes**: Both committed schedules and pending schedules from current run
- **Violation**: Schedule is invalid if limit exceeded
- **Applies to**: Core events only (other types have no daily limit)

#### 5. Already Scheduled Constraint
- **Rule**: Employee cannot have two events at the exact same datetime
- **Check**: Query for existing schedule at proposed datetime
- **Includes**: Both committed schedules and pending schedules from current run
- **Exception**: Club Supervisor can have multiple Supervisor events at noon
- **Violation**: Schedule is invalid if time slot occupied

#### 6. Due Date Constraint
- **Rule**: Event must be scheduled before its due date
- **Check**: Verify schedule_datetime.date() < event.due_datetime.date()
- **Violation**: Schedule is invalid if scheduled on or after due date

### Soft Constraints (Should be satisfied but can be violated)

#### 1. Club Supervisor Usage
- **Guideline**: Club Supervisor should not be assigned to regular events
- **Severity**: Soft constraint (warning only)
- **Exception**: Acceptable for Supervisor, Digitals, Freeosk, Other events
- **Reason**: Management role should focus on supervisory duties

### Special Constraint Rules

#### Club Supervisor Special Cases
The Club Supervisor has unique scheduling rules:
1. **Supervisor events**: Unlimited overlap at noon allowed
2. **Digitals/Freeosk/Other events**: Only day-level checks (time off, weekly availability)
3. **Time conflicts**: Completely ignored for Club Supervisor
4. **Core events**: Explicitly excluded (hard constraint)

#### Juicer Barista Special Cases
1. **Wave 1 priority**: Juicer events scheduled first
2. **Core event eligibility**: Only available on days without Juicer assignments
3. **Rotation-based**: Juicer events use rotation system (not free assignment)

#### Lead Event Specialist Special Cases
1. **Primary Lead rotation**: Some Leads designated as Primary Lead by day
2. **Core event priority**: Lead gets first pick (Wave 2.1) before others
3. **Multiple eligible events**: Can work Core, Digitals, Freeosk, Other

---

## Auto-Scheduler Methodology

### Scheduling Philosophy
The auto-scheduler uses a **wave-based priority system** to ensure critical events are scheduled first and employees are utilized efficiently. Events are scheduled in 5 waves, with higher-priority events claiming time slots before lower-priority ones.

### Scheduling Waves

#### Wave 1: Juicer Events (Highest Priority)
**Target**: All unscheduled Juicer events
**Assignment logic**:
1. Get rotation-assigned Juicer for event's start date
2. Check if Juicer is available (time off, weekly availability)
3. If unavailable, try next day (up to due date)
4. Continue day-by-day until Juicer available or due date reached

**Time assignment**:
- JUICER-PRODUCTION-SPCLTY: 9:00 AM
- Juicer Survey: 5:00 PM
- Default: 9:00 AM

**Success**: Create PendingSchedule with assigned employee
**Failure**: Create failed PendingSchedule with reason

**Why first?**: Juicer events are inflexible (rotation-based, specialized) and must be scheduled before Core events to prevent Juicers being unavailable for their primary duty.

---

#### Wave 2: Core Events (3 Subwaves)
**Target**: All unscheduled Core events
**Assignment priority order**:

##### Subwave 2.1: Lead Event Specialists (Highest Sub-Priority)
- **Strategy**: Prioritize filling Lead schedules on their available days
- **Logic**: Try to assign to Lead, even if event could start earlier
- **Time slots**: Rotating (9:45 AM, 10:30 AM, 11:00 AM, 11:30 AM)
- **Check**: Validate against all constraints
- **Success**: Mark event as scheduled, skip remaining subwaves

##### Subwave 2.2: Juicer Baristas (When Not Juicing)
- **Strategy**: Utilize Juicers on days they don't have Juicer events
- **Logic**:
  1. Check if Juicer has Juicer event on target date
  2. Only assign if NO Juicer event that day
- **Time slots**: Same rotating slots
- **Success**: Mark event as scheduled, skip remaining subwaves

##### Subwave 2.3: Event Specialists (Lowest Sub-Priority)
- **Strategy**: Standard event specialists handle remaining Core events
- **Logic**: Try each specialist until one passes validation
- **Time slots**: Same rotating slots
- **Failure**: Create failed PendingSchedule with reason

**Core Time Slot Rotation**:
- Slots: 9:45 AM, 10:30 AM, 11:00 AM, 11:30 AM
- Rotation: Per date (increments for each event scheduled that day)
- Example: 3 Core events on Monday → 9:45, 10:30, 11:00

---

#### Wave 3: Supervisor Events (Paired with Core)
**Target**: All unscheduled Supervisor events
**Pairing logic**:
1. Extract first 6 digits from Supervisor event name
2. Find Core event with matching 6 digits
3. Get Core event's scheduled date (from Wave 2)
4. Schedule Supervisor event same date at noon

**Assignment priority**:
1. **Club Supervisor** (priority):
   - Can have unlimited Supervisor events at noon
   - Only check day-level availability (time off, weekly pattern)
   - Ignore time conflicts
2. **Primary Lead** (fallback):
   - Use rotation system to find Primary Lead for that day
   - Check day-level availability
   - Assign if Club Supervisor unavailable

**Time**: Always noon (12:00 PM)

**Special rules**:
- If Core event failed to schedule → Supervisor event also fails
- Multiple Supervisor events can overlap (no time conflict checking)
- Must schedule on same date as paired Core event

---

#### Wave 4: Freeosk and Digital Events
**Target**: Freeosk, Digital Setup, Digital Refresh, Digital Teardown events
**Date constraint**: MUST schedule on event start date (no flexibility)

##### Digital Setup and Digital Refresh
**Time slots**: 9:15 AM - 12:00 PM (15-minute intervals)
- 9:15, 9:30, 9:45, 10:00, 10:15, 10:30, 10:45, 11:00, 11:15, 11:30, 11:45, 12:00
- Rotates for each event on that day

**Assignment priority**:
1. Primary Lead (rotation-based for that day)
2. Other Lead Event Specialists
3. Club Supervisor (fallback, no time conflict checks)

##### Digital Teardown
**Time slots**: 5:00 PM - 6:45 PM (15-minute intervals)
- 17:00, 17:15, 17:30, 17:45, 18:00, 18:15, 18:30, 18:45
- Rotates for each event on that day

**Assignment priority**:
1. Secondary Lead (any Lead except Primary Lead)
2. Club Supervisor (fallback, no time conflict checks)

##### Freeosk
**Time**: 9:00 AM (fixed)

**Assignment priority**:
1. Primary Lead (rotation-based for that day)
2. Other Lead Event Specialists
3. Club Supervisor (fallback)

**Constraint checking for all Wave 4 events**:
- Leads: Time off + weekly availability only (no time conflict checks)
- Club Supervisor: Time off + weekly availability only (no time conflict checks)
- Date flexibility: NONE (must be on start date)

---

#### Wave 5: Other Events (Lowest Priority)
**Target**: All remaining "Other" events
**Time**: Noon (12:00 PM)
**Assignment priority**:
1. **Club Supervisor** (priority):
   - Only check day-level availability
   - Ignore time conflicts
2. **ANY Lead Event Specialist** (fallback):
   - First available Lead gets assigned
   - Only check day-level availability
   - No time conflict checks

**Why last?**: Other events are catch-all/miscellaneous and least critical.

---

### Event Priority Sorting

Before wave processing, events are sorted by:
1. **Primary**: Due date (earlier due date = higher priority)
2. **Secondary**: Event type priority score

**Event Type Priority Scores** (lower = higher priority):
```
'Juicer': 1
'Digital Setup': 2
'Digital Refresh': 3
'Freeosk': 4
'Digital Teardown': 5
'Core': 6
'Supervisor': 7
'Digitals': 8
'Other': 9
```

---

### Scheduling Run Workflow

1. **Create run record**: `SchedulerRunHistory` tracks execution
2. **Get unscheduled events**: Query for `is_scheduled=False` and `condition='Unstaffed'`
3. **Sort events by priority**: Due date first, then event type
4. **Execute Wave 1**: Schedule Juicer events
5. **Execute Wave 2**: Schedule Core events (3 subwaves)
6. **Execute Wave 3**: Schedule Supervisor events
7. **Execute Wave 4**: Schedule Freeosk and Digital events
8. **Execute Wave 5**: Schedule Other events
9. **Create PendingSchedule records**: All proposals stored for review
10. **Update run statistics**: Total processed, scheduled, failed
11. **Mark run complete**: Set status and completion time

---

### Pending Schedule Workflow

The auto-scheduler creates **proposals** (PendingSchedule records) rather than immediately committing schedules. This allows:
- **Human review**: User can review all proposed assignments
- **Editing**: User can manually adjust assignments before approval
- **Bulk approval**: All proposals approved at once
- **API submission**: Approved schedules submitted to external system

**PendingSchedule States**:
1. **proposed**: Initial state after auto-scheduler run
2. **user_edited**: User manually changed the assignment
3. **approved**: User approved the proposal (ready for API)
4. **api_submitted**: Successfully sent to external system
5. **api_failed**: API submission failed (needs retry)

---

## Rotation System

### Purpose
Rotations ensure consistent weekly assignments for specialized roles:
- **Juicer rotation**: Assigns specific Juicer Baristas to specific weekdays
- **Primary Lead rotation**: Assigns specific Lead Event Specialists to specific weekdays

### Rotation Types

#### 1. Juicer Rotation
- **Purpose**: Assign Juicer events to consistent employees per day
- **Frequency**: Weekly pattern (Monday-Friday typically)
- **Flexibility**: If rotation Juicer unavailable, try next day
- **Model**: `RotationAssignment` with `rotation_type='juicer'`

#### 2. Primary Lead Rotation
- **Purpose**: Designate "lead" for each day (handles Digitals, Freeosk, gets first Core pick)
- **Frequency**: Weekly pattern (Monday-Friday typically)
- **Priority**: Primary Lead gets 9:45 AM slot for Core events
- **Model**: `RotationAssignment` with `rotation_type='primary_lead'`

### Rotation Configuration

**Data structure**:
```python
{
    'juicer': {
        0: 'EMP001',  # Monday
        1: 'EMP002',  # Tuesday
        2: 'EMP001',  # Wednesday
        3: 'EMP003',  # Thursday
        4: 'EMP002',  # Friday
    },
    'primary_lead': {
        0: 'LEAD001',  # Monday
        1: 'LEAD002',  # Tuesday
        2: 'LEAD001',  # Wednesday
        3: 'LEAD003',  # Thursday
        4: 'LEAD002',  # Friday
    }
}
```

**Days of week**: 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday

### Rotation Exceptions

**Purpose**: Override rotation for specific dates (vacations, special events)

**Example use cases**:
- Regular Monday Juicer has vacation on specific Monday
- Primary Lead has time off on specific day
- Special event requires different assignment

**Model**: `ScheduleException`
- `exception_date`: Specific date for override
- `rotation_type`: 'juicer' or 'primary_lead'
- `employee_id`: Employee to assign instead
- `reason`: Optional explanation

**Priority**: Exceptions take precedence over weekly rotation pattern

### Rotation Lookup Logic

```python
def get_rotation_employee(target_date, rotation_type):
    # 1. Check for one-time exception first
    exception = query_exception(target_date, rotation_type)
    if exception:
        return exception.employee

    # 2. Fall back to weekly rotation
    day_of_week = target_date.weekday()  # 0-6
    rotation = query_rotation(day_of_week, rotation_type)
    return rotation.employee if rotation else None
```

### Secondary Lead

**Definition**: Any Lead Event Specialist who is NOT the Primary Lead for that day

**Purpose**: Handle Digital Teardown events (which need Lead but not necessarily Primary)

**Logic**:
1. Find Primary Lead for target date
2. Query all Lead Event Specialists
3. Exclude Primary Lead from results
4. Return first available Lead

---

## Time Slot Assignments

### Core Events Time Slots

**Slots**: 9:45 AM, 10:30 AM, 11:00 AM, 11:30 AM

**Rotation logic**:
- Per date (each date has independent counter)
- Increments for each Core event scheduled that day
- Wraps around: After 11:30, next event gets 9:45

**Special case - Primary Lead**:
- Primary Lead gets 9:45 AM slot (priority)
- If Primary Lead unavailable or already has 9:45, use rotation

**Example**:
```
Monday Core events:
Event A → Primary Lead → 9:45 AM (priority slot)
Event B → Event Specialist → 10:30 AM (rotation slot 1)
Event C → Lead Event Specialist → 11:00 AM (rotation slot 2)
Event D → Event Specialist → 11:30 AM (rotation slot 3)
Event E → Juicer Barista → 9:45 AM (rotation wraps, slot 0)
```

### Digital Setup/Refresh Time Slots

**Slots**: 9:15 AM - 12:00 PM (15-minute intervals)
- 9:15, 9:30, 9:45, 10:00, 10:15, 10:30, 10:45, 11:00, 11:15, 11:30, 11:45, 12:00

**Rotation logic**:
- Per date (each date has independent counter)
- Increments for each Digital Setup/Refresh scheduled that day
- Wraps around after 12:00

**Example**:
```
Monday Digital events:
Digital Setup A → 9:15 AM
Digital Refresh B → 9:30 AM
Digital Setup C → 9:45 AM
```

### Digital Teardown Time Slots

**Slots**: 5:00 PM - 6:45 PM (15-minute intervals)
- 17:00, 17:15, 17:30, 17:45, 18:00, 18:15, 18:30, 18:45

**Rotation logic**:
- Per date (each date has independent counter)
- Increments for each Digital Teardown scheduled that day
- Wraps around after 18:45

### Fixed Time Slots

**Juicer Production**: 9:00 AM (fixed)
**Juicer Survey**: 5:00 PM (fixed)
**Other Juicer**: 9:00 AM (default)
**Supervisor**: 12:00 PM (noon, fixed)
**Freeosk**: 9:00 AM (fixed)
**Other**: 12:00 PM (noon, fixed)

---

## Conflict Resolution and Bumping

### Bumping Strategy

**Purpose**: When no employees available for high-priority event, "bump" a lower-priority event to make room

**Not currently implemented in production waves**, but infrastructure exists for future use.

### Priority Scoring

**Formula**: `priority_score = days_until_due_date`
- Lower score = higher priority (more urgent)
- Higher score = lower priority (more time available)

**Example**:
- Event due in 2 days: priority_score = 2 (HIGH priority)
- Event due in 10 days: priority_score = 10 (LOW priority)

### Bumpable Event Criteria

An event can be bumped if:
1. **Not too close to due date**: At least 2 days until due date
2. **Not a Supervisor event**: Supervisor events are paired with Core, cannot bump
3. **Lower priority than requesting event**: Must have higher priority_score
4. **Currently scheduled**: Must have existing schedule to bump

### Bumping Process (Theoretical)

1. **Identify conflict**: No employees available for Event A at desired time
2. **Find bumpable events**: Query scheduled events on that date for same employee
3. **Calculate priority scores**: Compare Event A score vs. scheduled events
4. **Select candidate**: Choose lowest-priority (highest score) bumpable event
5. **Validate swap**: Ensure bump makes logical sense
6. **Create swap proposal**: PendingSchedule with `is_swap=True`
7. **Human review**: User approves or rejects bump

### Swap Proposal

**Fields**:
- `is_swap`: Boolean flag indicating this is a bump
- `bumped_event_ref_num`: Reference to event being bumped
- `swap_reason`: Explanation of why bump is needed

**User review**:
- User sees both events involved
- User can accept, reject, or modify the swap
- Bumped event needs rescheduling (manual or next auto-run)

---

## Manual Scheduling Guidelines

### When to Schedule Manually

1. **Failed auto-schedule attempts**: Event couldn't be auto-assigned
2. **Rush assignments**: Event needs immediate scheduling (within 3-day window)
3. **Special requests**: Client requested specific employee
4. **Rotation exceptions**: One-time override of rotation
5. **Workload balancing**: Distribute work more evenly

### Manual Scheduling Best Practices

#### 1. Check Employee Availability
Before assigning:
- ✓ Verify no time-off conflicts
- ✓ Check weekly availability pattern
- ✓ Confirm no existing schedule at same time
- ✓ Verify employee role matches event type

#### 2. Respect Rotation Assignments
When manually scheduling:
- **Juicer events**: Prefer rotation-assigned Juicer for that day
- **Digital/Freeosk events**: Prefer rotation-assigned Primary Lead
- **Exceptions**: Create ScheduleException record if overriding rotation

#### 3. Follow Time Slot Guidelines
- **Core events**: Use standard slots (9:45, 10:30, 11:00, 11:30)
- **Juicer events**: 9 AM for production, 5 PM for surveys
- **Supervisor events**: Always noon (12:00 PM)
- **Digital events**: Use 15-minute intervals as specified

#### 4. Maintain Daily Limits
- **Core events**: Maximum 1 per employee per day
- **Other types**: No strict limits, but consider workload

#### 5. Pair Supervisor with Core
When manually scheduling Supervisor events:
1. Find corresponding Core event (match first 6 digits)
2. Schedule Supervisor same date as Core
3. Always use noon time slot
4. Prefer Club Supervisor

#### 6. Consider Due Dates
- **Priority**: Events closer to due date should be scheduled first
- **Buffer**: Try to schedule at least 2 days before due date
- **Urgency**: Never schedule on or after due date

### Manual Override Scenarios

#### Override Time Conflicts (Club Supervisor Only)
- Club Supervisor can have multiple Supervisor events at noon
- Club Supervisor can have Digitals/Freeosk/Other overlapping
- This is acceptable per business rules

#### Override Rotation (Create Exception)
If assigning different employee than rotation:
1. Create `ScheduleException` record for that date
2. Document reason (vacation, special request, etc.)
3. Exception takes precedence for that date only
4. Normal rotation resumes next occurrence

#### Override Daily Limit (Not Recommended)
- Core event daily limit is hard constraint
- Override only in emergencies
- Document reason clearly
- Consider assigning to different employee instead

### Manual Scheduling Workflow

1. **Identify event**: Find unscheduled event needing assignment
2. **Check event type**: Determine eligible employee roles
3. **Review date range**: Note start_datetime and due_datetime
4. **Check rotation**: If applicable, find rotation-assigned employee
5. **Verify availability**: Check time off and weekly pattern
6. **Check conflicts**: Ensure no existing schedule at proposed time
7. **Select time slot**: Use appropriate time based on event type
8. **Create schedule**: Add Schedule record
9. **Update event status**: Set `is_scheduled=True`, `condition='Staffed'`
10. **Notify employee** (future feature): Send assignment notification

---

## Special Cases and Edge Cases

### 1. Supervisor Event Without Matching Core
**Scenario**: Supervisor event exists but no Core event with matching number

**Detection**: Extract first 6 digits from event name, no Core event found

**Handling**:
- Auto-scheduler creates failed PendingSchedule
- Reason: "No Core event found with event number XXXXXX"
- **Manual resolution**:
  - Verify event number is correct
  - Check if Core event is missing from system
  - May schedule manually if Supervisor-only event is valid

### 2. Core Event Fails, Supervisor Event Blocked
**Scenario**: Core event couldn't be scheduled, linked Supervisor event exists

**Detection**: Core event has failed PendingSchedule, Supervisor event depends on it

**Handling**:
- Auto-scheduler skips Supervisor event
- Reason: "Core event failed to schedule: [core failure reason]"
- **Manual resolution**:
  - Fix Core event scheduling first (assign manually or adjust constraints)
  - Re-run auto-scheduler or manually schedule Supervisor

### 3. Juicer Unavailable All Days Until Due Date
**Scenario**: Rotation Juicer has time off for entire event window

**Detection**: Loop through start_date to due_date, all days have time-off or unavailable

**Handling**:
- Auto-scheduler creates failed PendingSchedule
- Reason: "No available Juicer rotation employee before due date"
- **Manual resolution**:
  - Create ScheduleException to assign different Juicer for specific day
  - Or adjust Juicer's time-off dates if incorrect
  - Or manually assign any Juicer Barista

### 4. No Primary Lead for Day
**Scenario**: Rotation not configured for specific day (e.g., Saturday, weekend)

**Detection**: `get_rotation_employee(date, 'primary_lead')` returns None

**Handling**:
- Freeosk/Digital events try other Lead Event Specialists
- Falls back to Club Supervisor
- **Manual resolution**:
  - Configure rotation for that day
  - Or manually assign any Lead Event Specialist

### 5. All Leads Unavailable (Freeosk/Digital)
**Scenario**: All Lead Event Specialists and Club Supervisor have time off

**Detection**: Wave 4 tries Primary Lead → Other Leads → Club Supervisor, all unavailable

**Handling**:
- Auto-scheduler creates failed PendingSchedule
- Reason: "No Lead or Club Supervisor available on [day] - This should not happen!"
- **Manual resolution**:
  - Adjust employee availability if incorrect
  - Create ScheduleException to assign specific Lead
  - Reschedule event if possible (change start_date)

### 6. Event Start Date in the Past
**Scenario**: Event imported with start_date before today

**Detection**: `_get_earliest_schedule_date()` returns today + 3 days (scheduling window)

**Handling**:
- Event can still be scheduled, but earliest date is today + 3 days
- If due_date also in past, event cannot be scheduled
- **Manual resolution**:
  - Update event start_date and due_date to future dates
  - Or schedule manually within 3-day window (override window rule)

### 7. Event Due Date Already Passed
**Scenario**: Event due_date is today or earlier

**Detection**: Constraint validator checks `schedule_datetime.date() >= event.due_datetime.date()`

**Handling**:
- Event cannot be scheduled (violates due date constraint)
- **Manual resolution**:
  - Update event due_date to future date
  - Or mark event as cancelled/expired

### 8. Multiple Core Events, Only 1 Employee Available
**Scenario**: 5 Core events on Monday, only 1 Event Specialist available

**Detection**: Wave 2 subwaves try each employee, only 1 passes validation

**Handling**:
- First event gets assigned to available employee
- Remaining 4 events fail (daily limit constraint)
- **Manual resolution**:
  - Adjust employee availability to make more employees available
  - Reschedule some events to different days
  - Create ScheduleException if needed

### 9. Club Supervisor Multiple Supervisor Events at Noon
**Scenario**: 10 Supervisor events all scheduled for same noon time slot

**Detection**: This is expected behavior

**Handling**:
- All assigned to Club Supervisor
- No time conflict violations (special rule)
- Club Supervisor sees consolidated list of Supervisor checks
- **This is normal**: Supervisor events are quick check-ins (5 min each)

### 10. Digital Event on Start Date, Start Date is Weekend
**Scenario**: Digital Setup event start_date is Saturday, no rotation for weekends

**Detection**: Wave 4 tries to schedule on start_date, no Primary Lead for Saturday

**Handling**:
- Falls back to other Lead Event Specialists
- Falls back to Club Supervisor
- If all unavailable, event fails
- **Manual resolution**:
  - Configure rotation for weekends if needed
  - Manually assign any Lead Event Specialist
  - Or negotiate with client to reschedule event to weekday

### 11. Pending Schedule Edited by User
**Scenario**: Auto-scheduler proposed Assignment A, user manually changed to Assignment B

**Detection**: PendingSchedule status changed to 'user_edited'

**Handling**:
- System respects user edit
- When approved, uses user's assignment (not original proposal)
- **Validation**: Ensure user edit still satisfies hard constraints

### 12. API Submission Fails
**Scenario**: PendingSchedule approved and submitted to external API, API returns error

**Detection**: API response indicates failure (network, validation, etc.)

**Handling**:
- PendingSchedule status set to 'api_failed'
- Error details stored in `api_error_details` field
- Schedule remains in pending state (not committed)
- **Manual resolution**:
  - Review API error details
  - Fix issue (bad employee ID, bad date format, etc.)
  - Retry API submission

### 13. Employee Deactivated After Schedule Created
**Scenario**: Employee scheduled for future event, then marked as `is_active=False`

**Detection**: Query schedules for inactive employees

**Handling**:
- Existing schedules remain (historical record)
- Employee no longer appears in available employees for new assignments
- **Manual resolution**:
  - Reassign affected future schedules to active employees
  - Run report to find all schedules for inactive employees

### 14. Rotation Changed Mid-Week
**Scenario**: Monday-Wednesday scheduled with EMP001 as Primary Lead, rotation changed Thursday to EMP002

**Detection**: Historical rotation data vs. current rotation configuration

**Handling**:
- Already-scheduled events keep original assignments
- New events (Thursday onwards) use new rotation
- **Best practice**: Change rotations on Sunday/Monday (week boundary)

### 15. Same Event Number, Multiple Event Types
**Scenario**: Event 595831-CORE and Event 595831-SUPERVISOR, but also 595831-OTHER exists

**Detection**: Supervisor event pairing looks for matching Core only

**Handling**:
- Supervisor event pairs with Core (by design)
- Other event with same number is unrelated (scheduled independently)
- **This is rare but acceptable**

---

## Appendix: Key Files Reference

### Models
- `models/employee.py`: Employee roles and qualifications
- `models/event.py`: Event types and attributes
- `models/schedule.py`: Schedule assignments
- `models/auto_scheduler.py`: Rotations, pending schedules, exceptions
- `models/availability.py`: Time off and weekly availability patterns

### Services
- `services/scheduling_engine.py`: Core auto-scheduler logic (5 waves)
- `services/constraint_validator.py`: Business rule validation
- `services/rotation_manager.py`: Rotation lookups and exceptions
- `services/conflict_resolver.py`: Bumping strategy (future use)

### Routes
- `routes/scheduling.py`: Manual scheduling endpoints
- `routes/auto_scheduler.py`: Auto-scheduler execution and review
- `routes/employees.py`: Employee management
- `routes/rotations.py`: Rotation configuration

---

## Glossary

**Auto-scheduler**: Automated system that assigns employees to events based on constraints and priorities

**Bumping**: Rescheduling a lower-priority event to make room for a higher-priority event

**Constraint**: Business rule that limits scheduling options (time off, role requirements, etc.)

**Core event**: Standard retail/promotional event requiring 6.5 hours of work

**Due date**: Latest date an event can be scheduled (deadline)

**Hard constraint**: Rule that MUST be satisfied (violating makes schedule invalid)

**Pending schedule**: Proposed assignment awaiting user approval

**Primary Lead**: Lead Event Specialist assigned to specific weekdays in rotation

**Rotation**: Recurring weekly assignment pattern for specialized roles

**Schedule exception**: One-time override of rotation for specific date

**Scheduling window**: 3-day buffer where auto-scheduler doesn't assign events

**Secondary Lead**: Any Lead Event Specialist who is not the Primary Lead for that day

**Soft constraint**: Rule that SHOULD be satisfied but can be violated if necessary

**Start date**: Earliest date an event can be scheduled

**Supervisor event**: Quick check-in (5 min) paired with Core event, scheduled at noon

**Wave**: Phase of auto-scheduler execution with specific event types and priorities

---

**Document Version**: 1.0
**Last Updated**: Generated from codebase analysis
**Maintainer**: Auto-generated from scheduling system source code
