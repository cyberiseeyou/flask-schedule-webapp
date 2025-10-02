# Printing, Settings, and Analytics Enhancements - Epic-Level Architecture

**Version:** 1.0
**Date:** 2025-10-01
**Status:** Design Phase

---

## Executive Summary

This document outlines the architectural design for five major feature enhancements to the Flask Schedule Webapp:

1. **Flexible Date-Based Printing** - Replace fixed today/tomorrow buttons with date picker
2. **Per-Event Paperwork Printing** - Print individual event paperwork on-demand
3. **Settings Management Page** - Configure credentials, auto-scheduler behavior
4. **Single-Event Auto-Scheduling** - Auto-schedule individual events on-demand
5. **Employee Analytics & Printing** - View schedules, print employee-specific paperwork
6. **Mobile Responsiveness** - Ensure all features work on mobile devices

---

## Current System Analysis

### Existing Printing Infrastructure

**Current Print Paperwork Flow** (`admin.py:914-1200`):
```
1. Schedule Page (HTML -> PDF) - All events for target date
2. For EACH Core event:
   a. EDR Report (Walmart Retail-Link API)
   b. Sales Tool PDF (downloaded from event.sales_tools_url)
   c. Activity Log PDF (static: docs/Event Table Activity Log.pdf)
   d. Checklist PDF (static: docs/Daily Task Checkoff Sheet.pdf)
3. Daily Item Numbers Page (aggregated from all EDR reports)
```

**Key Components:**
- **EDR Generator** (`services/edr_generator.py`) - Walmart Retail-Link integration
- **PDF Libraries:** PyPDF2, reportlab, xhtml2pdf
- **Session Caching:** EDR authentication token cached in Flask session
- **Config-based Credentials:** WALMART_EDR_USERNAME, WALMART_EDR_PASSWORD, WALMART_EDR_MFA_CREDENTIAL_ID

### Existing Auto-Scheduler

**Scheduling Engine** (`services/scheduling_engine.py`):
- Class-based design with validation and rotation logic
- Supports all event types: Core, Supervisor, Digital, Freeosk, Juicer, Other
- Rotation-aware scheduling (Primary Juicer, Primary/Secondary Lead)
- Constraint validation (time-off, availability, role restrictions)
- Pending schedule workflow (propose → review → approve)

**Auto-Scheduler Routes** (`routes/auto_scheduler.py`):
- `/run_scheduler` - Manual trigger for batch scheduling
- `/approve` - Approve pending schedules and submit to Crossmark API
- Supports 3-week lookahead window

---

## Feature 1: Flexible Date-Based Printing

### User Story
**As a** scheduler,
**I want to** select any date and print paperwork for that day,
**So that** I can prepare paperwork ahead of time or review historical schedules.

### Design Overview

**Current State:**
```
[Print Today's Paperwork] [Print Tomorrow's Paperwork]
```

**New State:**
```
Select Date: [Date Picker: ____] [Print Paperwork]
```

### Technical Approach

**Frontend Changes** (`templates/index.html`):
```html
<!-- Replace static buttons with date picker -->
<div class="print-controls">
  <label for="paperwork-date">Select Date:</label>
  <input type="date" id="paperwork-date" value="[today's date]">
  <button id="print-paperwork-btn" class="btn btn-primary">
    Print Paperwork
  </button>
</div>

<script>
// JavaScript handler
document.getElementById('print-paperwork-btn').addEventListener('click', function() {
    const selectedDate = document.getElementById('paperwork-date').value;
    window.open(`/api/print_paperwork_by_date/${selectedDate}`, '_blank');
});
</script>
```

**Backend Changes** (`routes/admin.py`):
```python
@admin_bp.route('/api/print_paperwork_by_date/<date_str>')
def print_paperwork_by_date(date_str):
    """
    Print paperwork for any selected date
    date_str: YYYY-MM-DD format
    """
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    # Reuse existing print_paperwork logic with target_date parameter
    return _generate_paperwork_pdf(target_date)

def _generate_paperwork_pdf(target_date):
    """
    Refactored paperwork generation logic
    (Extract from existing print_paperwork function)
    """
    # ... existing logic ...
```

**Key Design Decisions:**
- ✅ Reuse existing PDF generation logic - no duplication
- ✅ Maintain backward compatibility - keep existing today/tomorrow endpoints if needed
- ✅ Date validation prevents invalid inputs
- ✅ HTML5 date picker for native UX

### Integration Points
- **No external API changes** - uses existing EDR and PDF generation
- **No database schema changes** - queries existing schedules table

---

## Feature 2: Per-Event Paperwork Printing

### User Story
**As a** scheduler,
**I want to** print paperwork for a single event,
**So that** I can reprint or preview documents without printing the entire daily batch.

### Design Overview

**Location:** Events page, each unscheduled/scheduled event

**Current State:**
```
Event Details | [Schedule] [Edit] [Delete]
```

**New State:**
```
Event Details | [Schedule] [Edit] [Delete] [Print Event Paperwork]
```

### Technical Approach

**The "4 Pieces" for Individual Events:**
1. EDR Report
2. Sales Tool PDF
3. Activity Log
4. Checklist

**Exclusions (vs Daily Paperwork):**
- ❌ Schedule page (not applicable for single event)
- ❌ Daily Item Numbers page (aggregation not needed)

**Frontend Changes** (`templates/unscheduled.html` and `templates/scheduled.html`):
```html
<!-- Add print button to event action row -->
<button class="btn btn-sm btn-secondary"
        onclick="printEventPaperwork('{{ event.id }}')">
    <i class="icon-print"></i> Print Paperwork
</button>

<script>
function printEventPaperwork(eventId) {
    window.open(`/api/print_event_paperwork/${eventId}`, '_blank');
}
</script>
```

