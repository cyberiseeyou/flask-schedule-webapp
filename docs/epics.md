# flask-schedule-webapp - Epic Breakdown

**Author:** Elliot
**Date:** 2025-11-20
**Project Level:** Enhancement (Brownfield)
**Target Scale:** Focused Fix (Employee Management)

---

## Overview

This document provides the complete epic and story breakdown for flask-schedule-webapp employee management enhancement, decomposing the requirements from the [PRD](./prd.md) into implementable stories.

**Living Document Notice:** This is the initial version created with PRD and Architecture context. Will be updated if UX Design workflow is added later.

---

## Functional Requirements Inventory

### Employee Addition (Manual) - FR1-FR8
- **FR1:** Users can access an "Add Employee" form from the Employees page
- **FR2:** Users can enter employee name (required field) in the add form
- **FR3:** Users can optionally enter additional employee details: Employee ID, MV Retail employee number, email, phone, role, status, and availability settings
- **FR4:** System validates that name field is populated before allowing form submission
- **FR5:** System checks for duplicate employee names (case-insensitive) before creating new employee record
- **FR6:** System displays error message "Employee '[name]' already exists" if duplicate detected during manual add
- **FR7:** System creates new employee record with provided data when no duplicate exists
- **FR8:** System displays success confirmation after employee successfully added manually

