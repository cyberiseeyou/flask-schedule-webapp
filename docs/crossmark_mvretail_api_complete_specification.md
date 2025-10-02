# Crossmark MVRetail Complete API Specification

## Overview
The Crossmark MVRetail API provides comprehensive endpoints for field service management, including scheduling operations for field representatives, event creation, updates, availability management, reporting, and general system operations.

**Base URL:** `https://crossmark.mvretail.com`  
**Protocol:** HTTPS  
**Server:** Apache  
**Authentication:** Session-based (cookie authentication)  
**Security:** 
- Strict-Transport-Security: max-age=63072000; includeSubdomains
- Session-based authentication
- CORS headers for cross-origin requests

---

## Authentication Endpoints

### 1. User Authentication
**POST** `/login/authenticate`  
**Content-Type:** `application/json`  
**Description:** Authenticates user credentials for system access and establishes a session

#### Request Headers:
```json
{
  "Accept": "application/json, text/plain, */*",
  "Content-Type": "application/json"
}
```

#### Request Body:
```json
{
  "username": "string",
  "password": "string"
}
```

#### Response:
```json
{
  "success": true,
  "sessionId": "string",
  "userId": "string"
}
```

**Status Codes:**
- `200 OK` - Successful authentication
- `401 Unauthorized` - Invalid credentials

---

## User Management Endpoints

### 2. Get User Locale
**GET** `/users/getUserLocale`  
**POST** `/users/getUserLocale` *(Both methods supported)*  
**Description:** Retrieves the user's language/locale preferences

#### Response:
```json
{
  "locale": "en-US",
  "timezone": "America/New_York",
  "dateFormat": "MM/DD/YYYY"
}
```

### 3. Get User Information
**POST** `/users/getUserInfo`  
**Description:** Retrieves detailed information about the authenticated user including roles and permissions

