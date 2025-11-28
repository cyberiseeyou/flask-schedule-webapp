# Story 3.2: duplicate-filtering-before-display

Status: ready-for-dev

## Story

As a **scheduling manager**,
I want **the system to automatically filter out employees who already exist in my roster**,
so that **I only see NEW employees available for import and don't waste time reviewing duplicates**.

## Acceptance Criteria

**Given** the system has fetched 50 employees from Crossmark API
**And** 20 of those employees already exist in the database (matched by case-insensitive name)
**When** the system prepares the selection interface
**Then** only the 30 NEW employees are displayed for selection

**And** the 20 duplicates are completely filtered out (not shown at all)

**And** for duplicates where name casing differs from API, the existing employee's name is updated to match API casing

**And** the filtering completes in < 500ms for rosters up to 10k employees (NFR-P5)

**And** the count message shows: "30 new employees available to import"

## Tasks / Subtasks

- [ ] Task 1: Implement duplicate filtering in route handler (AC: Only new employees shown)
  - [ ] Subtask 1.1: In `app/routes/employees.py`, locate or update `/import-crossmark` route from Story 3.1
  - [ ] Subtask 1.2: After fetching api_employees, query all existing employees: `existing = Employee.query.all()`
  - [ ] Subtask 1.3: Call `EmployeeImportService.filter_duplicate_employees(api_employees, existing)`
  - [ ] Subtask 1.4: Extract returned tuple: `(new_employees, employees_needing_casing_update)`
  - [ ] Subtask 1.5: Store new_employees for display in selection interface
  - [ ] Subtask 1.6: Log filtering results: `logger.info(f"Filtered {len(api_employees)} API employees: {len(new_employees)} new, {len(employees_needing_casing_update)} casing updates")`

- [ ] Task 2: Update name casing for existing employees (AC: Casing matches API)
  - [ ] Subtask 2.1: Iterate employees_needing_casing_update list
  - [ ] Subtask 2.2: For each tuple (employee, new_name): update employee.name = new_name
  - [ ] Subtask 2.3: Commit casing updates in single transaction: `db.session.commit()`
  - [ ] Subtask 2.4: Log casing updates: `logger.info(f"Updated name casing for {count} existing employees")`
  - [ ] Subtask 2.5: Handle transaction errors with rollback and error message

- [ ] Task 3: Handle zero new employees scenario (AC: "No new employees" message)
  - [ ] Subtask 3.1: Check if len(new_employees) == 0
  - [ ] Subtask 3.2: Flash message: `flash('No new employees to import. All Crossmark employees already exist in your roster.', 'info')`
  - [ ] Subtask 3.3: Redirect back to employees list: `return redirect(url_for('employees.index'))`
  - [ ] Subtask 3.4: Ensure casing updates still happen before redirect
  - [ ] Subtask 3.5: Log zero-import scenario: `logger.info("Import initiated but no new employees found")`

- [ ] Task 4: Pass filtered employees to selection interface (AC: New employees ready for selection)
  - [ ] Subtask 4.1: Store new_employees in session or pass to next route
  - [ ] Subtask 4.2: Option A: `session['pending_import_employees'] = [emp.dict() for emp in new_employees]`
  - [ ] Subtask 4.3: Option B: Render selection template directly with new_employees
  - [ ] Subtask 4.4: Calculate count: `count = len(new_employees)`
  - [ ] Subtask 4.5: Pass count to template or next route for display
  - [ ] Subtask 4.6: If using session storage, serialize CrossmarkEmployee objects properly

- [ ] Task 5: Optimize filtering performance (AC: < 500ms for 10k employees)
  - [ ] Subtask 5.1: Verify `filter_duplicate_employees` uses O(n) hash map (implemented in Story 1.4)
  - [ ] Subtask 5.2: Build lowercase name lookup map: `{name.lower(): employee}` from existing employees
  - [ ] Subtask 5.3: Single pass through api_employees for classification
  - [ ] Subtask 5.4: Avoid N queries (N+1 problem) - bulk query existing employees once
  - [ ] Subtask 5.5: Add performance logging: `logger.debug(f"Filtering completed in {elapsed_ms}ms")`
  - [ ] Subtask 5.6: Test with large dataset (1000+ employees) to verify < 500ms

- [ ] Task 6: Add unit and integration tests (AC: Filtering logic tested)
  - [ ] Subtask 6.1: Test scenario: 50 API employees, 20 duplicates → expect 30 new
  - [ ] Subtask 6.2: Test scenario: All API employees are duplicates → expect 0 new, redirect with message
  - [ ] Subtask 6.3: Test scenario: All API employees are new → expect all shown
  - [ ] Subtask 6.4: Test casing update: API has "John Smith", DB has "john smith" → expect name updated
  - [ ] Subtask 6.5: Test performance: 10k existing employees → verify < 500ms filtering time
  - [ ] Subtask 6.6: Test transaction rollback: casing update fails → verify no partial updates

