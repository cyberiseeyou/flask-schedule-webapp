# Daily Manager Workflow Guide

## Overview
This guide provides a step-by-step daily routine for managers to ensure all events are properly scheduled, staffed, and documented. Following this workflow ensures nothing falls through the cracks.

---

## Morning Routine (8:00 AM - 9:00 AM)

### Step 1: Check Daily Validation Dashboard
**Time**: 5 minutes
**Action**: Navigate to `/dashboard/daily-validation` in your webapp

**What to review:**
- [ ] Today's event count by type
- [ ] Any unscheduled events requiring immediate attention
- [ ] Rotation assignments for today (Juicer, Primary Lead)
- [ ] Employee availability conflicts
- [ ] Missing paperwork flags

**Red flags to watch for:**
- ⚠️ Freeosk or Digital events without assignments
- ⚠️ Core events scheduled but no corresponding Supervisor event
- ⚠️ Employees scheduled during time-off periods
- ⚠️ Events approaching due date (within 24 hours)

---

### Step 2: Review Automated Audit Report
**Time**: 5 minutes
**Action**: Check email or audit log in webapp

**The automated audit runs at 6:00 AM daily and flags:**
- Missing Freeosk events (expected but not in system)
- Missing Digital events (expected but not in system)
- Rotation gaps (no Juicer or Primary Lead assigned)
- Events due today that are still unscheduled
- Paperwork not generated for today's events

**Action items:**
- [ ] Review each flagged item
- [ ] Determine if action needed (schedule event, contact MVRetail, etc.)
- [ ] Document any legitimate exceptions (event cancelled, store closed, etc.)

---

### Step 3: Validate Today's Rotation Assignments
**Time**: 3 minutes
**Location**: Dashboard or Rotation Management page

**Check:**
- [ ] **Juicer rotation**: Who is assigned for today?
  - Verify employee is available (no time off)
  - Check if Juicer events are scheduled to correct person
- [ ] **Primary Lead rotation**: Who is the lead for today?
  - Verify employee is available
  - Check if Freeosk/Digital events assigned to Primary Lead
  - Verify Core events prioritized to Primary Lead (9:45 AM slot)

**If rotation employee unavailable:**
1. Create Schedule Exception for today
2. Assign alternate employee (same role)
3. Notify affected employee of change
4. Document reason in exception notes

---

### Step 4: Generate and Print Today's Paperwork
**Time**: 10 minutes
**Location**: Calendar view or Paperwork page

**Process:**
1. Navigate to today's date in calendar
2. Click "Print all paperwork for a day" button
3. System generates EDR (Event Detail Reports) for all scheduled events
4. Review generated PDFs:
   - [ ] All events have paperwork
   - [ ] Store details are correct
   - [ ] Employee names are correct
   - [ ] Times are correct
5. Print or email paperwork to employees

**If paperwork missing or incorrect:**
- Check if event is fully scheduled (employee assigned)
- Verify event details in system match MVRetail
- Re-generate if needed
- Contact IT if generation fails

---

### Step 5: Brief Employees
**Time**: 10 minutes
**Method**: Team meeting, group text, or individual check-ins

**Communicate:**
- Today's assignments (who is working where)
- Any special instructions (new stores, complex events)
- Rotation confirmations (Juicer, Primary Lead)
- Changes from original schedule
- Expected completion times

**Verify:**
- [ ] All employees acknowledge their assignments
- [ ] Employees have necessary paperwork/materials
- [ ] Employees have travel directions to stores
- [ ] Employees know who to contact if issues arise

---

## Mid-Day Check (12:00 PM - 1:00 PM)

### Step 6: Monitor Event Progress
**Time**: 5 minutes
**Location**: Calendar or event list view

**Check:**
- [ ] Have morning events (9:00 AM - 11:30 AM) started?
- [ ] Any employee no-shows or issues reported?
- [ ] Are Supervisor check-ins happening at noon?

**Communication:**
- Text/call employees if no check-in by expected time
- Document any issues in event notes
- Adjust afternoon assignments if needed (employee sick, running late, etc.)

---

