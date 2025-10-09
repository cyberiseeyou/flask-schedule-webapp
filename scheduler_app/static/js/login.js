/**
 * Login Page JavaScript - Product Connections Scheduler
 * Handles authentication with Crossmark MVRetail API
 */

class LoginManager {
    constructor() {
        this.form = document.getElementById('loginForm');
        this.usernameInput = document.getElementById('username');
        this.passwordInput = document.getElementById('password');
        this.loginButton = document.getElementById('loginButton');
        this.passwordToggle = document.querySelector('.password-toggle');
        this.errorContainer = document.getElementById('errorContainer');
        this.successContainer = document.getElementById('successContainer');

        this.isSubmitting = false;
        this.maxRetries = 3;
        this.retryCount = 0;

        this.init();
    }

    init() {
        this.bindEvents();
        this.setupAccessibility();
        this.loadRememberedCredentials();
        this.focusFirstInput();
    }

    bindEvents() {
        // Form submission
        this.form.addEventListener('submit', this.handleSubmit.bind(this));

        // Password toggle
        this.passwordToggle.addEventListener('click', this.togglePassword.bind(this));

        // Real-time validation
        this.usernameInput.addEventListener('input', this.validateUsername.bind(this));
        this.passwordInput.addEventListener('input', this.validatePassword.bind(this));

        // Enter key handling
        this.usernameInput.addEventListener('keypress', this.handleEnterKey.bind(this));
        this.passwordInput.addEventListener('keypress', this.handleEnterKey.bind(this));

        // Input focus effects
        [this.usernameInput, this.passwordInput].forEach(input => {
            input.addEventListener('focus', this.handleInputFocus.bind(this));
            input.addEventListener('blur', this.handleInputBlur.bind(this));
        });
    }

    setupAccessibility() {
        // Add ARIA labels for better screen reader support
        this.form.setAttribute('aria-label', 'Login form');
        this.passwordToggle.setAttribute('aria-label', 'Toggle password visibility');

        // Set initial ARIA states
        this.updatePasswordToggleAria();
    }

    loadRememberedCredentials() {
        // Check for remembered username (never store password)
        const rememberedUsername = localStorage.getItem('rememberedUsername');
        const rememberCheckbox = document.getElementById('remember');

        if (rememberedUsername) {
            this.usernameInput.value = rememberedUsername;
            rememberCheckbox.checked = true;
            this.passwordInput.focus();
        }
    }

    focusFirstInput() {
        // Focus appropriate field on page load
        if (this.usernameInput.value) {
            this.passwordInput.focus();
        } else {
            this.usernameInput.focus();
        }
    }

    handleEnterKey(event) {
        if (event.key === 'Enter' && !this.isSubmitting) {
            this.form.dispatchEvent(new Event('submit', { bubbles: true }));
        }
    }

    handleInputFocus(event) {
        event.target.parentElement.classList.add('focused');
        this.clearMessages();
    }

    handleInputBlur(event) {
        event.target.parentElement.classList.remove('focused');
    }

    validateUsername() {
        const username = this.usernameInput.value.trim();
        const isValid = username.length >= 3;

        this.updateFieldValidation(this.usernameInput, isValid);
        return isValid;
    }

    validatePassword() {
        const password = this.passwordInput.value;
        const isValid = password.length >= 8;

        this.updateFieldValidation(this.passwordInput, isValid);
        return isValid;
    }

    updateFieldValidation(field, isValid) {
        if (field.value.length === 0) {
            field.classList.remove('valid', 'invalid');
            return;
        }

        field.classList.toggle('valid', isValid);
        field.classList.toggle('invalid', !isValid);
    }

    togglePassword() {
        const isPassword = this.passwordInput.type === 'password';
        const eyeOpen = this.passwordToggle.querySelector('.eye-open');
        const eyeClosed = this.passwordToggle.querySelector('.eye-closed');

        this.passwordInput.type = isPassword ? 'text' : 'password';
        eyeOpen.style.display = isPassword ? 'none' : 'block';
        eyeClosed.style.display = isPassword ? 'block' : 'none';

        this.updatePasswordToggleAria();

        // Maintain focus on password field
        this.passwordInput.focus();
    }

    updatePasswordToggleAria() {
        const isPassword = this.passwordInput.type === 'password';
        this.passwordToggle.setAttribute('aria-label', isPassword ? 'Show password' : 'Hide password');
    }

    async handleSubmit(event) {
        event.preventDefault();

        if (this.isSubmitting) return;

        // Clear previous messages
        this.clearMessages();

        // Validate inputs
        const isUsernameValid = this.validateUsername();
        const isPasswordValid = this.validatePassword();

        if (!isUsernameValid || !isPasswordValid) {
            this.showError('Please fill in all required fields correctly.');
            return;
        }

        // Start submission process
        this.setSubmitting(true);

        try {
            const result = await this.submitLogin();

            if (result.success) {
                this.handleLoginSuccess(result);
            } else {
                this.handleLoginError(result);
            }
        } catch (error) {
            this.handleLoginError({ error: 'Network error. Please check your connection and try again.' });
        } finally {
            this.setSubmitting(false);
        }
    }

