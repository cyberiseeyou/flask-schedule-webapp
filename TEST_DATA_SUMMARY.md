# Test Data Summary - CORE-Supervisor Pairing

**File:** test_data/sprint1_adapted_testdata.sql
**Generated:** 2025-10-12
**Total Events:** 21
**Total Schedules:** 16

---

## CORE-Supervisor Pairing Examples

### Understanding the Pairing Model

**Key Concept:** project_ref_num ≠ event_number

| Field | Description | CORE Example | Supervisor Example |
|-------|-------------|--------------|-------------------|
| **project_ref_num** | Database reference (UNIQUE per event) | 606001 | 606002 |
| **Event Number** | Business identifier (extracted from project_name) | 606001 | 606001 |
| **project_name** | Human-readable name with event number | 606001-CORE-Super Pretzel | 606001-Supervisor-Super Pretzel |

**Pairing Rule:** Events with the SAME event number (first 6 digits of project_name) are paired.

---

## Test Scenarios

### Scenario 1: Happy Path - CORE with Scheduled Supervisor

**Use Case:** TC-033 (Reschedule both), TC-041 (Unschedule both)

| Event | project_ref_num | project_name | Event # | Condition | Scheduled Time |
|-------|----------------|--------------|---------|-----------|----------------|
| CORE | 606001 | 606001-CORE-Super Pretzel | **606001** | Scheduled | 2025-10-15 10:00 |
| Supervisor | 606002 | 606001-Supervisor-Super Pretzel | **606001** | Scheduled | 2025-10-15 12:00 |

**Schedule Records:**
- Schedule 2001: Links to event_ref_num=606001 (CORE), employee_id=101
- Schedule 2002: Links to event_ref_num=606002 (Supervisor), employee_id=102

**Expected Behavior:**
- Reschedule CORE → Both CORE and Supervisor reschedule to new date
- Unschedule CORE → Both CORE and Supervisor unscheduled

---

### Scenario 2: Orphan CORE (No Supervisor)

**Use Case:** TC-034 (Reschedule only CORE), TC-042 (Unschedule only CORE)

| Event | project_ref_num | project_name | Event # | Condition | Scheduled Time |
|-------|----------------|--------------|---------|-----------|----------------|
| CORE | 606999 | 606999-CORE-Orphan Product | **606999** | Scheduled | 2025-10-15 11:00 |

**Schedule Records:**
- Schedule 2003: Links to event_ref_num=606999, employee_id=101

**Expected Behavior:**
- Reschedule CORE → Only CORE reschedules (no Supervisor exists)
- Unschedule CORE → Only CORE unscheduled

---

### Scenario 3: Unscheduled CORE and Supervisor Pair

**Use Case:** TC-045 (Manual scheduling should trigger auto-schedule)

| Event | project_ref_num | project_name | Event # | Condition | Scheduled Time |
|-------|----------------|--------------|---------|-----------|----------------|
| CORE | 607001 | 606002-CORE-Nature Valley | **606002** | Unstaffed | None |
| Supervisor | 607002 | 606002-Supervisor-Nature Valley | **606002** | Unstaffed | None |

**Schedule Records:** None (both unscheduled)

**Expected Behavior:**
- Schedule CORE manually → Supervisor should auto-schedule 2 hours later

---

### Scenario 4: CORE Scheduled, Supervisor Unscheduled

**Use Case:** TC-035 (Reschedule CORE when Supervisor unscheduled)

| Event | project_ref_num | project_name | Event # | Condition | Scheduled Time |
|-------|----------------|--------------|---------|-----------|----------------|
| CORE | 608001 | 606003-CORE-Cheetos | **606003** | Scheduled | 2025-10-15 09:00 |
| Supervisor | 608002 | 606003-Supervisor-Cheetos | **606003** | Unstaffed | None |

**Schedule Records:**
- Schedule 2004: Links to event_ref_num=608001 (CORE), employee_id=101

**Expected Behavior:**
- Reschedule CORE → Only CORE reschedules (Supervisor not scheduled)

---

### Scenario 5: Edge Case - Lowercase "core"

**Use Case:** TC-040 (Case-insensitive regex matching)

| Event | project_ref_num | project_name | Event # | Condition | Scheduled Time |
|-------|----------------|--------------|---------|-----------|----------------|
| CORE | 609001 | 606004-core-Lowercase Test | **606004** | Scheduled | 2025-10-15 14:00 |
| Supervisor | 609002 | 606004-supervisor-Lowercase Test | **606004** | Scheduled | 2025-10-15 16:00 |

**Schedule Records:**
- Schedule 2005: Links to event_ref_num=609001, employee_id=101
- Schedule 2006: Links to event_ref_num=609002, employee_id=102

**Expected Behavior:**
- Regex should match case-insensitively
- Pairing logic should work with lowercase "core" and "supervisor"

---

### Scenario 6: Edge Case - Invalid Event Number

**Use Case:** TC-039 (Regex fails gracefully)

| Event | project_ref_num | project_name | Event # | Condition | Scheduled Time |
|-------|----------------|--------------|---------|-----------|----------------|
| CORE | 610001 | ABC123-CORE-Invalid Number | None (invalid) | Scheduled | 2025-10-15 15:00 |

**Schedule Records:**
- Schedule 2007: Links to event_ref_num=610001, employee_id=101

