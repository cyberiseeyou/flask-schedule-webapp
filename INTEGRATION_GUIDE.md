# Integration Guide: Daily Validation Dashboard & Automated Audit System

## Overview
This guide explains how to integrate the three new components into your Flask scheduling webapp:

1. **Daily Manager Workflow** (Documentation) - Already complete, no integration needed
2. **Daily Validation Dashboard** (Web UI) - Requires route registration and navigation
3. **Automated Audit System** (Background tasks) - Requires database migration and Celery configuration

---

## Part 1: Daily Validation Dashboard Integration

### Step 1: Register the Dashboard Blueprint

**File**: `scheduler_app/__init__.py` or your main app factory

**Add the following**:

```python
# Import the dashboard blueprint
from routes.dashboard import dashboard_bp

# Register blueprint (add alongside other blueprint registrations)
app.register_blueprint(dashboard_bp)
```

**Example**:
```python
def create_app(config_name='default'):
    app = Flask(__name__)

    # ... existing config ...

    # Register blueprints
    from routes.main import main_bp
    from routes.scheduling import scheduling_bp
    from routes.employees import employees_bp
    from routes.auto_scheduler import auto_scheduler_bp
    from routes.dashboard import dashboard_bp  # NEW

    app.register_blueprint(main_bp)
    app.register_blueprint(scheduling_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(auto_scheduler_bp)
    app.register_blueprint(dashboard_bp)  # NEW

    return app
```

---

### Step 2: Add Navigation Link

**File**: `scheduler_app/templates/base.html`

**Find the navigation menu** and add a link to the dashboard:

```html
<nav class="navbar navbar-expand-lg navbar-dark bg-dark">
    <div class="container-fluid">
        <a class="navbar-brand" href="/">Scheduler</a>
        <ul class="navbar-nav">
            <li class="nav-item">
                <a class="nav-link" href="/">Dashboard</a>
            </li>
            <!-- NEW: Add Daily Validation link -->
            <li class="nav-item">
                <a class="nav-link" href="/dashboard/daily-validation">Daily Validation</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="/calendar">Calendar</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="/auto-scheduler">Auto-Scheduler</a>
            </li>
            <!-- ... rest of navigation ... -->
        </ul>
    </div>
</nav>
```

---

### Step 3: Test the Dashboard

1. **Start your Flask app**:
   ```bash
   python run.py  # or your app entry point
   ```

2. **Navigate to the dashboard**:
   ```
   http://localhost:5000/dashboard/daily-validation
   ```

3. **Verify**:
   - Page loads without errors
   - Today's event counts display correctly
   - Rotation assignments show
   - Validation issues appear (if any)
   - Health score calculates

---

## Part 2: Automated Audit System Integration

### Step 1: Create Database Migration

The audit system requires new database tables. Create a migration:

**Using Flask-Migrate**:

```bash
# Generate migration
flask db migrate -m "Add audit log tables"

# Review the generated migration file at migrations/versions/XXXXX_add_audit_log_tables.py
# Make sure it includes:
# - audit_logs table
# - audit_notification_settings table

# Apply migration
flask db upgrade
```

**Or manually create the tables** (if not using Flask-Migrate):

```sql
-- audit_logs table
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    audit_date DATE NOT NULL,
    audit_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_issues INTEGER DEFAULT 0,
    critical_issues INTEGER DEFAULT 0,
    warning_issues INTEGER DEFAULT 0,
    info_issues INTEGER DEFAULT 0,
    summary TEXT,
    details_json TEXT,
    notification_sent BOOLEAN DEFAULT FALSE,
    notification_sent_at TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(100)
);

CREATE INDEX idx_audit_date_timestamp ON audit_logs(audit_date, audit_timestamp);
CREATE INDEX idx_audit_logs_date ON audit_logs(audit_date);

-- audit_notification_settings table
CREATE TABLE audit_notification_settings (
    id SERIAL PRIMARY KEY,
    email_recipients TEXT,
    notify_on_critical BOOLEAN DEFAULT TRUE,
    notify_on_warning BOOLEAN DEFAULT FALSE,
    notify_on_info BOOLEAN DEFAULT FALSE,
    notification_time TIME DEFAULT '06:00:00',
    notification_days VARCHAR(50) DEFAULT '1,2,3,4,5',
    include_details BOOLEAN DEFAULT TRUE,
    include_action_items BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### Step 2: Register Audit Models

**File**: `scheduler_app/models/__init__.py`

**Add audit model imports and registration**:

```python
from models.audit import create_audit_models

