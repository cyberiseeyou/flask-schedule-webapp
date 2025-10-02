# Auto-Scheduler Feature - Brainstorming Session Results

**Session Date:** 2025-10-01
**Topic:** Auto-Scheduling Feature for Event Management System
**Duration:** ~45 minutes
**Techniques Used:** Systems Thinking, Reverse Thinking, Convergent Analysis

---

## Executive Summary

### Session Goals
- Design an auto-scheduling feature that schedules all events with start dates within 3 weeks of current date
- Ensure the system follows all existing manual scheduling restrictions and business rules
- Create a user-approval workflow with clear visibility into proposed changes
- Handle conflicts, failures, and edge cases gracefully

### Key Outcomes
- **Comprehensive system architecture** defined with clear priority rules and constraint enforcement
- **5-phase implementation roadmap** established for systematic development
- **User control mechanisms** designed: rotation assignments, editable proposals, manual triggers
- **Error handling strategies** identified for crashes, API failures, and deadline conflicts

### Ideas Generated
- 6 major feature categories identified
- 17 distinct implementation components mapped
- 5 deployment phases prioritized
- Multiple conflict resolution strategies defined

### Key Themes
1. **User approval before execution** - System proposes, humans approve
2. **Intelligent conflict resolution** - Auto-bump lower-priority events for urgent deadlines
3. **Graceful failure handling** - Log failures, notify users, allow manual intervention
4. **Flexible rotation management** - Standing rotations with one-time exception overrides

---

## Technique 1: Systems Thinking

**Duration:** ~20 minutes
**Purpose:** Map all inputs, constraints, and system dependencies

### Ideas Generated

#### System Inputs & Data Requirements

**Event Data:**
- Event number, type, name
- Start date and due date (must complete BEFORE due date)
- Event status and locked indicator
- Associated items and instructions
- Event type classifications (CORE, Supervisor, Digital Setup/Refresh/Teardown, Freeosk, Other, Juicer)

**Employee Data:**
- Employee roles: Lead Event Specialist, Event Specialist, Juicer Barista, Club Supervisor
- Availability windows (days/times available to work)
- Requested time off
- Current schedule/existing assignments
- Role-specific capabilities

**Business Rules:**
- One core event per employee per day (hard limit)
- Events must be scheduled within start date and BEFORE due date
- Lead Event Specialists get scheduling priority over Event Specialists
- Club Supervisor not scheduled to regular events
- Role-based event restrictions enforced

