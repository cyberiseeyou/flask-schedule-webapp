# Orphan Detection Job Specification
**Project:** Calendar Redesign - CORE-Supervisor Pairing Safety Net
**Version:** 1.0
**Created:** 2025-10-12
**Owner:** Backend Developer
**Timeline:** Sprint 2, Week 2

---

## 1. Purpose

This document specifies a **daily cron job** to detect orphaned CORE-Supervisor event pairs that may occur due to:

- Transaction rollback failures
- Manual database modifications
- Race conditions in concurrent operations
- Failed automatic pairing logic

The job serves as a **safety net** to catch data integrity issues before they impact scheduling operations.

---

## 2. Detection Criteria

### 2.1 Orphan Type 1: CORE and Supervisor on Different Dates

**Scenario:** A CORE event is rescheduled, but the paired Supervisor event remains on the original date.

**Detection Query:**
```sql
SELECT
    c.event_id AS core_event_id,
    c.project_name AS core_project_name,
    DATE(c.start_datetime) AS core_date,
    s.event_id AS supervisor_event_id,
    s.project_name AS supervisor_project_name,
    DATE(s.start_datetime) AS supervisor_date,
    DATEDIFF(c.start_datetime, s.start_datetime) AS days_apart
FROM events c
INNER JOIN events s ON SUBSTRING(c.project_name, 1, 6) = SUBSTRING(s.project_name, 1, 6)
WHERE c.project_name LIKE '%-CORE-%'
  AND s.project_name LIKE '%-Supervisor-%'
  AND c.condition = 'Scheduled'
  AND s.condition = 'Scheduled'
  AND DATE(c.start_datetime) != DATE(s.start_datetime)
ORDER BY ABS(DATEDIFF(c.start_datetime, s.start_datetime)) DESC;
```

**Expected Result:** 0 rows (empty result = no orphans)

---

### 2.2 Orphan Type 2: Scheduled CORE, Unscheduled Supervisor

**Scenario:** A CORE event is scheduled, but the paired Supervisor event remains unscheduled.

**Detection Query:**
```sql
SELECT
    c.event_id AS core_event_id,
    c.project_name AS core_project_name,
    c.condition AS core_condition,
    s.event_id AS supervisor_event_id,
    s.project_name AS supervisor_project_name,
    s.condition AS supervisor_condition
FROM events c
INNER JOIN events s ON SUBSTRING(c.project_name, 1, 6) = SUBSTRING(s.project_name, 1, 6)
WHERE c.project_name LIKE '%-CORE-%'
  AND s.project_name LIKE '%-Supervisor-%'
  AND c.condition = 'Scheduled'
  AND s.condition = 'Unstaffed';
```

**Expected Result:** 0 rows (empty result = no orphans)

---

### 2.3 Orphan Type 3: Unscheduled CORE, Scheduled Supervisor

**Scenario:** A CORE event is unscheduled, but the paired Supervisor event remains scheduled.

**Detection Query:**
```sql
SELECT
    c.event_id AS core_event_id,
    c.project_name AS core_project_name,
    c.condition AS core_condition,
    s.event_id AS supervisor_event_id,
    s.project_name AS supervisor_project_name,
    s.condition AS supervisor_condition
FROM events c
INNER JOIN events s ON SUBSTRING(c.project_name, 1, 6) = SUBSTRING(s.project_name, 1, 6)
WHERE c.project_name LIKE '%-CORE-%'
  AND s.project_name LIKE '%-Supervisor-%'
  AND c.condition = 'Unstaffed'
  AND s.condition = 'Scheduled';
```

**Expected Result:** 0 rows (empty result = no orphans)

---

## 3. Job Implementation

### 3.1 Python Implementation

**File:** `scheduler_app/jobs/orphan_detection.py`