    async submitLogin() {
        const formData = new FormData(this.form);

        // Handle remember me
        if (formData.get('remember')) {
            localStorage.setItem('rememberedUsername', formData.get('username'));
        } else {
            localStorage.removeItem('rememberedUsername');
        }

        // Convert FormData to URLSearchParams for proper form encoding
        const params = new URLSearchParams(formData);

        const response = await fetch(this.form.action, {
            method: 'POST',
            body: params,
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            },
            credentials: 'same-origin'
        });

        const contentType = response.headers.get('content-type');
        let result;

        if (contentType && contentType.includes('application/json')) {
            result = await response.json();
        } else {
            // Handle non-JSON responses (e.g., redirects)
            if (response.ok) {
                result = { success: true, redirect: response.url };
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        }

        return result;
    }

    handleLoginSuccess(result) {
        // Clear form for security
        this.passwordInput.value = '';

        // Check if database refresh is needed
        if (result.refresh_database) {
            // Show initial success briefly, then transition to database refresh
            this.showSuccess('Login successful!');
            // Add a small delay to ensure session cookie is properly set
            setTimeout(() => {
                this.showRefreshProgress('Clearing existing data and fetching latest events from Crossmark API...');
                this.triggerDatabaseRefresh(() => {
                    // Redirect after refresh completes
                    if (result.redirect) {
                        window.location.href = result.redirect;
                    } else {
                        window.location.href = '/';
                    }
                });
            }, 800); // 800ms delay - show success briefly then start refresh
        } else {
            // No database refresh needed
            this.showSuccess('Login successful! Redirecting to dashboard...');
            // Redirect after short delay
            setTimeout(() => {
                if (result.redirect) {
                    window.location.href = result.redirect;
                } else {
                    window.location.href = '/';
                }
            }, 1500);
        }
    }

