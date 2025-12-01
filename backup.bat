@echo off
REM Flask Schedule Webapp - Database Backup Script (Windows)
REM
REM This script provides database backup functionality with scheduling options
REM for PostgreSQL and SQLite databases.
REM
REM Usage:
REM   backup.bat                   - Interactive mode
REM   backup.bat --now             - Run backup immediately
REM   backup.bat --schedule        - Set up scheduled backups
REM   backup.bat --restore <file>  - Restore from backup file
REM   backup.bat --list            - List available backups

setlocal enabledelayedexpansion

REM Configuration
set BACKUP_DIR=backups
set RETENTION_DAYS=30
set DOCKER_DIR=deployment\docker

REM Banner
echo.
echo ===============================================================
echo.
echo          Flask Schedule Webapp - Database Backup
echo.
echo ===============================================================
echo.

REM Load environment variables from .env
if exist ".env" (
    for /f "tokens=1,2 delims==" %%a in (.env) do (
        set %%a=%%b
    )
)

REM Parse command line arguments
if "%1"=="--now" goto :run_backup_now
if "%1"=="--schedule" goto :setup_schedule
if "%1"=="--restore" goto :restore_backup
if "%1"=="--list" goto :list_backups
if "%1"=="--help" goto :show_help
if "%1"=="-h" goto :show_help
goto :show_menu

:show_menu
echo Detecting database configuration...

REM Detect database type
set DB_TYPE=none
docker ps --format "{{.Names}}" 2>nul | findstr /c:"scheduler-db" >nul 2>&1
if %ERRORLEVEL%==0 (
    set DB_TYPE=postgresql-docker
    echo [INFO] Detected: PostgreSQL ^(Docker^)
) else if exist "instance\scheduler.db" (
    set DB_TYPE=sqlite
    echo [INFO] Detected: SQLite
) else (
    echo [WARNING] No database detected
)

echo.
echo Select an option:
echo   1^) Run backup now
echo   2^) Set up scheduled backups ^(Windows Task Scheduler^)
echo   3^) Restore from backup
echo   4^) List available backups
echo   5^) Clean old backups
echo   6^) Exit
echo.
set /p OPTION="Select option [1-6]: "

if "%OPTION%"=="1" goto :run_backup_interactive
if "%OPTION%"=="2" goto :setup_schedule
if "%OPTION%"=="3" goto :restore_interactive
if "%OPTION%"=="4" goto :list_backups
if "%OPTION%"=="5" goto :cleanup_backups
if "%OPTION%"=="6" goto :exit_script
echo [ERROR] Invalid option
goto :eof

:run_backup_interactive
echo.
set /p INPUT_DIR="Backup directory [%BACKUP_DIR%]: "
if not "%INPUT_DIR%"=="" set BACKUP_DIR=%INPUT_DIR%
goto :run_backup

:run_backup_now
set BACKUP_DIR=backups
if "%2"=="--dir" set BACKUP_DIR=%3
goto :run_backup

:run_backup
REM Create backup directory if it doesn't exist
if not exist "%BACKUP_DIR%" (
    mkdir "%BACKUP_DIR%"
    echo [SUCCESS] Created backup directory: %BACKUP_DIR%
)

REM Generate timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set TIMESTAMP=%datetime:~0,4%%datetime:~4,2%%datetime:~6,2%_%datetime:~8,2%%datetime:~10,2%%datetime:~12,2%

REM Detect and run appropriate backup
docker ps --format "{{.Names}}" 2>nul | findstr /c:"scheduler-db" >nul 2>&1
if %ERRORLEVEL%==0 (
    goto :backup_postgresql_docker
) else if exist "instance\scheduler.db" (
    goto :backup_sqlite
) else (
    echo [ERROR] No database found to backup
    goto :eof
)

:backup_postgresql_docker
set BACKUP_FILE=%BACKUP_DIR%\scheduler_backup_postgresql_%TIMESTAMP%.sql
echo [INFO] Backing up PostgreSQL database from Docker container...

