# User Profile Dropdown and Help System - Design Document

**Document Status:** Draft
**Created:** 2025-01-10
**Last Updated:** 2025-01-10

---

## Executive Summary

This document outlines the design for three major feature enhancements to the Product Connections Scheduler:
1. User Profile Dropdown with Settings integration
2. Comprehensive Help/Getting Started system
3. Enhanced Manual Edit with Conflict Detection for Auto Scheduler

---

## Part 1: User Stories

### Epic 1: User Profile Dropdown

**US-001: Display User's Full Name in Header**
```
As a logged-in user
I want to see my first and last name in the header instead of just "Welcome, user"
So that I can confirm I'm logged in with the correct account
```
**Acceptance Criteria:**
- User's full name is displayed in the top-right corner of the header
- Name is displayed as "{First Name} {Last Name}"
- Falls back to username if full name not available
- Visible on all pages after login

**US-002: User Profile Dropdown Menu**
```
As a logged-in user
I want to click on my name to open a dropdown menu
So that I can access user-specific actions
```
**Acceptance Criteria:**
- Clicking on user's name opens a dropdown menu
- Dropdown shows a down arrow (▼) next to the name
- Clicking outside the dropdown closes it
- Dropdown is styled consistently with the application theme

**US-003: Move Settings to Profile Dropdown**
```
As a logged-in user
I want Settings to be in the profile dropdown instead of the navigation bar
So that the navigation is less cluttered and user settings are logically grouped
```
**Acceptance Criteria:**
- Settings link is removed from the main navigation bar
- Settings option appears in the profile dropdown
- Clicking Settings navigates to the Settings page
- Settings remains accessible to all users with appropriate permissions

**US-004: Logout from Profile Dropdown**
```
As a logged-in user
I want to log out from the profile dropdown
So that I can securely end my session
```
**Acceptance Criteria:**
- Logout option appears in the profile dropdown
- Clicking Logout ends the session and redirects to login page
- Logout functionality remains unchanged from current implementation

---

### Epic 2: Help and Getting Started System

**US-005: Help Button in Navigation**
```
As a user
I want a Help button in the navigation bar
So that I can access documentation and getting started guides
```
**Acceptance Criteria:**
- Help button is visible in the main navigation bar
- Help button is styled consistently with other nav items
- Clicking Help navigates to the Help page

**US-006: Getting Started Documentation**
```
As a new user
I want to see a comprehensive getting started guide
So that I can learn how to configure and use the scheduler
```
**Acceptance Criteria:**
- Help page includes sections for:
  - Setting Walmart Retail Link credentials
  - Adding and managing employees
  - Understanding the auto scheduler
  - Accepting or denying auto schedule proposals
- Each section has clear step-by-step instructions
- Sections are visually organized with headers and navigation

**US-007: Walmart Retail Link Credentials Setup Guide**
```
As a user
I want instructions on setting up Walmart Retail Link credentials
So that I can integrate with external systems
```
**Acceptance Criteria:**
- Section explains what Walmart Retail Link credentials are
- Step-by-step guide for entering credentials in Settings
- Information about where to find these credentials
- Troubleshooting tips for common authentication issues

**US-008: Employee Management Guide**
```
As a user
I want instructions on adding and managing employees
So that I can maintain accurate employee data for scheduling
```
**Acceptance Criteria:**
- Explains how to navigate to Employee Management
- Shows how to add new employees
- Describes employee fields and their importance
- Explains employee roles and permissions
- Covers updating and deactivating employees

**US-009: Auto Scheduler Explanation**
```
As a user
I want to understand how the auto scheduler works
So that I can trust and effectively use its recommendations
```
**Acceptance Criteria:**
- Explains the auto scheduler's purpose and goals
- Describes how it selects employees for events
- Explains rotation assignments (Juicer, Primary Lead)
- Describes constraints (availability, time-off, job roles)
- Shows how to manually trigger a scheduler run

