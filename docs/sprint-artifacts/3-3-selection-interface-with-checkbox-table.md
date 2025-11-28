# Story 3.3: selection-interface-with-checkbox-table

Status: ready-for-dev

## Story

As a **scheduling manager**,
I want **a clear table showing new employees with checkboxes so I can select which ones to import**,
so that **I have control over exactly who joins my roster**.

## Acceptance Criteria

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

## Tasks / Subtasks

- [ ] Task 1: Create selection interface template (AC: Table displays with all columns)
  - [ ] Subtask 1.1: Create file `app/templates/employees/import_select.html`
  - [ ] Subtask 1.2: Extend base template or employees base layout
  - [ ] Subtask 1.3: Add page heading: `<h2>{{ count }} new employees available to import</h2>`
  - [ ] Subtask 1.4: Create table structure with thead: Checkbox, Name, Employee ID, MV Retail #
  - [ ] Subtask 1.5: Add tbody with Jinja2 loop: `{% for employee in employees %}`
  - [ ] Subtask 1.6: Render each employee row with checkbox input and data fields
  - [ ] Subtask 1.7: Add table styling classes (Bootstrap or existing CSS framework)

- [ ] Task 2: Add checkbox column with data attributes (AC: Checkboxes identify employees)
  - [ ] Subtask 2.1: Add checkbox input: `<input type="checkbox" class="employee-select" ... />`
  - [ ] Subtask 2.2: Set data attributes: `data-employee-id="{{ employee.employeeId }}"`, `data-name="{{ employee.title }}"`
  - [ ] Subtask 2.3: Set data attribute: `data-rep-id="{{ employee.repId }}"`
  - [ ] Subtask 2.4: Default checkboxes to unchecked: no `checked` attribute
  - [ ] Subtask 2.5: Ensure checkbox IDs are unique: `id="emp-{{ loop.index }}"`
  - [ ] Subtask 2.6: Store full employee data as JSON in hidden div or data attribute for form submission

- [ ] Task 3: Render employee data in table cells (AC: All employee fields visible)
  - [ ] Subtask 3.1: Name column: `<td>{{ employee.title }}</td>`
  - [ ] Subtask 3.2: Employee ID column: `<td>{{ employee.employeeId }}</td>`
  - [ ] Subtask 3.3: MV Retail # column: `<td>{{ employee.repId }}</td>`
  - [ ] Subtask 3.4: Add conditional formatting for missing data (if any field is null/empty)
  - [ ] Subtask 3.5: Ensure proper HTML escaping: use `{{ }}` not `{{ | safe }}`
  - [ ] Subtask 3.6: Test with special characters in names (apostrophes, hyphens)

- [ ] Task 4: Add Select All / Deselect All controls (AC: Controls visible above table)
  - [ ] Subtask 4.1: Add controls div above table: `<div class="selection-controls">`
  - [ ] Subtask 4.2: Add "Select All" link: `<a href="#" id="select-all">Select All</a>`
  - [ ] Subtask 4.3: Add separator: ` | `
  - [ ] Subtask 4.4: Add "Deselect All" link: `<a href="#" id="deselect-all">Deselect All</a>`
  - [ ] Subtask 4.5: Style links consistently with existing UI patterns
  - [ ] Subtask 4.6: Position controls: right-aligned or left-aligned per design

- [ ] Task 5: Add Import Selected button (AC: Button disabled initially)
  - [ ] Subtask 5.1: Add button below table: `<button id="import-selected" type="submit" disabled>Import Selected</button>`
  - [ ] Subtask 5.2: Wrap table and button in form: `<form method="POST" action="{{ url_for('employees.import_crossmark_execute') }}">`
  - [ ] Subtask 5.3: Add CSRF token: `{{ csrf_token() }}`
  - [ ] Subtask 5.4: Style button: primary button style, disabled state visible
  - [ ] Subtask 5.5: Add button text span for dynamic count: `<span id="button-text">Import Selected</span>`
  - [ ] Subtask 5.6: Position button: centered or right-aligned per design

- [ ] Task 6: Update route to render selection template (AC: Route displays selection UI)
  - [ ] Subtask 6.1: In `app/routes/employees.py`, update `/import-crossmark` route from Story 3.2
  - [ ] Subtask 6.2: After filtering duplicates, check if new_employees list is not empty
  - [ ] Subtask 6.3: Calculate count: `count = len(new_employees)`
  - [ ] Subtask 6.4: Render template: `render_template('employees/import_select.html', employees=new_employees, count=count)`
  - [ ] Subtask 6.5: Pass CSRF token if not auto-included
  - [ ] Subtask 6.6: Test route: verify template renders with test data

- [ ] Task 7: Optimize for large datasets (AC: Responsive with 1000 employees)
  - [ ] Subtask 7.1: Test rendering with 1000+ employee records
  - [ ] Subtask 7.2: Add pagination if performance degrades (optional enhancement)
  - [ ] Subtask 7.3: Consider virtual scrolling for 5000+ records (optional)
  - [ ] Subtask 7.4: Ensure table uses efficient CSS (avoid complex selectors)
  - [ ] Subtask 7.5: Minimize JavaScript execution on page load
  - [ ] Subtask 7.6: Verify page load time < 2 seconds for 1000 employees (NFR-P3)

