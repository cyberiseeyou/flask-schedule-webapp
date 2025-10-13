# Test Plan - Calendar Redesign
## Detailed Test Procedures

**Project:** Flask Schedule WebApp - Calendar Enhancement
**QA Lead:** Quinn (Test Architect)
**Version:** 1.0
**Date:** 2025-10-12

---

## Table of Contents

1. [Test Execution Strategy](#test-execution-strategy)
2. [Sprint 1 Test Plan](#sprint-1-test-plan)
3. [Sprint 2 Test Plan](#sprint-2-test-plan)
4. [Critical Test Procedures](#critical-test-procedures)
5. [Test Data Setup](#test-data-setup)
6. [Bug Reporting Guidelines](#bug-reporting-guidelines)

---

## Test Execution Strategy

### Testing Phases

**Phase 1: Unit Testing (Continuous)**
- **Who:** Developers
- **When:** During development (TDD approach)
- **Tools:** pytest, pytest-cov
- **Entry Criteria:** Code written
- **Exit Criteria:** 80% code coverage, all tests pass

**Phase 2: Integration Testing (End of Sprint)**
- **Who:** Developers + QA
- **When:** Feature complete
- **Tools:** pytest with database fixtures
- **Entry Criteria:** Unit tests pass
- **Exit Criteria:** All API endpoints work, pairing logic validated

**Phase 3: System Testing (Pre-Demo)**
- **Who:** QA
- **When:** 2 days before sprint demo
- **Tools:** Manual testing, Selenium
- **Entry Criteria:** Integration tests pass
- **Exit Criteria:** All user stories validated

**Phase 4: UAT (Pre-Production)**
- **Who:** Product Owner
- **When:** Staging environment
- **Tools:** Manual testing
- **Entry Criteria:** System tests pass
- **Exit Criteria:** Business sign-off

---

## Sprint 1 Test Plan

### Sprint 1 Goals
- Calendar month view redesign
- Event type badge system
- Unscheduled warning indicators
- CORE-Supervisor automatic pairing

### Sprint 1 Test Schedule

| Day | Activity | Owner | Deliverable |
|-----|----------|-------|-------------|
| **Week 1** |
| Day 1-2 | Set up test environment | QA | Test DB, fixtures ready |
| Day 3-5 | Develop unit tests for pairing logic | Dev | 95% coverage |
| **Week 2** |
| Day 1-3 | Integration tests for pairing | Dev + QA | All TC-033 to TC-051 pass |
| Day 4 | Calendar UI tests | QA | TC-001 to TC-014 pass |
| Day 5 | Sprint 1 regression test | QA | Test report ready |

### Sprint 1 Test Cases (Priority Order)

**P0 Tests (Must Pass):**
1. TC-033: Reschedule CORE, Supervisor follows
2. TC-034: Reschedule CORE, no Supervisor exists
3. TC-036: Transaction rollback on failure
4. TC-041: Unschedule CORE, Supervisor also unscheduled
5. TC-001: Display event type counts
6. TC-002: Display unscheduled warning icon
7. TC-004: Click cell navigates to daily view
8. TC-012: Keyboard navigation works

**P1 Tests (Should Pass):**
9. TC-005: Full-screen layout on desktop
10. TC-006: Responsive layout on tablet
11. TC-007: Responsive layout on mobile
12. TC-037: Reschedule with employee change
13. TC-042: Unschedule CORE, no Supervisor

**P2 Tests (Nice to Have):**
14. TC-008: Empty calendar month
15. TC-021: Collapsible state persists

---

## Sprint 2 Test Plan

### Sprint 2 Goals
- Daily view page
- Event grouping with collapse/expand
- Supervisor modal
- Universal action buttons

### Sprint 2 Test Schedule

| Day | Activity | Owner | Deliverable |
|-----|----------|-------|-------------|
| **Week 1** |
| Day 1-2 | Daily view functional tests | QA | TC-015 to TC-025 pass |
| Day 3-4 | Supervisor modal tests | QA | TC-026 to TC-032 pass |
| Day 5 | Accessibility tests | QA | WCAG AA validation |
| **Week 2** |
| Day 1-2 | Performance/load testing | QA | TC-052 to TC-055 pass |
| Day 3 | Cross-browser testing | QA | Chrome/Firefox/Safari |
| Day 4-5 | UAT with Product Owner | PO + QA | Sign-off |

### Sprint 2 Test Cases (Priority Order)

**P0 Tests:**
1. TC-015: Display daily view header
2. TC-016: Display Juicer and Primary Lead
3. TC-019: Event groups display correctly
4. TC-022: CORE event card with scheduled Supervisor
5. TC-026: Open Supervisor modal
6. TC-032: Modal focus trap
7. TC-052: Calendar load performance (1000 events)
8. TC-056: Keyboard-only navigation

**P1 Tests:**
9. TC-053: Daily view load (50 events)
10. TC-054: Concurrent user load
11. TC-057: Screen reader full workflow
12. TC-060-064: Cross-browser tests

---

## Critical Test Procedures

### Procedure 1: TC-033 - Reschedule CORE, Supervisor Follows

**Test ID:** TC-033
**Priority:** 🔴 P0 (CRITICAL)
**Estimated Time:** 15 minutes
**Prerequisites:**
- Test database loaded with test data
- CORE event "606001-CORE-Super Pretzel" scheduled on 2025-10-15
- Supervisor event "606001-Supervisor-Super Pretzel" scheduled on 2025-10-15

**Test Steps:**

**SETUP:**
```sql
-- Verify initial state
SELECT event_id, project_name, condition,
       (SELECT start_datetime FROM schedule WHERE event_id = events.event_id) as scheduled_date
FROM events
WHERE project_name LIKE '606001-%';

-- Expected:
-- 606001-CORE-Super Pretzel | Scheduled | 2025-10-15 10:00:00
-- 606001-Supervisor-Super Pretzel | Scheduled | 2025-10-15 12:00:00
```

**STEPS:**

1. **Navigate to daily view**
   - Open browser: `http://localhost:5000/calendar/daily/2025-10-15`
   - ✅ Verify: CORE event "606001-CORE-Super Pretzel" visible
   - ✅ Verify: Status shows "✅ Supervisor Event Scheduled"

2. **Click Reschedule button**
   - Click [Reschedule] button on CORE event card
   - ✅ Verify: Reschedule modal opens

3. **Change date to 2025-10-20**
   - Select new date: `2025-10-20`
   - Click [Save]
   - ✅ Verify: Success message appears
   - ✅ Verify: Modal closes

4. **Verify CORE event rescheduled**
   - Refresh daily view for 2025-10-20: `http://localhost:5000/calendar/daily/2025-10-20`
   - ✅ Verify: CORE event appears on Oct 20
   - ✅ Verify: Start time remains 10:00 AM

5. **Verify Supervisor event also rescheduled**
   - ✅ Verify: Status shows "✅ Supervisor Event Scheduled (Employee @ 12:00 PM)"
   - Check database:
     ```sql
     SELECT project_name,
            (SELECT start_datetime FROM schedule WHERE event_id = events.event_id) as scheduled_date
     FROM events
     WHERE project_name LIKE '606001-%';

     -- Expected:
     -- 606001-CORE-Super Pretzel | 2025-10-20 10:00:00
     -- 606001-Supervisor-Super Pretzel | 2025-10-20 12:00:00
     ```

6. **Verify original date cleared**
   - Navigate to: `http://localhost:5000/calendar/daily/2025-10-15`
   - ✅ Verify: NO events with "606001" appear

**EXPECTED RESULTS:**
- ✅ CORE event rescheduled to 2025-10-20 at 10:00 AM
- ✅ Supervisor event rescheduled to 2025-10-20 at 12:00 PM
- ✅ Both events have `condition='Scheduled'`
- ✅ Log entry created: "Auto-rescheduled Supervisor event [ID] to 2025-10-20"

**ACTUAL RESULTS:**
_[To be filled during test execution]_

**PASS/FAIL:** _______

**NOTES:**
_[Any observations, issues, or deviations]_

---

### Procedure 2: TC-036 - Transaction Rollback on Failure

**Test ID:** TC-036
**Priority:** 🔴 P0 (CRITICAL)
**Estimated Time:** 20 minutes
**Prerequisites:**
- Test database with CORE and Supervisor events
- Ability to simulate database failure

**Test Steps:**

**SETUP:**

1. **Create test database trigger to simulate failure**
   ```sql
   -- Create trigger to force failure on Supervisor reschedule
   CREATE OR REPLACE FUNCTION test_fail_supervisor_update()
   RETURNS TRIGGER AS $$
   BEGIN
       IF NEW.event_id = (SELECT event_id FROM events WHERE project_name LIKE '606001-Supervisor-%' LIMIT 1) THEN
           RAISE EXCEPTION 'SIMULATED DATABASE FAILURE';
       END IF;
       RETURN NEW;
   END;
   $$ LANGUAGE plpgsql;

   CREATE TRIGGER test_supervisor_fail_trigger
   BEFORE UPDATE ON schedule
   FOR EACH ROW
   EXECUTE FUNCTION test_fail_supervisor_update();
   ```

2. **Verify initial state**
   ```sql
   SELECT project_name, condition,
          (SELECT start_datetime FROM schedule WHERE event_id = events.event_id) as scheduled_date
   FROM events WHERE project_name LIKE '606001-%';

   -- Both should be on 2025-10-15
   ```

**STEPS:**

1. **Attempt to reschedule CORE event**
   - Navigate to: `http://localhost:5000/calendar/daily/2025-10-15`
   - Click [Reschedule] on "606001-CORE-Super Pretzel"
   - Change date to 2025-10-20
   - Click [Save]

2. **Verify error response**
   - ✅ Verify: HTTP 500 error returned
   - ✅ Verify: Error message displayed: "Failed to reschedule event"
   - ✅ Verify: Modal remains open OR shows error inline

3. **Verify database rollback**
   ```sql
   SELECT project_name,
          (SELECT start_datetime FROM schedule WHERE event_id = events.event_id) as scheduled_date
   FROM events WHERE project_name LIKE '606001-%';

   -- Expected: BOTH still on 2025-10-15 (not rescheduled)
   ```

4. **Verify CORE event NOT rescheduled**
   - ✅ Verify: CORE event `start_datetime` = 2025-10-15 10:00 AM (unchanged)

5. **Verify Supervisor event NOT rescheduled**
   - ✅ Verify: Supervisor event `start_datetime` = 2025-10-15 12:00 PM (unchanged)

6. **Check error logs**
   - ✅ Verify: Log entry contains: "Transaction rolled back: SIMULATED DATABASE FAILURE"

**CLEANUP:**
```sql
-- Remove test trigger
DROP TRIGGER IF EXISTS test_supervisor_fail_trigger ON schedule;
DROP FUNCTION IF EXISTS test_fail_supervisor_update();
```

**EXPECTED RESULTS:**
- ✅ HTTP 500 error returned
- ✅ Both CORE and Supervisor events remain on 2025-10-15
- ✅ Database transaction rolled back successfully
- ✅ Error logged with exception details

**ACTUAL RESULTS:**
_[To be filled during test execution]_

**PASS/FAIL:** _______

---

### Procedure 3: TC-041 - Unschedule CORE, Supervisor Also Unscheduled

**Test ID:** TC-041
**Priority:** 🔴 P0 (CRITICAL)
**Estimated Time:** 10 minutes

**Test Steps:**

**SETUP:**
```sql
-- Verify both scheduled
SELECT e.project_name, e.condition, e.is_scheduled,
       s.schedule_id, emp.name as employee
FROM events e
LEFT JOIN schedule s ON e.event_id = s.event_id
LEFT JOIN employees emp ON s.employee_id = emp.employee_id
WHERE e.project_name LIKE '606001-%';

-- Expected: 2 rows, both with condition='Scheduled', schedule_id NOT NULL
```

**STEPS:**

1. **Navigate to daily view**
   - Open: `http://localhost:5000/calendar/daily/2025-10-15`
   - ✅ Verify: CORE event "606001-CORE-Super Pretzel" visible

2. **Click Unschedule button**
   - Click [Unschedule] on CORE event card
   - ✅ Verify: Confirmation dialog appears: "Are you sure?"
   - Click [Confirm]

3. **Verify success feedback**
   - ✅ Verify: Success message: "Event unscheduled successfully"
   - ✅ Verify: Event card disappears OR shows "Unscheduled" status

4. **Verify CORE event unscheduled in database**
   ```sql
   SELECT e.project_name, e.condition, e.is_scheduled, s.schedule_id
   FROM events e
   LEFT JOIN schedule s ON e.event_id = s.event_id
   WHERE e.project_name = '606001-CORE-Super Pretzel';

   -- Expected: condition='Unstaffed', is_scheduled=False, schedule_id=NULL
   ```

5. **Verify Supervisor event also unscheduled**
   ```sql
   SELECT e.project_name, e.condition, e.is_scheduled, s.schedule_id
   FROM events e
   LEFT JOIN schedule s ON e.event_id = s.event_id
   WHERE e.project_name = '606001-Supervisor-Super Pretzel';

   -- Expected: condition='Unstaffed', is_scheduled=False, schedule_id=NULL
   ```

6. **Check application logs**
   - ✅ Verify: Log entry: "Auto-unscheduled Supervisor event [ID]"

**EXPECTED RESULTS:**
- ✅ CORE event: `condition='Unstaffed'`, `is_scheduled=False`, Schedule deleted
- ✅ Supervisor event: `condition='Unstaffed'`, `is_scheduled=False`, Schedule deleted
- ✅ Both events unscheduled atomically (all-or-nothing)

**ACTUAL RESULTS:**
_[To be filled during test execution]_

**PASS/FAIL:** _______

---

### Procedure 4: TC-052 - Calendar Load Performance (1000 Events)

**Test ID:** TC-052
**Priority:** 🔴 P0 (CRITICAL)
**Estimated Time:** 30 minutes
**Prerequisites:**
- Test database loaded with 1000+ events in October 2025
- Performance monitoring tools (browser DevTools, NewRelic, etc.)

**Test Steps:**

**SETUP:**

1. **Load test data**
   ```bash
   python scripts/load_test_data.py --month=2025-10 --count=1000
   ```

2. **Verify test data loaded**
   ```sql
   SELECT COUNT(*) FROM events
   WHERE start_datetime >= '2025-10-01'
     AND start_datetime < '2025-11-01';

   -- Expected: 1000+
   ```

3. **Clear browser cache**
   - Open browser in incognito/private mode
   - OR clear cache manually

**STEPS:**

1. **Measure first load (cold cache)**
   - Open browser DevTools → Network tab
   - Click "Clear" to reset
   - Navigate to: `http://localhost:5000/calendar?year=2025&month=10`
   - ✅ Record: Page load time (DOMContentLoaded)
   - ✅ Record: API response time for `/api/calendar/month?year=2025&month=10`

2. **Measure subsequent load (warm cache)**
   - Refresh page (F5)
   - ✅ Record: Page load time (should be faster due to caching)

3. **Analyze database query performance**
   - Check application logs for SQL query execution time
   - ✅ Verify: Aggregation query executed in < 500ms
   - ✅ Verify: Only 1 aggregation query (no N+1 queries)

4. **Profile page rendering**
   - Open DevTools → Performance tab
   - Click "Record"
   - Reload page
   - Stop recording
   - ✅ Analyze: JavaScript execution time, rendering time
   - ✅ Verify: No long tasks (> 50ms)

5. **Check memory usage**
   - DevTools → Memory tab
   - Take heap snapshot before load
   - Load calendar
   - Take heap snapshot after load
   - ✅ Verify: Memory increase < 50MB
   - ✅ Verify: No memory leaks (reload 5 times, memory stabilizes)

**EXPECTED RESULTS:**
- ✅ **Cold load:** < 2 seconds (95th percentile)
- ✅ **Warm load:** < 500ms
- ✅ **Database query:** < 500ms
- ✅ **Single aggregation query:** No N+1 issues
- ✅ **Memory:** < 50MB increase, no leaks

**ACTUAL RESULTS:**

| Metric | Trial 1 | Trial 2 | Trial 3 | Average | Pass/Fail |
|--------|---------|---------|---------|---------|-----------|
| Cold load time | ___ ms | ___ ms | ___ ms | ___ ms | _____ |
| Warm load time | ___ ms | ___ ms | ___ ms | ___ ms | _____ |
| DB query time | ___ ms | ___ ms | ___ ms | ___ ms | _____ |
| Memory usage | ___ MB | ___ MB | ___ MB | ___ MB | _____ |

**PASS/FAIL:** _______

**NOTES:**
- If FAIL: Profile which operation is slow (query, rendering, JavaScript)
- Check if database indexes exist on `start_datetime`, `project_name`, `event_type`

---

### Procedure 5: TC-056 - Keyboard-Only Navigation

**Test ID:** TC-056
**Priority:** 🔴 P0 (Accessibility)
**Estimated Time:** 20 minutes
**Prerequisites:**
- Mouse/trackpad disconnected OR don't touch mouse during test

**Test Steps:**

**SETUP:**
- Navigate to calendar page: `http://localhost:5000/calendar`
- **Do NOT use mouse for entire test**

**STEPS:**

**Part 1: Calendar Month View Navigation**

1. **Tab to first calendar cell**
   - Press `Tab` repeatedly until focus reaches first calendar cell
   - ✅ Verify: Visual focus indicator visible (2px blue outline)

2. **Navigate between calendar cells**
   - Press `Tab` to move to next cell
   - Press `Shift+Tab` to move to previous cell
   - ✅ Verify: Focus indicator moves correctly
   - ✅ Verify: Focus never gets trapped

3. **Open daily view with keyboard**
   - Tab to October 15 cell
   - Press `Enter`
   - ✅ Verify: Browser navigates to `/calendar/daily/2025-10-15`

**Part 2: Daily View Navigation**

4. **Tab through daily view elements**
   - Press `Tab` repeatedly
   - ✅ Verify: Focus moves through: Back link → Event group headers → Event cards → Action buttons
   - ✅ Verify: Focus order is logical (top-to-bottom, left-to-right)

5. **Expand/collapse event group**
   - Tab to "CORE EVENTS" header
   - Press `Enter` or `Space`
   - ✅ Verify: Group collapses
   - Press `Enter` or `Space` again
   - ✅ Verify: Group expands

6. **Open Supervisor modal**
   - Tab to [View/Edit Supervisor Event] button
   - Press `Enter`
   - ✅ Verify: Modal opens

**Part 3: Modal Focus Trap**

7. **Test modal focus trap**
   - Press `Tab` repeatedly
   - ✅ Verify: Focus cycles within modal: Employee dropdown → [Update] → Date input → Time input → [Update] → [Unschedule] → [Save] → [Cancel] → back to Employee dropdown
   - ✅ Verify: Focus NEVER leaves modal

8. **Test reverse tab direction**
   - Press `Shift+Tab` repeatedly
   - ✅ Verify: Focus cycles in reverse order

9. **Close modal with keyboard**
   - Press `Escape`
   - ✅ Verify: Modal closes
   - ✅ Verify: Focus returns to triggering button ([View/Edit Supervisor Event])

**Part 4: Action Button Activation**

10. **Activate Reschedule button**
    - Tab to [Reschedule] button on any event
    - Press `Enter`
    - ✅ Verify: Reschedule dialog opens

11. **Navigate form fields**
    - Press `Tab` to move through: Date input → Employee dropdown → [Save] → [Cancel]
    - ✅ Verify: All form fields keyboard accessible

12. **Submit form with keyboard**
    - Tab to [Save] button
    - Press `Enter` OR `Space`
    - ✅ Verify: Form submits

**EXPECTED RESULTS:**
- ✅ All interactive elements reachable via Tab
- ✅ Visual focus indicator always visible (2px blue outline)
- ✅ Enter/Space keys activate buttons
- ✅ Escape closes modals
- ✅ Modal focus trap works (Tab cycles within modal)
- ✅ Focus returns to trigger after modal close
- ✅ No keyboard traps (except intentional modal)

**ACTUAL RESULTS:**
_[Document any issues, missing focus indicators, or inaccessible elements]_

**PASS/FAIL:** _______

---

## Test Data Setup

### Minimal Test Data Set

**Required for Sprint 1 Testing:**

```sql
-- Run this script to set up minimal test data
-- File: test_data/sprint1_minimal.sql

-- 1. CORE event with matching Supervisor (for pairing tests)
INSERT INTO events (event_id, project_name, event_type, condition, is_scheduled, estimated_hours, start_datetime, due_datetime)
VALUES
(1001, '606001-CORE-Super Pretzel', 'CORE', 'Scheduled', TRUE, 6.5, '2025-10-15 10:00:00', '2025-10-15'),
(1002, '606001-Supervisor-Super Pretzel', 'Supervisor', 'Scheduled', TRUE, 0.08, '2025-10-15 12:00:00', '2025-10-15');

INSERT INTO schedule (schedule_id, event_id, employee_id, start_datetime)
VALUES
(2001, 1001, 101, '2025-10-15 10:00:00'),  -- John Smith
(2002, 1002, 102, '2025-10-15 12:00:00');  -- Jane Doe

-- 2. CORE event without Supervisor (orphan test)
INSERT INTO events (event_id, project_name, event_type, condition, is_scheduled, estimated_hours, start_datetime, due_datetime)
VALUES
(1003, '606999-CORE-Orphan Product', 'CORE', 'Scheduled', TRUE, 5.0, '2025-10-15 11:00:00', '2025-10-15');

INSERT INTO schedule (schedule_id, event_id, employee_id, start_datetime)
VALUES
(2003, 1003, 101, '2025-10-15 11:00:00');

-- 3. Unscheduled CORE and Supervisor (for scheduling tests)
INSERT INTO events (event_id, project_name, event_type, condition, is_scheduled, estimated_hours, due_datetime)
VALUES
(1004, '606002-CORE-Nature Valley', 'CORE', 'Unstaffed', FALSE, 6.0, '2025-10-16'),
(1005, '606002-Supervisor-Nature Valley', 'Supervisor', 'Unstaffed', FALSE, 0.08, '2025-10-16');

-- 4. Juicer Production events (for calendar display)
INSERT INTO events (event_id, project_name, event_type, condition, is_scheduled, estimated_hours, start_datetime, due_datetime)
VALUES
(1006, 'Juicer Production - Costco #123', 'Juicer Production', 'Scheduled', TRUE, 8.0, '2025-10-15 08:00:00', '2025-10-15'),
(1007, 'Juicer Production - Target #456', 'Juicer Production', 'Scheduled', TRUE, 7.5, '2025-10-15 09:00:00', '2025-10-15');

INSERT INTO schedule (schedule_id, event_id, employee_id, start_datetime)
VALUES
(2004, 1006, 101, '2025-10-15 08:00:00'),
(2005, 1007, 103, '2025-10-15 09:00:00');

-- 5. Freeosk and Digital events
INSERT INTO events (event_id, project_name, event_type, condition, is_scheduled, estimated_hours, start_datetime, due_datetime)
VALUES
(1008, 'Freeosk Setup - Walmart #789', 'Freeosk', 'Scheduled', TRUE, 4.0, '2025-10-15 10:00:00', '2025-10-15'),
(1009, 'Digital Display - BestBuy #111', 'Digitals', 'Scheduled', TRUE, 3.0, '2025-10-15 13:00:00', '2025-10-15');

INSERT INTO schedule (schedule_id, event_id, employee_id, start_datetime)
VALUES
(2006, 1008, 104, '2025-10-15 10:00:00'),
(2007, 1009, 105, '2025-10-15 13:00:00');

-- 6. Unscheduled events (for warning icon test)
INSERT INTO events (event_id, project_name, event_type, condition, is_scheduled, due_datetime)
VALUES
(1010, 'Unscheduled Event 1', 'CORE', 'Unstaffed', FALSE, '2025-10-15'),
(1011, 'Unscheduled Event 2', 'Juicer Production', 'Unstaffed', FALSE, '2025-10-15');
```

### Load Test Data Set

**For Performance Testing (1000+ events):**

See separate file: `test_data/generate_load_test_data.py`

```python
# File: test_data/generate_load_test_data.py
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

def generate_load_test_data(month_start='2025-10-01', event_count=1000):
    """Generate SQL INSERT statements for load testing"""

    month_start = datetime.strptime(month_start, '%Y-%m-%d')
    month_end = month_start + timedelta(days=30)

    event_types = [
        ('CORE', 0.40),        # 40% CORE
        ('Juicer Production', 0.20),
        ('Supervisor', 0.20),
        ('Freeosk', 0.10),
        ('Digitals', 0.10)
    ]

    events = []
    schedules = []
    event_id = 5000
    schedule_id = 10000

    for i in range(event_count):
        # Pick event type based on distribution
        event_type = random.choices(
            [t[0] for t in event_types],
            weights=[t[1] for t in event_types]
        )[0]

        # Random date in month
        days_offset = random.randint(0, 29)
        event_date = month_start + timedelta(days=days_offset)

        # Random time
        hour = random.randint(8, 17)
        event_datetime = event_date.replace(hour=hour)

        # Generate project name
        if event_type == 'CORE':
            event_number = 600000 + (i % 1000)
            project_name = f'{event_number}-CORE-{fake.company()}'
        elif event_type == 'Supervisor':
            event_number = 600000 + (i % 1000)
            project_name = f'{event_number}-Supervisor-{fake.company()}'
        else:
            project_name = f'{event_type} - {fake.city()} #{random.randint(100,999)}'

        # 90% scheduled, 10% unscheduled
        is_scheduled = random.random() < 0.9
        condition = 'Scheduled' if is_scheduled else 'Unstaffed'

        # Create event INSERT
        events.append(
            f"({event_id}, '{project_name}', '{event_type}', '{condition}', "
            f"{is_scheduled}, {random.uniform(2.0, 8.0):.1f}, "
            f"'{event_datetime.isoformat()}', '{event_date.date()}'),"
        )

        # Create schedule INSERT if scheduled
        if is_scheduled:
            employee_id = random.randint(101, 120)
            schedules.append(
                f"({schedule_id}, {event_id}, {employee_id}, '{event_datetime.isoformat()}'),"
            )
            schedule_id += 1

        event_id += 1

    # Write to file
    with open('test_data/load_test_inserts.sql', 'w') as f:
        f.write("-- Load test data: 1000+ events\n\n")
        f.write("INSERT INTO events (event_id, project_name, event_type, condition, is_scheduled, estimated_hours, start_datetime, due_datetime)\nVALUES\n")
        f.write('\n'.join(events))
        f.write(";\n\n")

        f.write("INSERT INTO schedule (schedule_id, event_id, employee_id, start_datetime)\nVALUES\n")
        f.write('\n'.join(schedules))
        f.write(";\n")

    print(f"Generated {len(events)} events and {len(schedules)} schedules")

if __name__ == '__main__':
    generate_load_test_data(event_count=1000)
```

---

## Bug Reporting Guidelines

### Bug Report Template

```markdown
**Bug ID:** BUG-[Sprint]-[Number] (e.g., BUG-S1-001)
**Title:** [Clear, concise description]
**Severity:** P0 / P1 / P2 / P3
**Status:** Open / In Progress / Fixed / Closed
**Reported By:** [Name]
**Date:** [YYYY-MM-DD]

**Environment:**
- OS: [Windows/Mac/Linux]
- Browser: [Chrome 120, Firefox 115, etc.]
- Database: [PostgreSQL 14, SQLite 3.40, etc.]
- Test Data: [Minimal / Load test / Custom]

**Test Case:** TC-XXX

**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Result:**
[What should happen]

**Actual Result:**
[What actually happened]

**Evidence:**
- Screenshot: [Attach image]
- Logs: [Paste relevant log entries]
- Database state: [SQL query results]

**Impact:**
[How does this affect users/business?]

**Workaround:**
[Is there a temporary workaround?]

**Fix Recommendation:**
[Optional: Suggested fix]
```

### Bug Severity Definitions

**P0 (Blocker):**
- Data corruption or loss
- System crash
- Security vulnerability
- Critical feature completely broken
- **Action:** Fix immediately, block deployment

**P1 (Critical):**
- Major feature malfunction
- Poor performance (> 5s)
- WCAG AA violation
- **Action:** Fix before production, may defer if workaround exists

**P2 (Major):**
- Minor feature issue
- UI visual bugs
- Usability problem
- **Action:** Fix in next sprint

**P3 (Minor):**
- Cosmetic issues
- Edge case bugs
- Nice-to-have improvements
- **Action:** Backlog, fix when time permits

### Example Bug Report

```markdown
**Bug ID:** BUG-S1-001
**Title:** Rescheduling CORE event does not update Supervisor event date
**Severity:** P0 (Blocker)
**Status:** Open
**Reported By:** Quinn (QA)
**Date:** 2025-10-18

**Environment:**
- OS: Windows 11
- Browser: Chrome 120
- Database: PostgreSQL 14
- Test Data: Minimal test set

**Test Case:** TC-033

**Steps to Reproduce:**
1. Navigate to `/calendar/daily/2025-10-15`
2. Click [Reschedule] on CORE event "606001-CORE-Super Pretzel"
3. Change date to 2025-10-20
4. Click [Save]
5. Check database:
   ```sql
   SELECT project_name,
          (SELECT start_datetime FROM schedule WHERE event_id = events.event_id)
   FROM events WHERE project_name LIKE '606001-%';
   ```

**Expected Result:**
- CORE event: 2025-10-20 10:00:00
- Supervisor event: 2025-10-20 12:00:00

**Actual Result:**
- CORE event: 2025-10-20 10:00:00 ✅
- Supervisor event: 2025-10-15 12:00:00 ❌ (NOT updated)

**Evidence:**
- Screenshot: [daily_view_reschedule.png]
- Logs:
  ```
  [INFO] Rescheduling event 1001 to 2025-10-20
  [WARNING] No Supervisor event found for CORE event 1001
  ```

**Impact:**
- **CRITICAL:** Supervisor shows up on wrong day, business operations disrupted
- Supervisor may go to store on wrong date
- Data integrity compromised

**Root Cause Analysis:**
Regex match failing because:
```python
match = re.search(r'(\d{6})-CORE-', core_event.project_name)
# Returns None for event "606001-CORE-Super Pretzel" (should match)
```

**Fix Recommendation:**
```python
# Use case-insensitive regex
match = re.search(r'(\d{6})-CORE-', core_event.project_name, re.IGNORECASE)
```

**Workaround:**
Manually reschedule Supervisor event via database:
```sql
UPDATE schedule
SET start_datetime = '2025-10-20 12:00:00'
WHERE event_id = (SELECT event_id FROM events WHERE project_name = '606001-Supervisor-Super Pretzel');
```
```

---

## Appendix: Test Execution Checklist

### Sprint 1 Exit Criteria

- [ ] ALL P0 tests pass (100%)
- [ ] ≥ 95% P1 tests pass
- [ ] Unit test coverage ≥ 80% overall, 95% for pairing logic
- [ ] Zero P0 bugs open
- [ ] Performance baseline established (calendar load time < 2s)
- [ ] Code review approved
- [ ] Demo-ready (can show all features to stakeholders)

### Sprint 2 Exit Criteria

- [ ] ALL P0 tests pass (100%)
- [ ] ≥ 95% P1 tests pass
- [ ] Load testing complete (TC-052, TC-054)
- [ ] Accessibility WCAG AA validation pass
- [ ] Cross-browser testing complete (Chrome, Firefox, Safari)
- [ ] UAT sign-off from Product Owner
- [ ] Zero P0 bugs open, < 3 P1 bugs open

### Production Deployment Checklist

- [ ] ALL Sprint 1 + Sprint 2 exit criteria met
- [ ] Database backup created
- [ ] Rollback plan tested
- [ ] Orphan detection job deployed
- [ ] Monitoring alerts configured
- [ ] Load testing passed with production-scale data
- [ ] Security review complete
- [ ] Deployment runbook ready
- [ ] On-call rotation scheduled

---

**Document Version:** 1.0
**Last Updated:** 2025-10-12
**Owner:** Quinn (QA Test Architect)
