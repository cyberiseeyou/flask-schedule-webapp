document.addEventListener('DOMContentLoaded', function() {
    loadEmployees();
    initializeEmployeeForm();
    initializeTimeOffForm();
    loadTimeOffRequests();
});

function loadEmployees() {
    fetch('/api/employees')
        .then(response => response.json())
        .then(employees => {
            displayEmployees(employees);
        })
        .catch(error => {
            console.error('Error loading employees:', error);
            showStatus('Error loading employees', 'error');
        });
}

function displayEmployees(employees) {
    const grid = document.getElementById('employees-grid');
    
    if (employees.length === 0) {
        grid.innerHTML = '<p>No employees found. Use the form above to add employees.</p>';
        return;
    }
    
    grid.innerHTML = employees.map(emp => createEmployeeCard(emp)).join('');
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
    
    // Job title badge (only one, based on job_title)
    const jobTitleClass = getJobTitleBadgeClass(employee.job_title);
    badges.push(`<span class="employee-badge ${jobTitleClass}">${employee.job_title.toUpperCase()}</span>`);
    
    // Additional badges
    if (employee.adult_beverage_trained) badges.push('<span class="employee-badge badge-ab-trained">AB TRAINED</span>');
    if (!employee.is_active) badges.push('<span class="employee-badge badge-inactive">INACTIVE</span>');
    
    const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
    const dayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    
    const availabilityGrid = days.map((day, index) => {
        const isAvailable = employee.weekly_availability[day];
        const cellClass = isAvailable ? 'day-available' : 'day-unavailable';
        const status = isAvailable ? 'Y' : 'N';
        return `<div class="day-cell ${cellClass}">${status}</div>`;
    }).join('');
    
    return `
        <div class="employee-card" data-employee-id="${employee.id}">
            <div class="employee-header">
                <h3 class="employee-name">${employee.name}</h3>
                <div class="badges">${badges.join(' ')}</div>
            </div>
            
            <div class="employee-details">
                <p><strong>ID:</strong> ${employee.id}</p>
                <p><strong>Job Title:</strong> ${employee.job_title}</p>
                ${employee.email ? `<p><strong>Email:</strong> ${employee.email}</p>` : ''}
                ${employee.phone ? `<p><strong>Phone:</strong> ${employee.phone}</p>` : ''}
            </div>
            
            <div class="availability-section">
                <h4>Weekly Availability</h4>
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
            </div>
            
            <div class="employee-actions">
                <button class="btn btn-small btn-primary" onclick="editEmployee('${employee.id}')">Edit</button>
                <button class="btn btn-small btn-secondary" onclick="toggleEmployeeStatus('${employee.id}', ${!employee.is_active})">
                    ${employee.is_active ? 'Deactivate' : 'Activate'}
                </button>
                <button class="btn btn-small btn-danger" onclick="deleteEmployee('${employee.id}')">Delete</button>
            </div>
        </div>
    `;
}

function initializeEmployeeForm() {
    const form = document.getElementById('employee-form');
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = {
            id: document.getElementById('employee-id').value || null,
            name: document.getElementById('employee-name').value,
            email: document.getElementById('employee-email').value || null,
            phone: document.getElementById('employee-phone').value || null,
            is_supervisor: false, // Default to false since we removed the checkbox
            is_active: document.getElementById('is-active').checked,
            job_title: document.getElementById('job-title').value,
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
        
        // Check if we're editing an existing employee
        const editingEmployeeId = form.dataset.editingEmployeeId;
        if (editingEmployeeId) {
            formData.editing_employee_id = editingEmployeeId;
        }
        
        fetch('/api/employees', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showStatus(`Error: ${data.error}`, 'error');
            } else {
                const action = editingEmployeeId ? 'updated' : 'added';
                showStatus(`Employee ${action} successfully`, 'success');
                resetForm();
                loadEmployees(); // Refresh the grid
            }
        })
        .catch(error => {
            console.error('Error saving employee:', error);
            showStatus('Error saving employee', 'error');
        });
    });
    
    // Add reset button handler
    const resetBtn = form.querySelector('button[type="reset"]');
    resetBtn.addEventListener('click', function() {
        resetForm();
    });
}