    async triggerDatabaseRefresh(onComplete) {
        try {
            // Progress indicator already shown by caller
            const response = await fetch('/api/refresh/database', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });

            // Check if we got redirected to login (authentication failed)
            if (response.redirected && response.url.includes('/login')) {
                throw new Error('Authentication failed - session not established yet');
            }

            const result = await response.json();

            if (result.success) {
                const stats = result.stats;
                let message = `Database completely refreshed! Cleared ${stats.cleared} old events, added ${stats.created} fresh events from ${stats.total_fetched} fetched.`;

                // Show warning if there are Staffed events without schedules
                if (result.warning) {
                    message += `\n\n⚠️ ${result.warning}`;
                }

                this.showRefreshProgress(message);

                // Complete after showing final message (longer delay if there's a warning)
                const delay = result.warning ? 4000 : 2000;
                setTimeout(() => {
                    onComplete();
                }, delay);
            } else {
                this.showError(`Database refresh failed: ${result.message}`);
                // Still redirect on failure after delay
                setTimeout(() => {
                    onComplete();
                }, 3000);
            }
        } catch (error) {
            // If authentication failed, try once more after additional delay
            if (error.message.includes('Authentication failed')) {
                this.showRefreshProgress('Session not ready yet, retrying database refresh...');
                setTimeout(async () => {
                    try {
                        const retryResponse = await fetch('/api/refresh/database', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-Requested-With': 'XMLHttpRequest'
                            },
                            credentials: 'same-origin'
                        });

                        if (retryResponse.redirected && retryResponse.url.includes('/login')) {
                            throw new Error('Authentication still failed after retry');
                        }

                        const retryResult = await retryResponse.json();
                        if (retryResult.success) {
                            const stats = retryResult.stats;
                            this.showRefreshProgress(
                                `Database completely refreshed! Cleared ${stats.cleared} old events, added ${stats.created} fresh events from ${stats.total_fetched} fetched.`
                            );
                            setTimeout(() => {
                                onComplete();
                            }, 2000);
                        } else {
                            this.showError(`Database refresh failed: ${retryResult.message}`);
                            setTimeout(() => {
                                onComplete();
                            }, 3000);
                        }
                    } catch (retryError) {
                        this.showError('Database refresh failed after retry. Proceeding to dashboard...');
                        setTimeout(() => {
                            onComplete();
                        }, 3000);
                    }
                }, 1500); // Additional 1.5 second delay for retry
            } else {
                this.showError('Database refresh failed. Proceeding to dashboard...');
                // Still redirect on error after delay
                setTimeout(() => {
                    onComplete();
                }, 3000);
            }
        }
    }

    showRefreshProgress(message) {
        this.errorContainer.style.display = 'none';
        this.successContainer.style.display = 'block';

        // Clear the success container completely
        this.successContainer.innerHTML = '';

        // Create refresh progress element
        const progressIndicator = document.createElement('div');
        progressIndicator.className = 'success-message';
        progressIndicator.innerHTML = `
            <div class="progress-spinner"></div>
            <span class="progress-text">${message}</span>
        `;

        // Add the progress indicator
        this.successContainer.appendChild(progressIndicator);

        // Announce to screen readers
        this.successContainer.setAttribute('role', 'alert');
    }

    handleLoginError(result) {
        this.retryCount++;

        let errorMessage = 'Login failed. Please check your credentials.';

        if (result.error) {
            if (result.error.includes('401')) {
                errorMessage = 'Invalid username or password. Please try again.';
            } else if (result.error.includes('timeout')) {
                errorMessage = 'Connection timeout. Please check your network and try again.';
            } else if (result.error.includes('network')) {
                errorMessage = 'Network error. Please check your connection.';
            } else {
                errorMessage = result.error;
            }
        }

        // Add retry information
        if (this.retryCount >= this.maxRetries) {
            errorMessage += ' Please contact support if the problem persists.';
        } else {
            errorMessage += ` (Attempt ${this.retryCount}/${this.maxRetries})`;
        }

        this.showError(errorMessage);

        // Focus password field for retry
        this.passwordInput.select();
        this.passwordInput.focus();
    }

    setSubmitting(isSubmitting) {
        this.isSubmitting = isSubmitting;

        const buttonText = this.loginButton.querySelector('.button-text');
        const buttonLoading = this.loginButton.querySelector('.button-loading');

        if (isSubmitting) {
            buttonText.style.display = 'none';
            buttonLoading.style.display = 'flex';
            this.loginButton.disabled = true;
            this.form.classList.add('submitting');
        } else {
            buttonText.style.display = 'block';
            buttonLoading.style.display = 'none';
            this.loginButton.disabled = false;
            this.form.classList.remove('submitting');
        }
    }

    showError(message) {
        document.getElementById('errorMessage').textContent = message;
        this.errorContainer.style.display = 'block';
        this.successContainer.style.display = 'none';

        // Announce to screen readers
        this.errorContainer.setAttribute('role', 'alert');

        // Scroll error into view if needed
        this.errorContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    showSuccess(message) {
        document.getElementById('successMessage').textContent = message;
        this.successContainer.style.display = 'block';
        this.errorContainer.style.display = 'none';

        // Announce to screen readers
        this.successContainer.setAttribute('role', 'alert');
    }

    clearMessages() {
        this.errorContainer.style.display = 'none';
        this.successContainer.style.display = 'none';
    }
}

// Enhanced form validation styles and refresh progress styles
const style = document.createElement('style');
style.textContent = `
    .form-input.valid {
        border-color: var(--success-color);
    }

    .form-input.invalid {
        border-color: var(--error-color);
    }

    .input-container.focused {
        transform: translateY(-1px);
    }

    .login-form.submitting .form-input {
        pointer-events: none;
    }

    .login-form.submitting .password-toggle {
        pointer-events: none;
        opacity: 0.5;
    }

    /* Database refresh progress styles */
    .refresh-progress {
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
        margin-top: var(--spacing-xs);
        padding: var(--spacing-sm);
        background: rgba(46, 125, 50, 0.1);
        border-radius: var(--border-radius-sm);
        border-left: 4px solid var(--success-color);
    }

    .progress-spinner {
        width: 20px;
        height: 20px;
        border: 2px solid rgba(46, 125, 50, 0.3);
        border-top: 2px solid var(--success-color);
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }

    .progress-text {
        font-size: var(--font-size-small);
        font-weight: 500;
        color: var(--success-color);
        line-height: 1.4;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    /* Enhanced success message container for refresh */
    .success-container .refresh-progress {
        animation: slideInDown 0.3s ease-out;
    }

    @keyframes slideInDown {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
`;
document.head.appendChild(style);

// Initialize login manager when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new LoginManager());
} else {
    new LoginManager();
}

// Global error handler for uncaught errors
window.addEventListener('error', (event) => {
    console.error('Login page error:', event.error);

    // Show user-friendly error if login manager exists
    if (window.loginManager) {
        window.loginManager.showError('An unexpected error occurred. Please refresh the page and try again.');
    }
});

// Handle network status changes
window.addEventListener('online', () => {
    if (document.querySelector('.error-message')) {
        location.reload();
    }
});

window.addEventListener('offline', () => {
    if (window.loginManager) {
        window.loginManager.showError('You appear to be offline. Please check your connection.');
    }
});