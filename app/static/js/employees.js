// Employee Management - Redesigned with MVRetail Integration

document.addEventListener('DOMContentLoaded', function() {
    loadEmployees();
    setupModalHandlers();
});

// ========================================
// Load and Display Employees
// ========================================

function loadEmployees() {
    const grid = document.getElementById('employees-grid');
    grid.innerHTML = '<div class="loading">Loading employees</div>';

    fetch('/api/employees')
        .then(response => response.json())
        .then(employees => {
            renderEmployees(employees);
        })
        .catch(error => {
            console.error('Error loading employees:', error);
            grid.innerHTML = '<div class="alert alert-error">Error loading employees. Please refresh the page.</div>';
        });
}

function renderEmployees(employees) {
    const grid = document.getElementById('employees-grid');

    if (employees.length === 0) {
        grid.innerHTML = '<p style="color: #6c757d; text-align: center; padding: 40px;">No employees found. Click "Add Employee" to get started.</p>';
        updateStatistics(employees);
        return;
    }

    grid.innerHTML = employees.map(emp => createEmployeeCard(emp)).join('');
    updateStatistics(employees);
}

function updateStatistics(employees) {
    // Calculate statistics
    const totalEmployees = employees.length;
    const juicers = employees.filter(emp => emp.job_title === 'Juicer Barista').length;
    const eventSpecialists = employees.filter(emp => emp.job_title === 'Event Specialist').length;
    const leadSpecialists = employees.filter(emp => emp.job_title === 'Lead Event Specialist').length;
    const abTrained = employees.filter(emp => emp.adult_beverage_trained).length;

    // Update DOM
    document.getElementById('stat-total').textContent = totalEmployees;
    document.getElementById('stat-juicers').textContent = juicers;
    document.getElementById('stat-es').textContent = eventSpecialists;
    document.getElementById('stat-leads').textContent = leadSpecialists;
    document.getElementById('stat-ab').textContent = abTrained;
}

function getJobTitleBadgeClass(jobTitle) {
    const jobTitleMap = {
        'Lead Event Specialist': 'badge-lead-event-specialist',
        'Club Supervisor': 'badge-club-supervisor',
        'Juicer Barista': 'badge-juicer-barista',
        'Event Specialist': 'badge-event-specialist'
    };
    return jobTitleMap[jobTitle] || 'badge-event-specialist';
}

function createEmployeeCard(employee) {
    const badges = [];

    // Job title badge
    const jobTitleClass = getJobTitleBadgeClass(employee.job_title);
    badges.push(`<span class="employee-badge ${jobTitleClass}">${employee.job_title.toUpperCase()}</span>`);

    // Additional badges
    if (employee.adult_beverage_trained) {
        badges.push('<span class="employee-badge badge-ab-trained">AB TRAINED</span>');
    }
    if (!employee.is_active) {
        badges.push('<span class="employee-badge badge-inactive">INACTIVE</span>');
    }

    const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
    const availabilityGrid = days.map(day => {
        const isAvailable = employee.weekly_availability[day];
        const cellClass = isAvailable ? 'day-available' : 'day-unavailable';
        const status = isAvailable ? 'Y' : 'N';
        return `<div class="day-cell ${cellClass}">${status}</div>`;
    }).join('');

    return `
        <div class="employee-card" data-employee-id="${employee.id}">
            <div class="employee-header">
                <div>
                    <h3 class="employee-name">${employee.name}</h3>
                    ${employee.id ? `<div class="employee-id">ID: ${employee.id}</div>` : ''}
                </div>
                <div>${badges.join(' ')}</div>
            </div>

            ${employee.email || employee.phone ? `
            <div style="margin: 10px 0; font-size: 14px; color: #6c757d;">
                ${employee.email ? `<div>📧 ${employee.email}</div>` : ''}
                ${employee.phone ? `<div>📞 ${employee.phone}</div>` : ''}
            </div>
            ` : ''}

            <h4 style="margin-top: 15px; margin-bottom: 10px; color: var(--primary-color); font-size: 14px;">Weekly Availability</h4>
            <div class="availability-grid">
                <div class="day-cell day-header">Mon</div>
                <div class="day-cell day-header">Tue</div>
                <div class="day-cell day-header">Wed</div>
                <div class="day-cell day-header">Thu</div>
                <div class="day-cell day-header">Fri</div>
                <div class="day-cell day-header">Sat</div>
                <div class="day-cell day-header">Sun</div>
                ${availabilityGrid}
            </div>

            <div class="employee-actions">
                <div class="employee-actions-left">
                    <button type="button" class="btn btn-small btn-primary" onclick="editEmployee('${employee.id}')">Edit</button>
                    <button type="button" class="btn btn-small btn-secondary" onclick="toggleEmployeeStatus('${employee.id}', ${!employee.is_active})">
                        ${employee.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                    <button type="button" class="btn btn-small btn-danger" onclick="deleteEmployee('${employee.id}')">Delete</button>
                </div>
            </div>
        </div>
    `;
}

