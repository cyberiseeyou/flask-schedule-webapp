# Calendar Redesign - Implementation Guide

**Project:** Flask Schedule WebApp - Calendar Redesign
**Version:** 1.0
**Created:** 2025-10-12
**Target:** Sprint 2 (4 weeks)

---

## 📖 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Week 1: Backend Foundation](#week-1-backend-foundation)
4. [Week 2: Safety Nets & Performance](#week-2-safety-nets--performance)
5. [Week 3: Frontend Implementation](#week-3-frontend-implementation)
6. [Week 4: Testing & Deployment](#week-4-testing--deployment)
7. [Rollback Plan](#rollback-plan)
8. [FAQ](#faq)

---

## Overview

This guide provides a step-by-step implementation plan for the Calendar Redesign project. The redesign replaces the existing modal-based calendar with a full-screen month view and dedicated daily view page.

### Key Features

- **Full-screen calendar month view** with color-coded event badges
- **Dedicated daily view page** (replaces modal interface)
- **CORE-Supervisor automatic pairing** for reschedule/unschedule operations
- **Event type counts** (CORE, Juicer, Supervisor, Freeosk, Digitals, Other)
- **Unscheduled event warnings** (visual indicators)
- **Responsive design** (desktop, tablet, mobile)
- **Accessibility** (WCAG AA compliant)

### Critical Components

1. **Database Transactions** - Ensure CORE-Supervisor pairs stay synchronized
2. **Orphan Detection Job** - Daily monitoring for data integrity issues
3. **Performance Optimization** - Handle 1000+ events efficiently
4. **Frontend Calendar Grid** - Interactive month/day navigation

---

## Prerequisites

### Required Reading

Before starting implementation, read these documents:

1. **QA_DELIVERABLES_README.md** - Overview and quick start
2. **UX_MOCKUP_SPECIFICATION.md** - Complete UX design (scan sections 1-3)
3. **DATABASE_TRANSACTION_GUIDE.md** - Transaction implementation code
4. **FRONTEND_COMPONENT_CHECKLIST.md** - Frontend task breakdown

### Development Environment

```bash
# Ensure you have:
- Python 3.8+
- PostgreSQL 12+ (or MySQL 8+)
- Redis 6+ (for caching)
- Node.js 16+ (for frontend build tools)
- Git

# Install dependencies
pip install -r requirements.txt
npm install  # If using frontend build tools
```

### Test Database Setup

```bash
# Load test data
psql -U your_user -d scheduler_test -f test_data/sprint1_minimal_testdata.sql

# Verify test data loaded
psql -U your_user -d scheduler_test -c "SELECT COUNT(*) FROM events WHERE event_id >= 1000;"
# Expected: 21 rows
```

---

## Week 1: Backend Foundation

### Day 1: Database Transaction Implementation

**Goal:** Implement transaction handling for CORE-Supervisor pairing

**Tasks:**

1. **Create helper functions** (30 minutes)

```python
# In scheduler_app/utils/event_helpers.py (create new file)

import re
import logging
from scheduler_app.models import Event

logger = logging.getLogger(__name__)

def get_supervisor_event(core_event):
    """
    Find Supervisor event paired with CORE event.

    Args:
        core_event: Event object with project_name containing "-CORE-"

    Returns:
        Event object or None
    """
    match = re.search(r'(\d{6})-CORE-', core_event.project_name, re.IGNORECASE)
    if not match:
        logger.warning(f"Could not extract event number from: {core_event.project_name}")
        return None

    event_number = match.group(1)
    supervisor_event = Event.query.filter(
        Event.project_name.ilike(f'{event_number}-Supervisor-%')
    ).first()

    if not supervisor_event:
        logger.info(f"No Supervisor event found for CORE event {core_event.event_id}")

    return supervisor_event

def get_supervisor_status(core_event):
    """
    Get status of paired Supervisor event.

    Returns:
        dict: {
            'exists': bool,
            'event': Event or None,
            'is_scheduled': bool,
            'start_datetime': datetime or None
        }
    """
    supervisor = get_supervisor_event(core_event)

    if not supervisor:
        return {'exists': False, 'event': None, 'is_scheduled': False, 'start_datetime': None}

    return {
        'exists': True,
        'event': supervisor,
        'is_scheduled': supervisor.condition == 'Scheduled',
        'start_datetime': supervisor.start_datetime
    }
```

2. **Update reschedule endpoint** (45 minutes)

Open `scheduler_app/routes/main.py` and find the `reschedule_event` function. Replace it with the transaction-safe version from `DATABASE_TRANSACTION_GUIDE.md`:

```python
@app.route('/api/reschedule_event', methods=['POST'])
def reschedule_event():
    """
    Reschedule event with CORE-Supervisor pairing support.

    If rescheduling a CORE event, automatically reschedule paired Supervisor.
    Uses database transactions to ensure data integrity.
    """
    try:
        data = request.get_json()
        schedule_id = data.get('schedule_id')
        new_date_str = data.get('new_date')

        if not schedule_id or not new_date_str:
            return jsonify({'success': False, 'error': 'Missing required parameters'}), 400

        # Parse new date
        new_date = datetime.fromisoformat(new_date_str)

        # Fetch schedule and event
        schedule = Schedule.query.get(schedule_id)
        if not schedule:
            return jsonify({'success': False, 'error': 'Schedule not found'}), 404

        event = Event.query.get(schedule.event_id)
        if not event:
            return jsonify({'success': False, 'error': 'Event not found'}), 404

        # BEGIN TRANSACTION
        try:
            with db.session.begin_nested():  # Savepoint
                # Update CORE event
                old_date = schedule.start_datetime
                schedule.start_datetime = new_date
                event.start_datetime = new_date

                logger.info(f"Rescheduling event {event.event_id} from {old_date} to {new_date}")

                # If CORE event, reschedule Supervisor
                if '-CORE-' in event.project_name.upper():
                    supervisor_status = get_supervisor_status(event)

                    if supervisor_status['exists'] and supervisor_status['is_scheduled']:
                        supervisor_event = supervisor_status['event']
                        supervisor_schedule = Schedule.query.filter_by(
                            event_id=supervisor_event.event_id
                        ).first()

                        if supervisor_schedule:
                            # Reschedule Supervisor to 2 hours after CORE
                            supervisor_new_date = new_date + timedelta(hours=2)
                            supervisor_schedule.start_datetime = supervisor_new_date
                            supervisor_event.start_datetime = supervisor_new_date

                            logger.info(
                                f"✅ Auto-rescheduled Supervisor event {supervisor_event.event_id} "
                                f"to {supervisor_new_date}"
                            )

            # COMMIT TRANSACTION
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Event rescheduled successfully',
                'event_id': event.event_id
            })

        except Exception as nested_error:
            db.session.rollback()
            logger.error(f"Transaction failed: {nested_error}", exc_info=True)
            raise nested_error

    except Exception as e:
        db.session.rollback()
        logger.error(f"Reschedule failed: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
```

3. **Update unschedule endpoint** (45 minutes)

Similarly, update the `unschedule_event` function:

```python
@app.route('/api/unschedule_event', methods=['POST'])
def unschedule_event():
    """
    Unschedule event with CORE-Supervisor pairing support.

    If unscheduling a CORE event, automatically unschedule paired Supervisor.
    """
    try:
        data = request.get_json()
        schedule_id = data.get('schedule_id')

        if not schedule_id:
            return jsonify({'success': False, 'error': 'Missing schedule_id'}), 400

        # Fetch schedule and event
        schedule = Schedule.query.get(schedule_id)
        if not schedule:
            return jsonify({'success': False, 'error': 'Schedule not found'}), 404

        event = Event.query.get(schedule.event_id)

        # BEGIN TRANSACTION
        try:
            with db.session.begin_nested():
                # Unschedule CORE event
                db.session.delete(schedule)
                event.condition = 'Unstaffed'
                event.is_scheduled = False
                event.start_datetime = None

                logger.info(f"Unscheduling event {event.event_id}")

                # If CORE event, unschedule Supervisor
                if '-CORE-' in event.project_name.upper():
                    supervisor_status = get_supervisor_status(event)

                    if supervisor_status['exists'] and supervisor_status['is_scheduled']:
                        supervisor_event = supervisor_status['event']
                        supervisor_schedule = Schedule.query.filter_by(
                            event_id=supervisor_event.event_id
                        ).first()

                        if supervisor_schedule:
                            db.session.delete(supervisor_schedule)
                            supervisor_event.condition = 'Unstaffed'
                            supervisor_event.is_scheduled = False
                            supervisor_event.start_datetime = None

                            logger.info(f"✅ Auto-unscheduled Supervisor event {supervisor_event.event_id}")

            # COMMIT
            db.session.commit()

            return jsonify({'success': True, 'message': 'Event unscheduled successfully'})

        except Exception as nested_error:
            db.session.rollback()
            raise nested_error

    except Exception as e:
        db.session.rollback()
        logger.error(f"Unschedule failed: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
```

4. **Test transaction handling** (30 minutes)

```bash
# Run unit tests
pytest scheduler_app/tests/test_event_pairing.py -v

# Manual test:
# 1. Load test data
# 2. Navigate to daily view
# 3. Reschedule CORE event "606001-CORE-Super Pretzel"
# 4. Verify Supervisor "606001-Supervisor-Super Pretzel" also rescheduled
```

### Day 2: Database Indexing & Logging

**Goal:** Add indexes for performance and comprehensive logging

**Tasks:**

1. **Create database migration** (20 minutes)

```sql
-- migrations/add_calendar_indexes.sql

-- Index for project_name (used in CORE-Supervisor matching)
CREATE INDEX idx_events_project_name ON events(project_name);

-- Index for start_datetime (used in calendar queries)
CREATE INDEX idx_events_start_datetime ON events(start_datetime);

-- Index for event_type (used in type filtering)
CREATE INDEX idx_events_event_type ON events(event_type);

-- Index for condition (scheduled vs unscheduled)
CREATE INDEX idx_events_condition ON events(condition);

-- Composite index for schedule lookups
CREATE INDEX idx_schedule_event_employee ON schedule(event_id, employee_id);
```

Apply migration:

```bash
psql -U your_user -d scheduler_db -f migrations/add_calendar_indexes.sql
```

2. **Configure structured logging** (30 minutes)

```python
# In scheduler_app/__init__.py

import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging(app):
    """Configure structured logging for the application."""

    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.mkdir('logs')

    # File handler with rotation
    file_handler = RotatingFileHandler(
        'logs/scheduler_app.log',
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] - %(message)s'
    ))
    file_handler.setLevel(logging.INFO)

    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(levelname)s - %(message)s'
    ))
    console_handler.setLevel(logging.DEBUG)

    # Configure root logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)

    # Log startup
    app.logger.info('Scheduler App Starting')

# Call in create_app()
def create_app():
    app = Flask(__name__)
    # ... existing config ...
    setup_logging(app)
    return app
```

3. **Add audit logging** (40 minutes)

```python
# Create scheduler_app/models/audit_log.py

from scheduler_app import db
from datetime import datetime

class AuditLog(db.Model):
    __tablename__ = 'audit_log'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    action = db.Column(db.String(50), nullable=False)  # 'reschedule', 'unschedule', 'schedule'
    event_id = db.Column(db.Integer, db.ForeignKey('events.event_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # If you have user auth
    old_value = db.Column(db.Text)  # JSON string
    new_value = db.Column(db.Text)  # JSON string
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)

    def __repr__(self):
        return f'<AuditLog {self.action} on Event {self.event_id} at {self.timestamp}>'
```

Create migration:

```bash
flask db migrate -m "Add audit_log table"
flask db upgrade
```

Add audit logging to reschedule/unschedule:

```python
# In reschedule_event(), before commit:
audit = AuditLog(
    action='reschedule',
    event_id=event.event_id,
    old_value=json.dumps({'date': old_date.isoformat()}),
    new_value=json.dumps({'date': new_date.isoformat()}),
    success=True
)
db.session.add(audit)
```

### Day 3-4: Execute Critical Tests

**Goal:** Validate transaction handling works correctly

Follow **TEST_PLAN.md** Section 4 (Test Procedures):

- ✅ TC-033: Reschedule CORE, Supervisor follows
- ✅ TC-036: Transaction rollback on failure
- ✅ TC-041: Unschedule CORE, Supervisor unscheduled
- ✅ TC-043: Multiple supervisor events
- ✅ TC-045: Auto-schedule when CORE scheduled

Document results in `test_results/week1_results.md`

### Day 5: Code Review & Documentation

- Code review with team
- Update API documentation
- Update deployment notes
- Tag release: `v2.0-sprint2-week1`

---

## Week 2: Safety Nets & Performance

### Day 1-2: Orphan Detection Job

**Goal:** Implement daily monitoring for orphaned events

Follow **ORPHAN_DETECTION_JOB.md** Section 3.

1. **Create job file** (1 hour)

```bash
mkdir -p scheduler_app/jobs
touch scheduler_app/jobs/__init__.py
touch scheduler_app/jobs/orphan_detection.py
```

Copy implementation from `ORPHAN_DETECTION_JOB.md` Section 3.1 into `orphan_detection.py`.

2. **Create notifications module** (30 minutes)

```bash
touch scheduler_app/notifications.py
```

Copy implementation from `ORPHAN_DETECTION_JOB.md` Section 3.2.

3. **Configure environment variables** (15 minutes)

```bash
# Add to .env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=scheduler@example.com
MAIL_PASSWORD=your_password
MAIL_DEFAULT_SENDER=noreply@scheduler.com
```

4. **Configure cron job** (15 minutes)

```bash
crontab -e

# Add:
0 2 * * * cd /path/to/flask-schedule-webapp && /usr/bin/python3 scheduler_app/jobs/orphan_detection.py >> logs/orphan_detection.log 2>&1
```

5. **Test with simulated orphans** (30 minutes)

Follow `ORPHAN_DETECTION_JOB.md` Section 7.2 to create test orphans and verify alerts work.

### Day 3: Performance Testing

**Goal:** Ensure calendar handles 1000+ events efficiently

1. **Generate load test data** (15 minutes)

```bash
python test_data/generate_load_test_data.py --count=1000 --month=2025-10
```

2. **Load data into test database** (5 minutes)

```bash
psql -U your_user -d scheduler_test -f test_data/load_test_data.sql
```

3. **Run performance benchmarks** (1 hour)

Follow **TEST_PLAN.md** TC-052:

```bash
# Use browser dev tools to measure:
# - Page load time (target: < 2 seconds)
# - Calendar render time (target: < 500ms)
# - Database query time (target: < 200ms)
```

4. **Optimize if needed** (2-4 hours)

If performance is slow:

```python
# Add Redis caching for calendar data

from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis', 'CACHE_REDIS_URL': 'redis://localhost:6379/0'})

@app.route('/api/calendar/<int:year>/<int:month>')
@cache.cached(timeout=300)  # Cache for 5 minutes
def get_calendar_data(year, month):
    # ... existing calendar query ...
    pass
```

### Day 4-5: Additional Enhancements

1. **Add undo functionality** (4 hours)

```python
# Create undo_history table
class UndoHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    action = db.Column(db.String(50))  # 'reschedule', 'unschedule'
    event_id = db.Column(db.Integer, db.ForeignKey('events.event_id'))
    old_state = db.Column(db.Text)  # JSON snapshot
    can_undo = db.Column(db.Boolean, default=True)
    undo_expires = db.Column(db.DateTime)  # 5 minutes from now
```

2. **Implement rate limiting** (2 hours)

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["1000 per day", "100 per hour"]
)

@app.route('/api/reschedule_event', methods=['POST'])
@limiter.limit("10 per minute")
def reschedule_event():
    # ... existing code ...
    pass
```

---

## Week 3: Frontend Implementation

### Day 1-2: Calendar Month View

**Goal:** Create full-screen calendar grid

Follow **FRONTEND_COMPONENT_CHECKLIST.md** Phase 1.

1. **Create calendar template** (2 hours)

```html
<!-- scheduler_app/templates/calendar_month.html -->
{% extends "base.html" %}

{% block content %}
<div class="calendar-container">
    <div class="calendar-header">
        <button id="prev-month" class="btn-nav">←</button>
        <h2 id="current-month-year">October 2025</h2>
        <button id="today" class="btn-today">Today</button>
        <button id="next-month" class="btn-nav">→</button>
    </div>

    <div class="calendar-grid">
        <div class="calendar-weekdays">
            <div class="weekday">Sun</div>
            <div class="weekday">Mon</div>
            <div class="weekday">Tue</div>
            <div class="weekday">Wed</div>
            <div class="weekday">Thu</div>
            <div class="weekday">Fri</div>
            <div class="weekday">Sat</div>
        </div>

        <div class="calendar-days" id="calendar-days">
            <!-- Days generated by JavaScript -->
        </div>
    </div>
</div>
{% endblock %}
```

2. **Add calendar CSS** (1 hour)

```css
/* scheduler_app/static/css/calendar.css */

.calendar-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

.calendar-grid {
    border: 1px solid #ddd;
    border-radius: 8px;
    overflow: hidden;
}

.calendar-weekdays {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    background: #f5f5f5;
    border-bottom: 1px solid #ddd;
}

.weekday {
    padding: 12px;
    text-align: center;
    font-weight: 600;
}

.calendar-days {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 1px;
    background: #ddd;
}

.calendar-day {
    background: white;
    min-height: 120px;
    padding: 8px;
    cursor: pointer;
    transition: background 0.2s;
}

.calendar-day:hover {
    background: #f9f9f9;
}

.calendar-day.today {
    background: #e3f2fd;
}

.day-number {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 8px;
}
```

3. **Add calendar JavaScript** (3 hours)

```javascript
// scheduler_app/static/js/calendar.js

class Calendar {
    constructor() {
        this.currentDate = new Date();
        this.selectedDate = null;
        this.events = {};

        this.init();
    }

    init() {
        this.bindEvents();
        this.render();
        this.fetchEvents();
    }

    bindEvents() {
        document.getElementById('prev-month').addEventListener('click', () => {
            this.currentDate.setMonth(this.currentDate.getMonth() - 1);
            this.render();
            this.fetchEvents();
        });

        document.getElementById('next-month').addEventListener('click', () => {
            this.currentDate.setMonth(this.currentDate.getMonth() + 1);
            this.render();
            this.fetchEvents();
        });

        document.getElementById('today').addEventListener('click', () => {
            this.currentDate = new Date();
            this.render();
            this.fetchEvents();
        });
    }

    render() {
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();

        // Update header
        const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                           'July', 'August', 'September', 'October', 'November', 'December'];
        document.getElementById('current-month-year').textContent = `${monthNames[month]} ${year}`;

        // Generate calendar days
        const firstDay = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const today = new Date();

        const daysContainer = document.getElementById('calendar-days');
        daysContainer.innerHTML = '';

        // Empty cells for days before month starts
        for (let i = 0; i < firstDay; i++) {
            const emptyDay = document.createElement('div');
            emptyDay.classList.add('calendar-day', 'empty');
            daysContainer.appendChild(emptyDay);
        }

        // Days of the month
        for (let day = 1; day <= daysInMonth; day++) {
            const dayElement = document.createElement('div');
            dayElement.classList.add('calendar-day');
            dayElement.dataset.date = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;

            // Check if today
            if (year === today.getFullYear() && month === today.getMonth() && day === today.getDate()) {
                dayElement.classList.add('today');
            }

            dayElement.innerHTML = `
                <div class="day-number">${day}</div>
                <div class="day-events" id="events-${year}-${month + 1}-${day}"></div>
            `;

            dayElement.addEventListener('click', () => {
                this.selectDate(dayElement.dataset.date);
            });

            daysContainer.appendChild(dayElement);
        }
    }

    async fetchEvents() {
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth() + 1;

        try {
            const response = await fetch(`/api/calendar/${year}/${month}`);
            const data = await response.json();

            this.events = data.events;
            this.renderEvents();
        } catch (error) {
            console.error('Failed to fetch events:', error);
        }
    }

    renderEvents() {
        // Render event badges for each day
        for (const [dateStr, dayEvents] of Object.entries(this.events)) {
            const container = document.getElementById(`events-${dateStr}`);
            if (container) {
                container.innerHTML = this.renderEventBadges(dayEvents);
            }
        }
    }

    renderEventBadges(dayEvents) {
        // Implement event badges (Phase 2)
        // ...
    }

    selectDate(dateStr) {
        // Navigate to daily view
        window.location.href = `/calendar/day/${dateStr}`;
    }
}

// Initialize calendar
document.addEventListener('DOMContentLoaded', () => {
    new Calendar();
});
```

### Day 3: Event Badges & Type Counts

Follow **FRONTEND_COMPONENT_CHECKLIST.md** Phase 2.

Implement color-coded badges and event type counts as specified in the UX mockup.

### Day 4-5: Daily View Page

Follow **FRONTEND_COMPONENT_CHECKLIST.md** Phase 3.

Create dedicated daily view page with grouped event cards and reschedule/unschedule buttons.

---

## Week 4: Testing & Deployment

### Day 1-2: Full Test Execution

Execute all test scenarios from **TEST_PLAN.md**:

- Functional tests (TC-001 to TC-028)
- CORE-Supervisor pairing tests (TC-033 to TC-051)
- Performance tests (TC-052 to TC-054)
- Accessibility tests (TC-056 to TC-061)
- Mobile responsive tests (TC-062 to TC-065)

### Day 3: Accessibility Audit

Follow **TEST_PLAN.md** TC-056 to TC-061:

- Keyboard navigation
- Screen reader testing
- Color contrast verification (WCAG AA)
- Focus indicators
- ARIA labels

### Day 4: Bug Fixes & Polish

- Fix all P0 and P1 bugs
- Code cleanup
- Performance tuning
- Documentation updates

### Day 5: Production Deployment

1. **Pre-deployment checklist:**

```markdown
- [ ] All P0 tests passing (100%)
- [ ] All P1 tests passing (≥ 95%)
- [ ] Zero critical bugs
- [ ] Transaction handling tested
- [ ] Orphan detection job configured
- [ ] Performance benchmarks met (< 2s page load)
- [ ] Accessibility audit passed
- [ ] Production database backup created
- [ ] Rollback plan documented
- [ ] Deployment runbook reviewed
```

2. **Deployment steps:**

```bash
# 1. Backup production database
pg_dump scheduler_production > backup_pre_calendar_redesign.sql

# 2. Apply database migrations
flask db upgrade

# 3. Apply database indexes
psql -U prod_user -d scheduler_production -f migrations/add_calendar_indexes.sql

# 4. Deploy application code
git checkout main
git merge feature/calendar-redesign
git push origin main

# 5. Restart application servers
systemctl restart scheduler-webapp

# 6. Configure orphan detection cron job
crontab -e  # Add orphan detection job

# 7. Smoke test
curl https://scheduler.example.com/calendar/2025/10
curl https://scheduler.example.com/calendar/day/2025-10-15

# 8. Monitor logs
tail -f logs/scheduler_app.log
tail -f logs/orphan_detection.log
```

3. **Post-deployment monitoring:**

- Monitor error rates (first 24 hours)
- Check orphan detection job runs successfully
- Verify performance metrics
- Collect user feedback

---

## Rollback Plan

### If Critical Issues Occur:

**Step 1: Immediate Rollback (< 5 minutes)**

```bash
# 1. Revert to previous application version
git revert HEAD
git push origin main
systemctl restart scheduler-webapp

# 2. Verify old version is running
curl https://scheduler.example.com/
```

**Step 2: Database Rollback (if needed)**

```bash
# 1. Restore pre-deployment backup
psql -U prod_user -d scheduler_production < backup_pre_calendar_redesign.sql

# 2. Downgrade database migrations
flask db downgrade
```

**Step 3: Disable Orphan Detection Job**

```bash
crontab -e  # Comment out orphan detection line
```

**Step 4: Communication**

- Notify users of rollback
- Post incident report
- Schedule root cause analysis

---

## FAQ

### Q: What if a CORE event doesn't have a matching Supervisor?

**A:** The transaction will succeed for the CORE event, and a warning will be logged. This is expected behavior for events that legitimately don't need supervision.

### Q: What if the orphan detection job finds orphans?

**A:** Follow the incident response procedure in `ORPHAN_DETECTION_JOB.md` Section 8.2:
1. Verify the alert
2. Investigate root cause
3. Fix the orphan manually
4. Document the incident

### Q: How do I test transaction rollback?

**A:** Follow **TEST_PLAN.md** TC-036:
1. Modify code to simulate database error
2. Attempt reschedule
3. Verify both CORE and Supervisor remain unchanged

### Q: Can I run this in staging first?

**A:** Absolutely! We highly recommend:
1. Deploy to staging environment
2. Run full test suite
3. Conduct UAT (User Acceptance Testing)
4. Monitor for 1 week
5. Then deploy to production

### Q: What's the performance target?

**A:** Calendar page should load in < 2 seconds with 1000 events. Use Redis caching and database indexing to achieve this.

---

## Support & Resources

**Documentation:**
- QA_DELIVERABLES_README.md
- DATABASE_TRANSACTION_GUIDE.md
- ORPHAN_DETECTION_JOB.md
- TEST_PLAN.md
- UX_MOCKUP_SPECIFICATION.md
- FRONTEND_COMPONENT_CHECKLIST.md

**Team Contacts:**
- QA Lead: Quinn
- Backend Lead: [Assign]
- Frontend Lead: [Assign]
- DevOps: [Assign]

**Issue Tracking:**
- GitHub Issues: [Link]
- Jira Board: [Link]

---

**Last Updated:** 2025-10-12
**Version:** 1.0
