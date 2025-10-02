# Enhancement #2: Environment Configuration Security

**Priority**: 🔴 P0 - Critical Security Issue
**Effort**: Low (1-2 hours)
**Impact**: High - Prevents credential exposure

---

## **Why This Enhancement Matters**

**Current Problem:**
- `.env` file contains sensitive credentials (API passwords, secret keys)
- `.env` is tracked in Git repository
- Anyone with repo access can see production credentials
- Risk of accidental credential exposure to public GitHub, etc.

**Security Risks:**
1. **Credential Theft**: API keys exposed in version control
2. **Unauthorized Access**: Attackers can access external systems
3. **Compliance Violations**: GDPR, SOC2, PCI require credential protection
4. **Audit Trail Loss**: Can't track who accessed credentials when

**Goal**: Remove secrets from version control while maintaining easy local development setup.

---

## **System Prompt for AI Agent**

```
You are securing environment configuration for a Flask application.

CRITICAL SECURITY RULES:
1. NEVER commit .env files with real credentials
2. ALWAYS use .env.example with placeholder values
3. Git history must be cleaned - removing .env from past commits
4. Verify .gitignore blocks .env before proceeding

MOST IMPORTANT:
- Check if .env is already in Git history
- If yes, use git filter-branch or BFG Repo Cleaner to remove it
- Verify credentials are rotated after exposure
- Document setup steps for new developers

IGNORE/REMOVE FROM CONTEXT:
- Actual credential values - use placeholders only
- Historical .env contents - focus on current state
```

---

## **Step-by-Step Implementation Guide**

### **Phase 1: Assess Current Exposure**

#### **Step 1.1: Check Git Status**

**System Prompt:**
```
Check if .env is currently tracked by Git.
Determine if it exists in Git history (even if currently ignored).
Report findings before proceeding.
```

**Actions:**
```bash
cd /c/Users/mathe/flask-schedule-webapp/scheduler_app

# Check current Git status
git status | grep .env

# Check if .env is in Git history
git log --all --full-history --oneline -- .env

# Check if .env is in .gitignore
grep -n "\.env" ../.gitignore

# Check current .env file location
ls -la .env
```

**Possible Outcomes:**

**Scenario A: .env is tracked and in history**
```
Output: modified:   scheduler_app/.env
        commit abc123 Added environment configuration
```
→ **CRITICAL**: Must remove from history and rotate credentials

**Scenario B: .env exists but is ignored**
```
Output: .env (untracked)
```
→ **MODERATE**: Add to .gitignore, no history cleanup needed

**Scenario C: .env already in .gitignore**
```
Output: .gitignore:5:.env
```
→ **GOOD**: Already protected, verify it's working

---

#### **Step 1.2: Document Current Credentials**

**System Prompt:**
```
Read the current .env file and document what credentials exist.
DO NOT output actual credential values - only field names.
This helps determine what needs to be rotated if exposed.
```

**Actions:**
```bash
# List environment variable names (not values)
grep -E "^[A-Z_]+=" .env | cut -d= -f1
```

**Expected Output:**
```
SECRET_KEY
DATABASE_URL
EXTERNAL_API_BASE_URL
EXTERNAL_API_USERNAME
EXTERNAL_API_PASSWORD
EXTERNAL_API_TIMEZONE
SYNC_ENABLED
LOG_LEVEL
```

**Create credential inventory:**
```
- SECRET_KEY: Flask session encryption
- EXTERNAL_API_USERNAME: Crossmark API user
- EXTERNAL_API_PASSWORD: Crossmark API password
```

---

### **Phase 2: Remove .env from Git**

#### **Step 2.1: Add .env to .gitignore**

**System Prompt:**
```
Add comprehensive environment file patterns to .gitignore.
Include common variations (.env.local, .env.production, etc.).
Verify .gitignore is in the repository root.
```

**Check if .gitignore exists:**
```bash
cd /c/Users/mathe/flask-schedule-webapp

# Check for existing .gitignore
ls -la .gitignore

# If it doesn't exist, create it
touch .gitignore
```

**Add environment file patterns:**

Create or edit `.gitignore`:

