-- Sprint 1 Adapted Test Data
-- Calendar Redesign - Testing CORE-Supervisor Pairing Logic
-- ADAPTED FOR ACTUAL SCHEMA (uses project_ref_num, estimated_time in minutes)
-- Generated: 2025-10-12

-- =============================================================================
-- IMPORTANT: Run this script against your TEST database only
-- =============================================================================

-- Clear existing test data (optional)
-- DELETE FROM schedule WHERE id >= 2000;
-- DELETE FROM events WHERE id >= 1000;

-- =============================================================================
-- Test Scenario 1: CORE event with matching Supervisor (Happy Path)
-- =============================================================================
-- Used for: TC-033 (Reschedule pairing), TC-041 (Unschedule pairing)

INSERT INTO events (
    id,
    project_ref_num,
    project_name,
    event_type,
    condition,
    is_scheduled,
    estimated_time,
    start_datetime,
    due_datetime,
    external_id,
    sync_status
) VALUES
(1001, 606001, '606001-CORE-Super Pretzel', 'Core', 'Scheduled', 1, 390, '2025-10-15 10:00:00', '2025-10-15', 'CM_606001', 'synced'),
(1002, 606002, '606001-Supervisor-Super Pretzel', 'Supervisor', 'Scheduled', 1, 5, '2025-10-15 12:00:00', '2025-10-15', 'CM_606002', 'synced');

INSERT INTO schedule (
    id,
    event_ref_num,
    employee_id,
    schedule_datetime,
    external_id
) VALUES
(2001, 606001, 101, '2025-10-15 10:00:00', 'CM_SCH_2001'),  -- Assuming employee_id 101 = John Smith
(2002, 606002, 102, '2025-10-15 12:00:00', 'CM_SCH_2002');  -- Assuming employee_id 102 = Jane Doe

-- =============================================================================
-- Test Scenario 2: CORE event WITHOUT Supervisor (Orphan)
-- =============================================================================
-- Used for: TC-034 (Reschedule with no Supervisor), TC-042 (Unschedule with no Supervisor)

INSERT INTO events (
    id,
    project_ref_num,
    project_name,
    event_type,
    condition,
    is_scheduled,
    estimated_time,
    start_datetime,
    due_datetime,
    external_id,
    sync_status
) VALUES
(1003, 606999, '606999-CORE-Orphan Product', 'Core', 'Scheduled', 1, 300, '2025-10-15 11:00:00', '2025-10-15', 'CM_606999', 'synced');

INSERT INTO schedule (
    id,
    event_ref_num,
    employee_id,
    schedule_datetime,
    external_id
) VALUES
(2003, 606999, 101, '2025-10-15 11:00:00', 'CM_SCH_2003');

-- =============================================================================
-- Test Scenario 3: Unscheduled CORE and Supervisor pair
-- =============================================================================
-- Used for: TC-045 (Manual scheduling triggers auto-schedule)

INSERT INTO events (
    id,
    project_ref_num,
    project_name,
    event_type,
    condition,
    is_scheduled,
    estimated_time,
    due_datetime,
    sync_status
) VALUES
(1004, 607001, '606002-CORE-Nature Valley', 'Core', 'Unstaffed', 0, 360, '2025-10-16', 'pending'),
(1005, 607002, '606002-Supervisor-Nature Valley', 'Supervisor', 'Unstaffed', 0, 5, '2025-10-16', 'pending');

-- =============================================================================
-- Test Scenario 4: CORE scheduled, Supervisor unscheduled
-- =============================================================================
-- Used for: TC-035 (Reschedule CORE when Supervisor unscheduled)

INSERT INTO events (
    id,
    project_ref_num,
    project_name,
    event_type,
    condition,
    is_scheduled,
    estimated_time,
    start_datetime,
    due_datetime,
    external_id,
    sync_status
) VALUES
(1006, 608001, '606003-CORE-Cheetos', 'Core', 'Scheduled', 1, 420, '2025-10-15 09:00:00', '2025-10-15', 'CM_608001', 'synced'),
(1007, 608002, '606003-Supervisor-Cheetos', 'Supervisor', 'Unstaffed', 0, 5, '2025-10-15', NULL, 'pending');

