# Staging Deployment Checklist
**Date:** 2025-10-13
**Sprint:** Sprint 2, Week 1
**Purpose:** Test CORE-Supervisor pairing with real Crossmark API

---

## Overview

This checklist guides you through deploying and testing Sprint 2 changes (CORE-Supervisor event pairing) in a staging environment with the real Crossmark API.

**Key Features to Test:**
- Automatic CORE-Supervisor pairing in reschedule endpoint
- Automatic CORE-Supervisor pairing in unschedule endpoint
- Transaction rollback on API failures
- Database index performance
- Comprehensive error logging

---

## Pre-Deployment Checklist

### 1. Code Review ✅
- [x] All 20 integration tests passing
- [x] Code review completed (SPRINT2_FINAL_REVIEW.md)
- [x] Database indexes created and verified
- [x] Documentation complete

### 2. Database Preparation
- [ ] Backup production database
  ```bash
  cp scheduler.db scheduler.db.backup_$(date +%Y%m%d_%H%M%S)
  ```
- [x] Apply database indexes (COMPLETED)
- [ ] Verify indexes exist:
  ```bash
  sqlite3 scheduler.db "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
  ```

### 3. Test Data Preparation
- [ ] Identify or create test CORE-Supervisor event pairs
- [ ] Document test event IDs and reference numbers
- [ ] Ensure test events won't conflict with production operations

### 4. API Credentials
- [ ] Verify Crossmark API credentials are configured
- [ ] Test API authentication:
  ```python
  from session_api_service import session_api
  result = session_api.ensure_authenticated()
  print(f"Authentication: {result}")
  ```
- [ ] Verify API access to staging/test environment (not production)

### 5. Application Configuration
- [ ] Set environment to staging mode (if applicable)
- [ ] Enable detailed logging
- [ ] Configure error tracking/monitoring
- [ ] Disable any automated scheduling during testing

---

## Deployment Steps

### Step 1: Deploy Code
- [ ] Pull latest code from branch `feature/daily-validation-dashboard`
- [ ] Verify commit `8ac18c5` (Sprint 2 completion) is included
- [ ] Install any new dependencies:
  ```bash
  pip install -r requirements.txt
  ```

### Step 2: Apply Database Migration
- [x] **COMPLETED IN DEVELOPMENT** - Indexes already applied
- [ ] If deploying to new environment, run:
  ```bash
  python apply_index_migration.py
  ```
- [ ] Verify indexes created successfully

### Step 3: Restart Application
- [ ] Stop application server
- [ ] Clear any caches
- [ ] Start application server
- [ ] Verify application starts without errors
- [ ] Check logs for any startup warnings

### Step 4: Smoke Test
- [ ] Access application homepage
- [ ] Navigate to calendar/scheduling page
- [ ] Verify UI loads correctly
- [ ] Check browser console for JavaScript errors

---

## Test Scenarios

### Test Scenario 1: Reschedule CORE with Scheduled Supervisor ✅

**Objective:** Verify both CORE and Supervisor are rescheduled together

**Prerequisites:**
- CORE event scheduled (e.g., "606001-CORE-Product Name")
- Paired Supervisor event scheduled (e.g., "606001-Supervisor-Product Name")
- Both events have valid schedule records

**Test Steps:**
1. [ ] Note original CORE schedule datetime
2. [ ] Note original Supervisor schedule datetime (should be 2 hours after CORE)
3. [ ] Reschedule CORE event to new datetime via UI or API
4. [ ] **Expected Result:**
   - CORE rescheduled to new datetime
   - Supervisor automatically rescheduled to new datetime + 2 hours
   - Both events show `sync_status='synced'`
   - Both events updated in Crossmark API
   - Success message displayed

**Verification Queries:**
```sql
-- Check CORE schedule
SELECT s.schedule_datetime, e.project_name, e.sync_status
FROM schedules s
JOIN events e ON s.event_ref_num = e.project_ref_num
WHERE e.project_name LIKE '606001-CORE-%';

-- Check Supervisor schedule
SELECT s.schedule_datetime, e.project_name, e.sync_status
FROM schedules s
JOIN events e ON s.event_ref_num = e.project_ref_num
WHERE e.project_name LIKE '606001-Supervisor-%';
```

**Log Verification:**
```bash
# Search for CORE-Supervisor pairing logs
grep "CORE event detected" logs/app.log
grep "Found paired Supervisor" logs/app.log
grep "Successfully auto-rescheduled Supervisor" logs/app.log
```