### Employee Import (Crossmark API) - FR9-FR27
- **FR9:** Users can initiate Crossmark API employee import from the Employees page
- **FR10:** System authenticates with Crossmark API using existing session management
- **FR11:** System fetches available employees from Crossmark API endpoint (`POST /schedulingcontroller/getAvailableReps`)
- **FR12:** System extracts and maps employee data from Crossmark API response (title→name, repId→MV Retail #, employeeId→Crossmark ID, metadata)
- **FR13:** System compares fetched employees against existing employee roster using case-insensitive name matching
- **FR14:** System identifies employees as duplicates if names match regardless of case
- **FR15:** System updates existing employee name casing to match Crossmark API data when case differs
- **FR16:** System filters out duplicate employees and presents only NEW employees for import selection
- **FR17:** System displays "No new employees to import" message when all Crossmark employees already exist in roster
- **FR18:** System presents NEW employees in selectable table format with columns: Checkbox, Name, Employee ID, MV Retail #
- **FR19:** Users can select individual employees for import using checkboxes
- **FR20:** Users can select all displayed employees using "Select All" control
- **FR21:** Users can deselect all employees using "Deselect All" control
- **FR22:** System displays count of new employees available for import
- **FR23:** System disables "Import Selected" button when no employees are checked
- **FR24:** System updates "Import Selected" button to show count of selected employees
- **FR25:** System imports selected employees when user activates "Import Selected" button
- **FR26:** System sets default values for imported employees (Role: Event Specialist, Availability: None, Status: Inactive)
- **FR27:** System displays success message with count after import completes

### Employee Data Integrity - FR28-FR31
- **FR28:** System ensures MV Retail employee number (`repId`) is stored for all imported employees from Crossmark API
- **FR29:** System ensures imported employee data is accessible to auto-scheduler component
- **FR30:** System prevents duplicate employee records through import process
- **FR31:** System maintains data consistency between employee name casing and Crossmark API source

### Error Handling & User Feedback - FR32-FR36
- **FR32:** System displays loading indicator during Crossmark API fetch operation
- **FR33:** System handles Crossmark API network failures gracefully with error message
- **FR34:** System handles Crossmark API authentication errors and redirects to login if session invalid
- **FR35:** System provides clear error messages for all failure scenarios
- **FR36:** System provides success feedback for all successful operations

### Integration with Existing System - FR37-FR40
- **FR37:** System integrates with existing Employee model and database schema
- **FR38:** System reuses existing Crossmark session authentication mechanism
- **FR39:** System maintains compatibility with existing auto-scheduler component
- **FR40:** System maintains compatibility with existing employee management features

**Total: 40 Functional Requirements**

---

## Epic Structure Summary

This enhancement is organized into 3 epics that deliver incremental value:

### Epic 1: Database & Service Foundation
**Goal:** Establish the database schema and core service infrastructure for employee import operations

**User Value:** Foundation that enables both manual add and import features to work reliably with proper duplicate prevention

**FRs Covered:** FR37 (database integration), foundation for FR5, FR13-FR16, FR28-FR31

**Why This Epic:** Brownfield enhancement requires database migration and service layer setup before features can be built. This epic creates the technical foundation without which subsequent epics cannot function.

### Epic 2: Manual Employee Management
**Goal:** Enable reliable manual employee addition with duplicate prevention

**User Value:** Users can manually add employees to the roster with confidence that duplicates won't be created, serving as a backup to API import

**FRs Covered:** FR1-FR8, FR35-FR36 (error handling for manual add), FR40 (compatibility)

**Why This Epic:** Delivers working manual add capability immediately after foundation is complete. Users get value even before import is built.

### Epic 3: Crossmark API Import with Smart Selection
**Goal:** Enable bulk employee import from Crossmark API with intelligent duplicate filtering and user-controlled selection

**User Value:** Users can populate the entire employee roster from Crossmark API in minutes, with MV Retail numbers captured automatically, unblocking the auto-scheduler

**FRs Covered:** FR9-FR27, FR28-FR31 (data integrity), FR32-FR34 (error handling for import), FR38-FR39 (Crossmark integration)

**Why This Epic:** Delivers the primary operational unblock - auto-scheduler functionality restored through proper employee data with MV Retail numbers.

---

## FR Coverage Map

| Epic | FRs Covered | Story Count |
|------|-------------|-------------|
| Epic 1: Database & Service Foundation | FR37, foundation for FR5/FR13-FR16/FR28-FR31 | 4 stories |
| Epic 2: Manual Employee Management | FR1-FR8, FR35-FR36, FR40 | 3 stories |
| Epic 3: Crossmark API Import | FR9-FR27, FR28-FR31, FR32-FR34, FR38-FR39 | 7 stories |

**Total Stories:** 14 stories across 3 epics

**Coverage Verification:** All 40 FRs are mapped to specific stories within these epics.

---

## Epic 1: Database & Service Foundation

**Goal:** Establish the database schema and core service infrastructure for employee import operations

**Value Delivery:** Foundation that enables both manual add and import features to work reliably with proper duplicate prevention and data integrity

**Technical Context:** Extends existing Flask/SQLAlchemy architecture following brownfield enhancement patterns. Creates reusable service layer for duplicate detection and import logic.

---

### Story 1.1: Database Schema Migration for Employee Import Fields

As a **developer**,
I want **database fields for MV Retail employee number and Crossmark employee ID added to the Employee model**,
So that **imported employees can store critical identifiers needed by the auto-scheduler**.

**Acceptance Criteria:**

**Given** the existing Employee model in `app/models/employee.py`
**When** the database migration is created and applied
**Then** the employees table has two new fields:
- `mv_retail_employee_number` (String(50), nullable=True, indexed)
- `crossmark_employee_id` (String(50), nullable=True, unique=True)

**And** a database index exists on `lower(name)` for case-insensitive lookups

**And** the migration includes both upgrade and downgrade paths

**And** all existing employee records remain intact with new fields set to NULL

**Prerequisites:** None (foundation story)

**Technical Notes:**
- Create Alembic migration: `flask db migrate -m "Add MV Retail and Crossmark ID fields"`
- Follow pattern from Architecture doc section "Database Migration" (lines 516-563)
- Use SQLAlchemy `func.lower()` for index: `Index('ix_employee_name_lower', func.lower(Employee.name))`
- Unique constraint on `crossmark_employee_id` prevents duplicate API imports
- Test migration locally before committing: `flask db upgrade` then `flask db downgrade`
- **File to modify:** `app/models/employee.py`
- **File to create:** `migrations/versions/XXXX_add_employee_import_fields.py`

---

### Story 1.2: Employee Import Service Layer Setup

As a **developer**,
I want **a dedicated service layer for employee import business logic**,
So that **duplicate detection, API interaction, and import operations are centralized and testable**.

**Acceptance Criteria:**

**Given** the Flask application structure at `app/services/`
**When** the EmployeeImportService class is created
**Then** the service provides the following static methods:
- `check_duplicate_name(name: str) -> Optional[Employee]` - Case-insensitive name lookup
- `filter_duplicate_employees(api_employees, existing_employees) -> tuple[List, List]` - Returns (new_employees, employees_needing_casing_update)
- `bulk_import_employees(selected_employees: List[CrossmarkEmployee]) -> int` - Atomic import with transaction
- `fetch_crossmark_employees() -> List[CrossmarkEmployee]` - API wrapper

**And** the service uses the database index for O(log n) duplicate lookups

**And** the service handles case-insensitive matching using `func.lower()`

**And** all methods include docstrings with type hints

**Prerequisites:** Story 1.1 (needs database fields)

**Technical Notes:**
- **File to create:** `app/services/employee_import_service.py`
- Follow service pattern from Architecture doc section "Service Layer Pattern" (lines 272-313)
- Import existing `SessionAPIService` from `app/integrations/external_api/session_api_service.py`
- Use SQLAlchemy session from `app import db`
- Duplicate detection pattern from Architecture lines 381-416
- Each method should be independently testable without HTTP context
- See Architecture "API Contracts" section (lines 577-651) for method signatures

---

### Story 1.3: Pydantic Models for Crossmark API Response Validation

As a **developer**,
I want **type-safe validation of Crossmark API responses using Pydantic**,
So that **API contract changes are caught early and field mapping is self-documenting**.

**Acceptance Criteria:**

**Given** Crossmark API returns JSON employee objects
**When** the Pydantic model is defined
**Then** the `CrossmarkEmployee` model validates these fields:
- `id: str` - MV Retail employee number (repId fallback)
- `repId: str` - Primary MV Retail number
- `employeeId: str` - Crossmark employee ID
- `title: str` - Full employee name
- `lastName: str`, `nameSort: str` - Name components
- `availableHoursPerDay: str`, `scheduledHours: str`, `visitCount: str` - Metadata
- `role: Optional[str]` - Optional role field

**And** validation errors raise clear exceptions with field names

**And** the model is used in `EmployeeImportService.fetch_crossmark_employees()`

**And** Pydantic dependency (v2.x) is added to `requirements.txt`

**Prerequisites:** Story 1.2 (service layer exists)

**Technical Notes:**
- **File to modify:** `app/services/employee_import_service.py` (add model at top)
- Alternatively create: `app/models/crossmark_api.py` if keeping models separate
- Install: `pip install "pydantic>=2.0"`
- See Architecture "Integration Points" section (lines 148-182) for exact model definition
- Use model like: `employees = [CrossmarkEmployee(**emp) for emp in api_response]`
- Pydantic will auto-validate and raise `ValidationError` on schema mismatch

---

### Story 1.4: Case-Insensitive Duplicate Detection Implementation

As a **developer**,
I want **a reliable case-insensitive duplicate detection mechanism**,
So that **employees named "John Smith", "john smith", and "JOHN SMITH" are recognized as duplicates**.

**Acceptance Criteria:**

**Given** the Employee model with case-insensitive index
**When** `EmployeeImportService.check_duplicate_name("john SMITH")` is called
**Then** it returns the existing employee record if "John Smith" exists in the database

**And** the lookup uses the database index for performance (< 500ms for 10k employees per NFR-P5)

**And** the method returns `None` if no duplicate exists

**And** the filtering logic in `filter_duplicate_employees()` uses O(n) hash map approach for batch checking

**And** when case differs, the existing employee is marked for casing update to match API

**Prerequisites:** Story 1.1 (database index), Story 1.2 (service methods)

**Technical Notes:**
- Use SQLAlchemy pattern: `Employee.query.filter(func.lower(Employee.name) == func.lower(name)).first()`
- Database index on `lower(name)` enables fast lookups (created in Story 1.1)
- For batch filtering, build `{name.lower(): employee}` dict for O(n) lookup
- See Architecture "Duplicate Detection Pattern" (lines 381-416) for implementation
- Test with: identical case, different case, mixed case, special characters
- Meets NFR-R2: 100% accuracy, zero false negatives

---

## Epic 2: Manual Employee Management

**Goal:** Enable reliable manual employee addition with duplicate prevention

**Value Delivery:** Users can manually add employees to the roster with confidence that duplicates won't be created, serving as a backup to API import

**Technical Context:** Fixes existing manual add form at `/employees/add` with proper validation, duplicate checking, and user feedback. Uses WTForms for validation and EmployeeImportService for duplicate detection.

---

### Story 2.1: Manual Employee Add Form with Validation

As a **scheduling manager**,
I want **an "Add Employee" form that requires only a name and makes all other fields optional**,
So that **I can quickly add employees manually when needed without filling unnecessary fields**.

**Acceptance Criteria:**

**Given** I am on the Employees page
**When** I click "Add Employee" button
**Then** a form opens with the following fields:
- Name* (required, marked with asterisk)
- Employee ID (optional)
- MV Retail Employee # (optional, with tooltip: "Only available via Crossmark import")
- Email (optional)
- Phone (optional)
- Role (optional, default: Event Specialist)
- Status (optional, default: Inactive)
- Availability settings (optional)

**And** the form includes CSRF protection via Flask-WTF

**And** client-side validation marks Name field as required

**And** the form displays in a modal or dedicated page (consistent with existing UI pattern)

**Prerequisites:** Story 1.1 (database fields exist), Story 1.2 (service layer exists)

**Technical Notes:**
- **File to modify:** `app/routes/employees.py` - Fix existing `@bp.route('/add', methods=['GET', 'POST'])`
- **File to modify:** `app/templates/employees/add_employee.html` - Update form markup
- Use WTForms: `from wtforms import StringField, validators`
- Name field: `StringField('Name', [validators.DataRequired(message='Name is required')])`
- Tooltip for MV Retail field helps users understand import requirement
- Follow Architecture "Form Validation Messages" section (lines 489-497)
- Ensure form follows existing styling conventions in templates

---

### Story 2.2: Duplicate Detection on Manual Employee Add

As a **scheduling manager**,
I want **the system to prevent me from adding an employee with a duplicate name**,
So that **I don't accidentally create multiple records for the same person**.

**Acceptance Criteria:**

**Given** an employee named "Jane Doe" already exists in the database
**When** I submit the add form with name "jane doe" (different case)
**Then** the form does NOT create a new employee

**And** an error message displays: "Employee 'jane doe' already exists"

**And** the form remains open with my entered data preserved

**And** I can correct the name and resubmit

**And** server-side validation always checks for duplicates (client-side is UX only)

**And** the duplicate check completes in < 2 seconds (NFR-P1)

**Prerequisites:** Story 2.1 (form exists), Story 1.4 (duplicate detection works)

**Technical Notes:**
- In route handler, call: `existing = EmployeeImportService.check_duplicate_name(form.name.data)`
- If duplicate found: `flash(f"Employee '{form.name.data}' already exists", 'error')` and re-render form
- Use pattern from Architecture "Error Handling Pattern" (lines 354-377)
- Test both exact case match and different case match
- Meets FR5, FR6 exactly as specified in PRD

---

### Story 2.3: Success Confirmation for Manual Employee Add

As a **scheduling manager**,
I want **clear confirmation when I successfully add an employee**,
So that **I know the operation completed and can proceed with confidence**.

**Acceptance Criteria:**

**Given** I submit the add form with valid, unique employee data
**When** the employee is created successfully
**Then** I am redirected to the Employees list page

**And** a success message displays: "Employee '[name]' added successfully"

**And** the new employee appears in the employee list

**And** the employee has default values if optional fields were empty:
- Role: "Event Specialist"
- Status: "Inactive"
- Availability: None (no days available)

**And** the operation completes in < 2 seconds (NFR-P1)

**Prerequisites:** Story 2.1 (form exists), Story 2.2 (validation works)

**Technical Notes:**
- After successful `db.session.commit()`: `flash(f"Employee '{employee.name}' added successfully", 'success')`
- Redirect: `return redirect(url_for('employees.index'))`
- Use Flask flash message categories from Architecture "Consistency Rules" (lines 451-465)
- Log success: `current_app.logger.info(f"Manual add: {employee.name}")`
- Ensure transaction is committed before redirect
- Meets FR7, FR8, FR40 (compatibility with existing features)

---

## Epic 3: Crossmark API Import with Smart Selection

**Goal:** Enable bulk employee import from Crossmark API with intelligent duplicate filtering and user-controlled selection

**Value Delivery:** Users can populate the entire employee roster from Crossmark API in minutes, with MV Retail numbers captured automatically, unblocking the auto-scheduler

**Technical Context:** Integrates with existing Crossmark session authentication, implements server-rendered selection UI with checkboxes, handles all error cases gracefully, and ensures atomic batch import with proper data integrity.

---

### Story 3.1: Crossmark API Integration for Employee Fetch

As a **scheduling manager**,
I want **the system to fetch available employees from the Crossmark API**,
So that **I can import employee data including MV Retail numbers needed for scheduling**.

**Acceptance Criteria:**

**Given** I have a valid Crossmark session (logged in)
**When** I click "Import from Crossmark" button on Employees page
**Then** the system makes a POST request to `https://crossmark.mvretail.com/schedulingcontroller/getAvailableReps`

**And** the request uses existing session authentication from `SessionAPIService`

**And** the request includes a date range parameter in format: "MM/DD/YYYY HH:MM:SS,MM/DD/YYYY HH:MM:SS"

**And** the system parses the JSON response into `CrossmarkEmployee` Pydantic models

**And** the fetch completes within 10 seconds for typical datasets (NFR-P2)

**And** a loading spinner displays during the API call with message "Fetching employees from Crossmark..."

**Prerequisites:** Story 1.2 (service layer), Story 1.3 (Pydantic model), Story 1.4 (duplicate detection)

**Technical Notes:**
- **File to modify:** `app/integrations/external_api/session_api_service.py` - Add `fetch_available_reps()` method
- **File to modify:** `app/services/employee_import_service.py` - Add `fetch_crossmark_employees()` wrapper
- **File to create:** `app/routes/employees.py` - Add route `@bp.route('/import-crossmark', methods=['GET'])`
- Use existing session from `session_api_service` (reuse pattern from event sync)
- Date range: current time + 7 days ahead (reasonable window for rep availability)
- See Architecture "Integration Points" section (lines 148-182) for request/response format
- Parse response: `[CrossmarkEmployee(**emp) for emp in response.json()]`
- Meets FR9, FR10, FR11, FR12, FR32, FR38

---

### Story 3.2: Duplicate Filtering Before Display

As a **scheduling manager**,
I want **the system to automatically filter out employees who already exist in my roster**,
So that **I only see NEW employees available for import and don't waste time reviewing duplicates**.

**Acceptance Criteria:**

**Given** the system has fetched 50 employees from Crossmark API
**And** 20 of those employees already exist in the database (matched by case-insensitive name)
**When** the system prepares the selection interface
**Then** only the 30 NEW employees are displayed for selection

**And** the 20 duplicates are completely filtered out (not shown at all)

**And** for duplicates where name casing differs from API, the existing employee's name is updated to match API casing

**And** the filtering completes in < 500ms for rosters up to 10k employees (NFR-P5)

**And** the count message shows: "30 new employees available to import"

**Prerequisites:** Story 3.1 (API fetch works), Story 1.4 (duplicate detection implemented)

**Technical Notes:**
- Call `EmployeeImportService.filter_duplicate_employees(api_employees, Employee.query.all())`
- Returns tuple: `(new_employees, employees_needing_casing_update)`
- Update casing for existing employees: `for emp, new_name in casing_updates: emp.name = new_name; db.session.commit()`
- Use in-memory hash map for O(n) filtering (pattern from Architecture lines 398-416)
- If zero new employees: redirect with flash message "No new employees to import..."
- Meets FR13, FR14, FR15, FR16, FR17, FR30, FR31

---

### Story 3.3: Selection Interface with Checkbox Table

As a **scheduling manager**,
I want **a clear table showing new employees with checkboxes so I can select which ones to import**,
So that **I have control over exactly who joins my roster**.

**Acceptance Criteria:**

**Given** there are 30 new employees available for import
**When** the selection interface is displayed
**Then** I see a table with these columns:
- Checkbox (unchecked by default)
- Name
- Employee ID (Crossmark ID)
- MV Retail # (repId)

**And** the table shows all 30 employees in a scannable format

**And** a heading displays: "30 new employees available to import"

**And** "Select All" and "Deselect All" links appear above the table

**And** an "Import Selected" button appears below the table (disabled initially)

**And** the interface remains responsive with up to 1000 employees (NFR-P3)

**Prerequisites:** Story 3.2 (filtering works)

**Technical Notes:**
- **File to create:** `app/templates/employees/import_select.html` - Server-rendered Jinja2 template
- **File to create:** `app/static/js/employee_import.js` - Simple checkbox JavaScript
- Render template: `render_template('employees/import_select.html', employees=new_employees, count=len(new_employees))`
- Table uses existing Bootstrap/CSS styling from employees list
- No client-side framework needed - vanilla JS for checkboxes
- See Architecture "UI Integration" (lines 213-230) for flow
- Meets FR18, FR19, FR22

---

### Story 3.4: Select All / Deselect All Functionality

As a **scheduling manager**,
I want **"Select All" and "Deselect All" shortcuts**,
So that **I can quickly select all employees for import without checking boxes individually**.

**Acceptance Criteria:**

**Given** the import selection table is displayed with multiple employees
**When** I click "Select All"
**Then** all checkboxes in the table become checked

**And** the "Import Selected" button becomes enabled

**And** the button text updates to show count: "Import Selected (30)"

**When** I click "Deselect All"
**Then** all checkboxes become unchecked

**And** the "Import Selected" button becomes disabled/grayed out

**And** the button text reverts to: "Import Selected"

**And** individual checkbox clicks also update the button count dynamically

**Prerequisites:** Story 3.3 (selection UI exists)

**Technical Notes:**
- **File:** `app/static/js/employee_import.js`
- Select All: `document.querySelectorAll('input[type="checkbox"].employee-select').forEach(cb => cb.checked = true)`
- Deselect All: Same pattern with `checked = false`
- Update button on any checkbox change: listen for 'change' event
- Count checked: `document.querySelectorAll('input[type="checkbox"].employee-select:checked').length`
- Button disabled when count === 0: `button.disabled = (count === 0)`
- Vanilla JavaScript - no jQuery or frameworks needed
- Meets FR20, FR21, FR23, FR24, NFR-U2

---

### Story 3.5: Atomic Bulk Import Execution

As a **scheduling manager**,
I want **selected employees imported in a single atomic operation**,
So that **either all my selections are imported successfully or none are, preventing partial imports**.

**Acceptance Criteria:**

**Given** I have selected 15 employees from the import table
**When** I click "Import Selected (15)" button
**Then** the system creates 15 new Employee records in a single database transaction

**And** each imported employee has:
- Name from API `title` field
- MV Retail employee number from API `repId` field
- Crossmark employee ID from API `employeeId` field
- Role set to "Event Specialist"
- Status set to "Inactive"
- Availability set to None (no days available)

**And** if ANY employee fails to import, the ENTIRE transaction rolls back (zero employees imported)

**And** the import completes in < 5 seconds for batches up to 100 employees (NFR-P4)

**And** on success, I am redirected to Employees list with message: "15 employees imported successfully"

**Prerequisites:** Story 3.4 (selection works), Story 1.2 (service bulk_import method)

**Technical Notes:**
- **File to modify:** `app/routes/employees.py` - Add route `@bp.route('/import-crossmark/import', methods=['POST'])`
- **File to modify:** `app/services/employee_import_service.py` - Implement `bulk_import_employees()`
- POST request sends selected employee IDs/data from form
- Call: `count = EmployeeImportService.bulk_import_employees(selected_employees)`
- Use single transaction: wrap all inserts in `try/except` with `db.session.rollback()` on error
- See Architecture "Transaction Pattern" (lines 419-446) for atomic import code
- Log: `current_app.logger.info(f"Imported {count} employees from Crossmark")`
- Meets FR25, FR26, FR27, FR28, FR29, NFR-R1, NFR-R3, NFR-R4

---

### Story 3.6: Error Handling for API and Network Failures

As a **scheduling manager**,
I want **clear error messages when Crossmark API fails or network issues occur**,
So that **I understand what went wrong and can take appropriate action**.

**Acceptance Criteria:**

**Given** I click "Import from Crossmark" button
**When** the Crossmark API is unreachable (network failure)
**Then** I see an error message: "Unable to connect to Crossmark API. Please try again."

**And** I remain on the Employees page (no broken state)

**When** my Crossmark session has expired (authentication error)
**Then** I am redirected to the login page

**And** I see a message: "Session expired. Please log in again."

**When** the API returns an unexpected format (validation error)
**Then** I see an error message: "Received unexpected data from Crossmark. Please contact support."

**And** all errors are logged with full details for debugging

**And** no partial data is saved when errors occur

**Prerequisites:** Story 3.1 (API integration), Story 3.5 (import execution)

**Technical Notes:**
- **File to modify:** `app/routes/employees.py` - Add comprehensive exception handling
- Use pattern from Architecture "Error Handling Pattern" (lines 354-377)
- Catch `requests.exceptions.RequestException` for network errors
- Catch `APIAuthenticationError` (custom exception) for session issues
- Catch `ValidationError` from Pydantic for response format issues
- All exceptions: log with `current_app.logger.error(str(e), exc_info=True)`
- Flash messages use 'error' category for styling
- Meets FR32, FR33, FR34, FR35, NFR-S4, NFR-U3

---

### Story 3.7: Data Accessibility for Auto-Scheduler

As a **developer of the auto-scheduler**,
I want **imported employee data including MV Retail numbers immediately accessible**,
So that **the auto-scheduler can use employee data for scheduling operations without delays**.

**Acceptance Criteria:**

**Given** employees have been successfully imported from Crossmark API
**When** the auto-scheduler queries for employees with MV Retail numbers
**Then** all imported employees are returned with `mv_retail_employee_number` field populated

**And** the data is available immediately after import (no cache invalidation delay per NFR-R3)

**And** the auto-scheduler can filter employees by `mv_retail_employee_number IS NOT NULL`

**And** the `crossmark_employee_id` field can be used for future sync/update operations

**And** existing auto-scheduler code continues to work without modification (NFR-I1)

**Prerequisites:** Story 3.5 (import works), Story 1.1 (database fields exist)

**Technical Notes:**
- No code changes needed - this story validates integration
- Test by querying: `Employee.query.filter(Employee.mv_retail_employee_number.isnot(None)).all()`
- Verify auto-scheduler can access: check existing scheduling code paths
- Database fields are immediately available after commit (SQLAlchemy default behavior)
- Document field names for auto-scheduler team if needed
- **Integration test:** Verify auto-scheduler component can read imported data
- Meets FR29, FR39, NFR-I3, NFR-R3

---

## FR Coverage Matrix

This matrix validates that EVERY functional requirement from the PRD is covered by at least one story:

| FR | Description | Epic | Story |
|----|-------------|------|-------|
| FR1 | Access "Add Employee" form | Epic 2 | 2.1 |
| FR2 | Enter employee name (required) | Epic 2 | 2.1 |
| FR3 | Enter optional employee details | Epic 2 | 2.1 |
| FR4 | Validate name field populated | Epic 2 | 2.1 |
| FR5 | Check duplicate names (case-insensitive) | Epic 2 | 2.2 |
| FR6 | Display duplicate error message | Epic 2 | 2.2 |
| FR7 | Create new employee record | Epic 2 | 2.3 |
| FR8 | Display success confirmation | Epic 2 | 2.3 |
| FR9 | Initiate Crossmark API import | Epic 3 | 3.1 |
| FR10 | Authenticate with Crossmark API | Epic 3 | 3.1 |
| FR11 | Fetch available employees from API | Epic 3 | 3.1 |
| FR12 | Extract and map employee data | Epic 3 | 3.1 |
| FR13 | Compare against existing roster | Epic 3 | 3.2 |
| FR14 | Identify duplicates case-insensitive | Epic 3 | 3.2 |
| FR15 | Update existing name casing | Epic 3 | 3.2 |
| FR16 | Filter out duplicate employees | Epic 3 | 3.2 |
| FR17 | Display "no new employees" message | Epic 3 | 3.2 |
| FR18 | Present employees in table format | Epic 3 | 3.3 |
| FR19 | Select individual employees | Epic 3 | 3.3 |
| FR20 | Select all employees | Epic 3 | 3.4 |
| FR21 | Deselect all employees | Epic 3 | 3.4 |
| FR22 | Display count of new employees | Epic 3 | 3.3 |
| FR23 | Disable button when none selected | Epic 3 | 3.4 |
| FR24 | Update button with selection count | Epic 3 | 3.4 |
| FR25 | Import selected employees | Epic 3 | 3.5 |
| FR26 | Set default values for imported | Epic 3 | 3.5 |
| FR27 | Display success message with count | Epic 3 | 3.5 |
| FR28 | Store MV Retail employee number | Epic 3 | 3.5, 3.7 |
| FR29 | Data accessible to auto-scheduler | Epic 3 | 3.7 |
| FR30 | Prevent duplicate records | Epic 3 | 3.2 |
| FR31 | Maintain data consistency | Epic 3 | 3.2 |
| FR32 | Display loading indicator | Epic 3 | 3.1 |
| FR33 | Handle network failures | Epic 3 | 3.6 |
| FR34 | Handle authentication errors | Epic 3 | 3.6 |
| FR35 | Clear error messages | Epic 3 | 3.6, Epic 2 2.2 |
| FR36 | Success feedback | Epic 3 | 3.5, Epic 2 2.3 |
| FR37 | Integrate with Employee model | Epic 1 | 1.1 |
| FR38 | Reuse Crossmark session auth | Epic 3 | 3.1 |
| FR39 | Compatible with auto-scheduler | Epic 3 | 3.7 |
| FR40 | Compatible with existing features | Epic 2 | 2.3 |

**Coverage Validation:** ✅ All 40 FRs mapped to stories

---

## Epic Breakdown Summary

### Delivery Structure

**Epic 1: Database & Service Foundation** (4 stories)
- Sets up database schema with new fields for MV Retail # and Crossmark ID
- Creates service layer for duplicate detection and import operations
- Establishes Pydantic models for type-safe API response handling
- Implements case-insensitive duplicate detection algorithm

**Epic 2: Manual Employee Management** (3 stories)
- Fixes manual add form with proper validation (name required, others optional)
- Implements duplicate prevention on manual add with clear error messages
- Provides success confirmation and proper data defaults

**Epic 3: Crossmark API Import with Smart Selection** (7 stories)
- Integrates with Crossmark API to fetch available employees
- Filters duplicates automatically before displaying selection interface
- Provides checkbox-based selection UI with Select All/Deselect All
- Executes atomic bulk import with proper error handling
- Ensures imported data is immediately accessible to auto-scheduler

### User Value Delivery

**After Epic 1:** Technical foundation ready for both manual add and API import features

**After Epic 2:** Users can manually add employees without creating duplicates - backup capability operational

**After Epic 3:** Users can bulk import from Crossmark API with MV Retail numbers captured - auto-scheduler unblocked and operational

### Implementation Notes

- **Total Stories:** 14 stories across 3 epics
- **Sequencing:** Stories within each epic must be completed in order (no forward dependencies)
- **Vertical Slicing:** Each story delivers complete functionality (not just one layer)
- **Architecture Integration:** All stories reference specific architecture patterns and file locations
- **Testing:** Each story includes clear acceptance criteria for validation

### Context Incorporated

✅ **PRD Requirements:** All 40 functional requirements mapped and decomposed into tactical implementation details

✅ **Architecture Decisions:** Technical stack, patterns, naming conventions, and integration points incorporated into stories

✅ **Performance Requirements:** NFRs referenced in acceptance criteria (< 2s add, < 10s API fetch, < 500ms duplicate check, etc.)

✅ **Security & Reliability:** CSRF protection, atomic transactions, error handling patterns, session management

### Next Steps

**Ready for Phase 4 Implementation:**
- Sprint planning can begin using this epic breakdown
- Each story is sized for single dev agent completion
- Prerequisites clearly defined for story ordering
- Technical notes provide implementation guidance

**If Additional Context Needed:**
- UX Design workflow can enhance UI/interaction details in stories
- Domain requirements can be incorporated if specialized compliance emerges

---

## Summary

This epic breakdown transforms the employee management PRD into 14 implementable stories organized into 3 value-delivering epics. The structure enables incremental delivery: foundation first, then manual add backup capability, then full Crossmark import with the critical MV Retail employee numbers that unblock the auto-scheduler.

Every story includes:
- Clear user story format (As a... I want... So that...)
- BDD-style acceptance criteria (Given/When/Then)
- Prerequisites for sequencing
- Technical notes with file paths and architecture references
- FR coverage mapping

The breakdown is ready for implementation with complete coverage of all 40 functional requirements, proper integration with existing Flask architecture, and clear technical guidance for developers.

---

_For implementation: Use the `dev-story` workflow to execute individual stories from this epic breakdown._

_This document was created with PRD and Architecture context. Run UX Design workflow to add interaction details if needed._