// ========================================
// Modal Handlers
// ========================================

function setupModalHandlers() {
    // Add Employee button
    document.getElementById('add-employee-btn').addEventListener('click', openAddEmployeeModal);

    // Import Employees button
    document.getElementById('import-employees-btn').addEventListener('click', openImportEmployeesModal);

    // Add Employee form submission
    document.getElementById('add-employee-form').addEventListener('submit', handleAddEmployeeSubmit);

    // Close modal when clicking outside
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeAddEmployeeModal();
                closeImportEmployeesModal();
            }
        });
    });
}

// ========================================
// Add Employee Modal
// ========================================

function openAddEmployeeModal() {
    document.getElementById('add-employee-modal').classList.add('modal-open');
    document.getElementById('modal-alerts').innerHTML = '';

    // Reset form if not editing
    const form = document.getElementById('add-employee-form');
    if (!form.dataset.editingEmployeeId) {
        form.reset();
        document.getElementById('is-active').checked = true;

        // Check all availability by default
        ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].forEach(day => {
            document.getElementById(`avail-${day}`).checked = true;
        });

        // Set modal title to "Add New Employee"
        document.querySelector('#add-employee-modal .modal-header h2').textContent = 'Add New Employee';
    }
}

function closeAddEmployeeModal() {
    document.getElementById('add-employee-modal').classList.remove('modal-open');
    const form = document.getElementById('add-employee-form');
    delete form.dataset.editingEmployeeId;
    form.reset();
}

async function handleAddEmployeeSubmit(e) {
    e.preventDefault();

    const form = e.target;
    const modalAlerts = document.getElementById('modal-alerts');
    modalAlerts.innerHTML = '';

    const employeeIdInput = document.getElementById('employee-id').value.trim();
    const employeeName = document.getElementById('employee-name').value.trim();

    if (!employeeName) {
        showModalAlert('Employee name is required', 'error');
        return;
    }

    const formData = {
        id: employeeIdInput || null,
        name: employeeName,
        email: document.getElementById('employee-email').value.trim() || null,
        phone: document.getElementById('employee-phone').value.trim() || null,
        job_title: document.getElementById('job-title').value,
        is_active: document.getElementById('is-active').checked,
        adult_beverage_trained: document.getElementById('adult-beverage-trained').checked,
        weekly_availability: {
            monday: document.getElementById('avail-monday').checked,
            tuesday: document.getElementById('avail-tuesday').checked,
            wednesday: document.getElementById('avail-wednesday').checked,
            thursday: document.getElementById('avail-thursday').checked,
            friday: document.getElementById('avail-friday').checked,
            saturday: document.getElementById('avail-saturday').checked,
            sunday: document.getElementById('avail-sunday').checked
        }
    };

    // Check if editing
    const editingEmployeeId = form.dataset.editingEmployeeId;
    if (editingEmployeeId) {
        formData.editing_employee_id = editingEmployeeId;
    }

    try {
        const response = await fetch('/api/employees', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (data.error) {
            showModalAlert(`Error: ${data.error}`, 'error');
            return;
        }

        // Close modal immediately
        closeAddEmployeeModal();

        // Success! Show success message
        const savedEmployeeId = data.employee_id || editingEmployeeId;
        showFlashMessage(`Employee ${editingEmployeeId ? 'updated' : 'saved'} successfully`, 'success');

        // Lookup employee in MVRetail system
        showFlashMessage('Looking up scheduling ID from MVRetail...', 'info');
        await lookupEmployeeExternalId(savedEmployeeId, employeeName, employeeIdInput);

        // Reload employees list
        loadEmployees();

    } catch (error) {
        console.error('Error saving employee:', error);
        showModalAlert('Error saving employee. Please try again.', 'error');
    }
}

async function lookupEmployeeExternalId(employeeId, employeeName, employeeIdInput) {
    try {
        const response = await fetch('/api/lookup_employee_id', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                employee_id: employeeId,
                name: employeeName,
                crossmark_id: employeeIdInput
            })
        });

        const result = await response.json();

        if (result.found) {
            showFlashMessage(`Found in MVRetail! Scheduling ID: ${result.external_id}`, 'success');
        } else {
            showFlashMessage(`Employee not found in MVRetail system - cannot be scheduled until added to MVRetail`, 'warning');
        }

    } catch (error) {
        console.error('Error looking up employee external ID:', error);
        showFlashMessage('Could not verify employee in MVRetail system', 'warning');
    }
}

