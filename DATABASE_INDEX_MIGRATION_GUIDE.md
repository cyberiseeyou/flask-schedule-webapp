# Database Index Migration Guide
**Date:** 2025-10-13
**Sprint:** Sprint 2, Week 1
**Purpose:** Add performance indexes for CORE-Supervisor event pairing

---

## Overview

This migration adds three database indexes to optimize the performance of CORE-Supervisor event pairing queries introduced in Sprint 2 (Calendar Redesign).

**Migration File:** `scheduler_app/migrations/versions/add_indexes_for_core_supervisor_pairing.py`
**Revision ID:** f3d8a1b2c4e5
**Revises:** 0be04acd9951

---

## Indexes Added

### 1. idx_events_project_name
**Table:** `events`
**Column:** `project_name`
**Type:** Non-unique B-tree index
**Purpose:** Optimize LIKE queries for finding paired Supervisor events

**Query Optimized:**
```python
Event.query.filter(Event.project_name.ilike(f'{event_number}-Supervisor-%')).first()
```

**Performance Impact:**
- **Before:** Full table scan (O(n) where n = total events)
- **After:** Index scan with LIKE optimization (O(log n + m) where m = matching rows)
- **Expected Improvement:** 10-100x faster with 1000+ events

---

### 2. idx_events_project_ref_num
**Table:** `events`
**Column:** `project_ref_num`
**Type:** Unique B-tree index
**Purpose:** Optimize event lookups by reference number

**Query Optimized:**
```python
Event.query.filter_by(project_ref_num=schedule.event_ref_num).first()
```

**Performance Impact:**
- **Before:** Full table scan or sequential scan
- **After:** Direct index lookup (O(1) or O(log n))
- **Expected Improvement:** 50-200x faster with 1000+ events

---

### 3. idx_schedule_event_ref_num
**Table:** `schedule`
**Column:** `event_ref_num`
**Type:** Non-unique B-tree index
**Purpose:** Optimize schedule lookups by event reference

**Query Optimized:**
```python
Schedule.query.filter_by(event_ref_num=supervisor_event.project_ref_num).first()
```

**Performance Impact:**
- **Before:** Full table scan
- **After:** Index scan (O(log n))
- **Expected Improvement:** 20-100x faster with 1000+ schedules

---

## Running the Migration

### Development Environment

```bash
# Navigate to project directory
cd C:\Users\mathe\flask-schedule-webapp

# Run migration
flask db upgrade

# Verify indexes created
flask db current
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 0be04acd9951 -> f3d8a1b2c4e5, add_indexes_for_core_supervisor_pairing
```

---

### Production Environment

```bash
# 1. Backup database first!
cp scheduler.db scheduler.db.backup_$(date +%Y%m%d_%H%M%S)

# 2. Run migration (low risk - only adds indexes)
flask db upgrade

# 3. Verify migration
flask db current

# 4. Test application
# - Test reschedule operation with CORE event
# - Test unschedule operation with CORE event
# - Check logs for performance improvements
```

---

## Rollback Procedure

If any issues occur, you can rollback the migration:

```bash
# Rollback to previous version
flask db downgrade 0be04acd9951

# Verify rollback
flask db current
```

**Note:** Rolling back will remove the indexes but will NOT affect any data. The application will continue to work, just with slower performance.

---

## Verification

### 1. Verify Indexes Exist

**SQLite:**
```bash
sqlite3 scheduler.db
```

```sql
-- Check indexes on events table
PRAGMA index_list('events');

-- Check index details
PRAGMA index_info('idx_events_project_name');
PRAGMA index_info('idx_events_project_ref_num');

-- Check indexes on schedule table
PRAGMA index_list('schedule');
PRAGMA index_info('idx_schedule_event_ref_num');
```

**Expected Output:**
```
idx_events_project_name
idx_events_project_ref_num
idx_schedule_event_ref_num
```

---

### 2. Test Query Performance

**Before and After Comparison:**

```python
import time
from scheduler_app.models import Event

# Test LIKE query performance
start = time.time()
supervisor = Event.query.filter(Event.project_name.ilike('606001-Supervisor-%')).first()
duration = time.time() - start

print(f"Query duration: {duration*1000:.2f}ms")
```