def init_models(app, db):
    """Initialize all models with app and db instances"""

    # ... existing model initialization ...

    # NEW: Initialize audit models
    AuditLog, AuditNotificationSettings = create_audit_models(db)

    # Register in app config
    app.config['AuditLog'] = AuditLog
    app.config['AuditNotificationSettings'] = AuditNotificationSettings

    return {
        'Event': Event,
        'Employee': Employee,
        'Schedule': Schedule,
        # ... other models ...
        'AuditLog': AuditLog,  # NEW
        'AuditNotificationSettings': AuditNotificationSettings,  # NEW
    }
```

---

### Step 3: Configure Celery

**File**: `scheduler_app/celery_config.py` (create if doesn't exist)

```python
from celery import Celery
from celery.schedules import crontab

def make_celery(app):
    """Create Celery instance with Flask app context"""
    celery = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL'],
        backend=app.config['CELERY_RESULT_BACKEND']
    )

    celery.conf.update(app.config)

    # Configure periodic tasks
    celery.conf.beat_schedule = {
        # Daily audit at 6:00 AM every weekday
        'daily-audit': {
            'task': 'tasks.run_daily_audit',
            'schedule': crontab(hour=6, minute=0, day_of_week='1-5'),  # Mon-Fri at 6 AM
        },

        # Event import audit at 8:00 AM every weekday
        'audit-event-import': {
            'task': 'tasks.audit_event_import',
            'schedule': crontab(hour=8, minute=0, day_of_week='1-5'),  # Mon-Fri at 8 AM
        },

        # Rotation coverage check every Sunday at 9:00 AM
        'check-rotation-coverage': {
            'task': 'tasks.check_rotation_coverage',
            'schedule': crontab(hour=9, minute=0, day_of_week=0),  # Sunday at 9 AM
        },

        # Weekly audit report every Monday at 7:00 AM
        'weekly-audit-report': {
            'task': 'tasks.generate_weekly_audit_report',
            'schedule': crontab(hour=7, minute=0, day_of_week=1),  # Monday at 7 AM
        },
    }

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
```

**File**: `scheduler_app/__init__.py` or your app factory

```python
from celery_config import make_celery

def create_app(config_name='default'):
    app = Flask(__name__)

    # Celery configuration
    app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'  # Or your broker
    app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

    # ... rest of app initialization ...

    # Create Celery instance
    celery = make_celery(app)

    return app, celery
```

---

### Step 4: Install Dependencies

**Add to `requirements.txt`** (if not already present):

```
celery>=5.3.0
redis>=5.0.0  # Or your preferred broker (RabbitMQ, etc.)
```

**Install**:

```bash
pip install celery redis
```

---

### Step 5: Start Celery Worker and Beat

You need TWO Celery processes:
1. **Worker**: Executes tasks
2. **Beat**: Scheduler that triggers tasks at configured times

**Terminal 1 - Start Celery Worker**:

```bash
celery -A scheduler_app.celery worker --loglevel=info
```

**Terminal 2 - Start Celery Beat (Scheduler)**:

```bash
celery -A scheduler_app.celery beat --loglevel=info
```

**Or combine both** (for development):

```bash
celery -A scheduler_app.celery worker --beat --loglevel=info
```

---

### Step 6: Configure Notification Settings

**Create initial notification settings** (run once):

```python
# Python shell or migration script
from scheduler_app import create_app, db
from models.audit import create_audit_models

app = create_app()
AuditLog, AuditNotificationSettings = create_audit_models(db)

with app.app_context():
    settings = AuditNotificationSettings(
        email_recipients='manager@example.com,supervisor@example.com',
        notify_on_critical=True,
        notify_on_warning=True,
        notify_on_info=False,
        notification_time='06:00:00',
        notification_days='1,2,3,4,5',  # Monday-Friday
        is_active=True
    )
    db.session.add(settings)
    db.session.commit()
    print("Notification settings created")
```

---

### Step 7: Test the Audit System

**Manual test** (trigger audit immediately):

```python
from scheduler_app import create_app
from services.daily_audit_checker import DailyAuditChecker
from datetime import date

