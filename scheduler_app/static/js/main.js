document.addEventListener('DOMContentLoaded', function() {
    // Initialize import/export functionality if on dashboard
    initializeImportExport();
    
    // Initialize date constraints if on scheduling page
    if (window.eventData) {
        initializeDateConstraints();
        initializeFormValidation();
        initializeTimeRestrictions();
    }
});

function initializeImportExport() {
    const importBtn = document.getElementById('import-btn');
    const importFile = document.getElementById('import-file');
    const importScheduledBtn = document.getElementById('import-scheduled-btn');
    const importScheduledFile = document.getElementById('import-scheduled-file');
    const importStatus = document.getElementById('import-status');
    
    if (!importBtn || !importFile || !importStatus) {
        return; // Not on dashboard page
    }
    
    // Import events button click handler
    importBtn.addEventListener('click', function() {
        importFile.click();
    });
    
    // Import scheduled events button click handler
    if (importScheduledBtn && importScheduledFile) {
        importScheduledBtn.addEventListener('click', function() {
            importScheduledFile.click();
        });
        
        // Scheduled file selection handler
        importScheduledFile.addEventListener('change', function() {
            handleFileImport(this.files[0], '/api/import/scheduled', importScheduledBtn, 'Import Scheduled');
        });
    }
    
    // File selection handler for regular events
    importFile.addEventListener('change', function() {
        handleFileImport(this.files[0], '/api/import/events', importBtn, 'Import Events');
    });
}

function handleFileImport(file, apiUrl, button, buttonText) {
    if (!file) {
        return;
    }
    
    // Validate file type
    if (!file.name.toLowerCase().endsWith('.csv')) {
        showImportStatus('Error: Please select a CSV file', 'error');
        return;
    }
    
    // Show loading state
    button.disabled = true;
    button.textContent = 'Importing...';
    showImportStatus('Uploading file...', 'loading');
    
    // Create form data
    const formData = new FormData();
    formData.append('file', file);
    
    // Upload file
    fetch(apiUrl, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showImportStatus(`Error: ${data.error}`, 'error');
        } else {
            showImportStatus(`Success: ${data.message}`, 'success');
            // Refresh the page to show new events
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        }
    })
    .catch(error => {
        console.error('Import error:', error);
        showImportStatus('Error: Failed to import file', 'error');
    })
    .finally(() => {
        // Reset button state
        button.disabled = false;
        button.textContent = buttonText;
        // Clear file input
        if (apiUrl.includes('scheduled')) {
            document.getElementById('import-scheduled-file').value = '';
        } else {
            document.getElementById('import-file').value = '';
        }
    });
}

function showImportStatus(message, type) {
    const importStatus = document.getElementById('import-status');
    if (!importStatus) {
        return;
    }
    
    importStatus.textContent = message;
    importStatus.className = `import-status ${type}`;
    
    // Auto-hide success/error messages after 5 seconds
    if (type === 'success' || type === 'error') {
        setTimeout(() => {
            importStatus.textContent = '';
            importStatus.className = 'import-status';
        }, 5000);
    }
}

function initializeDateConstraints() {
    const dateInput = document.getElementById('scheduled_date');
    const submitButton = document.querySelector('.btn-primary');
    
    if (!dateInput || !submitButton) {
        return;
    }
    
    // Set min and max date constraints
    dateInput.min = window.eventData.startDate;
    dateInput.max = window.eventData.endDate;
    
    // Add change event listener to validate date and fetch employees
    dateInput.addEventListener('change', function() {
        validateDateSelection(this.value, submitButton);
        if (this.value) {
            fetchAvailableEmployees(this.value);
        }
    });
    
    // Add input event listener for real-time validation
    dateInput.addEventListener('input', function() {
        validateDateSelection(this.value, submitButton);
    });
}

