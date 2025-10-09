@echo off
REM Flask Schedule WebApp Launcher

REM Set Python path to current directory
set PYTHONPATH=%CD%

REM Activate virtual environment
call venv\Scripts\activate

REM Run the Flask application
python scheduler_app\app.py

pause