// ========================================
// Import Employees Modal
// ========================================

async function openImportEmployeesModal() {
    const modal = document.getElementById('import-employees-modal');
    const list = document.getElementById('import-employee-list');
    const alerts = document.getElementById('import-modal-alerts');

    modal.classList.add('modal-open');
    alerts.innerHTML = '';
    list.innerHTML = '<div class="loading">Loading available employees from MVRetail</div>';

    try {
        const response = await fetch('/api/get_available_reps');
        const data = await response.json();

        if (data.error) {
            list.innerHTML = `<div class="alert alert-error">${data.error}</div>`;
            return;
        }

        if (!data.representatives || data.representatives.length === 0) {
            list.innerHTML = '<div class="alert alert-info">No employees found in MVRetail system.</div>';
            return;
        }

        renderImportEmployeeList(data.representatives);

    } catch (error) {
        console.error('Error loading MVRetail employees:', error);
        list.innerHTML = '<div class="alert alert-error">Error loading employees from MVRetail. Please try again.</div>';
    }
}

function closeImportEmployeesModal() {
    document.getElementById('import-employees-modal').classList.remove('modal-open');
}

function renderImportEmployeeList(representatives) {
    const list = document.getElementById('import-employee-list');

    list.innerHTML = representatives.map(rep => `
        <div class="import-employee-item">
            <input type="checkbox" id="import-rep-${rep.id}" value="${rep.id}" data-rep='${JSON.stringify(rep)}'>
            <div class="import-employee-info">
                <div class="import-employee-name">${rep.name}</div>
                <div class="import-employee-id">ID: ${rep.id}</div>
                ${rep.email ? `<div style="font-size: 12px; color: #6c757d;">📧 ${rep.email}</div>` : ''}
            </div>
        </div>
    `).join('');
}

function selectAllImportEmployees() {
    document.querySelectorAll('#import-employee-list input[type="checkbox"]').forEach(cb => {
        cb.checked = true;
    });
}

function deselectAllImportEmployees() {
    document.querySelectorAll('#import-employee-list input[type="checkbox"]').forEach(cb => {
        cb.checked = false;
    });
}