#### Response Headers:
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Headers: X-Requested-With`

#### Response Body:
```json
{
  "userId": "string",
  "username": "string",
  "email": "string",
  "firstName": "string",
  "lastName": "string",
  "role": "string",
  "permissions": ["array"],
  "organizationId": "string"
}
```

---

## Configuration & Settings Endpoints

### 4. Get Client Logo
**POST** `/miscextcontroller/getClientLogo`  
**Description:** Retrieves the client's custom logo for branding

#### Response:
```json
{
  "logoUrl": "string",
  "altText": "string"
}
```
*Alternative response: Base64 encoded image data*

### 5. Get Current Branch Info
**POST** `/miscextcontroller/getCurrentBranchInfo`  
**Description:** Retrieves information about the current deployment branch/environment

#### Response:
```json
{
  "branch": "production",
  "version": "2.1.0",
  "buildNumber": "1234",
  "environment": "production"
}
```

### 6. Get Appetize Preference
**POST** `/login/getAppetizePreference`  
**Description:** Retrieves mobile app preview preferences (Appetize.io integration)

#### Response:
- **Status:** 200 OK
- **Content-Type:** `text/html; charset="utf-8"`

---

## Single Sign-On (SSO) Endpoints

### 7. Get SSO Provider Names
**POST** `/sso/getSSOProviderNames`  
**Description:** Retrieves list of available SSO providers for authentication

#### Response:
- **Status:** 404 Not Found (when SSO is not configured)
- **Content-Type:** `application/json`

### 8. Get SSO Error
**POST** `/sso/getError`  
**Content-Type:** `multipart/form-data`  
**Description:** Retrieves SSO error messages if authentication fails

#### Response:
```json
{
  "error": null
}
```
*Empty when no errors*

---

## Navigation & UI Endpoints

### 9. Get Navigation Options
**POST** `/navUtils/getNavOptions`  
**Description:** Retrieves navigation menu configuration based on user permissions

#### Response:
```json
{
  "navigation": [
    {
      "id": "dashboard",
      "label": "Dashboard",
      "url": "/dashboard",
      "icon": "dashboard",
      "children": []
    },
    {
      "id": "scheduling",
      "label": "Scheduling",
      "url": "/scheduling",
      "icon": "calendar",
      "children": [
        {
          "id": "hourly",
          "label": "Hourly View",
          "url": "/scheduling/hourly"
        },
        {
          "id": "daily",
          "label": "Daily View",
          "url": "/scheduling/daily"
        }
      ]
    }
  ]
}
```

---

## Scheduling Controller Endpoints

### 10. Get Scheduling Preferences
**POST** `/schedulingcontroller/getSchedulingPrefs`  
**Description:** Retrieves scheduling preferences and configuration for the current user

#### Response:
```json
{
  "defaultView": "month|week|day",
  "workingHours": {
    "start": "08:00",
    "end": "17:00"
  },
  "timeSlotDuration": 30,
  "allowWeekends": false,
  "autoScheduling": {
    "enabled": false,
    "rules": []
  }
}
```

### 11. Get Full Calendar License Key
**POST** `/schedulingcontroller/getFullCalendarLicenseKey`  
**Description:** Retrieves the FullCalendar license key for the calendar component

#### Response:
```json
{
  "licenseKey": "string"
}
```

### 12. Get Available Representatives
**POST** `/schedulingcontroller/getAvailableReps`  
**Description:** Retrieves a list of available field representatives for scheduling

#### Request Body (Optional):
```json
{
  "startDate": "YYYY-MM-DD",
  "endDate": "YYYY-MM-DD",
  "locationId": "string",
  "skillRequired": ["array"]
}
```

#### Response:
```json
{
  "representatives": [
    {
      "repId": "string",
      "name": "string",
      "email": "string",
      "phone": "string",
      "availability": {
        "monday": ["09:00-17:00"],
        "tuesday": ["09:00-17:00"],
        "wednesday": ["09:00-17:00"],
        "thursday": ["09:00-17:00"],
        "friday": ["09:00-17:00"]
      },
      "skills": ["array"],
      "currentLoad": 0.75,
      "maxCapacity": 40
    }
  ]
}
```

### 13. Get Scheduled Events
**POST** `/schedulingcontroller/getScheduledEvents`  
**Description:** Retrieves scheduled events within a date range

#### Request Body:
```json
{
  "startDate": "YYYY-MM-DD",
  "endDate": "YYYY-MM-DD",
  "repId": "string (optional)",
  "locationId": "string (optional)",
  "status": "scheduled|completed|cancelled (optional)"
}
```

#### Response:
```json
{
  "events": [
    {
      "eventId": "string",
      "title": "string",
      "description": "string",
      "startDateTime": "ISO 8601",
      "endDateTime": "ISO 8601",
      "repId": "string",
      "repName": "string",
      "locationId": "string",
      "locationName": "string",
      "status": "scheduled|in-progress|completed|cancelled",
      "type": "regular|emergency|training",
      "priority": "low|medium|high",
      "notes": "string",
      "createdBy": "string",
      "createdAt": "ISO 8601",
      "modifiedAt": "ISO 8601"
    }
  ],
  "totalCount": 100
}
```

### 14. Get Non-Scheduled Visits
**POST** `/schedulingcontroller/getNonScheduledVisits`  
**Description:** Retrieves visits that need to be scheduled

#### Response:
```json
{
  "visits": [
    {
      "visitId": "string",
      "locationId": "string",
      "locationName": "string",
      "requiredDate": "YYYY-MM-DD",
      "estimatedDuration": 60,
      "priority": "low|medium|high",
      "requirements": {
        "skills": ["array"],
        "certifications": ["array"]
      },
      "notes": "string"
    }
  ],
  "totalUnscheduled": 50
}
```

### 15. Get More Filters Options
**POST** `/schedulingcontroller/getMoreFiltersOptions`  
**Description:** Retrieves additional filter options for the scheduling interface

#### Response:
```json
{
  "filters": {
    "locations": [
      {
        "id": "string",
        "name": "string",
        "region": "string"
      }
    ],
    "representatives": [
      {
        "id": "string",
        "name": "string"
      }
    ],
    "eventTypes": ["regular", "emergency", "training"],
    "statuses": ["scheduled", "in-progress", "completed", "cancelled"],
    "priorities": ["low", "medium", "high"]
  }
}
```

### 16. Save Scheduled Event
**POST** `/schedulingcontroller/saveScheduledEvent`  
**Description:** Creates a new scheduled event

#### Request Body:
```json
{
  "title": "string",
  "description": "string",
  "startDateTime": "ISO 8601",
  "endDateTime": "ISO 8601",
  "repId": "string",
  "locationId": "string",
  "type": "regular|emergency|training",
  "priority": "low|medium|high",
  "recurrence": {
    "enabled": false,
    "pattern": "daily|weekly|monthly",
    "endDate": "YYYY-MM-DD"
  },
  "notifications": {
    "email": true,
    "sms": false,
    "reminderMinutes": 30
  },
  "notes": "string"
}
```

#### Response:
```json
{
  "success": true,
  "eventId": "string",
  "message": "Event created successfully"
}
```

### 17. Update Scheduled Event
**POST** `/schedulingcontroller/updateScheduledEvent`  
**Description:** Updates an existing scheduled event

#### Request Body:
```json
{
  "eventId": "string",
  "updates": {
    "title": "string (optional)",
    "description": "string (optional)",
    "startDateTime": "ISO 8601 (optional)",
    "endDateTime": "ISO 8601 (optional)",
    "repId": "string (optional)",
    "locationId": "string (optional)",
    "status": "string (optional)",
    "notes": "string (optional)"
  }
}
```

#### Response:
```json
{
  "success": true,
  "message": "Event updated successfully",
  "updatedFields": ["array"]
}
```

### 18. Delete Scheduled Event
**POST** `/schedulingcontroller/deleteScheduledEvent`  
**Description:** Deletes a scheduled event

#### Request Body:
```json
{
  "eventId": "string",
  "reason": "string (optional)",
  "notifyRep": true
}
```

#### Response:
```json
{
  "success": true,
  "message": "Event deleted successfully"
}
```

### 19. Get Event Details
**POST** `/schedulingcontroller/getEventDetails`  
**Description:** Retrieves detailed information about a specific event

#### Request Body:
```json
{
  "eventId": "string"
}
```

#### Response:
```json
{
  "event": {
    "eventId": "string",
    "title": "string",
    "description": "string",
    "startDateTime": "ISO 8601",
    "endDateTime": "ISO 8601",
    "duration": 60,
    "rep": {
      "id": "string",
      "name": "string",
      "email": "string",
      "phone": "string"
    },
    "location": {
      "id": "string",
      "name": "string",
      "address": "string",
      "coordinates": {
        "latitude": 0.0,
        "longitude": 0.0
      }
    },
    "status": "string",
    "type": "string",
    "priority": "string",
    "history": [
      {
        "action": "created|modified|cancelled",
        "timestamp": "ISO 8601",
        "user": "string",
        "changes": {}
      }
    ],
    "attachments": [],
    "customFields": {}
  }
}
```

### 20. Get Rep Availability
**POST** `/schedulingcontroller/getRepAvailability`  
**Description:** Checks availability for a specific representative

#### Request Body:
```json
{
  "repId": "string",
  "startDate": "YYYY-MM-DD",
  "endDate": "YYYY-MM-DD"
}
```

#### Response:
```json
{
  "availability": [
    {
      "date": "YYYY-MM-DD",
      "availableSlots": [
        {
          "start": "09:00",
          "end": "10:00",
          "available": true
        }
      ],
      "totalAvailableHours": 8,
      "bookedHours": 4,
      "utilization": 0.5
    }
  ]
}
```

### 21. Bulk Schedule Events
**POST** `/schedulingcontroller/bulkScheduleEvents`  
**Description:** Creates multiple scheduled events in a single request

#### Request Body:
```json
{
  "events": [
    {
      "title": "string",
      "startDateTime": "ISO 8601",
      "endDateTime": "ISO 8601",
      "repId": "string",
      "locationId": "string"
    }
  ],
  "validateConflicts": true,
  "autoResolveConflicts": false
}
```

#### Response:
```json
{
  "success": true,
  "created": 10,
  "failed": 2,
  "results": [
    {
      "index": 0,
      "success": true,
      "eventId": "string"
    },
    {
      "index": 1,
      "success": false,
      "error": "Conflict with existing event"
    }
  ]
}
```

---

## Planning Module Endpoints

### 22. Planning Dashboard
**GET** `/planning/`  
**Description:** Main planning dashboard page (HTML)

#### Response:
- **Status:** 200 OK
- **Content-Type:** `text/html; charset="utf-8"`

### 23. Rep Schedule
**GET** `/rep/schedule/`  
**Description:** Representative scheduling interface

#### Response:
- **Status:** 200 OK
- **Content-Type:** `text/html; charset="utf-8"`

---

## Internationalization (i18n) Endpoints

### 24. Get Language Translations
**GET** `/i18n/{language}.json`  
**Example:** `/i18n/en.json`  
**Description:** Retrieves translation strings for the specified language

#### Response:
```json
{
  "welcome": "Welcome",
  "login": "Login",
  "logout": "Logout",
  "schedule": "Schedule",
  "save": "Save",
  "cancel": "Cancel",
  // ... more translation key-value pairs
}
```

---

## Common Response Headers

All API responses include the following security headers:
```
Strict-Transport-Security: max-age=63072000; includeSubdomains
Cache-Control: no-cache, max-age=0, must-revalidate
Pragma: no-cache
Expires: Thu, 19 Nov 1981 08:52:00 GMT
Server: Apache
Access-Control-Allow-Origin: * (where applicable)
Access-Control-Allow-Headers: X-Requested-With (where applicable)
```

---

## Error Handling

### Standard Error Response Format
```json
{
  "error": true,
  "message": "Error description",
  "code": "ERROR_CODE",
  "details": {
    "field": "Additional error details"
  },
  "timestamp": "ISO 8601"
}
```

### Common HTTP Status Codes
- **200 OK** - Successful request
- **201 Created** - Resource created successfully
- **400 Bad Request** - Invalid request parameters
- **401 Unauthorized** - Authentication required
- **403 Forbidden** - Access denied / Insufficient permissions
- **404 Not Found** - Resource not found or feature not available
- **409 Conflict** - Resource conflict (e.g., scheduling conflict)
- **500 Internal Server Error** - Server-side error

---

## Rate Limiting

The API implements rate limiting to prevent abuse:
- **Default limit:** 1000 requests per hour per authenticated user
- **Burst limit:** 100 requests per minute
- Rate limit headers are included in responses:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

---

## Data Types and Formats

### DateTime Format
All date and time values use ISO 8601 format:
- Date: `YYYY-MM-DD`
- DateTime: `YYYY-MM-DDTHH:mm:ss.sssZ`
- Time: `HH:mm` (24-hour format)

### Common Enumerations

**Event Status:**
- `scheduled` - Event is scheduled
- `in-progress` - Event is currently being executed
- `completed` - Event has been completed
- `cancelled` - Event has been cancelled

**Event Type:**
- `regular` - Regular scheduled visit
- `emergency` - Emergency or urgent visit
- `training` - Training session

**Priority:**
- `low` - Low priority
- `medium` - Medium priority
- `high` - High priority

**View Types:**
- `month` - Monthly calendar view
- `week` - Weekly calendar view
- `day` - Daily calendar view

---

## Authentication Flow

1. User accesses the application at `/login`
2. Application loads React-based login interface
3. User submits credentials to `/login/authenticate`
4. Upon successful authentication, session cookie is set
5. User is redirected to dashboard
6. Session cookie is used for all subsequent API requests

---

## Technology Stack

### Frontend:
- **React.js** - Modern UI components
- **ExtJS** - Legacy interfaces (ongoing migration)
- **jQuery** - DOM manipulation
- **FullCalendar** - Calendar component
- **Moment.js** - Date handling
- **Bootstrap CSS** - Framework styling

### Backend:
- **Apache** - Web server
- **Session-based authentication** - Cookie authentication
- **JSON API** - RESTful-style endpoints
- **GZIP compression** - Response compression

### Security Features:
- **HTTPS enforced** - Via HSTS headers
- **CORS support** - For approved domains
- **Session management** - Secure cookie handling
- **Cache control** - Prevents sensitive data caching

---

## Static Resources

### JavaScript Libraries
- `/extjs/` - ExtJS framework files
- `/main/javascript/lib/jquery/` - jQuery library
- `/main/javascript/react/` - React components
- `/main/javascript/moment/` - Moment.js date library

### CSS Resources
- `/extjs/resources/css/` - ExtJS styles
- `/main/css/` - Application custom styles
- Component-specific stylesheets

### Image Assets
- `/main/images/` - Application images
- `/favicon.ico` - Site favicon
- Client logos and branding

---

## API Best Practices

### Request Guidelines
1. **Authentication Required:** Most endpoints require an authenticated session
2. **Content-Type:** All POST requests should use `Content-Type: application/json`
3. **Pagination:** Use `page` and `pageSize` parameters for list endpoints
4. **Filtering:** Most list endpoints support query parameter filtering
5. **Date Handling:** Always use ISO 8601 format for dates

### Performance Optimization
1. **Caching:** Respect cache headers; implement client-side caching where appropriate
2. **Batch Operations:** Use bulk endpoints when processing multiple items
3. **Pagination:** Request only necessary data using pagination
4. **Compression:** Server supports GZIP; ensure client accepts compressed responses

---

## Recommendations for API Enhancement

1. **RESTful Design:** Consider migrating POST endpoints to appropriate HTTP methods (GET for retrieval, PUT for updates, DELETE for deletions)
2. **API Versioning:** Implement version numbers in URLs (e.g., `/api/v1/`)
3. **Documentation:** Provide OpenAPI/Swagger documentation for interactive testing
4. **Rate Limiting:** More granular rate limiting with clear documentation
5. **Error Consistency:** Ensure all endpoints use the same error response format
6. **Authentication:** Consider implementing OAuth 2.0 or JWT tokens for modern authentication
7. **Webhooks:** Add webhook support for real-time event notifications
8. **GraphQL:** Consider GraphQL for more flexible data querying

---

## Version History

- **v1.0** - Initial API specification
- **v1.1** - Added bulk operations support
- **v1.2** - Enhanced filtering capabilities
- **v2.0** - Current version with improved scheduling algorithms
- **v2.1** - Merged comprehensive specification (September 2025)

---

## Additional Notes

1. **Multi-language Support:** System supports internationalization via i18n endpoints
2. **Mobile Integration:** Appetize.io integration for mobile app preview
3. **Analytics:** Google Analytics integration for usage tracking
4. **Field Service Focus:** System is designed for field service management with emphasis on representative scheduling
5. **Legacy Migration:** Ongoing migration from ExtJS to React indicates modernization efforts
6. **SSO Support:** Single Sign-On capability available but may require configuration

---

## Contact and Support

For additional API support or to report issues:
- Check application logs for detailed error messages
- Contact system administrator for authentication issues
- Refer to internal documentation for company-specific implementations

---

*This specification is based on observed network traffic and documented endpoints. Additional endpoints and functionality may exist that require specific permissions or configuration. Last Updated: September 2025*
