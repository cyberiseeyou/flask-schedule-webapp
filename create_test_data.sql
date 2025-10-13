-- Create test data for CORE-Supervisor pairing validation
-- Sprint 2 - Staging Validation
-- Date: 2025-10-13

BEGIN TRANSACTION;

-- Clean up any existing test data first
DELETE FROM schedules WHERE event_ref_num IN (606001, 606002, 606999, 608001, 608002);
DELETE FROM events WHERE project_ref_num IN (606001, 606002, 606999, 608001, 608002);

-- ============================================================================
-- Test Scenario 1: CORE with Scheduled Supervisor (Happy Path)
-- ============================================================================

-- CORE Event (606001)
INSERT INTO events (
    project_name,
    project_ref_num,
    location_mvid,
    store_number,
    store_name,
    start_datetime,
    due_datetime,
    estimated_time,
    is_scheduled,
    event_type,
    external_id,
    sync_status
) VALUES (
    '606001-CORE-Super Pretzel King Size',
    606001,
    'LOC_001',
    1234,
    'Test Store 1',
    '2025-10-20 10:00:00',
    '2025-10-20 16:30:00',
    390,
    1,
    'Core',
    'CM_EV_606001',
    'synced'
);

-- Supervisor Event (606002)
INSERT INTO events (
    project_name,
    project_ref_num,
    location_mvid,
    store_number,
    store_name,
    start_datetime,
    due_datetime,
    estimated_time,
    is_scheduled,
    event_type,
    external_id,
    sync_status
) VALUES (
    '606001-Supervisor-Super Pretzel King Size',
    606002,
    'LOC_001',
    1234,
    'Test Store 1',
    '2025-10-20 12:00:00',
    '2025-10-20 14:00:00',
    120,
    1,
    'Supervisor',
    'CM_EV_606002',
    'synced'
);

-- Schedules for CORE and Supervisor
INSERT INTO schedules (event_ref_num, employee_id, schedule_datetime, external_id)
SELECT 606001, id, '2025-10-20 10:00:00', 'CM_SCH_606001'
FROM employees
LIMIT 1;

INSERT INTO schedules (event_ref_num, employee_id, schedule_datetime, external_id)
SELECT 606002, id, '2025-10-20 12:00:00', 'CM_SCH_606002'
FROM employees
LIMIT 1;

-- ============================================================================
-- Test Scenario 2: Orphan CORE (No Supervisor)
-- ============================================================================

-- CORE Event (606999) - No paired Supervisor
INSERT INTO events (
    project_name,
    project_ref_num,
    location_mvid,
    store_number,
    store_name,
    start_datetime,
    due_datetime,
    estimated_time,
    is_scheduled,
    event_type,
    external_id,
    sync_status
) VALUES (
    '606999-CORE-Test Product Orphan',
    606999,
    'LOC_002',
    5678,
    'Test Store 2',
    '2025-10-21 11:00:00',
    '2025-10-21 17:30:00',
    390,
    1,
    'Core',
    'CM_EV_606999',
    'synced'
);

-- Schedule for orphan CORE
INSERT INTO schedules (event_ref_num, employee_id, schedule_datetime, external_id)
SELECT 606999, id, '2025-10-21 11:00:00', 'CM_SCH_606999'
FROM employees
LIMIT 1;

-- ============================================================================
-- Test Scenario 3: CORE Scheduled, Supervisor Unscheduled
-- ============================================================================

-- CORE Event (608001)
INSERT INTO events (
    project_name,
    project_ref_num,
    location_mvid,
    store_number,
    store_name,
    start_datetime,
    due_datetime,
    estimated_time,
    is_scheduled,
    event_type,
    external_id,
    sync_status
) VALUES (
    '608001-CORE-Product With Unscheduled Supervisor',
    608001,
    'LOC_003',
    9012,
    'Test Store 3',
    '2025-10-22 09:00:00',
    '2025-10-22 15:30:00',
    390,
    1,
    'Core',
    'CM_EV_608001',
    'synced'
);

-- Supervisor Event (608002) - Exists but NOT scheduled
INSERT INTO events (
    project_name,
    project_ref_num,
    location_mvid,
    store_number,
    store_name,
    start_datetime,
    due_datetime,
    estimated_time,
    is_scheduled,
    event_type,
    sync_status
) VALUES (
    '608001-Supervisor-Product With Unscheduled Supervisor',
    608002,
    'LOC_003',
    9012,
    'Test Store 3',
    '2025-10-22 00:00:00',
    '2025-10-22 02:00:00',
    120,
    0,
    'Supervisor',
    'pending'
);

-- Schedule ONLY for CORE, not Supervisor
INSERT INTO schedules (event_ref_num, employee_id, schedule_datetime, external_id)
SELECT 608001, id, '2025-10-22 09:00:00', 'CM_SCH_608001'
FROM employees
LIMIT 1;

COMMIT;

-- ============================================================================
-- Verification Queries
-- ============================================================================

.print
.print "Test Data Created Successfully!"
.print "================================================================================"
.print

-- Verify CORE events
.print "CORE Events:"
.print "------------"
SELECT project_ref_num, project_name, is_scheduled, sync_status
FROM events
WHERE project_name LIKE '%-CORE-%'
ORDER BY project_ref_num;

.print
.print "Supervisor Events:"
.print "------------------"
SELECT project_ref_num, project_name, is_scheduled, sync_status
FROM events
WHERE project_name LIKE '%-Supervisor-%'
ORDER BY project_ref_num;

.print
.print "Schedules:"
.print "----------"
SELECT s.id, s.event_ref_num, s.schedule_datetime, e.project_name
FROM schedules s
JOIN events e ON s.event_ref_num = e.project_ref_num
WHERE e.project_ref_num IN (606001, 606002, 606999, 608001, 608002)
ORDER BY s.schedule_datetime;

.print
.print "================================================================================"
.print "Test Scenarios Ready:"
.print "================================================================================"
.print "1. CORE (606001) + Supervisor (606002) - Both scheduled"
.print "   Use for: Reschedule together, Unschedule together"
.print
.print "2. CORE (606999) - Orphan (no Supervisor)"
.print "   Use for: Reschedule orphan, Unschedule orphan"
.print
.print "3. CORE (608001) + Supervisor (608002) - Only CORE scheduled"
.print "   Use for: Reschedule with unscheduled Supervisor"
.print "================================================================================"
