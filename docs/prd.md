# flask-schedule-webapp - Product Requirements Document

**Author:** Elliot
**Date:** 2025-11-20
**Version:** 1.0

---

## Executive Summary

**Enhancement Focus:** Employee Management - Add & Import Functionality

This PRD addresses critical defects in employee management that are blocking the auto-scheduler from functioning properly. The system currently cannot reliably add employees manually or import them from the Crossmark API without creating duplicates. More critically, the MV Retail employee number (`repId`) - essential for auto-scheduler operations - is only available through Crossmark API import, making proper import functionality mission-critical.

**Business Impact:** The auto-scheduler is non-functional without proper employee data containing MV Retail employee numbers. This enhancement unblocks core scheduling operations that are needed immediately.

### What Makes This Special

**This is an operational unblock, not a feature enhancement.** The auto-scheduler - the heart of this scheduling system - cannot function without MV Retail employee numbers that only exist in the Crossmark API. This PRD fixes the broken import pipeline that prevents the system from doing its primary job: automated scheduling.

**The fix provides:**
- Reliable employee data foundation for auto-scheduler
- Elimination of duplicate employee records
- User control over which employees to import
- Working manual employee addition as a backup

---

## Project Classification

**Technical Type:** web_app (Flask-based scheduling system)
**Domain:** general (workforce scheduling)
**Complexity:** low (focused enhancement to existing system)

**Project Context:** This is a brownfield enhancement to an existing production Flask scheduling webapp. The system integrates with Crossmark API for event synchronization and uses MV Retail employee data for automated scheduling. This PRD addresses defects in the employee management subsystem that block critical scheduling functionality.