**US-010: Accept/Deny Schedule Workflow Guide**
```
As a user
I want to understand how to review and approve/reject schedules
So that I can confidently make scheduling decisions
```
**Acceptance Criteria:**
- Explains the review page layout
- Shows newly scheduled events vs swaps vs failures
- Describes how to approve schedules
- Describes how to reject schedules
- Explains what happens after approval (API submission)

---

### Epic 3: Enhanced Manual Edit with Conflict Detection

**US-011: Edit Pending Schedule Events**
```
As a scheduler
I want to edit proposed schedule events before approval
So that I can make adjustments to the auto scheduler's recommendations
```
**Acceptance Criteria:**
- Edit button/link available for each pending schedule event
- Opens a modal or inline edit interface
- Can change employee assignment
- Can change date and time
- Edit action triggers conflict validation
- Changes are saved to pending schedule with 'user_edited' status

**US-012: Respect Hard Constraints During Manual Edit**
```
As a scheduler
I want the system to prevent invalid edits
So that I don't accidentally schedule someone when they're unavailable
```
**Acceptance Criteria:**
- Cannot assign employee on their requested days off
- Cannot assign employee outside their availability windows
- Cannot assign employee to events outside their job scope
- System shows clear error messages for constraint violations
- Edit is blocked until constraints are satisfied

**US-013: Not Limited by Auto Scheduler Proposal**
```
As a scheduler
I want to assign any available employee to any event
So that I have full flexibility to handle unique situations
```
**Acceptance Criteria:**
- Can assign any employee to any event (subject to hard constraints)
- Not limited to employees proposed by auto scheduler
- Can change event times freely (subject to availability)
- Can reassign events that auto scheduler failed to schedule

**US-014: Real-Time Conflict Detection**
```
As a scheduler
I want to see conflicts when I edit an event
So that I can identify and resolve scheduling conflicts
```
**Acceptance Criteria:**
- When an event is edited, system checks for conflicts with other pending events
- Conflicts are detected if same employee is assigned to multiple events on same date
- Conflicts are displayed below both conflicting events
- Conflict messages update in real-time as edits are made
- Conflicts do not block approval but serve as warnings

**US-015: Conflict Warning Message Format**
```
As a scheduler
I want clear, detailed conflict warnings
So that I can quickly understand and resolve conflicts
```
**Acceptance Criteria:**
- Conflict message format: "Schedule Conflict: {Employee's Name} is also proposed to be scheduled to {Event B} on {Scheduled Date}"
- Both events in a conflict show the warning
- Each conflict message references the other event by name
- Date is shown in human-readable format (e.g., "Monday, January 15, 2025")
- Conflict warnings are styled distinctly (warning color/icon)

**US-016: Multi-Event Conflict Detection**
```
As a scheduler
I want to see all conflicts for an event
So that I can understand the full impact of my changes
```
**Acceptance Criteria:**
- If an event conflicts with multiple other events, all conflicts are shown
- Each conflict is listed separately with its own message
- Conflicts are sorted chronologically by event time
- Total conflict count is displayed for the event

**US-017: Conflict Resolution Workflow**
```
As a scheduler
I want to easily resolve conflicts
So that I can finalize the schedule efficiently
```
**Acceptance Criteria:**
- Can click on a conflicting event to jump to it
- Can re-edit events to resolve conflicts
- Conflict warnings disappear when conflicts are resolved
- Can still approve schedule with conflicts (with confirmation warning)

---

## Part 2: Technical Architecture

### 2.1 User Profile Dropdown Architecture

#### 2.1.1 Database Changes
**Session Store Enhancement:**
- Add `first_name` and `last_name` to session user_info
- Source from Crossmark API during login if available
- Parse from username as fallback

**Data Model:**
```python
session_data = {
    'user_id': username,
    'user_info': {
        'username': username,
        'userId': userId,
        'first_name': first_name,  # NEW
        'last_name': last_name,    # NEW
        'full_name': f"{first_name} {last_name}",  # NEW
        'authenticated': True
    },
    'created_at': datetime.utcnow(),
    'crossmark_authenticated': True,
    'phpsessid': external_api.phpsessid
}
```

#### 2.1.2 Backend Changes