```bash
# Add to .gitignore
cat >> .gitignore << 'EOF'

# Environment files - NEVER commit these
.env
.env.local
.env.*.local
.env.development
.env.production
.env.test
*.env
.env.*
!.env.example

# Python virtual environment
venv/
env/
ENV/

# Instance folder (contains SQLite database)
instance/
*.db
*.sqlite
*.sqlite3

# Logs
*.log
logs/

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db

# Sensitive data
cookies.txt
session_cookies.txt
*.har

EOF
```

**Why This Pattern:**
- `.env*` catches all variations
- `!.env.example` allows example file (useful for docs)
- Includes other sensitive files (cookies, logs, etc.)

**Verify .gitignore works:**
```bash
# This should show .env is ignored
git check-ignore -v .env

# Expected output:
# .gitignore:2:.env    .env
```

---

#### **Step 2.2: Remove .env from Git Tracking**

**System Prompt:**
```
Remove .env from Git tracking WITHOUT deleting the local file.
This preserves local development setup while protecting the repo.
```

**Actions:**
```bash
# Remove from Git index but keep local file
git rm --cached scheduler_app/.env

# Verify it's untracked now
git status

# Should show:
# deleted:    scheduler_app/.env
```

**Commit the change:**
```bash
git add .gitignore
git commit -m "Security: Remove .env from version control

- Added comprehensive .env patterns to .gitignore
- Removed .env from Git tracking
- Local .env files preserved for development
- See .env.example for required configuration"
```

---

#### **Step 2.3: Remove .env from Git History (If Exposed)**

**System Prompt:**
```
IF .env was found in Git history (Step 1.1), remove it completely.
This is CRITICAL for security - exposed credentials remain in history.

WARNING: This rewrites Git history. Coordinate with team first.
Only proceed if you have permission to force-push.
```

**Option A: BFG Repo Cleaner (Recommended - Faster)**

```bash
# Install BFG (if not installed)
# Windows with Scoop:
scoop install bfg

# Or download from: https://rtyley.github.io/bfg-repo-cleaner/

# Backup repository first
cd /c/Users/mathe/flask-schedule-webapp
cp -r ../flask-schedule-webapp ../flask-schedule-webapp-backup

# Run BFG to remove .env from all history
bfg --delete-files .env

# Clean up Git references
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Verify .env is gone from history
git log --all --full-history -- scheduler_app/.env
# Should return empty
```

**Option B: git filter-branch (Built-in, Slower)**

```bash
# Backup first
cd /c/Users/mathe/flask-schedule-webapp
cp -r ../flask-schedule-webapp ../flask-schedule-webapp-backup

# Remove .env from entire history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch scheduler_app/.env" \
  --prune-empty --tag-name-filter cat -- --all

# Clean up references
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Verify removal
git log --all --full-history -- scheduler_app/.env
```

**Force push (if this is a shared repo - COORDINATE WITH TEAM):**
```bash
# WARNING: This overwrites remote history
# All team members must re-clone or rebase

git push origin --force --all
git push origin --force --tags
```

**Why This Matters:**
- Git history is permanent - exposed credentials stay accessible
- Attackers can view old commits to find credentials
- Compliance requires complete credential removal

---

### **Phase 3: Create .env.example Template**

#### **Step 3.1: Create Example Environment File**

**System Prompt:**
```
Create .env.example with placeholder values.
Include comments explaining each variable.
Use fake but realistic-looking values.
```

**Create scheduler_app/.env.example:**