{{#if domain_context_summary}}

### Domain Context

{{domain_context_summary}}
{{/if}}

---

## Success Criteria

**Primary Success Metric:** Auto-scheduler operational with complete employee data containing MV Retail employee numbers.

**Immediate Success Indicators:**
1. ✅ Manual employee add form successfully creates employee records
2. ✅ Crossmark API import fetches employees and extracts all required fields including `repId`
3. ✅ Zero duplicate employees created during import (case-insensitive name matching)
4. ✅ Users can selectively import employees using checkbox interface
5. ✅ Auto-scheduler can access MV Retail employee numbers for scheduling operations

**Operational Success:**
- Scheduling team can populate employee roster from Crossmark API within minutes
- No manual cleanup of duplicate records required
- Auto-scheduler functions correctly with imported employee data
- Manual add available as backup for edge cases

**Business Impact:**
- **Critical blocker removed:** Scheduling operations resume immediately
- **Time saved:** No manual duplicate cleanup required
- **Data quality:** Single source of truth (Crossmark API) for employee data
- **Operational continuity:** Backup manual add capability ensures resilience

---

## Product Scope

### MVP - Minimum Viable Product (THIS RELEASE - ASAP)

**Must Have - Blocks Auto-Scheduler:**

1. **Fix Manual Employee Add**
   - Form with Name (required) + all other fields optional
   - Duplicate detection on submit (case-insensitive name check)
   - If duplicate exists, show error: "Employee '[name]' already exists"
   - Success confirmation after add

2. **Fix Crossmark API Import with Selection**
   - Button: "Import from Crossmark"
   - Fetch employees via POST to `crossmark.mvretail.com/schedulingcontroller/getAvailableReps`
   - Extract and map fields:
     - `title` → Employee name
     - `repId` or `id` → MV Retail employee number (CRITICAL)
     - `employeeId` / `repMvid` → Crossmark employee ID
     - Additional metadata: `availableHoursPerDay`, `scheduledHours`, `visitCount`
   - **Filter duplicates BEFORE display**: Case-insensitive name comparison against existing employees
   - If existing employee has different case, update to match API casing
   - Display NEW employees only in selection table with:
     - Checkbox column (with select all/none)
     - Name
     - Employee ID
     - MV Retail #
   - "Import Selected" button
   - On import, set defaults:
     - Role: Event Specialist
     - Availability: None (no days available)
     - Status: Inactive
   - Success message: "[X] employees imported successfully"

**Out of Scope for MVP:**
- Bulk edit of existing employees
- Employee deactivation workflow
- Advanced filtering/search during import
- Import from other sources (CSV, manual entry of multiple)

### Growth Features (Post-MVP)

**After unblocking auto-scheduler:**

1. **Enhanced Import Controls**
   - Filter employees by role/region before import
   - Preview employee details before selection
   - Import history log (who imported when)

2. **Employee Data Enrichment**
   - Sync additional fields from Crossmark (if available)
   - Update existing employee data from API
   - Conflict resolution for changed data

3. **Bulk Operations**
   - Bulk edit availability
   - Bulk status changes
   - Export employee list to CSV

### Vision (Future)

**Long-term employee management improvements:**

1. **Automated Sync**
   - Scheduled background sync with Crossmark API
   - Automatic detection of new employees
   - Change tracking and notifications

2. **Advanced Duplicate Management**
   - Fuzzy name matching (handle typos, nicknames)
   - Merge duplicate employee records
   - Manual override for edge cases

3. **Employee Lifecycle Management**
   - Onboarding workflow
   - Termination with data retention
   - Rehire detection and handling

---

{{#if domain_considerations}}

## Domain-Specific Requirements

{{domain_considerations}}

This section shapes all functional and non-functional requirements below.
{{/if}}

---

{{#if innovation_patterns}}

## Innovation & Novel Patterns

{{innovation_patterns}}

### Validation Approach

{{validation_approach}}
{{/if}}

---

## Web App Specific Requirements

**Integration Requirements:**

1. **Crossmark API Integration**
   - Endpoint: `POST https://crossmark.mvretail.com/schedulingcontroller/getAvailableReps`
   - Authentication: Use existing session management from `app/integrations/external_api/session_api_service.py`
   - Request format: `multipart/form-data` with `project` field containing date range
   - Response handling: Parse JSON array of employee objects
   - Error handling: Network failures, authentication errors, empty results

2. **Session Management**
   - Reuse existing Crossmark session authentication
   - Handle session expiration gracefully
   - Redirect to login if session invalid

**Data Persistence:**

1. **Employee Model** (existing, may need field additions)
   - Ensure `mv_retail_employee_number` field exists (maps to `repId` from API)
   - Ensure `crossmark_employee_id` field exists (maps to `employeeId` from API)
   - Name field (primary duplicate detection key)
   - Role field (default: Event Specialist)
   - Status field (default: Inactive)
   - Availability fields

2. **Database Operations**
   - Case-insensitive name lookup for duplicate detection
   - Batch insert for selected employees from import
   - Update existing employee name casing if API provides different case

**UI/UX Technical Requirements:**

1. **Manual Add Form**
   - Client-side validation: Name required
   - Server-side duplicate check before save
   - Flash message for success/error
   - Form field list: Name*, Employee ID, MV Retail #, Email, Phone, Role, Status, Availability

2. **Import Selection Interface**
   - Modal or dedicated page (design decision)
   - Table with checkbox column
   - "Select All" / "Deselect All" functionality
   - Disabled "Import Selected" button when no checkboxes checked
   - Loading spinner during API fetch
   - Display employee count: "X new employees available to import"

**Browser Compatibility:**
- Modern browsers (Chrome, Firefox, Edge, Safari - last 2 versions)
- Responsive design not critical (admin interface, desktop primary)
- JavaScript required for checkbox interactions

{{#if endpoint_specification}}

### API Specification

{{endpoint_specification}}
{{/if}}

{{#if authentication_model}}

### Authentication & Authorization

{{authentication_model}}
{{/if}}

{{#if platform_requirements}}

### Platform Support

{{platform_requirements}}
{{/if}}

{{#if device_features}}

### Device Capabilities

{{device_features}}
{{/if}}

{{#if tenant_model}}

### Multi-Tenancy Architecture

{{tenant_model}}
{{/if}}

{{#if permission_matrix}}

### Permissions & Roles

{{permission_matrix}}
{{/if}}
{{/if}}

---

## User Experience Principles

**Design Philosophy:** Administrative efficiency with clear feedback. Users are scheduling managers who need to populate employee rosters quickly and confidently. Every interaction should communicate status clearly and prevent errors proactively.

**Core UX Principles:**

1. **Prevent Problems Before They Happen**
   - Filter duplicates out of import list (don't show, don't tempt)
   - Disable "Import Selected" when nothing checked
   - Validate name requirement before submit
   - This serves the genuine need: "I don't want to clean up mistakes later"

2. **Give Users Control**
   - Checkboxes for selective import (not blind batch)
   - "Select All" / "Deselect All" shortcuts
   - Preview employee data before committing
   - Users feel empowered: "I choose exactly who joins the roster"

3. **Clear Feedback at Every Step**
   - Loading spinner during API fetch: "We're getting your employees..."
   - Count display: "15 new employees available to import"
   - Success messages: "7 employees imported successfully"
   - Error messages: "Employee 'John Smith' already exists"
   - No silent failures - always communicate outcome

4. **Speed Matters (But Not at Cost of Accuracy)**
   - Single-click access to import flow
   - Minimal form fields for manual add (only Name required)
   - Batch import selected employees in one operation
   - But NEVER sacrifice duplicate checking for speed

### Key Interactions

**Import Flow User Journey:**

1. **Entry Point:**
   - User clicks "Import from Crossmark" button on Employees page
   - Expectation: "I'm going to bring in new employees from the system"

2. **Loading State:**
   - Spinner with message: "Fetching employees from Crossmark..."
   - Takes 2-5 seconds typically
   - User feels: "System is working, be patient"

3. **Selection Interface:**
   - **If no new employees:** Message: "No new employees to import. All Crossmark employees are already in your roster."
   - **If new employees available:**
     - Heading: "15 new employees available to import"
     - Table with clear columns: Checkbox | Name | Employee ID | MV Retail #
     - "Select All" / "Deselect All" links above table
     - Rows are scannable, easy to read
   - User feels: "I'm in control, I can see exactly who's available"

4. **Selection Actions:**
   - User checks/unchecks employees
   - "Import Selected" button updates: "Import Selected (3)" to show count
   - Button disabled/grayed when nothing selected
   - User feels: "System is responsive to my choices"

5. **Confirmation:**
   - User clicks "Import Selected (3)"
   - Brief loading state (if batch is large)
   - Success message: "3 employees imported successfully"
   - Table updates or modal closes, returns to employee list
   - User feels: "Done! My roster is updated correctly"

**Manual Add Flow User Journey:**

1. **Entry Point:**
   - "Add Employee" button on Employees page
   - Opens form (modal or dedicated page)

2. **Form Interaction:**
   - Name field marked with * (required)
   - Other fields available but optional
   - Tooltip: "MV Retail # can only be obtained via Crossmark import"
   - User feels: "I know what's required and what's optional"

3. **Submit:**
   - Click "Add Employee"
   - **If duplicate:** Error message: "Employee 'Jane Doe' already exists"
   - **If success:** Success message, form clears or closes
   - User feels: "Clear feedback, I know what happened"

**Visual Personality:**
- Utilitarian and clear (not playful)
- Tables and forms are clean, well-spaced
- Blue for actions, red for errors, green for success (standard conventions)
- Focus on readability and scannability
- Minimal cognitive load - users scan quickly and act confidently

---

## Functional Requirements

**Coverage Note:** These FRs represent the complete capability contract. UX designers design ONLY what's listed here. Architects support ONLY what's listed here. Epic breakdown implements ONLY what's listed here.

### Employee Addition (Manual)

**FR1:** Users can access an "Add Employee" form from the Employees page

**FR2:** Users can enter employee name (required field) in the add form

**FR3:** Users can optionally enter additional employee details: Employee ID, MV Retail employee number, email, phone, role, status, and availability settings

**FR4:** System validates that name field is populated before allowing form submission

**FR5:** System checks for duplicate employee names (case-insensitive) before creating new employee record

**FR6:** System displays error message "Employee '[name]' already exists" if duplicate detected during manual add

**FR7:** System creates new employee record with provided data when no duplicate exists

**FR8:** System displays success confirmation after employee successfully added manually

### Employee Import (Crossmark API)

**FR9:** Users can initiate Crossmark API employee import from the Employees page

**FR10:** System authenticates with Crossmark API using existing session management

**FR11:** System fetches available employees from Crossmark API endpoint (`POST /schedulingcontroller/getAvailableReps`)

**FR12:** System extracts and maps employee data from Crossmark API response:
- `title` → Employee name
- `repId` or `id` → MV Retail employee number
- `employeeId` / `repMvid` → Crossmark employee ID
- `availableHoursPerDay`, `scheduledHours`, `visitCount` → Additional metadata

**FR13:** System compares fetched employees against existing employee roster using case-insensitive name matching

**FR14:** System identifies employees as duplicates if names match regardless of case

**FR15:** System updates existing employee name casing to match Crossmark API data when case differs

**FR16:** System filters out duplicate employees and presents only NEW employees for import selection

**FR17:** System displays "No new employees to import" message when all Crossmark employees already exist in roster

**FR18:** System presents NEW employees in selectable table format with columns: Checkbox, Name, Employee ID, MV Retail #

**FR19:** Users can select individual employees for import using checkboxes

**FR20:** Users can select all displayed employees using "Select All" control

**FR21:** Users can deselect all employees using "Deselect All" control

**FR22:** System displays count of new employees available for import (e.g., "15 new employees available")

**FR23:** System disables "Import Selected" button when no employees are checked

**FR24:** System updates "Import Selected" button to show count of selected employees (e.g., "Import Selected (3)")

**FR25:** System imports selected employees when user activates "Import Selected" button

**FR26:** System sets default values for imported employees:
- Role: Event Specialist
- Availability: None (no days available)
- Status: Inactive

**FR27:** System displays success message with count after import completes (e.g., "7 employees imported successfully")

### Employee Data Integrity

**FR28:** System ensures MV Retail employee number (`repId`) is stored for all imported employees from Crossmark API

**FR29:** System ensures imported employee data is accessible to auto-scheduler component

**FR30:** System prevents duplicate employee records through import process

**FR31:** System maintains data consistency between employee name casing and Crossmark API source

### Error Handling & User Feedback

**FR32:** System displays loading indicator during Crossmark API fetch operation

**FR33:** System handles Crossmark API network failures gracefully with error message

**FR34:** System handles Crossmark API authentication errors and redirects to login if session invalid

**FR35:** System provides clear error messages for all failure scenarios (network, authentication, validation)

**FR36:** System provides success feedback for all successful operations (add, import)

### Integration with Existing System

**FR37:** System integrates with existing Employee model and database schema

**FR38:** System reuses existing Crossmark session authentication mechanism

**FR39:** System maintains compatibility with existing auto-scheduler component

**FR40:** System maintains compatibility with existing employee management features (list, edit, delete)

---

**FR Count: 40 functional requirements**

**Coverage Verification:**
✅ Manual add capability (FR1-FR8)
✅ Crossmark import with API integration (FR9-FR12)
✅ Duplicate detection and filtering (FR13-FR17)
✅ Selection interface (FR18-FR24)
✅ Import execution (FR25-FR27)
✅ Data integrity (FR28-FR31)
✅ Error handling (FR32-FR36)
✅ System integration (FR37-FR40)

Every capability discussed in vision, scope, and technical requirements is represented.

---

## Non-Functional Requirements

### Performance

**NFR-P1:** Manual employee add form submission completes within 2 seconds under normal conditions

**NFR-P2:** Crossmark API employee fetch completes within 10 seconds for typical datasets (100-500 employees)

**NFR-P3:** Import selection interface remains responsive with up to 1000 employees displayed

**NFR-P4:** Batch import of selected employees completes within 5 seconds for batches up to 100 employees

**NFR-P5:** Duplicate detection query executes within 500ms for rosters up to 10,000 existing employees

**Rationale:** Users need timely feedback during critical operations. API fetch timeout is higher due to external dependency.

### Reliability

**NFR-R1:** System gracefully handles Crossmark API failures without data corruption or partial imports

**NFR-R2:** Duplicate detection must be 100% accurate - zero false negatives (no duplicate creation allowed)

**NFR-R3:** Imported employee data must be immediately available to auto-scheduler without cache invalidation delays

**NFR-R4:** Manual add and import operations are atomic - either fully succeed or fully fail (no partial states)

**Rationale:** Data integrity is critical for auto-scheduler to function. This is an operational unblock - reliability is non-negotiable.

### Security

**NFR-S1:** Employee import requires authenticated user session (reuse existing auth)

**NFR-S2:** Manual employee add requires authenticated user session

**NFR-S3:** Crossmark API credentials are not exposed in client-side code or responses

**NFR-S4:** Employee data transmission uses HTTPS for all API calls

**NFR-S5:** CSRF protection enabled on all state-changing operations (add, import)

**Rationale:** Standard security practices for admin operations. No elevated requirements beyond existing system security.

### Usability

**NFR-U1:** Manual add form requires only 1 required field (Name) to minimize friction for backup use case

**NFR-U2:** Import selection interface allows batch selection ("Select All") to handle large imports efficiently

**NFR-U3:** All error messages are human-readable and actionable (not technical error codes)

**NFR-U4:** Loading states display within 200ms of user action to provide immediate feedback

**NFR-U5:** Success/error messages persist for 5 seconds or until dismissed by user

**Rationale:** Users need efficiency and clarity during time-sensitive operations. This serves operational urgency.

### Integration

**NFR-I1:** Solution integrates with existing Employee model without breaking current employee management features

**NFR-I2:** Solution reuses existing Crossmark API session management without requiring new authentication flows

**NFR-I3:** MV Retail employee number storage format is compatible with existing auto-scheduler data expectations

**NFR-I4:** Solution follows existing Flask blueprint and route conventions (e.g., `/employees/*` paths)

**NFR-I5:** Solution uses existing database connection pooling and transaction management patterns

**Rationale:** This is a brownfield fix - minimize architectural disruption. Reuse existing patterns for maintainability.

### Maintainability

**NFR-M1:** Code follows existing Flask project structure and conventions in codebase

**NFR-M2:** Duplicate detection logic is centralized in reusable service/utility function

**NFR-M3:** Crossmark API field mapping is externalized to configuration or documented clearly for future API changes

**NFR-M4:** Error handling follows existing error handling patterns in the application

**Rationale:** ASAP delivery doesn't mean technical debt. Follow existing patterns for long-term maintainability.

### Browser Compatibility

**NFR-B1:** Solution supports modern browsers: Chrome, Firefox, Edge, Safari (last 2 major versions)

**NFR-B2:** JavaScript functionality degrades gracefully if disabled (server-side validation still enforces rules)

**NFR-B3:** Import selection interface displays correctly on desktop resolutions (1280x720 minimum)

**Rationale:** Admin interface, desktop-focused. No mobile or legacy browser support required.

---

## PRD Summary

**This PRD captures:** A critical operational fix to unblock auto-scheduler functionality by repairing employee management infrastructure.

**The Core Problem:** Auto-scheduler cannot function without MV Retail employee numbers, which are only available through Crossmark API import. Current import and manual add processes are broken, creating duplicates and blocking scheduling operations.

**The Solution:**
- Fix manual employee add with duplicate prevention
- Implement Crossmark API import with intelligent duplicate filtering
- Provide user-controlled selective import interface
- Ensure MV Retail employee numbers are captured and accessible

**Business Value:**
- **Immediate:** Auto-scheduler operational, scheduling resumes
- **Data Quality:** Single source of truth, no duplicate cleanup needed
- **User Control:** Selective import prevents roster pollution
- **Operational Resilience:** Manual add provides backup capability

**Requirements Summary:**
- **40 Functional Requirements** covering manual add, API import, duplicate detection, selection UI, data integrity, error handling, and system integration
- **34 Non-Functional Requirements** across performance, reliability, security, usability, integration, maintainability, and browser compatibility

**Next Step:** Architecture workflow to design integration approach, followed by epic breakdown for implementation.

---

_This PRD captures the essence of flask-schedule-webapp employee management fix - an operational unblock that restores critical scheduling capabilities through reliable employee data infrastructure._

_Created through collaborative discovery between Elliot and BMad Method AI facilitation team._
