# Story 3.6: error-handling-for-api-and-network-failures

Status: ready-for-dev

## Story

As a **scheduling manager**,
I want **clear error messages when Crossmark API fails or network issues occur**,
so that **I understand what went wrong and can take appropriate action**.

## Acceptance Criteria

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

## Tasks / Subtasks

- [ ] Task 1: Add network error handling to API fetch (AC: Network failures caught and handled)
  - [ ] Subtask 1.1: In `app/routes/employees.py`, locate `/import-crossmark` route
  - [ ] Subtask 1.2: Wrap API call in try/except: `try: employees = EmployeeImportService.fetch_crossmark_employees()`
  - [ ] Subtask 1.3: Catch `requests.exceptions.RequestException`: network/connection errors
  - [ ] Subtask 1.4: Catch `requests.exceptions.Timeout`: API timeout errors
  - [ ] Subtask 1.5: Flash message: `flash('Unable to connect to Crossmark API. Please try again.', 'error')`
  - [ ] Subtask 1.6: Log error: `logger.error(f"Crossmark API network error: {str(e)}", exc_info=True)`
  - [ ] Subtask 1.7: Redirect to employees page: `return redirect(url_for('employees.index'))`

- [ ] Task 2: Add authentication error handling (AC: Session expiry redirects to login)
  - [ ] Subtask 2.1: Define custom exception in SessionAPIService: `class APIAuthenticationError(Exception)`
  - [ ] Subtask 2.2: In `app/integrations/external_api/session_api_service.py`, check API response status
  - [ ] Subtask 2.3: If response.status_code == 401 or 403: raise APIAuthenticationError
  - [ ] Subtask 2.4: In route, catch APIAuthenticationError
  - [ ] Subtask 2.5: Flash message: `flash('Session expired. Please log in again.', 'warning')`
  - [ ] Subtask 2.6: Clear session if needed: `session.clear()`
  - [ ] Subtask 2.7: Redirect to login page: `return redirect(url_for('auth.login'))` (adjust route name)

- [ ] Task 3: Add Pydantic validation error handling (AC: Invalid API responses caught)
  - [ ] Subtask 3.1: Import Pydantic ValidationError: `from pydantic import ValidationError`
  - [ ] Subtask 3.2: Catch ValidationError in route: `except ValidationError as e`
  - [ ] Subtask 3.3: Flash message: `flash('Received unexpected data from Crossmark. Please contact support.', 'error')`
  - [ ] Subtask 3.4: Log validation details: `logger.error(f"Crossmark API response validation failed: {str(e)}", exc_info=True)`
  - [ ] Subtask 3.5: Include response snippet in log (first 500 chars): `logger.debug(f"Response: {response_text[:500]}")`
  - [ ] Subtask 3.6: Redirect to employees page

- [ ] Task 4: Add comprehensive error logging (AC: All errors logged for debugging)
  - [ ] Subtask 4.1: Use current_app.logger for all error logging
  - [ ] Subtask 4.2: Log with appropriate levels: ERROR for failures, WARNING for auth issues
  - [ ] Subtask 4.3: Include exc_info=True for stack traces: `logger.error(msg, exc_info=True)`
  - [ ] Subtask 4.4: Log request details: endpoint, method, user (if available)
  - [ ] Subtask 4.5: Log response details: status code, response snippet
  - [ ] Subtask 4.6: Test logs appear in application logs during errors

- [ ] Task 5: Ensure no partial data saved on errors (AC: Database remains clean)
  - [ ] Subtask 5.1: Review all database operations in import flow
  - [ ] Subtask 5.2: Verify API errors happen BEFORE any database writes
  - [ ] Subtask 5.3: Casing updates (Story 3.2) happen in separate transaction - add rollback on error
  - [ ] Subtask 5.4: Import execution (Story 3.5) uses atomic transaction - already safe
  - [ ] Subtask 5.5: Test: inject API error, verify zero database changes
  - [ ] Subtask 5.6: Test: inject validation error, verify zero database changes