function resetForm() {
    const form = document.getElementById('employee-form');
    form.reset();
    document.getElementById('is-active').checked = true; // Reset to default
    
    // Clear editing state
    delete form.dataset.editingEmployeeId;
    
    // Reset button text
    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.textContent = 'Add Employee';
}


function editEmployee(employeeId) {
    // Fetch current employee data
    fetch('/api/employees')
        .then(response => response.json())
        .then(employees => {
            const employee = employees.find(emp => emp.id === employeeId);
            if (!employee) {
                showStatus('Employee not found', 'error');
                return;
            }
            
            // Populate form with current employee data
            document.getElementById('employee-id').value = employee.id;
            document.getElementById('employee-name').value = employee.name;
            document.getElementById('employee-email').value = employee.email || '';
            document.getElementById('employee-phone').value = employee.phone || '';
            document.getElementById('is-active').checked = employee.is_active;
            document.getElementById('job-title').value = employee.job_title || 'Event Specialist';
            document.getElementById('adult-beverage-trained').checked = employee.adult_beverage_trained;
            
            // Set availability checkboxes
            const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
            days.forEach(day => {
                document.getElementById(`avail-${day}`).checked = employee.weekly_availability[day];
            });
            
            // Store the employee ID for updating
            const form = document.getElementById('employee-form');
            form.dataset.editingEmployeeId = employeeId;
            
            // Change form button text
            const submitBtn = form.querySelector('button[type="submit"]');
            submitBtn.textContent = 'Update Employee';
            
            // Scroll to form
            form.scrollIntoView({ behavior: 'smooth' });
            
            showStatus(`Editing ${employee.name} - modify the form and click Update`, 'success');
        })
        .catch(error => {
            console.error('Error fetching employee:', error);
            showStatus('Error loading employee data', 'error');
        });
}

function toggleEmployeeStatus(employeeId, newActiveStatus) {
    const action = newActiveStatus ? 'activate' : 'deactivate';
    
    if (!confirm(`Are you sure you want to ${action} this employee?`)) {
        return;
    }
    
    fetch('/api/employees', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            id: employeeId,
            is_active: newActiveStatus
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showStatus(`Error: ${data.error}`, 'error');
        } else {
            showStatus(`Employee ${action}d successfully`, 'success');
            loadEmployees(); // Refresh the grid
        }
    })
    .catch(error => {
        console.error(`Error ${action}ing employee:`, error);
        showStatus(`Error ${action}ing employee`, 'error');
    });
}

function deleteEmployee(employeeId) {
    // Get employee name for confirmation
    fetch('/api/employees')
        .then(response => response.json())
        .then(employees => {
            const employee = employees.find(emp => emp.id === employeeId);
            const employeeName = employee ? employee.name : employeeId;
            
            if (!confirm(`Are you sure you want to permanently DELETE ${employeeName}?\n\nThis action cannot be undone. If the employee has scheduled events, they cannot be deleted.`)) {
                return;
            }
            
            fetch(`/api/employees/${employeeId}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showStatus(`Error: ${data.error}`, 'error');
                } else {
                    showStatus(data.message, 'success');
                    loadEmployees(); // Refresh the grid
                }
            })
            .catch(error => {
                console.error('Error deleting employee:', error);
                showStatus('Error deleting employee', 'error');
            });
        })
        .catch(error => {
            console.error('Error fetching employee data:', error);
            showStatus('Error loading employee data', 'error');
        });
}

function showStatus(message, type) {
    // Create a temporary status message element
    const statusDiv = document.createElement('div');
    statusDiv.textContent = message;
    statusDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 10px 20px;
        border-radius: 4px;
        color: white;
        z-index: 1000;
        font-weight: bold;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        ${type === 'success' ? 'background-color: #28a745;' : 'background-color: #dc3545;'}
    `;
    
    document.body.appendChild(statusDiv);
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
        if (statusDiv.parentNode) {
            statusDiv.parentNode.removeChild(statusDiv);
        }
    }, 3000);
}

function initializeTimeOffForm() {
    // Populate employee dropdown
    fetch('/api/employees')
        .then(response => response.json())
        .then(employees => {
            const select = document.getElementById('time-off-employee');
            select.innerHTML = '<option value="">Select an employee</option>';
            
            employees.forEach(emp => {
                const option = document.createElement('option');
                option.value = emp.id;
                option.textContent = `${emp.name} (${emp.job_title})`;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading employees for time off:', error);
        });
    
    // Handle form submission
    const form = document.getElementById('time-off-form');
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const employeeId = document.getElementById('time-off-employee').value;
        const startDate = document.getElementById('time-off-start-date').value;
        const endDate = document.getElementById('time-off-end-date').value;
        const reason = document.getElementById('time-off-reason').value;
        
        if (!employeeId || !startDate || !endDate) {
            showStatus('Please fill in all required fields', 'error');
            return;
        }
        
        // Validate dates
        if (new Date(startDate) > new Date(endDate)) {
            showStatus('Start date cannot be after end date', 'error');
            return;
        }
        
        const timeOffData = {
            start_date: startDate,
            end_date: endDate,
            reason: reason
        };
        
        fetch(`/api/employees/${employeeId}/time_off`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(timeOffData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showStatus(`Error: ${data.error}`, 'error');
            } else {
                showStatus(data.message, 'success');
                form.reset();
                loadTimeOffRequests();
            }
        })
        .catch(error => {
            console.error('Error adding time off:', error);
            showStatus('Error adding time off request', 'error');
        });
    });
    
    // Sync end date with start date when start date changes
    document.getElementById('time-off-start-date').addEventListener('change', function() {
        const endDateInput = document.getElementById('time-off-end-date');
        if (!endDateInput.value || endDateInput.value < this.value) {
            endDateInput.value = this.value;
        }
    });
}