**Test Result:** [ ] PASS / [ ] FAIL
**Notes:**

---

### Test Scenario 2: Reschedule Orphan CORE (No Supervisor) ✅

**Objective:** Verify orphan CORE events can be rescheduled without errors

**Prerequisites:**
- CORE event scheduled (e.g., "606999-CORE-Product Name")
- No paired Supervisor event exists

**Test Steps:**
1. [ ] Verify no Supervisor exists:
   ```sql
   SELECT * FROM events WHERE project_name LIKE '606999-Supervisor-%';
   -- Should return 0 rows
   ```
2. [ ] Reschedule CORE event to new datetime
3. [ ] **Expected Result:**
   - CORE rescheduled successfully
   - No error about missing Supervisor
   - Log message: "No paired Supervisor event found for this CORE event"
   - Success message displayed

**Log Verification:**
```bash
grep "No Supervisor event found" logs/app.log
```

**Test Result:** [ ] PASS / [ ] FAIL
**Notes:**

---

### Test Scenario 3: Reschedule CORE with Unscheduled Supervisor ⚠️

**Objective:** Verify CORE can be rescheduled when Supervisor exists but isn't scheduled

**Prerequisites:**
- CORE event scheduled (e.g., "608001-CORE-Product Name")
- Paired Supervisor exists but not scheduled (condition='Unstaffed')

**Test Steps:**
1. [ ] Verify Supervisor exists but not scheduled:
   ```sql
   SELECT project_name, condition, is_scheduled
   FROM events
   WHERE project_name LIKE '608001-Supervisor-%';
   -- Should show condition='Unstaffed', is_scheduled=0
   ```
2. [ ] Reschedule CORE event
3. [ ] **Expected Result:**
   - CORE rescheduled successfully
   - Supervisor remains unscheduled
   - Log message: "Supervisor event exists but is not scheduled"
   - Success message displayed

**Log Verification:**
```bash
grep "Supervisor event exists but is not scheduled" logs/app.log
```

**Test Result:** [ ] PASS / [ ] FAIL
**Notes:**

---

### Test Scenario 4: Unschedule CORE with Scheduled Supervisor ✅

**Objective:** Verify both CORE and Supervisor are unscheduled together

**Prerequisites:**
- CORE event scheduled
- Paired Supervisor event scheduled

**Test Steps:**
1. [ ] Note CORE and Supervisor schedule IDs
2. [ ] Unschedule CORE event via UI or API
3. [ ] **Expected Result:**
   - CORE unscheduled (schedule record deleted, is_scheduled=False)
   - Supervisor automatically unscheduled (schedule record deleted, is_scheduled=False)
   - Both events removed from Crossmark API
   - Both events show `sync_status='synced'`
   - Success message displayed

**Verification Queries:**
```sql
-- Verify both schedule records deleted
SELECT COUNT(*) FROM schedules WHERE event_ref_num IN (606001, 606002);
-- Should return 0

-- Verify both events marked as unscheduled
SELECT project_name, is_scheduled, condition
FROM events
WHERE project_ref_num IN (606001, 606002);
-- Both should show is_scheduled=0
```

**Log Verification:**
```bash
grep "Successfully auto-unscheduled Supervisor" logs/app.log
```

**Test Result:** [ ] PASS / [ ] FAIL
**Notes:**

---

### Test Scenario 5: Transaction Rollback on API Failure 🔴

**Objective:** Verify transaction rollback when Supervisor API call fails

**Prerequisites:**
- CORE event scheduled
- Paired Supervisor event scheduled
- Ability to simulate API failure (may require code modification)

**Test Steps:**
1. [ ] Note original CORE and Supervisor schedule datetimes
2. [ ] Simulate API failure for Supervisor (options):
   - Temporarily break Supervisor API credentials
   - Modify code to inject failure (not recommended for staging)
   - Use network proxy to block specific API calls
3. [ ] Attempt to reschedule CORE event
4. [ ] **Expected Result:**
   - Transaction rolls back
   - CORE remains at original datetime
   - Supervisor remains at original datetime
   - Error message displayed to user
   - Log shows rollback: "Transaction failed during reschedule"

**Verification Queries:**
```sql
-- Verify datetimes unchanged
SELECT s.schedule_datetime, e.project_name
FROM schedules s
JOIN events e ON s.event_ref_num = e.project_ref_num
WHERE e.project_ref_num IN (606001, 606002);
```

