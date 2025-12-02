# Scheduling Rules Reference Guide

> **Last Updated:** 2025-12-02
> **Version:** 1.0
> **Purpose:** Complete reference for manually scheduling employees to events without errors

---

## Table of Contents

1. [Quick Reference Decision Tree](#quick-reference-decision-tree)
2. [Employee Roles & Qualifications](#employee-roles--qualifications)
3. [Event Types & Scheduling Requirements](#event-types--scheduling-requirements)
4. [Time Slot Rules](#time-slot-rules)
5. [Constraint Rules (HARD - Cannot Be Violated)](#constraint-rules-hard---cannot-be-violated)
6. [Soft Constraints (Warnings - Can Override)](#soft-constraints-warnings---can-override)
7. [Auto-Scheduler Priority Waves](#auto-scheduler-priority-waves)
8. [Special Scenarios & Edge Cases](#special-scenarios--edge-cases)
9. [Validation Checklist](#validation-checklist)

---

## Quick Reference Decision Tree

```
1. IS THE DATE VALID?
   |-- Is the date a Company Holiday? --> STOP: Cannot schedule
   |-- Is the date within event's start/due window? --> NO: STOP
   |-- Continue...

2. IS THE EMPLOYEE AVAILABLE?
   |-- Employee has Time-Off on this date? --> STOP: Cannot schedule
   |-- Employee marked unavailable for this date? --> STOP
   |-- Employee's weekly availability includes this day? --> NO: WARNING (can override)
   |-- Continue...

3. DOES EMPLOYEE HAVE CORRECT ROLE?
   |-- See "Role Requirements by Event Type" table below
   |-- Continue if role matches...

4. CHECK DAILY LIMITS
   |-- For Core events: Does employee already have 1 Core event today? --> STOP
   |-- For Juicer events: Is this a Juicer Barista doing Juicer work? --> OK
   |-- Continue...

5. CHECK TIME CONFLICTS
   |-- Does the proposed time overlap with another scheduled event? --> STOP
   |-- Events within 2 hours of each other? --> WARNING

6. SCHEDULE THE EVENT
```

---

## Employee Roles & Qualifications

### Role Hierarchy

| Role | Code | Capabilities |
|------|------|-------------|
| **Club Supervisor** | `Club Supervisor` | Supervisor events, Freeosk, Digitals, Other; Should NOT do Core events |
| **Lead Event Specialist** | `Lead Event Specialist` | Core, Freeosk, Digitals, Digital Setup/Refresh/Teardown, Other |
| **Event Specialist** | `Event Specialist` | Core events only |
| **Juicer Barista** | `Juicer Barista` | Juicer events (priority), Core events (when not doing Juicer) |

### Role Requirements by Event Type

| Event Type | Allowed Roles | Notes |
|-----------|---------------|-------|
| **Core** | Event Specialist, Lead Event Specialist, Juicer Barista* | *Only when not assigned to Juicer that day |
| **Supervisor** | Club Supervisor ONLY | Auto-paired with Core events |
| **Juicer** | Juicer Barista ONLY | Takes priority over Core events |
| **Freeosk** | Lead Event Specialist, Club Supervisor | Primary Lead has priority |
| **Digitals** | Lead Event Specialist, Club Supervisor | Generic digital events |
| **Digital Setup** | Lead Event Specialist, Club Supervisor | Morning events |
| **Digital Refresh** | Lead Event Specialist, Club Supervisor | Same as Digital Setup |
| **Digital Teardown** | Lead Event Specialist, Club Supervisor | Evening events |
| **Other** | Club Supervisor, Lead Event Specialist | Supervisor gets priority |

### Critical Role Restrictions

1. **Juicer Baristas have dual-role capability:**
   - If assigned to Juicer event on a day, they **cannot** do Core on that day
   - If NOT assigned to Juicer, they **can** do Core events

2. **Club Supervisors should NOT be scheduled for Core events**
   - This is a SOFT constraint (warning, not error)
   - Supervisors should focus on Supervisor, Freeosk, and Other events

3. **Event Specialists are Core-only**
   - Cannot be assigned to Freeosk, Digitals, or Other events

---

## Event Types & Scheduling Requirements

### Event Type Priority Order (for Auto-Scheduler)

| Priority | Event Type | Reason |
|---------|-----------|--------|
| 1 (Highest) | Juicer | Rotation-based, can bump Core events |
| 2 | Digital Setup | Morning prep work |
| 3 | Digital Refresh | Mid-day digital work |
| 4 | Freeosk | Morning Lead work |
| 5 | Digital Teardown | End-of-day cleanup |
| 6 | Core | Main demo events |
| 7 | Supervisor | Paired with Core events |
| 8 | Digitals | Generic digital category |
| 9 (Lowest) | Other | Catch-all category |

### Event Duration Defaults

| Event Type | Work Time | Lunch | Total Duration | Notes |
|-----------|-----------|-------|----------------|-------|
| Core | 360 min (6 hrs) | 30 min | **390 minutes** | Full demo with 30-min lunch break |
| Supervisor | 5 min | - | **5 minutes** | Quick check-in at noon |
| Juicer Production | 480 min (8 hrs) | 60 min | **540 minutes** | Full day + 1-hour lunch |
| Juicer Survey | 30 min | - | **30 minutes** | End-of-day survey |
| Digital Setup | 30 min | - | **30 minutes** | Morning only |
| Digital Refresh | 30 min | - | **30 minutes** | Morning only |
| Digital Teardown | 30 min | - | **30 minutes** | Evening only |
| Freeosk | 30 min | - | **30 minutes** | Morning task |
| Other | 60 min | - | **60 minutes** | One hour default |

---

## Time Slot Rules

### Core Event Time Slots (Configured in Database Settings)

| Slot | Start Time | Lunch Begin | Lunch End | End Time | Duration |
|------|-----------|-------------|-----------|----------|----------|
| 1 | 10:45 | 13:30 | 14:00 | 17:15 | 390 min (6.5 hrs) |
| 2 | 11:15 | 14:15 | 14:45 | 17:45 | 390 min (6.5 hrs) |
| 3 | 11:45 | 14:45 | 15:15 | 18:15 | 390 min (6.5 hrs) |
| 4 | 12:15 | 15:45 | 16:15 | 18:45 | 390 min (6.5 hrs) |

**Note:** Each Core slot = 360 min work + 30 min lunch = 390 min total

**Rule:** Only ONE Core event per employee per day.

### Digital Setup/Refresh Time Slots

| Slot | Start Time | End Time | Duration |
|------|-----------|----------|----------|
| 1 | 10:15 | 10:45 | 30 min |
| 2 | 10:30 | 11:00 | 30 min |
| 3 | 10:45 | 11:15 | 30 min |
| 4 | 11:00 | 11:30 | 30 min |

### Digital Teardown Time Slots

| Slot | Start Time | End Time | Duration |
|------|-----------|----------|----------|
| 1 | 18:00 | 18:30 | 30 min |
| 2 | 18:15 | 18:45 | 30 min |
| 3 | 18:30 | 19:00 | 30 min |
| 4 | 18:45 | 19:15 | 30 min |
| 5+ | 19:00+ | Extended hours | 30 min |

### Fixed Time Events

| Event Type | Fixed Start Time | Duration | Notes |
|-----------|-----------------|----------|-------|
| Freeosk | 10:00 | 30 min | Morning task |
| Supervisor | 12:00 | 5 min | Noon check-in |
| Juicer Production | 09:00 | 540 min (9 hrs) | Full day + 1-hr lunch |
| Juicer Survey | 17:00 | 30 min | End-of-day survey |
| Other | 11:00 | 60 min | Default |

---

## Constraint Rules (HARD - Cannot Be Violated)

These constraints will **prevent** scheduling and show an **error**:

### 1. Company Holiday Check
- **Rule:** No events can be scheduled on Company Holidays
- **Source:** `CompanyHoliday.is_holiday(date)`
- **Message:** "Cannot schedule on {date} - Company Holiday: {holiday_name}"

### 2. Time-Off Check
- **Rule:** Cannot schedule employee who has approved time-off
- **Check:** `EmployeeTimeOff` table for overlapping dates
- **Message:** "Employee {name} has requested time off on {date}"

### 3. Date-Specific Unavailability
- **Rule:** Cannot schedule if employee marked specific date unavailable
- **Check:** `EmployeeAvailability` table where `is_available = false`
- **Message:** "{name} is marked as unavailable on {date}"

### 4. Weekly Availability (HARD in some contexts)
- **Rule:** Employee must be available on day of week
- **Check:** `EmployeeWeeklyAvailability` columns (monday through sunday)
- **Message:** "Employee {name} not available on {day_name}"

### 5. Role Requirements
- **Rule:** Employee must have authorized role for event type
- **Juicer events:** Requires `Juicer Barista` role
- **Lead-only events:** Requires `Lead Event Specialist` or `Club Supervisor`
  - Lead-only types: Freeosk, Digitals, Digital Setup, Digital Refresh, Digital Teardown, Other
- **Message:** "Event type '{type}' requires Lead or Supervisor role"

### 6. Daily Core Event Limit
- **Rule:** Maximum 1 Core event per employee per day
- **Check:** Count existing Core schedules for employee on date
- **Message:** "Employee {name} already has {count} core event(s) on {date}"

### 7. Time Overlap / Double-Booking
- **Rule:** Cannot schedule overlapping events for same employee
- **Check:** `(proposed_start < existing_end) AND (proposed_end > existing_start)`
- **Message:** "Employee {name} already scheduled for {event} from {time} to {time}"

### 8. Event Date Window
- **Rule:** Schedule date must be within event's start/due window
- **Check:** `event.start_datetime <= schedule_datetime < event.due_datetime`
- **Important:** Schedule must be **BEFORE** due date, not on it
- **Message:** "Event must be scheduled between {start_date} and {due_date}"

---

## Soft Constraints (Warnings - Can Override)

These constraints show a **warning** but can be overridden with approval:

### 1. Weekly Availability (SOFT in manual scheduling)
- **Scenario:** Employee typically not available on this day of week
- **Message:** "{name} is typically not available on {day_name}s"
- **Action:** Check with employee before scheduling

### 2. Club Supervisor on Core Events
- **Scenario:** Club Supervisor assigned to regular Core event
- **Message:** "Club Supervisor should not be assigned to regular events"
- **Reason:** Supervisors should focus on Supervisor-type events

### 3. Time Proximity Warning
- **Scenario:** Events scheduled within 2 hours of each other for same employee
- **Message:** "{name} has another event scheduled {minutes} minutes away"
- **Details:** Shows conflicting event name and time

---

## Auto-Scheduler Priority Waves

The auto-scheduler processes events in waves to ensure proper priority:

### Wave 1: Juicer Events (HIGHEST PRIORITY)
- **Assigned to:** Juicer Baristas based on rotation
- **Can bump:** Core events if Juicer Barista was assigned to Core
- **Time:** Based on Juicer sub-type (Production @ 9 AM, Survey @ 5 PM)

### Wave 2: Core Events (3 Sub-Waves)
- **Sub-Wave 2.1:** Lead Event Specialists (priority - fill their days first)
- **Sub-Wave 2.2:** Juicer Baristas (only when NOT doing Juicer that day)
- **Sub-Wave 2.3:** Event Specialists
- **Supervisor:** Scheduled INLINE with Core (auto-paired at noon)
- **Time Slots:** Rotated through 4 slots (10:45, 11:15, 11:45, 12:15)

### Wave 3: Freeosk Events
- **Priority Order:** Primary Lead -> Other Leads -> Club Supervisor
- **Time:** Fixed at 10:00
- **Duration:** 30 minutes

### Wave 4: Digital Events
- **Setup/Refresh:** Morning slots (10:15-11:30)
- **Teardown:** Evening slots (18:00+)
- **Duration:** 30 minutes each
- **Priority:** Primary/Secondary Lead -> Club Supervisor

### Wave 5: Other Events
- **Priority:** Club Supervisor -> Any Lead Event Specialist
- **Time:** Default at 11:00
- **Duration:** 60 minutes

---

## Special Scenarios & Edge Cases

### Scenario 1: Juicer Barista with Core Event
When a Juicer Barista is on Juicer rotation:
1. Their Core event (if any) gets **bumped**
2. Another employee is assigned to the Core event
3. Juicer Barista does Juicer work exclusively that day

### Scenario 2: Event Bumping/Cascading
When an urgent event needs a slot occupied by a less urgent event:
1. Less urgent event is **moved forward** (to earlier date if possible)
2. If no earlier date available, event is **unscheduled**
3. Maximum 3 bumps per event to prevent infinite loops

### Scenario 3: Supervisor Auto-Pairing & Cascade Rules

Supervisor events are tightly coupled to their paired Core events:

**Initial Scheduling:**
1. When Core event is scheduled at a time slot
2. Supervisor event for same day is created at 12:00 (noon)
3. Assigned to Club Supervisor

**Cascade Behavior (CRITICAL):**

| Action on Core Event | Effect on Supervisor | Notes |
|---------------------|---------------------|-------|
| **Unschedule** | **Auto-Unschedule** | Supervisor is automatically unscheduled when Core is unscheduled |
| **Reschedule** | **Auto-Reschedule** | Supervisor is moved to 2 hours after new Core start time |
| **Reissue** | **NO CASCADE** | Supervisor is NOT reissued - only the Core event is reissued |

**Why Reissue Does Not Cascade:**
- Reissue is a Crossmark system operation that may change the event's work order
- Supervisor events are internal scheduling constructs
- Reissuing a Core event doesn't require re-creating the Supervisor event

### Scenario 4: 3-Day Buffer Rule
Auto-scheduler will not schedule events within 3 days of today:
- **Earliest schedule date** = MAX(event.start_date, today + 3 days)
- Manual scheduling can override this buffer

### Scenario 5: Rotation Exceptions
For one-time changes to rotation assignments:
1. Create `ScheduleException` for specific date
2. Assign different employee for that date only
3. Standing rotation remains unchanged

---

## Validation Checklist

Use this checklist before finalizing any schedule:

### Pre-Scheduling Checks
- [ ] Event's due date has not passed
- [ ] Schedule date is within event's start/due window
- [ ] Schedule date is not a company holiday

### Employee Checks
- [ ] Employee exists and is active
- [ ] Employee has correct role for event type
- [ ] Employee does not have time-off on date
- [ ] Employee is not marked unavailable for date
- [ ] Employee's weekly availability includes this day

### Conflict Checks
- [ ] Employee does not already have a Core event (for Core events)
- [ ] No time overlap with existing schedules
- [ ] No events within 2-hour proximity (or acceptable)

### Role-Specific Checks
- [ ] Juicer events: Employee is Juicer Barista
- [ ] Lead-only events: Employee is Lead or Supervisor
- [ ] Supervisor events: Employee is Club Supervisor

### Time Slot Checks
- [ ] Time matches allowed slots for event type
- [ ] Time does not conflict with lunch breaks (for Core events)

---

## Quick Reference Card

### Can This Employee Do This Event?

| Event Type | Juicer Barista | Event Specialist | Lead Specialist | Club Supervisor |
|-----------|:--------------:|:----------------:|:---------------:|:---------------:|
| Core | Only if no Juicer | Yes | Yes | Warning |
| Juicer | Yes | No | No | No |
| Supervisor | No | No | No | Yes |
| Freeosk | No | No | Yes | Yes |
| Digital Setup | No | No | Yes | Yes |
| Digital Refresh | No | No | Yes | Yes |
| Digital Teardown | No | No | Yes | Yes |
| Digitals | No | No | Yes | Yes |
| Other | No | No | Yes | Yes |

### Daily Limits Summary

| Constraint | Limit | Notes |
|-----------|-------|-------|
| Core events per employee | 1 per day | HARD limit |
| Juicer events per employee | 1 per day | Typically via rotation |
| Events per employee | No hard limit | Use judgment |
| Time between events | 2+ hours preferred | SOFT - warning if closer |

---

## Related Documentation

- [Data Models](./data-models.md) - Database schema for scheduling tables
- [API Contracts](./api-contracts.md) - Scheduling API endpoints
- [Auto-Scheduler Architecture](./architecture.md) - Technical implementation details

---

*Generated by Document Project Workflow v1.2.0*
