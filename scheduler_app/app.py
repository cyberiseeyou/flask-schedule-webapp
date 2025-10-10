from flask import Flask, render_template, abort, jsonify, request, redirect, url_for, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect, generate_csrf
from datetime import datetime, time, date, timedelta
import os
import csv
import io
import logging
from io import StringIO, BytesIO
import requests
import subprocess
import tempfile
import re
import glob
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from config import get_config
from session_api_service import session_api as external_api
from sync_engine import sync_engine
from error_handlers import setup_logging, register_error_handlers, sync_logger, requires_sync_enabled, api_error_handler

# Import EDR reporting functionality
try:
    from edr import EDRReportGenerator
    edr_available = True
except ImportError:
    edr_available = False
    EDRReportGenerator = None

app = Flask(__name__)

# Load configuration
config_class = get_config()
app.config.from_object(config_class)

# Ensure instance directory exists
basedir = os.path.abspath(os.path.dirname(__file__))
os.makedirs(os.path.join(basedir, "instance"), exist_ok=True)

# Update database URI to use absolute path
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:///instance/'):
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "instance", "scheduler.db")}'

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)
external_api.init_app(app)
sync_engine.init_app(app, db)

# Enable foreign key constraints for SQLite
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key constraints for SQLite connections"""
    if 'sqlite' in str(dbapi_conn):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Configure logging and error handling
setup_logging(app)
register_error_handlers(app)

# Initialize database models from models module
from models import init_models
models = init_models(db)
Employee = models['Employee']
Event = models['Event']
Schedule = models['Schedule']
EmployeeWeeklyAvailability = models['EmployeeWeeklyAvailability']
EmployeeAvailability = models['EmployeeAvailability']
EmployeeTimeOff = models['EmployeeTimeOff']
RotationAssignment = models['RotationAssignment']
PendingSchedule = models['PendingSchedule']
SchedulerRunHistory = models['SchedulerRunHistory']
ScheduleException = models['ScheduleException']
SystemSetting = models['SystemSetting']

# Make models available in app config for blueprints
app.config['Employee'] = Employee
app.config['Event'] = Event
app.config['Schedule'] = Schedule
app.config['EmployeeWeeklyAvailability'] = EmployeeWeeklyAvailability
app.config['EmployeeAvailability'] = EmployeeAvailability
app.config['EmployeeTimeOff'] = EmployeeTimeOff
app.config['RotationAssignment'] = RotationAssignment
app.config['PendingSchedule'] = PendingSchedule
app.config['SchedulerRunHistory'] = SchedulerRunHistory
app.config['ScheduleException'] = ScheduleException
app.config['SystemSetting'] = SystemSetting

# Import authentication helpers and blueprint from routes
from routes import (
    auth_bp,
    is_authenticated,
    get_current_user,
    require_authentication,
    session_store
)

# Register blueprints
app.register_blueprint(auth_bp)

# Import and register main blueprint
from routes.main import main_bp
app.register_blueprint(main_bp)

# Import and register scheduling blueprint
from routes.scheduling import scheduling_bp
app.register_blueprint(scheduling_bp)

# Import and register employees blueprint
from routes.employees import employees_bp
app.register_blueprint(employees_bp)

# Import and register API blueprint
from routes.api import api_bp
app.register_blueprint(api_bp)

# Import and register rotations blueprint
from routes.rotations import rotations_bp
app.register_blueprint(rotations_bp)

# Import and register auto-scheduler blueprint
from routes.auto_scheduler import auto_scheduler_bp
app.register_blueprint(auto_scheduler_bp)

# Import and register admin blueprint
from routes.admin import admin_bp
app.register_blueprint(admin_bp)

# Import and register printing blueprint
from routes.printing import printing_bp
app.register_blueprint(printing_bp)

# Import and register Walmart API blueprint
from walmart_api import walmart_bp
app.register_blueprint(walmart_bp)

# Import and register EDR Sync blueprint
from routes.edr_sync import edr_sync_bp
app.register_blueprint(edr_sync_bp)

# Import and register Help blueprint
from routes.help import help_bp
app.register_blueprint(help_bp)

# Configure CSRF exemptions for specific routes (after blueprint registration)
# Only 2 routes are exempt with justified reasons:
# 1. /login (auth.login) - Cannot have CSRF token before authentication session exists
# 2. /api/webhook/schedule_update (admin.webhook_schedule_update) - External webhook (TODO: implement HMAC validation)

# After blueprint registration, view functions are in app.view_functions with 'blueprint.function' naming
# Apply exemptions to the registered view functions
if 'auth.login' in app.view_functions:
    csrf.exempt(app.view_functions['auth.login'])

if 'admin.webhook_schedule_update' in app.view_functions:
    csrf.exempt(app.view_functions['admin.webhook_schedule_update'])

# Setup Walmart API session cleanup
from walmart_api import session_manager
import threading

def cleanup_walmart_sessions():
    """Background task to cleanup expired Walmart sessions."""
    with app.app_context():
        session_manager.cleanup_expired_sessions()
    # Schedule next cleanup in 60 seconds
    threading.Timer(60.0, cleanup_walmart_sessions).start()

# Start session cleanup background task
cleanup_walmart_sessions()

@app.context_processor
def inject_user():
    """Make get_current_user available in templates"""
    return dict(get_current_user=get_current_user)

@app.after_request
def add_csrf_token_cookie(response):
    """
    Add CSRF token to cookie for AJAX requests.

    This allows JavaScript to read the token and include it in AJAX request headers.
    The token is validated on the server side for all POST/PUT/DELETE requests.
    """
    if request.endpoint and not request.endpoint.startswith('static'):
        # Generate and set CSRF token in cookie
        csrf_token = generate_csrf()
        response.set_cookie(
            'csrf_token',
            csrf_token,
            secure=app.config.get('SESSION_COOKIE_SECURE', False),  # HTTPS only in production
            httponly=False,  # Must be readable by JavaScript
            samesite='Lax'  # Provides CSRF protection while allowing normal navigation
        )
    return response

def init_db():
    db_path = os.path.join(basedir, "instance", "scheduler.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)