- [ ] Task 8: Add tests for selection interface (AC: Template and route tested)
  - [ ] Subtask 8.1: Test route renders template with correct data
  - [ ] Subtask 8.2: Test template displays count in heading
  - [ ] Subtask 8.3: Test table has correct number of rows
  - [ ] Subtask 8.4: Test checkboxes have correct data attributes
  - [ ] Subtask 8.5: Test Select All / Deselect All links present
  - [ ] Subtask 8.6: Test Import Selected button disabled by default
  - [ ] Subtask 8.7: Test form has CSRF token

## Dev Notes

### Architecture Patterns and Constraints

**UI Integration** (Architecture lines 213-230):
- Server-rendered Jinja2 template (no client-side framework needed)
- Use existing Bootstrap/CSS styling from employees list page
- Follow table structure patterns from existing templates
- Vanilla JavaScript for checkbox interactions (Story 3.4)

**Form Handling**:
- POST form submission to new route `/import-crossmark/import` (Story 3.5)
- CSRF protection via Flask-WTF: `{{ csrf_token() }}`
- Checkbox values submitted as array: `selected_employees[]`
- Store employee data in hidden inputs or data attributes for submission

**Performance Requirements** (PRD NFR-P3):
- Interface must remain responsive with up to 1000 employees
- Server-side rendering for 1000 rows should complete in < 2 seconds
- Consider pagination for 5000+ employees (future enhancement)

### Project Structure Notes

**Files to Create:**
- `app/templates/employees/import_select.html` - Selection interface template

**Files to Modify:**
- `app/routes/employees.py` - Update `/import-crossmark` route to render selection template

**Template Structure:**
```html
{% extends "base.html" %}
{% block content %}
<h2>{{ count }} new employees available to import</h2>
<div class="selection-controls">
  <a href="#" id="select-all">Select All</a> |
  <a href="#" id="deselect-all">Deselect All</a>
</div>
<form method="POST" action="{{ url_for('employees.import_crossmark_execute') }}">
  {{ csrf_token() }}
  <table class="table">
    <thead>
      <tr><th>Select</th><th>Name</th><th>Employee ID</th><th>MV Retail #</th></tr>
    </thead>
    <tbody>
      {% for employee in employees %}
      <tr>
        <td><input type="checkbox" class="employee-select" name="selected_employees[]" value="{{ employee.employeeId }}" data-name="{{ employee.title }}" data-rep-id="{{ employee.repId }}" /></td>
        <td>{{ employee.title }}</td>
        <td>{{ employee.employeeId }}</td>
        <td>{{ employee.repId }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  <button id="import-selected" type="submit" disabled>Import Selected</button>
</form>
{% endblock %}
```

**Dependencies:**
- Story 3.2: Route filters duplicates and passes new_employees to this template
- Story 1.3: CrossmarkEmployee Pydantic model defines employee data structure
- Story 3.4: JavaScript will be added for Select All/Deselect All functionality
- Story 3.5: Form submission route will be created

### Learnings from Previous Story

**From Story 3-2-duplicate-filtering-before-display (Status: drafted)**

- **new_employees Available**: Route `/import-crossmark` filters and returns List[CrossmarkEmployee]
- **Count Available**: len(new_employees) gives total count for heading
- **Zero-Import Handled**: If no new employees, redirect happens before this template
- **Next Step**: This story displays the filtered employees for selection

**From Story 3-1-crossmark-api-integration-for-employee-fetch (Status: drafted)**

- **CrossmarkEmployee Model**: Has fields: title (name), employeeId, repId, lastName, nameSort, etc.
- **Data Access**: `employee.title` for name, `employee.repId` for MV Retail #, `employee.employeeId` for Crossmark ID
- **Template Location**: `app/templates/employees/` directory for employee-related templates

**From Story 2-1-manual-employee-add-form-with-validation (Status: drafted)**

- **Form Pattern**: Use Flask-WTF for CSRF protection
- **Template Structure**: Extend base layout, use existing styling
- **Styling**: Follow Bootstrap or existing CSS framework patterns
- **Form Submission**: POST to dedicated route with CSRF token

**Integration Strategy:**
- This story creates the UI for employee selection
- Story 3.4 will add JavaScript for checkbox interactions
- Story 3.5 will handle form submission and bulk import
- Server-rendered approach (no client-side framework) keeps it simple

[Source: docs/sprint-artifacts/3-2-duplicate-filtering-before-display.md]
[Source: docs/sprint-artifacts/3-1-crossmark-api-integration-for-employee-fetch.md]
[Source: docs/sprint-artifacts/2-1-manual-employee-add-form-with-validation.md]

### References

- [Source: docs/epics.md#Story-3.3 (lines 463-500)] - Story definition and acceptance criteria
- [Source: docs/prd.md#Employee-Import-Crossmark-API (FR18-FR19, FR22)] - Selection interface requirements
- [Source: docs/architecture.md#UI-Integration (lines 213-230)] - Template and styling patterns
- [Flask-WTF CSRF Protection](https://flask-wtf.readthedocs.io/en/stable/csrf.html) - Form security

## Dev Agent Record

### Context Reference

Story context: docs/sprint-artifacts/3-3-*.context.xml

### Agent Model Used

<!-- Will be populated by dev agent -->

### Debug Log References

### Completion Notes List

### File List

## Change Log

| Date | Author | Change Description |
|------|--------|-------------------|
| 2025-11-21 | SM Agent (Elliot) | Initial story creation from Epic 3.3 - Selection interface with checkbox table |
