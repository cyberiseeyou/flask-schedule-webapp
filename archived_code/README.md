# Archived Code

This directory contains code that has been removed from the active codebase but preserved for historical reference.

## Files Archived

### api_service.py.archived_20250930

**Archived Date**: September 30, 2025
**Reason**: Unused API service layer - completely replaced by `session_api_service.py`
**Original Location**: `scheduler_app/api_service.py`
**File Size**: 231 lines (8.8KB)

**Why It Was Removed:**
- Token-based authentication approach was never fully integrated
- Application exclusively uses `session_api_service.py` (session-based auth)
- Zero imports found anywhere in codebase
- Missing required configuration (`EXTERNAL_API_KEY` not in config.py)
- Caused developer confusion about which API service to use
- Increased maintenance burden unnecessarily

**Verification:**
```bash
# Comprehensive search found zero usage:
grep -r "import api_service" . --exclude-dir=venv --exclude-dir=__pycache__
grep -r "from api_service" . --exclude-dir=venv --exclude-dir=__pycache__
grep -r "ExternalAPIService" . --exclude-dir=venv --exclude-dir=__pycache__
# All searches returned: No results (except from api_service.py itself)
```

**Active API Service:**
- `scheduler_app/session_api_service.py` (1,291 lines) - Session-based auth with Crossmark API
- Imported in `app.py` as: `from session_api_service import session_api as external_api`

**Impact of Removal:**
-  Removed 231 lines of dead code
-  Eliminated developer confusion
-  Reduced maintenance burden
-  Cleaner codebase
-   Zero breaking changes (file was never used)

**Restoration:**
If this file is ever needed again, it can be restored from this archive. However, significant updates would be required:
1. Add `EXTERNAL_API_KEY` to configuration
2. Implement missing endpoints to match session_api_service functionality
3. Update authentication flow throughout application

**Related Enhancement**: Enhancement #4 - Remove Unused API Service Layer (Priority P0)