INSERT INTO schedule (
    id,
    event_ref_num,
    employee_id,
    schedule_datetime,
    external_id
) VALUES
(2004, 608001, 101, '2025-10-15 09:00:00', 'CM_SCH_2004');

-- =============================================================================
-- Test Scenario 5: Edge Case - Lowercase 'core'
-- =============================================================================
-- Used for: TC-040 (Case-insensitive regex matching)

INSERT INTO events (
    id,
    project_ref_num,
    project_name,
    event_type,
    condition,
    is_scheduled,
    estimated_time,
    start_datetime,
    due_datetime,
    external_id,
    sync_status
) VALUES
(1008, 609001, '606004-core-Lowercase Test', 'Core', 'Scheduled', 1, 330, '2025-10-15 14:00:00', '2025-10-15', 'CM_609001', 'synced'),
(1009, 609002, '606004-supervisor-Lowercase Test', 'Supervisor', 'Scheduled', 1, 5, '2025-10-15 16:00:00', '2025-10-15', 'CM_609002', 'synced');

INSERT INTO schedule (
    id,
    event_ref_num,
    employee_id,
    schedule_datetime,
    external_id
) VALUES
(2005, 609001, 101, '2025-10-15 14:00:00', 'CM_SCH_2005'),
(2006, 609002, 102, '2025-10-15 16:00:00', 'CM_SCH_2006');

-- =============================================================================
-- Test Scenario 6: Edge Case - Invalid event number (non-numeric)
-- =============================================================================
-- Used for: TC-039 (Regex fails gracefully)

INSERT INTO events (
    id,
    project_ref_num,
    project_name,
    event_type,
    condition,
    is_scheduled,
    estimated_time,
    start_datetime,
    due_datetime,
    external_id,
    sync_status
) VALUES
(1010, 610001, 'ABC123-CORE-Invalid Number', 'Core', 'Scheduled', 1, 240, '2025-10-15 15:00:00', '2025-10-15', 'CM_610001', 'synced');

INSERT INTO schedule (
    id,
    event_ref_num,
    employee_id,
    schedule_datetime,
    external_id
) VALUES
(2007, 610001, 101, '2025-10-15 15:00:00', 'CM_SCH_2007');

-- =============================================================================
-- Test Scenario 7: Multiple event types for calendar display
-- =============================================================================
-- Used for: TC-001 (Display event type counts), TC-002 (Warning icon)

-- Juicer Production events
INSERT INTO events (
    id,
    project_ref_num,
    project_name,
    event_type,
    condition,
    is_scheduled,
    estimated_time,
    start_datetime,
    due_datetime,
    external_id,
    sync_status
) VALUES
(1011, 611001, 'Juicer Production - Costco #123', 'Juicer', 'Scheduled', 1, 480, '2025-10-15 08:00:00', '2025-10-15', 'CM_611001', 'synced'),
(1012, 611002, 'Juicer Production - Target #456', 'Juicer', 'Scheduled', 1, 450, '2025-10-15 09:00:00', '2025-10-15', 'CM_611002', 'synced');

INSERT INTO schedule (
    id,
    event_ref_num,
    employee_id,
    schedule_datetime,
    external_id
) VALUES
(2008, 611001, 101, '2025-10-15 08:00:00', 'CM_SCH_2008'),
(2009, 611002, 103, '2025-10-15 09:00:00', 'CM_SCH_2009');

-- Freeosk events
INSERT INTO events (
    id,
    project_ref_num,
    project_name,
    event_type,
    condition,
    is_scheduled,
    estimated_time,
    start_datetime,
    due_datetime,
    external_id,
    sync_status
) VALUES
(1013, 612001, 'Freeosk Setup - Walmart #789', 'Freeosk', 'Scheduled', 1, 240, '2025-10-15 10:00:00', '2025-10-15', 'CM_612001', 'synced');

