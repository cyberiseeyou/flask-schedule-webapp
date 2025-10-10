# CRITICAL-02: Review and Reduce CSRF Protection Exemptions

## Priority
🔴 **CRITICAL** - Immediate Action Required

## Status
🔵 In Progress - Implementation Complete, Testing Required

## Type
🔒 Security Vulnerability

## Assigned To
**Dev Agent (James)**

## Description
Currently, 10 blueprints are exempted from CSRF protection in `scheduler_app/app.py`, exposing the application to Cross-Site Request Forgery attacks.

### Current Exemptions (Lines 110-177)
```python
csrf.exempt(auth_bp)           # Line 110
csrf.exempt(scheduling_bp)     # Line 121
csrf.exempt(employees_bp)      # Line 128
csrf.exempt(api_bp)            # Line 135
csrf.exempt(rotations_bp)      # Line 142
csrf.exempt(auto_scheduler_bp) # Line 149
csrf.exempt(admin_bp)          # Line 156
csrf.exempt(printing_bp)       # Line 163
csrf.exempt(walmart_bp)        # Line 170
csrf.exempt(edr_sync_bp)       # Line 177
```

## Security Risk
- **Severity**: High
- **Impact**: CSRF attacks can modify schedules, delete events, change employee assignments
- **Attack Vector**: Malicious sites can submit authenticated requests
- **Affected Endpoints**: All POST/PUT/DELETE routes in exempted blueprints

## Acceptance Criteria
- [x] Audit all exempted blueprints for CSRF protection needs
- [x] Implement token-based CSRF for AJAX endpoints
- [x] Remove unnecessary exemptions
- [x] Add CSRF tokens to all forms (automatic via JavaScript)
- [x] Update frontend JavaScript to include CSRF tokens
- [ ] Test all API endpoints with CSRF enabled - **USER TESTING REQUIRED**
- [x] Document CSRF protection strategy

## Implementation Strategy

### Phase 1: Audit Exemptions (1-2 hours)

Create audit checklist:
```markdown
| Blueprint | Routes | Needs CSRF? | Reason for Exemption | Action |
|-----------|--------|-------------|----------------------|--------|
| auth_bp | login, logout | Partial | Login doesn't have token yet | Keep exempt for login only |
| scheduling_bp | schedule, reschedule | YES | AJAX endpoints | Add token-based CSRF |
| employees_bp | CRUD operations | YES | AJAX endpoints | Add token-based CSRF |
| api_bp | All API routes | YES | AJAX endpoints | Add token-based CSRF |
| rotations_bp | Rotation management | YES | AJAX endpoints | Add token-based CSRF |
| auto_scheduler_bp | Auto-schedule | YES | AJAX endpoints | Add token-based CSRF |
| admin_bp | Admin operations | YES | AJAX endpoints | Add token-based CSRF |
| printing_bp | Print endpoints | Partial | Read-only mostly | Protect POST routes |
| walmart_bp | External API | NO | External webhook | Document security measures |
| edr_sync_bp | EDR sync | YES | Admin operations | Add token-based CSRF |
```

### Phase 2: Implement CSRF for AJAX (4-6 hours)

#### Option A: Use Flask-WTF CSRF for AJAX
```python
# scheduler_app/app.py
from flask_wtf.csrf import CSRFProtect, generate_csrf

csrf = CSRFProtect(app)

# Add CSRF token to all responses
@app.after_request
def add_csrf_token(response):
    """Add CSRF token to response headers for AJAX"""
    if request.endpoint and not request.endpoint.startswith('static'):
        response.set_cookie('csrf_token', generate_csrf())
    return response

# Create decorator for routes that need CSRF
from functools import wraps
from flask import request, abort

def csrf_required(f):
    """Decorator to require CSRF token for AJAX requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if CSRF token is present
        token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
        if not token:
            abort(400, 'CSRF token missing')

        # Flask-WTF will validate the token
        return f(*args, **kwargs)
    return decorated_function
```

#### Option B: Remove Blanket Exemptions
```python
# scheduler_app/app.py

# BEFORE: Blanket exemptions
# csrf.exempt(api_bp)  # DON'T DO THIS

# AFTER: Selective exemptions per route
from flask_wtf.csrf import exempt

@api_bp.route('/webhook/external', methods=['POST'])
@exempt  # Only exempt specific routes that need it
def external_webhook():
    """External webhook - exempt from CSRF"""
    pass
```

### Phase 3: Update Frontend JavaScript (3-4 hours)

