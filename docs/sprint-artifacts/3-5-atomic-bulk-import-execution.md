# Story 3.5: atomic-bulk-import-execution

Status: ready-for-dev

## Story

As a **scheduling manager**,
I want **selected employees imported in a single atomic operation**,
so that **either all my selections are imported successfully or none are, preventing partial imports**.

## Acceptance Criteria

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

## Tasks / Subtasks

- [ ] Task 1: Create import execution route (AC: POST route handles form submission)
  - [ ] Subtask 1.1: In `app/routes/employees.py`, add route `@bp.route('/import-crossmark/import', methods=['POST'])`
  - [ ] Subtask 1.2: Import required dependencies: request, flash, redirect, url_for, db
  - [ ] Subtask 1.3: Import EmployeeImportService
  - [ ] Subtask 1.4: Add CSRF validation (automatic with Flask-WTF)
  - [ ] Subtask 1.5: Extract form data: `selected_ids = request.form.getlist('selected_employees[]')`
  - [ ] Subtask 1.6: Log import initiation: `logger.info(f"Bulk import initiated for {len(selected_ids)} employees")`

- [ ] Task 2: Retrieve employee data for selected IDs (AC: Full employee objects available for import)
  - [ ] Subtask 2.1: Retrieve pending import employees from session: `session.get('pending_import_employees', [])`
  - [ ] Subtask 2.2: Alternative: Re-fetch from Crossmark API if not using session storage
  - [ ] Subtask 2.3: Filter employees list to only selected IDs: `[emp for emp in employees if emp.employeeId in selected_ids]`
  - [ ] Subtask 2.4: Parse employee data into CrossmarkEmployee Pydantic models
  - [ ] Subtask 2.5: Validate all selected employees found: if count mismatch, show error
  - [ ] Subtask 2.6: Handle edge case: no employees selected (should be prevented by button disabled state)

- [ ] Task 3: Call bulk import service method (AC: EmployeeImportService creates records)
  - [ ] Subtask 3.1: Call `count = EmployeeImportService.bulk_import_employees(selected_employees)`
  - [ ] Subtask 3.2: Wrap in try/except for error handling
  - [ ] Subtask 3.3: Service method handles transaction commit/rollback internally
  - [ ] Subtask 3.4: Verify returned count matches expected: if mismatch, log warning
  - [ ] Subtask 3.5: Log successful import: `logger.info(f"Successfully imported {count} employees")`

- [ ] Task 4: Implement atomic transaction in service (AC: All-or-nothing import)
  - [ ] Subtask 4.1: Open `app/services/employee_import_service.py`
  - [ ] Subtask 4.2: Review/update `bulk_import_employees` method from Story 1.2
  - [ ] Subtask 4.3: Ensure single transaction wraps all employee insertions
  - [ ] Subtask 4.4: Use try/except block: `try: ... db.session.commit() except: db.session.rollback(); raise`
  - [ ] Subtask 4.5: Create Employee instances with all required fields
  - [ ] Subtask 4.6: Set default values: role="Event Specialist", status="Inactive", availability=None
  - [ ] Subtask 4.7: Map Crossmark fields: title→name, repId→mv_retail_employee_number, employeeId→crossmark_employee_id
  - [ ] Subtask 4.8: Verify transaction rollback on any error (test with invalid data)

- [ ] Task 5: Set default values for imported employees (AC: Correct defaults applied)
  - [ ] Subtask 5.1: Set role field: `employee.role = 'Event Specialist'` or `job_title`
  - [ ] Subtask 5.2: Set status field: `employee.status = 'Inactive'` or `is_active = False`
  - [ ] Subtask 5.3: Set availability to None: no days available initially
  - [ ] Subtask 5.4: Verify Employee model field names match (check `app/models/employee.py`)
  - [ ] Subtask 5.5: Leave optional fields NULL if not provided by API
  - [ ] Subtask 5.6: Ensure defaults match Story 1.2 implementation

