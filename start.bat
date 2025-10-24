@echo off
REM Flask Schedule Webapp - Windows Start Script
REM Quick start script for running the application

echo ========================================
echo Flask Schedule Webapp - Starting...
echo ========================================
echo.

REM Check if virtual environment exists in parent or current directory
if exist "..\venv\Scripts\activate.bat" (
    call ..\venv\Scripts\activate.bat
) else if exist "..\.venv\Scripts\activate.bat" (
    call "..\.venv\Scripts\activate.bat"
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo ERROR: Virtual environment not found!
    echo Please run setup.bat first to set up the application.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo WARNING: .env file not found!
    echo Using default development configuration...
    echo.
)

REM Set Flask environment variables
set FLASK_APP=app:app
set FLASK_ENV=development

REM Start the application
echo Starting Flask application...
echo.
echo The application will be available at:
echo   http://127.0.0.1:5000
echo.
echo Press Ctrl+C to stop the server
echo.

python app.py

pause