```python
#!/usr/bin/env python3
"""
Orphan Detection Job - CORE-Supervisor Event Pairing Monitor

Runs daily to detect mismatched CORE-Supervisor event pairs.
Sends alerts via Slack and Email when orphans are detected.

Usage:
    python scheduler_app/jobs/orphan_detection.py

Cron (Daily at 2 AM):
    0 2 * * * cd /path/to/flask-schedule-webapp && python scheduler_app/jobs/orphan_detection.py >> logs/orphan_detection.log 2>&1
"""

import os
import sys
from datetime import datetime
from sqlalchemy import text

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from scheduler_app import create_app, db
from scheduler_app.notifications import send_slack_alert, send_email_alert

def detect_date_mismatches():
    """Detect CORE-Supervisor pairs on different dates."""
    query = text("""
        SELECT
            c.event_id AS core_event_id,
            c.project_name AS core_project_name,
            DATE(c.start_datetime) AS core_date,
            s.event_id AS supervisor_event_id,
            s.project_name AS supervisor_project_name,
            DATE(s.start_datetime) AS supervisor_date,
            DATEDIFF(c.start_datetime, s.start_datetime) AS days_apart
        FROM events c
        INNER JOIN events s ON SUBSTRING(c.project_name, 1, 6) = SUBSTRING(s.project_name, 1, 6)
        WHERE c.project_name LIKE '%-CORE-%'
          AND s.project_name LIKE '%-Supervisor-%'
          AND c.condition = 'Scheduled'
          AND s.condition = 'Scheduled'
          AND DATE(c.start_datetime) != DATE(s.start_datetime)
        ORDER BY ABS(DATEDIFF(c.start_datetime, s.start_datetime)) DESC
    """)

    result = db.session.execute(query)
    orphans = result.fetchall()
    return orphans

def detect_condition_mismatches_core_scheduled():
    """Detect scheduled CORE with unscheduled Supervisor."""
    query = text("""
        SELECT
            c.event_id AS core_event_id,
            c.project_name AS core_project_name,
            c.condition AS core_condition,
            s.event_id AS supervisor_event_id,
            s.project_name AS supervisor_project_name,
            s.condition AS supervisor_condition
        FROM events c
        INNER JOIN events s ON SUBSTRING(c.project_name, 1, 6) = SUBSTRING(s.project_name, 1, 6)
        WHERE c.project_name LIKE '%-CORE-%'
          AND s.project_name LIKE '%-Supervisor-%'
          AND c.condition = 'Scheduled'
          AND s.condition = 'Unstaffed'
    """)

    result = db.session.execute(query)
    orphans = result.fetchall()
    return orphans

def detect_condition_mismatches_supervisor_scheduled():
    """Detect unscheduled CORE with scheduled Supervisor."""
    query = text("""
        SELECT
            c.event_id AS core_event_id,
            c.project_name AS core_project_name,
            c.condition AS core_condition,
            s.event_id AS supervisor_event_id,
            s.project_name AS supervisor_project_name,
            s.condition AS supervisor_condition
        FROM events c
        INNER JOIN events s ON SUBSTRING(c.project_name, 1, 6) = SUBSTRING(s.project_name, 1, 6)
        WHERE c.project_name LIKE '%-CORE-%'
          AND s.project_name LIKE '%-Supervisor-%'
          AND c.condition = 'Unstaffed'
          AND s.condition = 'Scheduled'
    """)

    result = db.session.execute(query)
    orphans = result.fetchall()
    return orphans

def format_orphan_report(orphans, orphan_type):
    """Format orphan detection results into human-readable report."""
    if not orphans:
        return None

    report = f"\n🚨 **ORPHAN TYPE: {orphan_type}**\n"
    report += f"Found {len(orphans)} orphaned pair(s)\n\n"

    for i, orphan in enumerate(orphans, 1):
        report += f"**Pair {i}:**\n"
        if orphan_type == "DATE_MISMATCH":
            report += f"  - CORE: [{orphan.core_event_id}] {orphan.core_project_name} (Date: {orphan.core_date})\n"
            report += f"  - Supervisor: [{orphan.supervisor_event_id}] {orphan.supervisor_project_name} (Date: {orphan.supervisor_date})\n"
            report += f"  - Days Apart: {orphan.days_apart}\n\n"
        else:
            report += f"  - CORE: [{orphan.core_event_id}] {orphan.core_project_name} (Condition: {orphan.core_condition})\n"
            report += f"  - Supervisor: [{orphan.supervisor_event_id}] {orphan.supervisor_project_name} (Condition: {orphan.supervisor_condition})\n\n"

    return report

def send_alerts(report_text):
    """Send alerts via Slack and Email."""
    try:
        # Slack alert
        send_slack_alert(
            channel="#scheduling-alerts",
            message=f"⚠️ Orphan Detection Job Found Issues:\n{report_text}",
            username="Orphan Detection Bot",
            icon_emoji=":warning:"
        )
        print(f"✅ Slack alert sent successfully")
    except Exception as e:
        print(f"❌ Failed to send Slack alert: {e}")

    try:
        # Email alert
        send_email_alert(
            to=["admin@example.com", "scheduling@example.com"],
            subject="🚨 Orphaned CORE-Supervisor Events Detected",
            body=report_text,
            html=True
        )
        print(f"✅ Email alert sent successfully")
    except Exception as e:
        print(f"❌ Failed to send email alert: {e}")

def run_orphan_detection():
    """Main job execution function."""
    print(f"\n{'='*60}")
    print(f"Orphan Detection Job Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    app = create_app()

    with app.app_context():
        total_orphans = 0
        full_report = ""

        # Check Type 1: Date mismatches
        print("🔍 Checking for date mismatches...")
        date_orphans = detect_date_mismatches()
        if date_orphans:
            total_orphans += len(date_orphans)
            report = format_orphan_report(date_orphans, "DATE_MISMATCH")
            full_report += report
            print(f"❌ Found {len(date_orphans)} date mismatch(es)")
        else:
            print("✅ No date mismatches found")

        # Check Type 2: Scheduled CORE, Unscheduled Supervisor
        print("🔍 Checking for scheduled CORE with unscheduled Supervisor...")
        core_scheduled_orphans = detect_condition_mismatches_core_scheduled()
        if core_scheduled_orphans:
            total_orphans += len(core_scheduled_orphans)
            report = format_orphan_report(core_scheduled_orphans, "CORE_SCHEDULED_SUPERVISOR_UNSTAFFED")
            full_report += report
            print(f"❌ Found {len(core_scheduled_orphans)} mismatch(es)")
        else:
            print("✅ No condition mismatches found")

        # Check Type 3: Unscheduled CORE, Scheduled Supervisor
        print("🔍 Checking for unscheduled CORE with scheduled Supervisor...")
        supervisor_scheduled_orphans = detect_condition_mismatches_supervisor_scheduled()
        if supervisor_scheduled_orphans:
            total_orphans += len(supervisor_scheduled_orphans)
            report = format_orphan_report(supervisor_scheduled_orphans, "CORE_UNSTAFFED_SUPERVISOR_SCHEDULED")
            full_report += report
            print(f"❌ Found {len(supervisor_scheduled_orphans)} mismatch(es)")
        else:
            print("✅ No condition mismatches found")

        # Send alerts if orphans detected
        if total_orphans > 0:
            print(f"\n🚨 TOTAL ORPHANS DETECTED: {total_orphans}")
            send_alerts(full_report)
        else:
            print(f"\n✅ No orphans detected - all CORE-Supervisor pairs are synchronized")

    print(f"\n{'='*60}")
    print(f"Orphan Detection Job Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    try:
        run_orphan_detection()
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

---

### 3.2 Notification Module

**File:** `scheduler_app/notifications.py`

```python
"""
Notification utilities for sending alerts via Slack and Email
"""