**File:** `scheduler_app/routes/auth.py`
- Modify `login()` function to extract first_name/last_name from API
- Add fallback logic to parse name from username
- Update session_store structure

**File:** `scheduler_app/app.py`
- Update `get_current_user()` context processor to include full name

#### 2.1.3 Frontend Changes

**File:** `scheduler_app/templates/base.html`
- Replace nav-user-section with dropdown component
- Add dropdown toggle button with user's full name
- Add dropdown menu with Settings and Logout options
- Remove Settings from main navigation

**New File:** `scheduler_app/static/js/user_dropdown.js`
- Handle dropdown open/close events
- Close dropdown when clicking outside
- Keyboard navigation support (Enter, Escape)

**File:** `scheduler_app/static/css/style.css`
- Add styles for dropdown component
- Add styles for dropdown arrow
- Add hover/active states
- Add responsive styles

#### 2.1.4 Component Structure
```html
<div class="nav-user-section">
    <div class="user-dropdown">
        <button class="user-dropdown-toggle" id="userDropdownToggle">
            <span class="user-name">{{ user.full_name or user.username }}</span>
            <span class="dropdown-arrow">▼</span>
        </button>
        <div class="user-dropdown-menu" id="userDropdownMenu" hidden>
            <a href="{{ url_for('admin.settings_page') }}" class="dropdown-item">
                <span class="dropdown-icon">⚙️</span>
                Settings
            </a>
            <div class="dropdown-divider"></div>
            <a href="{{ url_for('auth.logout') }}" class="dropdown-item">
                <span class="dropdown-icon">🚪</span>
                Logout
            </a>
        </div>
    </div>
</div>
```

---

### 2.2 Help System Architecture

#### 2.2.1 Backend Changes

**New File:** `scheduler_app/routes/help.py`
```python
"""Help and documentation routes"""
from flask import Blueprint, render_template

help_bp = Blueprint('help', __name__, url_prefix='/help')

@help_bp.route('/')
def help_home():
    """Display help home page"""
    return render_template('help/index.html')

@help_bp.route('/getting-started')
def getting_started():
    """Display getting started guide"""
    return render_template('help/getting_started.html')

@help_bp.route('/walmart-credentials')
def walmart_credentials():
    """Display Walmart Retail Link credentials guide"""
    return render_template('help/walmart_credentials.html')

@help_bp.route('/employee-management')
def employee_management():
    """Display employee management guide"""
    return render_template('help/employee_management.html')

@help_bp.route('/auto-scheduler')
def auto_scheduler_guide():
    """Display auto scheduler guide"""
    return render_template('help/auto_scheduler.html')

@help_bp.route('/review-approve')
def review_approve():
    """Display review and approval guide"""
    return render_template('help/review_approve.html')
```

**File:** `scheduler_app/app.py`
- Register help_bp blueprint

#### 2.2.2 Frontend Structure

**New Directory:** `scheduler_app/templates/help/`
- `index.html` - Help home with navigation to all guides
- `getting_started.html` - Overview and quick start
- `walmart_credentials.html` - Credential setup guide
- `employee_management.html` - Employee management guide
- `auto_scheduler.html` - Auto scheduler explanation
- `review_approve.html` - Review and approval workflow

**Template Structure:**
```html
{% extends "base.html" %}

{% block title %}Help - {{ section_title }}{% endblock %}

{% block content %}
<div class="help-container">
    <aside class="help-sidebar">
        <!-- Navigation -->
    </aside>
    <main class="help-content">
        <!-- Content -->
    </main>
</div>
{% endblock %}
```

**File:** `scheduler_app/templates/base.html`
- Add Help link to navigation bar (between Printing and user dropdown)

**New File:** `scheduler_app/static/css/help.css`
- Styles for help pages
- Sidebar navigation
- Content formatting
- Step-by-step guide styling
- Code/example blocks

---

### 2.3 Manual Edit with Conflict Detection Architecture

#### 2.3.1 Database Changes

**Table:** `pending_schedules`
Add columns for conflict tracking:
```python
# Add to PendingSchedule model
conflict_detected = db.Column(db.Boolean, default=False)
conflict_details = db.Column(db.JSON, nullable=True)  # Array of conflict objects
```

