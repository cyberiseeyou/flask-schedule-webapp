@echo off
REM Flask Schedule Webapp - Windows Start Script
REM Quick start script for running the application

echo ========================================
echo Flask Schedule Webapp - Starting...
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run setup.bat first to set up the application.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if .env file exists
if not exist ".env" (
    echo WARNING: .env file not found!
    echo Using default development configuration...
    echo.
)

REM Set Flask environment variables
set FLASK_APP=scheduler_app.app:app
set FLASK_ENV=development

REM Start the application
echo Starting Flask application...
echo.
echo The application will be available at:
echo   http://127.0.0.1:5000
echo.
echo Press Ctrl+C to stop the server
echo.

python -m flask run --host=0.0.0.0 --port=5000

pause