```javascript
// static/js/csrf_helper.js
/**
 * Get CSRF token from cookie
 */
function getCsrfToken() {
    const name = 'csrf_token=';
    const decodedCookie = decodeURIComponent(document.cookie);
    const cookieArray = decodedCookie.split(';');

    for (let cookie of cookieArray) {
        cookie = cookie.trim();
        if (cookie.indexOf(name) === 0) {
            return cookie.substring(name.length);
        }
    }
    return null;
}

/**
 * Setup CSRF token for all AJAX requests
 */
function setupCsrfProtection() {
    // Add CSRF token to all jQuery AJAX requests
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
                const token = getCsrfToken();
                if (token) {
                    xhr.setRequestHeader('X-CSRF-Token', token);
                }
            }
        }
    });

    // For fetch API
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        if (options.method && !/^(GET|HEAD|OPTIONS)$/i.test(options.method)) {
            options.headers = options.headers || {};
            options.headers['X-CSRF-Token'] = getCsrfToken();
        }
        return originalFetch(url, options);
    };
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', setupCsrfProtection);
```

```html
<!-- templates/base.html - Add to head -->
<script src="{{ url_for('static', filename='js/csrf_helper.js') }}"></script>
```

### Phase 4: Update Forms (2-3 hours)

For traditional form submissions:
```html
<!-- Example: templates/schedule.html -->
<form method="POST" action="/schedule/create">
    {{ csrf_token() }}  <!-- Add this to all forms -->
    <!-- rest of form fields -->
</form>
```

### Phase 5: Selective Exemptions (1-2 hours)

Keep exemptions only where absolutely necessary:

```python
# scheduler_app/routes/auth.py
from flask_wtf.csrf import exempt

@auth_bp.route('/login', methods=['POST'])
@exempt  # Login can't have CSRF token before authentication
def login():
    """Login endpoint - exempt from CSRF"""
    pass

# scheduler_app/routes/walmart_api.py
@walmart_bp.route('/webhook', methods=['POST'])
@exempt  # External webhook from Walmart
def walmart_webhook():
    """
    External webhook - exempt from CSRF.
    Security: Validate request signature instead.
    """
    # Implement signature validation
    pass
```

## Testing Checklist

### Manual Testing
- [ ] Test all schedule creation/modification flows
- [ ] Test employee CRUD operations
- [ ] Test rotation management
- [ ] Test auto-scheduler
- [ ] Test admin operations
- [ ] Test printing functionality
- [ ] Test EDR sync operations
- [ ] Verify forms include CSRF tokens
- [ ] Verify AJAX requests include tokens

### Automated Testing
```python
# tests/test_csrf_protection.py
def test_csrf_protection_enabled():
    """Test that CSRF protection blocks requests without token"""
    response = client.post('/api/schedule', json={'data': 'test'})
    assert response.status_code == 400  # Should fail without token

def test_csrf_token_in_forms():
    """Test that forms include CSRF token"""
    response = client.get('/schedule')
    assert b'csrf_token' in response.data

def test_ajax_with_csrf_token():
    """Test AJAX requests work with CSRF token"""
    csrf_token = get_csrf_token(client)
    headers = {'X-CSRF-Token': csrf_token}
    response = client.post('/api/schedule', headers=headers, json={'data': 'test'})
    assert response.status_code != 400  # Should succeed with token
```

## Rollout Plan

### Stage 1: Development (Week 1)
- Implement CSRF protection in dev environment
- Test all functionality
- Fix any broken endpoints

### Stage 2: Staging (Week 2)
- Deploy to staging
- Conduct thorough QA testing
- Fix any issues

### Stage 3: Production (Week 3)
- Deploy to production during low-traffic window
- Monitor for CSRF-related errors
- Have rollback plan ready

## Dependencies
- **CRITICAL-01** (optional): Can be done in parallel

## Estimated Effort
⏱️ **16-20 hours** (2-3 days)
- Audit: 2 hours
- Backend implementation: 6 hours
- Frontend implementation: 4 hours
- Testing: 4 hours
- Documentation: 2 hours

## Security Best Practices

1. **Double Submit Cookie Pattern**
   - Send token in cookie AND header/form
   - Server validates both match

2. **Token Rotation**
   - Generate new token on each request
   - Invalidate old tokens

3. **SameSite Cookie Attribute**
```python
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
```

4. **Content Security Policy**
```python
@app.after_request
def set_csp(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response
```

## References
- [OWASP: CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [Flask-WTF CSRF Protection](https://flask-wtf.readthedocs.io/en/stable/csrf.html)

## Notes
⚠️ **Breaking Change**: Frontend JavaScript must be updated simultaneously with backend changes to avoid breaking AJAX functionality.

---
**Created**: 2025-01-09
**Last Updated**: 2025-01-09
**Reporter**: Quinn (QA Agent)
