# Data Models

**Project:** Flask Schedule Webapp
**Generated:** 2025-12-02 (Exhaustive Rescan)
**Scan Level:** Exhaustive
**Model Count:** 18 database models

## Overview

This document catalogs all database models, schema structure, relationships, and data architecture for the Flask Schedule Webapp. The application uses SQLAlchemy ORM with support for both PostgreSQL (production) and SQLite (development).

## Database Architecture

**Pattern:** Factory Pattern for Model Creation
**ORM:** SQLAlchemy 3.1.1
**Migrations:** Alembic via Flask-Migrate 4.0.5
**Database Support:**
- PostgreSQL (production)
- SQLite (development/testing)

All models are created using factory functions (`create_*_model(db)`) which enables:
- Dynamic model instantiation
- Easier testing with different database instances
- Centralized model registry

## Core Models

### Employee
**Table:** `employees`
**Purpose:** Employee roster and profile information

**Fields:**
- `id` (String, PK) - Employee identifier
- `name` (String, NOT NULL) - Full name
- `email` (String, UNIQUE) - Email address
- `phone` (String) - Contact number
- `active` (Boolean, DEFAULT TRUE) - Employment status
- `hire_date` (Date) - Date hired
- `termination_date` (Date, NULLABLE) - Date terminated
- `skills` (JSON) - Employee skill set and certifications
- `notes` (Text) - Additional notes

**Relationships:**
- One-to-Many with `Schedule`
- One-to-Many with `EmployeeAvailability`
- One-to-Many with `EmployeeWeeklyAvailability`
- One-to-Many with `EmployeeTimeOff`
- One-to-Many with `EmployeeAttendance`
- One-to-Many with `RotationAssignment`

### Event
**Table:** `events`
**Purpose:** Work events/projects from Crossmark API

**Fields:**
- `id` (Integer, PK, Auto-increment)
- `project_name` (Text, NOT NULL) - Event name/description
- `project_ref_num` (Integer, NOT NULL, UNIQUE) - Business identifier from Crossmark
- `location_mvid` (Text) - Location identifier
- `store_number` (Integer) - Store number
- `store_name` (Text) - Store name
- `start_datetime` (DateTime, NOT NULL) - Earliest schedule date
- `due_datetime` (DateTime, NOT NULL) - Latest schedule date
- `estimated_time` (Integer) - Duration in minutes
- `event_type` (String) - Setup, Demo, Juicer, Core, Other
- `condition` (String) - Unstaffed, Scheduled, Submitted, Paused, Reissued
- `last_synced` (DateTime) - Last sync from external API
- `sync_source` (String) - crossmark.mvretail.com
- `external_id` (String) - External system reference

**Relationships:**
- One-to-Many with `Schedule`
- One-to-One with `PendingSchedule`
- One-to-Many with `EventSchedulingOverride`

**Indexes:**
- `idx_condition` on `condition` (for filtering)
- `idx_event_type` on `event_type` (for filtering)
- `idx_dates` on `start_datetime, due_datetime` (for date range queries)

### Schedule
**Table:** `schedules`
**Purpose:** Employee-event assignments

**Fields:**
- `id` (Integer, PK, Auto-increment)
- `event_ref_num` (Integer, FK → events.project_ref_num, NOT NULL)
- `employee_id` (String, FK → employees.id, NOT NULL)
- `schedule_datetime` (DateTime, NOT NULL) - Assigned date and time
- `created_at` (DateTime, DEFAULT NOW) - When assignment was made
- `created_by` (String) - User who created assignment
- `modified_at` (DateTime) - Last modification time
- `status` (String) - pending, confirmed, completed, cancelled
- `notes` (Text) - Schedule-specific notes

**Relationships:**
- Many-to-One with `Event` (via event_ref_num)
- Many-to-One with `Employee` (via employee_id)
- One-to-One with `EmployeeAttendance`

**Constraints:**
- Unique constraint on `(event_ref_num, schedule_datetime)` - prevents double-booking events
- Foreign key constraints with CASCADE on delete

## Availability Models

### EmployeeWeeklyAvailability
**Table:** `employee_weekly_availability`
**Purpose:** Recurring weekly availability patterns

**Fields:**
- `id` (Integer, PK)
- `employee_id` (String, FK → employees.id)
- `day_of_week` (Integer, 0-6) - Monday=0, Sunday=6
- `start_time` (Time) - Available from
- `end_time` (Time) - Available until
- `effective_date` (Date) - When pattern starts

**Relationships:**
- Many-to-One with `Employee`

### EmployeeAvailability
**Table:** `employee_availability`
**Purpose:** Date-specific availability (overrides weekly pattern)

**Fields:**
- `id` (Integer, PK)
- `employee_id` (String, FK → employees.id)
- `date` (Date, NOT NULL)
- `available` (Boolean) - True if available
- `start_time` (Time, NULLABLE) - Available from
- `end_time` (Time, NULLABLE) - Available until
- `reason` (Text) - Why unavailable or notes