## Dev Notes

### Architecture Patterns and Constraints

**Duplicate Detection Pattern** (Architecture lines 381-416):
- Use `EmployeeImportService.filter_duplicate_employees()` implemented in Story 1.4
- O(n) hash map approach: Build `{name.lower(): employee}` from existing roster
- Single pass through API employees for classification
- Return tuple: (new_employees_list, employees_needing_casing_update_list)

**Performance Requirements** (PRD NFR-P5):
- Filtering must complete in < 500ms for rosters up to 10k employees
- Use in-memory hash map (O(n)) instead of database queries (O(n²))
- Avoid N+1 query problem: fetch all existing employees once
- Log performance metrics for monitoring

**Consistency Rules** (Architecture lines 451-465):
- Update existing employee names to match API casing (source of truth)
- Use atomic transaction for casing updates
- Flash message categories: 'info' for zero-import scenario

### Project Structure Notes

**Files to Modify:**
- `app/routes/employees.py` - Update `/import-crossmark` route from Story 3.1
- `app/services/employee_import_service.py` - Verify filter_duplicate_employees implementation (Story 1.4)

**Dependencies:**
- Story 3.1: API fetch route exists and returns api_employees
- Story 1.4: filter_duplicate_employees method implemented and tested
- Story 1.2: EmployeeImportService available
- Story 1.1: Employee model has proper fields

**Flow After This Story:**
1. User clicks "Import from Crossmark" (Story 3.1)
2. System fetches employees from API (Story 3.1)
3. **System filters duplicates and updates casing (THIS STORY)**
4. System displays selection interface (Story 3.3)
5. User selects employees to import (Stories 3.4, 3.5)

### Learnings from Previous Story

**From Story 3-1-crossmark-api-integration-for-employee-fetch (Status: drafted)**

- **API Fetch**: Route `/import-crossmark` exists and calls `EmployeeImportService.fetch_crossmark_employees()`
- **Response Format**: Returns List[CrossmarkEmployee] (Pydantic models from Story 1.3)
- **Error Handling**: API errors handled with flash messages and redirect
- **Session Management**: Uses existing SessionAPIService for authentication
- **Next Step**: This story filters the fetched employees before display

**From Story 1-4-case-insensitive-duplicate-detection-implementation (Status: drafted)**

- **filter_duplicate_employees Available**: Method signature `filter_duplicate_employees(api_employees, existing_employees) -> tuple[List, List]`
- **Performance**: O(n) hash map approach meets < 500ms requirement
- **Returns**: Tuple of (new_employees, employees_needing_casing_update)
- **Usage Pattern**: Pass full lists, get filtered results back

**From Story 1-2-employee-import-service-layer-setup (Status: done)**

- **Service Location**: `app/services/employee_import_service.py`
- **Import Pattern**: `from app.services.employee_import_service import EmployeeImportService`
- **Database Access**: Query all employees: `Employee.query.all()`
- **Transaction Pattern**: Use try/except with db.session.commit() and rollback

**Integration Strategy:**
- This story bridges API fetch (3.1) and selection UI (3.3)
- Filtering happens server-side before rendering selection interface
- Casing updates happen immediately (not waiting for import)
- Zero-import scenario provides good UX feedback

[Source: docs/sprint-artifacts/3-1-crossmark-api-integration-for-employee-fetch.md#Dev-Agent-Record]
[Source: docs/sprint-artifacts/1-4-case-insensitive-duplicate-detection-implementation.md]
[Source: docs/sprint-artifacts/1-2-employee-import-service-layer-setup.md#Dev-Agent-Record]

### References

- [Source: docs/epics.md#Story-3.2 (lines 430-461)] - Story definition and acceptance criteria
- [Source: docs/prd.md#Employee-Import-Crossmark-API (FR13-FR17, FR30-FR31)] - Duplicate filtering requirements
- [Source: docs/architecture.md#Duplicate-Detection-Pattern (lines 381-416)] - O(n) hash map filtering approach
- [Source: docs/architecture.md#Performance-Requirements (NFR-P5)] - < 500ms filtering for 10k employees

## Dev Agent Record

### Context Reference

Story context: docs/sprint-artifacts/3-2-*.context.xml

### Agent Model Used

<!-- Will be populated by dev agent -->

### Debug Log References

### Completion Notes List

### File List

## Change Log

| Date | Author | Change Description |
|------|--------|-------------------|
| 2025-11-21 | SM Agent (Elliot) | Initial story creation from Epic 3.2 - Duplicate filtering before display |