**Weekly Rotation Assignments:**
- Primary Juicer rotation (Monday-Friday assignments)
- Primary Lead rotation (Monday-Friday assignments)
- Secondary Lead (auto-assigned to any Lead who isn't Primary for that day)

#### Scheduling Priority Order

**Phase 1: Weekly Rotations (Locked First)**
1. Juicer events → Assigned to Primary Juicer for that day of week
2. Digital Setups, Digital Refresh, Freeosk → Primary Lead for that day
3. Digital Teardowns → Secondary Lead for that day

**Phase 2: Remaining Events (Due Date Priority)**
4. Core events → Lead Event Specialists first, then Event Specialists (closest to due date first)
5. Supervisor events → Automatically paired with corresponding Core event (Club Supervisor at Noon, or Lead if unavailable)

#### Constraint Validation Rules

**Hard Constraints (Never Violate):**
- Never schedule employee outside availability window
- Never schedule employee on requested time off
- Never schedule employee if already scheduled for that time
- Never schedule more than one core event per employee per day
- Never schedule event after its due date
- Never schedule Club Supervisor to regular events
- Never schedule non-Lead to Freeosk/Digital/Other events
- Never schedule non-Juicer to Juicer events

**Soft Constraints (Prefer but Can Override with User Approval):**
- Prefer to keep existing schedules unchanged
- Prefer balanced workload distribution
- Prefer not to bump already-scheduled events

#### Event Type Assignment Logic

**CORE Events:**
- Eligible: Lead Event Specialists (priority), Event Specialists (secondary)
- Limit: 1 per employee per day
- Sorting: By due date (urgent first)

**Supervisor Events:**
- Must be same day as corresponding CORE event
- Priority 1: Club Supervisor at Noon
- Priority 2: Lead Event Specialist who has a CORE event that day
- Error if no Lead has CORE event

**Digital Setups, Digital Refresh, Freeosk:**
- Priority 1: Primary Lead for that day
- Priority 2: Any other available Lead
- Priority 3: Club Supervisor

**Digital Teardowns:**
- Priority 1: Secondary Lead for that day (any Lead who isn't Primary)
- Priority 2: Club Supervisor

**Juicer Events:**
- Assigned to Primary Juicer for that day of week
- If Primary Juicer unavailable → Save to manual review list

### Insights & Patterns

- **Hierarchy matters** - Lead specialists get priority, creating a natural flow
- **Rotations provide structure** - Weekly assignments prevent chaos and ensure fairness
- **Pairing logic reduces complexity** - Supervisor events auto-pair with Core events
- **Role-based restrictions prevent errors** - Type system enforces business rules automatically

---

## Technique 2: Reverse Thinking

**Duration:** ~10 minutes
**Purpose:** Identify potential failure modes and design guardrails

### Ideas Generated

#### Critical Failures to Prevent

**Worst-Case Scenario 1: Schedule People on Days Off**
- **Impact:** Destroys trust in system, creates staffing chaos
- **Guardrail Needed:** Hard validation against time-off requests and availability windows
- **Solution:** Pre-scheduling validation layer that rejects assignments to unavailable employees

**Worst-Case Scenario 2: Miss Event Deadlines**
- **Impact:** Compliance violations, customer dissatisfaction, business disruption
- **Guardrail Needed:** Deadline awareness with escalation logic
- **Solution:**
  - Sort events by due date urgency
  - Auto-bump lower-priority events to make room for urgent deadlines
  - Flag events approaching deadlines with "CRITICAL" indicators
  - Require user approval before bumping

#### Additional Failure Modes Identified

**Rotation Employee Unavailable:**
- Primary Juicer or Primary Lead on vacation
- **Solution:** Prompt manager to select one-time replacement (doesn't change standing rotation)

**System Overload:**
- Too many events, not enough staff
- **Solution:** Bumping strategy + failed events list with reasons

**API Failures During Submission:**
- Crossmark system down or individual call failures
- **Solution:** Continue processing, log failures, persistent notifications until resolved

**Scheduler Crash Mid-Run:**
- Unexpected errors during overnight processing
- **Solution:** Crash recovery prompt on login ("Run now or dismiss?") + manual trigger option

### Insights & Patterns

- **Trust is fragile** - One bad auto-assignment destroys confidence; must be bulletproof on basics
- **Transparency builds confidence** - Always explain WHY something failed
- **Human override is essential** - System proposes, humans approve
- **Graceful degradation** - Better to fail gracefully than schedule incorrectly

---

## Technique 3: Convergent Analysis

**Duration:** ~15 minutes
**Purpose:** Organize ideas into actionable categories and implementation phases

### Feature Categories

#### Category 1: Core Scheduling Engine

**Components:**
- Background batch job (runs nightly at 2 AM)
- Scheduling algorithm with priority logic
- Constraint validation system
- Conflict resolution & bumping logic
- Manual trigger option

**Key Behaviors:**
- Processes events with start dates within 3 weeks of current date
- Follows strict priority order (Juicer → Digital → Core → Supervisor)
- Validates all constraints before proposing assignments
- Auto-bumps lower-priority events for urgent deadlines
- Generates pending proposal for manager review

#### Category 2: User Configuration Interface

**Rotation Assignments Page:**
- Primary Juicer Rotation section (Mon-Fri dropdowns, filtered to Juicer Baristas only)
- Primary Lead Rotation section (Mon-Fri dropdowns, filtered to Lead Event Specialists only)
- Persistent assignments (don't change week-to-week unless manually updated)
- Exception handling: One-time replacement prompts when rotation employee unavailable

#### Category 3: Proposal Review & Approval

**Auto-Schedule Review Interface:**
- **Section 1:** Newly Scheduled Events
  - Shows: Event #, Type, Employee, Date/Time
  - Clean assignments with no conflicts

- **Section 2:** Events Requiring Swaps
  - Shows: New priority event ↔ Event being bumped
  - Both events' details with swap rationale

- **Section 3:** Daily Schedule Preview
  - Calendar view of complete daily assignments
  - Visual workload distribution confirmation

- **Section 4:** Failed Events List
  - Events that couldn't be scheduled
  - Reason codes for each failure

**Manager Capabilities:**
- Edit proposed schedule before approval
- Approve entire schedule
- Triggers sequential API calls to Crossmark

#### Category 4: Error Handling & Recovery

**API Call Failure Handling:**
- Continue processing remaining events
- Log failures with details (event, employee, timestamp, error)
- Show failed submissions in completion report
- Persistent notification: "You have unscheduled events pending submission to Crossmark"
- Badge/alert on every login until resolved

**Scheduler Crash Recovery:**
- On login after crash: "Auto-scheduler failed during last run. Run now or dismiss?"
- Manual trigger: "Run Auto-Scheduler" button available anytime
- If dismissed: Auto-runs again that night

**Deadline Protection:**
- Auto-bump lower-priority events to make room for urgent deadlines
- Show swaps in "Events Requiring Swaps" section
- Requires manager approval before executing

#### Category 5: Notifications & Dashboard

**Dashboard Integration:**
- Badge/notification when pending schedule awaits review
- Click notification → Navigate to Auto-Schedule Review page
- Single notification type (no severity-based alerts)

**Status Messages:**
- "All events within 3 weeks are already scheduled" (when nothing to do)
- Failed events shown in report section (no special alerts)

#### Category 6: Data Management

**Pending Schedule Lifecycle:**
- Unapproved proposals treated as "current schedule" for next run
- New runs build on top of pending proposals (no conflicts)
- Prevents multiple competing proposals

**History & Retention:**
- Summary view of auto-scheduler runs (date, events scheduled, success rate)
- Auto-purge data older than 3 weeks
- Track auto-scheduled vs. manually scheduled events (for analytics)

### Implementation Phases

#### PHASE 1: Foundation (Must Build First)
**Rationale:** Core infrastructure everything else depends on

1. **Rotation Assignments Page**
   - UI with Monday-Friday dropdowns
   - Filtered employee dropdowns by role
   - Save/update rotation configuration

2. **Database Schema**
   - `rotation_assignments` table (juicer_rotation, lead_rotation)
   - `pending_schedules` table (proposed assignments awaiting approval)
   - `scheduler_run_history` table (run logs, success metrics)
   - `schedule_exceptions` table (one-time rotation overrides)

3. **Constraint Validation System**
   - Reusable validation functions
   - Check availability, time-off, role restrictions
   - Return violation reasons for logging

#### PHASE 2: Scheduling Engine (Core Value)
**Rationale:** The heart of the feature - delivers primary value

4. **Scheduling Algorithm**
   - Priority-based assignment logic
   - Due date sorting
   - Role-based event type routing
   - Rotation-aware assignments

5. **Conflict Resolution & Bumping Logic**
   - Identify capacity conflicts
   - Auto-select events to bump (furthest from due date)
   - Generate swap proposals

6. **Background Batch Job**
   - Scheduled task (2 AM daily)
   - Process 3-week event window
   - Generate pending proposal

7. **Manual Trigger Option**
   - User-initiated scheduler runs
   - For testing and crash recovery

#### PHASE 3: User Approval Flow (Makes it Usable)
**Rationale:** Users need to review and approve before it's useful

8. **Proposal Review Interface**
   - 4-section approval screen
   - Newly scheduled, swaps, daily preview, failed events

9. **Editable Proposed Schedule**
   - Manager modifications before approval
   - Inline editing of assignments

10. **Dashboard Notifications**
    - Badge for pending reviews
    - Persistent alerts for failed API calls
    - Click-through navigation

#### PHASE 4: API Integration (Makes it Complete)
**Rationale:** Actually submits schedules to Crossmark

11. **API Call Sequencing**
    - One-at-a-time submission
    - Detailed logging (event, employee, timestamp, result)

12. **Failure Handling & Retry Logic**
    - Continue on failure
    - Persistent notifications
    - Manual retry option

13. **Completion Report**
    - Success/failure summary
    - Failed events with reasons
    - API call logs

#### PHASE 5: Polish & Recovery (Production-Ready)
**Rationale:** Handles edge cases and crashes gracefully

14. **Crash Recovery Prompts**
    - "Run now or dismiss?" dialog
    - Manual trigger always available

15. **Rotation Exception Handling**
    - One-time replacement prompts
    - Date-specific overrides

16. **History & Data Retention**
    - Auto-purge after 3 weeks
    - Run history summary view

17. **Analytics/Summary View**
    - Scheduler performance metrics
    - Success rates over time

---

## Idea Categorization

### Immediate Opportunities (Ready to Implement Now)

**Phase 1 Components:**
- Rotation Assignments Page UI
- Database schema for rotations and pending schedules
- Basic constraint validation functions

**Why Immediate:**
- Well-defined requirements
- No external dependencies
- Foundational for other features
- Can be tested independently

**Next Steps:**
- Design database schema
- Create Rotation Assignments page mockup/wireframe
- Implement validation logic as utility functions

---

### Future Innovations (Requires Development/Research)

**Advanced Scheduling Intelligence:**
- Machine learning to predict optimal assignments based on historical performance
- Employee preference learning (e.g., "Sarah does better with Digital events on Tuesdays")
- Predictive workload balancing (prevent burnout patterns)

**Enhanced Analytics:**
- Auto-scheduler performance dashboards
- Employee utilization reports
- Event completion rate trends
- Bottleneck identification

**Mobile Integration:**
- Push notifications for pending approvals
- Mobile approval interface
- Quick-edit proposed schedules from phone

**Why Future:**
- Requires Phase 1-4 completion first
- Need historical data for ML models
- Mobile app infrastructure needed
- Not critical for MVP

---

### Moonshots (Ambitious, Transformative Concepts)

**AI-Powered Scheduling Assistant:**
- Natural language interface: "Schedule all juice bar events for next week"
- Conversational approval: "Looks good except move Sarah to Wednesday"
- Proactive suggestions: "You have 3 Leads on vacation next week - should we redistribute rotations?"

**Predictive Event Creation:**
- Analyze historical patterns to suggest upcoming events
- "You usually have 5 juice bar events in October - should I create them?"
- Seasonal trend detection and auto-event generation

**Cross-Location Optimization:**
- Multi-store scheduling coordination
- Employee sharing across locations
- Resource pooling for busy periods

**Why Moonshot:**
- Requires significant AI/NLP investment
- Multi-tenant architecture changes
- Beyond current scope but inspiring for long-term vision

---

### Insights & Learnings

**Key Realizations from Session:**

1. **Rotations are the foundation** - Without weekly rotation assignments configured, auto-scheduler can't function effectively. This is the critical first step.

2. **User approval is non-negotiable** - The system must propose, not execute. Trust is built through transparency and control.

3. **Deadline protection is paramount** - Missing event deadlines is the worst failure mode. Auto-bumping with approval is the right balance.

4. **Graceful degradation beats perfection** - Better to schedule 90% successfully and flag 10% for manual review than to fail entirely or make bad guesses.

5. **The "pending schedule as current schedule" insight** - This prevents proposal conflicts and allows iterative refinement over multiple days.

6. **Secondary Lead auto-assignment** - "Any Lead who isn't Primary" is simple and flexible. No need for complex rotation configuration.

7. **One-time exceptions don't break rotations** - Rotation overrides are date-specific, preserving the standing rotation for future weeks.

8. **API calls happen AFTER approval** - This separates scheduling logic from integration, making testing easier and failures recoverable.

---

## Action Planning

### Top 3 Priority Ideas with Rationale

#### Priority 1: Build Rotation Assignments Page + Database Schema
**Rationale:**
- Absolute prerequisite for auto-scheduler functionality
- Low complexity, high impact
- Can be built and tested independently
- Provides immediate value (centralizes rotation management even before auto-scheduler exists)

**Next Steps:**
1. Design database schema for `rotation_assignments` table
2. Create Rotation Assignments page UI (two sections: Juicer rotation, Lead rotation)
3. Implement save/load functionality
4. Add validation (ensure selected employees have correct roles)
5. Test with current manual scheduling workflow

**Resources Needed:**
- Database migration tools
- UI framework/templates
- Employee role data already in system

**Timeline:**
- Database schema: 1 day
- UI implementation: 2-3 days
- Testing: 1 day
- **Total: ~1 week**

---

#### Priority 2: Build Core Scheduling Algorithm (Without API Integration)
**Rationale:**
- The heart of the feature
- Can be tested offline without affecting production
- Validates feasibility of constraint logic
- Provides foundation for all future enhancements

**Next Steps:**
1. Implement constraint validation functions (availability, time-off, role checks)
2. Build priority-based assignment logic
3. Implement conflict detection and bumping strategy
4. Create pending schedule data structure
5. Unit test with realistic scenarios

**Resources Needed:**
- Access to current scheduling business logic
- Test data (employees, events, availability, time-off)
- Validation against manual scheduling rules

**Timeline:**
- Validation functions: 2-3 days
- Assignment algorithm: 3-4 days
- Conflict resolution: 2-3 days
- Testing: 2-3 days
- **Total: ~2 weeks**

---

#### Priority 3: Build Proposal Review Interface
**Rationale:**
- Makes scheduling algorithm usable
- Critical feedback loop for managers
- Low risk (read-only until approval)
- Validates that proposed schedules make sense to users

**Next Steps:**
1. Design 4-section approval interface mockup
2. Implement newly scheduled events list
3. Implement events requiring swaps list
4. Implement daily schedule preview
5. Implement failed events list with reasons
6. Add inline editing capability
7. User acceptance testing with managers

**Resources Needed:**
- Calendar/schedule visualization component
- UI components for lists and tables
- Pending schedule data from Priority 2

**Timeline:**
- UI design: 2 days
- Section 1-2 implementation: 2-3 days
- Section 3 (calendar view): 2-3 days
- Section 4 + editing: 2 days
- Testing: 2 days
- **Total: ~2 weeks**

---

### Overall Timeline Estimate

**Phase 1 (Foundation):** 1-2 weeks
**Phase 2 (Scheduling Engine):** 2-3 weeks
**Phase 3 (Approval Flow):** 2-3 weeks
**Phase 4 (API Integration):** 1-2 weeks
**Phase 5 (Polish & Recovery):** 1-2 weeks

**Total Estimated Development Time:** 7-12 weeks (depending on testing cycles and iterations)

---

## Reflection & Follow-up

### What Worked Well in This Session

- **Systems Thinking provided comprehensive coverage** - Mapping inputs, constraints, and flows upfront prevented missed requirements
- **Reverse Thinking identified critical guardrails** - Focusing on failure modes revealed must-have validations
- **Convergent phase created actionable roadmap** - Organizing ideas into phases makes implementation feel achievable
- **Interactive dialogue built on ideas** - Each answer led to deeper questions and refinements

### Areas for Further Exploration

**Technical Architecture Questions:**
- Should scheduler be a separate microservice or integrated into main Flask app?
- Database transaction strategy for pending schedules (atomic operations needed?)
- Caching strategy for rotation assignments and employee data
- Performance optimization for large event sets (100+ events in 3-week window)

**UX/UI Design Questions:**
- Calendar visualization details (daily/weekly/monthly views?)
- Mobile responsiveness for approval interface
- Real-time updates if scheduler runs while manager reviewing proposal
- Color coding and visual indicators for event types and urgency

**Edge Cases & Business Logic:**
- What if employee is terminated mid-week while in rotation?
- Should rotations support "off-weeks" (e.g., rotation employee on vacation entire week)?
- Can events have partial time requirements (e.g., 2-hour setup vs. 4-hour demo)?
- Should there be limits on how many events can be bumped?

### Recommended Follow-up Techniques

**For Next Brainstorming Session:**

1. **Prototyping** - Build quick mockups of Rotation Assignments page and Approval Interface
   - Get real user feedback on UI/UX
   - Validate that interface makes sense to managers

2. **User Story Mapping** - Create detailed user stories for each phase
   - "As a manager, I want to configure weekly rotations so that..."
   - Define acceptance criteria for each feature

3. **Risk Analysis** - Deep dive on technical risks
   - Database performance with large datasets
   - API rate limiting and retry strategies
   - Concurrent access (two managers approving simultaneously)

4. **Testing Strategy Workshop** - Define test scenarios
   - Unit tests for constraint validation
   - Integration tests for scheduling algorithm
   - User acceptance testing criteria

### Questions That Emerged for Future Sessions

1. **How should the system handle holiday weeks or special events?**
   - Should there be "event blackout dates"?
   - Can rotations have holiday overrides?

2. **Should employees be able to see proposed schedules before manager approves?**
   - Transparency vs. avoiding confusion if proposals change

3. **What reporting/analytics do managers need to trust the auto-scheduler?**
   - Success rate over time?
   - Time saved vs. manual scheduling?
   - Employee workload balance metrics?

4. **Should there be role-based access control for rotation configuration?**
   - Can only senior managers edit rotations?
   - Audit log for rotation changes?

5. **How should the system handle newly created events that arrive after overnight run?**
   - Should scheduler auto-run on event creation?
   - Or wait for next nightly run?

---

## Appendix: Raw Ideas & Notes

### Constraint Validation Ideas
- Pre-flight validation before API calls
- Dry-run mode for testing algorithm changes
- Validation error taxonomy (availability, role, capacity, deadline, conflict)

### UI/UX Ideas
- Color-coded event types in calendar view
- Drag-and-drop to edit proposed schedule
- "Auto-schedule this event now" quick action
- Bulk approve/reject for event groups

### Performance Optimization Ideas
- Cache rotation assignments (invalidate on change)
- Index events by due date for fast sorting
- Lazy-load daily preview (only render visible dates)
- Background job queue for large scheduler runs

### Future Feature Ideas
- Employee skills/certifications tracking (beyond just roles)
- Preferred time slots per employee
- Team-based scheduling (ensure certain employees work together)
- Budget/cost tracking for scheduled events
- Integration with payroll systems

---

**End of Brainstorming Session Report**
**Generated:** 2025-10-01
**Powered by BMAD™ Core**
