# Celery Background Sync Setup Guide

## Overview

This application uses **Celery** with **Redis** as a message broker to handle background synchronization with the Crossmark API. This provides a non-blocking user experience where schedule operations complete immediately in the local database, and synchronization with Crossmark happens automatically in the background.

## Architecture

### Components

1. **Flask Application** (`app.py`) - Main web application
2. **Celery Worker** (`celery_worker.py`) - Background task processor
3. **Redis** - Message broker and result backend
4. **Sync Service** (`services/sync_service.py`) - Contains Celery task definitions

### How It Works

1. User performs a scheduling operation (create, update, delete)
2. Operation is saved immediately to local database
3. Background sync task is queued in Redis
4. Celery worker picks up the task and syncs to Crossmark API
5. If sync fails, Celery automatically retries with exponential backoff (up to 3 times)

## Installation

### Prerequisites

- Python 3.8+
- Redis server

### Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `celery==5.3.4`
- `redis==5.0.1`

### Install Redis

#### Windows
Download and install Redis from: https://github.com/microsoftarchive/redis/releases

Or use Windows Subsystem for Linux (WSL):
```bash
sudo apt update
sudo apt install redis-server
```

#### Linux/Mac
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server

# Mac (using Homebrew)
brew install redis
```

## Running the Application

You need to run **THREE** separate processes:

### 1. Start Redis Server

#### Windows
```bash
redis-server
```

#### Linux/Mac
```bash
redis-server
# Or use systemd
sudo systemctl start redis
```

**Verify Redis is running:**
```bash
redis-cli ping
# Should return: PONG
```

### 2. Start Celery Worker

In a new terminal window:

```bash
cd scheduler_app
celery -A services.sync_service.celery_app worker --loglevel=info
```

**On Windows**, you may need to add the `--pool=solo` flag:
```bash
celery -A services.sync_service.celery_app worker --loglevel=info --pool=solo
```

**You should see output like:**
```
-------------- celery@hostname v5.3.4
---- **** -----
--- * ***  * -- Windows-10.0-26100 2025-09-30 15:30:00
-- * - **** ---
- ** ---------- [config]
- ** ---------- .> app:         scheduler_sync:0x...
- ** ---------- .> transport:   redis://localhost:6379/0
- ** ---------- .> results:     redis://localhost:6379/0
- *** --- * --- .> concurrency: 4 (solo)
-- ******* ---- .> task events: OFF
--- ***** -----
 -------------- [queues]
                .> celery           exchange=celery(direct) key=celery

[tasks]
  . services.sync_service.refresh_events_from_crossmark
  . services.sync_service.sync_employee_to_crossmark
  . services.sync_service.sync_schedule_deletion_to_crossmark
  . services.sync_service.sync_schedule_to_crossmark
  . services.sync_service.sync_schedule_update_to_crossmark
```

### 3. Start Flask Application

In another terminal window:

```bash
cd scheduler_app
python app.py
```

**Or use Gunicorn for production:**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 4. (Optional) Start Celery Beat for Periodic Tasks

If you want automatic periodic refresh of events from Crossmark:

```bash
cd scheduler_app
celery -A services.sync_service.celery_app beat --loglevel=info
```

This will run `refresh_events_from_crossmark` every hour.

## Background Tasks

### Available Tasks

1. **sync_schedule_to_crossmark(schedule_id)**
   - Syncs a new schedule to Crossmark API
   - Automatically retries on failure (3 times with exponential backoff)
   - Used by: `/save_schedule` endpoint

2. **sync_schedule_update_to_crossmark(schedule_id, new_employee_id=None, new_datetime=None)**
   - Syncs schedule updates (reschedule, employee change, trade)
   - Automatically retries on failure
   - Used by: `/api/reschedule`, `/api/reschedule_event`, `/api/trade_events`, `/api/change_employee`

3. **sync_schedule_deletion_to_crossmark(external_id)**
   - Syncs schedule deletion/unscheduling to Crossmark API
   - Automatically retries on failure
   - Used by: `/api/unschedule/<schedule_id>`

4. **sync_employee_to_crossmark(employee_id)**
   - Syncs employee changes to Crossmark API
   - Used for employee CRUD operations

5. **refresh_events_from_crossmark()**
   - Periodic task to refresh events from Crossmark API
   - Runs every hour if Celery Beat is enabled

## Monitoring

### Check Task Status

You can monitor Celery tasks in several ways:

#### 1. Celery Worker Logs
Watch the Celery worker terminal for task execution logs:
```
[INFO] Task services.sync_service.sync_schedule_to_crossmark[abc-123] received
[INFO] Triggered background sync for schedule 42
[INFO] Task services.sync_service.sync_schedule_to_crossmark[abc-123] succeeded in 1.234s
```

#### 2. Flask Application Logs
The Flask app logs background sync trigger events:
```
INFO: Triggered background sync for schedule 42
WARNING: Failed to trigger background sync: Connection refused
```

#### 3. Flower (Optional Monitoring Tool)
Install Flower for a web-based monitoring UI:
```bash
pip install flower
celery -A services.sync_service.celery_app flower
```

Then visit: http://localhost:5555

### Common Issues

#### Redis Connection Error
```
Error: Redis connection to localhost:6379 failed
```
**Solution:** Make sure Redis server is running (`redis-server`)

#### Celery Worker Not Starting
```
Error: No module named 'app'
```
**Solution:** Make sure you're running the Celery worker from the `scheduler_app` directory

#### Tasks Not Processing
**Solution:** Check that:
1. Redis is running
2. Celery worker is running
3. No errors in Celery worker logs

## Configuration

### Celery Configuration (services/sync_service.py)

```python
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=240,  # 4 minute soft limit
    broker_connection_retry_on_startup=True,
)
```

### Redis Configuration

Default: `redis://localhost:6379/0`