**Expected Results:**
- **Without indexes:** 50-500ms with 1000+ events
- **With indexes:** 1-10ms with 1000+ events

---

## Database Size Impact

### Estimated Index Size

| Index | Estimated Size | Formula |
|-------|---------------|---------|
| idx_events_project_name | ~100-500 KB | ~100 bytes/row × num_events |
| idx_events_project_ref_num | ~50-200 KB | ~50 bytes/row × num_events |
| idx_schedule_event_ref_num | ~50-300 KB | ~50 bytes/row × num_schedules |

**Total Estimated Size:** 200 KB - 1 MB (negligible)

**Note:** Actual size depends on number of events and schedules. For typical deployments (1000-5000 events), the total index size will be < 1 MB.

---

## Performance Benchmarks (Estimated)

### Small Dataset (100 events, 50 schedules)
- **Query Improvement:** 5-10x faster
- **Migration Time:** < 1 second
- **User Impact:** Minimal (already fast)

### Medium Dataset (1000 events, 500 schedules)
- **Query Improvement:** 20-50x faster
- **Migration Time:** 1-2 seconds
- **User Impact:** Noticeable improvement in reschedule/unschedule operations

### Large Dataset (5000+ events, 2000+ schedules)
- **Query Improvement:** 50-200x faster
- **Migration Time:** 5-10 seconds
- **User Impact:** Significant improvement (slow queries now fast)

---

## Troubleshooting

### Issue: Migration Fails with "Index Already Exists"

**Cause:** Index was manually created previously

**Solution:**
```bash
# Option 1: Mark migration as complete without running
flask db stamp f3d8a1b2c4e5

# Option 2: Drop existing indexes and re-run migration
sqlite3 scheduler.db "DROP INDEX IF EXISTS idx_events_project_name;"
sqlite3 scheduler.db "DROP INDEX IF EXISTS idx_events_project_ref_num;"
sqlite3 scheduler.db "DROP INDEX IF EXISTS idx_schedule_event_ref_num;"
flask db upgrade
```

---

### Issue: Performance Doesn't Improve

**Possible Causes:**
1. Dataset too small to see improvement (< 100 events)
2. SQLite not using index (check with EXPLAIN QUERY PLAN)
3. Cache masking performance improvements

**Diagnosis:**
```sql
-- Check if index is being used
EXPLAIN QUERY PLAN
SELECT * FROM events WHERE project_name LIKE '606001-Supervisor-%';
```

**Expected Output (with index):**
```
SEARCH TABLE events USING INDEX idx_events_project_name
```

---

### Issue: Application Slowdown After Migration

**Unlikely, but if it occurs:**

**Cause:** Index overhead on INSERT/UPDATE operations (rare with SQLite)

**Solution:**
1. Verify indexes are appropriate for query patterns
2. Check application logs for errors
3. Consider removing idx_events_project_name if LIKE queries are infrequent
4. Rollback migration if necessary

---

## Related Documentation

- **Sprint 2 Progress:** `SPRINT2_PROGRESS_SUMMARY.md`
- **Sprint 2 Review:** `SPRINT2_FINAL_REVIEW.md`
- **Implementation Notes:** `IMPLEMENTATION_NOTES.md`
- **Test Results:** `INTEGRATION_TEST_SUMMARY.md`

---

## FAQs

**Q: Do I need to run this migration immediately?**
A: No, it's optional but recommended. The application will work without indexes, just slower with large datasets (1000+ events).

**Q: Will this migration affect existing data?**
A: No, this migration only adds indexes. No data is modified or deleted.

**Q: Can I run this migration in production without downtime?**
A: Yes, SQLite index creation is fast (< 10 seconds even for large datasets). No downtime required.

**Q: What happens if I skip this migration?**
A: The CORE-Supervisor pairing feature will work correctly but may be slow with large datasets. Reschedule/unschedule operations may take 50-500ms instead of 1-10ms.

**Q: Can I add indexes manually instead of using migration?**
A: Yes, but using the migration is recommended for version control and consistency across environments.

---

**Last Updated:** 2025-10-13
**Author:** Development Team
**Next Review:** After production deployment and performance monitoring
