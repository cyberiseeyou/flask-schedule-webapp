# Flask Schedule Webapp - Setup Guide

Complete setup instructions for the Flask Schedule Webapp.

---

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Manual Setup](#manual-setup)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- **Python 3.11 or higher** - [Download Python](https://www.python.org/downloads/)
- **Git** (optional, for version control)

### System Requirements
- **OS:** Windows 10/11, macOS 10.14+, or Linux
- **RAM:** Minimum 2GB
- **Disk Space:** ~500MB for application and dependencies

---

## Quick Start

### Windows

1. **Run the setup script:**
   ```cmd
   setup.bat
   ```

2. **Configure the application:**
   - Edit `.env` file with your settings (see [Configuration](#configuration))

3. **Start the application:**
   ```cmd
   start.bat
   ```

4. **Open your browser:**
   - Navigate to: http://127.0.0.1:5000

### Linux/Mac

1. **Make scripts executable:**
   ```bash
   chmod +x setup.sh start.sh
   ```

2. **Run the setup script:**
   ```bash
   ./setup.sh
   ```

3. **Configure the application:**
   - Edit `.env` file with your settings (see [Configuration](#configuration))

4. **Start the application:**
   ```bash
   ./start.sh
   ```

5. **Open your browser:**
   - Navigate to: http://127.0.0.1:5000

---

## Manual Setup

If you prefer to set up manually or the scripts don't work:

### 1. Create Virtual Environment

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Create Required Directories

**Windows:**
```cmd
mkdir scheduler_app\instance
mkdir scheduler_app\logs
mkdir scheduler_app\uploads
mkdir edr_printer
```

**Linux/Mac:**
```bash
mkdir -p scheduler_app/instance
mkdir -p scheduler_app/logs
mkdir -p scheduler_app/uploads
mkdir -p edr_printer
```

### 4. Create Environment File

Create a `.env` file in the project root (see [Configuration](#configuration) section)

### 5. Initialize Database

**Windows:**
```cmd
cd scheduler_app
python -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.create_all()"
cd ..
```

**Linux/Mac:**
```bash
cd scheduler_app
python3 -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.create_all()"
cd ..
```

---

## Configuration

### Environment Variables (.env)

Create a `.env` file in the project root with the following variables:

```bash
# Flask Configuration
FLASK_APP=scheduler_app.app:create_app
FLASK_ENV=development
SECRET_KEY=your-secret-key-here-change-in-production

# Database Configuration
DATABASE_URL=sqlite:///instance/scheduler.db

# Crossmark API Configuration (if using external sync)
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

### Important Configuration Notes

1. **SECRET_KEY**:
   - Generate a secure random key for production:
     ```python
     python -c "import secrets; print(secrets.token_hex(32))"
     ```
   - Never commit the actual secret key to version control

2. **DATABASE_URL**:
   - Default uses SQLite (good for development)
   - For production, consider PostgreSQL:
     ```
     DATABASE_URL=postgresql://user:password@localhost/dbname
     ```

3. **SYNC_ENABLED**:
   - Set to `true` only if you have valid Crossmark API credentials
   - Leave as `false` for standalone operation

4. **FLASK_ENV**:
   - Use `development` for development
   - Use `production` for production deployment

---

## Database Setup

### Initialize Database

The setup scripts offer to initialize the database automatically. If you declined or need to reinitialize:

**Windows:**
```cmd
venv\Scripts\activate
cd scheduler_app
python -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.create_all(); print('Database initialized')"
cd ..
```

**Linux/Mac:**
```bash
source venv/bin/activate
cd scheduler_app
python3 -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.create_all(); print('Database initialized')"
cd ..
```

### Database Migrations

If you need to run migrations:

```bash
# Initialize migrations (first time only)
flask db init

# Create a migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade
```

### Reset Database

⚠️ **Warning: This will delete all data!**

**Windows:**
```cmd
del scheduler_app\instance\scheduler.db
setup.bat
```

**Linux/Mac:**
```bash
rm scheduler_app/instance/scheduler.db
./setup.sh
```

---

## Running the Application

### Using Start Scripts (Recommended)

**Windows:**
```cmd
start.bat
```

**Linux/Mac:**
```bash
./start.sh
```

### Using Flask CLI

**Windows:**
```cmd
venv\Scripts\activate
set FLASK_APP=scheduler_app.app:create_app
set FLASK_ENV=development
flask run
```

**Linux/Mac:**
```bash
source venv/bin/activate
export FLASK_APP=scheduler_app.app:create_app
export FLASK_ENV=development
flask run
```

### Custom Host/Port

```bash
flask run --host=0.0.0.0 --port=8080
```

### Production Deployment

For production, use a WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "scheduler_app.app:create_app()"
```

---

## Troubleshooting

### Common Issues

#### 1. "Python not found"
**Solution:**
- Install Python 3.11+ from [python.org](https://www.python.org/downloads/)
- Ensure Python is added to PATH during installation
- Try using `python3` instead of `python` on Linux/Mac

#### 2. "Module not found" errors
**Solution:**
```bash
# Ensure virtual environment is activated
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### 3. "Database locked" error
**Solution:**
- Close all connections to the database
- Restart the application
- If persists, consider using PostgreSQL instead of SQLite

#### 4. "Port already in use"
**Solution:**
```bash
# Find process using port 5000
# Windows: netstat -ano | findstr :5000
# Linux/Mac: lsof -i :5000

# Kill the process or use a different port
flask run --port=8080
```

#### 5. ".env file not loading"
**Solution:**
- Ensure `.env` is in the project root directory
- Install python-dotenv: `pip install python-dotenv`
- Check file permissions

#### 6. "Permission denied" on scripts (Linux/Mac)
**Solution:**
```bash
chmod +x setup.sh start.sh
```

### Test the Setup

Run the test suite to verify everything is working:

```bash
# Activate virtual environment first
pytest test_search.py -v
```

Expected result: All tests should pass

---

## Additional Setup Options

### Development Tools

Install additional development dependencies:

```bash
pip install pytest pytest-cov black flake8 mypy
```

### IDE Configuration

#### VS Code
Create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black"
}
```

#### PyCharm
1. File → Settings → Project → Python Interpreter
2. Add Interpreter → Existing Environment
3. Select `venv/bin/python` (or `venv\Scripts\python.exe` on Windows)

---

## Next Steps

After successful setup:

1. **Create an admin user** (if user authentication is enabled)
2. **Import employee data** via the UI or API
3. **Configure Crossmark API** (if using external sync)
4. **Test the search feature** at the events page
5. **Schedule some events** to see auto-scheduling in action
6. **Review the documentation** in `/docs` folder

---

## Getting Help

- **Documentation:** See `/docs` folder for detailed feature documentation
- **Issues:** Check existing issues or create a new one on GitHub
- **Logs:** Check `scheduler_app/logs/app.log` for detailed error messages

---

## Security Checklist for Production

- [ ] Change `SECRET_KEY` to a secure random value
- [ ] Set `FLASK_ENV=production`
- [ ] Use a production database (PostgreSQL recommended)
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall rules
- [ ] Set up regular database backups
- [ ] Review and update `.gitignore` to exclude sensitive files
- [ ] Use environment-specific `.env` files (never commit them)
- [ ] Set up logging and monitoring
- [ ] Configure CORS if needed

---

**Setup Version:** 1.0
**Last Updated:** January 2025
**Minimum Python Version:** 3.11
