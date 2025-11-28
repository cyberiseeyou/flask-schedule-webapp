# Story 3.1: crossmark-api-integration-for-employee-fetch

Status: ready-for-dev

## Story

As a **scheduling manager**,
I want **the system to fetch available employees from the Crossmark API**,
so that **I can import employee data including MV Retail numbers needed for scheduling**.

## Acceptance Criteria

**Given** I have a valid Crossmark session (logged in)
**When** I click "Import from Crossmark" button on Employees page
**Then** the system makes a POST request to `https://crossmark.mvretail.com/schedulingcontroller/getAvailableReps`

**And** the request uses existing session authentication from `SessionAPIService`

**And** the request includes a date range parameter in format: "MM/DD/YYYY HH:MM:SS,MM/DD/YYYY HH:MM:SS"

**And** the system parses the JSON response into `CrossmarkEmployee` Pydantic models

**And** the fetch completes within 10 seconds for typical datasets (NFR-P2)

**And** a loading spinner displays during the API call with message "Fetching employees from Crossmark..."

## Tasks / Subtasks

- [ ] Task 1: Add fetch_available_reps method to SessionAPIService (AC: API call method exists)
  - [ ] Subtask 1.1: Open `app/integrations/external_api/session_api_service.py`
  - [ ] Subtask 1.2: Add method `fetch_available_reps(date_range: str) -> dict`
  - [ ] Subtask 1.3: Construct POST URL: `{base_url}/schedulingcontroller/getAvailableReps`
  - [ ] Subtask 1.4: Include date_range in request body or params
  - [ ] Subtask 1.5: Use existing session authentication mechanism
  - [ ] Subtask 1.6: Return JSON response as dict
  - [ ] Subtask 1.7: Handle API errors and raise appropriate exceptions

- [ ] Task 2: Update EmployeeImportService.fetch_crossmark_employees (AC: Returns List[CrossmarkEmployee])
  - [ ] Subtask 2.1: Open `app/services/employee_import_service.py`
  - [ ] Subtask 2.2: Update method to call SessionAPIService.fetch_available_reps
  - [ ] Subtask 2.3: Generate date range: current datetime + 7 days
  - [ ] Subtask 2.4: Format date range: "MM/DD/YYYY HH:MM:SS,MM/DD/YYYY HH:MM:SS"
  - [ ] Subtask 2.5: Parse response and create List[CrossmarkEmployee] (requires Story 1.3 Pydantic model)
  - [ ] Subtask 2.6: Handle ValidationError from Pydantic
  - [ ] Subtask 2.7: Handle network errors and API failures

- [ ] Task 3: Create import initiation route (AC: "Import from Crossmark" button triggers fetch)
  - [ ] Subtask 3.1: In `app/routes/employees.py`, add route `@bp.route('/import-crossmark', methods=['GET'])`
  - [ ] Subtask 3.2: Call `EmployeeImportService.fetch_crossmark_employees()`
  - [ ] Subtask 3.3: Store fetched employees in session or pass to next view
  - [ ] Subtask 3.4: Redirect to selection interface (Story 3.3 will create this)
  - [ ] Subtask 3.5: Handle errors gracefully with flash messages

- [ ] Task 4: Add "Import from Crossmark" button to Employees page (AC: Button accessible)
  - [ ] Subtask 4.1: Open `app/templates/employees/index.html`
  - [ ] Subtask 4.2: Add button: "Import from Crossmark" linking to `/employees/import-crossmark`
  - [ ] Subtask 4.3: Style button consistently with existing page buttons
  - [ ] Subtask 4.4: Position button near "Add Employee" button
  - [ ] Subtask 4.5: Add icon (optional): Import/download icon

- [ ] Task 5: Implement loading spinner/indicator (AC: Loading feedback during API call)
  - [ ] Subtask 5.1: Add client-side JavaScript for loading state
  - [ ] Subtask 5.2: On button click: Show spinner overlay with message "Fetching employees from Crossmark..."
  - [ ] Subtask 5.3: Disable button during loading to prevent double-clicks
  - [ ] Subtask 5.4: If using AJAX: Remove spinner on response; If using redirect: Show until page loads
  - [ ] Subtask 5.5: Test loading indicator appears and disappears correctly

