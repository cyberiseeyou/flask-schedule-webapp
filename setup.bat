@echo off
REM Flask Schedule Webapp - Docker Setup Script (Windows)
REM
REM This script sets up the application with Docker Compose
REM Usage: setup.bat [dev|prod]

setlocal enabledelayedexpansion

REM Banner
echo.
echo ===============================================================
echo.
echo          Flask Schedule Webapp - Docker Setup
echo.
echo ===============================================================
echo.

REM Determine environment (default: production)
set ENVIRONMENT=%1
if "%ENVIRONMENT%"=="" set ENVIRONMENT=prod

if "%ENVIRONMENT%"=="dev" (
    echo [INFO] Setting up DEVELOPMENT environment
    set COMPOSE_FILE=docker-compose.dev.yml
) else (
    echo [INFO] Setting up PRODUCTION environment
    set COMPOSE_FILE=docker-compose.yml
)

REM Step 1: Check Docker installation
echo [INFO] Checking Docker installation...
docker --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker is not installed!
    echo [INFO] Please install Docker Desktop from: https://docs.docker.com/desktop/install/windows-install/
    exit /b 1
)
echo [SUCCESS] Docker is installed
docker --version

REM Step 2: Check Docker Compose installation
echo [INFO] Checking Docker Compose installation...
docker-compose --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    docker compose version >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Docker Compose is not installed!
        exit /b 1
    )
    set COMPOSE_CMD=docker compose
) else (
    set COMPOSE_CMD=docker-compose
)
echo [SUCCESS] Docker Compose is installed
%COMPOSE_CMD% --version

REM Step 3: Create .env file if it doesn't exist
echo [INFO] Configuring environment variables...
set ENV_FILE=scheduler_app\.env
set ENV_EXAMPLE=scheduler_app\.env.example

if not exist "%ENV_FILE%" (
    if exist "%ENV_EXAMPLE%" (
        copy "%ENV_EXAMPLE%" "%ENV_FILE%" >nul
        echo [SUCCESS] Created .env file from .env.example
    ) else (
        echo [ERROR] .env.example file not found!
        exit /b 1
    )
) else (
    echo [WARNING] .env file already exists, skipping...
)

REM Step 4: Generate secure secrets
echo [INFO] Generating secure secrets...

REM Generate SECRET_KEY using Python
python -c "import secrets; print(f'SECRET_KEY={secrets.token_hex(32)}')" > temp_secret.txt 2>nul
if exist temp_secret.txt (
    for /f "delims=" %%i in (temp_secret.txt) do set NEW_SECRET=%%i
    powershell -Command "(Get-Content '%ENV_FILE%') -replace '^SECRET_KEY=.*', '!NEW_SECRET!' | Set-Content '%ENV_FILE%'"
    del temp_secret.txt
    echo [SUCCESS] Generated SECRET_KEY
)

REM Create .env for Docker Compose if it doesn't exist
if not exist ".env" (
    echo [INFO] Creating Docker Compose .env file...

    REM Generate random passwords
    python -c "import secrets; print(secrets.token_urlsafe(32)[:32])" > temp_db_pass.txt 2>nul
    python -c "import secrets; print(secrets.token_urlsafe(32)[:32])" > temp_redis_pass.txt 2>nul

    set /p DB_PASS=<temp_db_pass.txt
    set /p REDIS_PASS=<temp_redis_pass.txt

    (
        echo # Docker Compose Environment Variables
        echo # Database Configuration
        echo POSTGRES_DB=scheduler_db
        echo POSTGRES_USER=scheduler_user
        echo POSTGRES_PASSWORD=!DB_PASS!
        echo POSTGRES_PORT=5432
        echo.
        echo # Redis Configuration
        echo REDIS_PASSWORD=!REDIS_PASS!
        echo REDIS_PORT=6379
        echo.
        echo # Application Configuration
        echo APP_PORT=8000
        echo.
        echo # Nginx Configuration ^(Production only^)
        echo NGINX_HTTP_PORT=80
        echo NGINX_HTTPS_PORT=443
    ) > .env

    del temp_db_pass.txt temp_redis_pass.txt 2>nul
    echo [SUCCESS] Created Docker Compose .env file with secure passwords
) else (
    echo [WARNING] Docker Compose .env file already exists, skipping...
)

REM Load environment variables from .env
for /f "tokens=1,2 delims==" %%a in (.env) do (
    set %%a=%%b
)

REM Step 5: Update DATABASE_URL in app .env
echo [INFO] Updating database connection string...
set DB_URL=postgresql://%POSTGRES_USER%:%POSTGRES_PASSWORD%@localhost:%POSTGRES_PORT%/%POSTGRES_DB%
powershell -Command "(Get-Content '%ENV_FILE%') -replace '^DATABASE_URL=.*', 'DATABASE_URL=%DB_URL%' | Set-Content '%ENV_FILE%'"
echo [SUCCESS] Updated DATABASE_URL in %ENV_FILE%

REM Step 6: Build Docker images
echo [INFO] Building Docker images...
%COMPOSE_CMD% -f %COMPOSE_FILE% build
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to build Docker images
    exit /b 1
)
echo [SUCCESS] Docker images built successfully

REM Step 7: Start containers
echo [INFO] Starting containers...
%COMPOSE_CMD% -f %COMPOSE_FILE% up -d
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to start containers
    exit /b 1
)
echo [SUCCESS] Containers started successfully

REM Step 8: Wait for database to be ready
echo [INFO] Waiting for database to be ready...
timeout /t 5 /nobreak >nul

REM Step 9: Run database migrations
echo [INFO] Running database migrations...
%COMPOSE_CMD% -f %COMPOSE_FILE% exec -T app flask db upgrade
echo [SUCCESS] Database migrations completed

REM Step 10: Display status
echo.
echo [SUCCESS] Setup completed successfully!
echo.
echo [INFO] Container Status:
%COMPOSE_CMD% -f %COMPOSE_FILE% ps

REM Step 11: Display access information
echo.
echo [INFO] Application is running at:
if "%ENVIRONMENT%"=="dev" (
    echo   http://localhost:5000
) else (
    echo   http://localhost:8000
)

echo.
echo [INFO] Health Check:
echo   http://localhost:%APP_PORT%/health/ping

echo.
echo [INFO] Useful Commands:
echo   View logs:    %COMPOSE_CMD% -f %COMPOSE_FILE% logs -f
echo   Stop app:     %COMPOSE_CMD% -f %COMPOSE_FILE% down
echo   Restart app:  %COMPOSE_CMD% -f %COMPOSE_FILE% restart
echo   Shell access: %COMPOSE_CMD% -f %COMPOSE_FILE% exec app /bin/bash

echo.
echo [SUCCESS] Happy scheduling!
echo.

pause