**Backend Changes** (`routes/admin.py`):
```python
@admin_bp.route('/api/print_event_paperwork/<int:event_id>')
def print_event_paperwork(event_id):
    """
    Print paperwork for a single event (4 pieces)
    Structure: EDR -> Sales Tool -> Activity Log -> Checklist
    (No schedule page, no item numbers aggregation)
    """
    db = current_app.extensions['sqlalchemy']
    Event = current_app.config['Event']
    Employee = current_app.config['Employee']
    Schedule = current_app.config['Schedule']

    # Get event and its schedule
    event_query = db.session.query(
        Event.project_name,
        Event.sales_tools_url,
        Event.location_mvid,
        Employee.name.label('employee_name')
    ).join(
        Schedule, Event.project_ref_num == Schedule.event_ref_num
    ).join(
        Employee, Schedule.employee_id == Employee.id
    ).filter(Event.id == event_id).first()

    if not event_query:
        return jsonify({'error': 'Event not found or not scheduled'}), 404

    # Initialize PDF writer
    pdf_writer = PdfWriter()

    # Initialize EDR generator
    edr_generator = _initialize_edr_generator()

    # 1. Add EDR Report
    event_number = extract_event_number(event_query.project_name)
    if event_number and edr_generator:
        edr_pdf = _generate_edr_pdf(edr_generator, event_number, event_query.employee_name)
        if edr_pdf:
            for page in edr_pdf.pages:
                pdf_writer.add_page(page)

    # 2. Add Sales Tool PDF
    sales_tool_pdf = _download_and_add_pdf(event_query.sales_tools_url)
    if sales_tool_pdf:
        for page in sales_tool_pdf.pages:
            pdf_writer.add_page(page)

    # 3. Add Activity Log (static PDF)
    activity_log_pdf = PdfReader('docs/Event Table Activity Log.pdf')
    for page in activity_log_pdf.pages:
        pdf_writer.add_page(page)

    # 4. Add Checklist (static PDF)
    checklist_pdf = PdfReader('docs/Daily Task Checkoff Sheet.pdf')
    for page in checklist_pdf.pages:
        pdf_writer.add_page(page)

    # Return combined PDF
    output = BytesIO()
    pdf_writer.write(output)
    output.seek(0)

    return send_file(
        output,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'Event_{event_number}_Paperwork.pdf'
    )
```

**Key Design Decisions:**
- ✅ Reuse existing PDF generation helpers - extract common functions
- ✅ Maintain same document order as daily paperwork
- ✅ Handle unscheduled events gracefully (show error or allow without schedule)
- ✅ Event-specific filename for easy identification

### Integration Points
- **Reuses EDR Generator** - same authentication flow
- **Reuses PDF utilities** - _download_and_add_pdf, _generate_edr_pdf
- **No new database tables** - queries existing Events/Schedules

---

## Feature 3: Settings Management Page

### User Story
**As a** scheduler administrator,
**I want to** manage system settings in one place,
**So that** I can configure credentials and auto-scheduler behavior without code changes.

### Design Overview

**New Page:** `/admin/settings`

**Settings Categories:**

1. **Retail-Link Credentials**
   - EDR Username
   - EDR Password (masked input)
   - MFA Credential ID

2. **Auto-Scheduler Configuration**
   - Enable/Disable automatic runs (checkbox)
   - Require user approval before changes (checkbox)

### Technical Approach

**Database Schema - New Table:**
```sql
CREATE TABLE system_settings (
    id INTEGER PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(50), -- 'string', 'boolean', 'encrypted'
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100)
);

-- Initial settings
INSERT INTO system_settings (setting_key, setting_value, setting_type, description) VALUES
('edr_username', NULL, 'string', 'Walmart Retail-Link EDR Username'),
('edr_password', NULL, 'encrypted', 'Walmart Retail-Link EDR Password (encrypted)'),
('edr_mfa_credential_id', NULL, 'string', 'Walmart Retail-Link MFA Credential ID'),
('auto_scheduler_enabled', 'true', 'boolean', 'Enable automatic scheduler runs'),
('auto_scheduler_require_approval', 'true', 'boolean', 'Require user approval before scheduling changes');
```

**Model** (`models.py`):
```python
class SystemSetting(db.Model):
    __tablename__ = 'system_settings'

    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text)
    setting_type = db.Column(db.String(50))
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_by = db.Column(db.String(100))

    @staticmethod
    def get_setting(key, default=None):
        setting = SystemSetting.query.filter_by(setting_key=key).first()
        if not setting:
            return default

        # Type conversion
        if setting.setting_type == 'boolean':
            return setting.setting_value.lower() == 'true'
        elif setting.setting_type == 'encrypted':
            return _decrypt_value(setting.setting_value)
        else:
            return setting.setting_value

    @staticmethod
    def set_setting(key, value, setting_type='string', user='system'):
        setting = SystemSetting.query.filter_by(setting_key=key).first()

        # Encrypt if needed
        if setting_type == 'encrypted':
            value = _encrypt_value(value)
        elif setting_type == 'boolean':
            value = str(value).lower()

        if setting:
            setting.setting_value = value
            setting.updated_at = datetime.utcnow()
            setting.updated_by = user
        else:
            setting = SystemSetting(
                setting_key=key,
                setting_value=value,
                setting_type=setting_type,
                updated_by=user
            )
            db.session.add(setting)

        db.session.commit()
```

**Encryption Helper** (`utils/encryption.py`):
```python
from cryptography.fernet import Fernet
from flask import current_app

def _get_encryption_key():
    """Get encryption key from app config or generate if missing"""
    key = current_app.config.get('SETTINGS_ENCRYPTION_KEY')
    if not key:
        # Generate and save key (one-time setup)
        key = Fernet.generate_key()
        current_app.logger.warning("Generated new encryption key - store in config!")
    return key

def _encrypt_value(plain_text):
    if not plain_text:
        return None
    f = Fernet(_get_encryption_key())
    return f.encrypt(plain_text.encode()).decode()

def _decrypt_value(encrypted_text):
    if not encrypted_text:
        return None
    f = Fernet(_get_encryption_key())
    return f.decrypt(encrypted_text.encode()).decode()
```

