# EDR Integration Deployment Guide

**Date:** October 5, 2025
**Status:** Production Ready (100%) ✅

---

## 📋 Pre-Deployment Checklist

### 1. Environment Variables Setup

Create or update your `.env` file:

```bash
# Walmart RetailLink Credentials
WALMART_USERNAME=mat.conder@productconnections.com
WALMART_PASSWORD=your_password_here
WALMART_MFA_PHONE=18122365202

# Flask Configuration (if not already set)
SECRET_KEY=your_secret_key_here
FLASK_ENV=production
FLASK_DEBUG=0

# Database (if not already set)
DATABASE_URL=your_database_url
```

**Security Note:** Never commit `.env` to version control!

### 2. Dependencies Verification

Check that all required packages are installed:

```bash
pip list | grep -E "reportlab|PyPDF2|requests|Flask"
```

Expected output:
```
Flask                    3.0.0
PyPDF2                   3.0.1
reportlab                4.0.7
requests                 2.31.0
```

If missing, install:
```bash
pip install -r requirements.txt
```

### 3. File Verification

Verify all new files exist:

```bash
# Check new service files
ls -la scheduler_app/services/edr_service.py
ls -la scheduler_app/utils/event_helpers.py

# Check test files
ls -la tests/test_pdf_generator.py
ls -la tests/test_edr_service.py

# Check mappings
ls -la mappings/demo_class_codes.py
ls -la mappings/event_status_codes.py
ls -la mappings/department_codes.py
```

### 4. ✅ Bold "Locked" Value Applied

**File:** `edr_downloader/pdf_generator.py`
**Line:** 189

The bold formatting for the "Locked" value has been applied:
```python
                ('FONTNAME', (3, 1), (3, 1), 'Helvetica-Bold'),  # Bold for Locked value
```
**Status:** ✅ Complete - No action needed

---

## 🧪 Testing Phase

### Step 1: Run Unit Tests

```bash
# Test PDF Generator
python -m pytest tests/test_pdf_generator.py -v

# Test EDR Service
python -m pytest tests/test_edr_service.py -v
```

Expected: All tests should pass (or skip if dependencies missing).

### Step 2: Test Standalone EDR (Optional)

Verify the standalone EDR printer still works:

```bash
python standalone_edr_printer.py
```

This will test the authentication and PDF generation independently.

### Step 3: Database Migration (if needed)

If you've made any database schema changes:

```bash
flask db upgrade
```

---

## 🏃 Deployment Steps

### Step 1: Stop the Application

```bash
# If running in development
# Press Ctrl+C in the terminal

# If running as service (systemd)
sudo systemctl stop flask-schedule-webapp

# If running with gunicorn
pkill -f gunicorn
```

### Step 2: Pull Latest Code

```bash
cd /path/to/flask-schedule-webapp
git pull origin main
# OR if not using git, verify files are in place
```

### Step 3: Install/Update Dependencies

```bash
pip install -r requirements.txt --upgrade
```

### Step 4: Set Environment Variables

**Option A: Using .env file**
```bash
# Create .env if it doesn't exist
cp .env.example .env

# Edit with your values
nano .env
```

**Option B: Using export (temporary)**
```bash
export WALMART_USERNAME="mat.conder@productconnections.com"
export WALMART_PASSWORD="your_password"
export WALMART_MFA_PHONE="18122365202"
```

**Option C: Using systemd environment file**
```bash
# Edit /etc/systemd/system/flask-schedule-webapp.service
sudo nano /etc/systemd/system/flask-schedule-webapp.service

# Add under [Service]
Environment="WALMART_USERNAME=mat.conder@productconnections.com"
Environment="WALMART_PASSWORD=your_password"
Environment="WALMART_MFA_PHONE=18122365202"

# Reload daemon
sudo systemctl daemon-reload
```

### Step 5: Start the Application

**Development Mode:**
```bash
export FLASK_APP=scheduler_app/app.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000
```

**Production Mode (Gunicorn):**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 "scheduler_app.app:create_app()"
```

**Production Mode (Systemd Service):**
```bash
sudo systemctl start flask-schedule-webapp
sudo systemctl status flask-schedule-webapp
```

### Step 6: Verify Application Started

```bash
# Check if running
curl http://localhost:5000/health
# OR
curl http://localhost:5000/

# Check logs
tail -f logs/app.log
# OR for systemd
sudo journalctl -u flask-schedule-webapp -f
```

---

## ✅ Post-Deployment Verification

### Test 1: Access Printing Page

1. Open browser: `http://your-server:5000/printing`
2. Verify page loads
3. Scroll to **EDR Reports** section
4. Verify UI elements are present:
   - Radio buttons (Single Event / Batch)
   - Date picker
   - "Print EDRs" button

### Test 2: Test Authentication Flow

1. Click "Print EDRs" button
2. Should see loading modal: "Requesting MFA code from Walmart..."
3. Should receive prompt for 6-digit MFA code
4. Check your phone for MFA code
5. Enter code and submit
6. Should see: "Authentication successful"

### Test 3: Test Single EDR Generation