import os
import requests
from flask_mail import Message
from scheduler_app import mail

def send_slack_alert(channel, message, username="Scheduler Bot", icon_emoji=":robot_face:"):
    """
    Send alert to Slack channel via webhook.

    Args:
        channel: Slack channel (e.g., "#scheduling-alerts")
        message: Alert message text
        username: Bot display name
        icon_emoji: Bot icon emoji
    """
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')

    if not webhook_url:
        raise ValueError("SLACK_WEBHOOK_URL environment variable not set")

    payload = {
        "channel": channel,
        "username": username,
        "icon_emoji": icon_emoji,
        "text": message
    }

    response = requests.post(webhook_url, json=payload)
    response.raise_for_status()

def send_email_alert(to, subject, body, html=False):
    """
    Send email alert via Flask-Mail.

    Args:
        to: List of recipient email addresses
        subject: Email subject line
        body: Email body text
        html: If True, body is treated as HTML
    """
    msg = Message(
        subject=subject,
        recipients=to,
        sender=os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@scheduler.com')
    )

    if html:
        msg.html = body
    else:
        msg.body = body

    mail.send(msg)
```

---

## 4. Cron Job Configuration

### 4.1 Linux/Mac Crontab

**Schedule:** Daily at 2:00 AM

```bash
# Edit crontab
crontab -e