**Frontend** (`templates/settings.html`):
```html
<!DOCTYPE html>
<html>
<head>
    <title>System Settings</title>
    <!-- Include existing styles -->
</head>
<body>
    <div class="container">
        <h1>System Settings</h1>

        <form method="POST" action="/admin/settings">
            <!-- Retail-Link Credentials Section -->
            <div class="settings-section">
                <h2>Retail-Link Credentials</h2>
                <p class="help-text">Configure Walmart Retail-Link EDR authentication</p>

                <div class="form-group">
                    <label for="edr_username">EDR Username:</label>
                    <input type="text" id="edr_username" name="edr_username"
                           value="{{ settings.edr_username }}" class="form-control">
                </div>

                <div class="form-group">
                    <label for="edr_password">EDR Password:</label>
                    <input type="password" id="edr_password" name="edr_password"
                           placeholder="••••••••" class="form-control">
                    <small class="form-text">Leave blank to keep current password</small>
                </div>

                <div class="form-group">
                    <label for="edr_mfa_credential_id">MFA Credential ID:</label>
                    <input type="text" id="edr_mfa_credential_id" name="edr_mfa_credential_id"
                           value="{{ settings.edr_mfa_credential_id }}" class="form-control">
                </div>
            </div>

            <!-- Auto-Scheduler Configuration Section -->
            <div class="settings-section">
                <h2>Auto-Scheduler Configuration</h2>
                <p class="help-text">Control automatic scheduling behavior</p>

                <div class="form-check">
                    <input type="checkbox" id="auto_scheduler_enabled"
                           name="auto_scheduler_enabled" value="true"
                           {% if settings.auto_scheduler_enabled %}checked{% endif %}
                           class="form-check-input">
                    <label for="auto_scheduler_enabled" class="form-check-label">
                        Enable Automatic Scheduler Runs
                    </label>
                    <small class="form-text">When enabled, scheduler runs daily at 2 AM</small>
                </div>

                <div class="form-check">
                    <input type="checkbox" id="auto_scheduler_require_approval"
                           name="auto_scheduler_require_approval" value="true"
                           {% if settings.auto_scheduler_require_approval %}checked{% endif %}
                           class="form-check-input">
                    <label for="auto_scheduler_require_approval" class="form-check-label">
                        Require User Approval Before Changes
                    </label>
                    <small class="form-text">When enabled, proposed schedules must be reviewed before submission to Crossmark</small>
                </div>
            </div>

            <div class="form-actions">
                <button type="submit" class="btn btn-primary">Save Settings</button>
                <a href="/" class="btn btn-secondary">Cancel</a>
            </div>
        </form>
    </div>
</body>
</html>
```

**Backend Route** (`routes/admin.py`):
```python
@admin_bp.route('/admin/settings', methods=['GET', 'POST'])
@require_authentication
def manage_settings():
    """System settings management"""
    from scheduler_app.models import SystemSetting

    if request.method == 'POST':
        # Update Retail-Link credentials
        SystemSetting.set_setting('edr_username', request.form.get('edr_username'))

        # Only update password if provided
        if request.form.get('edr_password'):
            SystemSetting.set_setting('edr_password', request.form.get('edr_password'), 'encrypted')

        SystemSetting.set_setting('edr_mfa_credential_id', request.form.get('edr_mfa_credential_id'))

        # Update auto-scheduler settings
        SystemSetting.set_setting(
            'auto_scheduler_enabled',
            request.form.get('auto_scheduler_enabled') == 'true',
            'boolean'
        )
        SystemSetting.set_setting(
            'auto_scheduler_require_approval',
            request.form.get('auto_scheduler_require_approval') == 'true',
            'boolean'
        )

        flash('Settings saved successfully', 'success')
        return redirect(url_for('admin.manage_settings'))

    # GET request - display current settings
    settings = {
        'edr_username': SystemSetting.get_setting('edr_username'),
        'edr_mfa_credential_id': SystemSetting.get_setting('edr_mfa_credential_id'),
        'auto_scheduler_enabled': SystemSetting.get_setting('auto_scheduler_enabled', True),
        'auto_scheduler_require_approval': SystemSetting.get_setting('auto_scheduler_require_approval', True),
    }

    return render_template('settings.html', settings=settings)
```

**Migration to Settings-Based Credentials:**

Update all credential usage points:
```python
# OLD (config-based):
username = current_app.config.get('WALMART_EDR_USERNAME')

# NEW (settings-based):
from scheduler_app.models import SystemSetting
username = SystemSetting.get_setting('edr_username')
```

**Key Design Decisions:**
- ✅ Database-backed settings - no code changes for config updates
- ✅ Encrypted password storage - uses cryptography library
- ✅ Type-aware settings - boolean, string, encrypted
- ✅ Backward compatible - fallback to config if setting not found
- ✅ Audit trail - track who updated settings and when

### Integration Points
- **Auto-Scheduler Routes** - check `auto_scheduler_enabled` before running
- **EDR Generator** - use SystemSetting.get_setting() for credentials
- **Admin UI** - add navigation link to settings page

---

## Feature 4: Single-Event Auto-Scheduling

### User Story
**As a** scheduler,
**I want to** auto-schedule a single event on-demand,
**So that** I can quickly assign an event without waiting for the batch scheduler or manually selecting employees.

### Design Overview

**Location:** Events page, each unscheduled event

**Current State:**
```
Event Details | [Schedule Manually] [Edit] [Delete]
```

**New State:**
```
Event Details | [Auto Schedule] [Schedule Manually] [Edit] [Delete]
```

### Technical Approach