**Conflict Details Structure:**
```json
[
  {
    "conflicting_pending_id": 123,
    "conflicting_event_ref_num": 456,
    "conflicting_event_name": "Core - Walmart #5832",
    "employee_id": "US######",
    "employee_name": "John Doe",
    "schedule_date": "2025-01-15",
    "schedule_datetime": "2025-01-15T09:00:00"
  }
]
```

#### 2.3.2 Backend Changes

**New File:** `scheduler_app/services/conflict_detection.py`
```python
"""
Conflict detection service for manual schedule edits
Validates proposed schedules against hard constraints and detects conflicts
"""

class ConflictDetector:
    def __init__(self, db_session, models):
        self.db = db_session
        self.models = models

    def validate_hard_constraints(self, employee_id, event_ref_num, schedule_datetime):
        """
        Validate that assignment doesn't violate hard constraints
        Returns: (is_valid: bool, errors: List[str])
        """
        pass

    def check_time_off(self, employee_id, schedule_date):
        """Check if employee has requested time off"""
        pass

    def check_availability(self, employee_id, schedule_datetime):
        """Check if employee is available at the scheduled time"""
        pass

    def check_job_scope(self, employee_id, event_type):
        """Check if employee can work this event type"""
        pass

    def detect_conflicts(self, scheduler_run_id, exclude_pending_id=None):
        """
        Detect all conflicts within a scheduler run's pending schedules
        Returns: Dict[pending_id, List[conflict_objects]]
        """
        pass

    def get_conflicts_for_pending(self, pending_id):
        """Get conflicts for a specific pending schedule"""
        pass

    def update_conflict_flags(self, scheduler_run_id):
        """Update conflict_detected and conflict_details for all pending schedules"""
        pass
```

**File:** `scheduler_app/routes/auto_scheduler.py`

Modify `edit_pending_schedule()`:
```python
@auto_scheduler_bp.route('/api/pending/<int:pending_id>', methods=['PUT'])
def edit_pending_schedule(pending_id):
    """Edit a pending schedule with validation and conflict detection"""
    from services.conflict_detection import ConflictDetector

    # ... existing code to get pending schedule ...

    data = request.get_json()

    # Validate hard constraints
    detector = ConflictDetector(db.session, models)

    if 'employee_id' in data or 'schedule_datetime' in data:
        # Get updated values
        new_employee_id = data.get('employee_id', pending.employee_id)
        new_datetime = data.get('schedule_datetime', pending.schedule_datetime)

        # Validate constraints
        is_valid, errors = detector.validate_hard_constraints(
            new_employee_id,
            pending.event_ref_num,
            new_datetime
        )

        if not is_valid:
            return jsonify({
                'success': False,
                'errors': errors
            }), 400

    # Update pending schedule
    if 'employee_id' in data:
        pending.employee_id = data['employee_id']

    if 'schedule_datetime' in data:
        pending.schedule_datetime = datetime.fromisoformat(data['schedule_datetime'])
        pending.schedule_time = pending.schedule_datetime.time()

    pending.status = 'user_edited'

    # Detect conflicts for this run
    detector.update_conflict_flags(pending.scheduler_run_id)

    db.session.commit()

    # Get updated conflicts for this pending schedule
    conflicts = detector.get_conflicts_for_pending(pending_id)

    return jsonify({
        'success': True,
        'message': 'Schedule updated',
        'updated_schedule': {
            'id': pending.id,
            'employee_id': pending.employee_id,
            'schedule_datetime': pending.schedule_datetime.isoformat(),
            'conflict_detected': pending.conflict_detected,
            'conflicts': conflicts
        }
    })
```

Add new endpoint for conflict checking:
```python
@auto_scheduler_bp.route('/api/pending/<int:pending_id>/validate', methods=['POST'])
def validate_pending_edit(pending_id):
    """Validate proposed changes without saving"""
    from services.conflict_detection import ConflictDetector

    # ... validation logic ...

    return jsonify({
        'valid': is_valid,
        'errors': errors,
        'conflicts': potential_conflicts
    })
```