- [ ] Task 6: Display success message and redirect (AC: User sees confirmation)
  - [ ] Subtask 6.1: On successful import: `flash(f'{count} employees imported successfully', 'success')`
  - [ ] Subtask 6.2: Redirect to employees list: `return redirect(url_for('employees.index'))`
  - [ ] Subtask 6.3: Clear session data if used: `session.pop('pending_import_employees', None)`
  - [ ] Subtask 6.4: Ensure flash message displays on redirected page
  - [ ] Subtask 6.5: Test flash message styling (success category)

- [ ] Task 7: Handle import errors gracefully (AC: Errors don't crash, transaction rolls back)
  - [ ] Subtask 7.1: Catch database errors: `except IntegrityError as e`
  - [ ] Subtask 7.2: Catch general errors: `except Exception as e`
  - [ ] Subtask 7.3: Log error details: `logger.error(f"Bulk import failed: {str(e)}", exc_info=True)`
  - [ ] Subtask 7.4: Flash error message: `flash('Import failed. Please try again.', 'error')`
  - [ ] Subtask 7.5: Redirect back to selection page or employees list
  - [ ] Subtask 7.6: Verify transaction rollback: check database has zero new employees on error

- [ ] Task 8: Test bulk import end-to-end (AC: All scenarios tested)
  - [ ] Subtask 8.1: Test successful import: 15 employees selected → all 15 imported
  - [ ] Subtask 8.2: Test single employee import: 1 selected → 1 imported
  - [ ] Subtask 8.3: Test large batch: 100 employees → all imported in < 5 seconds
  - [ ] Subtask 8.4: Test transaction rollback: inject error mid-import → zero employees imported
  - [ ] Subtask 8.5: Test duplicate constraint: try importing same employee twice → error handled
  - [ ] Subtask 8.6: Test success message displays correctly
  - [ ] Subtask 8.7: Test imported employees appear in employees list with correct data

- [ ] Task 9: Performance optimization (AC: < 5 seconds for 100 employees)
  - [ ] Subtask 9.1: Use bulk insert if available: `db.session.bulk_save_objects(employees)`
  - [ ] Subtask 9.2: Minimize queries: create all Employee objects, then single commit
  - [ ] Subtask 9.3: Test performance with 100 employee import
  - [ ] Subtask 9.4: Log import duration: `logger.info(f"Import completed in {elapsed}s")`
  - [ ] Subtask 9.5: Verify meets NFR-P4: < 5 seconds for 100 employees
  - [ ] Subtask 9.6: Profile database queries if performance is slow

## Dev Notes

### Architecture Patterns and Constraints

**Transaction Pattern** (Architecture lines 419-446):
- Single database transaction wraps all employee insertions
- Atomic operation: all succeed or all fail (no partial imports)
- Explicit rollback on any error: `db.session.rollback()`
- Use try/except block for transaction management

**Service Layer Pattern** (Architecture lines 272-313):
- Business logic in `EmployeeImportService.bulk_import_employees()`
- Route handler delegates to service, handles HTTP concerns only
- Service returns count of imported employees
- Service raises exceptions on errors, route catches and handles

**Performance Requirements** (PRD NFR-P4):
- Import must complete in < 5 seconds for batches up to 100 employees
- Use efficient database operations (bulk insert, single commit)
- Minimize round-trips to database
- Log performance metrics for monitoring

**Error Handling Pattern** (Architecture lines 354-377):
- Catch specific exceptions first (IntegrityError), then general Exception
- Log full exception details with `exc_info=True`
- Display user-friendly error messages via flash
- Always rollback transaction on error

### Project Structure Notes

**Files to Modify:**
- `app/routes/employees.py` - Add `/import-crossmark/import` POST route
- `app/services/employee_import_service.py` - Verify/update `bulk_import_employees` method (Story 1.2)

**Route Handler Pattern:**
```python
@bp.route('/import-crossmark/import', methods=['POST'])
def import_crossmark_execute():
    try:
        selected_ids = request.form.getlist('selected_employees[]')
        employees = session.get('pending_import_employees', [])
        selected = [CrossmarkEmployee(**emp) for emp in employees if emp['employeeId'] in selected_ids]

        count = EmployeeImportService.bulk_import_employees(selected)

        flash(f'{count} employees imported successfully', 'success')
        session.pop('pending_import_employees', None)
        return redirect(url_for('employees.index'))
    except Exception as e:
        current_app.logger.error(f"Import failed: {str(e)}", exc_info=True)
        flash('Import failed. Please try again.', 'error')
        return redirect(url_for('employees.index'))
```

**Dependencies:**
- Story 1.2: `EmployeeImportService.bulk_import_employees()` method exists
- Story 3.4: Form submission includes selected employee IDs
- Story 3.3: Form posts to this route with CSRF token
- Story 1.3: CrossmarkEmployee Pydantic model for data validation

### Learnings from Previous Story

**From Story 3-4-select-all-deselect-all-functionality (Status: drafted)**

- **Form Submission**: Form posts to `/import-crossmark/import` route
- **Checkbox Values**: Selected employees submitted as array: `selected_employees[]`
- **Button Enabled**: Form only submits when button enabled (at least 1 checkbox checked)

**From Story 3-3-selection-interface-with-checkbox-table (Status: drafted)**

- **Form Method**: POST with CSRF token
- **Employee Data**: Checkboxes have employee data in data attributes or session
- **Template Form**: Wraps table and button for submission

**From Story 1-2-employee-import-service-layer-setup (Status: done)**

- **Service Method**: `bulk_import_employees(selected_employees: List[CrossmarkEmployee]) -> int`
- **Transaction Handling**: Service wraps all inserts in single transaction
- **Default Values**: Role="Event Specialist", Status="Inactive", Availability=None
- **Field Mapping**: repId→mv_retail_employee_number, employeeId→crossmark_employee_id, title→name
- **Returns**: Count of imported employees

**From Story 3-2-duplicate-filtering-before-display (Status: drafted)**

- **Session Storage**: Employee data stored in session: `session['pending_import_employees']`
- **Data Format**: List of dicts or serialized CrossmarkEmployee objects
- **Retrieval**: Extract in this route for import execution

**Integration Strategy:**
- This story completes the import workflow (fetch → filter → select → import)
- Route receives form submission from Story 3.3/3.4 UI
- Calls service layer from Story 1.2 for business logic
- Success redirects to employees list with confirmation
- Story 3.6 will add comprehensive error handling for edge cases

[Source: docs/sprint-artifacts/3-4-select-all-deselect-all-functionality.md]
[Source: docs/sprint-artifacts/3-3-selection-interface-with-checkbox-table.md]
[Source: docs/sprint-artifacts/1-2-employee-import-service-layer-setup.md#Dev-Agent-Record]
[Source: docs/sprint-artifacts/3-2-duplicate-filtering-before-display.md]

### References

- [Source: docs/epics.md#Story-3.5 (lines 541-579)] - Story definition and acceptance criteria
- [Source: docs/prd.md#Employee-Import-Crossmark-API (FR25-FR27, FR28, NFR-R1, NFR-R3, NFR-R4, NFR-P4)] - Bulk import requirements
- [Source: docs/architecture.md#Transaction-Pattern (lines 419-446)] - Atomic transaction implementation
- [Source: docs/architecture.md#Service-Layer-Pattern (lines 272-313)] - Business logic delegation
- [SQLAlchemy: Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html) - Transaction management

## Dev Agent Record

### Context Reference

Story context: docs/sprint-artifacts/3-5-*.context.xml

### Agent Model Used

<!-- Will be populated by dev agent -->

### Debug Log References

### Completion Notes List

### File List

## Change Log

| Date | Author | Change Description |
|------|--------|-------------------|
| 2025-11-21 | SM Agent (Elliot) | Initial story creation from Epic 3.5 - Atomic bulk import execution |
