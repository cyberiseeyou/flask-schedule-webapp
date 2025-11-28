# Story 3.4: select-all-deselect-all-functionality

Status: ready-for-dev

## Story

As a **scheduling manager**,
I want **"Select All" and "Deselect All" shortcuts**,
so that **I can quickly select all employees for import without checking boxes individually**.

## Acceptance Criteria

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

## Tasks / Subtasks

- [ ] Task 1: Create employee import JavaScript file (AC: JavaScript module exists)
  - [ ] Subtask 1.1: Create file `app/static/js/employee_import.js`
  - [ ] Subtask 1.2: Add IIFE wrapper or ES6 module structure for encapsulation
  - [ ] Subtask 1.3: Add file header comment with description and dependencies
  - [ ] Subtask 1.4: Initialize on DOM ready: `document.addEventListener('DOMContentLoaded', init)`

- [ ] Task 2: Implement Select All functionality (AC: All checkboxes checked on click)
  - [ ] Subtask 2.1: Select "Select All" link: `document.getElementById('select-all')`
  - [ ] Subtask 2.2: Add click event listener with preventDefault
  - [ ] Subtask 2.3: Query all employee checkboxes: `document.querySelectorAll('input[type="checkbox"].employee-select')`
  - [ ] Subtask 2.4: Iterate checkboxes and set checked = true
  - [ ] Subtask 2.5: Call updateImportButton() after selection
  - [ ] Subtask 2.6: Prevent default link navigation: `event.preventDefault()`

- [ ] Task 3: Implement Deselect All functionality (AC: All checkboxes unchecked on click)
  - [ ] Subtask 3.1: Select "Deselect All" link: `document.getElementById('deselect-all')`
  - [ ] Subtask 3.2: Add click event listener with preventDefault
  - [ ] Subtask 3.3: Query all employee checkboxes: same selector as Select All
  - [ ] Subtask 3.4: Iterate checkboxes and set checked = false
  - [ ] Subtask 3.5: Call updateImportButton() after deselection
  - [ ] Subtask 3.6: Prevent default link navigation

- [ ] Task 4: Implement button state update logic (AC: Button updates with count)
  - [ ] Subtask 4.1: Create function updateImportButton()
  - [ ] Subtask 4.2: Query all checked checkboxes: `document.querySelectorAll('input[type="checkbox"].employee-select:checked')`
  - [ ] Subtask 4.3: Get count: `checkedBoxes.length`
  - [ ] Subtask 4.4: Select import button: `document.getElementById('import-selected')`
  - [ ] Subtask 4.5: If count === 0: disable button, set text to "Import Selected"
  - [ ] Subtask 4.6: If count > 0: enable button, set text to `Import Selected (${count})`
  - [ ] Subtask 4.7: Update button.disabled property
  - [ ] Subtask 4.8: Update button text content or innerHTML

- [ ] Task 5: Add individual checkbox change listeners (AC: Single checkbox updates button)
  - [ ] Subtask 5.1: Query all employee checkboxes
  - [ ] Subtask 5.2: Add 'change' event listener to each checkbox
  - [ ] Subtask 5.3: Event handler calls updateImportButton()
  - [ ] Subtask 5.4: Test single checkbox check updates count
  - [ ] Subtask 5.5: Test single checkbox uncheck updates count
  - [ ] Subtask 5.6: Ensure button disabled when count reaches 0

- [ ] Task 6: Include JavaScript file in template (AC: Script loaded on page)
  - [ ] Subtask 6.1: Open `app/templates/employees/import_select.html`
  - [ ] Subtask 6.2: Add script tag in template: `<script src="{{ url_for('static', filename='js/employee_import.js') }}"></script>`
  - [ ] Subtask 6.3: Place script at end of body or in scripts block
  - [ ] Subtask 6.4: Verify static file routing works: test script loads in browser
  - [ ] Subtask 6.5: Check browser console for JavaScript errors
  - [ ] Subtask 6.6: Test script executes on page load

- [ ] Task 7: Test all checkbox interactions (AC: All scenarios work correctly)
  - [ ] Subtask 7.1: Test Select All: all checkboxes checked, button enabled, count shown
  - [ ] Subtask 7.2: Test Deselect All: all checkboxes unchecked, button disabled, no count
  - [ ] Subtask 7.3: Test individual checkbox: button updates with correct count
  - [ ] Subtask 7.4: Test mixed interactions: Select All, uncheck one, verify count decreases
  - [ ] Subtask 7.5: Test edge case: 1 employee selected, deselect, verify button disabled
  - [ ] Subtask 7.6: Test with different browser engines (Chrome, Firefox, Safari if possible)

- [ ] Task 8: Optimize for large datasets (AC: Responsive with 1000 checkboxes)
  - [ ] Subtask 8.1: Test Select All/Deselect All with 1000+ checkboxes
  - [ ] Subtask 8.2: Verify operations complete in < 1 second (NFR-U2)
  - [ ] Subtask 8.3: Use efficient DOM queries (querySelectorAll once, cache results)
  - [ ] Subtask 8.4: Avoid N iterations for button update (single pass)
  - [ ] Subtask 8.5: Consider requestAnimationFrame for UI updates if needed
  - [ ] Subtask 8.6: Profile JavaScript performance with browser DevTools

