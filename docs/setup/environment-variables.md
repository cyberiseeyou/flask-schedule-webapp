# Environment Variables Setup Guide

## Overview
This document provides comprehensive instructions for configuring environment variables required by the Flask Schedule Webapp.

**Last Updated**: 2025-01-09

---

## Quick Start

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in all required values

3. **NEVER commit `.env` to version control** - it contains sensitive credentials

---

## Required Environment Variables

### Critical Variables (Application will not start without these)

#### Walmart EDR Credentials
These credentials are **REQUIRED** for EDR (Event Data Report) functionality.

| Variable | Description | Example |
|----------|-------------|---------|
| `WALMART_EDR_USERNAME` | Walmart Retail Link email | `user@example.com` |
| `WALMART_EDR_PASSWORD` | Walmart Retail Link password | `SecurePassword123!` |
| `WALMART_EDR_MFA_CREDENTIAL_ID` | MFA credential ID | `12345678901` |

**How to obtain credentials**:
1. Contact your Walmart Retail Link administrator
2. Request an MFA-enabled account
3. Record the username, password, and MFA credential ID
4. Set these values in your `.env` file

**Security Note**: These credentials provide access to sensitive retail data. Handle with extreme care.

---

## Optional Environment Variables

### Flask Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `development` | Environment: `development`, `testing`, or `production` |
| `SECRET_KEY` | Auto-generated | Flask secret key for sessions (MUST set in production) |

**Production Note**: Always set `SECRET_KEY` in production. Generate using:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Database Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///instance/scheduler.db` | Database connection string |

**Examples**:
- SQLite (dev): `sqlite:///instance/scheduler.db`
- PostgreSQL (prod): `postgresql://user:pass@localhost:5432/scheduler`

### External API (Crossmark)

| Variable | Default | Description |
|----------|---------|-------------|
| `EXTERNAL_API_BASE_URL` | `https://crossmark.mvretail.com` | Crossmark API base URL |
| `EXTERNAL_API_USERNAME` | - | Crossmark username |
| `EXTERNAL_API_PASSWORD` | - | Crossmark password |
| `EXTERNAL_API_TIMEZONE` | `America/Indiana/Indianapolis` | Timezone for API calls |
| `EXTERNAL_API_TIMEOUT` | `30` | API timeout in seconds |
| `EXTERNAL_API_MAX_RETRIES` | `3` | Max retry attempts |
| `EXTERNAL_API_RETRY_DELAY` | `1` | Delay between retries (seconds) |
| `SESSION_REFRESH_INTERVAL` | `3600` | Session refresh interval (seconds) |

### Sync Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `SYNC_ENABLED` | `false` | Enable background sync |
| `SYNC_INTERVAL_MINUTES` | `15` | Sync interval in minutes |
| `SYNC_BATCH_SIZE` | `50` | Number of records per batch |

### Encryption

| Variable | Default | Description |
|----------|---------|-------------|
| `SETTINGS_ENCRYPTION_KEY` | - | Fernet encryption key for sensitive settings |

**Generate encryption key**:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## Setup Instructions

### Development Environment

1. **Copy the example file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your credentials**:
   ```bash
   # Use your preferred editor
   nano .env
   # OR
   notepad .env
   ```

3. **Set required Walmart EDR credentials**:
   ```env
   WALMART_EDR_USERNAME=your_actual_email@example.com
   WALMART_EDR_PASSWORD=your_actual_password
   WALMART_EDR_MFA_CREDENTIAL_ID=your_actual_mfa_id
   ```

4. **Verify setup**:
   ```bash
   python -c "from scheduler_app.config import get_config; print('Config loaded successfully!')"
   ```

   If credentials are missing, you'll see:
   ```
   ValueError: Missing required environment variables: WALMART_EDR_USERNAME, ...
   ```

### Production Environment

**DO NOT use `.env` files in production!** Instead, set environment variables directly:

#### Linux/Unix (systemd service)
```ini
# /etc/systemd/system/scheduler-app.service
[Service]
Environment="FLASK_ENV=production"
Environment="SECRET_KEY=your-production-secret-key"
Environment="DATABASE_URL=postgresql://user:pass@localhost/scheduler"
Environment="WALMART_EDR_USERNAME=production_user@example.com"
Environment="WALMART_EDR_PASSWORD=production_password"
Environment="WALMART_EDR_MFA_CREDENTIAL_ID=production_mfa_id"
```

#### Docker
```dockerfile
# docker-compose.yml
services:
  app:
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
      - WALMART_EDR_USERNAME=${WALMART_EDR_USERNAME}
      - WALMART_EDR_PASSWORD=${WALMART_EDR_PASSWORD}
      - WALMART_EDR_MFA_CREDENTIAL_ID=${WALMART_EDR_MFA_CREDENTIAL_ID}
```

#### Cloud Platforms
- **AWS**: Use AWS Secrets Manager or Parameter Store
- **Azure**: Use Azure Key Vault
- **Google Cloud**: Use Secret Manager
- **Heroku**: Use Config Vars in dashboard

---

## Security Best Practices

### 1. Never Commit Credentials
- ✅ `.env` is in `.gitignore`
- ✅ Use `.env.example` as template (no real values)
- ❌ Never commit `.env` or any file with real credentials

### 2. Rotate Credentials Regularly
- Rotate Walmart EDR credentials every 90 days
- Update production environment variables after rotation
- Document rotation in security log

### 3. Use Secrets Management in Production
- **Don't** store production secrets in `.env` files
- **Do** use cloud provider secrets management
- **Do** implement automated secret rotation

### 4. Limit Access
- Only authorized personnel should have access to credentials
- Use separate credentials for development, staging, and production
- Implement role-based access control (RBAC)

### 5. Monitor Credential Usage
- Enable audit logging for EDR API access
- Monitor for unusual access patterns
- Set up alerts for failed authentication attempts

---

## Troubleshooting

### Error: "Missing required environment variables"

**Cause**: Required credentials not set in environment

**Solution**:
1. Check that `.env` file exists in project root
2. Verify all required variables are set:
   ```bash
   cat .env | grep WALMART_EDR
   ```
3. Ensure no typos in variable names
4. Restart application after updating `.env`

### Error: "Authentication failed" (Walmart EDR)

**Cause**: Incorrect credentials or expired password

**Solution**:
1. Verify credentials are correct
2. Check if MFA credential ID is valid
3. Try logging in manually to Walmart Retail Link
4. Contact Walmart administrator if password expired

### Application starts but EDR features don't work

**Cause**: Credentials set but incorrect

**Solution**:
1. Test credentials manually in browser
2. Check MFA setup is correct
3. Review EDR service logs for error details
4. Verify network access to Walmart Retail Link

---

## Environment Variable Validation

The application validates required environment variables at startup. For non-testing environments, the following are checked:

```python
# Required variables (will raise ValueError if missing)
WALMART_EDR_USERNAME
WALMART_EDR_PASSWORD
WALMART_EDR_MFA_CREDENTIAL_ID
```

**Testing Environment**: Validation is skipped for `FLASK_ENV=testing` to allow unit tests to run without credentials.

---

## Credential Rotation Procedure

When credentials need to be rotated (security incident, regular rotation, employee departure):

1. **Generate new credentials**:
   - Contact Walmart Retail Link administrator
   - Request new password and MFA credential
   - Document in security log

2. **Update environment variables**:
   ```bash
   # Development
   nano .env  # Update values

   # Production
   # Update via cloud secrets manager or service configuration
   ```

3. **Test with new credentials**:
   ```bash
   python -c "from scheduler_app.edr.authentication import authenticate; authenticate()"
   ```

4. **Deploy to production**:
   - Update production environment variables
   - Restart application services
   - Monitor logs for authentication success

5. **Revoke old credentials**:
   - Contact administrator to disable old account
   - Confirm revocation
   - Document completion

---

## References

- [12-Factor App: Config](https://12factor.net/config)
- [OWASP: Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [Python Decouple Documentation](https://github.com/henriquebastos/python-decouple)

---

**Document Owner**: Dev Team
**Last Reviewed**: 2025-01-09
**Next Review**: 2025-04-09