To change, edit `services/sync_service.py`:
```python
celery_app = Celery(
    'scheduler_sync',
    broker='redis://your-redis-host:6379/0',
    backend='redis://your-redis-host:6379/0'
)
```

## Production Deployment

### Using Supervisor (Linux)

Create `/etc/supervisor/conf.d/scheduler-celery.conf`:
```ini
[program:scheduler-celery]
command=/path/to/venv/bin/celery -A services.sync_service.celery_app worker --loglevel=info
directory=/path/to/scheduler_app
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery/worker.log

[program:scheduler-celery-beat]
command=/path/to/venv/bin/celery -A services.sync_service.celery_app beat --loglevel=info
directory=/path/to/scheduler_app
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery/beat.log
```

Then:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start scheduler-celery
sudo supervisorctl start scheduler-celery-beat
```

### Using Systemd (Linux)

Create `/etc/systemd/system/scheduler-celery.service`:
```ini
[Unit]
Description=Scheduler Celery Worker
After=network.target redis.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/scheduler_app
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/celery -A services.sync_service.celery_app worker --loglevel=info --detach

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable scheduler-celery
sudo systemctl start scheduler-celery
```

### Docker Compose

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  web:
    build: .
    ports:
      - "5000:5000"
    depends_on:
      - redis
      - celery
    environment:
      - REDIS_URL=redis://redis:6379/0

  celery:
    build: .
    command: celery -A services.sync_service.celery_app worker --loglevel=info
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379/0

  celery-beat:
    build: .
    command: celery -A services.sync_service.celery_app beat --loglevel=info
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379/0
```

## Testing

### Manual Testing

1. Start all three processes (Redis, Celery worker, Flask app)
2. Create a new schedule through the web interface
3. Watch the Celery worker logs for task execution
4. Verify the schedule appears in Crossmark

### Unit Testing

Create tests for Celery tasks:
```python
from services.sync_service import sync_schedule_to_crossmark

def test_sync_schedule():
    result = sync_schedule_to_crossmark.apply(args=[1])
    assert result.successful()
    assert result.result['success'] == True
```

## Benefits

 **Non-blocking user experience** - Operations complete immediately
 **Automatic retries** - Failed syncs retry automatically with exponential backoff
 **Resilient** - API failures don't block user operations
 **Scalable** - Can add more Celery workers to handle increased load
 **Monitoring** - Easy to monitor task execution and failures
 **Periodic tasks** - Automatic hourly refresh of events

## Troubleshooting

### Check Celery Worker Status
```bash
celery -A services.sync_service.celery_app inspect active
```

### Purge All Tasks
```bash
celery -A services.sync_service.celery_app purge
```

### Check Redis Queue
```bash
redis-cli
> KEYS *
> LLEN celery
```

### View Task Results
```python
from services.sync_service import celery_app
result = celery_app.AsyncResult('task-id-here')
print(result.state)  # PENDING, STARTED, SUCCESS, FAILURE
print(result.result)
```

## Additional Resources

- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Documentation](https://redis.io/documentation)
- [Flask-Celery Patterns](https://flask.palletsprojects.com/en/2.3.x/patterns/celery/)
