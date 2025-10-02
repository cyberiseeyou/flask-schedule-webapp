# Docker Deployment Guide

## Quick Start

### 1. Prerequisites
- Docker installed (version 20.10+)
- Docker Compose installed (version 2.0+)

### 2. Environment Setup

Copy the example environment file:
```bash
cp .env.docker .env
```

Edit `.env` with your configuration:
```bash
# Update at minimum:
SECRET_KEY=your-super-secret-key-here
SETTINGS_ENCRYPTION_KEY=your-encryption-key-here
```

### 3. Build and Run

```bash
# Build the Docker image
docker-compose build

# Start the application
docker-compose up -d

# View logs
docker-compose logs -f web
```

The application will be available at: **http://localhost:8135**

## Container Management

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### Restart Services
```bash
docker-compose restart
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
```

### Access Container Shell
```bash
docker-compose exec web bash
```

## Database Management

### SQLite (Default)

The SQLite database is stored in `./scheduler_app/instance/scheduler.db` and is mounted as a volume.

#### Initialize Database
```bash
docker-compose exec web python -c "from scheduler_app.app import init_db; init_db()"
```

#### Run Migrations
```bash
docker-compose exec web flask db upgrade
```

#### Backup Database
```bash
docker-compose exec web cp /app/scheduler_app/instance/scheduler.db /app/scheduler_app/instance/scheduler_backup_$(date +%Y%m%d).db
```

### PostgreSQL (Optional)

To use PostgreSQL instead of SQLite:

1. Uncomment the `db` service in `docker-compose.yml`
2. Update `.env`:
   ```
   SQLALCHEMY_DATABASE_URI=postgresql://scheduler:scheduler_password@db:5432/scheduler_db
   ```
3. Restart services:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

## Development Mode

For development with hot reload:

```bash
# Create docker-compose.override.yml
cat > docker-compose.override.yml <<EOF
version: '3.8'

services:
  web:
    environment:
      - FLASK_ENV=development
      - FLASK_DEBUG=1
    volumes:
      - .:/app
    command: python -m flask run --host=0.0.0.0 --port=5000 --reload
EOF

# Start in development mode
docker-compose up
```

## Celery Background Tasks (Optional)

To enable background task processing:

1. Uncomment `redis` and `celery-worker` services in `docker-compose.yml`
2. Update `.env`:
   ```
   CELERY_BROKER_URL=redis://redis:6379/0
   CELERY_RESULT_BACKEND=redis://redis:6379/0
   ```
3. Restart services

## Testing

### Run Tests in Container
```bash
# Run all tests
docker-compose exec web pytest

# Run specific test file
docker-compose exec web pytest scheduler_app/test_system_settings.py

# Run with coverage
docker-compose exec web pytest --cov=scheduler_app
```

## Production Deployment

### 1. Security Configuration

**Critical:** Update these in `.env`:
```bash
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
SETTINGS_ENCRYPTION_KEY=$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')
```

### 2. Use PostgreSQL
```bash
# Uncomment PostgreSQL service in docker-compose.yml
# Update database credentials in .env
SQLALCHEMY_DATABASE_URI=postgresql://scheduler:STRONG_PASSWORD@db:5432/scheduler_db
```

### 3. Enable SSL/TLS

Use a reverse proxy (nginx/traefik) in front of the Flask app:

```yaml
# docker-compose.yml - add nginx service
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    networks:
      - app-network
```

### 4. Resource Limits

Add resource limits to `docker-compose.yml`:

```yaml
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## Monitoring

### Health Check
```bash
curl http://localhost:8135/
```

### Container Stats
```bash
docker stats flask-schedule-webapp
```

### Application Logs
```bash
docker-compose logs -f web | grep ERROR
```

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose logs web

# Inspect container
docker-compose ps
docker inspect flask-schedule-webapp
```

### Database Connection Issues
```bash
# Check database service (if using PostgreSQL)
docker-compose exec db psql -U scheduler -d scheduler_db -c "\dt"

# Verify environment variables
docker-compose exec web env | grep DATABASE
```

### Permission Issues
```bash
# Fix ownership (run on host)
sudo chown -R $USER:$USER scheduler_app/instance
```

### Reset Everything
```bash
# Stop and remove all containers, volumes
docker-compose down -v

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d
```

## Backup and Restore

### Backup
```bash
# Create backup directory
mkdir -p backups

# Backup database
docker-compose exec web cp /app/scheduler_app/instance/scheduler.db /app/backups/scheduler_$(date +%Y%m%d_%H%M%S).db

# Backup .env file
cp .env backups/.env.backup
```

### Restore
```bash
# Restore database
docker-compose exec web cp /app/backups/scheduler_20250101_120000.db /app/scheduler_app/instance/scheduler.db

# Restart application
docker-compose restart web
```

## Scaling (Load Balancing)

```bash
# Scale web service to 3 instances
docker-compose up -d --scale web=3

# Use nginx for load balancing (see nginx.conf example)
```

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/docker.yml
name: Docker Build and Deploy

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: docker-compose build

      - name: Run tests
        run: docker-compose run web pytest

      - name: Push to registry
        run: |
          echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin
          docker-compose push
```

## Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `FLASK_ENV` | Flask environment | `production` | Yes |
| `SECRET_KEY` | Flask secret key | - | Yes |
| `SQLALCHEMY_DATABASE_URI` | Database connection string | `sqlite:///instance/scheduler.db` | Yes |
| `SETTINGS_ENCRYPTION_KEY` | Fernet encryption key | - | Yes |
| `WALMART_EDR_USERNAME` | EDR username | - | No |
| `WALMART_EDR_PASSWORD` | EDR password | - | No |
| `CELERY_BROKER_URL` | Celery broker URL | - | No |

## Support

For issues or questions:
- GitHub Issues: https://github.com/cyberiseeyou/flask-schedule-webapp/issues
- Documentation: See README.md