async function importSelectedEmployees() {
    const checkboxes = document.querySelectorAll('#import-employee-list input[type="checkbox"]:checked');

    if (checkboxes.length === 0) {
        showImportAlert('Please select at least one employee to import', 'warning');
        return;
    }

    const selectedReps = Array.from(checkboxes).map(cb => JSON.parse(cb.dataset.rep));

    showImportAlert(`Importing ${selectedReps.length} employee(s)...`, 'info');

    try {
        const response = await fetch('/api/import_employees', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ employees: selectedReps })
        });

        const data = await response.json();

        if (data.error) {
            showImportAlert(`Error: ${data.error}`, 'error');
            return;
        }

        const message = `Successfully imported ${data.imported} employee(s). Updated ${data.updated} existing employee(s).`;
        showImportAlert(message, 'success');

        // Close modal and reload after short delay
        setTimeout(() => {
            closeImportEmployeesModal();
            loadEmployees();
            showFlashMessage(message, 'success');
        }, 2000);

    } catch (error) {
        console.error('Error importing employees:', error);
        showImportAlert('Error importing employees. Please try again.', 'error');
    }
}

// ========================================
// Edit Employee
// ========================================

async function editEmployee(employeeId) {
    try {
        const response = await fetch('/api/employees');
        const employees = await response.json();
        const employee = employees.find(emp => emp.id === employeeId);

        if (!employee) {
            showFlashMessage('Employee not found', 'error');
            return;
        }

        // Populate form
        document.getElementById('employee-id').value = employee.id || '';
        document.getElementById('employee-name').value = employee.name;
        document.getElementById('employee-email').value = employee.email || '';
        document.getElementById('employee-phone').value = employee.phone || '';
        document.getElementById('job-title').value = employee.job_title;
        document.getElementById('is-active').checked = employee.is_active;
        document.getElementById('adult-beverage-trained').checked = employee.adult_beverage_trained;

        // Set availability
        ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].forEach(day => {
            document.getElementById(`avail-${day}`).checked = employee.weekly_availability[day];
        });

        // Set editing mode
        const form = document.getElementById('add-employee-form');
        form.dataset.editingEmployeeId = employeeId;

        // Update modal title
        document.querySelector('#add-employee-modal .modal-header h2').textContent = `Editing ${employee.name}`;

        // Open modal
        openAddEmployeeModal();

    } catch (error) {
        console.error('Error loading employee for edit:', error);
        showFlashMessage('Error loading employee data', 'error');
    }
}

// ========================================
// Toggle Employee Status
// ========================================

async function toggleEmployeeStatus(employeeId, newActiveStatus) {
    const action = newActiveStatus ? 'activate' : 'deactivate';

    if (!confirm(`Are you sure you want to ${action} this employee?`)) {
        return;
    }

    try {
        const response = await fetch('/api/employees', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                id: employeeId,
                is_active: newActiveStatus
            })
        });

        const data = await response.json();

        if (data.error) {
            showFlashMessage(`Error: ${data.error}`, 'error');
        } else {
            showFlashMessage(`Employee ${action}d successfully`, 'success');
            loadEmployees();
        }

    } catch (error) {
        console.error(`Error ${action}ing employee:`, error);
        showFlashMessage(`Error ${action}ing employee`, 'error');
    }
}

// ========================================
// Delete Employee
// ========================================

async function deleteEmployee(employeeId) {
    try {
        const response = await fetch('/api/employees');
        const employees = await response.json();
        const employee = employees.find(emp => emp.id === employeeId);
        const employeeName = employee ? employee.name : employeeId;

        if (!confirm(`Are you sure you want to permanently DELETE ${employeeName}?\n\nThis action cannot be undone.`)) {
            return;
        }

        const deleteResponse = await fetch(`/api/employees/${employeeId}`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        });

        const data = await deleteResponse.json();

        if (data.error) {
            showFlashMessage(`Error: ${data.error}`, 'error');
        } else {
            showFlashMessage(data.message, 'success');
            loadEmployees();
        }

    } catch (error) {
        console.error('Error deleting employee:', error);
        showFlashMessage('Error deleting employee', 'error');
    }
}

// ========================================
// Alert/Message Functions
// ========================================

function showModalAlert(message, type) {
    const alerts = document.getElementById('modal-alerts');
    alerts.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
}

function showImportAlert(message, type) {
    const alerts = document.getElementById('import-modal-alerts');
    alerts.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
}

function showFlashMessage(message, type) {
    const flashContainer = document.getElementById('flash-messages');
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    flashContainer.appendChild(alertDiv);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