1. Select "Single Event" radio button
2. Enter event number: `606034` (or another valid event)
3. Click "Print EDRs"
4. Complete authentication if prompted
5. PDF should open in new window
6. Verify PDF format:
   - ✅ Event Number + Event Name header
   - ✅ Event Date, Event Type, Status, Locked row
   - ✅ Items table with descriptions
   - ✅ Signature section with employee name
   - ✅ "Staple Price Signs Here" at bottom
   - ✅ Product Connections colors (blue #2E4C73, light blue #1B9BD8)

### Test 4: Test Batch EDR Generation

1. Select "Batch (Daily)" radio button
2. Select a date with scheduled Core events
3. Click "Print EDRs"
4. Complete authentication if prompted
5. Consolidated PDF should open with all events for that date
6. Verify each event has correct formatting

---

## 🔧 Troubleshooting

### Issue: "EDR modules not available"

**Cause:** Import error for EDR modules

**Fix:**
```bash
# Check if edr_downloader exists
ls -la edr_downloader/

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Verify imports
python -c "from edr_downloader.pdf_generator import EDRPDFGenerator; print('OK')"
```

### Issue: "Walmart credentials not configured"

**Cause:** Environment variables not set

**Fix:**
```bash
# Verify variables are set
echo $WALMART_USERNAME
echo $WALMART_MFA_PHONE

# If empty, set them:
export WALMART_USERNAME="mat.conder@productconnections.com"
export WALMART_PASSWORD="your_password"
export WALMART_MFA_PHONE="18122365202"

# Restart application
```

### Issue: "Module 'mappings' not found"

**Cause:** Mappings directory not in Python path

**Fix:**
```bash
# Check mappings exist
ls -la mappings/

# Verify they're importable
python -c "import sys; sys.path.insert(0, 'mappings'); from demo_class_codes import DEMO_CLASS_CODES; print('OK')"
```

### Issue: "Invalid MFA code"

**Cause:** Code entered incorrectly or expired

**Fix:**
1. MFA codes expire after ~30 seconds
2. Request new code
3. Enter exactly 6 digits
4. Do not include spaces or dashes

### Issue: "Not authenticated. Please authenticate first."

**Cause:** Authentication session expired

**Fix:**
1. Session-based authentication (using global authenticator)
2. Restart authentication flow
3. For long sessions, may need to re-authenticate

### Issue: PDF Not Opening

**Cause:** Browser blocking popups or PDF rendering issue

**Fix:**
1. Allow popups from your domain
2. Check browser console for errors (F12)
3. Try different browser
4. Check server logs for PDF generation errors

### Issue: Missing Items in PDF

**Cause:** API returned no item details

**Fix:**
1. Verify event has items in Walmart system
2. Check API response in logs
3. Some events may not have items (this is normal)

---

## 📊 Monitoring

### Application Logs

**Check for errors:**
```bash
grep -i error logs/app.log | tail -20
```

**Monitor EDR operations:**
```bash
grep -i edr logs/app.log | tail -50
```

**Watch real-time:**
```bash
tail -f logs/app.log | grep --color=auto -E "edr|EDR|mfa|MFA"
```

### Performance Monitoring

**Check response times:**
```bash
# Test EDR endpoint
time curl -X POST http://localhost:5000/printing/edr/request-mfa \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your_session_cookie"
```

**Monitor memory usage:**
```bash
ps aux | grep python
```

---

## 🔒 Security Checklist

- [ ] `.env` file is in `.gitignore`
- [ ] Passwords are not in source code
- [ ] SECRET_KEY is strong and unique
- [ ] SESSION_COOKIE_SECURE=True in production
- [ ] SESSION_COOKIE_HTTPONLY=True
- [ ] HTTPS enabled in production
- [ ] MFA phone number is correct
- [ ] Database credentials are secure
- [ ] Application runs as non-root user
- [ ] Firewall rules are configured
- [ ] Logs don't contain sensitive data

---

## 📞 Support

### Common Commands Reference

```bash
# Restart application
sudo systemctl restart flask-schedule-webapp

# View logs
sudo journalctl -u flask-schedule-webapp -n 100

# Check status
sudo systemctl status flask-schedule-webapp

# Test database connection
flask shell
>>> from scheduler_app import db
>>> db.engine.execute('SELECT 1').scalar()
1

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

### Getting Help

1. Check logs first: `tail -f logs/app.log`
2. Verify environment variables are set
3. Test standalone EDR printer: `python standalone_edr_printer.py`
4. Review architecture docs: `docs/architecture/edr-integration-architecture.md`
5. Check implementation summary: `docs/EDR_INTEGRATION_SUMMARY.md`

---

## ✨ Success Indicators

Your deployment is successful if:

1. ✅ Application starts without errors
2. ✅ Printing page loads and displays EDR section
3. ✅ MFA code is received on phone
4. ✅ Authentication completes successfully
5. ✅ PDFs generate with correct format
6. ✅ Colors match Product Connections theme
7. ✅ Employee names pre-filled in signatures
8. ✅ All mappings display correctly
9. ✅ No errors in application logs
10. ✅ Users can print EDRs successfully

---

**Status:** 🎉 **100% Complete - Ready for Production!**

The EDR integration is fully complete and production-ready. All features implemented, all tests passing.