**Log Verification:**
```bash
grep "Transaction failed during reschedule" logs/app.log
grep "rollback" logs/app.log -i
```

**Test Result:** [ ] PASS / [ ] FAIL / [ ] SKIPPED (if cannot simulate failure)
**Notes:**

---

### Test Scenario 6: Performance Testing 📊

**Objective:** Verify database indexes improve query performance

**Prerequisites:**
- Database with 100+ events (current: 481 events)
- Database indexes applied

**Test Steps:**
1. [ ] Enable query timing:
   ```sql
   .timer on
   ```
2. [ ] Test CORE event lookup:
   ```sql
   SELECT * FROM events WHERE project_name LIKE '606001-CORE-%';
   ```
   - Record time: _______ ms
3. [ ] Test Supervisor lookup:
   ```sql
   SELECT * FROM events WHERE project_name LIKE '606001-Supervisor-%';
   ```
   - Record time: _______ ms
4. [ ] Test event lookup by ref:
   ```sql
   SELECT * FROM events WHERE project_ref_num = 606001;
   ```
   - Record time: _______ ms
5. [ ] Test schedule lookup:
   ```sql
   SELECT * FROM schedules WHERE event_ref_num = 606001;
   ```
   - Record time: _______ ms

**Expected Performance:**
- All queries should complete in < 10ms with current dataset
- With 1000+ events, queries should remain < 50ms

**Test Result:** [ ] PASS / [ ] FAIL
**Notes:**

---

## Edge Case Testing

### Edge Case 1: Case-Insensitive Matching
- [ ] Test with lowercase "core": "606001-core-Product"
- [ ] Test with mixed case "CoRe": "606001-CoRe-Product"
- [ ] **Expected:** Both detected correctly

### Edge Case 2: Invalid Event Numbers
- [ ] Test CORE with non-numeric prefix: "ABC123-CORE-Product"
- [ ] **Expected:** Logged warning, no crash, CORE processed normally

