# Story 3.7: data-accessibility-for-auto-scheduler

Status: ready-for-dev

## Story

As a **developer of the auto-scheduler**,
I want **imported employee data including MV Retail numbers immediately accessible**,
so that **the auto-scheduler can use employee data for scheduling operations without delays**.

## Acceptance Criteria

**Given** employees have been successfully imported from Crossmark API
**When** the auto-scheduler queries for employees with MV Retail numbers
**Then** all imported employees are returned with `mv_retail_employee_number` field populated

**And** the data is available immediately after import (no cache invalidation delay per NFR-R3)

**And** the auto-scheduler can filter employees by `mv_retail_employee_number IS NOT NULL`

**And** the `crossmark_employee_id` field can be used for future sync/update operations

**And** existing auto-scheduler code continues to work without modification (NFR-I1)

## Tasks / Subtasks

- [ ] Task 1: Verify Employee model fields accessible (AC: Fields available for querying)
  - [ ] Subtask 1.1: Review Employee model in `app/models/employee.py`
  - [ ] Subtask 1.2: Verify `mv_retail_employee_number` field exists and is queryable
  - [ ] Subtask 1.3: Verify `crossmark_employee_id` field exists and is queryable
  - [ ] Subtask 1.4: Verify fields are properly typed (String) and indexed if needed
  - [ ] Subtask 1.5: Test query: `Employee.query.filter(Employee.mv_retail_employee_number.isnot(None)).all()`
  - [ ] Subtask 1.6: Verify query returns expected employees after import

- [ ] Task 2: Test immediate data availability after import (AC: No cache delay)
  - [ ] Subtask 2.1: Import employee via Story 3.5 import execution
  - [ ] Subtask 2.2: Immediately query for imported employee by name
  - [ ] Subtask 2.3: Verify employee record returned with mv_retail_employee_number populated
  - [ ] Subtask 2.4: Verify no caching layer blocks immediate access (Flask-SQLAlchemy default behavior)
  - [ ] Subtask 2.5: Test in same request context and different request context
  - [ ] Subtask 2.6: Meets NFR-R3: data available immediately after commit

- [ ] Task 3: Create helper query for auto-scheduler integration (AC: Query helper available)
  - [ ] Subtask 3.1: In Employee model or service, add class method: `get_employees_with_mv_retail_number()`
  - [ ] Subtask 3.2: Method returns: `Employee.query.filter(Employee.mv_retail_employee_number.isnot(None)).all()`
  - [ ] Subtask 3.3: Add docstring explaining purpose for auto-scheduler integration
  - [ ] Subtask 3.4: Optional: Add method `get_by_mv_retail_number(mv_number: str) -> Optional[Employee]`
  - [ ] Subtask 3.5: Optional: Add method `get_by_crossmark_id(crossmark_id: str) -> Optional[Employee]`
  - [ ] Subtask 3.6: Test helper methods return correct results

- [ ] Task 4: Review auto-scheduler component integration (AC: No breaking changes)
  - [ ] Subtask 4.1: Locate auto-scheduler code (likely in `app/routes/auto_scheduler.py` or `app/services/scheduling_engine.py`)
  - [ ] Subtask 4.2: Review how auto-scheduler queries employees
  - [ ] Subtask 4.3: Verify existing queries still work (backward compatibility)
  - [ ] Subtask 4.4: Check if auto-scheduler already uses mv_retail_employee_number (may be expecting it)
  - [ ] Subtask 4.5: Document any integration points or assumptions
  - [ ] Subtask 4.6: No code changes needed if existing queries compatible (NFR-I1)

- [ ] Task 5: Create integration test for auto-scheduler access (AC: Integration validated)
  - [ ] Subtask 5.1: Create test: import employee, then query as auto-scheduler would
  - [ ] Subtask 5.2: Test filter: employees with MV Retail numbers only
  - [ ] Subtask 5.3: Test query by specific MV Retail number
  - [ ] Subtask 5.4: Test query by Crossmark ID
  - [ ] Subtask 5.5: Verify data integrity: all fields present and correct
  - [ ] Subtask 5.6: Test performance: query completes quickly (< 100ms for typical datasets)

- [ ] Task 6: Document data fields for auto-scheduler team (AC: Integration documented)
  - [ ] Subtask 6.1: Create or update documentation: data models or API contracts
  - [ ] Subtask 6.2: Document `mv_retail_employee_number`: Purpose, type, nullable, source
  - [ ] Subtask 6.3: Document `crossmark_employee_id`: Purpose, type, unique constraint, source
  - [ ] Subtask 6.4: Document query patterns: filter by IS NOT NULL, query by specific value
  - [ ] Subtask 6.5: Document data availability: immediate after import commit
  - [ ] Subtask 6.6: Document default values for manually added employees (fields will be NULL)

