# Production Deployment Guide
## Flask Schedule Webapp - Enterprise Deployment

This guide provides comprehensive instructions for deploying the Flask Schedule Webapp in a production environment with enterprise-grade security, performance, and reliability.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Production Setup](#production-setup)
4. [Security Hardening](#security-hardening)
5. [Database Configuration](#database-configuration)
6. [Deployment Options](#deployment-options)
7. [Monitoring & Health Checks](#monitoring--health-checks)
8. [Backup & Recovery](#backup--recovery)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ / RHEL 8+ / Windows Server 2019+
- **Python**: 3.11 or higher
- **RAM**: Minimum 2GB, Recommended 4GB+
- **Disk**: Minimum 10GB free space
- **Network**: HTTPS/TLS capability for production

### Required Software
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip nginx supervisor postgresql

# RHEL/CentOS
sudo dnf install python311 python3-pip nginx supervisor postgresql-server
```

---

## Quick Start

### 1. Clone Repository
```bash
git clone <repository-url>
cd flask-schedule-webapp
```

### 2. Create Virtual Environment
```bash
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
# Copy example environment file
cp scheduler_app/.env.example scheduler_app/.env

# Generate secure secret key
python -c 'import secrets; print(f"SECRET_KEY={secrets.token_hex(32)}")' >> scheduler_app/.env

# Edit .env file and configure required settings
nano scheduler_app/.env
```

### 5. Initialize Database
```bash
cd scheduler_app
flask db upgrade
cd ..
```

### 6. Run Production Server
```bash
gunicorn --config gunicorn_config.py wsgi:app
```

---

## Production Setup

### Environment Configuration

#### Required Environment Variables
```bash
# CRITICAL - Must be set for production
SECRET_KEY=<64-character-hex-string>
FLASK_ENV=production
WALMART_EDR_USERNAME=<your-username>
WALMART_EDR_PASSWORD=<your-password>
WALMART_EDR_MFA_CREDENTIAL_ID=<your-mfa-id>
```

#### Production Database (PostgreSQL)
```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE scheduler_db;
CREATE USER scheduler_user WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE scheduler_db TO scheduler_user;
\q

# Update .env
DATABASE_URL=postgresql://scheduler_user:secure_password@localhost:5432/scheduler_db
```

### Application Setup

#### 1. Set Up Application User
```bash
# Create dedicated user for running the application
sudo useradd -r -s /bin/bash -d /opt/scheduler scheduler

# Copy application files
sudo mkdir -p /opt/scheduler
sudo cp -r . /opt/scheduler/
sudo chown -R scheduler:scheduler /opt/scheduler
```

#### 2. Configure Systemd Service (Linux)
Create `/etc/systemd/system/scheduler.service`:

```ini
[Unit]
Description=Flask Schedule Webapp
After=network.target postgresql.service

[Service]
Type=notify
User=scheduler
Group=scheduler
WorkingDirectory=/opt/scheduler
Environment="PATH=/opt/scheduler/venv/bin"
EnvironmentFile=/opt/scheduler/scheduler_app/.env
ExecStart=/opt/scheduler/venv/bin/gunicorn --config gunicorn_config.py wsgi:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable scheduler.service
sudo systemctl start scheduler.service
sudo systemctl status scheduler.service
```

#### 3. Configure Nginx Reverse Proxy
Create `/etc/nginx/sites-available/scheduler`:

```nginx
upstream scheduler_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name scheduler.yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name scheduler.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/scheduler.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/scheduler.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/scheduler_access.log;
    error_log /var/log/nginx/scheduler_error.log;

    # Client body size (for file uploads)
    client_max_body_size 10M;

    # Proxy settings
    location / {
        proxy_pass http://scheduler_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files
    location /static {
        alias /opt/scheduler/scheduler_app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Health check endpoint
    location /health/ping {
        proxy_pass http://scheduler_app;
        access_log off;
    }
}
```

Enable and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/scheduler /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Security Hardening

### 1. SSL/TLS Certificates
```bash
# Install Certbot for Let's Encrypt
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d scheduler.yourdomain.com
```

### 2. Firewall Configuration
```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Firewalld (RHEL)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 3. Database Security
```bash
# PostgreSQL - Edit pg_hba.conf
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Use md5 or scram-sha-256 authentication
# local   all             all                                     scram-sha-256
# host    all             all             127.0.0.1/32            scram-sha-256
```

### 4. Environment Variable Protection
```bash
# Restrict .env file permissions
chmod 600 /opt/scheduler/scheduler_app/.env
chown scheduler:scheduler /opt/scheduler/scheduler_app/.env
```

---

## Deployment Options

### Option 1: Systemd Service (Recommended for Linux)
See [Application Setup](#application-setup) above.

### Option 2: Docker Container
```bash
# Build Docker image
docker build -t scheduler-app:latest .

# Run container
docker run -d \
  --name scheduler \
  -p 8000:8000 \
  --env-file scheduler_app/.env \
  -v scheduler_data:/opt/scheduler/instance \
  scheduler-app:latest
```

### Option 3: Kubernetes Deployment
See `k8s/` directory for Kubernetes manifests (TODO: create these).

---

## Monitoring & Health Checks

### Health Check Endpoints

The application provides several health check endpoints:

#### 1. Ping Endpoint
```bash
curl https://scheduler.yourdomain.com/health/ping
# Response: {"status": "ok", "message": "pong"}
```

#### 2. Liveness Probe
```bash
curl https://scheduler.yourdomain.com/health/live
# Response: {"status": "alive", "timestamp": "..."}
```

#### 3. Readiness Probe
```bash
curl https://scheduler.yourdomain.com/health/ready
# Response: {"status": "ready", "checks": {...}}
```

#### 4. Status Endpoint
```bash
curl https://scheduler.yourdomain.com/health/status
# Response: Detailed system information
```

#### 5. Metrics Endpoint (Prometheus-compatible)
```bash
curl https://scheduler.yourdomain.com/health/metrics
# Response: Prometheus text format metrics
```

### Application Logging

Logs are written to:
- **Application logs**: `scheduler_app/logs/app.log`
- **Gunicorn access logs**: stdout (captured by systemd)
- **Gunicorn error logs**: stderr (captured by systemd)

View logs:
```bash
# Systemd service logs
sudo journalctl -u scheduler.service -f

# Application logs
tail -f /opt/scheduler/scheduler_app/logs/app.log
```

### Monitoring Setup

#### Prometheus Integration
Add to `prometheus.yml`:
```yaml
scrape_configs:
  - job_name: 'scheduler-webapp'
    static_configs:
      - targets: ['scheduler.yourdomain.com:443']
    metrics_path: '/health/metrics'
    scheme: https
```

#### Uptime Monitoring
Configure external monitoring (e.g., UptimeRobot, Pingdom) to check:
- URL: `https://scheduler.yourdomain.com/health/ping`
- Interval: 5 minutes
- Expected: 200 OK with JSON response

---

## Backup & Recovery

### Database Backups

#### PostgreSQL Automated Backup
```bash
# Create backup script
cat > /opt/scheduler/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/scheduler/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U scheduler_user scheduler_db > $BACKUP_DIR/scheduler_db_$TIMESTAMP.sql

# Keep only last 7 days of backups
find $BACKUP_DIR -name "scheduler_db_*.sql" -mtime +7 -delete
EOF

chmod +x /opt/scheduler/backup.sh

# Add to cron (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/scheduler/backup.sh") | crontab -
```

#### SQLite Backup
```bash
# Backup SQLite database
cp /opt/scheduler/instance/scheduler.db /opt/scheduler/backups/scheduler_$(date +%Y%m%d).db
```

### Application Files Backup
```bash
# Backup entire application
tar -czf scheduler_backup_$(date +%Y%m%d).tar.gz /opt/scheduler
```

### Recovery Procedure
```bash
# Stop service
sudo systemctl stop scheduler

# Restore database
psql -U scheduler_user scheduler_db < backup_file.sql

# Restart service
sudo systemctl start scheduler
```

---

## Troubleshooting

### Common Issues

#### 1. Application Won't Start
```bash
# Check service status
sudo systemctl status scheduler

# Check logs
sudo journalctl -u scheduler.service -n 100

# Verify environment variables
sudo -u scheduler cat /opt/scheduler/scheduler_app/.env
```

#### 2. Database Connection Errors
```bash
# Test database connection
psql -U scheduler_user -d scheduler_db -h localhost

# Check PostgreSQL status
sudo systemctl status postgresql
```

#### 3. Permission Errors
```bash
# Fix ownership
sudo chown -R scheduler:scheduler /opt/scheduler

# Fix permissions
sudo chmod 755 /opt/scheduler
sudo chmod 600 /opt/scheduler/scheduler_app/.env
```

#### 4. High Memory Usage
```bash
# Reduce Gunicorn workers
# Edit gunicorn_config.py or set environment variable
export GUNICORN_WORKERS=2
sudo systemctl restart scheduler
```

### Performance Tuning

#### Gunicorn Workers
```bash
# Formula: (2 x CPU_CORES) + 1
# For 4 CPUs: 9 workers
export GUNICORN_WORKERS=9
```

#### Database Connection Pool
```bash
# Adjust based on concurrent users
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
```

---

## Maintenance

### Updates & Upgrades
```bash
# Pull latest code
cd /opt/scheduler
sudo -u scheduler git pull

# Activate virtual environment
sudo -u scheduler /opt/scheduler/venv/bin/pip install -r requirements.txt

# Run database migrations
cd scheduler_app
sudo -u scheduler /opt/scheduler/venv/bin/flask db upgrade

# Restart service
sudo systemctl restart scheduler
```

### Log Rotation
Create `/etc/logrotate.d/scheduler`:
```
/opt/scheduler/scheduler_app/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 scheduler scheduler
    sharedscripts
    postrotate
        systemctl reload scheduler > /dev/null 2>&1 || true
    endscript
}
```

---

## Support & Documentation

- **Application Logs**: `/opt/scheduler/scheduler_app/logs/`
- **System Logs**: `journalctl -u scheduler.service`
- **Health Checks**: `https://yourdomain.com/health/status`

For additional support, contact your system administrator or refer to the main README.md.
