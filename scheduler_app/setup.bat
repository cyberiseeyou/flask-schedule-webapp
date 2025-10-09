@echo off
REM Flask Schedule Webapp - Windows Setup Script
REM This script sets up the application environment and dependencies

echo ========================================
echo Flask Schedule Webapp - Setup Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo [1/7] Checking Python version...
python --version

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo.
    echo [2/7] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
) else (
    echo.
    echo [2/7] Virtual environment already exists, skipping...
)

REM Activate virtual environment
echo.
echo [3/7] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Upgrade pip
echo.
echo [4/7] Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo.
echo [5/7] Installing dependencies from requirements.txt...
if exist "requirements.txt" (
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
) else (
    echo WARNING: requirements.txt not found, skipping dependency installation
)

REM Create necessary directories
echo.
echo [6/7] Creating necessary directories...
if not exist "scheduler_app\instance" mkdir scheduler_app\instance
if not exist "scheduler_app\logs" mkdir scheduler_app\logs
if not exist "scheduler_app\uploads" mkdir scheduler_app\uploads
if not exist "edr_printer" mkdir edr_printer

REM Setup environment file
echo.
echo [7/7] Setting up environment configuration...
if not exist ".env" (
    echo Creating .env file from template...
    (
        echo # Flask Schedule Webapp Configuration
        echo # Copy this file to .env and update with your actual values
        echo.
        echo # Flask Configuration
        echo FLASK_APP=scheduler_app.app:create_app
        echo FLASK_ENV=development
        echo SECRET_KEY=change-this-to-a-random-secret-key-in-production
        echo.
        echo # Database Configuration
        echo DATABASE_URL=sqlite:///instance/scheduler.db
        echo.
        echo # Crossmark API Configuration
        echo CROSSMARK_API_URL=https://api.crossmark.com
        echo CROSSMARK_USERNAME=your_username_here
        echo CROSSMARK_PASSWORD=your_password_here
        echo.
        echo # Sync Configuration
        echo SYNC_ENABLED=false
        echo AUTO_SYNC_INTERVAL=3600
        echo.
        echo # Logging
        echo LOG_LEVEL=INFO
        echo LOG_FILE=scheduler_app/logs/app.log
    ) > .env
    echo .env file created - Please update with your actual configuration values
) else (
    echo .env file already exists, skipping...
)

REM Initialize database
echo.
echo ========================================
echo Database Initialization
echo ========================================
echo.
echo Would you like to initialize the database now? (Y/N)
set /p INIT_DB="Enter your choice: "

if /i "%INIT_DB%"=="Y" (
    echo.
    echo Initializing database...
    cd scheduler_app
    python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database initialized successfully')"
    if errorlevel 1 (
        echo ERROR: Database initialization failed
        cd ..
        pause
        exit /b 1
    )
    cd ..
    echo Database initialized successfully
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Update .env file with your actual configuration values
echo 2. Run 'venv\Scripts\activate.bat' to activate the virtual environment
echo 3. Run 'python -m scheduler_app.app' to start the application
echo.
echo For development:
echo   set FLASK_APP=scheduler_app.app:create_app
echo   set FLASK_ENV=development
echo   flask run
echo.
echo Or use the start script:
echo   start.bat
echo.
pause
