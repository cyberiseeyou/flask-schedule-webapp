-- Sprint 1 Minimal Test Data
-- Calendar Redesign - Testing CORE-Supervisor Pairing Logic
-- Generated: 2025-10-12

-- =============================================================================
-- IMPORTANT: Run this script against your TEST database only
-- =============================================================================

-- Clear existing test data (optional)
-- DELETE FROM schedule WHERE schedule_id >= 2000;
-- DELETE FROM events WHERE event_id >= 1000;

-- =============================================================================
-- Test Scenario 1: CORE event with matching Supervisor (Happy Path)
-- =============================================================================
-- Used for: TC-033 (Reschedule pairing), TC-041 (Unschedule pairing)

INSERT INTO events (event_id, project_name, event_type, condition, is_scheduled, estimated_hours, start_datetime, due_datetime, created_at)
VALUES
(1001, '606001-CORE-Super Pretzel', 'CORE', 'Scheduled', TRUE, 6.5, '2025-10-15 10:00:00', '2025-10-15', NOW()),
(1002, '606001-Supervisor-Super Pretzel', 'Supervisor', 'Scheduled', TRUE, 0.08, '2025-10-15 12:00:00', '2025-10-15', NOW());

INSERT INTO schedule (schedule_id, event_id, employee_id, start_datetime, created_at)
VALUES
(2001, 1001, 101, '2025-10-15 10:00:00', NOW()),  -- Assuming employee_id 101 = John Smith
(2002, 1002, 102, '2025-10-15 12:00:00', NOW());  -- Assuming employee_id 102 = Jane Doe

-- =============================================================================
-- Test Scenario 2: CORE event WITHOUT Supervisor (Orphan)
-- =============================================================================
-- Used for: TC-034 (Reschedule with no Supervisor), TC-042 (Unschedule with no Supervisor)

INSERT INTO events (event_id, project_name, event_type, condition, is_scheduled, estimated_hours, start_datetime, due_datetime, created_at)
VALUES
(1003, '606999-CORE-Orphan Product', 'CORE', 'Scheduled', TRUE, 5.0, '2025-10-15 11:00:00', '2025-10-15', NOW());

INSERT INTO schedule (schedule_id, event_id, employee_id, start_datetime, created_at)
VALUES
(2003, 1003, 101, '2025-10-15 11:00:00', NOW());

-- =============================================================================
-- Test Scenario 3: Unscheduled CORE and Supervisor pair
-- =============================================================================
-- Used for: TC-045 (Manual scheduling triggers auto-schedule)

INSERT INTO events (event_id, project_name, event_type, condition, is_scheduled, estimated_hours, due_datetime, created_at)
VALUES
(1004, '606002-CORE-Nature Valley', 'CORE', 'Unstaffed', FALSE, 6.0, '2025-10-16', NOW()),
(1005, '606002-Supervisor-Nature Valley', 'Supervisor', 'Unstaffed', FALSE, 0.08, '2025-10-16', NOW());

-- =============================================================================
-- Test Scenario 4: CORE scheduled, Supervisor unscheduled
-- =============================================================================
-- Used for: TC-035 (Reschedule CORE when Supervisor unscheduled)

INSERT INTO events (event_id, project_name, event_type, condition, is_scheduled, estimated_hours, start_datetime, due_datetime, created_at)
VALUES
(1006, '606003-CORE-Cheetos', 'CORE', 'Scheduled', TRUE, 7.0, '2025-10-15 09:00:00', '2025-10-15', NOW()),
(1007, '606003-Supervisor-Cheetos', 'Supervisor', 'Unstaffed', FALSE, 0.08, '2025-10-15', NOW());

INSERT INTO schedule (schedule_id, event_id, employee_id, start_datetime, created_at)
VALUES
(2004, 1006, 101, '2025-10-15 09:00:00', NOW());

-- =============================================================================
-- Test Scenario 5: Edge Case - Lowercase 'core'
-- =============================================================================
-- Used for: TC-040 (Case-insensitive regex matching)

