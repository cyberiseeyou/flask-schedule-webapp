# Story 2.2: duplicate-detection-on-manual-employee-add

Status: ready-for-dev

## Story

As a **scheduling manager**,
I want **the system to prevent me from adding an employee with a duplicate name**,
so that **I don't accidentally create multiple records for the same person**.

## Acceptance Criteria

**Given** an employee named "Jane Doe" already exists in the database
**When** I submit the add form with name "jane doe" (different case)
**Then** the form does NOT create a new employee

**And** an error message displays: "Employee 'jane doe' already exists"

**And** the form remains open with my entered data preserved

**And** I can correct the name and resubmit

**And** server-side validation always checks for duplicates (client-side is UX only)

**And** the duplicate check completes in < 2 seconds (NFR-P1)

## Tasks / Subtasks

- [ ] Task 1: Add duplicate detection to form handler (AC: Server-side duplicate check)
  - [ ] Subtask 1.1: In `/add` route POST handler, after `form.validate_on_submit()` passes
  - [ ] Subtask 1.2: Import EmployeeImportService: `from app.services.employee_import_service import EmployeeImportService`
  - [ ] Subtask 1.3: Call duplicate check: `existing = EmployeeImportService.check_duplicate_name(form.name.data)`
  - [ ] Subtask 1.4: If existing employee found, set form error and re-render
  - [ ] Subtask 1.5: Add form field error: `form.name.errors.append(f"Employee '{form.name.data}' already exists")`
  - [ ] Subtask 1.6: Return rendered template with form (preserves entered data)

- [ ] Task 2: Display duplicate error message (AC: Clear error message displayed)
  - [ ] Subtask 2.1: In `add_employee.html` template, add error display block for name field
  - [ ] Subtask 2.2: Use WTForms error rendering: `{% if form.name.errors %} ... {% endif %}`
  - [ ] Subtask 2.3: Style error message with Bootstrap alert-danger or similar
  - [ ] Subtask 2.4: Ensure error message is visible above or below name field
  - [ ] Subtask 2.5: Test error display: Submit duplicate name, verify error shows

- [ ] Task 3: Preserve form data on validation failure (AC: Entered data preserved)
  - [ ] Subtask 3.1: Verify WTForms automatically populates form fields with previous data
  - [ ] Subtask 3.2: Test: Enter data in all fields, submit with duplicate name
  - [ ] Subtask 3.3: Verify all fields (except name if corrected) retain entered values
  - [ ] Subtask 3.4: Ensure dropdowns and checkboxes maintain selected state

- [ ] Task 4: Add comprehensive duplicate detection tests (AC: All case variations tested)
  - [ ] Subtask 4.1: Create `tests/test_employee_routes.py` for route testing
  - [ ] Subtask 4.2: Test exact case match: Add "John Smith" when "John Smith" exists
  - [ ] Subtask 4.3: Test different case: Add "john smith" when "John Smith" exists
  - [ ] Subtask 4.4: Test mixed case: Add "JOHN SMITH" when "John Smith" exists
  - [ ] Subtask 4.5: Test partial match doesn't trigger: "John" doesn't match "John Smith"
  - [ ] Subtask 4.6: Test whitespace variations: " John Smith " matches "John Smith"
  - [ ] Subtask 4.7: Verify error message format and content

- [ ] Task 5: Measure and verify performance (AC: Duplicate check < 2 seconds)
  - [ ] Subtask 5.1: Add timing measurement in route handler (optional, for dev verification)
  - [ ] Subtask 5.2: Test with database of 1000 employees
  - [ ] Subtask 5.3: Measure duplicate check execution time
  - [ ] Subtask 5.4: Verify check completes in < 2 seconds (should be < 100ms with index)
  - [ ] Subtask 5.5: Document performance results in completion notes

## Dev Notes

### Architecture Patterns and Constraints

**Error Handling Pattern** (Architecture lines 354-377):
- Server-side validation is mandatory (client-side is UX enhancement only)
- Use WTForms field errors for inline error display
- Flash messages for general errors (network failures, etc.)
- Re-render form with errors, preserving user input

**Duplicate Detection Pattern** (Architecture lines 381-416):
- Use EmployeeImportService.check_duplicate_name for case-insensitive lookup
- O(log n) performance via database index ix_employee_name_lower
- Returns Optional[Employee]: None if unique, Employee if duplicate

**Performance Requirements** (PRD NFR-P1):
- Manual add operations must complete in < 2 seconds
- Duplicate check leverages database index for fast lookups
- Expected performance: < 100ms for duplicate check

### Project Structure Notes

**Files to Modify:**
- `app/routes/employees.py` - Add duplicate detection to `/add` POST handler
- `app/templates/employees/add_employee.html` - Add error display markup

**Files to Create:**
- `tests/test_employee_routes.py` - Integration tests for employee add route

**Integration Points:**
- EmployeeImportService.check_duplicate_name (Story 1.2, verified in Story 1.4)
- Employee model with ix_employee_name_lower index (Story 1.1)

### Learnings from Previous Story

**From Story 2-1-manual-employee-add-form-with-validation (Status: drafted)**

- **Form Handler Location**: `/add` route in `app/routes/employees.py`
- **Form Class**: AddEmployeeForm with name field as required
- **Template**: `app/templates/employees/add_employee.html`
- **Validation**: Uses `form.validate_on_submit()` for POST requests

**From Story 1-4-case-insensitive-duplicate-detection-implementation (Status: drafted)**

- **Duplicate Detection Method**: `EmployeeImportService.check_duplicate_name(name)`
- **Return Type**: `Optional[Employee]` - None if unique, Employee object if duplicate
- **Performance**: Uses ix_employee_name_lower index for O(log n) lookups
- **Case Handling**: Fully case-insensitive, handles unicode characters

**From Story 1-2-employee-import-service-layer-setup (Status: done)**

- **Service Import**: `from app.services.employee_import_service import EmployeeImportService`
- **Method Signature**: `check_duplicate_name(name: str) -> Optional[Employee]`
- **Usage Pattern**: Call before creating new employee to check for duplicates

**Implementation Approach:**
1. Add duplicate check after form validation passes
2. If duplicate found: Add field error and re-render form
3. If unique: Proceed with employee creation (Story 2.3 handles success)

[Source: docs/sprint-artifacts/2-1-manual-employee-add-form-with-validation.md]
[Source: docs/sprint-artifacts/1-2-employee-import-service-layer-setup.md#Dev-Agent-Record]

### References

- [Source: docs/epics.md#Story-2.2 (lines 316-347)] - Story definition and acceptance criteria
- [Source: docs/prd.md#Employee-Addition-Manual (FR5-FR6)] - Duplicate detection requirements
- [Source: docs/architecture.md#Error-Handling-Pattern (lines 354-377)] - Error handling and form validation
- [Source: docs/architecture.md#Duplicate-Detection-Pattern (lines 381-416)] - Case-insensitive duplicate logic

## Dev Agent Record

### Context Reference

Story context: docs/sprint-artifacts/2-2-duplicate-detection-on-manual-employee-add.context.xml

### Agent Model Used

<!-- Will be populated by dev agent -->

### Debug Log References

### Completion Notes List

### File List

## Change Log

| Date | Author | Change Description |
|------|--------|-------------------|
| 2025-11-21 | SM Agent (Elliot) | Initial story creation from Epic 2.2 - Duplicate detection for manual add |
