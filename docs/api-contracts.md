# API Contracts

**Project:** Flask Schedule Webapp
**Generated:** 2025-11-20
**Scan Level:** Exhaustive

## Overview

This document catalogs all REST API endpoints exposed by the Flask Schedule Webapp, including request/response formats, authentication requirements, and usage examples.

## API Organization

The application uses Flask Blueprints to organize API endpoints into logical modules:

- **Main Routes** (`/`) - Dashboard and view pages
- **Scheduling Routes** (`/schedule`) - Event scheduling operations
- **API Routes** (`/api`) - RESTful API endpoints
- **Employee Routes** (`/employees`) - Employee management
- **Auto-Scheduler Routes** (`/auto-scheduler`) - Automated scheduling
- **Authentication Routes** (`/auth`) - Login/logout
- **Admin Routes** (`/admin`) - Administrative functions
- **Printing Routes** (`/print`) - Report generation
- **EDR Sync Routes** (`/edr`) - External data sync
- **Health Routes** (`/health`) - System health checks
- **AI Routes** (`/ai`) - AI assistant endpoints

## Authentication

Most endpoints require authentication via session cookies. Protected routes use the `@require_authentication()` decorator.

## Core API Endpoints

### Event Management

#### Get Daily Event Summary
```
GET /api/daily-summary/<date>
```

**Description:** Get event type counts and timeslot coverage for a specific date

**Parameters:**
- `date` (path) - Date in YYYY-MM-DD format

**Response:**
```json
{
  "event_types": {
    "Setup": 5,
    "Demo": 3,
    "Juicer": 2,
    "Other": 1
  },
  "total_events": 11,
  "timeslot_coverage": {
    "09:45:00": 4,
    "10:30:00": 2,
    "11:00:00": 0,
    "11:30:00": 3
  }
}
```

#### Get Daily Events
```
GET /api/daily-events/<date>
```

**Description:** Retrieve all scheduled events for a specific date with full details

**Parameters:**
- `date` (path) - Date in YYYY-MM-DD format

**Response:** Array of event objects with schedule details

#### Get Available Employees
```
GET /api/available_employees/<date>
GET /api/available_employees/<date>/<event_id>
```

**Description:** Get list of employees available for scheduling on a specific date

**Parameters:**
- `date` (path) - Date in YYYY-MM-DD format
- `event_id` (path, optional) - Event ID for context-specific availability
- `override` (query, optional) - Set to 'true' to bypass constraints

**Response:** Array of available employee objects

### Scheduling Operations

#### Schedule Event
```
POST /save_schedule
```

**Description:** Create or update an event schedule

**Request Body:**
```json
{
  "event_id": 123,
  "employee_id": "EMP001",
  "schedule_date": "2025-11-20",
  "schedule_time": "09:45"
}
```

#### Reschedule Event
```
POST /api/reschedule
```

**Description:** Modify an existing schedule

### Employee Management

#### Get Employee List
```
GET /employees
GET /api/employees
```

**Description:** Retrieve employee roster with availability status

#### Import Employees
```
POST /employees/import
```

**Description:** Bulk import employees from CSV

**Request:** Multipart form data with CSV file

#### Terminate Employee
```
POST /api/employees/<employee_id>/terminate
```

**Description:** Mark employee as terminated with optional final date

### Attendance Tracking

#### Record Attendance
```
POST /api/attendance/record
```

**Description:** Log employee attendance for an event

**Request Body:**
```json
{
  "schedule_id": 456,
  "employee_id": "EMP001",
  "status": "present",
  "timestamp": "2025-11-20T09:45:00"
}
```

#### Get Attendance Report
```
GET /api/attendance/report
```

**Description:** Generate attendance report for date range

**Query Parameters:**
- `start_date` - Start of date range
- `end_date` - End of date range
- `employee_id` (optional) - Filter by employee

### Auto-Scheduler

#### Run Auto-Scheduler
```
POST /auto-scheduler/run
```

**Description:** Execute automated event assignment

**Request Body:**
```json
{
  "date_range_start": "2025-11-20",
  "date_range_end": "2025-11-27",
  "event_types": ["Setup", "Demo"]
}
```

#### Get Scheduler Settings
```
GET /api/auto-scheduler/settings
```

