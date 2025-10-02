# Setup Scripts Documentation

Complete documentation for the Flask Schedule Webapp setup and start scripts.

---

## Overview

The setup system includes automated scripts for both Windows and Linux/Mac environments that handle:
- Virtual environment creation
- Dependency installation
- Directory structure setup
- Environment configuration
- Database initialization

---

## Files Created

### Setup Scripts

1. **setup.bat** (Windows)
   - Location: Project root
   - Purpose: Automated setup for Windows users
   - Features:
     - Python version check
     - Virtual environment creation
     - Dependency installation
     - Directory creation
     - .env file generation
     - Optional database initialization

2. **setup.sh** (Linux/Mac)
   - Location: Project root
   - Purpose: Automated setup for Unix-based systems
   - Features: Same as setup.bat
   - Permissions: Executable (`chmod +x setup.sh`)

### Start Scripts

3. **start.bat** (Windows)
   - Location: Project root
   - Purpose: Quick start script for Windows
   - Features:
     - Virtual environment activation
     - Environment variable setup
     - Flask application launch

4. **start.sh** (Linux/Mac)
   - Location: Project root
   - Purpose: Quick start script for Unix-based systems
   - Features: Same as start.bat
   - Permissions: Executable (`chmod +x start.sh`)

### Documentation

5. **SETUP.md**
   - Comprehensive setup guide
   - Sections:
     - Prerequisites
     - Quick start (automated)
     - Manual setup instructions
     - Configuration guide
     - Database setup
     - Running the application
     - Troubleshooting
     - Production deployment checklist

6. **QUICK_START.md**
   - Quick reference card
   - Sections:
     - 5-minute setup instructions
     - Common commands
     - Key features to try
     - Configuration essentials
     - Quick troubleshooting table
     - Directory structure
     - Security reminders

7. **.gitignore**
   - Comprehensive Git ignore rules
   - Excludes:
     - Virtual environments
     - Environment files (.env)
     - Database files
     - Logs
     - IDE settings
     - OS-specific files
     - Temporary files
     - Compiled Python files

---

## Setup Script Features

### Automated Checks

Both setup scripts perform the following checks:

1. **Python Installation**
   - Verifies Python is installed
   - Displays version information
   - Exits with error if Python not found

2. **Virtual Environment**
   - Checks if venv already exists
   - Creates new venv if needed
   - Skips if already present

3. **Dependencies**
   - Upgrades pip to latest version
   - Installs all requirements from requirements.txt
   - Handles installation errors

4. **Directory Structure**
   - Creates `scheduler_app/instance/` (database location)
   - Creates `scheduler_app/logs/` (log files)
   - Creates `scheduler_app/uploads/` (uploaded files)
   - Creates `edr_printer/` (EDR output)

5. **Environment Configuration**
   - Generates template .env file
   - Includes all necessary variables
   - Preserves existing .env if present

6. **Database Initialization**
   - Optional interactive prompt
   - Creates all database tables
   - Handles initialization errors

---

## Usage Workflows

### First-Time Setup Workflow

#### Windows:
```
1. Double-click setup.bat
2. Wait for completion
3. Edit .env file
4. Double-click start.bat
5. Open http://127.0.0.1:5000
```

#### Linux/Mac:
```
1. chmod +x setup.sh start.sh
2. ./setup.sh
3. Edit .env file
4. ./start.sh
5. Open http://127.0.0.1:5000
```

### Daily Use Workflow

**Windows:**
```
Double-click start.bat
```

**Linux/Mac:**
```
./start.sh
```

### Update Dependencies Workflow

**Windows:**
```cmd
venv\Scripts\activate
pip install -r requirements.txt
```

**Linux/Mac:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

## Environment Variables

### Required Variables

The setup scripts create a .env template with these variables:

```bash
# Flask Configuration
FLASK_APP=scheduler_app.app:create_app
FLASK_ENV=development
SECRET_KEY=change-this-to-a-random-secret-key-in-production

# Database Configuration
DATABASE_URL=sqlite:///instance/scheduler.db

# Crossmark API Configuration
CROSSMARK_API_URL=https://api.crossmark.com
CROSSMARK_USERNAME=your_username_here
CROSSMARK_PASSWORD=your_password_here

# Sync Configuration
SYNC_ENABLED=false
AUTO_SYNC_INTERVAL=3600

# Logging
LOG_LEVEL=INFO
LOG_FILE=scheduler_app/logs/app.log
```

### Variable Descriptions

| Variable | Purpose | Default | Production Notes |
|----------|---------|---------|------------------|
| FLASK_APP | Application entry point | scheduler_app.app:create_app | Don't change |
| FLASK_ENV | Environment mode | development | Set to `production` |
| SECRET_KEY | Session encryption | (random) | Generate secure key |
| DATABASE_URL | Database connection | SQLite | Use PostgreSQL |
| CROSSMARK_API_URL | External API endpoint | (example) | Set if using sync |
| CROSSMARK_USERNAME | API username | (placeholder) | Set if using sync |
| CROSSMARK_PASSWORD | API password | (placeholder) | Set if using sync |
| SYNC_ENABLED | Enable external sync | false | Set to true with valid credentials |
| AUTO_SYNC_INTERVAL | Sync frequency (seconds) | 3600 | Adjust as needed |
| LOG_LEVEL | Logging verbosity | INFO | DEBUG, INFO, WARNING, ERROR |
| LOG_FILE | Log file location | scheduler_app/logs/app.log | Adjust as needed |