- [ ] Task 7: Test backward compatibility with existing features (AC: No regressions)
  - [ ] Subtask 7.1: Test existing employee list view: verify new fields don't break display
  - [ ] Subtask 7.2: Test existing employee edit: verify new fields can be updated if needed
  - [ ] Subtask 7.3: Test existing manual add: verify works without MV Retail number (NULL)
  - [ ] Subtask 7.4: Test auto-scheduler: run scheduling operation with mixed employees (some with MV #, some without)
  - [ ] Subtask 7.5: Verify no SQL errors or null pointer exceptions
  - [ ] Subtask 7.6: Meets NFR-I1: existing features continue to work

- [ ] Task 8: Validate Epic 3 completion (AC: All import functionality working end-to-end)
  - [ ] Subtask 8.1: Run full import workflow: Fetch → Filter → Select → Import
  - [ ] Subtask 8.2: Verify imported employees appear in employees list
  - [ ] Subtask 8.3: Verify imported employees have MV Retail numbers populated
  - [ ] Subtask 8.4: Verify auto-scheduler can access imported employees
  - [ ] Subtask 8.5: Verify error handling works for all failure scenarios (Story 3.6)
  - [ ] Subtask 8.6: Verify all acceptance criteria from Epic 3 met
  - [ ] Subtask 8.7: Epic 3 complete: Auto-scheduler unblocked and operational

## Dev Notes

### Architecture Patterns and Constraints

**Integration Points** (Architecture lines 148-182):
- Employee model fields: `mv_retail_employee_number`, `crossmark_employee_id`
- Auto-scheduler component: Uses Employee model for scheduling operations
- No caching layer: Flask-SQLAlchemy default behavior ensures immediate data access
- Backward compatibility: Existing code continues to work (fields nullable)

**Reliability Requirements** (PRD NFR-R3):
- Data available immediately after db.session.commit() completes
- No cache invalidation delay (default Flask-SQLAlchemy behavior)
- SQLAlchemy session management handles consistency

**Integration Requirements** (PRD NFR-I1, NFR-I3):
- Existing auto-scheduler code continues to work without modification
- New fields are optional (nullable) for backward compatibility
- Auto-scheduler can selectively query employees with MV Retail numbers
- Crossmark employee ID enables future sync operations

### Project Structure Notes

**Files to Review:**
- `app/models/employee.py` - Employee model with new fields (Story 1.1)
- `app/routes/auto_scheduler.py` - Auto-scheduler routes (integration point)
- `app/services/scheduling_engine.py` - Scheduling logic (integration point)

**Files to Modify (Optional):**
- `app/models/employee.py` - Add helper class methods for auto-scheduler queries
- Documentation files - Document new fields and integration patterns

**Query Patterns:**
```python
# Get all employees with MV Retail numbers (for auto-scheduler)
employees = Employee.query.filter(Employee.mv_retail_employee_number.isnot(None)).all()

# Get employee by MV Retail number
employee = Employee.query.filter_by(mv_retail_employee_number='12345').first()

# Get employee by Crossmark ID
employee = Employee.query.filter_by(crossmark_employee_id='EMP001').first()

# Filter in auto-scheduler (backward compatible)
all_employees = Employee.query.filter_by(is_active=True).all()
# New fields are NULL for manually added employees, populated for imported
```

**Dependencies:**
- Story 1.1: Database fields exist and are accessible
- Story 3.5: Import execution populates fields correctly
- Existing auto-scheduler component (integration target)

### Learnings from Previous Story

**From Story 3-6-error-handling-for-api-and-network-failures (Status: drafted)**

- **Error Handling Complete**: All import routes have comprehensive error handling
- **Data Integrity**: No partial data saved on errors ensures clean database state
- **Transaction Safety**: Atomic operations ensure data consistency

**From Story 3-5-atomic-bulk-import-execution (Status: drafted)**

- **Import Execution**: bulk_import_employees populates mv_retail_employee_number and crossmark_employee_id
- **Field Mapping**: repId → mv_retail_employee_number, employeeId → crossmark_employee_id, title → name
- **Immediate Commit**: db.session.commit() makes data immediately available (no delay)

**From Story 1-1-database-schema-migration-for-employee-import-fields (Status: ready-for-dev/done)**

- **Database Fields**: mv_retail_employee_number (String(50), nullable, indexed)
- **Database Fields**: crossmark_employee_id (String(50), nullable, unique)
- **Index**: Case-insensitive index on name for duplicate detection
- **Backward Compatibility**: Fields nullable, existing data intact

**From Story 1-2-employee-import-service-layer-setup (Status: done)**

- **Service Implementation**: All import methods tested and working
- **Data Access**: Uses Employee model via current_app.config['Employee'] (factory pattern)
- **Query Performance**: Database queries optimized with indexes

**Integration Strategy:**
- This story validates that Epic 3 achieves its goal: unblock auto-scheduler
- No new functionality - validation and integration testing
- Documents data fields for cross-team coordination
- Confirms backward compatibility and immediate data availability
- Epic 3 completion milestone: Auto-scheduler operational with MV Retail numbers

[Source: docs/sprint-artifacts/3-6-error-handling-for-api-and-network-failures.md]
[Source: docs/sprint-artifacts/3-5-atomic-bulk-import-execution.md]
[Source: docs/sprint-artifacts/1-1-database-schema-migration-for-employee-import-fields.md]
[Source: docs/sprint-artifacts/1-2-employee-import-service-layer-setup.md#Dev-Agent-Record]

### References

- [Source: docs/epics.md#Story-3.7 (lines 621-653)] - Story definition and acceptance criteria
- [Source: docs/prd.md#Integration-with-Existing-System (FR29, FR37-FR40, NFR-I1, NFR-I3, NFR-R3)] - Integration requirements
- [Source: docs/architecture.md#Integration-Points (lines 148-182)] - System integration patterns
- [SQLAlchemy: Querying Guide](https://docs.sqlalchemy.org/en/20/orm/queryguide.html) - Query patterns and filtering

## Dev Agent Record

### Context Reference

Story context: docs/sprint-artifacts/3-7-*.context.xml

### Agent Model Used

<!-- Will be populated by dev agent -->

### Debug Log References

### Completion Notes List

### File List

## Change Log

| Date | Author | Change Description |
|------|--------|-------------------|
| 2025-11-21 | SM Agent (Elliot) | Initial story creation from Epic 3.7 - Data accessibility for auto-scheduler (Epic 3 completion validation) |