INSERT INTO events (event_id, project_name, event_type, condition, is_scheduled, estimated_hours, start_datetime, due_datetime, created_at)
VALUES
(1008, '606004-core-Lowercase Test', 'CORE', 'Scheduled', TRUE, 5.5, '2025-10-15 14:00:00', '2025-10-15', NOW()),
(1009, '606004-supervisor-Lowercase Test', 'Supervisor', 'Scheduled', TRUE, 0.08, '2025-10-15 12:00:00', '2025-10-15', NOW());

INSERT INTO schedule (schedule_id, event_id, employee_id, start_datetime, created_at)
VALUES
(2005, 1008, 101, '2025-10-15 14:00:00', NOW()),
(2006, 1009, 102, '2025-10-15 12:00:00', NOW());

-- =============================================================================
-- Test Scenario 6: Edge Case - Invalid event number (non-numeric)
-- =============================================================================
-- Used for: TC-039 (Regex fails gracefully)

INSERT INTO events (event_id, project_name, event_type, condition, is_scheduled, estimated_hours, start_datetime, due_datetime, created_at)
VALUES
(1010, 'ABC123-CORE-Invalid Number', 'CORE', 'Scheduled', TRUE, 4.0, '2025-10-15 15:00:00', '2025-10-15', NOW());

INSERT INTO schedule (schedule_id, event_id, employee_id, start_datetime, created_at)
VALUES
(2007, 1010, 101, '2025-10-15 15:00:00', NOW());

-- =============================================================================
-- Test Scenario 7: Multiple event types for calendar display
-- =============================================================================
-- Used for: TC-001 (Display event type counts), TC-002 (Warning icon)

-- Juicer Production events
INSERT INTO events (event_id, project_name, event_type, condition, is_scheduled, estimated_hours, start_datetime, due_datetime, created_at)
VALUES
(1011, 'Juicer Production - Costco #123', 'Juicer Production', 'Scheduled', TRUE, 8.0, '2025-10-15 08:00:00', '2025-10-15', NOW()),
(1012, 'Juicer Production - Target #456', 'Juicer Production', 'Scheduled', TRUE, 7.5, '2025-10-15 09:00:00', '2025-10-15', NOW());

INSERT INTO schedule (schedule_id, event_id, employee_id, start_datetime, created_at)
VALUES
(2008, 1011, 101, '2025-10-15 08:00:00', NOW()),
(2009, 1012, 103, '2025-10-15 09:00:00', NOW());

-- Freeosk events
INSERT INTO events (event_id, project_name, event_type, condition, is_scheduled, estimated_hours, start_datetime, due_datetime, created_at)
VALUES
(1013, 'Freeosk Setup - Walmart #789', 'Freeosk', 'Scheduled', TRUE, 4.0, '2025-10-15 10:00:00', '2025-10-15', NOW());

INSERT INTO schedule (schedule_id, event_id, employee_id, start_datetime, created_at)
VALUES
(2010, 1013, 104, '2025-10-15 10:00:00', NOW());

-- Digital events
INSERT INTO events (event_id, project_name, event_type, condition, is_scheduled, estimated_hours, start_datetime, due_datetime, created_at)
VALUES
(1014, 'Digital Display - BestBuy #111', 'Digitals', 'Scheduled', TRUE, 3.0, '2025-10-15 13:00:00', '2025-10-15', NOW()),
(1015, 'Digital Display - HomeDepot #222', 'Digitals', 'Scheduled', TRUE, 3.5, '2025-10-15 14:00:00', '2025-10-15', NOW()),
(1016, 'Digital Display - Lowes #333', 'Digitals', 'Scheduled', TRUE, 3.0, '2025-10-15 15:00:00', '2025-10-15', NOW());

INSERT INTO schedule (schedule_id, event_id, employee_id, start_datetime, created_at)
VALUES
(2011, 1014, 105, '2025-10-15 13:00:00', NOW()),
(2012, 1015, 105, '2025-10-15 14:00:00', NOW()),
(2013, 1016, 105, '2025-10-15 15:00:00', NOW());

-- =============================================================================
-- Test Scenario 8: Unscheduled events (for warning icon)
-- =============================================================================
-- Used for: TC-002 (Warning icon displayed when unscheduled events exist)