set DB_NAME=%POSTGRES_DB%
if "%DB_NAME%"=="" set DB_NAME=crossmark_scheduler
set DB_USER=%POSTGRES_USER%
if "%DB_USER%"=="" set DB_USER=scheduler_app

docker exec scheduler-db pg_dump -U %DB_USER% %DB_NAME% > "%BACKUP_FILE%" 2>nul
if %ERRORLEVEL%==0 (
    echo [SUCCESS] Backup created: %BACKUP_FILE%

    REM Compress the backup if gzip is available
    where gzip >nul 2>&1
    if %ERRORLEVEL%==0 (
        gzip "%BACKUP_FILE%"
        echo [INFO] Backup compressed
    )
) else (
    echo [ERROR] Failed to backup PostgreSQL database
    del "%BACKUP_FILE%" 2>nul
)
goto :eof

:backup_sqlite
set BACKUP_FILE=%BACKUP_DIR%\scheduler_backup_sqlite_%TIMESTAMP%.db
echo [INFO] Backing up SQLite database...

copy "instance\scheduler.db" "%BACKUP_FILE%" >nul 2>&1
if %ERRORLEVEL%==0 (
    echo [SUCCESS] Backup created: %BACKUP_FILE%

    REM Compress if gzip available
    where gzip >nul 2>&1
    if %ERRORLEVEL%==0 (
        gzip "%BACKUP_FILE%"
        echo [INFO] Backup compressed
    )
) else (
    echo [ERROR] Failed to backup SQLite database
)
goto :eof

:restore_interactive
call :list_backups
echo.
set /p BACKUP_FILE="Enter backup file path: "
goto :restore_backup_file

:restore_backup
if "%2"=="" (
    echo [ERROR] Please specify backup file: backup.bat --restore ^<file^>
    goto :eof
)
set BACKUP_FILE=%2

:restore_backup_file
if not exist "%BACKUP_FILE%" (
    echo [ERROR] Backup file not found: %BACKUP_FILE%
    goto :eof
)

echo [WARNING] This will overwrite the current database!
set /p CONFIRM="Are you sure you want to restore from %BACKUP_FILE%? (yes/no): "
if not "%CONFIRM%"=="yes" (
    echo [INFO] Restore cancelled
    goto :eof
)

REM Check file type and restore accordingly
echo %BACKUP_FILE% | findstr /c:".sql" >nul
if %ERRORLEVEL%==0 (
    goto :restore_postgresql
)

echo %BACKUP_FILE% | findstr /c:".db" >nul
if %ERRORLEVEL%==0 (
    goto :restore_sqlite
)

echo [ERROR] Unknown backup format
goto :eof

:restore_postgresql
echo [INFO] Restoring PostgreSQL database...

set DB_NAME=%POSTGRES_DB%
if "%DB_NAME%"=="" set DB_NAME=crossmark_scheduler
set DB_USER=%POSTGRES_USER%
if "%DB_USER%"=="" set DB_USER=scheduler_app

REM Check if file is gzipped
echo %BACKUP_FILE% | findstr /c:".gz" >nul
if %ERRORLEVEL%==0 (
    where gzip >nul 2>&1
    if %ERRORLEVEL%==0 (
        gzip -dc "%BACKUP_FILE%" | docker exec -i scheduler-db psql -U %DB_USER% -d %DB_NAME%
    ) else (
        echo [ERROR] gzip not found, cannot decompress backup
        goto :eof
    )
) else (
    docker exec -i scheduler-db psql -U %DB_USER% -d %DB_NAME% < "%BACKUP_FILE%"
)

if %ERRORLEVEL%==0 (
    echo [SUCCESS] Database restored successfully
) else (
    echo [ERROR] Failed to restore database
)
goto :eof

:restore_sqlite
echo [INFO] Restoring SQLite database...

REM Check if file is gzipped
echo %BACKUP_FILE% | findstr /c:".gz" >nul
if %ERRORLEVEL%==0 (
    where gzip >nul 2>&1
    if %ERRORLEVEL%==0 (
        gzip -dc "%BACKUP_FILE%" > "instance\scheduler.db"
    ) else (
        echo [ERROR] gzip not found, cannot decompress backup
        goto :eof
    )
) else (
    copy "%BACKUP_FILE%" "instance\scheduler.db" >nul
)

