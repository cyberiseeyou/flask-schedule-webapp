# CRITICAL-01: Remove Hardcoded Credentials from Config

## Priority
🔴 **CRITICAL** - Immediate Action Required

## Status
🟡 Open

## Type
🔒 Security Vulnerability

## Assigned To
**Dev Agent (James)**

## Description
Hardcoded credentials found in `scheduler_app/config.py` lines 36-38 expose sensitive Walmart EDR authentication information in version control.

### Current Code (VULNERABLE)
```python
# Lines 36-38 in scheduler_app/config.py
WALMART_EDR_USERNAME = config('WALMART_EDR_USERNAME', default='mat.conder@productconnections.com')
WALMART_EDR_PASSWORD = config('WALMART_EDR_PASSWORD', default='Demos812Th$')
WALMART_EDR_MFA_CREDENTIAL_ID = config('WALMART_EDR_MFA_CREDENTIAL_ID', default='18122365202')
```

## Security Risk
- **Severity**: Critical
- **Impact**: Unauthorized access to Walmart Retail Link system
- **Exposure**: Credentials visible in git history
- **Compliance**: Violation of security best practices

## Acceptance Criteria
- [x] Remove all hardcoded credential defaults from `config.py`
- [x] Update `config.py` to raise error if credentials not set in environment
- [x] Create `.env.example` with placeholder values
- [x] Verify `.env` is in `.gitignore`
- [x] Update documentation with environment variable setup instructions
- [ ] Rotate exposed credentials (contact Walmart admin) - **ACTION REQUIRED BY USER**
- [ ] Audit git history for credential exposure - **MANUAL REVIEW RECOMMENDED**

## Implementation Steps

### Step 1: Update config.py
```python
# scheduler_app/config.py (lines 36-38)
# BEFORE removing defaults, ensure environment variables are set!

WALMART_EDR_USERNAME = config('WALMART_EDR_USERNAME')  # Remove default
WALMART_EDR_PASSWORD = config('WALMART_EDR_PASSWORD')  # Remove default
WALMART_EDR_MFA_CREDENTIAL_ID = config('WALMART_EDR_MFA_CREDENTIAL_ID')  # Remove default

# Add validation in get_config()
def get_config(config_name=None):
    """Get configuration class based on environment"""
    if config_name is None:
        config_name = config('FLASK_ENV', default='development')

    # Validate critical credentials are set
    required_vars = [
        'WALMART_EDR_USERNAME',
        'WALMART_EDR_PASSWORD',
        'WALMART_EDR_MFA_CREDENTIAL_ID'
    ]

    missing = [var for var in required_vars if not os.getenv(var)]
    if missing and config_name != 'testing':
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    return config_mapping.get(config_name, DevelopmentConfig)
```

### Step 2: Create .env.example
```bash
# Create .env.example in project root
cat > .env.example << 'EOF'
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite:///instance/scheduler.db

# External API (Crossmark)
EXTERNAL_API_BASE_URL=https://crossmark.mvretail.com
EXTERNAL_API_USERNAME=your_crossmark_username
EXTERNAL_API_PASSWORD=your_crossmark_password
EXTERNAL_API_TIMEZONE=America/Indiana/Indianapolis

# Walmart Retail Link EDR (NEVER commit actual values!)
WALMART_EDR_USERNAME=your_walmart_email@example.com
WALMART_EDR_PASSWORD=your_secure_password
WALMART_EDR_MFA_CREDENTIAL_ID=your_mfa_credential_id

# Sync Settings
SYNC_ENABLED=false
SYNC_INTERVAL_MINUTES=15

# Encryption
SETTINGS_ENCRYPTION_KEY=generate_using_cryptography_fernet
EOF
```

### Step 3: Verify .gitignore
```bash
# Add to .gitignore if not already present
echo ".env" >> .gitignore
echo "*.env" >> .gitignore
echo ".env.local" >> .gitignore
```

### Step 4: Create Setup Documentation
Create `docs/setup/environment-variables.md`:
```markdown
# Environment Variables Setup

## Required Environment Variables

### Walmart EDR Credentials
1. Contact Walmart Retail Link administrator
2. Request MFA-enabled account credentials
3. Set environment variables:
   - `WALMART_EDR_USERNAME`: Your Walmart email
   - `WALMART_EDR_PASSWORD`: Your secure password
   - `WALMART_EDR_MFA_CREDENTIAL_ID`: MFA credential ID

### Setup Instructions
1. Copy `.env.example` to `.env`
2. Fill in all required values
3. NEVER commit `.env` to version control
```

### Step 5: Credential Rotation (URGENT)
- [ ] Contact Walmart Retail Link administrator
- [ ] Report credential exposure
- [ ] Request password reset for exposed account
- [ ] Generate new MFA credential
- [ ] Update production environment variables

## Testing Checklist
- [x] Application starts without errors when env vars set
- [x] Application raises clear error when env vars missing
- [x] `.env` file is ignored by git
- [x] `.env.example` is committed to repo
- [x] Documentation is clear and complete
- [ ] No credentials in git log: `git log -S "Demos812" --all` - **MANUAL REVIEW RECOMMENDED**

## Dependencies
- None (standalone fix)

## Estimated Effort
⏱️ **2-3 hours** (implementation + documentation + testing)

## Additional Security Recommendations
1. Implement secret rotation schedule (90 days)
2. Use Azure Key Vault / AWS Secrets Manager for production
3. Enable MFA for all external API accounts
4. Implement audit logging for credential usage

## References
- [OWASP: Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [12-Factor App: Config](https://12factor.net/config)

## Notes
⚠️ **IMPORTANT**: Rotate credentials BEFORE committing changes to ensure old credentials are invalidated.

---
**Created**: 2025-01-09
**Last Updated**: 2025-01-09
**Reporter**: Quinn (QA Agent)