- [ ] Task 6: Add comprehensive tests (AC: API integration tested)
  - [ ] Subtask 6.1: Mock SessionAPIService.fetch_available_reps in tests
  - [ ] Subtask 6.2: Test successful fetch: Mock returns employee data, verify CrossmarkEmployee list created
  - [ ] Subtask 6.3: Test API error: Mock raises exception, verify error handling
  - [ ] Subtask 6.4: Test authentication error: Mock returns 401, verify redirect to login
  - [ ] Subtask 6.5: Test network timeout: Mock raises timeout, verify error message
  - [ ] Subtask 6.6: Test Pydantic validation error: Mock returns invalid data, verify error handling

## Dev Notes

### Architecture Patterns and Constraints

**Integration Points** (Architecture lines 148-182):
- Crossmark API endpoint: `POST /schedulingcontroller/getAvailableReps`
- Authentication: Reuse existing session from SessionAPIService
- Date range format: "MM/DD/YYYY HH:MM:SS,MM/DD/YYYY HH:MM:SS"
- Response parsing: Use CrossmarkEmployee Pydantic model from Story 1.3

**API Response Structure**:
```json
[
  {
    "id": "12345",
    "repId": "12345",
    "employeeId": "EMP001",
    "title": "John Smith",
    "lastName": "Smith",
    "nameSort": "Smith, John",
    "availableHoursPerDay": "8",
    "scheduledHours": "0",
    "visitCount": "0",
    "role": null
  }
]
```

**Performance Requirements** (PRD NFR-P2):
- API fetch must complete within 10 seconds for typical datasets
- Show loading indicator to manage user expectations
- Handle timeouts gracefully

### Project Structure Notes

**Files to Modify:**
- `app/integrations/external_api/session_api_service.py` - Add fetch_available_reps method
- `app/services/employee_import_service.py` - Update fetch_crossmark_employees to use new API method
- `app/routes/employees.py` - Add /import-crossmark route
- `app/templates/employees/index.html` - Add "Import from Crossmark" button

**Files to Create:**
- `app/static/js/employee_import.js` - Loading spinner JavaScript (if using client-side)

**Dependencies:**
- Story 1.3: CrossmarkEmployee Pydantic model must be complete
- Story 1.2: EmployeeImportService.fetch_crossmark_employees method exists (needs update)
- Existing SessionAPIService: Crossmark session authentication

### Learnings from Previous Story

**From Story 2-3-success-confirmation-for-manual-employee-add (Status: drafted)**

- **Flash Message Pattern**: Use `flash(message, category)` for user feedback
- **Redirect Pattern**: `return redirect(url_for('employees.index'))`
- **Error Handling**: Try/except with rollback and error messages

**From Story 1-3-pydantic-models-for-crossmark-api-response-validation (Status: drafted)**

- **CrossmarkEmployee Model**: Available in `app/services/employee_import_service.py`
- **Validation**: Use `[CrossmarkEmployee(**emp) for emp in response]` to parse API response
- **Error Handling**: Catch `ValidationError` from Pydantic for invalid responses

**From Story 1-2-employee-import-service-layer-setup (Status: done)**

- **Service Location**: `app/services/employee_import_service.py`
- **Method**: fetch_crossmark_employees() currently returns List[dict], needs update for Pydantic
- **SessionAPIService**: Existing at `app/integrations/external_api/session_api_service.py`

**Integration Strategy:**
1. Add API call method to SessionAPIService (low-level HTTP)
2. Update EmployeeImportService to use new API method (business logic)
3. Create route to trigger fetch (web layer)
4. Add UI button to initiate import (presentation layer)
5. Story 3.2 will filter duplicates before display

[Source: docs/sprint-artifacts/1-2-employee-import-service-layer-setup.md#Dev-Agent-Record]

### References

- [Source: docs/epics.md#Story-3.1 (lines 394-428)] - Story definition and acceptance criteria
- [Source: docs/prd.md#Employee-Import-Crossmark-API (FR9-FR12, FR32, FR38)] - API integration requirements
- [Source: docs/architecture.md#Integration-Points (lines 148-182)] - API endpoint and response format
- [Crossmark API Documentation] - Endpoint specifications (if available)

## Dev Agent Record

### Context Reference

Story context: docs/sprint-artifacts/3-1-crossmark-api-integration-for-employee-fetch.context.xml

### Agent Model Used

<!-- Will be populated by dev agent -->

### Debug Log References

### Completion Notes List

### File List

## Change Log

| Date | Author | Change Description |
|------|--------|-------------------|
| 2025-11-21 | SM Agent (Elliot) | Initial story creation from Epic 3.1 - Crossmark API integration foundation |
