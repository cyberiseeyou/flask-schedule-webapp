from flask import Flask, render_template, abort, jsonify, request, redirect, url_for, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
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
from scheduler_app.config import get_config
from scheduler_app.session_api_service import session_api as external_api
from scheduler_app.sync_engine import sync_engine
from scheduler_app.error_handlers import setup_logging, register_error_handlers, sync_logger, requires_sync_enabled, api_error_handler

# Import EDR reporting functionality
try:
    from product_connections_implementation.edr_printer import EDRReportGenerator
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

# Configure logging and error handling
setup_logging(app)
register_error_handlers(app)

# Initialize database models from models module
from scheduler_app.models import init_models
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
from scheduler_app.routes import (
    auth_bp,
    is_authenticated,
    get_current_user,
    require_authentication,
    session_store
)

# Register blueprints
app.register_blueprint(auth_bp)

# Import and register main blueprint
from scheduler_app.routes.main import main_bp
app.register_blueprint(main_bp)

# Import and register scheduling blueprint
from scheduler_app.routes.scheduling import scheduling_bp
app.register_blueprint(scheduling_bp)

# Import and register employees blueprint
from scheduler_app.routes.employees import employees_bp
app.register_blueprint(employees_bp)

# Import and register API blueprint
from scheduler_app.routes.api import api_bp
app.register_blueprint(api_bp)

# Import and register rotations blueprint
from scheduler_app.routes.rotations import rotations_bp
app.register_blueprint(rotations_bp)

# Import and register auto-scheduler blueprint
from scheduler_app.routes.auto_scheduler import auto_scheduler_bp
app.register_blueprint(auto_scheduler_bp)

# Import and register admin blueprint
from scheduler_app.routes.admin import admin_bp
app.register_blueprint(admin_bp)

@app.context_processor
def inject_user():
    """Make get_current_user available in templates"""
    return dict(get_current_user=get_current_user)

def init_db():
    db_path = os.path.join(basedir, "instance", "scheduler.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)