- [ ] Task 6: Add error handling to import execution route (AC: Import errors handled gracefully)
  - [ ] Subtask 6.1: In `/import-crossmark/import` POST route (Story 3.5), review error handling
  - [ ] Subtask 6.2: Catch IntegrityError: duplicate key or constraint violations
  - [ ] Subtask 6.3: Flash message: `flash('Import failed due to data conflict. Please try again.', 'error')`
  - [ ] Subtask 6.4: Catch general exceptions: `except Exception as e`
  - [ ] Subtask 6.5: Flash message: `flash('Import failed. Please try again or contact support.', 'error')`
  - [ ] Subtask 6.6: Log error details: `logger.error(f"Bulk import execution failed: {str(e)}", exc_info=True)`
  - [ ] Subtask 6.7: Verify transaction rollback happens (from Story 3.5 implementation)

- [ ] Task 7: Create user-friendly error message helper (AC: Consistent error messages)
  - [ ] Subtask 7.1: Create error message constants in route or service
  - [ ] Subtask 7.2: MSG_NETWORK_ERROR = "Unable to connect to Crossmark API. Please try again."
  - [ ] Subtask 7.3: MSG_AUTH_ERROR = "Session expired. Please log in again."
  - [ ] Subtask 7.4: MSG_VALIDATION_ERROR = "Received unexpected data from Crossmark. Please contact support."
  - [ ] Subtask 7.5: MSG_IMPORT_ERROR = "Import failed. Please try again or contact support."
  - [ ] Subtask 7.6: Use constants in flash messages for consistency

- [ ] Task 8: Test all error scenarios (AC: All error paths tested)
  - [ ] Subtask 8.1: Test network timeout: Mock API call to raise Timeout exception
  - [ ] Subtask 8.2: Test connection error: Mock API call to raise ConnectionError
  - [ ] Subtask 8.3: Test authentication error: Mock API response with 401 status
  - [ ] Subtask 8.4: Test validation error: Mock API response with invalid JSON structure
  - [ ] Subtask 8.5: Test import constraint error: Try importing employee with duplicate crossmark_employee_id
  - [ ] Subtask 8.6: Test general error: Mock service to raise unexpected exception
  - [ ] Subtask 8.7: Verify error messages display correctly in UI
  - [ ] Subtask 8.8: Verify error logs contain useful debugging information
  - [ ] Subtask 8.9: Verify no database changes occur when errors happen

## Dev Notes

### Architecture Patterns and Constraints

**Error Handling Pattern** (Architecture lines 354-377):
- Catch specific exceptions first (RequestException, ValidationError), then general Exception
- Log all errors with full stack traces: `logger.error(msg, exc_info=True)`
- Display user-friendly error messages via flash (never expose internal details)
- Always redirect to safe page (employees list or login)
- Use appropriate flash categories: 'error' for failures, 'warning' for auth issues

**Security Requirements** (PRD NFR-S4):
- Never expose internal error details to users
- Generic messages: "Unable to connect", "Please try again"
- Log full details server-side for debugging
- Sanitize any response data before logging (no credentials)

**Reliability Requirements** (PRD NFR-R1, NFR-R4):
- No partial data saved when errors occur
- Atomic transactions for all database operations
- Graceful degradation: errors don't crash application
- Users can recover by retrying or logging in again

### Project Structure Notes

**Files to Modify:**
- `app/routes/employees.py` - Add error handling to `/import-crossmark` and `/import-crossmark/import` routes
- `app/integrations/external_api/session_api_service.py` - Add APIAuthenticationError exception, check response status
- `app/services/employee_import_service.py` - Ensure errors propagate with clear exceptions