function loadTimeOffRequests() {
    Promise.all([
        fetch('/api/employees').then(r => r.json()),
        // Get all time off requests for all employees
        fetch('/api/employees').then(r => r.json()).then(employees => {
            return Promise.all(employees.map(emp => 
                fetch(`/api/employees/${emp.id}/time_off`).then(r => r.json()).then(timeOff => ({
                    employee: emp,
                    timeOff: timeOff
                }))
            ));
        })
    ])
    .then(([employees, employeeTimeOff]) => {
        const timeOffList = document.getElementById('time-off-list');
        const allTimeOff = [];
        
        employeeTimeOff.forEach(({ employee, timeOff }) => {
            timeOff.forEach(req => {
                allTimeOff.push({
                    ...req,
                    employeeName: employee.name,
                    employeeJobTitle: employee.job_title
                });
            });
        });
        
        if (allTimeOff.length === 0) {
            timeOffList.innerHTML = '<p style="color: #6c757d; text-align: center; padding: 20px;">No time off requests found.</p>';
            return;
        }
        
        // Sort by start date (most recent first)
        allTimeOff.sort((a, b) => new Date(b.start_date) - new Date(a.start_date));
        
        timeOffList.innerHTML = allTimeOff.map(req => createTimeOffCard(req)).join('');
    })
    .catch(error => {
        console.error('Error loading time off requests:', error);
        showStatus('Error loading time off requests', 'error');
    });
}

function createTimeOffCard(timeOffRequest) {
    // Parse dates properly to avoid timezone issues
    const startDate = new Date(timeOffRequest.start_date + 'T12:00:00').toLocaleDateString();
    const endDate = new Date(timeOffRequest.end_date + 'T12:00:00').toLocaleDateString();
    const dateRange = startDate === endDate ? startDate : `${startDate} - ${endDate}`;
    
    return `
        <div class="time-off-request">
            <div class="time-off-info">
                <div class="time-off-dates">${dateRange}</div>
                <div class="time-off-employee">${timeOffRequest.employeeName} (${timeOffRequest.employeeJobTitle})</div>
                ${timeOffRequest.reason ? `<div class="time-off-reason">${timeOffRequest.reason}</div>` : ''}
            </div>
            <div class="time-off-actions">
                <button class="btn-delete" onclick="deleteTimeOffRequest(${timeOffRequest.id})">Delete</button>
            </div>
        </div>
    `;
}

function deleteTimeOffRequest(timeOffId) {
    if (!confirm('Are you sure you want to delete this time off request?')) {
        return;
    }
    
    fetch(`/api/time_off/${timeOffId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showStatus(`Error: ${data.error}`, 'error');
        } else {
            showStatus(data.message, 'success');
            loadTimeOffRequests();
        }
    })
    .catch(error => {
        console.error('Error deleting time off request:', error);
        showStatus('Error deleting time off request', 'error');
    });
}