**Frontend Changes** (`templates/unscheduled.html`):
```html
<button class="btn btn-sm btn-success"
        onclick="autoScheduleEvent('{{ event.id }}')">
    <i class="icon-calendar"></i> Auto Schedule
</button>

<script>
function autoScheduleEvent(eventId) {
    if (!confirm('Auto-schedule this event using rotation and priority logic?')) {
        return;
    }

    // Show loading indicator
    const btn = event.target;
    btn.disabled = true;
    btn.innerHTML = '<i class="spinner"></i> Scheduling...';

    // Call API
    fetch(`/api/auto_schedule_event/${eventId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`Event scheduled to ${data.employee_name} on ${data.schedule_date} at ${data.schedule_time}`);
            location.reload(); // Refresh page to show updated event
        } else {
            alert(`Failed to schedule event: ${data.error}`);
            btn.disabled = false;
            btn.innerHTML = '<i class="icon-calendar"></i> Auto Schedule';
        }
    })
    .catch(error => {
        alert('Error scheduling event: ' + error);
        btn.disabled = false;
        btn.innerHTML = '<i class="icon-calendar"></i> Auto Schedule';
    });
}
</script>
```

**Backend Route** (`routes/auto_scheduler.py`):
```python
@auto_scheduler_bp.route('/api/auto_schedule_event/<int:event_id>', methods=['POST'])
@require_authentication
def auto_schedule_single_event(event_id):
    """
    Auto-schedule a single event using the same logic as batch scheduler
    Returns: JSON with success/failure and assignment details
    """
    from scheduler_app.services.scheduling_engine import SchedulingEngine
    from scheduler_app.models import SystemSetting

    db = current_app.extensions['sqlalchemy']
    Event = current_app.config['Event']

    # Get the event
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({'success': False, 'error': 'Event not found'}), 404

    if event.is_scheduled:
        return jsonify({'success': False, 'error': 'Event is already scheduled'}), 400

    # Create a temporary run record (for logging/tracking)
    SchedulerRunHistory = current_app.config['SchedulerRunHistory']
    run = SchedulerRunHistory(
        run_type='single_event',
        total_events=1,
        events_scheduled=0,
        events_failed=0,
        run_status='in_progress'
    )
    db.session.add(run)
    db.session.commit()

    try:
        # Initialize scheduling engine
        engine = SchedulingEngine(db)

        # Schedule the event using same logic as batch scheduler
        # This will create a pending_schedule record
        engine.schedule_event(run, event)

        # Check if auto-approval is disabled
        require_approval = SystemSetting.get_setting('auto_scheduler_require_approval', True)

        if require_approval:
            # Return pending schedule for user review
            run.run_status = 'pending_approval'
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Event scheduled (pending approval)',
                'requires_approval': True,
                'run_id': run.id
            })
        else:
            # Auto-approve and submit to Crossmark API
            pending = db.session.query(PendingSchedule).filter_by(
                scheduler_run_id=run.id,
                event_ref_num=event.project_ref_num
            ).first()

            if not pending:
                raise Exception("Failed to create pending schedule")

            # Submit to Crossmark API (reuse existing approval logic)
            from scheduler_app.session_api_service import session_api as external_api

            success = _submit_pending_schedule_to_api(pending, event, external_api)

            if success:
                run.events_scheduled = 1
                run.run_status = 'completed'
                event.is_scheduled = True
                db.session.commit()

                return jsonify({
                    'success': True,
                    'message': 'Event scheduled successfully',
                    'employee_name': pending.employee.name,
                    'schedule_date': pending.schedule_date.strftime('%Y-%m-%d'),
                    'schedule_time': pending.schedule_time.strftime('%I:%M %p')
                })
            else:
                run.events_failed = 1
                run.run_status = 'failed'
                db.session.commit()

                return jsonify({
                    'success': False,
                    'error': 'Failed to submit to Crossmark API'
                }), 500

    except Exception as e:
        run.events_failed = 1
        run.run_status = 'failed'
        run.error_details = str(e)
        db.session.commit()

        current_app.logger.error(f"Single event scheduling failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
```

**Key Design Decisions:**
- ✅ Reuse SchedulingEngine - same logic as batch scheduler
- ✅ Respect approval setting - honors system_settings.auto_scheduler_require_approval
- ✅ Immediate feedback - returns result to user via AJAX
- ✅ Track as scheduler run - creates SchedulerRunHistory record
- ✅ Handles API submission - integrates with Crossmark if auto-approved

### Integration Points
- **SchedulingEngine** - reuses existing event scheduling logic
- **SystemSettings** - checks auto_scheduler_require_approval
- **Crossmark API** - submits schedule if auto-approved
- **PendingSchedule** - creates pending record for approval workflow

---

## Feature 5: Employee Analytics & Printing

### User Story
**As a** scheduler,
**I want to** view employee scheduling statistics and print individual/weekly schedules,
**So that** I can balance workloads and provide paper schedules to employees.

### Design Overview

**New Page:** `/employees/analytics`

**Features:**
1. **Employee Schedule Summary Table**
   - Days scheduled this week (count)
   - Total events this week (count)
   - Sortable columns

2. **Weekly Employee Schedules (Summary)**
   - Print button for all employees
   - Format: Sun-Sat, Name + Time only
   - Filter: CORE and Juicer events only
   - Layout: Landscape A4, one page

3. **Individual Employee Schedules (Detailed)**
   - Print button per employee
   - Format: Sun-Sat, Name + Time + Event Name
   - Layout: Landscape A4, one page per employee
   - For employees not using mobile app

### Technical Approach

**Database Queries:**

```python
def get_weekly_employee_stats(start_date, end_date):
    """
    Get employee scheduling statistics for the week
    Returns: [(employee_name, days_scheduled, total_events)]
    """
    db = current_app.extensions['sqlalchemy']
    Schedule = current_app.config['Schedule']
    Employee = current_app.config['Employee']
    Event = current_app.config['Event']

    # Get unique days scheduled per employee
    stats = db.session.query(
        Employee.name,
        func.count(func.distinct(func.date(Schedule.schedule_datetime))).label('days_scheduled'),
        func.count(Schedule.id).label('total_events')
    ).join(
        Schedule, Employee.id == Schedule.employee_id
    ).filter(
        func.date(Schedule.schedule_datetime) >= start_date,
        func.date(Schedule.schedule_datetime) <= end_date
    ).group_by(
        Employee.id, Employee.name
    ).order_by(
        func.count(func.distinct(func.date(Schedule.schedule_datetime))).desc()
    ).all()

    return stats
```

**Frontend** (`templates/employee_analytics.html`):
```html
<!DOCTYPE html>
<html>
<head>
    <title>Employee Analytics</title>
    <!-- Include existing styles -->
</head>
<body>
    <div class="container">
        <h1>Employee Scheduling Analytics</h1>

        <!-- Week Selector -->
        <div class="week-selector">
            <label for="week-start">Week Starting:</label>
            <input type="date" id="week-start" value="{{ week_start }}">
            <button onclick="loadWeekStats()">Refresh</button>
        </div>

        <!-- Employee Statistics Table -->
        <table class="analytics-table">
            <thead>
                <tr>
                    <th>Employee Name</th>
                    <th>Days Scheduled</th>
                    <th>Total Events</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for stat in employee_stats %}
                <tr>
                    <td>{{ stat.employee_name }}</td>
                    <td>{{ stat.days_scheduled }}</td>
                    <td>{{ stat.total_events }}</td>
                    <td>
                        <button onclick="printIndividualSchedule('{{ stat.employee_id }}', '{{ week_start }}')">
                            Print Individual Schedule
                        </button>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <!-- Print Actions -->
        <div class="print-actions">
            <button class="btn btn-primary" onclick="printWeeklySummary('{{ week_start }}')">
                Print Weekly Summary (All Employees)
            </button>
        </div>
    </div>

    <script>
    function printWeeklySummary(weekStart) {
        window.open(`/api/print_weekly_summary/${weekStart}`, '_blank');
    }

    function printIndividualSchedule(employeeId, weekStart) {
        window.open(`/api/print_employee_schedule/${employeeId}/${weekStart}`, '_blank');
    }
    </script>