**Error Handling Structure:**
```python
from requests.exceptions import RequestException, Timeout
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

@bp.route('/import-crossmark', methods=['GET'])
def import_crossmark_initiate():
    try:
        # Fetch employees from API
        employees = EmployeeImportService.fetch_crossmark_employees()

        # Filter duplicates
        existing = Employee.query.all()
        new_employees, casing_updates = EmployeeImportService.filter_duplicate_employees(employees, existing)

        # Update casing
        try:
            for emp, new_name in casing_updates:
                emp.name = new_name
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.warning(f"Casing update failed: {str(e)}")

        # Render selection or redirect if zero new
        if len(new_employees) == 0:
            flash('No new employees to import...', 'info')
            return redirect(url_for('employees.index'))

        session['pending_import_employees'] = [emp.dict() for emp in new_employees]
        return render_template('employees/import_select.html', employees=new_employees, count=len(new_employees))

    except APIAuthenticationError:
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))
    except (RequestException, Timeout) as e:
        current_app.logger.error(f"Crossmark API network error: {str(e)}", exc_info=True)
        flash('Unable to connect to Crossmark API. Please try again.', 'error')
        return redirect(url_for('employees.index'))
    except ValidationError as e:
        current_app.logger.error(f"Crossmark API validation error: {str(e)}", exc_info=True)
        flash('Received unexpected data from Crossmark. Please contact support.', 'error')
        return redirect(url_for('employees.index'))
    except Exception as e:
        current_app.logger.error(f"Import initiation failed: {str(e)}", exc_info=True)
        flash('An unexpected error occurred. Please try again.', 'error')
        return redirect(url_for('employees.index'))
```

**Dependencies:**
- Story 3.1: API fetch route exists
- Story 3.2: Duplicate filtering logic
- Story 3.5: Import execution route
- Story 1.2: Service methods that may raise exceptions

### Learnings from Previous Story

**From Story 3-5-atomic-bulk-import-execution (Status: drafted)**

- **Import Route**: `/import-crossmark/import` POST route needs error handling
- **Transaction Safety**: bulk_import_employees uses atomic transaction with rollback
- **Error Logging**: Already logs import failures, ensure comprehensive
- **Flash Messages**: Uses 'success' and 'error' categories

**From Story 3-1-crossmark-api-integration-for-employee-fetch (Status: drafted)**

- **API Call**: fetch_crossmark_employees() calls SessionAPIService
- **Error Points**: Network errors, authentication errors, response parsing errors
- **SessionAPIService**: Located at `app/integrations/external_api/session_api_service.py`
- **Loading Indicator**: Already shows during API call

**From Story 1-2-employee-import-service-layer-setup (Status: done)**

- **Service Errors**: Methods raise exceptions on failures
- **Error Handling**: Generic exceptions raised, need specific exception types
- **API Wrapper**: fetch_crossmark_employees wraps SessionAPIService call

**From Story 1-3-pydantic-models-for-crossmark-api-response-validation (Status: drafted)**

- **ValidationError**: Pydantic raises ValidationError on schema mismatch
- **Parsing**: `[CrossmarkEmployee(**emp) for emp in response]` can fail
- **Error Details**: ValidationError provides field-level details for logging

**Integration Strategy:**
- This story adds comprehensive error handling to all import routes
- Wraps existing functionality from Stories 3.1, 3.2, 3.5
- Defines custom APIAuthenticationError for session management
- Ensures no database corruption on failures
- Story 3.7 will validate data accessibility (final integration check)

[Source: docs/sprint-artifacts/3-5-atomic-bulk-import-execution.md]
[Source: docs/sprint-artifacts/3-1-crossmark-api-integration-for-employee-fetch.md]
[Source: docs/sprint-artifacts/1-2-employee-import-service-layer-setup.md#Dev-Agent-Record]
[Source: docs/sprint-artifacts/1-3-pydantic-models-for-crossmark-api-response-validation.md]

### References

- [Source: docs/epics.md#Story-3.6 (lines 581-619)] - Story definition and acceptance criteria
- [Source: docs/prd.md#Error-Handling-User-Feedback (FR32-FR36, NFR-S4, NFR-U3)] - Error handling requirements
- [Source: docs/architecture.md#Error-Handling-Pattern (lines 354-377)] - Exception handling implementation
- [Python Requests: Exception Handling](https://requests.readthedocs.io/en/latest/user/quickstart/#errors-and-exceptions) - Network error types
- [Pydantic: ValidationError](https://docs.pydantic.dev/latest/concepts/validation_errors/) - API validation errors

## Dev Agent Record

### Context Reference

Story context: docs/sprint-artifacts/3-6-*.context.xml

### Agent Model Used

<!-- Will be populated by dev agent -->

### Debug Log References

### Completion Notes List

### File List

## Change Log

| Date | Author | Change Description |
|------|--------|-------------------|
| 2025-11-21 | SM Agent (Elliot) | Initial story creation from Epic 3.6 - Error handling for API and network failures |
