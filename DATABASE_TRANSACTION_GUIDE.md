# Database Transaction Implementation Guide
## CORE-Supervisor Pairing Logic

**Project:** Flask Schedule WebApp - Calendar Redesign
**Critical Component:** Data Integrity for Automatic Pairing
**Author:** Quinn (QA Test Architect)
**Date:** 2025-10-12

---

## Overview

This guide provides **production-ready code** for implementing database transactions in the CORE-Supervisor pairing logic. Proper transaction handling is **CRITICAL** to prevent data corruption.

**Key Principle:** Rescheduling or unscheduling a CORE event and its paired Supervisor event must be **ATOMIC** (all-or-nothing).

---

## Table of Contents

1. [Transaction Fundamentals](#transaction-fundamentals)
2. [Reschedule Implementation](#reschedule-implementation)
3. [Unschedule Implementation](#unschedule-implementation)
4. [Helper Functions](#helper-functions)
5. [Error Handling](#error-handling)
6. [Testing Transactions](#testing-transactions)
7. [Rollback Scenarios](#rollback-scenarios)

---

## Transaction Fundamentals

### What is a Database Transaction?

A transaction ensures that a group of database operations either:
- **ALL succeed** (committed to database)
- **ALL fail** (rolled back, no changes)

There is no "partial success" - this prevents data corruption.

### Why Transactions Matter for CORE-Supervisor Pairing

**Without Transactions:**
```python
# ❌ DANGER: No transaction
schedule.start_datetime = new_date  # CORE rescheduled
db.session.commit()                  # Committed!

supervisor_schedule.start_datetime = new_date  # If this fails...
db.session.commit()                            # ...CORE is rescheduled but Supervisor is not!
```

**Result:** CORE event on Oct 20, Supervisor event still on Oct 15 → Data corruption!

**With Transactions:**
```python
# ✅ SAFE: With transaction
try:
    schedule.start_datetime = new_date  # CORE rescheduled
    supervisor_schedule.start_datetime = new_date  # Supervisor rescheduled
    db.session.commit()  # BOTH committed together
except Exception as e:
    db.session.rollback()  # BOTH rolled back
    raise e
```

**Result:** Either BOTH rescheduled OR BOTH unchanged → Data integrity maintained!

---

## Reschedule Implementation

### File: `scheduler_app/routes/api.py`

```python
from flask import jsonify, request
from scheduler_app import db
from scheduler_app.models import Event, Schedule
from scheduler_app.utils.supervisor_helpers import get_supervisor_event
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@app.route('/api/reschedule_event', methods=['POST'])
def reschedule_event():
    """
    Reschedule an event, automatically rescheduling paired Supervisor event if applicable.

    Request JSON:
        {
            "schedule_id": int,
            "new_date": "2025-10-20T10:00:00",  # ISO format
            "new_employee_id": int (optional)
        }

    Returns:
        {
            "success": true,
            "message": "Event rescheduled successfully",
            "supervisor_rescheduled": true/false,
            "new_date": "2025-10-20T10:00:00"
        }
    """
    try:
        # =====================================================================
        # 1. VALIDATE INPUT
        # =====================================================================
        data = request.get_json()

        if not data or 'schedule_id' not in data or 'new_date' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: schedule_id, new_date'
            }), 400

        schedule_id = data['schedule_id']
        new_date_str = data['new_date']
        new_employee_id = data.get('new_employee_id')  # Optional

        # Parse new date
        try:
            new_date = datetime.fromisoformat(new_date_str.replace('Z', '+00:00'))
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': f'Invalid date format: {new_date_str}. Use ISO format.'
            }), 400

        # =====================================================================
        # 2. FETCH SCHEDULE AND EVENT
        # =====================================================================
        schedule = Schedule.query.get(schedule_id)
        if not schedule:
            return jsonify({
                'success': False,
                'error': f'Schedule not found: {schedule_id}'
            }), 404

        event = Event.query.get(schedule.event_id)
        if not event:
            return jsonify({
                'success': False,
                'error': f'Event not found for schedule: {schedule_id}'
            }), 404

        old_date = schedule.start_datetime

        logger.info(f"Rescheduling event {event.event_id} ({event.project_name}) from {old_date} to {new_date}")

        # =====================================================================
        # 3. BEGIN TRANSACTION (CRITICAL)
        # =====================================================================
        supervisor_rescheduled = False

        try:
            # Use nested transaction for savepoint (rollback partial changes)
            with db.session.begin_nested():

                # ================================================================
                # 3a. UPDATE CORE EVENT SCHEDULE
                # ================================================================
                schedule.start_datetime = new_date

                if new_employee_id:
                    schedule.employee_id = new_employee_id
                    logger.info(f"  Changed employee from {schedule.employee_id} to {new_employee_id}")

                # ================================================================
                # 3b. CHECK IF THIS IS A CORE EVENT
                # ================================================================
                if '-CORE-' in event.project_name.upper():  # Case-insensitive
                    logger.info(f"  CORE event detected, looking for paired Supervisor...")

                    supervisor_event = get_supervisor_event(event)

                    if not supervisor_event:
                        logger.warning(f"  No Supervisor event found for CORE event {event.event_id}: {event.project_name}")
                        # Continue with CORE reschedule only (not an error)

                    elif supervisor_event.condition != 'Scheduled':
                        logger.info(f"  Supervisor event {supervisor_event.event_id} is not scheduled (condition={supervisor_event.condition}), skipping")
                        # Don't reschedule unscheduled Supervisor events

                    else:
                        # Supervisor event exists and is scheduled - reschedule it
                        supervisor_schedule = Schedule.query.filter_by(
                            event_id=supervisor_event.event_id
                        ).first()

                        if supervisor_schedule:
                            # Reschedule Supervisor to same date at 12:00 PM (default time)
                            supervisor_new_date = new_date.replace(hour=12, minute=0, second=0)
                            supervisor_old_date = supervisor_schedule.start_datetime

                            supervisor_schedule.start_datetime = supervisor_new_date

                            logger.info(f"  ✅ Auto-rescheduled Supervisor event {supervisor_event.event_id} from {supervisor_old_date} to {supervisor_new_date}")
                            supervisor_rescheduled = True
                        else:
                            logger.warning(f"  Supervisor event {supervisor_event.event_id} has no schedule record")

                # ================================================================
                # 3c. COMMIT NESTED TRANSACTION
                # ================================================================
                # If we reach here, all changes succeeded
                # Nested transaction will commit

            # =====================================================================
            # 4. COMMIT OUTER TRANSACTION
            # =====================================================================
            db.session.commit()

            logger.info(f"✅ Successfully rescheduled event {event.event_id} to {new_date}")

            return jsonify({
                'success': True,
                'message': 'Event rescheduled successfully',
                'supervisor_rescheduled': supervisor_rescheduled,
                'new_date': new_date.isoformat(),
                'event_id': event.event_id
            }), 200

        except Exception as nested_error:
            # Nested transaction failed - rollback to savepoint
            logger.error(f"❌ Nested transaction failed: {nested_error}", exc_info=True)
            db.session.rollback()
            raise nested_error

    except Exception as e:
        # Outer exception handler - rollback entire transaction
        logger.error(f"❌ Failed to reschedule event {schedule_id}: {e}", exc_info=True)
        db.session.rollback()

        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to reschedule event. No changes made.'
        }), 500
```

### Key Points

1. **Nested Transactions (`begin_nested()`):**
   - Creates a savepoint
   - If inner transaction fails, rollback to savepoint
   - Outer transaction remains intact

2. **Error Handling:**
   - Inner `try/except` catches nested transaction errors
   - Outer `try/except` catches all errors and returns HTTP 500

3. **Logging:**
   - Structured logging with event IDs, dates, and outcomes
   - Enables debugging and monitoring

4. **Case-Insensitive Matching:**
   - `-CORE-` check uses `.upper()` to handle "core", "CORE", "Core"

5. **Supervisor Scheduling Logic:**
   - Only reschedule if Supervisor is already scheduled
   - Default time: 12:00 PM on new date
   - Employee assignment remains unchanged

---

## Unschedule Implementation

### File: `scheduler_app/routes/api.py`

```python
@app.route('/api/unschedule/<int:schedule_id>', methods=['DELETE'])
def unschedule(schedule_id):
    """
    Unschedule an event, automatically unscheduling paired Supervisor event if applicable.

    Args:
        schedule_id: Schedule ID to unschedule

    Returns:
        {
            "success": true,
            "message": "Event unscheduled successfully",
            "supervisor_unscheduled": true/false
        }
    """
    try:
        # =====================================================================
        # 1. FETCH SCHEDULE AND EVENT
        # =====================================================================
        schedule = Schedule.query.get(schedule_id)
        if not schedule:
            return jsonify({
                'success': False,
                'error': f'Schedule not found: {schedule_id}'
            }), 404

        event = Event.query.get(schedule.event_id)
        if not event:
            return jsonify({
                'success': False,
                'error': f'Event not found for schedule: {schedule_id}'
            }), 404

        logger.info(f"Unscheduling event {event.event_id} ({event.project_name})")

        # =====================================================================
        # 2. BEGIN TRANSACTION (CRITICAL)
        # =====================================================================
        supervisor_unscheduled = False

        try:
            with db.session.begin_nested():

                # ================================================================
                # 2a. UNSCHEDULE CORE EVENT
                # ================================================================
                event.condition = 'Unstaffed'
                event.is_scheduled = False
                db.session.delete(schedule)  # Remove schedule record

                logger.info(f"  Unscheduled CORE event, deleted schedule {schedule_id}")

                # ================================================================
                # 2b. CHECK IF THIS IS A CORE EVENT
                # ================================================================
                if '-CORE-' in event.project_name.upper():
                    logger.info(f"  CORE event detected, looking for paired Supervisor...")

                    supervisor_event = get_supervisor_event(event)

                    if not supervisor_event:
                        logger.warning(f"  No Supervisor event found for CORE event {event.event_id}")
                        # Continue with CORE unschedule only

                    elif supervisor_event.condition != 'Scheduled':
                        logger.info(f"  Supervisor event {supervisor_event.event_id} is already unscheduled, skipping")

                    else:
                        # Supervisor event exists and is scheduled - unschedule it
                        supervisor_schedule = Schedule.query.filter_by(
                            event_id=supervisor_event.event_id
                        ).first()

                        if supervisor_schedule:
                            supervisor_event.condition = 'Unstaffed'
                            supervisor_event.is_scheduled = False
                            db.session.delete(supervisor_schedule)

                            logger.info(f"  ✅ Auto-unscheduled Supervisor event {supervisor_event.event_id}")
                            supervisor_unscheduled = True
                        else:
                            logger.warning(f"  Supervisor event {supervisor_event.event_id} has no schedule record")

                # ================================================================
                # 2c. COMMIT NESTED TRANSACTION
                # ================================================================
                # All changes succeeded, commit nested transaction

            # =====================================================================
            # 3. COMMIT OUTER TRANSACTION
            # =====================================================================
            db.session.commit()

            logger.info(f"✅ Successfully unscheduled event {event.event_id}")

            return jsonify({
                'success': True,
                'message': 'Event unscheduled successfully',
                'supervisor_unscheduled': supervisor_unscheduled,
                'event_id': event.event_id
            }), 200

        except Exception as nested_error:
            logger.error(f"❌ Nested transaction failed: {nested_error}", exc_info=True)
            db.session.rollback()
            raise nested_error

    except Exception as e:
        logger.error(f"❌ Failed to unschedule event {schedule_id}: {e}", exc_info=True)
        db.session.rollback()

        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to unschedule event. No changes made.'
        }), 500
```

---

## Helper Functions

### File: `scheduler_app/utils/supervisor_helpers.py`

Create this new file for pairing logic helpers:

```python
"""
Supervisor Event Pairing Helpers
Provides functions to match CORE events with their paired Supervisor events
"""

import re
import logging
from scheduler_app.models import Event

logger = logging.getLogger(__name__)

def get_supervisor_event(core_event):
    """
    Find the Supervisor event paired with a CORE event.

    Matching Strategy:
    1. Extract 6-digit event number from CORE event name (e.g., "606001-CORE-Product" → "606001")
    2. Query for Supervisor event with matching event number (e.g., "606001-Supervisor-*")
    3. Return first match OR None if not found

    Args:
        core_event: Event object with project_name containing '-CORE-'

    Returns:
        Event object (Supervisor event) OR None if not found

    Example:
        core = Event(project_name="606001-CORE-Super Pretzel")
        supervisor = get_supervisor_event(core)  # Returns "606001-Supervisor-Super Pretzel"
    """

    logger.debug(f"Looking for Supervisor event for CORE: {core_event.project_name}")

    # =========================================================================
    # STRATEGY 1: Regex extraction of 6-digit event number
    # =========================================================================
    match = re.search(r'(\d{6})-CORE-', core_event.project_name, re.IGNORECASE)

    if not match:
        logger.warning(f"Could not extract 6-digit event number from: {core_event.project_name}")
        logger.warning(f"  Expected format: NNNNNN-CORE-ProductName (e.g., 606001-CORE-Product)")
        return None

    event_number = match.group(1)
    logger.debug(f"  Extracted event number: {event_number}")

    # =========================================================================
    # STRATEGY 2: Query for matching Supervisor event (case-insensitive)
    # =========================================================================
    supervisor_event = Event.query.filter(
        Event.project_name.ilike(f'{event_number}-Supervisor-%')
    ).first()

    if supervisor_event:
        logger.debug(f"  ✅ Found Supervisor event: {supervisor_event.event_id} ({supervisor_event.project_name})")
        return supervisor_event
    else:
        logger.warning(f"  ❌ No Supervisor event found with event number: {event_number}")
        return None


def get_supervisor_status(core_event):
    """
    Get the scheduling status of a CORE event's paired Supervisor event.

    Returns:
        dict with keys:
            - status: 'scheduled' | 'unscheduled' | 'not_found'
            - message: Human-readable message
            - employee: Employee name (if scheduled)
            - time: Scheduled time (if scheduled)
            - event_id: Supervisor event ID

    Example:
        {
            'status': 'scheduled',
            'message': 'Supervisor Event Scheduled (Jane Doe @ 12:00 PM)',
            'employee': 'Jane Doe',
            'time': '12:00 PM',
            'event_id': 1002
        }
    """
    from scheduler_app.models import Schedule  # Import here to avoid circular imports

    supervisor_event = get_supervisor_event(core_event)

    if not supervisor_event:
        return {
            'status': 'not_found',
            'message': 'No Supervisor event configured for this CORE event'
        }

    if supervisor_event.condition == 'Scheduled' and supervisor_event.is_scheduled:
        # Supervisor is scheduled - get schedule details
        schedule = Schedule.query.filter_by(
            event_id=supervisor_event.event_id
        ).first()

        if schedule and schedule.employee:
            return {
                'status': 'scheduled',
                'message': f'Supervisor Event Scheduled ({schedule.employee.name} @ {schedule.start_datetime.strftime("%I:%M %p")})',
                'employee': schedule.employee.name,
                'time': schedule.start_datetime.strftime('%I:%M %p'),
                'event_id': supervisor_event.event_id
            }
        else:
            # Inconsistent state: marked as scheduled but no schedule record
            logger.warning(f"Supervisor event {supervisor_event.event_id} marked as Scheduled but has no schedule record")
            return {
                'status': 'unscheduled',
                'message': 'Supervisor Event NOT Scheduled (data inconsistency)',
                'event_id': supervisor_event.event_id
            }
    else:
        # Supervisor is unscheduled
        return {
            'status': 'unscheduled',
            'message': 'Supervisor Event NOT Scheduled',
            'event_id': supervisor_event.event_id
        }
```

---

## Error Handling

### Common Error Scenarios

**1. Database Connection Lost:**
```python
# SQLAlchemy will raise OperationalError
# Transaction automatically rolls back
# Return HTTP 500 with error message
```

**2. Constraint Violation:**
```python
# E.g., foreign key violation, unique constraint
# Transaction rolls back
# Return HTTP 400 or 500 depending on error
```

**3. Supervisor Event Not Found:**
```python
# NOT an error - log warning and continue
# CORE event rescheduled successfully
# Return success with supervisor_rescheduled=False
```

### Error Response Format

```json
{
    "success": false,
    "error": "Short error message",
    "message": "User-friendly error message",
    "details": "Optional detailed error information"
}
```

---

## Testing Transactions

### Unit Test: Transaction Rollback

```python
# File: tests/test_reschedule_pairing.py

import pytest
from scheduler_app import db
from scheduler_app.models import Event, Schedule
from unittest.mock import patch

def test_reschedule_rollback_on_supervisor_failure(client, test_db):
    """Test that CORE reschedule rolls back if Supervisor reschedule fails"""

    # Setup: Create CORE and Supervisor events
    core_event = Event(
        project_name='606001-CORE-Test Product',
        event_type='CORE',
        condition='Scheduled',
        is_scheduled=True,
        start_datetime=datetime(2025, 10, 15, 10, 0)
    )
    supervisor_event = Event(
        project_name='606001-Supervisor-Test Product',
        event_type='Supervisor',
        condition='Scheduled',
        is_scheduled=True,
        start_datetime=datetime(2025, 10, 15, 12, 0)
    )
    db.session.add_all([core_event, supervisor_event])
    db.session.commit()

    core_schedule = Schedule(event_id=core_event.event_id, employee_id=101, start_datetime=datetime(2025, 10, 15, 10, 0))
    supervisor_schedule = Schedule(event_id=supervisor_event.event_id, employee_id=102, start_datetime=datetime(2025, 10, 15, 12, 0))
    db.session.add_all([core_schedule, supervisor_schedule])
    db.session.commit()

    # Simulate database failure during Supervisor update
    with patch('scheduler_app.models.db.session.commit', side_effect=Exception('Simulated DB failure')):
        response = client.post('/api/reschedule_event', json={
            'schedule_id': core_schedule.schedule_id,
            'new_date': '2025-10-20T10:00:00'
        })

    # Assert: HTTP 500 error
    assert response.status_code == 500
    assert 'Simulated DB failure' in response.json['error']

    # Assert: CORE event NOT rescheduled (rolled back)
    db.session.refresh(core_schedule)
    assert core_schedule.start_datetime == datetime(2025, 10, 15, 10, 0)

    # Assert: Supervisor event NOT rescheduled (rolled back)
    db.session.refresh(supervisor_schedule)
    assert supervisor_schedule.start_datetime == datetime(2025, 10, 15, 12, 0)
```

---

## Rollback Scenarios

### Scenario 1: Partial Success (NO ROLLBACK)

**What happens:**
- CORE event reschedule succeeds
- Supervisor event not found
- Transaction commits

**Result:** ✅ CORRECT - CORE rescheduled, no Supervisor to reschedule

---

### Scenario 2: Database Failure (ROLLBACK)

**What happens:**
- CORE event reschedule succeeds
- Supervisor event reschedule fails (database error)
- Exception raised

**Result:** ✅ CORRECT - Both rolled back, no changes

---

### Scenario 3: Constraint Violation (ROLLBACK)

**What happens:**
- CORE event reschedule succeeds
- Supervisor event reschedule violates unique constraint
- Exception raised

**Result:** ✅ CORRECT - Both rolled back, no changes

---

## Production Checklist

Before deploying to production, ensure:

- [ ] All reschedule/unschedule functions use transactions
- [ ] Error logging configured (application logs to file/Splunk/Kibana)
- [ ] Monitoring alerts set up for transaction failures
- [ ] Database backup created
- [ ] Rollback plan documented
- [ ] Load testing completed with transaction failures simulated
- [ ] Code review approved by Tech Lead

---

**Document Version:** 1.0
**Last Updated:** 2025-10-12
**Owner:** Quinn (QA Test Architect)