function initializeFormValidation() {
    const employeeSelect = document.getElementById('employee_id');
    const startTimeInput = document.getElementById('start_time');
    const startTimeDropdown = document.getElementById('start_time_dropdown');
    const form = document.getElementById('scheduling-form');
    
    if (employeeSelect) {
        employeeSelect.addEventListener('change', function() {
            validateForm();
        });
    }
    
    if (startTimeInput) {
        startTimeInput.addEventListener('change', function() {
            validateForm();
        });
    }
    
    // Handle form submission to use the correct time value
    if (form) {
        form.addEventListener('submit', function(e) {
            // If dropdown is visible and has a value, copy it to the hidden time input
            if (startTimeDropdown && startTimeDropdown.style.display !== 'none' && startTimeDropdown.value) {
                startTimeInput.value = startTimeDropdown.value;
            }
        });
    }
}

function validateDateSelection(selectedDate, submitButton) {
    if (!selectedDate || !window.eventData) {
        submitButton.disabled = true;
        return;
    }
    
    const selected = new Date(selectedDate);
    const startDate = new Date(window.eventData.startDate);
    const endDate = new Date(window.eventData.endDate);
    
    // Check if selected date is within valid range
    const isValidDate = selected >= startDate && selected <= endDate;
    
    // Add visual feedback
    const dateInput = document.getElementById('scheduled_date');
    if (isValidDate) {
        dateInput.style.borderColor = '#28a745';
    } else {
        dateInput.style.borderColor = '#dc3545';
    }
    
    // Validate entire form
    validateForm();
}

function fetchAvailableEmployees(date) {
    const employeeSelect = document.getElementById('employee_id');
    const loadingSpinner = document.getElementById('employee-loading');
    
    if (!employeeSelect || !loadingSpinner) {
        return;
    }
    
    // Show loading state
    loadingSpinner.style.display = 'block';
    employeeSelect.disabled = true;
    employeeSelect.innerHTML = '<option value="">Loading...</option>';
    
    // Make AJAX call to availability API with event ID for role-based filtering
    const eventId = window.eventData ? window.eventData.id : null;
    const apiUrl = eventId ? `/api/available_employees/${date}/${eventId}` : `/api/available_employees/${date}`;
    
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(employees => {
            // Hide loading state
            loadingSpinner.style.display = 'none';
            employeeSelect.disabled = false;
            
            // Populate dropdown with employees
            if (employees.length === 0) {
                employeeSelect.innerHTML = '<option value="">No employees available</option>';
            } else {
                employeeSelect.innerHTML = '<option value="">Select an employee</option>';
                employees.forEach(employee => {
                    const option = document.createElement('option');
                    option.value = employee.id;
                    option.textContent = `${employee.name} (${employee.job_title})`;
                    employeeSelect.appendChild(option);
                });
            }
            
            // Validate form after loading employees
            validateForm();
        })
        .catch(error => {
            console.error('Error fetching available employees:', error);
            
            // Hide loading state and show error
            loadingSpinner.style.display = 'none';
            employeeSelect.disabled = false;
            employeeSelect.innerHTML = '<option value="">Error loading employees</option>';
            
            // Validate form
            validateForm();
        });
}

function validateForm() {
    const dateInput = document.getElementById('scheduled_date');
    const employeeSelect = document.getElementById('employee_id');
    const startTimeInput = document.getElementById('start_time');
    const startTimeDropdown = document.getElementById('start_time_dropdown');
    const submitButton = document.querySelector('.btn-primary');

    if (!dateInput || !employeeSelect || !submitButton) {
        return;
    }

    // Check if all required fields are filled
    const dateValid = dateInput.value && isValidDate(dateInput.value);
    const employeeValid = employeeSelect.value && employeeSelect.value !== '';

    // Check time validity based on which input is active
    let timeValid = false;
    if (startTimeDropdown && startTimeDropdown.style.display !== 'none' && startTimeDropdown.required) {
        timeValid = startTimeDropdown.value && startTimeDropdown.value !== '';
    } else if (startTimeInput && startTimeInput.style.display !== 'none' && startTimeInput.required) {
        timeValid = startTimeInput.value && startTimeInput.value !== '';
    }

    // Enable submit button only if all fields are valid
    submitButton.disabled = !(dateValid && employeeValid && timeValid);

    // Check for conflicts if all fields are valid
    if (dateValid && employeeValid && timeValid) {
        checkSchedulingConflicts();
    }
}