# Add this line:
0 2 * * * cd /path/to/flask-schedule-webapp && /usr/bin/python3 scheduler_app/jobs/orphan_detection.py >> logs/orphan_detection.log 2>&1
```

### 4.2 Windows Task Scheduler

**Schedule:** Daily at 2:00 AM

```powershell
# Create scheduled task
schtasks /create /tn "OrphanDetection" /tr "C:\Python39\python.exe C:\flask-schedule-webapp\scheduler_app\jobs\orphan_detection.py" /sc daily /st 02:00
```

### 4.3 Docker/Kubernetes CronJob

**File:** `k8s/orphan-detection-cronjob.yaml`

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: orphan-detection
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM UTC
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: orphan-detection
            image: flask-schedule-webapp:latest
            command:
            - /bin/bash
            - -c
            - python scheduler_app/jobs/orphan_detection.py
            env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: url
            - name: SLACK_WEBHOOK_URL
              valueFrom:
                secretKeyRef:
                  name: slack-credentials
                  key: webhook-url
          restartPolicy: OnFailure
```

---

## 5. Environment Variables

### 5.1 Required Configuration

**File:** `.env` (add these variables)

```bash
# Slack webhook for alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Email configuration (Flask-Mail)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=scheduler@example.com
MAIL_PASSWORD=your_email_password
MAIL_DEFAULT_SENDER=noreply@scheduler.com

# Alert recipients
ALERT_EMAILS=admin@example.com,scheduling@example.com
```

### 5.2 Obtaining Slack Webhook URL

1. Go to https://api.slack.com/apps
2. Create new app → "From scratch"
3. Enable "Incoming Webhooks"
4. Click "Add New Webhook to Workspace"
5. Select channel (e.g., `#scheduling-alerts`)
6. Copy webhook URL

---

## 6. Logging

### 6.1 Log File Location

**Path:** `logs/orphan_detection.log`

**Format:**
```
============================================================
Orphan Detection Job Started: 2025-10-12 02:00:00
============================================================

🔍 Checking for date mismatches...
✅ No date mismatches found
🔍 Checking for scheduled CORE with unscheduled Supervisor...
✅ No condition mismatches found
🔍 Checking for unscheduled CORE with scheduled Supervisor...
✅ No condition mismatches found

✅ No orphans detected - all CORE-Supervisor pairs are synchronized

============================================================
Orphan Detection Job Completed: 2025-10-12 02:00:15
============================================================
```

### 6.2 Log Rotation

**File:** `logrotate.d/orphan-detection`

```
/path/to/flask-schedule-webapp/logs/orphan_detection.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
}
```

---

## 7. Testing the Job

### 7.1 Manual Test Run

```bash
# Run job manually
cd /path/to/flask-schedule-webapp
python scheduler_app/jobs/orphan_detection.py

# Expected output (if no orphans):
# ✅ No orphans detected - all CORE-Supervisor pairs are synchronized
```

### 7.2 Test with Simulated Orphans

**Create test orphans:**

```sql
-- Create CORE event on Oct 15
INSERT INTO events (event_id, project_name, event_type, condition, is_scheduled, estimated_hours, start_datetime, due_datetime, created_at)
VALUES (9001, '999999-CORE-Test Orphan', 'CORE', 'Scheduled', TRUE, 6.0, '2025-10-15 10:00:00', '2025-10-15', NOW());

INSERT INTO schedule (schedule_id, event_id, employee_id, start_datetime, created_at)
VALUES (9001, 9001, 101, '2025-10-15 10:00:00', NOW());

-- Create Supervisor event on Oct 20 (ORPHAN - 5 days apart)
INSERT INTO events (event_id, project_name, event_type, condition, is_scheduled, estimated_hours, start_datetime, due_datetime, created_at)
VALUES (9002, '999999-Supervisor-Test Orphan', 'Supervisor', 'Scheduled', TRUE, 0.08, '2025-10-20 12:00:00', '2025-10-20', NOW());

INSERT INTO schedule (schedule_id, event_id, employee_id, start_datetime, created_at)
VALUES (9002, 9002, 102, '2025-10-20 12:00:00', NOW());
```

**Run job:**

```bash
python scheduler_app/jobs/orphan_detection.py
```

**Expected output:**

```
🔍 Checking for date mismatches...
❌ Found 1 date mismatch(es)

🚨 TOTAL ORPHANS DETECTED: 1
✅ Slack alert sent successfully
✅ Email alert sent successfully
```

**Clean up test data:**

```sql
DELETE FROM schedule WHERE schedule_id IN (9001, 9002);
DELETE FROM events WHERE event_id IN (9001, 9002);
```

---

## 8. Monitoring and Maintenance

### 8.1 Success Criteria

- ✅ Job runs daily at 2:00 AM without errors
- ✅ Log file updated daily with execution results
- ✅ Alerts sent within 5 minutes when orphans detected
- ✅ Zero false positives (all detected orphans are legitimate issues)