app = create_app()
with app.app_context():
    db = app.extensions['sqlalchemy']
    models = app.config

    checker = DailyAuditChecker(db.session, models)
    result = checker.run_daily_audit(date.today())

    print(f"Audit complete!")
    print(f"Total issues: {result['total_issues']}")
    print(f"Critical: {result['critical_issues']}")
    print(f"Summary: {result['summary']}")
```

**Or trigger via Celery task**:

```python
from tasks.audit_tasks import run_daily_audit

# Execute immediately
result = run_daily_audit.delay()
print(result.get())  # Wait for result
```

---

## Part 3: Email Configuration (Optional)

To enable email notifications, configure Flask-Mail:

### Install Flask-Mail

```bash
pip install Flask-Mail
```

### Configure in App

**File**: `scheduler_app/__init__.py`

```python
from flask_mail import Mail

mail = Mail()

def create_app(config_name='default'):
    app = Flask(__name__)

    # Email configuration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Or your SMTP server
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'your-email@example.com'
    app.config['MAIL_PASSWORD'] = 'your-password'  # Use environment variable!
    app.config['MAIL_DEFAULT_SENDER'] = 'scheduler@example.com'

    # Initialize mail
    mail.init_app(app)

    # ... rest of app initialization ...

    return app
```

### Implement Email Sending

**File**: `scheduler_app/services/daily_audit_checker.py`

**Replace the `send_audit_notification` method**:

```python
def send_audit_notification(self, audit_result: Dict, recipients: List[str]):
    """Send audit results via email"""
    from flask import current_app
    from flask_mail import Message

    try:
        subject = f"Daily Scheduling Audit - {audit_result['date']}"

        if audit_result['critical_issues'] > 0:
            subject = f"🚨 URGENT: {subject}"

        # Build HTML email body
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Daily Audit Report for {audit_result['date']}</h2>

            <p><strong>{audit_result['summary']}</strong></p>

            <table style="border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Total Issues:</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{audit_result['total_issues']}</td>
                </tr>
                <tr style="background-color: #ffebee;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Critical:</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{audit_result['critical_issues']}</td>
                </tr>
                <tr style="background-color: #fff3e0;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Warnings:</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{audit_result['warning_issues']}</td>
                </tr>
                <tr style="background-color: #e1f5fe;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Info:</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{audit_result['info_issues']}</td>
                </tr>
            </table>

            <h3>Issue Details:</h3>
            <ul>
        """

        for issue in audit_result['issues']:
            severity_color = {
                'critical': '#d32f2f',
                'warning': '#f57c00',
                'info': '#0288d1'
            }.get(issue['severity'], '#666')

            body_html += f"""
            <li style="margin-bottom: 15px;">
                <span style="background: {severity_color}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px;">
                    {issue['severity'].upper()}
                </span>
                <strong>{issue['message']}</strong><br>
                <em style="color: #666;">Action: {issue['action']}</em>
            </li>
            """

        body_html += """
            </ul>

            <p style="margin-top: 30px; color: #666; font-size: 14px;">
                View full dashboard: <a href="http://your-domain.com/dashboard/daily-validation">Daily Validation Dashboard</a>
            </p>
        </body>
        </html>
        """

        # Send email
        msg = Message(
            subject,
            recipients=recipients,
            html=body_html
        )

        from flask_mail import mail
        mail.send(msg)

        logger.info(f"Audit notification sent to {len(recipients)} recipient(s)")

    except Exception as e:
        logger.error(f"Failed to send audit notification: {e}")
```

---

## Part 4: Production Deployment

### Supervisor Configuration (Linux)

**File**: `/etc/supervisor/conf.d/scheduler-celery.conf`

```ini
[program:scheduler-celery-worker]
command=/path/to/venv/bin/celery -A scheduler_app.celery worker --loglevel=info
directory=/path/to/flask-schedule-webapp
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/celery/worker.err.log
stdout_logfile=/var/log/celery/worker.out.log

[program:scheduler-celery-beat]
command=/path/to/venv/bin/celery -A scheduler_app.celery beat --loglevel=info
directory=/path/to/flask-schedule-webapp
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/celery/beat.err.log
stdout_logfile=/var/log/celery/beat.out.log
```

**Reload Supervisor**:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start scheduler-celery-worker
sudo supervisorctl start scheduler-celery-beat
```

---

### Windows Service (Windows Production)

**Use NSSM** (Non-Sucking Service Manager):

1. Download NSSM: https://nssm.cc/download
2. Install Celery Worker as service:

```cmd
nssm install SchedulerCeleryWorker "C:\path\to\venv\Scripts\celery.exe" "-A scheduler_app.celery worker --loglevel=info"
nssm set SchedulerCeleryWorker AppDirectory "C:\path\to\flask-schedule-webapp"
nssm start SchedulerCeleryWorker
```

3. Install Celery Beat as service:

```cmd
nssm install SchedulerCeleryBeat "C:\path\to\venv\Scripts\celery.exe" "-A scheduler_app.celery beat --loglevel=info"
nssm set SchedulerCeleryBeat AppDirectory "C:\path\to\flask-schedule-webapp"
nssm start SchedulerCeleryBeat
```

---

## Part 5: Monitoring and Maintenance

### View Audit Logs

**Create an audit log viewer page** (optional):

**File**: `scheduler_app/routes/dashboard.py`

Add this route:

```python
@dashboard_bp.route('/audit-logs')
def audit_logs():
    """View historical audit logs"""
    db = current_app.extensions['sqlalchemy']
    AuditLog = current_app.config.get('AuditLog')

    if not AuditLog:
        return "Audit logs not available", 404

    # Get last 30 days of logs
    logs = db.session.query(AuditLog).order_by(
        AuditLog.audit_date.desc(),
        AuditLog.audit_timestamp.desc()
    ).limit(30).all()

    return render_template('dashboard/audit_logs.html', logs=logs)
```

### Monitor Celery Tasks

**Flower** (Celery monitoring tool):

```bash
pip install flower
flower -A scheduler_app.celery --port=5555
```

Access at: `http://localhost:5555`

---

## Troubleshooting

### Issue: Dashboard shows no data

**Solution**: Check database models are registered:

```python
python
>>> from scheduler_app import create_app
>>> app = create_app()
>>> print(app.config.keys())
# Should include 'AuditLog', 'AuditNotificationSettings'
```

### Issue: Celery tasks not running

**Check**:
1. Is Celery worker running? (`celery status`)
2. Is Redis/broker accessible? (`redis-cli ping`)
3. Check logs: `/var/log/celery/` or console output

### Issue: Audit notifications not sending

**Check**:
1. Is email configured correctly?
2. Are notification settings active in database?
3. Check Celery logs for errors

### Issue: Dashboard route not found (404)

**Check**:
1. Is dashboard blueprint registered?
2. Restart Flask app after adding blueprint
3. Check route: `/dashboard/daily-validation` (not `/daily-validation`)

---

## Summary Checklist

### Daily Validation Dashboard
- [ ] Register `dashboard_bp` blueprint in app factory
- [ ] Add navigation link to `base.html`
- [ ] Test dashboard at `/dashboard/daily-validation`

### Automated Audit System
- [ ] Create database migration for audit tables
- [ ] Run migration (`flask db upgrade`)
- [ ] Register audit models in `models/__init__.py`
- [ ] Configure Celery in app
- [ ] Install Celery and Redis
- [ ] Start Celery worker and beat
- [ ] Configure notification settings
- [ ] Test audit manually

### Optional
- [ ] Configure Flask-Mail for email notifications
- [ ] Set up Supervisor/NSSM for production
- [ ] Install Flower for Celery monitoring
- [ ] Create audit log viewer page

---

## Next Steps

1. **Integrate the Dashboard** (10 minutes)
   - Register blueprint, add navigation, test

2. **Set Up Audit System** (30 minutes)
   - Database migration, Celery setup, test

3. **Configure Notifications** (15 minutes)
   - Email settings, notification preferences

4. **Train Staff** (30 minutes)
   - Walk through Daily Manager Workflow
   - Show how to use dashboard
   - Explain audit notifications

5. **Monitor for 1 Week** (ongoing)
   - Review daily audit results
   - Adjust notification thresholds
   - Fix recurring issues

---

**Questions or Issues?**
- Check logs: `/var/log/celery/` or Flask app logs
- Review Celery documentation: https://docs.celeryproject.org/
- Check Flask-Mail docs: https://pythonhosted.org/Flask-Mail/

**Good luck!** Your scheduling system now has automated health monitoring and daily validation.