if %ERRORLEVEL%==0 (
    echo [SUCCESS] Database restored successfully
) else (
    echo [ERROR] Failed to restore database
)
goto :eof

:list_backups
echo.
echo [INFO] Available backups in %BACKUP_DIR%:
echo.

if not exist "%BACKUP_DIR%" (
    echo [WARNING] No backup directory found
    goto :eof
)

set COUNT=0
for %%f in ("%BACKUP_DIR%\scheduler_backup_*") do (
    echo   - %%~nxf ^(%%~zf bytes^)
    set /a COUNT+=1
)

if %COUNT%==0 (
    echo [WARNING] No backups found
) else (
    echo.
    echo [INFO] Total: %COUNT% backup^(s^)
)
goto :eof

:cleanup_backups
echo.
set /p DAYS="Delete backups older than how many days? [%RETENTION_DAYS%]: "
if "%DAYS%"=="" set DAYS=%RETENTION_DAYS%

echo [INFO] Cleaning up backups older than %DAYS% days...

forfiles /p "%BACKUP_DIR%" /m "scheduler_backup_*" /d -%DAYS% /c "cmd /c del @path" 2>nul

echo [SUCCESS] Cleanup completed
goto :eof

:setup_schedule
echo.
echo Configure automated backup schedule using Windows Task Scheduler
echo.

set /p BACKUP_PATH="Backup directory [%BACKUP_DIR%]: "
if "%BACKUP_PATH%"=="" set BACKUP_PATH=%BACKUP_DIR%

echo.
echo Select backup frequency:
echo   1^) Daily
echo   2^) Every 12 hours
echo   3^) Every 6 hours
echo   4^) Weekly ^(Sundays^)
echo.
set /p FREQ="Select option [1-4]: "

if "%FREQ%"=="1" set SCHEDULE=DAILY
if "%FREQ%"=="2" set SCHEDULE=DAILY /mo 1 /ri 720
if "%FREQ%"=="3" set SCHEDULE=DAILY /mo 1 /ri 360
if "%FREQ%"=="4" set SCHEDULE=WEEKLY /d SUN
if "%SCHEDULE%"=="" set SCHEDULE=DAILY

set /p HOUR="Preferred hour (0-23) [2]: "
if "%HOUR%"=="" set HOUR=2

set /p RETENTION="Keep backups for how many days? [%RETENTION_DAYS%]: "
if "%RETENTION%"=="" set RETENTION=%RETENTION_DAYS%

set SCRIPT_PATH=%CD%\backup.bat
set TASK_NAME=FlaskSchedulerBackup

echo.
echo [INFO] Creating Windows scheduled task...

REM Delete existing task if present
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

REM Create new scheduled task
schtasks /create /tn "%TASK_NAME%" /tr "\"%SCRIPT_PATH%\" --now --dir \"%BACKUP_PATH%\"" /sc %SCHEDULE% /st %HOUR%:00 /f

if %ERRORLEVEL%==0 (
    echo.
    echo [SUCCESS] Scheduled backup configured!
    echo.
    echo [INFO] Task name: %TASK_NAME%
    echo [INFO] Backup directory: %BACKUP_PATH%
    echo [INFO] Retention: %RETENTION% days
    echo.
    echo [INFO] To view task: schtasks /query /tn "%TASK_NAME%"
    echo [INFO] To delete task: schtasks /delete /tn "%TASK_NAME%" /f
) else (
    echo [ERROR] Failed to create scheduled task
    echo [INFO] You may need to run this script as Administrator
)
goto :eof

:show_help
echo Usage: backup.bat [option]
echo.
echo Options:
echo   ^(none^)              Interactive mode
echo   --now               Run backup immediately
echo     --dir ^<path^>      Backup directory ^(default: backups^)
echo   --schedule          Set up scheduled backups
echo   --restore ^<file^>    Restore from backup file
echo   --list              List available backups
echo   --help              Show this help message
echo.
goto :eof

:exit_script
echo [INFO] Goodbye!
goto :eof