```bash
cat > scheduler_app/.env.example << 'EOF'
# Flask Schedule Webapp - Environment Configuration Template
# Copy this file to .env and fill in your actual values
# NEVER commit .env to version control

# =============================================================================
# Flask Application Settings
# =============================================================================

# Flask secret key - Generate with: python -c "import secrets; print(secrets.token_hex(32))"
# CRITICAL: Change this in production!
SECRET_KEY=your-secret-key-here-generate-a-random-string

# Flask environment (development, testing, production)
FLASK_ENV=development

# Database URL
# Development: sqlite:///instance/scheduler.db
# Production: Use PostgreSQL or MySQL
DATABASE_URL=sqlite:///instance/scheduler.db

# =============================================================================
# External API Configuration (Crossmark MVRetail)
# =============================================================================

# Base URL for external scheduling API
EXTERNAL_API_BASE_URL=https://crossmark.mvretail.com

# API authentication credentials
# Contact your API administrator for these values
EXTERNAL_API_USERNAME=your.username
EXTERNAL_API_PASSWORD=your-secure-password

# Timezone for API operations (IANA timezone format)
EXTERNAL_API_TIMEZONE=America/Indiana/Indianapolis

# API request settings
EXTERNAL_API_TIMEOUT=30
EXTERNAL_API_MAX_RETRIES=3
EXTERNAL_API_RETRY_DELAY=1

# Session refresh interval in seconds (default: 1 hour)
SESSION_REFRESH_INTERVAL=3600

# =============================================================================
# Synchronization Settings
# =============================================================================

# Enable/disable automatic sync with external API
SYNC_ENABLED=false

# Sync interval in minutes
SYNC_INTERVAL_MINUTES=15

# Number of records to sync per batch
SYNC_BATCH_SIZE=50

# =============================================================================
# Logging Configuration
# =============================================================================

# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Log file path (relative to scheduler_app directory)
LOG_FILE=logs/scheduler.log

# =============================================================================
# Security Settings
# =============================================================================

# Session cookie settings (for production)
# SESSION_COOKIE_SECURE=true
# SESSION_COOKIE_HTTPONLY=true
# SESSION_COOKIE_SAMESITE=Lax

# CSRF protection (uncomment for production)
# WTF_CSRF_ENABLED=true

EOF
```

**Why This Format:**
- Grouped by functional area = easy to understand
- Comments explain purpose of each variable
- Examples show expected format
- Security warnings prevent common mistakes

---

#### **Step 3.2: Update Documentation**

**System Prompt:**
```
Update README.md with clear instructions for environment setup.
Emphasize security best practices.
```

**Add to README.md:**

```markdown
## Environment Configuration

### Initial Setup

1. **Copy environment template:**
   ```bash
   cd scheduler_app
   cp .env.example .env
   ```

2. **Generate secure secret key:**
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

3. **Edit .env file:**
   ```bash
   nano .env  # or your preferred editor
   ```

4. **Required values:**
   - `SECRET_KEY`: Use generated value from step 2
   - `EXTERNAL_API_USERNAME`: Your Crossmark API username
   - `EXTERNAL_API_PASSWORD`: Your Crossmark API password

5. **Optional settings:**
   - `SYNC_ENABLED`: Set to `true` to enable automatic sync
   - `LOG_LEVEL`: Use `DEBUG` for development, `INFO` for production

### Security Best Practices

⚠️ **NEVER commit .env files to version control**

- `.env` contains sensitive credentials
- Use `.env.example` for documentation only
- Rotate credentials immediately if accidentally exposed
- Use environment variables in production (not .env files)

### Production Deployment

For production environments:

1. **Use proper secrets management:**
   - AWS Secrets Manager
   - HashiCorp Vault
   - Azure Key Vault
   - Environment variables in hosting platform

2. **Enable security settings:**
   ```bash
   FLASK_ENV=production
   SESSION_COOKIE_SECURE=true
   WTF_CSRF_ENABLED=true
   ```

3. **Use strong database:**
   ```bash
   DATABASE_URL=postgresql://user:pass@host:5432/dbname
   ```
```

---

### **Phase 4: Credential Rotation (If Exposed)**

#### **Step 4.1: Rotate Compromised Credentials**

**System Prompt:**
```
IF credentials were exposed in Git history, they MUST be rotated.
This is non-negotiable for security.
```

**Credentials to Rotate:**

**1. SECRET_KEY:**
```bash
# Generate new secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Copy output and update .env:
SECRET_KEY=<new-generated-key>
```

**2. EXTERNAL_API_PASSWORD:**
```
1. Log into Crossmark admin panel
2. Navigate to user management
3. Change password for API user account
4. Update .env with new password
```

**3. Database Credentials (if exposed):**
```
1. Access database admin panel
2. Create new database user with strong password
3. Grant same permissions as old user
4. Update .env with new credentials
5. Test application works
6. Revoke access for old user
```

**Why Immediate Rotation:**
- Git history is public once pushed
- Credentials may have been compromised
- Better safe than breached

---

#### **Step 4.2: Verify Security**