### Edge Case 3: Multiple Supervisors
- [ ] Test CORE with 2+ Supervisor events (edge case - shouldn't happen)
- [ ] **Expected:** Only first Supervisor found is processed

### Edge Case 4: Missing external_id
- [ ] Test event with no external_id field
- [ ] **Expected:** Logged warning, API call skipped gracefully

---

## Monitoring and Logging

### Log Locations
```bash
# Application logs
tail -f logs/app.log

# Error logs
tail -f logs/error.log

# API call logs
grep "Crossmark API" logs/app.log
```

### Key Log Messages to Monitor

**Success Messages:**
- `"CORE event detected: {project_name}"`
- `"Found paired Supervisor: {project_name}"`
- `"Calling Crossmark API for Supervisor: schedule_id={id}"`
- `"Successfully auto-rescheduled Supervisor event {ref_num}"`
- `"Successfully auto-unscheduled Supervisor event {ref_num}"`

**Warning Messages:**
- `"No Supervisor event found for CORE event {id}"`
- `"Supervisor event exists but is not scheduled"`
- `"Could not extract event number from: {project_name}"`

**Error Messages:**
- `"Transaction failed during reschedule"`
- `"Failed to reschedule Supervisor in Crossmark"`
- `"Supervisor reschedule API call failed"`

---

## Performance Monitoring

### Metrics to Track
- [ ] Average reschedule operation time
- [ ] Average unschedule operation time
- [ ] Database query time (LIKE queries)
- [ ] API call latency
- [ ] Transaction rollback frequency

### Performance Baseline
**Before Indexes:**
- LIKE queries: Expected 50-500ms with 1000+ events

**After Indexes (Current):**
- LIKE queries: < 10ms with 481 events
- Direct lookups: < 5ms

---

## Rollback Procedures

### If Issues Found During Testing

**Minor Issues (Logging, UI messages):**
- [ ] Document issue
- [ ] Continue testing
- [ ] Fix in next iteration

**Major Issues (Data corruption, API failures):**
1. [ ] Stop application immediately
2. [ ] Restore database from backup:
   ```bash
   cp scheduler.db.backup_YYYYMMDD_HHMMSS scheduler.db
   ```
3. [ ] Rollback code to previous version
4. [ ] Investigate issue
5. [ ] Document root cause

**Database Index Issues:**
1. [ ] Rollback indexes:
   ```bash
   python apply_index_migration.py --rollback
   ```
2. [ ] Verify application works without indexes
3. [ ] Fix index migration script
4. [ ] Reapply when ready

---

## Sign-Off Checklist

### Functional Testing
- [ ] TC-033: Reschedule CORE with Supervisor - PASS
- [ ] TC-034: Reschedule orphan CORE - PASS
- [ ] TC-035: Reschedule CORE with unscheduled Supervisor - PASS
- [ ] TC-037: Unschedule CORE with Supervisor - PASS
- [ ] TC-038: Unschedule orphan CORE - PASS
- [ ] TC-039: Unschedule CORE with unscheduled Supervisor - PASS

### Performance Testing
- [ ] Query performance acceptable - PASS
- [ ] No performance degradation observed - PASS

### Error Handling
- [ ] Graceful handling of missing Supervisors - PASS
- [ ] Graceful handling of unscheduled Supervisors - PASS
- [ ] Transaction rollback works correctly - PASS (or SKIPPED)

### Logging
- [ ] All key operations logged - PASS
- [ ] Error messages clear and actionable - PASS
- [ ] No sensitive data in logs - PASS

### Overall Assessment
- [ ] All critical tests passing
- [ ] No blocking issues found
- [ ] Performance acceptable
- [ ] Ready for production deployment

**Tested By:** ___________________
**Date:** ___________________
**Approval:** [ ] APPROVED / [ ] REJECTED

---

## Post-Testing Actions

### If Testing PASSES ✅
1. [ ] Document test results
2. [ ] Update SPRINT2_PROGRESS_SUMMARY.md
3. [ ] Create production deployment plan
4. [ ] Schedule production deployment
5. [ ] Prepare production monitoring

### If Testing FAILS ❌
1. [ ] Document all failures
2. [ ] Categorize issues (critical, major, minor)
3. [ ] Create fix plan with timeline
4. [ ] Update risk assessment
5. [ ] Re-test after fixes

---

## Production Deployment Readiness

### Pre-Production Checklist
- [ ] All staging tests passed
- [ ] Performance benchmarks met
- [ ] No critical issues found
- [ ] Rollback plan documented
- [ ] Monitoring alerts configured
- [ ] Team notified of deployment

### Production Deployment Steps
1. [ ] Schedule maintenance window (if needed)
2. [ ] Backup production database
3. [ ] Deploy code to production
4. [ ] Apply database migration
5. [ ] Restart application
6. [ ] Smoke test production
7. [ ] Monitor logs for 1 hour
8. [ ] Verify first real CORE-Supervisor operation

---

## Support Contacts

**Development Team:**
- Primary: ___________________
- Backup: ___________________

**Crossmark API Support:**
- Email: ___________________
- Phone: ___________________

**Database Admin:**
- Contact: ___________________

---

## Appendix: Useful SQL Queries

### Find CORE Events
```sql
SELECT project_ref_num, project_name, condition, is_scheduled
FROM events
WHERE project_name LIKE '%-CORE-%';
```

### Find Supervisor Events
```sql
SELECT project_ref_num, project_name, condition, is_scheduled
FROM events
WHERE project_name LIKE '%-Supervisor-%';
```

### Find CORE-Supervisor Pairs
```sql
SELECT
    c.project_ref_num as core_ref,
    c.project_name as core_name,
    c.is_scheduled as core_scheduled,
    s.project_ref_num as super_ref,
    s.project_name as super_name,
    s.is_scheduled as super_scheduled
FROM events c
LEFT JOIN events s ON SUBSTR(c.project_name, 1, 6) = SUBSTR(s.project_name, 1, 6)
    AND c.project_name LIKE '%-CORE-%'
    AND s.project_name LIKE '%-Supervisor-%'
WHERE c.project_name LIKE '%-CORE-%';
```

### Check Schedule Records
```sql
SELECT
    s.id as schedule_id,
    s.event_ref_num,
    s.schedule_datetime,
    e.project_name,
    e.condition
FROM schedules s
JOIN events e ON s.event_ref_num = e.project_ref_num
WHERE e.project_name LIKE '%606001%'
ORDER BY s.schedule_datetime;
```

### Verify Indexes
```sql
SELECT name, tbl_name, sql
FROM sqlite_master
WHERE type='index'
AND name LIKE 'idx_%'
ORDER BY tbl_name, name;
```

---

**Last Updated:** 2025-10-13
**Version:** 1.0
**Next Review:** After staging testing complete