#### 2.3.3 Frontend Changes

**File:** `scheduler_app/templates/auto_schedule_review.html`
- Add Edit button to each pending schedule item
- Add conflict warning display area below each item
- Add modal for editing schedule details
- Add employee selector dropdown
- Add date/time picker

**New File:** `scheduler_app/static/js/schedule_editor.js`
```javascript
/**
 * Schedule Editor for Manual Edits with Conflict Detection
 */

class ScheduleEditor {
    constructor(pendingScheduleId) {
        this.pendingId = pendingScheduleId;
        this.modal = null;
        this.form = null;
    }

    async openEditor() {
        // Load current schedule data
        // Display edit modal
        // Populate form fields
    }

    async validateChanges(employeeId, scheduleDateTime) {
        // Call validation endpoint
        // Display errors if any
        // Return validation result
    }

    async saveChanges() {
        // Validate first
        // Submit changes
        // Update UI with conflicts
        // Refresh schedule list
    }

    displayConflicts(conflicts) {
        // Show conflict warnings below schedule item
        // Format conflict messages
        // Add click handlers to navigate to conflicting events
    }

    closeEditor() {
        // Close modal
        // Clear form
        // Reset state
    }
}

// Initialize editors for all schedule items
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.schedule-edit-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const pendingId = e.target.dataset.pendingId;
            const editor = new ScheduleEditor(pendingId);
            editor.openEditor();
        });
    });
});
```

**File:** `scheduler_app/static/css/schedule_editor.css`
- Modal styles
- Form field styles
- Conflict warning styles
- Edit button styles
- Responsive design

#### 2.3.4 UI/UX Workflow

**Edit Flow:**
1. User clicks "Edit" button on a pending schedule item
2. Modal opens with current schedule details
3. User can:
   - Select different employee from dropdown (filtered by constraints)
   - Change date using date picker
   - Change time using time picker
4. As user changes values, real-time validation occurs:
   - Invalid changes show error messages
   - Valid changes enable Save button
5. User clicks "Save"
6. Backend validates and detects conflicts
7. Response includes:
   - Success/failure status
   - Any constraint violations
   - List of conflicts
8. UI updates:
   - Schedule item shows new values
   - Conflict warnings appear below item
   - Other conflicting items also show warnings
9. User can:
   - Continue editing other items
   - Resolve conflicts by editing conflicting items
   - Approve despite conflicts (with warning confirmation)

**Conflict Display:**
```html
<div class="schedule-item" data-pending-id="123">
    <div class="schedule-details">
        <!-- Event name, employee, date/time -->
    </div>
    <div class="schedule-actions">
        <button class="schedule-edit-btn">Edit</button>
    </div>

    <!-- Conflict warnings (if any) -->
    <div class="schedule-conflicts" hidden>
        <div class="conflict-warning">
            ⚠️ Schedule Conflict: John Doe is also proposed to be scheduled to
            <a href="#pending-456" class="conflict-link">Supervisor - Walmart #5832</a>
            on Monday, January 15, 2025
        </div>
    </div>
</div>
```

---

## Part 3: Implementation Plan

### Phase 1: User Profile Dropdown (1-2 days)
1. Update auth.py to capture full name
2. Update base.html template
3. Create user_dropdown.js
4. Add dropdown styles to style.css
5. Test across all pages
6. Test dropdown behavior (open/close, click outside)

### Phase 2: Help System (2-3 days)
1. Create help blueprint and routes
2. Create help template directory structure
3. Write help content for each section:
   - Getting Started overview
   - Walmart credentials guide
   - Employee management guide
   - Auto scheduler explanation
   - Review/approve workflow
4. Create help.css stylesheet
5. Add Help link to navigation
6. Test navigation and content display
7. Review content for accuracy and completeness

### Phase 3: Conflict Detection Backend (2-3 days)
1. Add columns to pending_schedules table
2. Create database migration
3. Implement ConflictDetector service:
   - Hard constraint validation
   - Conflict detection logic
   - Conflict update methods
4. Write unit tests for ConflictDetector
5. Update edit_pending_schedule endpoint
6. Add validate_pending_edit endpoint
7. Test validation and conflict detection