INSERT INTO events (event_id, project_name, event_type, condition, is_scheduled, due_datetime, created_at)
VALUES
(1017, 'Unscheduled CORE Event 1', 'CORE', 'Unstaffed', FALSE, '2025-10-15', NOW()),
(1018, 'Unscheduled Juicer Event 1', 'Juicer Production', 'Unstaffed', FALSE, '2025-10-15', NOW());

-- =============================================================================
-- Test Scenario 9: Events on different days (for calendar navigation)
-- =============================================================================

-- October 16
INSERT INTO events (event_id, project_name, event_type, condition, is_scheduled, estimated_hours, start_datetime, due_datetime, created_at)
VALUES
(1019, '606005-CORE-Doritos', 'CORE', 'Scheduled', TRUE, 6.0, '2025-10-16 10:00:00', '2025-10-16', NOW()),
(1020, '606005-Supervisor-Doritos', 'Supervisor', 'Scheduled', TRUE, 0.08, '2025-10-16 12:00:00', '2025-10-16', NOW());

INSERT INTO schedule (schedule_id, event_id, employee_id, start_datetime, created_at)
VALUES
(2014, 1019, 101, '2025-10-16 10:00:00', NOW()),
(2015, 1020, 102, '2025-10-16 12:00:00', NOW());

-- October 17
INSERT INTO events (event_id, project_name, event_type, condition, is_scheduled, estimated_hours, start_datetime, due_datetime, created_at)
VALUES
(1021, 'Juicer Production - Costco #456', 'Juicer Production', 'Scheduled', TRUE, 8.0, '2025-10-17 08:00:00', '2025-10-17', NOW());

INSERT INTO schedule (schedule_id, event_id, employee_id, start_datetime, created_at)
VALUES
(2016, 1021, 101, '2025-10-17 08:00:00', NOW());

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
-- WHERE event_id >= 1000
-- GROUP BY event_type
-- ORDER BY event_type;

-- Expected:
-- CORE: 9
-- Supervisor: 6
-- Juicer Production: 4
-- Freeosk: 1
-- Digitals: 3

-- 2. Verify CORE-Supervisor pairs
-- SELECT
--     c.event_id as core_id,
--     c.project_name as core_name,
--     s.event_id as supervisor_id,
--     s.project_name as supervisor_name
-- FROM events c
-- LEFT JOIN events s ON SUBSTRING(c.project_name, 1, 6) = SUBSTRING(s.project_name, 1, 6)
--     AND s.project_name LIKE '%-Supervisor-%'
-- WHERE c.project_name LIKE '%-CORE-%'
--   AND c.event_id >= 1000;

-- 3. Verify scheduled vs unscheduled counts
-- SELECT
--     condition,
--     COUNT(*) as count
-- FROM events
-- WHERE event_id >= 1000
-- GROUP BY condition;

-- Expected:
-- Scheduled: ~18-20
-- Unstaffed: ~3-5

-- 4. Verify Oct 15 event counts (for TC-001)
-- SELECT
--     SUM(CASE WHEN project_name LIKE '%-CORE-%' THEN 1 ELSE 0 END) as core_count,
--     SUM(CASE WHEN event_type = 'Juicer Production' THEN 1 ELSE 0 END) as juicer_count,
--     SUM(CASE WHEN project_name LIKE '%-Supervisor-%' THEN 1 ELSE 0 END) as supervisor_count,
--     SUM(CASE WHEN event_type LIKE '%Freeosk%' THEN 1 ELSE 0 END) as freeosk_count,
--     SUM(CASE WHEN event_type LIKE '%Digital%' THEN 1 ELSE 0 END) as digitals_count
-- FROM events
-- WHERE DATE(start_datetime) = '2025-10-15'
--   OR DATE(due_datetime) = '2025-10-15';

-- Expected: C: 6, J: 2, S: 4, F: 1, D: 3

-- =============================================================================
-- Cleanup Script (run after testing)
-- =============================================================================

-- To remove all test data:
-- DELETE FROM schedule WHERE schedule_id >= 2000;
-- DELETE FROM events WHERE event_id >= 1000;

-- Reset sequences (PostgreSQL):
-- SELECT setval('events_event_id_seq', (SELECT MAX(event_id) FROM events));
-- SELECT setval('schedule_schedule_id_seq', (SELECT MAX(schedule_id) FROM schedule));
