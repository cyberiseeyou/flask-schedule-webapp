# Quick Setup Guide: Daily Validation Dashboard

## ✅ Already Completed

The following integration steps have been completed on the `feature/daily-validation-dashboard` branch:

- ✅ Dashboard blueprint registered in `app.py`
- ✅ Navigation link added to `base.html`
- ✅ Audit models registered in `models/__init__.py`
- ✅ All new files committed to git

## 🚀 Next Steps to Get Dashboard Running

### Step 1: Create Database Tables

**Option A - Using Flask Shell** (Recommended):

```bash
cd scheduler_app
python
```

```python
from app import app, db
with app.app_context():
    db.create_all()
    print("✓ Database tables created")
exit()
```

**Option B - Using Flask-Migrate** (if you have migrations set up):

```bash
cd scheduler_app
flask db upgrade
```

### Step 2: Start Your Flask App

```bash
cd scheduler_app
python app.py
```

### Step 3: Access the Dashboard

Open your browser and navigate to:
```
http://localhost:5000/dashboard/daily-validation
```

You should see:
- System Health Score
- Today's event counts
- Rotation assignments
- Validation checks
- Quick action buttons

## 📋 What You'll See

### First Time Viewing Dashboard

On first view, you may see warnings like:
- "No Juicer rotation assigned for [day]"
- "No Primary Lead rotation assigned for [day]"

This is normal! You need to configure rotations first.

### Configure Rotations

1. Navigate to **Rotations** page (in navigation menu)
2. Set up weekly rotation assignments:
   - **Juicer Rotation**: Assign Juicer Baristas for each weekday
   - **Primary Lead Rotation**: Assign Lead Event Specialists for each weekday

### Expected Dashboard Views

**Healthy System (90-100 score)**:
- All events scheduled
- No validation issues
- Rotations configured
- No employee conflicts

**Needs Attention (60-89 score)**:
- Some unscheduled events
- Minor warnings (rotation gaps, missing paperwork)

**Critical (< 60 score)**:
- Urgent unscheduled events
- Employee time-off conflicts
- Multiple critical issues

## 🔧 Optional: Set Up Automated Audits

If you want the system to automatically check for issues every morning:

### 1. Install Celery Dependencies

```bash
pip install celery redis
```

### 2. Start Redis (Celery Broker)

**Windows**:
- Download Redis: https://github.com/microsoftarchive/redis/releases
- Run: `redis-server.exe`

**Linux/Mac**:
```bash
sudo apt install redis-server  # Ubuntu/Debian
brew install redis             # macOS
redis-server
```

### 3. Start Celery Worker and Beat

**Terminal 1 - Celery Worker**:
```bash
cd scheduler_app
celery -A app.celery worker --loglevel=info
```

**Terminal 2 - Celery Beat (Scheduler)**:
```bash
cd scheduler_app
celery -A app.celery beat --loglevel=info
```

### 4. Configure Email Notifications (Optional)

Edit `app.py` to add email settings:

```python
# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@example.com'
app.config['MAIL_PASSWORD'] = 'your-app-password'
```

Install Flask-Mail:
```bash
pip install Flask-Mail
```

## 📊 Dashboard Features

### Health Score
- **90-100**: Excellent - System running smoothly
- **75-89**: Good - Minor issues to review
- **60-74**: Fair - Several issues need attention
- **< 60**: Needs Attention - Critical issues present

### Validation Checks
1. **Urgent Unscheduled**: Events due today/tomorrow unscheduled
2. **Freeosk Gaps**: Freeosk events today without assignments
3. **Digital Gaps**: Digital events today without assignments
4. **Missing Supervisor**: Core events without paired Supervisor events
5. **Time-Off Conflicts**: Employees scheduled during time off
6. **Rotation Unavailable**: Rotation employee has time off
7. **Pending Approvals**: Schedules awaiting approval
8. **3-Day Window**: Events within 3 days unscheduled

### Quick Actions
- **View Today's Calendar**: See all today's assignments
- **Run Auto-Scheduler**: Automatically assign unscheduled events
- **Manage Rotations**: Configure Juicer and Primary Lead rotations
- **Employee Management**: View availability and time off

## 🐛 Troubleshooting

### Dashboard Shows "Template Not Found"
- Verify `scheduler_app/templates/dashboard/daily_validation.html` exists
- Check that `dashboard_bp` is registered in `app.py`

### Dashboard Shows No Data
- Verify database tables were created
- Check that models are registered in `app.config`
- Run `db.create_all()` to ensure tables exist

### Dashboard Shows All Red (Critical Issues)
- This is expected if you haven't:
  - Configured rotations
  - Scheduled any events
  - Set up employee availability
- Follow the setup guide to configure your system

### Navigation Link Not Appearing
- Hard refresh browser (Ctrl+F5)
- Check `base.html` for navigation link
- Verify Flask app restarted after changes

## 📖 Full Documentation

For comprehensive information, see:

- **DAILY_MANAGER_WORKFLOW.md**: Daily routine and best practices
- **SCHEDULING_GUIDE.md**: Complete scheduling system reference
- **INTEGRATION_GUIDE.md**: Detailed setup instructions for all features

## 🎉 You're Done!

The Daily Validation Dashboard is now integrated and ready to use. It will:
- Give you instant visibility into scheduling status
- Flag issues before they become problems
- Help you maintain a healthy, well-scheduled system
- Save you time with quick action buttons

Happy scheduling! 🗓️