INSERT INTO schedule (
    id,
    event_ref_num,
    employee_id,
    schedule_datetime,
    external_id
) VALUES
(2010, 612001, 104, '2025-10-15 10:00:00', 'CM_SCH_2010');

-- Digital events
INSERT INTO events (
    id,
    project_ref_num,
    project_name,
    event_type,
    condition,
    is_scheduled,
    estimated_time,
    start_datetime,
    due_datetime,
    external_id,
    sync_status
) VALUES
(1014, 613001, 'Digital Display - BestBuy #111', 'Digitals', 'Scheduled', 1, 180, '2025-10-15 13:00:00', '2025-10-15', 'CM_613001', 'synced'),
(1015, 613002, 'Digital Display - HomeDepot #222', 'Digitals', 'Scheduled', 1, 210, '2025-10-15 14:00:00', '2025-10-15', 'CM_613002', 'synced'),
(1016, 613003, 'Digital Display - Lowes #333', 'Digitals', 'Scheduled', 1, 180, '2025-10-15 15:00:00', '2025-10-15', 'CM_613003', 'synced');

INSERT INTO schedule (
    id,
    event_ref_num,
    employee_id,
    schedule_datetime,
    external_id
) VALUES
(2011, 613001, 105, '2025-10-15 13:00:00', 'CM_SCH_2011'),
(2012, 613002, 105, '2025-10-15 14:00:00', 'CM_SCH_2012'),
(2013, 613003, 105, '2025-10-15 15:00:00', 'CM_SCH_2013');

-- =============================================================================
-- Test Scenario 8: Unscheduled events (for warning icon)
-- =============================================================================
-- Used for: TC-002 (Warning icon displayed when unscheduled events exist)

INSERT INTO events (
    id,
    project_ref_num,
    project_name,
    event_type,
    condition,
    is_scheduled,
    due_datetime,
    sync_status
) VALUES
(1017, 614001, 'Unscheduled CORE Event 1', 'Core', 'Unstaffed', 0, '2025-10-15', 'pending'),
(1018, 614002, 'Unscheduled Juicer Event 1', 'Juicer', 'Unstaffed', 0, '2025-10-15', 'pending');

-- =============================================================================
-- Test Scenario 9: Events on different days (for calendar navigation)
-- =============================================================================

-- October 16
INSERT INTO events (
    id,
    project_ref_num,
    project_name,
    event_type,
    condition,
    is_scheduled,
    estimated_time,
    start_datetime,
    due_datetime,
    external_id,
    sync_status
) VALUES
(1019, 615001, '606005-CORE-Doritos', 'Core', 'Scheduled', 1, 360, '2025-10-16 10:00:00', '2025-10-16', 'CM_615001', 'synced'),
(1020, 615002, '606005-Supervisor-Doritos', 'Supervisor', 'Scheduled', 1, 5, '2025-10-16 12:00:00', '2025-10-16', 'CM_615002', 'synced');

INSERT INTO schedule (
    id,
    event_ref_num,
    employee_id,
    schedule_datetime,
    external_id
) VALUES
(2014, 615001, 101, '2025-10-16 10:00:00', 'CM_SCH_2014'),
(2015, 615002, 102, '2025-10-16 12:00:00', 'CM_SCH_2015');

-- October 17
INSERT INTO events (
    id,
    project_ref_num,
    project_name,
    event_type,
    condition,
    is_scheduled,
    estimated_time,
    start_datetime,
    due_datetime,
    external_id,
    sync_status
) VALUES
(1021, 616001, 'Juicer Production - Costco #456', 'Juicer', 'Scheduled', 1, 480, '2025-10-17 08:00:00', '2025-10-17', 'CM_616001', 'synced');

INSERT INTO schedule (
    id,
    event_ref_num,
    employee_id,
    schedule_datetime,
    external_id
) VALUES
(2016, 616001, 101, '2025-10-17 08:00:00', 'CM_SCH_2016');

-- =============================================================================
-- Test Scenario 10: Empty day (for empty state testing)
-- =============================================================================
-- October 18 - intentionally left empty (no events)

-- =============================================================================
-- Verification Queries
-- =============================================================================