### Phase 4: Manual Edit UI (2-3 days)
1. Create edit modal in auto_schedule_review.html
2. Implement ScheduleEditor class
3. Add edit buttons to schedule items
4. Create employee selector with constraint filtering
5. Add date/time pickers
6. Implement real-time validation
7. Create conflict warning display
8. Add conflict navigation (click to jump)
9. Style everything with schedule_editor.css
10. Test edit workflow end-to-end
11. Test conflict detection and display
12. Test approval with conflicts

### Phase 5: Integration Testing (1-2 days)
1. Test all features together
2. Test responsive design on mobile/tablet
3. Test accessibility (keyboard navigation, screen readers)
4. Performance testing (large number of pending schedules)
5. Cross-browser testing
6. Security testing (auth checks, input validation)

### Phase 6: Documentation and Deployment (1 day)
1. Update developer documentation
2. Create user guide (or add to Help system)
3. Update README if needed
4. Deploy to staging environment
5. User acceptance testing
6. Deploy to production

**Total Estimated Time:** 9-14 days (1.5-3 weeks)

---

## Part 4: API Endpoints Summary

### New Endpoints

**GET /help/**
- Returns help home page

**GET /help/getting-started**
- Returns getting started guide

**GET /help/walmart-credentials**
- Returns Walmart credentials guide

**GET /help/employee-management**
- Returns employee management guide

**GET /help/auto-scheduler**
- Returns auto scheduler guide

**GET /help/review-approve**
- Returns review/approve guide

**POST /auto-schedule/api/pending/{pending_id}/validate**
- Validates proposed schedule changes
- Request body:
  ```json
  {
    "employee_id": "US######",
    "schedule_datetime": "2025-01-15T09:00:00"
  }
  ```
- Response:
  ```json
  {
    "valid": true/false,
    "errors": ["error message 1", "error message 2"],
    "conflicts": [
      {
        "conflicting_pending_id": 123,
        "conflicting_event_name": "Event Name",
        "employee_name": "John Doe",
        "schedule_date": "2025-01-15"
      }
    ]
  }
  ```

### Modified Endpoints

**PUT /auto-schedule/api/pending/{pending_id}**
- Enhanced with validation and conflict detection
- New response fields:
  ```json
  {
    "success": true,
    "message": "Schedule updated",
    "updated_schedule": {
      "id": 123,
      "employee_id": "US######",
      "schedule_datetime": "2025-01-15T09:00:00",
      "conflict_detected": true,
      "conflicts": [...]
    }
  }
  ```

**GET /auto-schedule/api/pending**
- Enhanced to include conflict information
- Each pending schedule includes:
  ```json
  {
    "id": 123,
    "event_ref_num": 456,
    "event_name": "Core - Walmart #5832",
    "employee_name": "John Doe",
    "schedule_datetime": "2025-01-15T09:00:00",
    "conflict_detected": true,
    "conflicts": [...]
  }
  ```

---

## Part 5: Database Migrations

### Migration 1: Add conflict tracking to pending_schedules

**File:** `scheduler_app/migrations/versions/{timestamp}_add_conflict_tracking.py`

```python
"""Add conflict tracking to pending_schedules

Revision ID: {revision_id}
Revises: {previous_revision}
Create Date: 2025-01-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '{revision_id}'
down_revision = '{previous_revision}'
branch_labels = None
depends_on = None

def upgrade():
    # Add conflict_detected column
    op.add_column('pending_schedules',
        sa.Column('conflict_detected', sa.Boolean(), nullable=False, server_default='false'))

    # Add conflict_details column (JSON)
    op.add_column('pending_schedules',
        sa.Column('conflict_details', sa.JSON(), nullable=True))

    # Add index for conflict queries
    op.create_index('idx_pending_schedules_conflicts',
        'pending_schedules', ['scheduler_run_id', 'conflict_detected'])

def downgrade():
    op.drop_index('idx_pending_schedules_conflicts', table_name='pending_schedules')
    op.drop_column('pending_schedules', 'conflict_details')
    op.drop_column('pending_schedules', 'conflict_detected')
```

---

## Part 6: Security Considerations

### Authentication & Authorization
- All new endpoints require authentication (use @require_authentication() decorator)
- Help pages accessible to all authenticated users
- Settings access remains restricted (admin only if applicable)
- Validate user session before any edit operations

### Input Validation
- Sanitize all user inputs in edit forms
- Validate employee_id exists and is active
- Validate schedule_datetime is in valid format and future date
- Prevent SQL injection in all queries
- Use parameterized queries

### CSRF Protection
- All POST/PUT endpoints must include CSRF token validation
- Edit modal forms include CSRF token
- Validation endpoint requires CSRF token

### Data Integrity
- Transaction boundaries around conflict detection and updates
- Rollback on validation failures
- Prevent race conditions with proper locking
- Validate foreign key references

---

## Part 7: Testing Strategy

### Unit Tests
- `test_auth.py`: Test name extraction and session updates
- `test_conflict_detector.py`: Test all ConflictDetector methods
- `test_auto_scheduler_routes.py`: Test edit and validate endpoints
- `test_help_routes.py`: Test help page routes

### Integration Tests
- Test full edit workflow from UI to database
- Test conflict detection across multiple edits
- Test constraint validation with real data
- Test approval with conflicts

### E2E Tests
- Test complete user journey: login → review → edit → resolve conflicts → approve
- Test help navigation and content display
- Test user dropdown functionality

### Performance Tests
- Test conflict detection with 100+ pending schedules
- Test page load time with many conflicts
- Test database query performance

---

## Part 8: Success Metrics

### User Profile Dropdown
- User's full name is displayed correctly 100% of the time
- Dropdown opens/closes smoothly with no UI glitches
- Settings remains accessible in new location

### Help System
- Help pages load in < 1 second
- All help content is accurate and up-to-date
- Users can navigate easily between sections

### Manual Edit with Conflict Detection
- All hard constraints are enforced 100% of the time
- Conflicts are detected accurately within 1 second
- Conflict messages are clear and actionable
- Users can successfully resolve conflicts
- No invalid schedules are approved

---

## Part 9: Future Enhancements

### User Profile Dropdown
- Add user avatar/profile picture
- Add "View Profile" option to edit user settings
- Add notification badge for pending actions

### Help System
- Add search functionality
- Add video tutorials
- Add interactive walkthroughs
- Add FAQ section
- Add "What's New" section for feature updates

### Manual Edit
- Add bulk edit functionality
- Add drag-and-drop to reassign employees
- Add visual calendar view for editing
- Add conflict resolution suggestions
- Add AI-powered scheduling recommendations
- Add undo/redo functionality
- Add auto-save drafts

---

## Appendix A: File Structure

```
scheduler_app/
├── routes/
│   ├── auth.py (modified)
│   ├── auto_scheduler.py (modified)
│   └── help.py (new)
├── services/
│   └── conflict_detection.py (new)
├── templates/
│   ├── base.html (modified)
│   ├── auto_schedule_review.html (modified)
│   └── help/ (new)
│       ├── index.html
│       ├── getting_started.html
│       ├── walmart_credentials.html
│       ├── employee_management.html
│       ├── auto_scheduler.html
│       └── review_approve.html
├── static/
│   ├── js/
│   │   ├── user_dropdown.js (new)
│   │   └── schedule_editor.js (new)
│   └── css/
│       ├── style.css (modified)
│       ├── help.css (new)
│       └── schedule_editor.css (new)
├── models/
│   └── auto_scheduler.py (modified - add conflict fields)
└── migrations/
    └── versions/
        └── {timestamp}_add_conflict_tracking.py (new)
```

---

## Appendix B: Configuration

No new configuration variables required. All features use existing configuration.

---

## Appendix C: Dependencies

No new Python dependencies required. All features use existing Flask and SQLAlchemy capabilities.

---

## Sign-off

**Document Prepared By:** Claude (Architect)
**Reviewed By:** [To be filled]
**Approved By:** [To be filled]
**Approval Date:** [To be filled]

