// EDR Downloader - Main JavaScript

let isAuthenticated = false;
let currentEvents = [];

// DOM Elements
const eventDateInput = document.getElementById('event-date');
const previewBtn = document.getElementById('preview-btn');
const downloadBtn = document.getElementById('download-btn');
const statusMessage = document.getElementById('status-message');
const eventList = document.getElementById('event-list');
const eventItems = document.getElementById('event-items');
const progressContainer = document.getElementById('progress-container');
const progressFill = document.getElementById('progress-fill');
const progressText = document.getElementById('progress-text');
const resultsContainer = document.getElementById('results-container');
const resultsContent = document.getElementById('results-content');

// MFA Modal Elements
const mfaModal = document.getElementById('mfa-modal');
const mfaCodeInput = document.getElementById('mfa-code');
const mfaSubmitBtn = document.getElementById('mfa-submit-btn');
const mfaCancelBtn = document.getElementById('mfa-cancel-btn');
const mfaError = document.getElementById('mfa-error');

// Set default date to today
eventDateInput.valueAsDate = new Date();

// Event Listeners
previewBtn.addEventListener('click', previewEvents);
downloadBtn.addEventListener('click', startDownload);
mfaSubmitBtn.addEventListener('click', submitMFACode);
mfaCancelBtn.addEventListener('click', closeMFAModal);

// Allow Enter key in MFA input
mfaCodeInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        submitMFACode();
    }
});

// Utility Functions
function showStatus(message, type) {
    statusMessage.textContent = message;
    statusMessage.className = `status-message ${type}`;
    statusMessage.style.display = 'block';
}

function hideStatus() {
    statusMessage.style.display = 'none';
}

function showMFAModal() {
    mfaModal.classList.add('active');
    mfaCodeInput.value = '';
    mfaCodeInput.focus();
    mfaError.classList.remove('active');
}

function closeMFAModal() {
    mfaModal.classList.remove('active');
    downloadBtn.disabled = false;
}

function showMFAError(message) {
    mfaError.textContent = message;
    mfaError.classList.add('active');
}

// Preview Events
async function previewEvents() {
    const selectedDate = eventDateInput.value;

    if (!selectedDate) {
        showStatus('Please select a date', 'error');
        return;
    }

    previewBtn.disabled = true;
    hideStatus();
    eventList.style.display = 'none';
    progressContainer.style.display = 'none';
    resultsContainer.style.display = 'none';

    try {
        const response = await fetch('/api/get-events', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ date: selectedDate })
        });

        const data = await response.json();

        if (data.success) {
            currentEvents = data.events;

            if (data.count === 0) {
                showStatus('No CORE events found for this date', 'info');
                eventList.style.display = 'none';
            } else {
                // Display events
                eventItems.innerHTML = '';
                data.events.forEach((event, index) => {
                    const eventDiv = document.createElement('div');
                    eventDiv.className = 'event-item';
                    eventDiv.innerHTML = `
                        <strong>Event ${index + 1}:</strong> ${event.project_name}<br>
                        <small>Event Number: ${event.event_number} | Store: ${event.store_name || 'N/A'}</small>
                    `;
                    eventItems.appendChild(eventDiv);
                });

                eventList.style.display = 'block';
                showStatus(`Found ${data.count} CORE event(s)`, 'success');
            }
        } else {
            showStatus(data.error || 'Failed to retrieve events', 'error');
        }
    } catch (error) {
        showStatus('Error connecting to server', 'error');
        console.error('Error:', error);
    } finally {
        previewBtn.disabled = false;
    }
}

