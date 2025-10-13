# QA Comprehensive Review
## Calendar Redesign - Quality Assurance Assessment

**Project:** Flask Schedule WebApp - Calendar Enhancement
**QA Reviewer:** Quinn (Test Architect)
**Review Date:** 2025-10-12
**Priority:** P0 (Critical - Data Integrity)
**Status:** 🔴 **CONCERNS** - Conditional Approval with Critical Testing Requirements

---

## Executive Summary

This calendar redesign is a **critical P0 project** that enhances user experience while introducing **significant business logic changes** to CORE-Supervisor event pairing. The project has been thoroughly analyzed across risk, testability, and quality dimensions.

### Quality Gate Decision: **🟡 CONCERNS (Conditional Pass)**

**Recommendation:** Approve for development **with mandatory quality gates**:
- ✅ **Approve UI/UX redesign** (Calendar view, Daily view, responsive design)
- ⚠️ **Conditional approval for CORE-Supervisor pairing logic** (requires comprehensive testing + rollback plan)
- 🔴 **Block production deployment** until all P0 test scenarios pass

### Key Findings:
- **3 HIGH RISK areas** requiring extensive testing
- **8 MEDIUM RISK areas** requiring standard test coverage
- **150+ test scenarios** identified across functional, integration, and NFR testing
- **Data integrity concerns** with CORE-Supervisor automatic pairing
- **Performance risks** with calendar aggregation queries

---

## Table of Contents