**Relationships:**
- Many-to-One with `Employee`

**Indexes:**
- `idx_date_employee` on `(date, employee_id)` (for availability queries)

### EmployeeTimeOff
**Table:** `employee_time_off`
**Purpose:** Time-off requests and approvals

**Fields:**
- `id` (Integer, PK)
- `employee_id` (String, FK → employees.id)
- `start_date` (Date, NOT NULL)
- `end_date` (Date, NOT NULL)
- `reason` (String) - Vacation, Sick, Personal, etc.
- `status` (String) - pending, approved, denied
- `requested_at` (DateTime)
- `approved_by` (String)
- `approved_at` (DateTime)
- `notes` (Text)

**Relationships:**
- Many-to-One with `Employee`

### EmployeeAvailabilityOverride
**Table:** `employee_availability_overrides`
**Purpose:** Temporary availability changes

**Fields:**
- `id` (Integer, PK)
- `employee_id` (String, FK → employees.id)
- `date` (Date)
- `available` (Boolean)
- `reason` (Text)
- `created_at` (DateTime)

**Relationships:**
- Many-to-One with `Employee`

## Auto-Scheduler Models

### RotationAssignment
**Table:** `rotation_assignments`
**Purpose:** Daily role rotations (Juicer, Primary Lead)

**Fields:**
- `id` (Integer, PK)
- `employee_id` (String, FK → employees.id)
- `date` (Date, NOT NULL)
- `rotation_type` (String) - Juicer, Primary Lead
- `assigned_at` (DateTime)

**Relationships:**
- Many-to-One with `Employee`

**Indexes:**
- Unique constraint on `(date, rotation_type)` - one person per role per day

### PendingSchedule
**Table:** `pending_schedules`
**Purpose:** Auto-scheduler proposals awaiting approval

**Fields:**
- `id` (Integer, PK)
- `event_ref_num` (Integer, FK → events.project_ref_num, UNIQUE)
- `employee_id` (String, FK → employees.id)
- `schedule_datetime` (DateTime)
- `confidence_score` (Float) - Algorithm confidence (0.0-1.0)
- `reason` (Text) - Why this assignment was chosen
- `created_at` (DateTime)
- `reviewed` (Boolean, DEFAULT FALSE)
- `approved` (Boolean, NULLABLE)

**Relationships:**
- One-to-One with `Event`
- Many-to-One with `Employee`

### SchedulerRunHistory
**Table:** `scheduler_run_history`
**Purpose:** Auto-scheduler execution logs

**Fields:**
- `id` (Integer, PK)
- `run_at` (DateTime, NOT NULL)
- `date_range_start` (Date)
- `date_range_end` (Date)
- `events_processed` (Integer)
- `events_assigned` (Integer)
- `events_failed` (Integer)
- `execution_time_seconds` (Float)
- `settings_snapshot` (JSON) - Scheduler config at runtime
- `error_log` (Text)

### ScheduleException
**Table:** `schedule_exceptions`
**Purpose:** Auto-scheduler constraint violations and warnings

**Fields:**
- `id` (Integer, PK)
- `schedule_id` (Integer, FK → schedules.id, NULLABLE)
- `event_ref_num` (Integer, FK → events.project_ref_num)
- `exception_type` (String) - conflict, coverage, availability, skill_mismatch
- `severity` (String) - info, warning, error, critical
- `message` (Text)
- `detected_at` (DateTime)
- `resolved` (Boolean, DEFAULT FALSE)

**Relationships:**
- Many-to-One with `Schedule` (optional)
- Many-to-One with `Event`

### EventSchedulingOverride
**Table:** `event_scheduling_overrides`
**Purpose:** Manual constraints for specific events

**Fields:**
- `id` (Integer, PK)
- `event_ref_num` (Integer, FK → events.project_ref_num)
- `required_employee_id` (String, FK → employees.id, NULLABLE)
- `excluded_employee_ids` (JSON) - Array of employee IDs to exclude
- `preferred_time` (Time, NULLABLE)
- `notes` (Text)
- `created_at` (DateTime)

**Relationships:**
- Many-to-One with `Event`
- Many-to-One with `Employee` (for required employee)

## System Models

### SystemSetting
**Table:** `system_settings`
**Purpose:** Application configuration stored in database

**Fields:**
- `id` (Integer, PK)
- `key` (String, UNIQUE, NOT NULL) - Setting identifier
- `value` (Text) - Setting value (JSON or string)
- `data_type` (String) - string, int, bool, json, encrypted
- `description` (Text) - What this setting does
- `category` (String) - General, Scheduler, Sync, Security
- `encrypted` (Boolean, DEFAULT FALSE) - Is value encrypted?
- `modified_at` (DateTime)
- `modified_by` (String)

