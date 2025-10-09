# Daily Paperwork EDR Integration - Architecture Refactoring

**Date:** 2025-10-03
**Architect:** Winston
**Status:** ✅ Complete

## Problem Statement

The daily paperwork generation system had duplicate authentication logic and was failing to generate EDR reports because:

1. **Incorrect Event ID Usage:** Using `event.external_id` (mPlanID) instead of event number from `project_name`
2. **Duplicate Authentication:** DailyPaperworkGenerator had its own MFA flow instead of reusing Flask session auth
3. **Architectural Inconsistency:** Two different patterns for EDR authentication across the codebase

## Architectural Solution

### **Separation of Concerns**

```
┌─────────────────────────────────────────────────────────────┐
│                    Authentication Domains                    │
├──────────────────────────────┬──────────────────────────────┤
│   Crossmark (mvretail.com)   │   Walmart RetailLink         │
├──────────────────────────────┼──────────────────────────────┤
│ • Planning events            │ • EDR reports only           │
│ • Schedules                  │ • Separate credentials       │
│ • Employee data              │ • Flask session storage      │
│ • SalesTools URLs            │ • Cookie-based auth          │
└──────────────────────────────┴──────────────────────────────┘
```

### **Dependency Injection Pattern**

```python
# BEFORE: DailyPaperworkGenerator creates its own EDR generator
generator = DailyPaperworkGenerator(db, models, session_api)
generator.initialize_edr_generator()  # ❌ Creates new instance
generator.request_mfa_code()          # ❌ Separate auth flow

# AFTER: Inject authenticated instance from Flask session
edr_gen = restore_from_flask_session()  # ✅ Reuse existing auth
generator = DailyPaperworkGenerator(
    db, models, session_api,
    edr_generator=edr_gen  # ✅ Dependency injection
)
```

## Implementation Changes

### 1. **Shared Utility for Event Number Extraction**

**File:** `scheduler_app/utils/event_helpers.py` (NEW)

```python
def extract_event_number(project_name):
    """
    Extract 6-digit event number from project name.
    Example: "606034-JJSF-Super Pretzel" → "606034"
    """
    match = re.match(r'^(\d{6})', project_name)
    return match.group(1) if match else None
```

**Locations Updated:**
- ✅ `scheduler_app/routes/admin.py` - Now uses shared utility
- ✅ `scheduler_app/services/daily_paperwork_generator.py` - Imports and uses utility

### 2. **DailyPaperworkGenerator Refactoring**

**File:** `scheduler_app/services/daily_paperwork_generator.py`

**Constructor Signature:**
```python
def __init__(self, db_session, models_dict,
             session_api_service=None,
             edr_generator=None):  # ← NEW: Accept authenticated instance
```

**EDR Generation Logic:**
```python
# BEFORE (commented out):
# if event.external_id and event.event_type == 'Core':
#     edr_pdf = self.get_event_edr_pdf(event.external_id, ...)

# AFTER:
if self.edr_generator and event.event_type == 'Core':
    event_num = extract_event_number(event.project_name)  # ← Use project_name
    if event_num:
        edr_pdf = self.get_event_edr_pdf(event_num, employee.name)
```

**Methods Deprecated:**
- `initialize_edr_generator()` - Use constructor injection
- `request_mfa_code()` - Use `/api/admin/edr/request-code`
- `complete_authentication()` - Use `/api/admin/edr/authenticate`

### 3. **Route Refactoring**

**File:** `scheduler_app/routes/admin.py`

#### `/api/daily_paperwork/request_mfa` (DEPRECATED)
```python
def request_daily_paperwork_mfa():
    """Redirects to unified EDR authentication"""
    return edr_request_code()  # ← Reuse existing endpoint
```

#### `/api/daily_paperwork/generate` (REFACTORED)
```python
def generate_daily_paperwork():
    # 1. Restore EDR generator from Flask session
    if flask_session.get('edr_auth_token'):
        edr_gen = EDRReportGenerator(...)
        edr_gen.auth_token = flask_session['edr_auth_token']
        # Restore cookies...

    # 2. Inject into generator
    generator = DailyPaperworkGenerator(
        db.session, models_dict, session_api_service,
        edr_generator=edr_gen  # ← Dependency injection
    )

    # 3. Generate paperwork (EDRs included automatically)
    pdf_path = generator.generate_complete_daily_paperwork(target_date)
```

