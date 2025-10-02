# Flask Schedule Webapp - Quick Start Guide

## 🚀 First Time Setup (5 minutes)

### Windows
```cmd
# 1. Run setup
setup.bat

# 2. Edit .env file with your settings

# 3. Start the app
start.bat
```

### Linux/Mac
```bash
# 1. Make scripts executable
chmod +x setup.sh start.sh

# 2. Run setup
./setup.sh

# 3. Edit .env file with your settings

# 4. Start the app
./start.sh
```

**Then open:** http://127.0.0.1:5000

---

## 📋 Common Commands

### Start the Application
**Windows:** `start.bat`
**Linux/Mac:** `./start.sh`

### Stop the Application
Press `Ctrl+C` in the terminal

### Activate Virtual Environment
**Windows:** `venv\Scripts\activate`
**Linux/Mac:** `source venv/bin/activate`

### Run Tests
```bash
pytest test_search.py -v
```

### Reset Database
⚠️ **Deletes all data!**
**Windows:** `del scheduler_app\instance\scheduler.db` then re-run `setup.bat`
**Linux/Mac:** `rm scheduler_app/instance/scheduler.db` then re-run `./setup.sh`

---

## 🎯 Key Features to Try

1. **Visual Priority Coding**
   - Go to Unscheduled Events
   - See color-coded priority badges (🔴 Red = Critical, 🟡 Yellow = Urgent, 🟢 Green = Normal)

2. **Universal Search**
   - Use the search bar on events page
   - Try searching for: event names, employee names, store names, dates, IDs
   - Toggle between Scheduling/All/Tracking contexts

3. **Auto-Schedule Supervisor Events**
   - Schedule any Core event
   - Watch the corresponding Supervisor event get auto-scheduled
   - Tuesday-Saturday → Assigned to Club Supervisor at noon
   - Monday/Sunday → Assigned to Lead working that day

4. **Real-time Conflict Detection**
   - When scheduling an event
   - Select employee and date
   - See real-time warnings for conflicts

5. **Paperwork Generation**
   - Dashboard → "Print Today's Paperwork" or "Print Tomorrow's Paperwork"
   - Downloads complete PDF with EDR + Sales Tools

---

## 🔧 Configuration

### Minimum .env Setup
```bash
SECRET_KEY=change-this-to-random-value
DATABASE_URL=sqlite:///instance/scheduler.db
FLASK_ENV=development
```

### Generate Secure Secret Key
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Python not found" | Install Python 3.11+ and add to PATH |
| "Module not found" | Activate venv and run `pip install -r requirements.txt` |
| "Port already in use" | Change port: `flask run --port=8080` |
| ".env not loading" | Ensure file is in project root, check permissions |
| Scripts won't run (Linux/Mac) | Run `chmod +x setup.sh start.sh` |

---

## 📁 Directory Structure

```
flask-schedule-webapp/
├── scheduler_app/          # Main application code
│   ├── models/            # Database models
│   ├── routes/            # URL routes
│   ├── static/            # CSS, JS, images
│   ├── templates/         # HTML templates
│   ├── instance/          # Database file (created by setup)
│   └── logs/              # Application logs (created by setup)
├── docs/                  # Documentation
├── tests/                 # Test files
├── venv/                  # Virtual environment (created by setup)
├── .env                   # Configuration (created by setup)
├── setup.bat              # Windows setup script
├── setup.sh               # Linux/Mac setup script
├── start.bat              # Windows start script
├── start.sh               # Linux/Mac start script
├── requirements.txt       # Python dependencies
└── SETUP.md              # Detailed setup guide
```

---

## 🎓 Learn More

- **Full Setup Guide:** See [SETUP.md](SETUP.md)
- **Features Documentation:** See [docs/enhancements-implemented.md](docs/enhancements-implemented.md)
- **API Documentation:** See [docs/api-documentation.md](docs/api-documentation.md) (if exists)

---

## 🔐 Security Reminders

✅ Change `SECRET_KEY` before production
✅ Never commit `.env` file to git
✅ Use PostgreSQL for production (not SQLite)
✅ Enable HTTPS in production
✅ Set `FLASK_ENV=production` in production

---

## 📞 Support

- Check logs: `scheduler_app/logs/app.log`
- Run tests: `pytest -v`
- Review setup: [SETUP.md](SETUP.md)

---

**Happy Scheduling! 🎉**