-- Run these queries to verify test data loaded correctly:

-- 1. Count events by type
-- SELECT event_type, COUNT(*) as count
-- FROM events
-- WHERE id >= 1000
-- GROUP BY event_type
-- ORDER BY event_type;

-- Expected:
-- Core: 9
-- Supervisor: 6
-- Juicer: 4
-- Freeosk: 1
-- Digitals: 3

-- 2. Verify CORE-Supervisor pairs (using actual schema)
-- SELECT
--     c.id as core_id,
--     c.project_name as core_name,
--     s.id as supervisor_id,
--     s.project_name as supervisor_name
-- FROM events c
-- LEFT JOIN events s ON SUBSTR(c.project_name, 1, 6) = SUBSTR(s.project_name, 1, 6)
--     AND s.project_name LIKE '%-Supervisor-%'
-- WHERE c.project_name LIKE '%-CORE-%'
--   AND c.id >= 1000;

-- 3. Verify scheduled vs unscheduled counts
-- SELECT
--     condition,
--     COUNT(*) as count
-- FROM events
-- WHERE id >= 1000
-- GROUP BY condition;

-- Expected:
-- Scheduled: ~18-20
-- Unstaffed: ~3-5

-- 4. Verify Oct 15 event counts (for TC-001)
-- SELECT
--     SUM(CASE WHEN project_name LIKE '%-CORE-%' THEN 1 ELSE 0 END) as core_count,
--     SUM(CASE WHEN event_type = 'Juicer' THEN 1 ELSE 0 END) as juicer_count,
--     SUM(CASE WHEN project_name LIKE '%-Supervisor-%' THEN 1 ELSE 0 END) as supervisor_count,
--     SUM(CASE WHEN event_type LIKE '%Freeosk%' THEN 1 ELSE 0 END) as freeosk_count,
--     SUM(CASE WHEN event_type LIKE '%Digital%' THEN 1 ELSE 0 END) as digitals_count
-- FROM events
-- WHERE DATE(start_datetime) = '2025-10-15'
--    OR DATE(due_datetime) = '2025-10-15';

-- Expected: C: 6, J: 2, S: 4, F: 1, D: 3

-- 5. Test helper function queries (using actual schema)
-- -- Find Supervisor for CORE event 606001
-- SELECT * FROM events
-- WHERE project_name LIKE '606001-Supervisor-%'
-- LIMIT 1;

-- -- Count orphaned pairs (CORE and Supervisor on different dates)
-- SELECT
--     c.id AS core_id,
--     c.project_name AS core_name,
--     DATE(c.start_datetime) AS core_date,
--     s.id AS supervisor_id,
--     s.project_name AS supervisor_name,
--     DATE(s.start_datetime) AS supervisor_date
-- FROM events c
-- INNER JOIN events s ON SUBSTR(c.project_name, 1, 6) = SUBSTR(s.project_name, 1, 6)
-- WHERE c.project_name LIKE '%-CORE-%'
--   AND s.project_name LIKE '%-Supervisor-%'
--   AND c.condition = 'Scheduled'
--   AND s.condition = 'Scheduled'
--   AND DATE(c.start_datetime) != DATE(s.start_datetime)
--   AND c.id >= 1000;

-- Expected: 0 rows (no orphans in initial test data)

-- =============================================================================
-- Cleanup Script (run after testing)
-- =============================================================================

-- To remove all test data:
-- DELETE FROM schedule WHERE id >= 2000;
-- DELETE FROM events WHERE id >= 1000;

-- Reset auto-increment (SQLite):
-- DELETE FROM sqlite_sequence WHERE name IN ('events', 'schedule');

-- Reset auto-increment (MySQL):
-- ALTER TABLE events AUTO_INCREMENT = 1;
-- ALTER TABLE schedule AUTO_INCREMENT = 1;

-- Reset sequences (PostgreSQL):
-- SELECT setval('events_id_seq', (SELECT COALESCE(MAX(id), 1) FROM events));
-- SELECT setval('schedule_id_seq', (SELECT COALESCE(MAX(id), 1) FROM schedule));