**Request Body:**
```json
// BEFORE:
{
  "mfa_code": "123456",  // ❌ No longer needed
  "date": "2025-10-04"
}

// AFTER:
{
  "date": "2025-10-04"  // ✅ Auth handled via Flask session
}
```

### 4. **Frontend Update**

**File:** `scheduler_app/templates/index.html`

```javascript
// Removed mfa_code from request body
fetch('/api/daily_paperwork/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        date: selectedPaperworkDate  // ← No mfa_code needed
    })
})
```

## Authentication Flow

### **New Unified Flow**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User clicks "Print Paperwork"                            │
│    → Calls /api/admin/edr/request-code                      │
│    → MFA code sent to phone                                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. User enters MFA code                                      │
│    → Calls /api/admin/edr/authenticate                      │
│    → Stores auth_token + cookies in Flask session           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Backend generates paperwork                               │
│    → Restores EDRReportGenerator from Flask session         │
│    → Injects into DailyPaperworkGenerator                   │
│    → Extracts event numbers from project_name               │
│    → Fetches EDRs for Core events                           │
│    → Downloads SalesTools                                    │
│    → Merges: Schedule → Items → [EDR → ST → Log → List]    │
└─────────────────────────────────────────────────────────────┘
```

## Benefits

### ✅ **Single Source of Truth**
- One authentication flow for all EDR operations
- No duplicate MFA logic
- Consistent session management

### ✅ **Proper Event ID Mapping**
- Uses correct event number extraction
- Matches working `print_paperwork_internal()` pattern
- Follows existing successful implementation

### ✅ **Dependency Injection**
- Testable (can mock EDR generator)
- Flexible (can inject different implementations)
- Clear dependencies

### ✅ **Backward Compatibility**
- `extract_event_number()` wrapper in admin.py
- Deprecated methods documented
- Gradual migration path

## Testing Checklist

- [ ] User can authenticate via Settings → Retail-Link Credentials
- [ ] User can click "Print Paperwork" → MFA sent
- [ ] User enters MFA code → Authentication succeeds
- [ ] Paperwork generation includes:
  - [ ] Daily schedule (Core events only)
  - [ ] Item numbers master list
  - [ ] Per-event packets:
    - [ ] EDR report (with employee name)
    - [ ] SalesTools PDF
    - [ ] Activity log
    - [ ] Checklist
- [ ] Only Core events generate EDRs
- [ ] Event numbers extracted correctly from project_name
- [ ] Flask session persists authentication across requests

## Files Modified

### Created:
- `scheduler_app/utils/event_helpers.py`

### Modified:
- `scheduler_app/services/daily_paperwork_generator.py`
- `scheduler_app/routes/admin.py`
- `scheduler_app/templates/index.html`
- `edr_printer/edr_report_generator.py` (cookie-based auth update)

## Migration Notes

### For Future Development:

1. **Remove deprecated methods** after confirming no usage:
   ```python
   # In DailyPaperworkGenerator:
   # - initialize_edr_generator()
   # - request_mfa_code()
   # - complete_authentication()
   ```

2. **Update all callers** of `extract_event_number()` to import from `utils.event_helpers`

3. **Consider consolidating** `print_paperwork_internal()` and `DailyPaperworkGenerator` to eliminate duplication

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                         Flask Routes                          │
├────────────────┬─────────────────────┬──────────────────────┤
│ /api/admin/    │ /api/daily_         │ Shared               │
│ edr/           │ paperwork/          │                      │
├────────────────┼─────────────────────┼──────────────────────┤
│ request-code   │ request_mfa         │ SystemSetting        │
│                │ (redirects →)       │ (credentials)        │
├────────────────┼─────────────────────┼──────────────────────┤
│ authenticate   │ generate            │ Flask Session        │
│ (stores auth)  │ (restores auth)     │ (auth state)         │
└────────────────┴─────────────────────┴──────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│                   EDRReportGenerator                          │
│  (authenticated instance from Flask session)                 │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│              DailyPaperworkGenerator                          │
│  - Accepts EDRReportGenerator via DI                         │
│  - Extracts event numbers from project_name                  │
│  - Generates consolidated paperwork                          │
└──────────────────────────────────────────────────────────────┘
```

---

**Next Steps:**
1. Test the complete flow end-to-end
2. Monitor logs for EDR API responses
3. Update architecture.md if successful
4. Consider additional refactoring to eliminate `print_paperwork_internal()` duplication