---

## Error Handling

### Common Setup Errors

#### 1. Python Not Found
**Error:** `Python is not installed or not in PATH`
**Solution:**
- Install Python 3.11+ from python.org
- Ensure "Add Python to PATH" is checked during installation
- Restart terminal/command prompt after installation

#### 2. Permission Denied (Linux/Mac)
**Error:** `Permission denied` when running scripts
**Solution:**
```bash
chmod +x setup.sh start.sh
```

#### 3. Virtual Environment Creation Failed
**Error:** `Failed to create virtual environment`
**Solution:**
- Ensure sufficient disk space
- Check Python installation is complete
- Try manual venv creation:
  ```bash
  python -m venv venv
  ```

#### 4. Dependency Installation Failed
**Error:** `Failed to install dependencies`
**Solution:**
- Check internet connection
- Update pip: `pip install --upgrade pip`
- Install dependencies individually to identify problem package

#### 5. Database Initialization Failed
**Error:** `Database initialization failed`
**Solution:**
- Check `scheduler_app/instance/` directory exists
- Ensure no existing database file is locked
- Check Python import paths
- Try manual initialization (see SETUP.md)

---

## Directory Structure After Setup

```
flask-schedule-webapp/
├── scheduler_app/
│   ├── instance/              # Created by setup
│   │   └── scheduler.db      # Created by DB init
│   ├── logs/                 # Created by setup
│   │   └── app.log          # Created on first run
│   ├── uploads/              # Created by setup
│   ├── models/
│   ├── routes/
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   ├── templates/
│   └── app.py
├── edr_printer/              # Created by setup
├── docs/
├── venv/                     # Created by setup
├── .env                      # Created by setup
├── .gitignore               # Created for version control
├── setup.bat                # Windows setup
├── setup.sh                 # Linux/Mac setup
├── start.bat                # Windows start
├── start.sh                 # Linux/Mac start
├── requirements.txt
├── SETUP.md                 # Full setup guide
└── QUICK_START.md          # Quick reference
```

---

## Customization

### Custom Setup Steps

To add custom setup steps, edit the setup scripts:

**Windows (setup.bat):**
```batch
REM Add after line 60 (before database init)
echo.
echo [Custom Step] Running custom setup...
python custom_setup_script.py
```

**Linux/Mac (setup.sh):**
```bash
# Add after line 60 (before database init)
echo ""
echo "[Custom Step] Running custom setup..."
python3 custom_setup_script.py
```

### Custom Start Options

To modify startup behavior, edit start scripts:

**Example: Add custom port**
```batch
REM Windows (start.bat)
python -m flask run --host=0.0.0.0 --port=8080
```

```bash
# Linux/Mac (start.sh)
python -m flask run --host=0.0.0.0 --port=8080
```

---

## Testing the Setup

### Verify Installation

Run these commands to verify setup:

```bash
# Activate virtual environment
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Check Python version
python --version

# Check installed packages
pip list

# Verify Flask is installed
flask --version

# Run test suite
pytest test_search.py -v
```

### Expected Results

✅ Python 3.11 or higher
✅ Flask installed and version displayed
✅ All dependencies from requirements.txt installed
✅ Test suite passes (22/22 tests)

---

## Maintenance

### Update Dependencies

```bash
# Activate venv
pip install --upgrade -r requirements.txt
```

### Regenerate .env

```bash
# Backup current .env
mv .env .env.backup

# Run setup again (will create new .env)
# Windows: setup.bat
# Linux/Mac: ./setup.sh

# Restore your customizations from .env.backup
```

### Reset Application

```bash
# Remove virtual environment
rm -rf venv/  # Linux/Mac
rmdir /s venv  # Windows

# Remove database
rm scheduler_app/instance/scheduler.db  # Linux/Mac
del scheduler_app\instance\scheduler.db  # Windows

# Re-run setup
./setup.sh  # Linux/Mac
setup.bat   # Windows
```

---

## Production Deployment

### Pre-deployment Checklist

- [ ] Update SECRET_KEY to secure random value
- [ ] Set FLASK_ENV=production
- [ ] Configure production database (PostgreSQL)
- [ ] Enable HTTPS/SSL
- [ ] Set up reverse proxy (nginx/Apache)
- [ ] Configure firewall rules
- [ ] Set up automatic backups
- [ ] Configure monitoring/logging
- [ ] Review and restrict file permissions
- [ ] Set up process manager (systemd/supervisor)

### Production Start

Don't use the start scripts in production. Instead:

```bash
# Install production server
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "scheduler_app.app:create_app()"

# Or use systemd service (recommended)
# See docs/production-deployment.md (if exists)
```

---

## Support

### Getting Help

1. **Check logs:** `scheduler_app/logs/app.log`
2. **Review documentation:** SETUP.md, QUICK_START.md
3. **Run diagnostics:** `pytest -v`
4. **Check GitHub issues**
5. **Review environment:** `.env` file

### Reporting Issues

When reporting setup issues, include:
- OS and version
- Python version (`python --version`)
- Error messages
- Steps to reproduce
- Contents of error logs

---

**Script Version:** 1.0
**Last Updated:** January 2025
**Compatible Python:** 3.11+
**Compatible OS:** Windows 10/11, macOS 10.14+, Linux
