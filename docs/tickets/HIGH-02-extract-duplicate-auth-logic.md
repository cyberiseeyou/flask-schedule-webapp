# HIGH-02: Extract Duplicate Authentication Logic

## Priority
🟡 **HIGH** - Within 2 Weeks

## Status
🟡 Open

## Type
🔨 Code Quality / DRY Principle

## Assigned To
**Dev Agent (James)**

## Description
Authentication logic for Crossmark API is duplicated across 4+ routes in `api.py` (reschedule, reschedule_event, change_employee, trade_events). This violates DRY principle and makes maintenance difficult.

## Current Duplication
```python
# Repeated in 4 places in routes/api.py
from session_api_service import session_api as external_api

# Prepare API data
rep_id = str(employee.external_id) if employee.external_id else None
mplan_id = str(event.external_id) if event.external_id else None
location_id = str(event.location_mvid) if event.location_mvid else None

# Validate required fields
if not rep_id:
    return jsonify({'error': f'Missing Crossmark employee ID'}), 400
if not mplan_id:
    return jsonify({'error': 'Missing Crossmark event ID'}), 400
if not location_id:
    return jsonify({'error': 'Missing Crossmark location ID'}), 400

# Ensure authenticated
if not external_api.ensure_authenticated():
    return jsonify({'error': 'Failed to authenticate'}), 500

# Submit to API
api_result = external_api.schedule_mplan_event(...)
```

## Solution: Create Decorator

```python
# utils/decorators.py
from functools import wraps
from flask import jsonify, current_app

def require_crossmark_auth(f):
    """Ensure Crossmark API authentication before proceeding"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from session_api_service import session_api
        if not session_api.ensure_authenticated():
            current_app.logger.error("Crossmark authentication failed")
            return jsonify({'error': 'Failed to authenticate with Crossmark API'}), 500
        return f(*args, **kwargs)
    return decorated_function

def validate_crossmark_ids(f):
    """Validate required Crossmark IDs are present"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        data = request.get_json()
        # Validation logic
        return f(*args, **kwargs)
    return decorated_function
```

## Usage After Refactoring
```python
@api_bp.route('/reschedule', methods=['POST'])
@require_crossmark_auth
def reschedule():
    """Reschedule event - authentication handled by decorator"""
    data = request.get_json()
    # Business logic only
    ...
```

## Acceptance Criteria
- [ ] Create `utils/decorators.py` with authentication decorators
- [ ] Extract validation helpers
- [ ] Update all 4 routes to use decorators
- [ ] Tests pass
- [ ] No code duplication

## Estimated Effort
⏱️ **8-12 hours**

---
**Created**: 2025-01-09