**System Prompt:**
```
Run security verification checks to ensure .env is protected.
```

**Verification Checklist:**

```bash
cd /c/Users/mathe/flask-schedule-webapp

# 1. Verify .env is ignored
git check-ignore -v scheduler_app/.env
# Should show: .gitignore:X:.env    scheduler_app/.env

# 2. Verify .env is not in staging
git status | grep .env
# Should NOT appear in "Changes to be committed"

# 3. Verify .env is not in history
git log --all --oneline -- scheduler_app/.env
# Should return empty

# 4. Verify .env.example exists and is tracked
git ls-files | grep .env.example
# Should show: scheduler_app/.env.example

# 5. Test application still works
cd scheduler_app
python app.py
# Should start without errors
```

**All checks passed?**
✅ Security hardening complete
✅ Credentials protected
✅ Development workflow maintained

---

### **Phase 5: Team Communication**

#### **Step 5.1: Notify Team (If Shared Repository)**

**System Prompt:**
```
If this is a team repository, create communication for developers.
Explain changes and required actions.
```

**Email/Slack Template:**

```
Subject: ACTION REQUIRED - Environment Configuration Security Update

Team,

We've updated the repository security to protect sensitive credentials:

WHAT CHANGED:
- .env files are now ignored by Git
- Historical .env data removed from repository
- .env.example added as configuration template

ACTION REQUIRED:
1. Pull latest changes: git pull origin main
2. Copy template: cp scheduler_app/.env.example scheduler_app/.env
3. Fill in your credentials (check password manager or ask admin)
4. Verify app works: cd scheduler_app && python app.py

IMPORTANT:
- NEVER commit .env files
- Use .env.example for documentation only
- Contact [admin] if you need API credentials

If you committed .env in the past:
- Your local repo history was rewritten
- You may need to: git fetch --all && git reset --hard origin/main
- Back up local changes first!

Questions? Reply to this thread.

Security Team
```

---

### **Phase 6: Continuous Security**

#### **Step 6.1: Add Pre-commit Hook (Optional)**

**System Prompt:**
```
Add Git pre-commit hook to prevent accidental .env commits.
This is a safety net for developers.
```

**Create .git/hooks/pre-commit:**

```bash
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/sh
# Pre-commit hook to prevent .env file commits

# Check for .env files being committed
if git diff --cached --name-only | grep -E "\.env$|\.env\..*$" | grep -v "\.env\.example"; then
    echo "❌ ERROR: Attempting to commit .env file!"
    echo ""
    echo "Environment files contain sensitive credentials."
    echo "They should NEVER be committed to version control."
    echo ""
    echo "Files blocked:"
    git diff --cached --name-only | grep -E "\.env$|\.env\..*$" | grep -v "\.env\.example"
    echo ""
    echo "To fix:"
    echo "  1. Remove from staging: git reset HEAD <file>"
    echo "  2. Ensure .gitignore includes .env patterns"
    echo "  3. Use .env.example for documentation"
    echo ""
    exit 1
fi

# Check for potential secrets in any file
if git diff --cached | grep -E "SECRET_KEY=|PASSWORD=|API_KEY=" | grep -v "\.env\.example"; then
    echo "⚠️  WARNING: Potential secrets detected in staged files"
    echo ""
    echo "Please verify you're not committing sensitive data:"
    git diff --cached | grep -E "SECRET_KEY=|PASSWORD=|API_KEY=" | grep -v "\.env\.example"
    echo ""
    echo "If these are placeholder values, you can proceed."
    echo "If these are real credentials, unstage them immediately!"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

exit 0
EOF

# Make executable
chmod +x .git/hooks/pre-commit
```

**Test the hook:**
```bash
# Try to commit .env (should fail)
git add scheduler_app/.env
git commit -m "Test"

# Should see error message and commit blocked
```

---

#### **Step 6.2: Add Secret Scanning (GitHub)**

**System Prompt:**
```
If using GitHub, enable secret scanning to detect exposed credentials.
```

**For GitHub repositories:**

1. Navigate to repository settings
2. Click "Security & analysis"
3. Enable "Secret scanning"
4. Enable "Push protection" (prevents commits with secrets)

**For GitLab:**
- Enable Secret Detection in CI/CD settings