function checkSchedulingConflicts() {
    const dateInput = document.getElementById('scheduled_date');
    const employeeSelect = document.getElementById('employee_id');
    const startTimeInput = document.getElementById('start_time');
    const startTimeDropdown = document.getElementById('start_time_dropdown');

    if (!dateInput || !employeeSelect) {
        return;
    }

    const employeeId = employeeSelect.value;
    const scheduledDate = dateInput.value;

    // Get time from appropriate input
    let scheduledTime;
    if (startTimeDropdown && startTimeDropdown.style.display !== 'none' && startTimeDropdown.value) {
        scheduledTime = startTimeDropdown.value;
    } else if (startTimeInput && startTimeInput.value) {
        scheduledTime = startTimeInput.value;
    } else {
        return; // No time selected yet
    }

    // Get event info from page
    const eventData = window.eventData || {};
    const eventId = eventData.id;
    const eventType = eventData.eventType;

    // Call conflict detection API
    fetch('/api/check_conflicts', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            employee_id: employeeId,
            scheduled_date: scheduledDate,
            scheduled_time: scheduledTime,
            event_id: eventId,
            event_type: eventType
        })
    })
    .then(response => response.json())
    .then(data => {
        displayConflictWarnings(data);
    })
    .catch(error => {
        console.error('Error checking conflicts:', error);
    });
}

function displayConflictWarnings(conflictData) {
    // Remove any existing conflict warnings
    const existingWarnings = document.getElementById('conflict-warnings');
    if (existingWarnings) {
        existingWarnings.remove();
    }

    if (!conflictData.has_conflicts && !conflictData.has_warnings) {
        return; // No issues to display
    }

    // Create warnings container
    const warningsContainer = document.createElement('div');
    warningsContainer.id = 'conflict-warnings';
    warningsContainer.style.cssText = `
        margin: var(--spacing-md) 0;
        padding: var(--spacing-md);
        border-radius: var(--border-radius-md);
        background: ${conflictData.has_conflicts ? 'rgba(220, 53, 69, 0.1)' : 'rgba(255, 193, 7, 0.1)'};
        border: 2px solid ${conflictData.has_conflicts ? '#dc3545' : '#ffc107'};
    `;

    // Add header
    const header = document.createElement('div');
    header.style.cssText = `
        font-weight: bold;
        margin-bottom: var(--spacing-sm);
        color: ${conflictData.has_conflicts ? '#dc3545' : '#cc8800'};
        font-size: 16px;
    `;
    header.textContent = conflictData.has_conflicts
        ? '⚠️ Scheduling Conflicts Detected'
        : '⚡ Scheduling Warnings';
    warningsContainer.appendChild(header);

    // Display conflicts
    if (conflictData.conflicts && conflictData.conflicts.length > 0) {
        conflictData.conflicts.forEach(conflict => {
            const conflictDiv = document.createElement('div');
            conflictDiv.style.cssText = `
                margin-bottom: var(--spacing-sm);
                padding: var(--spacing-sm);
                background: white;
                border-radius: var(--border-radius-sm);
                border-left: 4px solid #dc3545;
            `;
            conflictDiv.innerHTML = `
                <div style="font-weight: bold; color: #dc3545; margin-bottom: 4px;">
                    🚫 ${conflict.message}
                </div>
                <div style="font-size: 13px; color: #666;">
                    ${conflict.detail}
                </div>
            `;
            warningsContainer.appendChild(conflictDiv);
        });
    }

    // Display warnings
    if (conflictData.warnings && conflictData.warnings.length > 0) {
        conflictData.warnings.forEach(warning => {
            const warningDiv = document.createElement('div');
            warningDiv.style.cssText = `
                margin-bottom: var(--spacing-sm);
                padding: var(--spacing-sm);
                background: white;
                border-radius: var(--border-radius-sm);
                border-left: 4px solid #ffc107;
            `;
            warningDiv.innerHTML = `
                <div style="font-weight: bold; color: #cc8800; margin-bottom: 4px;">
                    ⚠️ ${warning.message}
                </div>
                <div style="font-size: 13px; color: #666;">
                    ${warning.detail}
                </div>
            `;
            warningsContainer.appendChild(warningDiv);
        });
    }

    // Add action message
    const actionMessage = document.createElement('div');
    actionMessage.style.cssText = `
        margin-top: var(--spacing-sm);
        padding-top: var(--spacing-sm);
        border-top: 1px solid rgba(0,0,0,0.1);
        font-size: 13px;
        font-style: italic;
        color: #666;
    `;
    actionMessage.textContent = conflictData.can_proceed
        ? 'You can proceed but please review the warnings above.'
        : 'Please resolve the conflicts before scheduling this event.';
    warningsContainer.appendChild(actionMessage);

    // Insert warnings before submit button
    const submitButton = document.querySelector('.btn-primary');
    if (submitButton && submitButton.parentElement) {
        submitButton.parentElement.insertBefore(warningsContainer, submitButton);
    } else {
        // Fallback: insert after employee select
        const employeeSelect = document.getElementById('employee_id');
        if (employeeSelect && employeeSelect.parentElement) {
            employeeSelect.parentElement.insertAdjacentElement('afterend', warningsContainer);
        }
    }

    // Disable submit if there are conflicts (not just warnings)
    if (conflictData.has_conflicts && submitButton) {
        submitButton.disabled = true;
        submitButton.title = 'Please resolve conflicts before scheduling';
    }
}