**Expected Behavior:**
- Regex extraction fails (no 6-digit number)
- `get_supervisor_event()` returns None
- Reschedule only the CORE event (no Supervisor search)

---

### Scenario 7-9: Other Event Types (Not CORE/Supervisor)

**Use Case:** TC-001 (Calendar display), TC-002 (Warning icons)

| Event Type | Count | Examples |
|------------|-------|----------|
| Juicer | 4 | Juicer Production - Costco #123 |
| Freeosk | 1 | Freeosk Setup - Walmart #789 |
| Digitals | 3 | Digital Display - BestBuy #111 |

**Purpose:** Test calendar display with multiple event types

---

## SQL Verification Queries

### 1. Find CORE-Supervisor Pairs

```sql
SELECT
    c.project_ref_num AS core_ref,
    c.project_name AS core_name,
    s.project_ref_num AS supervisor_ref,
    s.project_name AS supervisor_name,
    SUBSTR(c.project_name, 1, 6) AS shared_event_number
FROM events c
LEFT JOIN events s ON SUBSTR(c.project_name, 1, 6) = SUBSTR(s.project_name, 1, 6)
    AND s.project_name LIKE '%-Supervisor-%'
WHERE c.project_name LIKE '%-CORE-%'
  AND c.id >= 1000;
```

**Expected Results:**

| core_ref | core_name | supervisor_ref | supervisor_name | shared_event_number |
|----------|-----------|----------------|-----------------|---------------------|
| 606001 | 606001-CORE-Super Pretzel | 606002 | 606001-Supervisor-Super Pretzel | 606001 |
| 606999 | 606999-CORE-Orphan Product | NULL | NULL | 606999 |
| 607001 | 606002-CORE-Nature Valley | 607002 | 606002-Supervisor-Nature Valley | 606002 |
| 608001 | 606003-CORE-Cheetos | 608002 | 606003-Supervisor-Cheetos | 606003 |
| 609001 | 606004-core-Lowercase Test | 609002 | 606004-supervisor-Lowercase Test | 606004 |
| 610001 | ABC123-CORE-Invalid Number | NULL | NULL | ABC123 |
| 615001 | 606005-CORE-Doritos | 615002 | 606005-Supervisor-Doritos | 606005 |

---

### 2. Find Orphaned Pairs (Different Dates)

```sql
SELECT
    c.project_ref_num AS core_ref,
    c.project_name AS core_name,
    DATE(c.start_datetime) AS core_date,
    s.project_ref_num AS supervisor_ref,
    s.project_name AS supervisor_name,
    DATE(s.start_datetime) AS supervisor_date
FROM events c
INNER JOIN events s ON SUBSTR(c.project_name, 1, 6) = SUBSTR(s.project_name, 1, 6)
WHERE c.project_name LIKE '%-CORE-%'
  AND s.project_name LIKE '%-Supervisor-%'
  AND c.condition = 'Scheduled'
  AND s.condition = 'Scheduled'
  AND DATE(c.start_datetime) != DATE(s.start_datetime)
  AND c.id >= 1000;
```

**Expected Results:** 0 rows (no orphans in initial test data)

---

### 3. Count Events by Type

```sql
SELECT event_type, COUNT(*) as count
FROM events
WHERE id >= 1000
GROUP BY event_type
ORDER BY event_type;
```

**Expected Results:**

| event_type | count |
|------------|-------|
| Core | 9 |
| Supervisor | 6 |
| Juicer | 4 |
| Freeosk | 1 |
| Digitals | 3 |

---

## Helper Function Test Matrix

| Function | Input | Expected Output | Test Scenario |
|----------|-------|----------------|---------------|
| `is_core_event_redesign()` | Event 606001 | True | Scenario 1 |
| `get_supervisor_event()` | Event 606001 | Event 606002 | Scenario 1 |
| `get_supervisor_status()` | Event 606001 | `{'exists': True, 'is_scheduled': True}` | Scenario 1 |
| `get_supervisor_event()` | Event 606999 | None | Scenario 2 (orphan) |
| `get_supervisor_event()` | Event 609001 | Event 609002 | Scenario 5 (lowercase) |
| `get_supervisor_event()` | Event 610001 | None | Scenario 6 (invalid) |

---

## Expected Test Outcomes

### TC-033: Reschedule CORE with Scheduled Supervisor

**Input:** Reschedule event_ref_num=606001 (CORE) to 2025-10-20

**Expected:**
1. CORE (606001) rescheduled to 2025-10-20 10:00
2. Supervisor (606002) rescheduled to 2025-10-20 12:00 (2 hours later)
3. 2 API calls logged (CORE + Supervisor)
4. Both sync_status updated to 'synced'

### TC-034: Reschedule Orphan CORE

**Input:** Reschedule event_ref_num=606999 (orphan CORE) to 2025-10-22

**Expected:**
1. CORE (606999) rescheduled to 2025-10-22 11:00
2. No Supervisor rescheduled (doesn't exist)
3. 1 API call logged (CORE only)

### TC-036: Transaction Rollback on API Failure

**Input:** Reschedule event_ref_num=606001, but Supervisor API call fails

**Expected:**
1. Transaction rolls back
2. CORE (606001) remains at original datetime (2025-10-15 10:00)
3. Supervisor (606002) remains at original datetime (2025-10-15 12:00)
4. No database changes persisted

---

**Last Updated:** 2025-10-12
**Status:** Test data ready for integration testing