**Description:** Retrieve auto-scheduler configuration

#### Update Scheduler Settings
```
POST /api/auto-scheduler/settings
```

**Description:** Modify auto-scheduler behavior and constraints

### Availability Management

#### Get Employee Availability
```
GET /api/employees/<employee_id>/availability
```

**Description:** Retrieve employee availability patterns and time-off

#### Update Weekly Availability
```
POST /api/employees/<employee_id>/availability/weekly
```

**Description:** Set recurring weekly availability pattern

**Request Body:**
```json
{
  "monday": ["09:00-17:00"],
  "tuesday": ["09:00-17:00"],
  "wednesday": [],
  "thursday": ["09:00-12:00"],
  "friday": ["09:00-17:00"]
}
```

#### Add Availability Override
```
POST /api/availability/override
```

**Description:** Create specific date availability exception

**Request Body:**
```json
{
  "employee_id": "EMP001",
  "date": "2025-11-20",
  "available": false,
  "reason": "Personal day"
}
```

### Schedule Validation

#### Validate Schedule
```
GET /api/validate-schedule/<date>
```

**Description:** Run validation checks on scheduled events for a date

**Response:**
```json
{
  "valid": false,
  "warnings": [
    {
      "type": "coverage",
      "message": "Core timeslot 10:30 has insufficient coverage",
      "severity": "high"
    }
  ],
  "errors": [
    {
      "type": "conflict",
      "message": "Employee EMP001 double-booked at 09:45",
      "severity": "critical"
    }
  ]
}
```

### External Sync

#### Sync Events from Crossmark
```
POST /api/sync/events
```

**Description:** Pull events from Crossmark API (crossmark.mvretail.com)

**Request Body:**
```json
{
  "date_range_start": "2025-11-20",
  "date_range_end": "2025-11-27"
}
```

#### Sync EDR Data
```
POST /edr/sync
```

**Description:** Sync sales data from Walmart Retail Link

### Reporting & Export

#### Export Schedule CSV
```
GET /api/export/schedule
```

**Description:** Download scheduled events as CSV

**Query Parameters:**
- `start_date` - Start of date range
- `end_date` - End of date range

#### Generate Paperwork
```
POST /api/paperwork/generate
```

**Description:** Create event paperwork PDFs with EDR data

**Request Body:**
```json
{
  "schedule_id": 456,
  "template_id": 1
}
```

### AI Assistant

#### Chat with AI
```
POST /ai/chat
```

**Description:** Send natural language query to AI assistant

**Request Body:**
```json
{
  "message": "Show me all unscheduled Setup events for tomorrow",
  "context": {}
}
```

**Response:**
```json
{
  "response": "I found 5 unscheduled Setup events for 2025-11-21...",
  "data": [...],
  "suggestions": [...]
}
```

### System Health

#### Health Check
```
GET /health
GET /api/health
```

**Description:** System health status

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "external_api": "connected",
  "redis": "connected",
  "timestamp": "2025-11-20T17:45:00Z"
}
```

## Response Status Codes

- **200 OK** - Successful request
- **201 Created** - Resource created successfully
- **400 Bad Request** - Invalid request parameters
- **401 Unauthorized** - Authentication required
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Resource does not exist
- **409 Conflict** - Scheduling conflict or constraint violation
- **422 Unprocessable Entity** - Validation failed
- **500 Internal Server Error** - Server error

## Rate Limiting

API endpoints are rate-limited in production:
- **Default:** 100 requests per hour per IP
- **Authentication endpoints:** 20 requests per hour per IP

## Error Response Format

```json
{
  "error": "Error message",
  "details": "Additional context",
  "code": "ERROR_CODE",
  "timestamp": "2025-11-20T17:45:00Z"
}
```

## WebSocket Support

Currently, the application uses traditional HTTP requests. Real-time updates are achieved through polling or page refresh.

## API Versioning

Currently at version 1.2 (cache busting version). No formal API versioning scheme in place.

## Notes for Development

- All datetime values use ISO 8601 format
- Date-only values use YYYY-MM-DD format
- Time-only values use HH:MM:SS format
- Timezone is America/Indiana/Indianapolis (configured in settings)
- CSRF protection enabled for state-changing operations
- Session-based authentication with secure cookies in production