**For Bitbucket:**
- Use secret scanning apps from marketplace

---

## **Verification & Testing**

### **Final Security Checklist**

```bash
# Run this verification script
cat > verify_security.sh << 'EOF'
#!/bin/bash

echo "=== Environment Security Verification ==="
echo ""

# Check 1: .env is ignored
echo "✓ Checking if .env is in .gitignore..."
if grep -q "\.env" .gitignore; then
    echo "  ✅ .env pattern found in .gitignore"
else
    echo "  ❌ .env NOT in .gitignore - add it!"
    exit 1
fi

# Check 2: .env is not tracked
echo "✓ Checking if .env is tracked by Git..."
if git ls-files | grep -q "scheduler_app/\.env$"; then
    echo "  ❌ .env is tracked - remove with: git rm --cached scheduler_app/.env"
    exit 1
else
    echo "  ✅ .env is not tracked"
fi

# Check 3: .env is not in history
echo "✓ Checking Git history for .env..."
if git log --all --full-history -- scheduler_app/.env | grep -q "commit"; then
    echo "  ⚠️  .env found in history - consider cleaning with BFG"
else
    echo "  ✅ .env not in history"
fi

# Check 4: .env.example exists
echo "✓ Checking for .env.example..."
if [ -f "scheduler_app/.env.example" ]; then
    echo "  ✅ .env.example exists"
else
    echo "  ❌ .env.example missing - create it!"
    exit 1
fi

# Check 5: .env file exists locally
echo "✓ Checking local .env exists..."
if [ -f "scheduler_app/.env" ]; then
    echo "  ✅ Local .env exists"
else
    echo "  ⚠️  Local .env missing - copy from .env.example"
fi

echo ""
echo "=== Security Verification Complete ==="
EOF

chmod +x verify_security.sh
./verify_security.sh
```

---

## **Summary & Best Practices**

### **What We Accomplished**

✅ Removed `.env` from version control
✅ Created `.env.example` template
✅ Updated `.gitignore` with comprehensive patterns
✅ Cleaned Git history (if needed)
✅ Documented setup process
✅ Added pre-commit hooks (optional)
✅ Enabled secret scanning (if using GitHub)

### **Developer Workflow Going Forward**

**New Developer Setup:**
```bash
git clone <repo>
cd flask-schedule-webapp/scheduler_app
cp .env.example .env
# Edit .env with real credentials
python app.py
```

**Daily Development:**
- `.env` is automatically ignored
- Changes to configuration go in `.env.example`
- Credentials never leave local machine

### **Production Deployment**

**Don't use .env in production!** Use:
- Cloud provider secret managers (AWS Secrets Manager, etc.)
- Container orchestration secrets (Kubernetes Secrets)
- Platform environment variables (Heroku Config Vars)

**Example production setup:**
```bash
# Set environment variables in production
export SECRET_KEY="production-secret-from-vault"
export DATABASE_URL="postgresql://..."
export EXTERNAL_API_PASSWORD="secure-password"

# Run app (reads from environment)
python app.py
```

---

## **Troubleshooting**

### **Problem: App won't start after changes**

```bash
# Verify .env exists
ls -la scheduler_app/.env

# If missing, copy from example
cp scheduler_app/.env.example scheduler_app/.env

# Edit with real values
nano scheduler_app/.env
```

### **Problem: .env still showing in git status**

```bash
# Clear Git cache
git rm -r --cached .
git add .
git commit -m "Fix .gitignore"
```

### **Problem: Team member committed .env**

```bash
# Immediately revert the commit
git revert <commit-hash>

# Remove from history
bfg --delete-files .env

# Rotate ALL credentials
# Force push cleaned history
git push --force
```

---

## **Estimated Time**

- **Basic implementation**: 30 minutes
- **History cleaning**: +30 minutes (if needed)
- **Team coordination**: +1 hour (if shared repo)
- **Credential rotation**: +30 minutes (if exposed)

**Total**: 1-2 hours depending on scope

---

## **Success Criteria**

✅ No .env files in Git repository
✅ .env.example provides clear template
✅ All developers can set up locally
✅ Pre-commit hooks prevent accidents
✅ Documentation explains security practices
✅ Credentials rotated if exposed