**Common Settings:**
- `core_timeslots` - JSON array of core event times
- `auto_scheduler_enabled` - Boolean
- `sync_interval_minutes` - Integer
- `max_events_per_employee_per_day` - Integer

### UserSession
**Table:** `user_sessions`
**Purpose:** Active session tracking for Crossmark API

**Fields:**
- `id` (Integer, PK)
- `session_token` (String, UNIQUE) - External API session token
- `created_at` (DateTime)
- `expires_at` (DateTime)
- `last_refreshed` (DateTime)
- `active` (Boolean, DEFAULT TRUE)

### PaperworkTemplate
**Table:** `paperwork_templates`
**Purpose:** PDF templates for event paperwork

**Fields:**
- `id` (Integer, PK)
- `name` (String, NOT NULL)
- `description` (Text)
- `template_type` (String) - daily, event_specific, summary
- `template_data` (JSON) - Template structure and fields
- `active` (Boolean, DEFAULT TRUE)

## Audit & Tracking Models

### AuditLog
**Table:** `audit_logs`
**Purpose:** System activity audit trail

**Fields:**
- `id` (Integer, PK)
- `timestamp` (DateTime, NOT NULL, DEFAULT NOW)
- `user_id` (String) - User who performed action
- `action` (String) - create, update, delete, login, etc.
- `resource_type` (String) - employee, event, schedule
- `resource_id` (String) - ID of affected resource
- `changes` (JSON) - Before/after values
- `ip_address` (String)
- `user_agent` (String)

**Indexes:**
- `idx_timestamp` on `timestamp` (for log queries)
- `idx_resource` on `(resource_type, resource_id)` (for resource history)

### AuditNotificationSettings
**Table:** `audit_notification_settings`
**Purpose:** Alert configuration for audit events

**Fields:**
- `id` (Integer, PK)
- `event_type` (String) - What triggers notification
- `enabled` (Boolean)
- `notification_method` (String) - email, sms, webhook
- `recipients` (JSON) - Array of notification targets

### EmployeeAttendance
**Table:** `employee_attendance`
**Purpose:** Event attendance tracking

**Fields:**
- `id` (Integer, PK)
- `schedule_id` (Integer, FK → schedules.id, UNIQUE)
- `employee_id` (String, FK → employees.id)
- `status` (String) - present, absent, excused, unreported
- `check_in_time` (DateTime)
- `check_out_time` (DateTime)
- `method` (String) - qr_code, manual, auto
- `notes` (Text)
- `recorded_by` (String)
- `recorded_at` (DateTime)

**Relationships:**
- One-to-One with `Schedule`
- Many-to-One with `Employee`

## Database Migrations

**Location:** `migrations/versions/`
**Tool:** Alembic via Flask-Migrate

**Key Migrations:**
1. `1bc16a06f62e` - Initial database schema
2. `62eca6d029af` - Add auto_scheduler tables and event tracking
3. `0be04acd9951` - Add system_settings table

**Running Migrations:**
```bash
# Upgrade to latest
flask db upgrade

# Create new migration
flask db migrate -m "Description"

# Downgrade
flask db downgrade
```

## Data Relationships Diagram

```
Employee ────┬──── Schedule ──── Event
             │         │
             ├──── EmployeeWeeklyAvailability
             ├──── EmployeeAvailability
             ├──── EmployeeTimeOff
             ├──── EmployeeAttendance
             └──── RotationAssignment

Event ────┬──── Schedule
          ├──── PendingSchedule
          ├──── EventSchedulingOverride
          └──── ScheduleException

Schedule ──── EmployeeAttendance
          └──── ScheduleException
```

## Indexing Strategy

**Optimized Indexes:**
- Date range queries on `events.start_datetime` and `events.due_datetime`
- Employee lookups on `schedules.employee_id`
- Event condition filtering on `events.condition`
- Availability date lookups on `employee_availability.date`
- Audit log timestamp queries on `audit_logs.timestamp`

## Data Integrity

**Foreign Key Constraints:** Enabled (including for SQLite via PRAGMA)
**Cascade Deletes:** Configured for dependent records
**Unique Constraints:** Prevent duplicate schedules and assignments
**NOT NULL Constraints:** Enforce required fields

## Performance Considerations

- **Connection Pooling:** Configured in production (pool_size=10, max_overflow=20)
- **Pool Pre-ping:** Enabled to detect stale connections
- **Pool Recycle:** Connections recycled every 3600 seconds
- **Query Optimization:** Date range queries use indexed columns
- **Batch Operations:** Available for bulk imports and updates

## Notes for Development

- All datetime fields are timezone-aware (America/Indiana/Indianapolis)
- JSON fields support complex data structures
- Encrypted fields use AES-256 via cryptography library
- Model registry pattern allows dynamic model access via `get_models()`
- Factory pattern enables easier testing with in-memory databases