## Dev Notes

### Architecture Patterns and Constraints

**UI Integration** (Architecture lines 213-230):
- Vanilla JavaScript (no jQuery or frameworks needed)
- Use modern DOM APIs: querySelector, querySelectorAll, addEventListener
- Follow existing JavaScript patterns in project
- Ensure compatibility with modern browsers (ES6+)

**Usability Requirements** (PRD NFR-U2):
- Select All/Deselect All must be intuitive and responsive
- Button state must update immediately (< 100ms perceived delay)
- Clear visual feedback: disabled state, button text changes
- Operations complete in < 1 second for 1000 employees

**Consistency Rules** (Architecture lines 451-465):
- Follow existing JavaScript naming conventions
- Use consistent event handling patterns
- Match existing button styling for disabled state

### Project Structure Notes

**Files to Create:**
- `app/static/js/employee_import.js` - Checkbox interaction logic

**Files to Modify:**
- `app/templates/employees/import_select.html` - Include JavaScript file

**JavaScript Structure:**
```javascript
// app/static/js/employee_import.js
(function() {
  'use strict';

  function updateImportButton() {
    const checkedBoxes = document.querySelectorAll('input[type="checkbox"].employee-select:checked');
    const count = checkedBoxes.length;
    const button = document.getElementById('import-selected');

    if (count === 0) {
      button.disabled = true;
      button.textContent = 'Import Selected';
    } else {
      button.disabled = false;
      button.textContent = `Import Selected (${count})`;
    }
  }

  function selectAll(event) {
    event.preventDefault();
    document.querySelectorAll('input[type="checkbox"].employee-select').forEach(cb => {
      cb.checked = true;
    });
    updateImportButton();
  }

  function deselectAll(event) {
    event.preventDefault();
    document.querySelectorAll('input[type="checkbox"].employee-select').forEach(cb => {
      cb.checked = false;
    });
    updateImportButton();
  }

  function init() {
    document.getElementById('select-all').addEventListener('click', selectAll);
    document.getElementById('deselect-all').addEventListener('click', deselectAll);

    document.querySelectorAll('input[type="checkbox"].employee-select').forEach(cb => {
      cb.addEventListener('change', updateImportButton);
    });

    // Initialize button state on page load
    updateImportButton();
  }

  document.addEventListener('DOMContentLoaded', init);
})();
```

**Dependencies:**
- Story 3.3: Template has checkboxes with class 'employee-select', Select All/Deselect All links, Import Selected button
- HTML element IDs: 'select-all', 'deselect-all', 'import-selected'
- Checkbox class: 'employee-select'

### Learnings from Previous Story

**From Story 3-3-selection-interface-with-checkbox-table (Status: drafted)**

- **Template Created**: `app/templates/employees/import_select.html` has table with checkboxes
- **Checkbox Class**: All checkboxes have class 'employee-select'
- **Link IDs**: 'select-all' and 'deselect-all' links exist
- **Button ID**: 'import-selected' button exists, initially disabled
- **Button State**: Button should be disabled when count === 0

**From Story 3-2-duplicate-filtering-before-display (Status: drafted)**

- **Employee Count**: Template receives count variable with total new employees
- **Data Available**: Each checkbox has employee data in data attributes
- **Performance**: Interface designed for up to 1000 employees

**From Story 2-1-manual-employee-add-form-with-validation (Status: drafted)**

- **JavaScript Location**: Static files in `app/static/js/`
- **Template Include**: Use `{{ url_for('static', filename='...') }}` for script tags
- **Existing Patterns**: Review existing JavaScript files for coding style

**Integration Strategy:**
- This story adds client-side interactivity to Story 3.3 template
- No server-side changes needed - pure JavaScript
- Story 3.5 will handle form submission when button is clicked
- Keep JavaScript simple and dependency-free

[Source: docs/sprint-artifacts/3-3-selection-interface-with-checkbox-table.md]
[Source: docs/sprint-artifacts/3-2-duplicate-filtering-before-display.md]
[Source: docs/sprint-artifacts/2-1-manual-employee-add-form-with-validation.md]

### References

- [Source: docs/epics.md#Story-3.4 (lines 502-539)] - Story definition and acceptance criteria
- [Source: docs/prd.md#Employee-Import-Crossmark-API (FR20-FR21, FR23-FR24, NFR-U2)] - Select All functionality requirements
- [Source: docs/architecture.md#UI-Integration (lines 213-230)] - JavaScript patterns and conventions
- [MDN: querySelectorAll](https://developer.mozilla.org/en-US/docs/Web/API/Document/querySelectorAll) - DOM API reference

## Dev Agent Record

### Context Reference

Story context: docs/sprint-artifacts/3-4-*.context.xml

### Agent Model Used

<!-- Will be populated by dev agent -->

### Debug Log References

### Completion Notes List

### File List

## Change Log

| Date | Author | Change Description |
|------|--------|-------------------|
| 2025-11-21 | SM Agent (Elliot) | Initial story creation from Epic 3.4 - Select All/Deselect All functionality |