1. [Risk Profile Analysis](#1-risk-profile-analysis)
2. [Requirements Traceability](#2-requirements-traceability)
3. [Test Strategy](#3-test-strategy)
4. [Comprehensive Test Scenarios](#4-comprehensive-test-scenarios)
5. [Non-Functional Requirements (NFR) Assessment](#5-non-functional-requirements-nfr-assessment)
6. [Testability Assessment](#6-testability-assessment)
7. [Quality Gate Criteria](#7-quality-gate-criteria)
8. [Recommendations](#8-recommendations)

---

## 1. Risk Profile Analysis

### 1.1 Risk Assessment Matrix

| Risk Area | Probability | Impact | Risk Level | Mitigation |
|-----------|------------|--------|------------|------------|
| **CORE-Supervisor Pairing Data Corruption** | MEDIUM | **CRITICAL** | 🔴 **HIGH** | Comprehensive integration tests, database transactions, rollback plan |
| **Reschedule/Unschedule Orphaned Events** | MEDIUM | **CRITICAL** | 🔴 **HIGH** | Automated orphan detection, integrity constraints, monitoring |
| **Calendar Performance Degradation** | HIGH | **HIGH** | 🔴 **HIGH** | Query optimization, caching, load testing (1000+ events) |
| **Event Count Aggregation Errors** | MEDIUM | MEDIUM | 🟡 **MEDIUM** | Unit tests, data validation, error handling |
| **Responsive Design Breakage** | MEDIUM | MEDIUM | 🟡 **MEDIUM** | Cross-browser/device testing, visual regression tests |
| **Accessibility Violations (WCAG AA)** | MEDIUM | MEDIUM | 🟡 **MEDIUM** | Automated accessibility scans, manual screen reader testing |
| **Modal Focus Trap Failures** | LOW | MEDIUM | 🟡 **MEDIUM** | Keyboard navigation tests, focus management validation |
| **Unscheduled Event Detection Failures** | LOW | MEDIUM | 🟡 **MEDIUM** | Edge case testing, timezone handling |
| **Empty State UI Errors** | MEDIUM | LOW | 🟢 **LOW** | UI component tests, null-safety checks |
| **Mobile Touch Target Too Small** | LOW | LOW | 🟢 **LOW** | Manual mobile testing, touch target size validation |
| **Color Contrast Accessibility** | LOW | LOW | 🟢 **LOW** | Contrast checker tools, WCAG validation |

---

### 1.2 Critical Risk Deep Dive

#### 🔴 **RISK 1: CORE-Supervisor Pairing Data Corruption**

**Description:**
When rescheduling or unscheduling a CORE event, the new automatic pairing logic could fail mid-transaction, leaving:
- CORE event rescheduled but Supervisor event orphaned on old date
- CORE event unscheduled but Supervisor event still assigned
- Database in inconsistent state if rollback fails

**Probability:** MEDIUM
**Impact:** CRITICAL (Data integrity, business operations)

**Mitigation Strategy:**
1. **Database Transactions:**
   ```python
   @app.route('/api/reschedule_event', methods=['POST'])
   def reschedule_event():
       try:
           with db.session.begin_nested():  # Savepoint
               # Reschedule CORE event
               # Reschedule Supervisor event
               db.session.commit()
       except Exception as e:
           db.session.rollback()
           return jsonify({'error': str(e)}), 500
   ```

2. **Orphan Detection Job:**
   ```python
   def detect_orphaned_supervisor_events():
       # Daily cron job to find Supervisor events scheduled
       # on different dates than their paired CORE events
       orphans = db.session.query(Event).filter(
           Event.project_name.like('%Supervisor%'),
           Event.condition == 'Scheduled'
       ).all()

       for sup_event in orphans:
           core_event = get_core_event(sup_event)
           if core_event and core_event.schedule.start_datetime.date() != sup_event.schedule.start_datetime.date():
               alert_admins(f"Orphaned Supervisor event: {sup_event.event_id}")
   ```

3. **Integration Tests:**
   - Test transaction rollback on failure
   - Test concurrent reschedule/unschedule operations
   - Test edge cases (Supervisor exists but CORE doesn't, etc.)

**Test Coverage Required:** 95%+ for pairing logic
**Mandatory Before Production:** Yes

---

#### 🔴 **RISK 2: Reschedule/Unschedule Orphaned Events**

**Description:**
New pairing logic uses regex extraction (`\d{6}-CORE-`) to match events. If event naming convention changes or regex fails:
- `get_supervisor_event()` returns `None`
- Pairing silently fails
- Supervisor events become orphaned

**Example Failure Scenarios:**
- Event named `606001-Core-Product` (lowercase 'c') → regex fails
- Event named `60601-CORE-Product` (5 digits) → regex fails
- Event named `ABC123-CORE-Product` (non-numeric) → regex fails

**Probability:** MEDIUM
**Impact:** CRITICAL

**Mitigation Strategy:**
1. **Robust Event Matching:**
   ```python
   def get_supervisor_event(core_event):
       # Try multiple matching strategies

       # Strategy 1: Regex on 6-digit number
       match = re.search(r'(\d{6})-CORE-', core_event.project_name, re.IGNORECASE)
       if match:
           event_number = match.group(1)
           supervisor = Event.query.filter(
               Event.project_name.ilike(f'{event_number}-Supervisor-%')
           ).first()
           if supervisor:
               return supervisor

       # Strategy 2: Use parent_event_ref_num field (if populated)
       if core_event.parent_event_ref_num:
           supervisor = Event.query.filter_by(
               parent_event_ref_num=core_event.parent_event_ref_num,
               event_type__like='%Supervisor%'
           ).first()
           if supervisor:
               return supervisor

       # Strategy 3: Fuzzy matching on project_name
       # (last resort, log warning)

       return None
   ```

2. **Validation & Logging:**
   ```python
   def reschedule_event():
       # ... existing code ...

       if '-CORE-' in event.project_name:
           supervisor_event = get_supervisor_event(event)
           if not supervisor_event:
               logger.warning(f"No Supervisor event found for CORE event {event.event_id}: {event.project_name}")
               # Continue with CORE reschedule only
           else:
               # Reschedule supervisor
               logger.info(f"Auto-rescheduled Supervisor event {supervisor_event.event_id} to {new_date}")
   ```

3. **Monitoring Dashboard:**
   - Daily report: "CORE events without paired Supervisor events"
   - Alert: "Supervisor pairing failure rate > 5%"

**Test Coverage Required:** 90%+ including edge cases
**Mandatory Before Production:** Yes

---

#### 🔴 **RISK 3: Calendar Performance Degradation**

**Description:**
Aggregated event count query must run for **every calendar page load**. With 1000+ events in a month:
- Query could take > 5 seconds
- Database load spikes
- Calendar becomes unusable

**Current Query:**
```python
event_counts = db.session.query(
    func.date(Event.start_datetime).label('date'),
    func.sum(case((Event.project_name.like('%-CORE-%'), 1), else_=0)).label('core_count'),
    # ... 5 more aggregations ...
).filter(
    func.date(Event.start_datetime).between(start_date, end_date)
).group_by(
    func.date(Event.start_datetime)
).all()
```

**Probability:** HIGH (with realistic data volumes)
**Impact:** HIGH (unusable UI)

**Mitigation Strategy:**
1. **Database Indexing:**
   ```sql
   CREATE INDEX idx_events_start_datetime ON events(start_datetime);
   CREATE INDEX idx_events_project_name ON events(project_name);
   CREATE INDEX idx_events_event_type ON events(event_type);
   CREATE INDEX idx_events_condition ON events(condition);
   ```

2. **Caching Layer:**
   ```python
   from functools import lru_cache
   from datetime import datetime, timedelta

   @lru_cache(maxsize=128)
   def get_calendar_event_counts(year, month):
       # Cache for 5 minutes
       cache_key = f"calendar:{year}:{month}"
       cached = cache.get(cache_key)
       if cached:
           return cached

       counts = _fetch_event_counts(year, month)
       cache.set(cache_key, counts, ex=300)  # 5 min TTL
       return counts
   ```

3. **Materialized View (if needed):**
   ```sql
   CREATE MATERIALIZED VIEW calendar_event_counts AS
   SELECT
       DATE(start_datetime) as event_date,
       SUM(CASE WHEN project_name LIKE '%-CORE-%' THEN 1 ELSE 0 END) as core_count,
       SUM(CASE WHEN event_type = 'Juicer Production' THEN 1 ELSE 0 END) as juicer_count,
       -- ... more aggregations
   FROM events
   GROUP BY DATE(start_datetime);

   REFRESH MATERIALIZED VIEW calendar_event_counts;  -- Run nightly or on event changes
   ```

**Performance SLA:** Calendar load < 2 seconds (95th percentile)
**Test Coverage Required:** Load testing with 10,000+ events
**Mandatory Before Production:** Yes (load testing)

---

### 1.3 Risk Mitigation Checklist

**Before Sprint 1 Starts:**
- [ ] Review and approve database transaction strategy
- [ ] Set up logging infrastructure for pairing operations
- [ ] Create database indexes for performance
- [ ] Set up caching infrastructure (Redis or in-memory)
- [ ] Define rollback plan for pairing logic bugs

**During Development:**
- [ ] Code review for all pairing logic changes
- [ ] Unit tests for `get_supervisor_event()` with edge cases
- [ ] Integration tests for reschedule/unschedule workflows
- [ ] Performance benchmarking for calendar queries

**Before Production Deployment:**
- [ ] Load testing with production-scale data
- [ ] Database backup created
- [ ] Rollback scripts tested
- [ ] Monitoring alerts configured
- [ ] Orphan detection job deployed

---

## 2. Requirements Traceability

### 2.1 User Story Mapping

| User Story | Acceptance Criteria | Test Coverage |
|------------|---------------------|---------------|
| **US-1: Full-Screen Calendar** | Desktop calendar uses 100vw, mobile/tablet responsive | ✅ Responsive tests |
| **US-2: Event Type Badges** | 6 color-coded badges (CORE, Juicer, Supervisor, Freeosk, Digitals, Other) | ✅ UI component tests |
| **US-3: Unscheduled Event Warning** | ⚠️ icon appears when `condition='Unstaffed'` events exist | ✅ Logic + UI tests |
| **US-4: Daily View Page** | Dedicated route `/calendar/daily/<date>` replaces modal | ✅ Integration tests |
| **US-5: Juicer/Lead Detection** | Summary banner shows Juicer and Primary Lead employees | ✅ Data logic tests |
| **US-6: Event Grouping** | 5 collapsible groups (Juicer, Freeosk, Digitals, CORE, Supervisor) | ✅ UI tests |
| **US-7: CORE-Supervisor Indicator** | CORE cards show ✅/⚠️ supervisor status | ✅ Logic + UI tests |
| **US-8: Supervisor Modal** | View/edit supervisor via modal, not separate section | ✅ Modal interaction tests |
| **US-9: Universal Action Buttons** | All events have Reschedule/Unschedule/Change Employee buttons | ✅ UI tests |
| **US-10: Trade Button (CORE only)** | CORE events have additional Trade button | ✅ UI + authorization tests |
| **US-11: Automatic Reschedule Pairing** | Rescheduling CORE event also reschedules Supervisor event | ✅🔴 **CRITICAL** Integration tests |
| **US-12: Automatic Unschedule Pairing** | Unscheduling CORE event also unschedules Supervisor event | ✅🔴 **CRITICAL** Integration tests |

### 2.2 Given-When-Then Scenarios

#### **US-11: Automatic Reschedule Pairing**

**Scenario 1: Successful Pairing on Reschedule**
```gherkin
GIVEN a CORE event "606001-CORE-Super Pretzel" scheduled on 2025-10-15
  AND a Supervisor event "606001-Supervisor-Super Pretzel" scheduled on 2025-10-15 at 12:00 PM
WHEN I reschedule the CORE event to 2025-10-20
THEN the CORE event start_datetime should be 2025-10-20
  AND the Supervisor event start_datetime should be 2025-10-20 at 12:00 PM
  AND both events should have condition='Scheduled'
```

**Scenario 2: CORE Rescheduled, No Supervisor Exists**
```gherkin
GIVEN a CORE event "606002-CORE-Nature Valley" scheduled on 2025-10-15
  AND NO matching Supervisor event exists
WHEN I reschedule the CORE event to 2025-10-20
THEN the CORE event start_datetime should be 2025-10-20
  AND no error should occur
  AND a warning should be logged: "No Supervisor event found for CORE event 606002"
```

**Scenario 3: CORE Rescheduled, Supervisor Unscheduled**
```gherkin
GIVEN a CORE event "606003-CORE-Cheetos" scheduled on 2025-10-15
  AND a Supervisor event "606003-Supervisor-Cheetos" with condition='Unstaffed' (not scheduled)
WHEN I reschedule the CORE event to 2025-10-20
THEN the CORE event start_datetime should be 2025-10-20
  AND the Supervisor event should remain condition='Unstaffed'
  AND the Supervisor event should NOT be rescheduled
```

**Scenario 4: Transaction Rollback on Failure**
```gherkin
GIVEN a CORE event "606004-CORE-Doritos" scheduled on 2025-10-15
  AND a Supervisor event "606004-Supervisor-Doritos" scheduled on 2025-10-15
  AND the database will fail during Supervisor reschedule (simulated)
WHEN I reschedule the CORE event to 2025-10-20
THEN the reschedule request should return HTTP 500 error
  AND the CORE event start_datetime should still be 2025-10-15 (rolled back)
  AND the Supervisor event start_datetime should still be 2025-10-15 (rolled back)
  AND an error should be logged with exception details
```

#### **US-12: Automatic Unschedule Pairing**

**Scenario 1: Successful Pairing on Unschedule**
```gherkin
GIVEN a CORE event "606001-CORE-Super Pretzel" scheduled with employee John Smith
  AND a Supervisor event "606001-Supervisor-Super Pretzel" scheduled with employee Jane Doe
WHEN I unschedule the CORE event
THEN the CORE event condition should be 'Unstaffed'
  AND the CORE event is_scheduled should be False
  AND the CORE event Schedule record should be deleted
  AND the Supervisor event condition should be 'Unstaffed'
  AND the Supervisor event is_scheduled should be False
  AND the Supervisor event Schedule record should be deleted
```

**Scenario 2: Unschedule CORE, No Supervisor**
```gherkin
GIVEN a CORE event "606005-CORE-Pepsi" scheduled
  AND NO matching Supervisor event exists
WHEN I unschedule the CORE event
THEN the CORE event condition should be 'Unstaffed'
  AND no error should occur
  AND a warning should be logged
```

---

## 3. Test Strategy

### 3.1 Testing Pyramid

```
           /\
          /  \  E2E Tests (10%)
         /────\  - Full user workflows (calendar → daily view → reschedule)
        /  🔴  \ - Cross-browser testing
       /────────\
      / Integr.  \ Integration Tests (30%)
     /────────────\ - API endpoint tests (reschedule, unschedule, daily view)
    /   🟡🟡🟡    \ - CORE-Supervisor pairing workflows
   /──────────────\ - Database transaction tests
  /   Unit Tests   \ Unit Tests (60%)
 /──────────────────\ - get_supervisor_event() logic
/____________________\ - Event count aggregation
  🟢🟢🟢🟢🟢🟢🟢       - UI component rendering
```

### 3.2 Test Phases

**Phase 1: Unit Testing (Developers)**
- Duration: Throughout development
- Coverage Target: 80% code coverage overall, 95% for pairing logic
- Tools: pytest, unittest
- Focus: Individual functions, pure logic

**Phase 2: Integration Testing (Developers + QA)**
- Duration: End of each sprint
- Coverage Target: All API endpoints, all user workflows
- Tools: pytest with database fixtures, Selenium for UI
- Focus: Multi-component interactions, database transactions

**Phase 3: System Testing (QA)**
- Duration: 1 week before production
- Coverage Target: All user stories, all acceptance criteria
- Tools: Manual testing, automated E2E tests
- Focus: End-to-end workflows, real-world scenarios

**Phase 4: Performance Testing (QA + DevOps)**
- Duration: 3 days before production
- Coverage Target: All critical paths under load
- Tools: Locust, JMeter
- Focus: Calendar query performance, concurrent user load

**Phase 5: Accessibility Testing (QA)**
- Duration: 2 days before production
- Coverage Target: WCAG AA compliance
- Tools: axe DevTools, NVDA, VoiceOver
- Focus: Keyboard navigation, screen readers, color contrast

**Phase 6: User Acceptance Testing (UAT - Product Owner)**
- Duration: 3 days before production
- Coverage Target: All user stories validated by business stakeholders
- Tools: Manual testing in staging environment
- Focus: Business value, usability, real-world workflows

---

## 4. Comprehensive Test Scenarios

### 4.1 Calendar Month View Tests

#### Functional Tests

**TC-001: Display Event Type Counts**
- **Priority:** P0
- **Given:** Calendar loaded for October 2025
- **When:** Events exist on Oct 15: 4 CORE, 2 Juicer, 4 Supervisor, 1 Freeosk, 3 Digitals, 0 Other
- **Then:**
  - Cell for Oct 15 displays badges: C:4, J:2, S:4, F:1, D:3, O:0
  - Colors match spec: CORE (red), Juicer (green), Supervisor (purple), Freeosk (orange), Digitals (blue), Other (gray)
  - Zero-count badges (O:0) have dashed border and muted color

**TC-002: Display Unscheduled Warning Icon**
- **Priority:** P0
- **Given:** Calendar loaded for October 2025
- **When:** 3 events on Oct 15 have `condition='Unstaffed'`
- **Then:**
  - Cell for Oct 15 displays ⚠️ icon in top-right corner
  - Icon color is #FFC107 (amber)
  - Tooltip shows "3 unscheduled events due this day"
  - Icon pulses on hover

**TC-003: No Warning Icon When All Scheduled**
- **Priority:** P1
- **Given:** Calendar loaded for October 2025
- **When:** All events on Oct 15 have `condition='Scheduled'`
- **Then:** No ⚠️ icon displayed on Oct 15 cell

**TC-004: Click Cell Navigates to Daily View**
- **Priority:** P0
- **Given:** Calendar displayed
- **When:** User clicks on Oct 15 cell
- **Then:**
  - Browser navigates to `/calendar/daily/2025-10-15`
  - Loading spinner displayed during navigation
  - Page transition is smooth (< 500ms)

**TC-005: Full-Screen Layout on Desktop**
- **Priority:** P1
- **Given:** Browser width = 1920px
- **When:** Calendar loaded
- **Then:**
  - Calendar container width = 100vw (minus scrollbar)
  - Cell min-height = 180px
  - Font sizes match desktop spec (h1: 3rem, body: 1.125rem)

**TC-006: Responsive Layout on Tablet**
- **Priority:** P1
- **Given:** Browser width = 1024px
- **When:** Calendar loaded
- **Then:**
  - Cell min-height = 140px
  - Badge font-size = 0.75rem
  - Container padding = 1.5rem

**TC-007: Responsive Layout on Mobile**
- **Priority:** P1
- **Given:** Browser width = 375px
- **When:** Calendar loaded
- **Then:**
  - Cell min-height = 120px
  - Badges display horizontally or as icons
  - Touch targets ≥ 44px × 44px

**TC-008: Empty Calendar Month**
- **Priority:** P2
- **Given:** Calendar loaded for month with NO events
- **When:** Viewing calendar
- **Then:**
  - All cells display zero counts: C:0, J:0, S:0, F:0, D:0, O:0
  - No warning icons displayed
  - Empty state message: "No events scheduled this month"

#### Performance Tests

**TC-009: Calendar Load Performance (100 Events)**
- **Priority:** P0
- **Given:** Database contains 100 events in October 2025
- **When:** User navigates to calendar page
- **Then:**
  - Page loads in < 1 second (95th percentile)
  - Aggregation query executes in < 200ms
  - No N+1 query issues (verified in SQL logs)

**TC-010: Calendar Load Performance (1000 Events)**
- **Priority:** P0
- **Given:** Database contains 1000 events in October 2025
- **When:** User navigates to calendar page
- **Then:**
  - Page loads in < 2 seconds (95th percentile)
  - Aggregation query uses database indexes
  - Caching reduces subsequent loads to < 500ms

**TC-011: Concurrent User Load**
- **Priority:** P1
- **Given:** 50 users simultaneously load calendar
- **When:** All users request October 2025
- **Then:**
  - All requests complete successfully
  - Average response time < 2 seconds
  - No database connection pool exhaustion

#### Accessibility Tests

**TC-012: Keyboard Navigation**
- **Priority:** P0
- **Given:** Calendar displayed
- **When:** User presses Tab key
- **Then:**
  - Focus moves to first calendar cell
  - Visual focus indicator (2px blue outline) visible
  - Pressing Enter opens daily view
  - Arrow keys navigate between cells (optional)

**TC-013: Screen Reader Announces Cell Content**
- **Priority:** P0
- **Given:** Screen reader active (NVDA/JAWS)
- **When:** User focuses on Oct 15 cell
- **Then:** Screen reader announces: "October 15, 2025. 4 CORE events, 2 Juicer events, 4 Supervisor events, 1 Freeosk event, 3 Digital events. Warning: 2 unscheduled events due."

**TC-014: Color Contrast (WCAG AA)**
- **Priority:** P0
- **Given:** Badge colors defined in CSS
- **When:** Running contrast checker
- **Then:**
  - All badge text-to-background contrast ≥ 4.5:1
  - Juicer badge uses #1e7e34 (darker green) for AA compliance
  - Warning icon #FFC107 meets AA for large text

---

### 4.2 Daily View Page Tests

#### Functional Tests

**TC-015: Display Daily View Header**
- **Priority:** P0
- **Given:** Daily view loaded for Oct 15, 2025
- **When:** Page renders
- **Then:**
  - Header displays "Friday, October 15, 2025"
  - "Back to Calendar" link navigates to `/calendar`
  - Date font-size = 2.5rem, bold

**TC-016: Display Juicer and Primary Lead**
- **Priority:** P0
- **Given:** Daily view for Oct 15
  - Juicer Production events assigned to John Smith and Jane Doe
  - CORE event assigned to Sarah Johnson (Lead Event Specialist)
- **When:** Summary banner renders
- **Then:**
  - Summary shows "🧃 Juicer: John Smith, Jane Doe"
  - Summary shows "👔 Primary Lead: Sarah Johnson"
  - Background color = #e7f3ff (light blue)

**TC-017: Display Warning When No Juicer**
- **Priority:** P1
- **Given:** Daily view for Oct 15
  - No Juicer Production events scheduled
- **When:** Summary banner renders
- **Then:**
  - Summary shows "🧃 Juicer: None scheduled"
  - Text color = #dc3545 (red warning)

**TC-018: Display Supervisor Summary**
- **Priority:** P1
- **Given:** Daily view for Oct 15
  - 3 Supervisor events with `condition='Scheduled'`
  - 1 Supervisor event with `condition='Unstaffed'`
- **When:** Summary banner renders
- **Then:**
  - Summary shows "✅ 3 Supervisor Events Scheduled"
  - Summary shows "⚠️ 1 Unscheduled Events Due Today"

**TC-019: Event Groups Display Correctly**
- **Priority:** P0
- **Given:** Daily view for Oct 15 with events in all categories
- **When:** Page renders
- **Then:**
  - 5 groups displayed: Juicer, Freeosk, Digitals, CORE, Supervisor
  - Groups in correct order (Juicer, Freeosk, Digitals, CORE, Supervisor)
  - Each group shows event count in header (e.g., "🎯 CORE EVENTS (4)")
  - All groups expanded except Supervisor (collapsed by default)

**TC-020: Collapse/Expand Event Group**
- **Priority:** P1
- **Given:** CORE Events group is expanded
- **When:** User clicks group header
- **Then:**
  - Group collapses with smooth animation (0.3s)
  - Arrow icon changes from ▼ to ▶
  - Event cards hidden
  - Clicking again expands group

**TC-021: Collapsible State Persists**
- **Priority:** P2
- **Given:** User collapsed CORE Events group
- **When:** User refreshes page or navigates back to daily view
- **Then:**
  - CORE Events group remains collapsed
  - State stored in `localStorage`

**TC-022: CORE Event Card with Scheduled Supervisor**
- **Priority:** P0
- **Given:** Daily view for Oct 15
  - CORE event "606001-CORE-Super Pretzel" assigned to John Smith
  - Supervisor event "606001-Supervisor-Super Pretzel" scheduled with Jane Doe @ 12:00 PM
- **When:** CORE event card renders
- **Then:**
  - Card displays event details (time, employee, store, duration, due date)
  - Supervisor status banner displayed: "✅ Supervisor Event Scheduled (Jane Doe @ 12:00 PM)"
  - Banner background = #d4edda (green)
  - Action buttons visible: [Reschedule] [Unschedule] [Trade] [Change Employee]
  - Additional button: [📋 View/Edit Supervisor Event]

**TC-023: CORE Event Card with Unscheduled Supervisor**
- **Priority:** P0
- **Given:** CORE event "606002-CORE-Nature Valley" scheduled
  - Supervisor event "606002-Supervisor-Nature Valley" with `condition='Unstaffed'`
- **When:** CORE event card renders
- **Then:**
  - Supervisor status banner: "⚠️ Supervisor Event NOT Scheduled"
  - Banner background = #fff3cd (amber warning)

**TC-024: CORE Event Card with No Supervisor**
- **Priority:** P1
- **Given:** CORE event "606999-CORE-Orphan" scheduled
  - NO matching Supervisor event exists
- **When:** CORE event card renders
- **Then:**
  - Supervisor status banner: "ℹ️ No Supervisor event configured for this CORE event"
  - Banner background = #d1ecf1 (info blue)

**TC-025: Empty Event Group**
- **Priority:** P2
- **Given:** Daily view for Oct 15
  - No Freeosk events scheduled
- **When:** Freeosk Events group renders
- **Then:**
  - Group header displays "🎪 FREEOSK EVENTS (0)"
  - Empty state message: "No Freeosk events scheduled for this day"
  - Text style: italic, centered, muted gray

#### Supervisor Modal Tests

**TC-026: Open Supervisor Modal**
- **Priority:** P0
- **Given:** CORE event card with "View/Edit Supervisor Event" button
- **When:** User clicks button
- **Then:**
  - Modal opens with fade-in + scale-up animation (0.3s)
  - Semi-transparent black overlay appears
  - Modal centered on viewport
  - Focus moves to first interactive element (employee dropdown)

**TC-027: Display Supervisor Event Details**
- **Priority:** P0
- **Given:** Supervisor modal opened for event "606001-Supervisor-Super Pretzel"
  - Assigned to Jane Doe @ 12:00 PM on Oct 15
- **When:** Modal renders
- **Then:**
  - Event name displayed: "606001-Supervisor-Super Pretzel"
  - Paired CORE displayed: "606001-CORE-Super Pretzel (John Smith)"
  - Current assignment shows: Jane Doe (Lead Event Specialist), 12:00 PM, Oct 15, 0.08 hours

**TC-028: Change Supervisor Employee**
- **Priority:** P0
- **Given:** Supervisor modal open
- **When:** User selects "Sarah Johnson" from dropdown and clicks [Update]
- **Then:**
  - API request: `POST /api/change_employee` with new employee_id
  - Modal displays success message
  - Supervisor event reassigned to Sarah Johnson
  - Modal closes

**TC-029: Reschedule Supervisor Time**
- **Priority:** P1
- **Given:** Supervisor modal open, event scheduled for 12:00 PM
- **When:** User changes time to 2:00 PM and clicks [Update]
- **Then:**
  - API request: `POST /api/reschedule_supervisor` with new time
  - Supervisor event rescheduled to 2:00 PM (same date)
  - Modal closes

**TC-030: Unschedule Supervisor Event**
- **Priority:** P1
- **Given:** Supervisor modal open
- **When:** User clicks [Unschedule Supervisor Event] button
- **Then:**
  - Confirmation dialog: "Are you sure you want to unschedule this Supervisor event?"
  - If confirmed, API request: `DELETE /api/unschedule/{schedule_id}`
  - Supervisor event condition = 'Unstaffed'
  - Modal closes
  - Daily view refreshes, Supervisor status shows ⚠️

**TC-031: Close Modal (Multiple Methods)**
- **Priority:** P1
- **Given:** Supervisor modal open
- **When:** User performs any of: clicks [×] button, clicks [Cancel], presses ESC key, clicks outside modal
- **Then:**
  - Modal closes with fade-out animation
  - Focus returns to triggering button
  - No changes saved

**TC-032: Modal Focus Trap**
- **Priority:** P0 (Accessibility)
- **Given:** Supervisor modal open
- **When:** User presses Tab repeatedly
- **Then:**
  - Focus cycles through: employee dropdown → [Update] → date input → time input → [Update] → [Unschedule] → [Save] → [Cancel] → back to employee dropdown
  - Focus never leaves modal
  - Shift+Tab reverses direction

---

### 4.3 CORE-Supervisor Pairing Tests (CRITICAL)

#### Reschedule Pairing Tests

**TC-033: Reschedule CORE, Supervisor Follows**
- **Priority:** 🔴 P0 (CRITICAL)
- **Given:**
  - CORE event "606001-CORE-Super Pretzel" scheduled on 2025-10-15 @ 10:00 AM (employee: John Smith)
  - Supervisor event "606001-Supervisor-Super Pretzel" scheduled on 2025-10-15 @ 12:00 PM (employee: Jane Doe)
- **When:** User reschedules CORE event to 2025-10-20 @ 10:00 AM
- **Then:**
  - CORE event `start_datetime` = 2025-10-20 10:00 AM
  - CORE event employee remains John Smith
  - Supervisor event `start_datetime` = 2025-10-20 12:00 PM (same date, default time)
  - Supervisor event employee remains Jane Doe
  - Both events have `condition='Scheduled'`
  - Database transaction committed successfully
  - Log entry: "Auto-rescheduled Supervisor event 12345 to 2025-10-20"

**TC-034: Reschedule CORE, No Supervisor Exists**
- **Priority:** 🔴 P0
- **Given:**
  - CORE event "606999-CORE-Orphan" scheduled on 2025-10-15
  - NO matching Supervisor event
- **When:** User reschedules CORE event to 2025-10-20
- **Then:**
  - CORE event rescheduled successfully
  - No error thrown
  - Log warning: "No Supervisor event found for CORE event 606999-CORE-Orphan"
  - HTTP 200 response

**TC-035: Reschedule CORE, Supervisor Unscheduled**
- **Priority:** 🔴 P0
- **Given:**
  - CORE event "606002-CORE-Nature Valley" scheduled on 2025-10-15
  - Supervisor event "606002-Supervisor-Nature Valley" exists but `condition='Unstaffed'` (no schedule)
- **When:** User reschedules CORE event to 2025-10-20
- **Then:**
  - CORE event rescheduled successfully
  - Supervisor event remains `condition='Unstaffed'` (NOT rescheduled)
  - No error thrown

**TC-036: Reschedule Transaction Rollback on Failure**
- **Priority:** 🔴 P0
- **Given:**
  - CORE event "606001-CORE-Super Pretzel" scheduled on 2025-10-15
  - Supervisor event "606001-Supervisor-Super Pretzel" scheduled on 2025-10-15
  - Database configured to fail on Supervisor update (test scenario)
- **When:** User reschedules CORE event to 2025-10-20
- **Then:**
  - HTTP 500 error returned
  - Error message: "Failed to reschedule Supervisor event: [database error]"
  - CORE event `start_datetime` still = 2025-10-15 (rolled back)
  - Supervisor event `start_datetime` still = 2025-10-15 (rolled back)
  - Database in consistent state

**TC-037: Reschedule with Employee Change**
- **Priority:** P1
- **Given:**
  - CORE event "606001-CORE-Super Pretzel" scheduled (employee: John Smith)
  - Supervisor event scheduled (employee: Jane Doe)
- **When:** User reschedules CORE event to new date AND changes employee to Sarah Johnson
- **Then:**
  - CORE event assigned to Sarah Johnson
  - Supervisor event remains assigned to Jane Doe (employee change does NOT cascade)
  - Both events rescheduled to new date

**TC-038: Reschedule Non-CORE Event (No Pairing)**
- **Priority:** P1
- **Given:** Juicer Production event scheduled on 2025-10-15
- **When:** User reschedules to 2025-10-20
- **Then:**
  - Juicer event rescheduled successfully
  - No pairing logic executed
  - No warnings logged

**TC-039: Reschedule with Invalid Event Number**
- **Priority:** P1
- **Given:** CORE event "ABC123-CORE-InvalidNumber" (non-numeric event number)
- **When:** User reschedules to 2025-10-20
- **Then:**
  - CORE event rescheduled successfully
  - Regex match fails, `get_supervisor_event()` returns None
  - Log warning: "Could not extract event number from: ABC123-CORE-InvalidNumber"
  - No error thrown

**TC-040: Reschedule with Lowercase 'core'**
- **Priority:** P1
- **Given:** CORE event "606001-core-Product" (lowercase)
- **When:** User reschedules to 2025-10-20
- **Then:**
  - Regex with `re.IGNORECASE` matches successfully
  - Supervisor event found and rescheduled
  - Case-insensitive matching works

#### Unschedule Pairing Tests

**TC-041: Unschedule CORE, Supervisor Also Unscheduled**
- **Priority:** 🔴 P0 (CRITICAL)
- **Given:**
  - CORE event "606001-CORE-Super Pretzel" scheduled (employee: John Smith)
  - Supervisor event "606001-Supervisor-Super Pretzel" scheduled (employee: Jane Doe)
- **When:** User clicks [Unschedule] on CORE event
- **Then:**
  - CORE event `condition` = 'Unstaffed'
  - CORE event `is_scheduled` = False
  - CORE Schedule record deleted from database
  - Supervisor event `condition` = 'Unstaffed'
  - Supervisor event `is_scheduled` = False
  - Supervisor Schedule record deleted
  - Log entry: "Auto-unscheduled Supervisor event 12345"

**TC-042: Unschedule CORE, No Supervisor Exists**
- **Priority:** 🔴 P0
- **Given:**
  - CORE event "606999-CORE-Orphan" scheduled
  - NO matching Supervisor event
- **When:** User unschedules CORE event
- **Then:**
  - CORE event unscheduled successfully
  - No error thrown
  - Log warning: "No Supervisor event found for CORE event 606999"

**TC-043: Unschedule Transaction Rollback**
- **Priority:** 🔴 P0
- **Given:**
  - CORE and Supervisor events both scheduled
  - Database fails during Supervisor unschedule (test scenario)
- **When:** User unschedules CORE event
- **Then:**
  - HTTP 500 error returned
  - CORE event still `condition='Scheduled'` (rolled back)
  - Supervisor event still `condition='Scheduled'` (rolled back)
  - Schedule records NOT deleted

**TC-044: Unschedule Non-CORE Event (No Pairing)**
- **Priority:** P1
- **Given:** Freeosk event scheduled
- **When:** User unschedules
- **Then:**
  - Freeosk event unscheduled
  - No pairing logic executed

#### Manual Scheduling Pairing Tests

**TC-045: Manual Schedule CORE, Supervisor Auto-Scheduled**
- **Priority:** 🔴 P0
- **Given:**
  - CORE event "606001-CORE-Super Pretzel" unscheduled
  - Supervisor event "606001-Supervisor-Super Pretzel" unscheduled
- **When:** User manually schedules CORE event via `/schedule` form (employee: John Smith, date: 2025-10-15)
- **Then:**
  - CORE event scheduled successfully
  - `auto_schedule_supervisor_event()` function called
  - Supervisor event automatically scheduled with available Lead/Supervisor at 12:00 PM on 2025-10-15
  - Both events `condition='Scheduled'`

**TC-046: Auto-Scheduler Schedules CORE and Supervisor**
- **Priority:** 🔴 P0
- **Given:**
  - Multiple unscheduled CORE events
  - Auto-scheduler run for week of 2025-10-15
- **When:** Auto-scheduler executes
- **Then:**
  - CORE events scheduled
  - For each scheduled CORE event, corresponding Supervisor event also scheduled
  - Supervisor events assigned to available Leads/Supervisors
  - No orphaned CORE events (CORE scheduled without Supervisor)

**TC-047: CSV Import with CORE Events**
- **Priority:** P1
- **Given:** CSV file contains CORE event schedules
- **When:** User imports CSV
- **Then:**
  - CORE events scheduled from CSV
  - Supervisor auto-scheduling triggered for each CORE event
  - Import summary shows: "10 CORE events scheduled, 10 Supervisor events auto-scheduled"

#### Edge Case & Error Handling Tests

**TC-048: Concurrent Reschedule Attempts**
- **Priority:** P1
- **Given:**
  - CORE event "606001-CORE-Super Pretzel" scheduled
  - Two users simultaneously attempt to reschedule to different dates
- **When:** Both requests processed concurrently
- **Then:**
  - One request succeeds, other gets conflict error
  - Database optimistic locking prevents corruption
  - Both CORE and Supervisor maintain referential integrity

**TC-049: Reschedule During Supervisor Modal Edit**
- **Priority:** P2
- **Given:**
  - User A has Supervisor modal open editing event
  - User B reschedules the CORE event
- **When:** User A tries to save Supervisor changes
- **Then:**
  - Stale data error detected
  - Modal shows warning: "Supervisor event has been updated. Please refresh."
  - Changes not saved

**TC-050: Supervisor Event Deleted Externally**
- **Priority:** P2
- **Given:**
  - CORE and Supervisor events both scheduled
  - Supervisor event manually deleted from database
- **When:** User reschedules CORE event
- **Then:**
  - CORE event rescheduled successfully
  - `get_supervisor_event()` returns None
  - Log warning: "Supervisor event not found (may have been deleted)"
  - No error thrown

**TC-051: Multiple CORE Events with Same Number**
- **Priority:** P2
- **Given:**
  - Two CORE events: "606001-CORE-Product A" and "606001-CORE-Product B" (data error)
  - One Supervisor event: "606001-Supervisor-Product"
- **When:** User reschedules first CORE event
- **Then:**
  - `get_supervisor_event()` returns first match
  - Supervisor rescheduled once
  - Log warning: "Multiple CORE events with same number: 606001"

---

### 4.4 Performance & Load Tests

**TC-052: Calendar Page Load (1000 Events)**
- **Priority:** 🔴 P0
- **Test Data:** 1000 events distributed across October 2025
- **Acceptance Criteria:**
  - Page load < 2 seconds (95th percentile)
  - Aggregation query < 500ms
  - No memory leaks

**TC-053: Daily View Load (50 Events in One Day)**
- **Priority:** P1
- **Test Data:** 50 events on Oct 15 (10 CORE, 10 Supervisor, 15 Juicer, 10 Freeosk, 5 Digitals)
- **Acceptance Criteria:**
  - Page load < 1.5 seconds
  - All event cards render
  - Smooth scrolling

**TC-054: Concurrent User Load (100 Users)**
- **Priority:** P1
- **Simulation:** 100 users accessing calendar/daily view simultaneously
- **Acceptance Criteria:**
  - All requests complete < 3 seconds
  - No 500 errors
  - Database connection pool stable

**TC-055: Reschedule Stress Test**
- **Priority:** P1
- **Simulation:** 50 concurrent reschedule requests
- **Acceptance Criteria:**
  - All complete successfully
  - No race conditions
  - Database transactions isolated

---

### 4.5 Accessibility Tests (WCAG AA)

**TC-056: Keyboard-Only Navigation (Full Workflow)**
- **Priority:** 🔴 P0
- **Given:** User using keyboard only (no mouse)
- **When:** User navigates from calendar → daily view → reschedule
- **Then:**
  - Tab key moves through all interactive elements
  - Enter/Space activate buttons
  - ESC closes modals
  - Focus visible at all times (2px blue outline)
  - No keyboard traps (except intentional modal trap)

**TC-057: Screen Reader Full Workflow (NVDA)**
- **Priority:** P0
- **Given:** NVDA screen reader active
- **When:** User navigates calendar and daily view
- **Then:**
  - All content announced logically
  - ARIA labels correct
  - Dynamic content changes announced (aria-live regions)
  - Modal focus trap works with screen reader

**TC-058: Color Contrast Automated Scan**
- **Priority:** P0
- **Tool:** axe DevTools
- **When:** Running scan on calendar and daily view pages
- **Then:**
  - Zero WCAG AA violations
  - All text contrast ≥ 4.5:1
  - All UI components meet contrast requirements

**TC-059: Touch Target Size (Mobile)**
- **Priority:** P0
- **Given:** Mobile viewport (375px)
- **When:** Measuring all interactive elements
- **Then:**
  - All buttons ≥ 44px × 44px
  - Calendar cells ≥ 120px × 120px
  - Links have adequate padding

---

### 4.6 Cross-Browser & Device Tests

**TC-060: Chrome Desktop**
- **Priority:** P0
- **Browsers:** Chrome 120+
- **Acceptance:** All features work, visual appearance matches spec

**TC-061: Firefox Desktop**
- **Priority:** P1
- **Browsers:** Firefox 115+
- **Acceptance:** All features work, minor visual differences acceptable

**TC-062: Safari Desktop**
- **Priority:** P1
- **Browsers:** Safari 17+
- **Acceptance:** All features work, CSS compatibility verified

**TC-063: Mobile Safari (iPhone)**
- **Priority:** P0
- **Devices:** iPhone 12, iPhone SE
- **Acceptance:** Touch targets work, no zoom issues (16px input min)

**TC-064: Mobile Chrome (Android)**
- **Priority:** P1
- **Devices:** Samsung Galaxy S21
- **Acceptance:** Touch interactions work, responsive layout correct

---

## 5. Non-Functional Requirements (NFR) Assessment

### 5.1 Performance NFRs

| NFR | Requirement | Status | Test Coverage |
|-----|-------------|--------|---------------|
| **NFR-01: Calendar Load Time** | < 2 seconds (95th percentile) with 1000 events | ⚠️ **AT RISK** | TC-052 (requires load testing) |
| **NFR-02: Daily View Load Time** | < 1.5 seconds with 50 events | ✅ **LIKELY MET** | TC-053 |
| **NFR-03: Reschedule Response Time** | < 500ms per operation | ✅ **LIKELY MET** | TC-033, TC-041 |
| **NFR-04: Concurrent User Support** | 100 users without degradation | ⚠️ **AT RISK** | TC-054 (requires load testing) |
| **NFR-05: Database Query Optimization** | Single aggregated query, no N+1 | ✅ **MET** | Implementation uses aggregation |

**Risk Assessment:**
- **NFR-01 and NFR-04 are AT RISK** without load testing and caching
- **Recommendation:** Mandatory load testing before production

### 5.2 Security NFRs

| NFR | Requirement | Status | Test Coverage |
|-----|-------------|--------|---------------|
| **NFR-06: Authorization Checks** | Only authorized users can reschedule/unschedule | ⚠️ **UNKNOWN** | Missing authorization tests |
| **NFR-07: SQL Injection Prevention** | All queries parameterized | ✅ **MET** | ORM usage prevents SQL injection |
| **NFR-08: XSS Prevention** | User input sanitized | ✅ **LIKELY MET** | Jinja2 auto-escapes by default |
| **NFR-09: CSRF Protection** | All POST requests have CSRF token | ⚠️ **UNKNOWN** | Missing CSRF tests |

**Risk Assessment:**
- **Missing authorization and CSRF tests** - recommendation: Add before production

### 5.3 Accessibility NFRs

| NFR | Requirement | Status | Test Coverage |
|-----|-------------|--------|---------------|
| **NFR-10: WCAG AA Compliance** | All pages meet WCAG 2.1 Level AA | ✅ **DESIGNED FOR** | TC-058 (automated scan required) |
| **NFR-11: Keyboard Navigation** | 100% keyboard accessible | ✅ **DESIGNED FOR** | TC-056, TC-032 |
| **NFR-12: Screen Reader Support** | All content accessible via screen reader | ✅ **DESIGNED FOR** | TC-057, TC-013 |
| **NFR-13: Color Contrast** | All text ≥ 4.5:1 contrast | ✅ **MET** | Spec includes contrast fixes |

**Risk Assessment:**
- **Accessibility well-designed** - requires validation testing

### 5.4 Usability NFRs

| NFR | Requirement | Status | Test Coverage |
|-----|-------------|--------|---------------|
| **NFR-14: Mobile Usability** | Touch targets ≥ 44px, no pinch-zoom needed | ✅ **DESIGNED FOR** | TC-059 |
| **NFR-15: Responsive Design** | Works on desktop (1920px), tablet (1024px), mobile (375px) | ✅ **DESIGNED FOR** | TC-005, TC-006, TC-007 |
| **NFR-16: Error Recovery** | Clear error messages, retry options | ⚠️ **PARTIAL** | Error states designed but not fully tested |

### 5.5 Reliability NFRs

| NFR | Requirement | Status | Test Coverage |
|-----|-------------|--------|---------------|
| **NFR-17: Data Integrity** | CORE-Supervisor pairing 100% consistent | 🔴 **CRITICAL** | TC-033-051 (extensive coverage) |
| **NFR-18: Transaction Atomicity** | Reschedule/unschedule all-or-nothing | ✅ **DESIGNED FOR** | TC-036, TC-043 |
| **NFR-19: Orphan Detection** | Daily job detects mismatched pairs | ⚠️ **NOT IMPLEMENTED** | Missing orphan detection job |

**Risk Assessment:**
- **NFR-19 is critical** - recommendation: Implement orphan detection before production

---

## 6. Testability Assessment

### 6.1 Controllability (Ability to Set Up Test Conditions)

**Rating: 🟡 MODERATE**

**Strengths:**
- Database fixtures can create any event/schedule combination
- Test data generation straightforward (create CORE, Supervisor, Juicer events)
- API endpoints testable in isolation

**Weaknesses:**
- Complex event pairing logic requires multiple database records
- Simulating transaction failures requires database mocking
- Timezone handling adds complexity

**Improvements Needed:**
```python
# Add test utility functions
def create_core_supervisor_pair(event_number, scheduled=True, same_date=True):
    """Helper to create paired CORE and Supervisor events for testing"""
    core = Event(project_name=f"{event_number}-CORE-Test Product")
    supervisor = Event(project_name=f"{event_number}-Supervisor-Test Product")

    if scheduled:
        core_schedule = Schedule(event=core, employee=test_employee1, start_datetime=test_date)
        if same_date:
            sup_schedule = Schedule(event=supervisor, employee=test_employee2,
                                   start_datetime=test_date.replace(hour=12))
        else:
            sup_schedule = Schedule(event=supervisor, employee=test_employee2,
                                   start_datetime=test_date + timedelta(days=1))

    db.session.add_all([core, supervisor])
    db.session.commit()
    return core, supervisor
```

### 6.2 Observability (Ability to Verify Results)

**Rating: ✅ GOOD**

**Strengths:**
- Database state easily queryable after operations
- Logs capture pairing actions
- HTTP responses indicate success/failure
- UI state verifiable via Selenium/Playwright

**Weaknesses:**
- Missing structured logging for pairing events
- No metrics/monitoring for pairing success rate

**Improvements Needed:**
```python
# Add structured logging
import logging
logger = logging.getLogger(__name__)

def reschedule_event(schedule_id, new_date):
    # ... existing code ...

    if supervisor_event:
        logger.info("supervisor.pairing.reschedule", extra={
            "core_event_id": event.event_id,
            "core_event_number": event_number,
            "supervisor_event_id": supervisor_event.event_id,
            "old_date": old_date.isoformat(),
            "new_date": new_date.isoformat(),
            "success": True
        })
```

### 6.3 Debuggability (Ability to Diagnose Failures)

**Rating: 🟡 MODERATE**

**Strengths:**
- Stack traces available for exceptions
- Database queries logged in debug mode
- Browser DevTools for frontend debugging

**Weaknesses:**
- Regex matching failures are silent (returns None)
- Transaction rollbacks don't preserve error context
- Frontend JavaScript errors not centrally logged

**Improvements Needed:**
```python
def get_supervisor_event(core_event):
    logger.debug(f"Looking for Supervisor event for CORE: {core_event.project_name}")

    match = re.search(r'(\d{6})-CORE-', core_event.project_name, re.IGNORECASE)
    if not match:
        logger.warning(f"Could not extract event number from: {core_event.project_name}")
        return None

    event_number = match.group(1)
    logger.debug(f"Extracted event number: {event_number}")

    supervisor = Event.query.filter(
        Event.project_name.ilike(f'{event_number}-Supervisor-%')
    ).first()

    if supervisor:
        logger.debug(f"Found Supervisor event: {supervisor.event_id}")
    else:
        logger.warning(f"No Supervisor event found with number: {event_number}")

    return supervisor
```

### 6.4 Isolatability (Tests Run Independently)

**Rating: ✅ GOOD**

**Strengths:**
- Database can be reset between tests
- Test transactions can be rolled back
- API stateless (REST)

**Weaknesses:**
- LocalStorage state persists in UI tests
- Cache may affect test isolation

**Improvements Needed:**
```python
# Clear cache between tests
@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()
```

---

## 7. Quality Gate Criteria

### 7.1 Sprint 1 Quality Gate (Calendar View + Pairing Logic)

**Must Pass Before Sprint 1 Demo:**
- [ ] ✅ All P0 calendar view tests pass (TC-001 through TC-010)
- [ ] 🔴 **CRITICAL:** All CORE-Supervisor pairing tests pass (TC-033 through TC-051)
- [ ] ✅ Unit test coverage ≥ 80% overall, 95% for pairing logic
- [ ] ✅ Zero P0 bugs open
- [ ] ✅ Code review approved by Tech Lead

**May Defer to Sprint 2:**
- Performance load testing (TC-052, TC-054) - can test in Sprint 2
- Cross-browser testing (TC-060-064) - Chrome required, others nice-to-have
- Accessibility automated scans (TC-058) - can run in Sprint 2

### 7.2 Sprint 2 Quality Gate (Daily View)

**Must Pass Before Sprint 2 Demo:**
- [ ] ✅ All P0 daily view tests pass (TC-015 through TC-032)
- [ ] ✅ All Supervisor modal tests pass (TC-026 through TC-032)
- [ ] ✅ Accessibility keyboard navigation works (TC-056, TC-032)
- [ ] ✅ Mobile responsive tests pass (TC-007, TC-063)
- [ ] ✅ Zero P0 bugs open

### 7.3 Production Deployment Quality Gate

**Mandatory Before Production:**
- [ ] 🔴 **CRITICAL:** ALL P0 tests pass (100% pass rate)
- [ ] ✅ All P1 tests pass (≥ 95% pass rate)
- [ ] 🔴 **CRITICAL:** Load testing complete with acceptable performance (TC-052, TC-054)
- [ ] ✅ Security review complete (authorization, CSRF protection)
- [ ] ✅ Accessibility scan shows zero WCAG AA violations (TC-058)
- [ ] ✅ Cross-browser testing pass (Chrome, Firefox, Safari, Mobile Safari)
- [ ] ✅ Database backup created
- [ ] ✅ Rollback plan tested
- [ ] 🔴 **CRITICAL:** Orphan detection job deployed and tested
- [ ] ✅ Monitoring alerts configured
- [ ] ✅ UAT sign-off from Product Owner

**Deployment Blockers (Auto-Fail):**
- Any P0 test failure
- CORE-Supervisor pairing data corruption in any test
- Calendar load time > 3 seconds (95th percentile)
- WCAG AA violations
- Missing rollback plan

---

## 8. Recommendations

### 8.1 High Priority Recommendations (Before Development Starts)

**RECOMMENDATION 1: Implement Database Transactions Correctly**
- **Why:** Prevent data corruption during CORE-Supervisor pairing
- **How:** Use `db.session.begin_nested()` for savepoints, catch exceptions, rollback on failure
- **Owner:** Backend Developer
- **Timeline:** Sprint 1, Week 1
- **Success Criteria:** TC-036 and TC-043 pass

**RECOMMENDATION 2: Add Robust Logging for Pairing Operations**
- **Why:** Enable debugging and monitoring of pairing success/failure
- **How:** Structured logging with event IDs, old/new dates, success status
- **Owner:** Backend Developer
- **Timeline:** Sprint 1, Week 1
- **Success Criteria:** Logs viewable in Kibana/Splunk with filtering

**RECOMMENDATION 3: Create Test Utility Functions**
- **Why:** Simplify test data creation for complex scenarios
- **How:** `create_core_supervisor_pair()`, `create_unscheduled_event()`, etc.
- **Owner:** Backend Developer
- **Timeline:** Sprint 1, Week 1
- **Success Criteria:** Tests use utilities, DRY principle followed

**RECOMMENDATION 4: Implement Orphan Detection Job**
- **Why:** Catch pairing failures that slip through testing
- **How:** Daily cron job queries for CORE/Supervisor events on different dates, alerts admins
- **Owner:** Backend Developer
- **Timeline:** Sprint 2, Week 2
- **Success Criteria:** Job runs daily, alerts sent to Slack/Email

**RECOMMENDATION 5: Set Up Performance Monitoring**
- **Why:** Detect performance regressions early
- **How:** NewRelic/DataDog APM, track calendar load time, query execution time
- **Owner:** DevOps
- **Timeline:** Sprint 1, Week 2
- **Success Criteria:** Dashboards visible, alerts configured for > 2s load time

### 8.2 Medium Priority Recommendations (During Development)

**RECOMMENDATION 6: Add Feature Flag for Pairing Logic**
- **Why:** Enable quick rollback if pairing bugs found in production
- **How:** Environment variable `ENABLE_SUPERVISOR_PAIRING=true/false`
- **Owner:** Backend Developer
- **Timeline:** Sprint 1, Week 2
- **Success Criteria:** Pairing can be disabled without code deployment

**RECOMMENDATION 7: Implement Caching for Calendar Queries**
- **Why:** Improve performance, reduce database load
- **How:** Redis cache with 5-minute TTL, invalidate on event changes
- **Owner:** Backend Developer
- **Timeline:** Sprint 1 if time permits, Sprint 2 otherwise
- **Success Criteria:** TC-010 passes with < 500ms subsequent loads

**RECOMMENDATION 8: Create UAT Test Plan Document**
- **Why:** Structure user acceptance testing for Product Owner
- **How:** Test scenarios with step-by-step instructions, expected results
- **Owner:** QA Engineer
- **Timeline:** Sprint 2, Week 1
- **Success Criteria:** Product Owner can execute tests independently

**RECOMMENDATION 9: Set Up Visual Regression Testing**
- **Why:** Catch unintended UI changes
- **How:** Percy.io or Chromatic for screenshot comparisons
- **Owner:** Frontend Developer + QA
- **Timeline:** Sprint 2
- **Success Criteria:** Baseline screenshots captured, CI integration

### 8.3 Low Priority Recommendations (Nice-to-Have)

**RECOMMENDATION 10: Add End-to-End Test Suite**
- **Why:** Validate full user workflows
- **How:** Playwright/Cypress tests for critical paths
- **Owner:** QA Engineer
- **Timeline:** Post-Sprint 2 (continuous improvement)
- **Success Criteria:** 3-5 E2E tests covering happy paths

**RECOMMENDATION 11: Implement A/B Testing for Calendar Design**
- **Why:** Validate UX improvements with real users
- **How:** Feature flag to show old vs new calendar to 50% of users, track metrics
- **Owner:** Product Manager + DevOps
- **Timeline:** Post-production (if needed)
- **Success Criteria:** Metrics show improved user engagement

**RECOMMENDATION 12: Create Pairing Logic Documentation**
- **Why:** Help future developers understand complex logic
- **How:** Markdown doc with diagrams, flowcharts, examples
- **Owner:** Backend Developer
- **Timeline:** Sprint 2, Week 2
- **Success Criteria:** New developer can understand logic in < 30 min

---

## 9. Summary & Final Verdict

### 9.1 Quality Assessment Summary

**Overall Project Health: 🟡 MODERATE RISK**

**Strengths:**
- ✅ Comprehensive UX specification with accessibility built-in
- ✅ Detailed implementation checklist (150+ tasks)
- ✅ Well-designed UI components and responsive breakpoints
- ✅ Thorough test scenario coverage (60+ test cases)
- ✅ Product Manager approval with clear requirements

**Weaknesses:**
- 🔴 **CRITICAL:** CORE-Supervisor pairing introduces data integrity risk
- ⚠️ Performance unknowns (load testing required)
- ⚠️ Missing orphan detection safeguard
- ⚠️ No rollback plan documented
- ⚠️ Security testing gaps (authorization, CSRF)

---

### 9.2 Final Quality Gate Decision

## 🟡 **CONCERNS (Conditional Approval)**

**Verdict:** Approve for development **with mandatory quality gates and risk mitigations**.

### Approval Conditions:

**✅ APPROVE for Sprint 1 Start:**
- Calendar month view redesign
- Daily view page implementation
- **Conditional approval** for CORE-Supervisor pairing logic with:
  - Mandatory: Database transactions with rollback
  - Mandatory: Comprehensive integration tests (TC-033 through TC-051)
  - Mandatory: Structured logging for all pairing operations
  - Mandatory: Code review by Tech Lead before merge

**🔴 BLOCK Production Deployment Until:**
- [ ] ALL P0 tests pass (100% pass rate)
- [ ] Load testing complete (TC-052, TC-054) with < 2s page load
- [ ] Orphan detection job implemented and tested
- [ ] Database backup + rollback plan tested
- [ ] Security review complete (authorization, CSRF)
- [ ] WCAG AA accessibility validation passes
- [ ] UAT sign-off from Product Owner

**⚠️ REQUIRE Before Sprint 2:**
- [ ] Sprint 1 quality gate passed
- [ ] No P0 bugs from Sprint 1
- [ ] Performance benchmarks established

---

### 9.3 Risk Acceptance

**Product Manager Decision Required:**

This project introduces **3 HIGH RISK areas**:
1. CORE-Supervisor pairing data integrity
2. Calendar performance with large datasets
3. Potential orphaned events

**Accept these risks if:**
- ✅ You agree to comprehensive testing (150+ test scenarios)
- ✅ You commit to rollback plan if bugs found in production
- ✅ You accept potential 2-week delay if load testing fails

**Reject/defer this project if:**
- ❌ Data integrity cannot be compromised
- ❌ Performance requirements are hard SLAs
- ❌ Team lacks capacity for comprehensive testing

---

### 9.4 Estimated Testing Effort

**Sprint 1 Testing:**
- Unit tests (Backend): 3 days
- Integration tests (Pairing logic): 3 days
- UI component tests: 2 days
- Code review + fixes: 2 days
- **Total: 10 days (2 weeks)**

**Sprint 2 Testing:**
- Daily view functional tests: 3 days
- Accessibility tests: 2 days
- Cross-browser tests: 2 days
- Performance/load tests: 3 days
- UAT: 3 days
- **Total: 13 days (2.5 weeks)**

**Grand Total: 23 days (4.5 weeks) of QA effort**

---

### 9.5 Go/No-Go Checklist

**Before Starting Sprint 1:**
- [ ] Product Manager accepts risk assessment
- [ ] Tech Lead reviews pairing logic design
- [ ] Database transaction strategy approved
- [ ] Test data generation utilities ready
- [ ] Logging infrastructure set up

**Before Starting Sprint 2:**
- [ ] Sprint 1 quality gate passed
- [ ] All P0 bugs from Sprint 1 fixed
- [ ] Performance baseline established

**Before Production Deployment:**
- [ ] ALL quality gate criteria met (Section 7.3)
- [ ] Zero deployment blockers
- [ ] Rollback plan tested
- [ ] Monitoring/alerts configured
- [ ] Product Owner sign-off

---

## 10. Appendices

### Appendix A: Test Data Requirements

**Minimum Test Data Set:**
- 20 CORE events with matching Supervisor events
- 5 CORE events without Supervisor events (orphans)
- 5 Supervisor events with unscheduled CORE events
- 10 Juicer Production events
- 10 Freeosk events
- 10 Digital events
- 5 events with condition='Unstaffed' on various dates
- Events distributed across October 2025 (1-31)

**Load Testing Data Set:**
- 1000+ events across October 2025
- Realistic distribution: 40% CORE, 20% Juicer, 20% Supervisor, 10% Freeosk, 10% Digitals
- 10% of events unscheduled

### Appendix B: Test Environment Requirements

**Development Environment:**
- Python 3.11+
- Flask with SQLAlchemy
- PostgreSQL or SQLite (with date functions)
- pytest, pytest-cov
- Selenium/Playwright for UI tests

**Staging Environment:**
- Production-like configuration
- Sanitized copy of production data
- Redis cache (if using)
- Load testing tools (Locust, JMeter)

**Test Automation CI/CD:**
- GitHub Actions or Jenkins
- Run unit tests on every commit
- Run integration tests on PR merge
- Run E2E tests nightly

### Appendix C: Bug Severity Definitions

**P0 (Blocker):**
- Data corruption
- System crash
- Security vulnerability
- Complete feature failure

**P1 (Critical):**
- Major feature malfunction
- Poor performance (> 5s load)
- Accessibility WCAG AA violation

**P2 (Major):**
- Minor feature issue
- UI visual bugs
- Usability problem

**P3 (Minor):**
- Cosmetic issues
- Edge case bugs
- Nice-to-have improvements

---

**Document Status:** ✅ Complete
**Approval Required:** Product Manager, Tech Lead
**Next Action:** Review with team, accept risks, start Sprint 1
**QA Reviewer:** Quinn (Test Architect) | 2025-10-12