### 8.2 Alert Response Procedure

**When an orphan is detected:**

1. **Verify the Alert**
   - Log into database
   - Run verification queries manually
   - Confirm orphan exists

2. **Investigate Root Cause**
   - Check application logs for transaction failures
   - Review recent reschedule/unschedule operations
   - Identify if manual database changes were made

3. **Fix the Orphan**
   - Use admin panel to manually reschedule/unschedule
   - OR run SQL update to synchronize events:
     ```sql
     -- Fix date mismatch (reschedule Supervisor to match CORE)
     UPDATE schedule s
     SET start_datetime = (
         SELECT sc.start_datetime
         FROM schedule sc
         WHERE sc.event_id = <CORE_EVENT_ID>
     )
     WHERE s.event_id = <SUPERVISOR_EVENT_ID>;
     ```

4. **Document the Incident**
   - Log issue in incident tracking system
   - Note root cause and resolution
   - Update test scenarios if new edge case discovered

### 8.3 Periodic Review

**Monthly:**
- Review orphan detection logs
- Count total orphans detected
- Analyze trends (are orphans increasing?)

**Quarterly:**
- Review alert thresholds
- Optimize SQL queries if performance degrades
- Update notification channels as team changes

---

## 9. Performance Considerations

### 9.1 Query Optimization

**Index Requirements:**

```sql
-- Ensure these indexes exist for fast query performance
CREATE INDEX idx_events_project_name ON events(project_name);
CREATE INDEX idx_events_condition ON events(condition);
CREATE INDEX idx_events_start_datetime ON events(start_datetime);
```

**Expected Query Execution Time:**
- Small dataset (< 1000 events): < 100ms
- Medium dataset (1000-10000 events): < 500ms
- Large dataset (10000+ events): < 2 seconds

### 9.2 Timeout Configuration

Set query timeout to prevent long-running queries from blocking:

```python
# In orphan_detection.py, add timeout to queries
query = text("SELECT ... WITH (QUERY_TIMEOUT=10000)")  # 10 second timeout
```

---

## 10. Appendix: Manual Verification Queries

### Query 1: Count All CORE-Supervisor Pairs

```sql
SELECT
    COUNT(*) as total_pairs
FROM events c
INNER JOIN events s ON SUBSTRING(c.project_name, 1, 6) = SUBSTRING(s.project_name, 1, 6)
WHERE c.project_name LIKE '%-CORE-%'
  AND s.project_name LIKE '%-Supervisor-%';
```

### Query 2: List All Synchronized Pairs

```sql
SELECT
    c.event_id AS core_id,
    c.project_name AS core_name,
    DATE(c.start_datetime) AS core_date,
    c.condition AS core_condition,
    s.event_id AS supervisor_id,
    s.project_name AS supervisor_name,
    DATE(s.start_datetime) AS supervisor_date,
    s.condition AS supervisor_condition,
    CASE
        WHEN DATE(c.start_datetime) = DATE(s.start_datetime)
         AND c.condition = s.condition
        THEN '✅ Synchronized'
        ELSE '❌ Out of Sync'
    END AS sync_status
FROM events c
INNER JOIN events s ON SUBSTRING(c.project_name, 1, 6) = SUBSTRING(s.project_name, 1, 6)
WHERE c.project_name LIKE '%-CORE-%'
  AND s.project_name LIKE '%-Supervisor-%'
ORDER BY sync_status, c.start_datetime;
```

### Query 3: Find CORE Events Without Supervisor

```sql
SELECT
    c.event_id,
    c.project_name,
    c.condition,
    DATE(c.start_datetime) AS event_date
FROM events c
WHERE c.project_name LIKE '%-CORE-%'
  AND NOT EXISTS (
      SELECT 1
      FROM events s
      WHERE SUBSTRING(s.project_name, 1, 6) = SUBSTRING(c.project_name, 1, 6)
        AND s.project_name LIKE '%-Supervisor-%'
  );
```

---

## 11. Change Log

| Date       | Version | Author        | Changes                          |
|------------|---------|---------------|----------------------------------|
| 2025-10-12 | 1.0     | QA Architect  | Initial specification created    |

---

## 12. Approval

| Role                  | Name          | Signature | Date       |
|-----------------------|---------------|-----------|------------|
| Backend Developer     | _____________  |           |            |
| QA Lead               | Quinn         | ✓         | 2025-10-12 |
| Product Manager       | _____________  |           |            |

---

**END OF SPECIFICATION**