</body>
</html>
```

**Backend Routes** (`routes/admin.py`):

**1. Weekly Summary (All Employees, CORE + Juicer Only):**
```python
@admin_bp.route('/api/print_weekly_summary/<week_start_str>')
def print_weekly_summary(week_start_str):
    """
    Print weekly schedule summary for all employees
    Layout: Landscape A4, one page
    Shows: Sun-Sat, Name + Time only
    Filter: CORE and Juicer events only
    """
    try:
        week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()

        # Get Sunday of the week
        sunday = week_start - timedelta(days=week_start.weekday() + 1)
        saturday = sunday + timedelta(days=6)

        # Get all CORE and Juicer events for the week
        db = current_app.extensions['sqlalchemy']
        Schedule = current_app.config['Schedule']
        Employee = current_app.config['Employee']
        Event = current_app.config['Event']

        schedules = db.session.query(
            Employee.name,
            Schedule.schedule_datetime,
            Event.event_type
        ).join(
            Schedule, Employee.id == Schedule.employee_id
        ).join(
            Event, Schedule.event_ref_num == Event.project_ref_num
        ).filter(
            func.date(Schedule.schedule_datetime) >= sunday,
            func.date(Schedule.schedule_datetime) <= saturday,
            Event.event_type.in_(['Core', 'Juicer'])
        ).order_by(
            Employee.name,
            Schedule.schedule_datetime
        ).all()

        # Generate HTML for landscape layout
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Weekly Schedule Summary</title>
            <style>
                @page {{
                    size: A4 landscape;
                    margin: 0.5in;
                }}
                body {{
                    font-family: Arial, sans-serif;
                    font-size: 10pt;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 20px;
                    border-bottom: 2px solid #2E4C73;
                    padding-bottom: 10px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                th {{
                    background: #2E4C73;
                    color: white;
                    padding: 8px;
                    text-align: left;
                    font-size: 9pt;
                }}
                td {{
                    padding: 6px 8px;
                    border: 1px solid #ddd;
                    font-size: 9pt;
                }}
                tr:nth-child(even) {{ background: #f9f9f9; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Weekly Schedule Summary - {sunday.strftime('%B %d')} to {saturday.strftime('%B %d, %Y')}</h2>
                <p>(CORE and Juicer Events Only)</p>
            </div>

            <table>
                <thead>
                    <tr>
                        <th style="width: 20%;">Employee</th>
                        <th style="width: 11.4%;">Sun</th>
                        <th style="width: 11.4%;">Mon</th>
                        <th style="width: 11.4%;">Tue</th>
                        <th style="width: 11.4%;">Wed</th>
                        <th style="width: 11.4%;">Thu</th>
                        <th style="width: 11.4%;">Fri</th>
                        <th style="width: 11.4%;">Sat</th>
                    </tr>
                </thead>
                <tbody>
        """

        # Group schedules by employee
        from collections import defaultdict
        employee_schedules = defaultdict(lambda: defaultdict(list))

        for schedule in schedules:
            day_name = schedule.schedule_datetime.strftime('%A')[:3]  # Sun, Mon, Tue...
            time_str = schedule.schedule_datetime.strftime('%I:%M %p')
            employee_schedules[schedule.name][day_name].append(time_str)

        # Generate table rows
        for employee_name in sorted(employee_schedules.keys()):
            html += f"<tr><td><strong>{employee_name}</strong></td>"

            for day in ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']:
                times = employee_schedules[employee_name].get(day, [])
                html += f"<td>{'<br>'.join(times) if times else '-'}</td>"

            html += "</tr>"

        html += """
                </tbody>
            </table>
        </body>
        </html>
        """

        # Convert to PDF
        output = BytesIO()
        pisa.CreatePDF(html, dest=output)
        output.seek(0)

        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'Weekly_Summary_{week_start_str}.pdf'
        )

    except Exception as e:
        current_app.logger.error(f"Error generating weekly summary: {str(e)}")
        return jsonify({'error': str(e)}), 500
```

**2. Individual Employee Schedule (Detailed):**
```python
@admin_bp.route('/api/print_employee_schedule/<employee_id>/<week_start_str>')
def print_employee_schedule(employee_id, week_start_str):
    """
    Print detailed schedule for one employee
    Layout: Landscape A4, one page
    Shows: Sun-Sat, Name + Time + Event Name
    Includes: ALL event types
    """
    try:
        week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()

        # Get Sunday-Saturday range
        sunday = week_start - timedelta(days=week_start.weekday() + 1)
        saturday = sunday + timedelta(days=6)

        # Get employee details
        db = current_app.extensions['sqlalchemy']
        Employee = current_app.config['Employee']
        employee = db.session.get(Employee, employee_id)

        if not employee:
            return jsonify({'error': 'Employee not found'}), 404

        # Get all schedules for the week
        Schedule = current_app.config['Schedule']
        Event = current_app.config['Event']

        schedules = db.session.query(
            Schedule.schedule_datetime,
            Event.project_name,
            Event.event_type
        ).join(
            Event, Schedule.event_ref_num == Event.project_ref_num
        ).filter(
            Schedule.employee_id == employee_id,
            func.date(Schedule.schedule_datetime) >= sunday,
            func.date(Schedule.schedule_datetime) <= saturday
        ).order_by(
            Schedule.schedule_datetime
        ).all()

        # Generate HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{employee.name} - Weekly Schedule</title>
            <style>
                @page {{
                    size: A4 landscape;
                    margin: 0.75in;
                }}
                body {{
                    font-family: Arial, sans-serif;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    border-bottom: 3px solid #2E4C73;
                    padding-bottom: 15px;
                }}
                h1 {{
                    color: #2E4C73;
                    margin: 0;
                    font-size: 24pt;
                }}
                .week-range {{
                    color: #666;
                    font-size: 14pt;
                    margin-top: 10px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                th {{
                    background: #2E4C73;
                    color: white;
                    padding: 12px;
                    text-align: left;
                    font-size: 12pt;
                }}
                td {{
                    padding: 10px 12px;
                    border: 1px solid #ddd;
                    font-size: 11pt;
                    vertical-align: top;
                }}
                tr:nth-child(even) {{ background: #f9f9f9; }}
                .day-header {{
                    font-weight: bold;
                    color: #2E4C73;
                    font-size: 12pt;
                }}
                .event-time {{
                    color: #1B9BD8;
                    font-weight: bold;
                }}
                .event-name {{
                    margin-left: 10px;
                }}
                .no-events {{
                    color: #999;
                    font-style: italic;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{employee.name}</h1>
                <p class="week-range">Week of {sunday.strftime('%B %d')} - {saturday.strftime('%B %d, %Y')}</p>
            </div>

            <table>
                <thead>
                    <tr>
                        <th style="width: 15%;">Day</th>
                        <th style="width: 15%;">Time</th>
                        <th style="width: 70%;">Event</th>
                    </tr>
                </thead>
                <tbody>
        """

        # Group schedules by day
        from collections import defaultdict
        daily_schedules = defaultdict(list)

        for schedule in schedules:
            day_key = schedule.schedule_datetime.date()
            daily_schedules[day_key].append({
                'time': schedule.schedule_datetime.strftime('%I:%M %p'),
                'name': schedule.project_name,
                'type': schedule.event_type
            })

        # Generate rows for each day of the week
        current_date = sunday
        while current_date <= saturday:
            day_name = current_date.strftime('%A, %B %d')
            events = daily_schedules.get(current_date, [])

            if events:
                for idx, event in enumerate(events):
                    if idx == 0:
                        html += f"""
                        <tr>
                            <td class="day-header" rowspan="{len(events)}">{day_name}</td>
                            <td class="event-time">{event['time']}</td>
                            <td class="event-name">{event['name']} <em>({event['type']})</em></td>
                        </tr>
                        """
                    else:
                        html += f"""
                        <tr>
                            <td class="event-time">{event['time']}</td>
                            <td class="event-name">{event['name']} <em>({event['type']})</em></td>
                        </tr>
                        """
            else:
                html += f"""
                <tr>
                    <td class="day-header">{day_name}</td>
                    <td class="no-events" colspan="2">No events scheduled</td>
                </tr>
                """

            current_date += timedelta(days=1)

        html += """
                </tbody>
            </table>
        </body>
        </html>
        """

        # Convert to PDF
        output = BytesIO()
        pisa.CreatePDF(html, dest=output)
        output.seek(0)

        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'{employee.name.replace(" ", "_")}_Schedule_{week_start_str}.pdf'
        )

    except Exception as e:
        current_app.logger.error(f"Error generating employee schedule: {str(e)}")
        return jsonify({'error': str(e)}), 500
```

**Key Design Decisions:**
- ✅ Landscape A4 layout - optimizes horizontal space for week view
- ✅ One-page constraint - fits on single sheet for easy distribution
- ✅ Differentiated formats - summary vs detailed based on use case
- ✅ Event type filtering - CORE/Juicer only for summary, all types for individual
- ✅ Sunday-Saturday week - standard scheduling week format

### Integration Points
- **Existing Schedule/Event queries** - reuses database models
- **PDF generation** - reuses xhtml2pdf infrastructure
- **Date utilities** - leverages Python datetime for week calculations

---

## Feature 6: Mobile Responsiveness

### User Story
**As a** scheduler using a mobile device,
**I want** all features to work seamlessly on my phone,
**So that** I can manage schedules on-the-go.

### Design Overview

**Strategy:** Progressive enhancement with mobile-first CSS

**Key Responsive Areas:**
1. Dashboard (date picker, print buttons)
2. Settings page (form inputs, checkboxes)
3. Employee analytics table
4. Event lists (auto-schedule buttons)

### Technical Approach

**Base CSS Framework:**
```css
/* Mobile-first responsive utilities */
/* File: static/css/responsive.css */

/* Base mobile styles (default) */
.container {
    padding: 15px;
    max-width: 100%;
}

.btn {
    padding: 12px 16px;
    font-size: 16px; /* Touch-friendly size */
    min-height: 44px; /* Apple HIG minimum touch target */
}

/* Date picker on mobile */
input[type="date"] {
    width: 100%;
    font-size: 16px; /* Prevents iOS zoom */
    padding: 12px;
}

/* Tables responsive on mobile */
.analytics-table {
    display: block;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}

.analytics-table th,
.analytics-table td {
    white-space: nowrap;
    padding: 8px;
}

/* Settings form on mobile */
.settings-section {
    margin-bottom: 30px;
}

.form-group {
    margin-bottom: 20px;
}

.form-control {
    width: 100%;
    font-size: 16px; /* Prevents iOS zoom */
    padding: 12px;
}

/* Button groups stack on mobile */
.print-actions {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.print-actions .btn {
    width: 100%;
}

/* Tablet and larger (768px+) */
@media (min-width: 768px) {
    .container {
        padding: 30px;
        max-width: 960px;
        margin: 0 auto;
    }

    .print-actions {
        flex-direction: row;
        justify-content: space-between;
    }

    .print-actions .btn {
        width: auto;
    }

    input[type="date"] {
        width: auto;
        max-width: 300px;
    }
}

/* Desktop (1024px+) */
@media (min-width: 1024px) {
    .container {
        max-width: 1200px;
    }

    .analytics-table {
        display: table;
    }
}
```

**Viewport Meta Tag** (add to all templates):
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

**Touch-Friendly Interactions:**
```javascript
// Ensure buttons have adequate touch targets
document.querySelectorAll('.btn').forEach(btn => {
    // Minimum 44x44px touch target (Apple HIG)
    const rect = btn.getBoundingClientRect();
    if (rect.height < 44) {
        btn.style.minHeight = '44px';
    }
});

// Prevent double-tap zoom on buttons
document.querySelectorAll('.btn').forEach(btn => {
    btn.addEventListener('touchend', function(e) {
        e.preventDefault();
        btn.click();
    });
});
```

**Key Design Decisions:**
- ✅ Mobile-first CSS - starts with mobile, enhances for desktop
- ✅ Touch-friendly targets - 44px minimum (Apple HIG)
- ✅ Prevent iOS zoom - 16px font size on inputs
- ✅ Horizontal scroll tables - preserves data on small screens
- ✅ Stacked buttons - easier thumb access on mobile

### Testing Checklist
- [ ] Test on iOS Safari (iPhone 12+)
- [ ] Test on Android Chrome (Pixel 6+)
- [ ] Test landscape orientation
- [ ] Test form inputs don't zoom on focus
- [ ] Test button tap targets are adequate
- [ ] Test table scrolling on small screens

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
**Goal:** Database and core infrastructure

- ✅ Create SystemSettings table and model
- ✅ Implement encryption utilities
- ✅ Create settings page UI
- ✅ Migrate EDR credentials to settings
- ✅ Test settings save/load

**Deliverables:**
- Database migration script
- SystemSettings model
- Settings page (GET/POST)
- Encryption helper functions

---

### Phase 2: Printing Enhancements (Week 2-3)
**Goal:** Flexible date-based and per-event printing

- ✅ Refactor print_paperwork to support date parameter
- ✅ Create print_paperwork_by_date route
- ✅ Update dashboard with date picker
- ✅ Create print_event_paperwork route
- ✅ Add print buttons to event lists
- ✅ Test PDF generation for various dates

**Deliverables:**
- Updated dashboard UI
- New printing routes
- Refactored PDF generation helpers

---

### Phase 3: Single-Event Auto-Scheduling (Week 3-4)
**Goal:** On-demand auto-scheduling for individual events

- ✅ Create auto_schedule_single_event route
- ✅ Integrate with SchedulingEngine
- ✅ Add approval workflow check
- ✅ Update unscheduled events UI
- ✅ Test with various event types
- ✅ Test approval vs auto-submit flows

**Deliverables:**
- Auto-schedule button on events
- API route with approval logic
- Integration with SchedulingEngine

---

### Phase 4: Employee Analytics & Printing (Week 4-5)
**Goal:** Employee scheduling insights and printable schedules

- ✅ Create employee_analytics page
- ✅ Implement weekly stats query
- ✅ Create print_weekly_summary route (landscape A4)
- ✅ Create print_employee_schedule route (landscape A4)
- ✅ Design analytics table UI
- ✅ Test PDF layouts on actual printers

**Deliverables:**
- Employee analytics page
- Weekly summary PDF (landscape)
- Individual schedule PDF (landscape)
- Statistics dashboard

---

### Phase 5: Mobile Responsiveness (Week 5-6)
**Goal:** Mobile-optimized experience

- ✅ Create responsive.css stylesheet
- ✅ Update all templates with viewport meta
- ✅ Test on iOS and Android devices
- ✅ Fix touch target issues
- ✅ Test form inputs (no zoom on focus)
- ✅ Test table scrolling
- ✅ Cross-browser testing

**Deliverables:**
- Responsive CSS file
- Mobile-tested all pages
- Touch-friendly interactions
- Documented browser support matrix

---

## Technical Dependencies

### New Python Packages
```
cryptography>=41.0.0  # For settings encryption
PyPDF2>=3.0.0         # Already exists (PDF manipulation)
reportlab>=4.0.0      # Already exists (PDF generation)
xhtml2pdf>=0.2.11     # Already exists (HTML to PDF)
```

### Database Migrations
```sql
-- Migration 001: Create system_settings table
CREATE TABLE system_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(50),
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100)
);

-- Insert default settings
INSERT INTO system_settings (setting_key, setting_value, setting_type, description) VALUES
('edr_username', NULL, 'string', 'Walmart Retail-Link EDR Username'),
('edr_password', NULL, 'encrypted', 'Walmart Retail-Link EDR Password'),
('edr_mfa_credential_id', NULL, 'string', 'Walmart Retail-Link MFA Credential ID'),
('auto_scheduler_enabled', 'true', 'boolean', 'Enable automatic scheduler runs'),
('auto_scheduler_require_approval', 'true', 'boolean', 'Require user approval before scheduling changes');
```

### Configuration Updates
```python
# config.py - Add encryption key
SETTINGS_ENCRYPTION_KEY = os.environ.get('SETTINGS_ENCRYPTION_KEY') or Fernet.generate_key()
```

---

## Security Considerations

### Credential Storage
- ✅ **Encrypted at rest** - Fernet symmetric encryption for passwords
- ✅ **Access control** - Settings page requires authentication
- ✅ **Audit trail** - Track who updated settings and when
- ✅ **Environment variables** - Encryption key stored separately

### API Endpoints
- ✅ **Authentication required** - All admin routes use @require_authentication
- ✅ **Input validation** - Date strings validated before parsing
- ✅ **Error handling** - No sensitive info in error messages

### PDF Generation
- ✅ **User input sanitization** - HTML escaping in templates
- ✅ **File path validation** - Prevent directory traversal
- ✅ **Resource limits** - Prevent large PDF DoS

---

## Testing Strategy

### Unit Tests
```python
# test_settings.py
def test_get_setting_string()
def test_get_setting_boolean()
def test_get_setting_encrypted()
def test_set_setting_creates_new()
def test_set_setting_updates_existing()

# test_printing.py
def test_print_paperwork_by_date_valid()
def test_print_paperwork_by_date_invalid()
def test_print_event_paperwork_found()
def test_print_event_paperwork_not_found()

# test_auto_schedule.py
def test_auto_schedule_event_success()
def test_auto_schedule_event_requires_approval()
def test_auto_schedule_event_already_scheduled()

# test_employee_analytics.py
def test_weekly_stats_calculation()
def test_print_weekly_summary_pdf()
def test_print_individual_schedule_pdf()
```

### Integration Tests
```python
def test_settings_roundtrip()  # Save -> Load -> Verify
def test_print_workflow_end_to_end()  # Select date -> Print -> Verify PDF
def test_auto_schedule_with_approval()  # Schedule -> Approve -> API submit
def test_employee_schedule_across_week()  # Multiple events -> Print -> Verify
```

### Manual Testing Checklist
- [ ] Print paperwork for various dates (past, future, today)
- [ ] Print individual event paperwork (scheduled vs unscheduled)
- [ ] Auto-schedule different event types (Core, Juicer, Digital)
- [ ] Update settings and verify credential usage
- [ ] Print weekly summary (verify landscape, one page)
- [ ] Print individual schedule (verify all event types shown)
- [ ] Test all features on mobile (iOS + Android)

---

## Performance Considerations

### PDF Generation Optimization
- **Caching:** EDR session tokens cached to avoid re-authentication
- **Async generation:** Consider background jobs for large PDFs
- **Resource cleanup:** Properly close BytesIO buffers

### Database Queries
- **Indexed columns:** Ensure Schedule.schedule_datetime indexed
- **Query optimization:** Use joins instead of N+1 queries
- **Date range filters:** Limit query scope to relevant date ranges

### Mobile Performance
- **CSS minification:** Compress responsive.css in production
- **Image optimization:** Use appropriate sizes for mobile
- **Lazy loading:** Load analytics tables on-demand

---

## Monitoring & Logging

### Key Metrics to Track
- PDF generation time (avg, p95, p99)
- EDR API call success rate
- Settings update frequency
- Auto-schedule success/failure rate
- Mobile vs desktop usage ratio

### Logging Points
```python
# Settings changes
logger.info(f"Settings updated: {setting_key} by {user}")

# PDF generation
logger.info(f"Generating paperwork for {date} - {num_events} events")
logger.info(f"PDF generation completed in {elapsed}ms")

# Auto-scheduling
logger.info(f"Auto-scheduled event {event_id} to {employee_name}")
logger.error(f"Auto-schedule failed: {error_details}")
```

---

## Rollback Plan

### If Issues Arise

**Phase 1 (Settings):**
- Rollback migration, restore config-based credentials
- Keep existing print_paperwork endpoints

**Phase 2 (Printing):**
- Revert dashboard to static today/tomorrow buttons
- Remove date picker UI changes

**Phase 3 (Auto-schedule):**
- Hide auto-schedule buttons
- Disable route (return 503)

**Phase 4 (Analytics):**
- Remove analytics page from navigation
- Keep routes for future retry

**Phase 5 (Mobile):**
- Remove responsive.css from template includes
- Desktop-only fallback

---

## Success Criteria

### Feature 1: Date-Based Printing ✅
- [ ] Date picker accepts any date
- [ ] PDFs generate correctly for selected date
- [ ] Backward compatible with existing routes

### Feature 2: Event Paperwork ✅
- [ ] Print button appears on all events
- [ ] PDF contains exactly 4 pieces (EDR, Sales Tool, Activity Log, Checklist)
- [ ] Excludes schedule and item numbers pages

### Feature 3: Settings Page ✅
- [ ] All settings save and load correctly
- [ ] Passwords encrypted in database
- [ ] EDR authentication uses settings-based credentials

### Feature 4: Single-Event Auto-Schedule ✅
- [ ] Successfully schedules events using rotation logic
- [ ] Respects approval setting
- [ ] Handles all event types correctly

### Feature 5: Employee Analytics ✅
- [ ] Stats calculate accurately (days, events)
- [ ] Weekly summary fits on one page (landscape)
- [ ] Individual schedules show all events

### Feature 6: Mobile Responsive ✅
- [ ] All pages usable on mobile devices
- [ ] Touch targets meet 44px minimum
- [ ] Forms don't zoom on focus (iOS)
- [ ] Tables scroll horizontally on small screens

---

## Open Questions for Stakeholder Review

1. **Settings Encryption:**
   - Should encryption key be rotated periodically?
   - Who should have access to settings page?

2. **Auto-Schedule Approval:**
   - Should single-event auto-schedule bypass approval if batch requires it?
   - Or always respect the global setting?

3. **PDF Layouts:**
   - Are landscape A4 layouts acceptable for all printers?
   - Should we support other paper sizes?

4. **Employee Analytics:**
   - What additional metrics would be valuable?
   - Should we track historical trends (month-over-month)?

5. **Mobile Priorities:**
   - Which features are most critical on mobile?
   - Are there desktop-only features we can deprioritize?

---

## Conclusion

This architecture provides a comprehensive blueprint for implementing five major feature enhancements across 6 weeks of development. The design prioritizes:

- **Reusability** - Leverages existing PDF generation and scheduling infrastructure
- **Security** - Encrypted credentials, authentication-required endpoints
- **User Experience** - Mobile-first responsive design, intuitive workflows
- **Maintainability** - Modular code, clear separation of concerns
- **Flexibility** - Settings-based configuration, easy to adapt

Each phase delivers standalone value while building toward a complete enhancement suite. The phased approach allows for feedback and iteration between implementations.

**Next Steps:**
1. Review and approve architecture with stakeholders
2. Create detailed user stories for each phase
3. Begin Phase 1 (Settings infrastructure) development
4. Schedule design reviews with users for PDF layouts
5. Plan mobile device testing sessions

---

**Document Version:** 1.0
**Author:** Winston, Architect
**Date:** 2025-10-01
**Status:** Ready for Epic Planning