function isValidDate(selectedDate) {
    if (!selectedDate || !window.eventData) {
        return false;
    }
    
    const selected = new Date(selectedDate);
    const startDate = new Date(window.eventData.startDate);
    const endDate = new Date(window.eventData.endDate);
    
    return selected >= startDate && selected <= endDate;
}

function initializeTimeRestrictions() {
    const timeInput = document.getElementById('start_time');
    const timeDropdown = document.getElementById('start_time_dropdown');
    
    if (!timeInput || !timeDropdown || !window.eventData.eventType) {
        return;
    }
    
    const eventType = window.eventData.eventType;
    
    // Define time options for each event type
    const timeRestrictions = {
        'Core': ['09:45', '10:30', '11:00', '11:30'],
        'Supervisor': ['12:00'],
        'Freeosk': ['09:00', '12:00'],
        'Digitals': ['09:15', '09:30', '09:45', '10:00']
    };
    
    // Check if this event type has time restrictions
    if (timeRestrictions[eventType]) {
        // Hide time input, show dropdown
        timeInput.style.display = 'none';
        timeInput.required = false;
        timeDropdown.style.display = 'block';
        timeDropdown.required = true;
        
        // Populate dropdown with allowed times
        timeDropdown.innerHTML = '<option value="">Select a time</option>';
        timeRestrictions[eventType].forEach(time => {
            const option = document.createElement('option');
            option.value = time;
            option.textContent = formatTime(time);
            timeDropdown.appendChild(option);
        });
        
        // Set default value for Freeosk events
        if (eventType === 'Freeosk') {
            timeDropdown.value = '09:00';
        }
        
        // Add change event listener for validation
        timeDropdown.addEventListener('change', function() {
            validateForm();
        });
    } else {
        // Show time input, hide dropdown (for Other events)
        timeInput.style.display = 'block';
        timeInput.required = true;
        timeDropdown.style.display = 'none';
        timeDropdown.required = false;
    }
}

function formatTime(time24) {
    // Convert 24-hour time to 12-hour format for display
    const [hours, minutes] = time24.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour;
    return `${displayHour}:${minutes} ${ampm}`;
}

// Export validation functions
function validateAndExport() {
    const exportBtn = document.getElementById('export-btn');
    if (!exportBtn) return;
    
    // Show loading state
    exportBtn.disabled = true;
    exportBtn.textContent = 'Validating...';
    
    // Call validation API
    fetch('/api/validate_schedule_for_export')
        .then(response => response.json())
        .then(data => {
            if (data.valid) {
                // No errors, proceed with direct export
                window.location.href = '/api/export/schedule';
            } else {
                // Show validation modal with errors
                showValidationModal(data.errors);
            }
        })
        .catch(error => {
            console.error('Validation error:', error);
            alert('Error validating schedule. Please try again.');
        })
        .finally(() => {
            // Reset button state
            exportBtn.disabled = false;
            exportBtn.textContent = 'Export Schedule';
        });
}