### Step 7: Review Tomorrow's Schedule
**Time**: 10 minutes
**Location**: Calendar view (tomorrow's date)

**Validate tomorrow's assignments:**
- [ ] All events scheduled with employees
- [ ] Rotation assignments confirmed (Juicer, Primary Lead)
- [ ] No scheduling conflicts (employee double-booked)
- [ ] Paperwork ready to print tomorrow morning

**If gaps found:**
- Run auto-scheduler for tomorrow's date
- Manually assign if auto-scheduler fails
- Check employee availability for tomorrow
- Create rotation exceptions if needed

---

## Afternoon Routine (3:00 PM - 4:00 PM)

### Step 8: Check 3-Day Ahead Schedule
**Time**: 15 minutes
**Location**: Calendar view (3 days from today)

**Why 3 days?** Auto-scheduler uses a 3-day buffer, so events 3 days out are ready for auto-assignment.

**Review:**
- [ ] All events within 3 days are scheduled
- [ ] No unscheduled events approaching due date
- [ ] Rotation coverage for next 3 days
- [ ] Employee availability for next 3 days

**Actions:**
- Run auto-scheduler if many unscheduled events exist
- Review and approve pending schedule proposals
- Make manual adjustments as needed
- Check for employee time-off conflicts

---

### Step 9: Run Auto-Scheduler (If Needed)
**Time**: 10 minutes
**Location**: Auto-Scheduler page

**When to run:**
- New events imported from MVRetail
- Employees added or availability changed
- Events approaching due date still unscheduled
- At least once per day (recommended)

**Process:**
1. Click "Run Auto-Scheduler" (manual run)
2. Wait for execution to complete
3. Review SchedulerRunHistory results:
   - Total events processed
   - Events successfully scheduled
   - Events requiring swaps
   - Events failed to schedule
4. Review pending schedule proposals:
   - Check each proposed assignment
   - Verify employee is appropriate
   - Verify time makes sense
   - Edit if needed (changes status to 'user_edited')
5. Approve batch:
   - Click "Approve All" if satisfied
   - Or individually approve/reject
   - Approved schedules move to 'approved' status

**Failed events:**
- Review failure reasons
- Fix underlying issues (employee availability, rotation gaps, etc.)
- Manually assign if auto-scheduler can't solve
- Document persistent issues

---

### Step 10: Approve and Submit to API
**Time**: 5 minutes
**Location**: Pending Schedules page

**Process:**
1. Review all approved pending schedules
2. Click "Submit to API" button
3. System sends approved schedules to MVRetail API
4. Monitor submission results:
   - Successfully submitted → status = 'api_submitted'
   - Failed submission → status = 'api_failed'
5. Handle failures:
   - Review API error details
   - Fix issues (invalid employee ID, bad date format, etc.)
   - Retry submission

**Why submit to API?**
- Syncs your local schedules with MVRetail system
- Ensures employees see assignments in their mobile app
- Maintains data consistency across systems

---

## End of Day (5:00 PM - 5:30 PM)

### Step 11: Verify Today's Events Completed
**Time**: 10 minutes
**Location**: Calendar view (today's date)

**Check:**
- [ ] All events marked as completed (if tracking completion)
- [ ] Digital Teardown events happened (scheduled for 5:00 PM - 6:45 PM)
- [ ] No outstanding issues or employee concerns
- [ ] All paperwork submitted/filed

**Follow-up:**
- Contact employees who haven't reported completion
- Document any issues for tomorrow's planning
- Update event notes if necessary

---

### Step 12: Prepare for Tomorrow
**Time**: 5 minutes
**Location**: Dashboard and calendar

**Final checks:**
- [ ] Tomorrow's schedule is complete
- [ ] Rotation assignments confirmed
- [ ] Paperwork ready to print in morning
- [ ] No employee availability conflicts
- [ ] Auto-scheduler ran today (covers 3 days ahead)

**Set reminders:**
- Employees with early assignments (text reminder tonight)
- Special events requiring extra attention
- Employee time-off starting tomorrow

---

## Weekly Routine (Monday 8:00 AM)

### Step 13: Review Weekly Rotations
**Time**: 10 minutes
**Location**: Rotation Management page

**Check:**
- [ ] Juicer rotation assigned for all weekdays
- [ ] Primary Lead rotation assigned for all weekdays
- [ ] No gaps in rotation coverage
- [ ] Rotation employees are still active (not quit, transferred, etc.)

**Adjust if needed:**
- Update rotation if employee unavailable this week
- Create exceptions for one-time changes
- Balance rotation assignments (don't overload one employee)

---

### Step 14: Review Week Ahead Schedule
**Time**: 15 minutes
**Location**: Calendar view (full week)

**Validate:**
- [ ] Monday through Friday schedules are complete
- [ ] Weekend events handled (if applicable)
- [ ] Employee workload balanced
- [ ] No employee working too many days consecutively
- [ ] Core events evenly distributed

**Planning:**
- Identify potential issues (multiple events same store, travel conflicts)
- Preemptively adjust schedule if needed
- Communicate weekly plan to team

---

## Monthly Routine (1st of Month)

### Step 15: Review Rotation Effectiveness
**Time**: 20 minutes
**Reports**: Rotation usage, employee workload, failed schedules

**Analyze:**
- Are rotation assignments balanced?
- Are rotation employees available most days (low exception rate)?
- Are certain employees consistently unavailable?
- Are rotation assignments leading to successful auto-scheduling?

**Adjust:**
- Rebalance rotations if one employee overloaded
- Change rotation days if availability patterns changed
- Consider adding more employees to rotation pool

---

### Step 16: Audit Event Types and Rules
**Time**: 15 minutes
**Reports**: Event type distribution, scheduling success rate

**Review:**
- Are all event types being imported correctly?
- Are events being detected as correct type (Core, Juicer, Digital, etc.)?
- Are scheduling rules still appropriate (time slots, daily limits, etc.)?
- Are there new event types that need configuration?

**Update:**
- Adjust event type detection rules if misclassifications occur
- Update time slots if business needs changed
- Document any rule changes

---

## Emergency Procedures

### Employee No-Show
**When**: Employee doesn't show up for event

**Immediate actions:**
1. Contact employee (call, text, email)
2. Find replacement employee:
   - Check who else is available/not scheduled
   - Verify replacement has correct role (Lead for Digital, etc.)
   - Contact replacement and confirm
3. Update schedule in system:
   - Remove original employee
   - Add replacement employee
   - Document reason in notes
4. Submit change to API
5. Print new paperwork for replacement
6. Notify store if event will be delayed

---

### Event Added Last-Minute (Within 3-Day Window)
**When**: MVRetail adds event that needs to happen tomorrow or today

**Immediate actions:**
1. Manually schedule (can't use auto-scheduler within 3-day window)
2. Check rotation assignments for that day
3. Assign appropriate employee:
   - Juicer event → rotation Juicer
   - Digital/Freeosk → Primary Lead
   - Core → available Lead or Specialist
4. Verify employee availability (time off, conflicts)
5. Generate paperwork immediately
6. Contact employee with assignment
7. Submit to API

---

### Auto-Scheduler Fails to Run
**When**: Scheduled auto-scheduler run doesn't execute or crashes

**Immediate actions:**
1. Check SchedulerRunHistory for error message
2. Review error details:
   - Database connection issue?
   - Missing rotation assignments?
   - Code error?
3. Fix underlying issue if possible
4. Manually run auto-scheduler
5. If still failing, manually schedule critical events (due soon)
6. Contact IT/developer if issue persists

---

### MVRetail API Down
**When**: Can't sync events or submit schedules to MVRetail

**Immediate actions:**
1. Continue scheduling locally (don't wait for API)
2. Generate paperwork from local database
3. Manually notify employees of assignments (text/email)
4. Document all local-only changes
5. When API returns:
   - Batch submit all pending schedules
   - Verify sync status
   - Reconcile any conflicts

---

## Tips for Success

### Daily Habits
- **Check dashboard first thing** - Don't start your day blind
- **Run auto-scheduler daily** - Even if few events, keeps 3-day buffer full
- **Print paperwork early** - Don't wait until last minute
- **Communicate proactively** - Tell employees their assignments early

### Weekly Habits
- **Review rotations Monday** - Ensures week starts smoothly
- **Balance workload** - Don't overload same employees
- **Plan ahead** - Look at next week on Friday

### Tools to Use
- **Calendar view** - Visual overview of all assignments
- **Dashboard** - Quick status check
- **Auto-scheduler** - Let system do heavy lifting
- **Audit reports** - Catch issues automatically

### Common Mistakes to Avoid
- ❌ Forgetting to approve pending schedules (stuck in limbo)
- ❌ Not checking rotation exceptions (wrong employee shows up)
- ❌ Ignoring failed events (they don't disappear on their own)
- ❌ Not submitting to API (employees don't see assignments)
- ❌ Printing paperwork too late (employees already left)

---

## Checklist: Did I Do Everything Today?

**Morning:**
- [ ] Checked daily validation dashboard
- [ ] Reviewed automated audit report
- [ ] Validated rotation assignments
- [ ] Generated and printed today's paperwork
- [ ] Briefed employees on assignments

**Mid-Day:**
- [ ] Monitored event progress
- [ ] Reviewed tomorrow's schedule

**Afternoon:**
- [ ] Checked 3-day ahead schedule
- [ ] Ran auto-scheduler if needed
- [ ] Approved and submitted pending schedules

**End of Day:**
- [ ] Verified today's events completed
- [ ] Confirmed tomorrow is ready

**Weekly (Monday):**
- [ ] Reviewed weekly rotations
- [ ] Validated week ahead schedule

---

## Quick Reference: Key Pages in Webapp

| Page | URL | Purpose |
|------|-----|---------|
| Daily Dashboard | `/dashboard/daily-validation` | Morning status check |
| Calendar | `/calendar` | View all events by date |
| Auto-Scheduler | `/auto-scheduler` | Run scheduler, review pending |
| Rotation Management | `/rotations` | Configure weekly rotations |
| Employee Management | `/employees` | View availability, time off |
| Audit Log | `/audit/log` | Review automated checks |
| Pending Schedules | `/auto-scheduler/pending` | Approve/edit proposals |

---

## Contact Information

**Technical Issues:**
- IT Support: [Contact info]
- Developer: [Contact info]

**Business Issues:**
- MVRetail Support: [Contact info]
- Store Coordinator: [Contact info]

---

**Document Version**: 1.0
**Last Updated**: Generated with scheduling system
**Review Frequency**: Monthly (adjust as processes evolve)
