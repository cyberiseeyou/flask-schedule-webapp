# Docker Deployment Guide
## Flask Schedule Webapp - Containerized Deployment

This guide covers deploying the Flask Schedule Webapp using Docker and Docker Compose.

---

## Table of Contents
1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Setup Options](#setup-options)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [Architecture](#architecture)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Configuration](#advanced-configuration)

---

## Quick Start

### One-Command Setup

**Linux/Mac:**
```bash
git clone <repository-url>
cd flask-schedule-webapp
chmod +x setup.sh
./setup.sh
```

**Windows:**
```cmd
git clone <repository-url>
cd flask-schedule-webapp
setup.bat
```

That's it! The setup script will:
- ✅ Check Docker installation
- ✅ Generate secure secrets
- ✅ Build Docker images
- ✅ Start all containers
- ✅ Run database migrations
- ✅ Display access information

---

## Prerequisites

### Required Software

1. **Docker Desktop** (Recommended) or **Docker Engine**
   - **Windows:** [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
   - **Mac:** [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
   - **Linux:** [Docker Engine](https://docs.docker.com/engine/install/)

2. **Docker Compose**
   - Included with Docker Desktop
   - Linux: Install separately if needed

### Minimum System Requirements

- **CPU:** 2 cores
- **RAM:** 4GB (8GB recommended)
- **Disk:** 10GB free space
- **OS:** Windows 10/11, macOS 10.15+, or Linux

---

## Setup Options

### Option 1: Automated Setup (Recommended)

Use the provided setup scripts for automatic configuration.

**Production:**
```bash
./setup.sh prod         # Linux/Mac
setup.bat prod          # Windows
```

**Development:**
```bash
./setup.sh dev          # Linux/Mac
setup.bat dev           # Windows
```

### Option 2: Manual Setup

#### Step 1: Create Environment Files

```bash
# Copy environment template
cp scheduler_app/.env.example scheduler_app/.env

# Edit configuration
nano scheduler_app/.env
```

#### Step 2: Generate Secrets

**Linux/Mac:**
```bash
# Generate SECRET_KEY
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

**Windows:**
```cmd
python -c "import secrets; print(secrets.token_hex(32))"
```

Update `.env` with the generated key.

#### Step 3: Create Docker Compose Environment

Create `.env` in the project root:

```env
POSTGRES_DB=scheduler_db
POSTGRES_USER=scheduler_user
POSTGRES_PASSWORD=<secure-password>
POSTGRES_PORT=5432

REDIS_PASSWORD=<secure-password>
REDIS_PORT=6379

APP_PORT=8000
```

#### Step 4: Build and Run

```bash
# Build images
docker-compose build

# Start containers
docker-compose up -d

# Run migrations
docker-compose exec app flask db upgrade
```

---

## Configuration

### Environment Variables

#### Application Configuration (`scheduler_app/.env`)

```env
# Flask Configuration
SECRET_KEY=<64-character-hex-string>
FLASK_ENV=production

# Database (automatically set by Docker Compose)
DATABASE_URL=postgresql://user:pass@db:5432/scheduler_db

# Walmart EDR Credentials
WALMART_EDR_USERNAME=your-username
WALMART_EDR_PASSWORD=your-password
WALMART_EDR_MFA_CREDENTIAL_ID=your-mfa-id

# External API
EXTERNAL_API_USERNAME=your-crossmark-username
EXTERNAL_API_PASSWORD=your-crossmark-password
```

#### Docker Compose Configuration (`.env` in project root)

```env
# Database
POSTGRES_DB=scheduler_db
POSTGRES_USER=scheduler_user
POSTGRES_PASSWORD=secure_password_here
POSTGRES_PORT=5432

# Redis
REDIS_PASSWORD=secure_redis_password
REDIS_PORT=6379

# Application
APP_PORT=8000

# Nginx (Production)
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443
```

---

## Usage

### Starting the Application

```bash
# Production
docker-compose up -d

# Development (with hot-reload)
docker-compose -f docker-compose.dev.yml up -d
```

### Stopping the Application

```bash
docker-compose down

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f db
docker-compose logs -f celery

# Last 100 lines
docker-compose logs --tail=100 app
```

### Accessing the Application

- **Production:** http://localhost:8000
- **Development:** http://localhost:5000
- **Health Check:** http://localhost:8000/health/ping

### Database Access

```bash
# Connect to PostgreSQL
docker-compose exec db psql -U scheduler_user -d scheduler_db

# Backup database
docker-compose exec db pg_dump -U scheduler_user scheduler_db > backup.sql

# Restore database
docker-compose exec -T db psql -U scheduler_user scheduler_db < backup.sql
```

### Running Migrations

```bash
# Run pending migrations
docker-compose exec app flask db upgrade

# Create new migration
docker-compose exec app flask db migrate -m "Description"

# Downgrade migration
docker-compose exec app flask db downgrade
```

### Shell Access

```bash
# App container bash
docker-compose exec app /bin/bash

# Python shell with app context
docker-compose exec app python

# Database shell
docker-compose exec db psql -U scheduler_user scheduler_db
```

### Restarting Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart app

# Rebuild and restart
docker-compose up -d --build app
```

---

## Architecture

### Container Stack

The Docker Compose setup includes:

1. **app** - Flask application (Gunicorn)
   - Port: 8000 (production) / 5000 (development)
   - Dependencies: PostgreSQL, Redis

2. **db** - PostgreSQL 15
   - Port: 5432
   - Persistent volume: `postgres_data`

3. **redis** - Redis 7
   - Port: 6379
   - Persistent volume: `redis_data`

4. **celery** - Celery worker (background tasks)
   - No exposed ports
   - Depends on: app, db, redis

5. **nginx** - Nginx reverse proxy (optional, production)
   - Ports: 80, 443
   - Profile: production

### Network Architecture

```
┌─────────────────────────────────────────────┐
│              Docker Network                 │
│                                             │
│  ┌─────────┐      ┌─────────┐             │
│  │  Nginx  │─────▶│   App   │             │
│  │  :80    │      │  :8000  │             │
│  └─────────┘      └────┬────┘             │
│                        │                   │
│                   ┌────┴────┐              │
│                   │         │              │
│              ┌────▼───┐ ┌──▼────┐         │
│              │   DB   │ │ Redis │         │
│              │ :5432  │ │ :6379 │         │
│              └────────┘ └───────┘         │
│                                             │
│              ┌──────────┐                  │
│              │  Celery  │                  │
│              │  Worker  │                  │
│              └──────────┘                  │
│                                             │
└─────────────────────────────────────────────┘
```

### Volumes

- **postgres_data** - Database files
- **redis_data** - Redis persistence
- **./scheduler_app/instance** - SQLite database (if used)
- **./scheduler_app/logs** - Application logs

---

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

**Error:** `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution:**
```bash
# Check what's using the port
lsof -i :8000           # Mac/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process or change APP_PORT in .env
```

#### 2. Database Connection Errors

**Error:** `could not connect to server: Connection refused`

**Solution:**
```bash
# Check database status
docker-compose ps db

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

#### 3. Permission Denied Errors

**Error:** `Permission denied` when accessing files

**Solution:**
```bash
# Fix ownership (Linux/Mac)
sudo chown -R $USER:$USER .

# Or run docker with sudo
sudo docker-compose up -d
```

#### 4. Out of Memory

**Error:** Container crashes or Docker becomes unresponsive

**Solution:**
```bash
# Increase Docker memory limit in Docker Desktop settings
# Or reduce worker count in gunicorn_config.py

export GUNICORN_WORKERS=2
docker-compose up -d --build
```

#### 5. Migration Errors

**Error:** `Target database is not up to date`

**Solution:**
```bash
# Check migration status
docker-compose exec app flask db current

# Run migrations
docker-compose exec app flask db upgrade

# If stuck, rollback and retry
docker-compose exec app flask db downgrade
docker-compose exec app flask db upgrade
```

### Debugging Tips

#### Enable Debug Logging

```bash
# Set log level in scheduler_app/.env
LOG_LEVEL=DEBUG

# Restart containers
docker-compose restart app
```

#### Check Health Status

```bash
# Application health
curl http://localhost:8000/health/status

# Container health
docker-compose ps
```

#### Inspect Containers

```bash
# View container details
docker inspect scheduler-app

# Check resource usage
docker stats

# View container processes
docker-compose top
```

---

## Advanced Configuration

### Using Custom Database

To use an external PostgreSQL database:

1. Update `scheduler_app/.env`:
   ```env
   DATABASE_URL=postgresql://user:pass@external-host:5432/dbname
   ```

2. Remove `db` service dependency in `docker-compose.yml`

3. Start without database service:
   ```bash
   docker-compose up -d app celery
   ```

### SSL/TLS Configuration

1. Place SSL certificates in `nginx/ssl/`:
   ```
   nginx/ssl/cert.pem
   nginx/ssl/key.pem
   ```

2. Uncomment SSL server block in `nginx/nginx.conf`

3. Start with nginx:
   ```bash
   docker-compose --profile production up -d
   ```

### Scaling Services

```bash
# Scale celery workers
docker-compose up -d --scale celery=3

# Scale app instances (requires load balancer)
docker-compose up -d --scale app=2
```

### Custom Gunicorn Configuration

Edit `gunicorn_config.py` and rebuild:

```bash
# Modify gunicorn_config.py
# Then rebuild
docker-compose build app
docker-compose up -d app
```

### Environment-Specific Overrides

Create `docker-compose.override.yml` for local customizations:

```yaml
version: '3.8'
services:
  app:
    environment:
      - DEBUG=true
    ports:
      - "5000:8000"
```

This file is automatically loaded by Docker Compose and git-ignored.

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] Update all secrets in `.env` files
- [ ] Set `FLASK_ENV=production`
- [ ] Configure SSL certificates
- [ ] Set up backups (see below)
- [ ] Configure monitoring
- [ ] Test health endpoints

### Backup Strategy

**Database Backup:**
```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
docker-compose exec -T db pg_dump -U scheduler_user scheduler_db | \
    gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
EOF

chmod +x backup.sh

# Add to crontab (daily at 2 AM)
0 2 * * * /path/to/backup.sh
```

**Volume Backup:**
```bash
# Backup volumes
docker run --rm -v scheduler_postgres_data:/data -v $(pwd):/backup \
    alpine tar czf /backup/postgres_backup.tar.gz /data
```

### Monitoring

Use health check endpoints for monitoring:

```bash
# Liveness probe
curl -f http://localhost:8000/health/live

# Readiness probe
curl -f http://localhost:8000/health/ready

# Detailed status
curl http://localhost:8000/health/status

# Prometheus metrics
curl http://localhost:8000/health/metrics
```

---

## Support & Documentation

- **Main Documentation:** [README.md](README.md)
- **Deployment Guide:** [DEPLOYMENT.md](DEPLOYMENT.md)
- **Production Checklist:** [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md)

For issues, check the logs:
```bash
docker-compose logs -f
```

---

## License

See LICENSE file for details.