function showValidationModal(errors) {
    const modal = document.getElementById('validation-modal');
    const errorsList = document.getElementById('validation-errors-list');
    
    if (!modal || !errorsList) return;
    
    // Clear previous errors
    errorsList.innerHTML = '';
    
    // Add each error to the list
    errors.forEach(error => {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'validation-error-item';
        errorDiv.innerHTML = `
            <div class="validation-error-title">${error.project_name} (${error.event_type})</div>
            <div class="validation-error-details">
                Scheduled: ${error.scheduled_date}<br>
                Valid Range: ${error.valid_start} to ${error.valid_end}
            </div>
            <div class="validation-error-actions">
                <button class="btn-fix" onclick="fixScheduleError(${error.schedule_id}, '${error.project_name}', '${error.error}')">
                    Fix Error
                </button>
            </div>
        `;
        errorsList.appendChild(errorDiv);
    });
    
    // Show modal
    modal.style.display = 'flex';
}

function closeValidationModal() {
    const modal = document.getElementById('validation-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function proceedWithValidExport() {
    // Close validation modal
    closeValidationModal();
    
    // Export only valid events
    window.location.href = '/api/export/schedule?valid_only=true';
}

function fixScheduleError(scheduleId, projectName, errorMessage) {
    // Fetch schedule details to populate the reschedule modal
    fetch(`/api/schedule/${scheduleId}`)
        .then(response => response.json())
        .then(schedule => {
            // Populate reschedule modal with current schedule data
            document.getElementById('reschedule-schedule-id').value = scheduleId;
            document.getElementById('reschedule-event-info').textContent = projectName;
            document.getElementById('reschedule-error-info').textContent = errorMessage;

            // Set current values
            const currentDate = new Date(schedule.schedule_datetime);
            document.getElementById('reschedule-date').value = currentDate.toISOString().split('T')[0];
            document.getElementById('reschedule-time').value = currentDate.toTimeString().slice(0, 5);

            // Store event type and current employee for proper filtering
            window.currentEventType = schedule.event_type;
            window.currentEmployeeId = schedule.employee_id;
            window.currentScheduleDate = currentDate.toISOString().split('T')[0];

            // Set date constraints for reschedule modal
            initializeRescheduleDateConstraints(schedule.start_date, schedule.due_date);

            // Initialize time restrictions for reschedule modal
            initializeRescheduleTimeRestrictions(schedule.event_type, currentDate.toTimeString().slice(0, 5));

            // Load available employees for the date with event type filtering
            fetchEmployeesForReschedule(currentDate.toISOString().split('T')[0], schedule.event_type, schedule.employee_id, currentDate.toISOString().split('T')[0]);

            // Hide validation modal and show reschedule modal
            closeValidationModal();
            document.getElementById('reschedule-modal').style.display = 'flex';
        })
        .catch(error => {
            console.error('Error fetching schedule details:', error);
            alert('Error loading schedule details. Please try again.');
        });
}

function fetchEmployeesForReschedule(date, eventType, currentEmployeeId, currentDate) {
    const employeeSelect = document.getElementById('reschedule-employee');
    if (!employeeSelect) return;

    // Show loading state
    employeeSelect.disabled = true;
    employeeSelect.innerHTML = '<option value="">Loading...</option>';

    // Use role-based filtering endpoint for proper event type restrictions
    let apiUrl = eventType ? `/api/available_employees_for_change/${date}/${eventType}` : `/api/available_employees/${date}`;

    // Add current employee and date parameters if provided
    if (currentEmployeeId && currentDate) {
        apiUrl += `?current_employee_id=${currentEmployeeId}&current_date=${currentDate}`;
    }

    // Fetch available employees with proper role-based filtering
    fetch(apiUrl)
        .then(response => response.json())
        .then(employees => {
            employeeSelect.disabled = false;
            
            if (employees.length === 0) {
                employeeSelect.innerHTML = '<option value="">No employees available</option>';
            } else {
                employeeSelect.innerHTML = '<option value="">Select an employee</option>';
                employees.forEach(employee => {
                    const option = document.createElement('option');
                    option.value = employee.id;
                    option.textContent = `${employee.name} (${employee.job_title})`;
                    employeeSelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error fetching employees:', error);
            employeeSelect.disabled = false;
            employeeSelect.innerHTML = '<option value="">Error loading employees</option>';
        });
}

function initializeRescheduleDateConstraints(startDate, dueDate) {
    const dateInput = document.getElementById('reschedule-date');

    if (!dateInput || !startDate || !dueDate) {
        return;
    }

    // Set min and max date constraints
    dateInput.min = startDate;
    dateInput.max = dueDate;

    // Add change event listener to refresh employee list when date changes
    dateInput.addEventListener('change', function() {
        if (this.value && window.currentEventType) {
            fetchEmployeesForReschedule(this.value, window.currentEventType, window.currentEmployeeId, window.currentScheduleDate);
        }
    });
}

function initializeRescheduleTimeRestrictions(eventType, currentTime) {
    const timeInput = document.getElementById('reschedule-time');
    const timeDropdown = document.getElementById('reschedule-time-dropdown');
    
    if (!timeInput || !timeDropdown || !eventType) {
        return;
    }
    
    // Define time options for each event type
    const timeRestrictions = {
        'Core': ['09:45', '10:30', '11:00', '11:30'],
        'Supervisor': ['12:00'],
        'Freeosk': ['09:00', '12:00'],
        'Digitals': ['09:15', '09:30', '09:45', '10:00']
    };
    
    // Check if this event type has time restrictions
    if (timeRestrictions[eventType]) {
        // Hide time input, show dropdown
        timeInput.style.display = 'none';
        timeInput.required = false;
        timeDropdown.style.display = 'block';
        timeDropdown.required = true;
        timeDropdown.classList.remove('hidden');
        
        // Populate dropdown with allowed times
        timeDropdown.innerHTML = '<option value="">Select a time</option>';
        timeRestrictions[eventType].forEach(time => {
            const option = document.createElement('option');
            option.value = time;
            option.textContent = formatTime(time);
            if (time === currentTime) {
                option.selected = true;
            }
            timeDropdown.appendChild(option);
        });
        
        // Set default value for Freeosk events if no current time matches
        if (eventType === 'Freeosk' && !timeRestrictions[eventType].includes(currentTime)) {
            timeDropdown.value = '09:00';
        }
        
    } else {
        // Show time input, hide dropdown (for Other events)
        timeInput.style.display = 'block';
        timeInput.required = true;
        timeDropdown.style.display = 'none';
        timeDropdown.required = false;
        timeDropdown.classList.add('hidden');
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

// Initialize reschedule form submission
document.addEventListener('DOMContentLoaded', function() {
    const rescheduleForm = document.getElementById('reschedule-form');
    if (rescheduleForm) {
        rescheduleForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const scheduleId = document.getElementById('reschedule-schedule-id').value;
            const date = document.getElementById('reschedule-date').value;
            const timeInput = document.getElementById('reschedule-time');
            const timeDropdown = document.getElementById('reschedule-time-dropdown');
            const employeeId = document.getElementById('reschedule-employee').value;
            
            // Get time value from the appropriate input (dropdown takes precedence if visible)
            let time;
            if (timeDropdown && timeDropdown.style.display !== 'none' && timeDropdown.value) {
                time = timeDropdown.value;
            } else {
                time = timeInput.value;
            }
            
            if (!scheduleId || !date || !time || !employeeId) {
                alert('Please fill in all required fields.');
                return;
            }
            
            // Submit reschedule request
            const formData = new FormData();
            formData.append('schedule_id', scheduleId);
            formData.append('new_date', date);
            formData.append('new_time', time);
            formData.append('employee_id', employeeId);
            
            fetch('/api/reschedule', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Event rescheduled successfully!');
                    closeModal('reschedule-modal');
                    // Optionally refresh validation or page
                    window.location.reload();
                } else {
                    alert(`Error: ${data.error || 'Failed to reschedule event'}`);
                }
            })
            .catch(error => {
                console.error('Reschedule error:', error);
                alert('Error rescheduling event. Please try again.');
            });
        });
    }
});