// Start Download Process
async function startDownload() {
    const selectedDate = eventDateInput.value;

    if (!selectedDate) {
        showStatus('Please select a date', 'error');
        return;
    }

    downloadBtn.disabled = true;
    hideStatus();
    progressContainer.style.display = 'none';
    resultsContainer.style.display = 'none';

    // Check if authenticated
    if (!isAuthenticated) {
        // Request MFA code
        showStatus('Requesting MFA code...', 'info');

        try {
            const response = await fetch('/api/request-mfa', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (data.success) {
                showStatus('MFA code sent to your phone', 'success');
                showMFAModal();
            } else {
                showStatus(data.error || 'Failed to request MFA code', 'error');
                downloadBtn.disabled = false;
            }
        } catch (error) {
            showStatus('Error connecting to server', 'error');
            console.error('Error:', error);
            downloadBtn.disabled = false;
        }
    } else {
        // Already authenticated, proceed with download
        downloadEDRs(selectedDate);
    }
}

// Submit MFA Code
async function submitMFACode() {
    const mfaCode = mfaCodeInput.value.trim();

    if (!mfaCode || mfaCode.length !== 6) {
        showMFAError('Please enter a valid 6-digit code');
        return;
    }

    mfaSubmitBtn.disabled = true;

    try {
        const response = await fetch('/api/authenticate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ mfa_code: mfaCode })
        });

        const data = await response.json();

        if (data.success) {
            isAuthenticated = true;
            closeMFAModal();
            showStatus('Authentication successful! Starting download...', 'success');

            // Proceed with download
            const selectedDate = eventDateInput.value;
            setTimeout(() => downloadEDRs(selectedDate), 1000);
        } else {
            showMFAError(data.error || 'Invalid MFA code');
            mfaSubmitBtn.disabled = false;
        }
    } catch (error) {
        showMFAError('Error connecting to server');
        console.error('Error:', error);
        mfaSubmitBtn.disabled = false;
    }
}

// Download EDRs
async function downloadEDRs(selectedDate) {
    hideStatus();
    progressContainer.style.display = 'block';
    resultsContainer.style.display = 'none';
    progressFill.style.width = '0%';
    progressText.textContent = 'Starting download...';

    try {
        const response = await fetch('/api/download-edrs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ date: selectedDate })
        });

        const data = await response.json();

        if (response.status === 401) {
            // Authentication expired
            isAuthenticated = false;
            showStatus('Authentication expired. Please try again.', 'error');
            downloadBtn.disabled = false;
            progressContainer.style.display = 'none';
            return;
        }

        if (data.success) {
            // Update progress
            const total = data.downloaded + data.failed;
            const percentage = total > 0 ? (data.downloaded / total * 100) : 0;
            progressFill.style.width = percentage + '%';
            progressText.textContent = `${data.downloaded} / ${total} downloaded`;

            // Show results
            resultsContainer.style.display = 'block';
            resultsContent.innerHTML = '';

            // Show successful downloads
            if (data.files.length > 0) {
                const successHeader = document.createElement('h4');
                successHeader.textContent = `Successfully Downloaded (${data.files.length})`;
                successHeader.style.color = '#28a745';
                successHeader.style.marginBottom = '10px';
                resultsContent.appendChild(successHeader);

                data.files.forEach(file => {
                    const resultDiv = document.createElement('div');
                    resultDiv.className = 'result-success';
                    resultDiv.innerHTML = `
                        <strong>${file.event_number}</strong>: ${file.project_name}<br>
                        <small>File: ${file.filename}</small>
                    `;
                    resultsContent.appendChild(resultDiv);
                });
            }

            // Show failed downloads
            if (data.errors.length > 0) {
                const errorHeader = document.createElement('h4');
                errorHeader.textContent = `Failed (${data.errors.length})`;
                errorHeader.style.color = '#dc3545';
                errorHeader.style.marginTop = '20px';
                errorHeader.style.marginBottom = '10px';
                resultsContent.appendChild(errorHeader);

                data.errors.forEach(error => {
                    const resultDiv = document.createElement('div');
                    resultDiv.className = 'result-error';
                    resultDiv.innerHTML = `
                        <strong>${error.event_number || 'N/A'}</strong>: ${error.project_name}<br>
                        <small>Error: ${error.error}</small>
                    `;
                    resultsContent.appendChild(resultDiv);
                });
            }

            showStatus(
                `Download complete! ${data.downloaded} successful, ${data.failed} failed`,
                data.failed === 0 ? 'success' : 'info'
            );
        } else {
            showStatus(data.error || 'Failed to download EDRs', 'error');
            progressContainer.style.display = 'none';
        }
    } catch (error) {
        showStatus('Error connecting to server', 'error');
        console.error('Error:', error);
        progressContainer.style.display = 'none';
    } finally {
        downloadBtn.disabled = false;
    }
}
