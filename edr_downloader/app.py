"""
EDR Downloader Flask Application.

A lightweight web application for downloading Event Detail Reports (EDR) from
Walmart's Retail Link Event Management System for CORE events scheduled on
a specific date.

This application provides a simple web interface that allows users to:
    1. Authenticate with Walmart Retail Link using MFA
    2. Select a date to view CORE events
    3. Download EDR PDF reports for all CORE events on that date

The application queries the local scheduler database to find CORE events,
then fetches their corresponding EDR data from Walmart's API and generates
PDF documents suitable for printing and employee signatures.

Architecture:
    - Flask web framework for HTTP server and routing
    - SQLAlchemy for database access (read-only access to scheduler.db)
    - EDRAuthenticator for Walmart API authentication
    - EDRPDFGenerator for PDF creation

API Endpoints:
    GET  /                     - Main page with date picker
    POST /api/request-mfa      - Request MFA code via SMS
    POST /api/authenticate     - Complete authentication with MFA code
    POST /api/get-events       - Get CORE events for a specific date
    POST /api/download-edrs    - Download all EDR PDFs for a date

Port: 5001 (to avoid conflict with main scheduler on port 5000)

Author: Schedule Management System
Version: 1.0
"""
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import logging
import re
from config import Config
from models import db, Event, Schedule, Employee
from authenticator import EDRAuthenticator
from pdf_generator import EDRPDFGenerator

# Configure logging to show INFO level messages and above
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Initialize database connection with Flask app
db.init_app(app)

# Global authenticator instance (persists across requests during session)
# This maintains the authentication state and session cookies
authenticator = None

# PDF generator instance (stateless, can be reused across requests)
pdf_generator = EDRPDFGenerator()


@app.route('/')
def index():
    """
    Main page with date picker and download interface.

    Serves the primary user interface where users can:
        - Request MFA authentication
        - Enter MFA code to complete login
        - Select a date to view CORE events
        - Download EDR reports for all events on that date

    Returns:
        str: Rendered HTML template for the main page

    Template: index.html
    """
    return render_template('index.html')


@app.route('/api/request-mfa', methods=['POST'])
def request_mfa():
    """
    Step 1 of authentication: Request MFA code to be sent via SMS.

    Initiates the authentication flow by:
        1. Creating a new EDRAuthenticator instance with credentials from config
        2. Submitting username/password to Walmart Retail Link
        3. Requesting an SMS OTP code to be sent to the registered phone

    The global authenticator instance is stored to maintain session state
    for the subsequent authentication step.

    Request Body: None required

    Returns:
        JSON response with structure:
        {
            'success': bool,
            'message': str (on success),
            'error': str (on failure)
        }

    Status Codes:
        200: MFA code sent successfully
        400: Failed to submit password or request MFA
        500: Unexpected server error

    Example:
        POST /api/request-mfa
        Response: {"success": true, "message": "MFA code sent to your phone"}

    Notes:
        - Credentials are loaded from app.config (environment variables or defaults)
        - The MFA code is typically received within 30-60 seconds
        - The authenticator session persists in memory until authentication completes
    """
    global authenticator

    try:
        # Initialize authenticator with credentials from configuration
        authenticator = EDRAuthenticator(
            username=app.config['WALMART_EDR_USERNAME'],
            password=app.config['WALMART_EDR_PASSWORD'],
            mfa_credential_id=app.config['WALMART_EDR_MFA_CREDENTIAL_ID']
        )

        # Step 1: Submit username and password
        if not authenticator.step1_submit_password():
            return jsonify({'success': False, 'error': 'Failed to submit password'}), 400

        # Step 2: Request MFA code to be sent via SMS
        if not authenticator.step2_request_mfa_code():
            return jsonify({'success': False, 'error': 'Failed to request MFA code'}), 400

        return jsonify({'success': True, 'message': 'MFA code sent to your phone'})

    except Exception as e:
        logger.error(f"MFA request failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/authenticate', methods=['POST'])
def authenticate():
    """
    Step 2 of authentication: Complete authentication with MFA code.

    Validates the SMS OTP code and completes the authentication flow by:
        1. Validating the MFA code entered by the user
        2. Registering page access with Walmart's analytics
        3. Navigating to Event Management system
        4. Obtaining the authentication token for API access

    The authenticator instance must have been initialized via /api/request-mfa
    before calling this endpoint.

    Request Body (JSON):
        {
            'mfa_code': str  # 6-digit OTP code from SMS
        }

    Returns:
        JSON response with structure:
        {
            'success': bool,
            'message': str (on success),
            'error': str (on failure)
        }

    Status Codes:
        200: Authentication successful, ready to make API calls
        400: MFA code validation failed or missing prerequisites
        500: Unexpected server error

    Prerequisites:
        - /api/request-mfa must have been called successfully
        - MFA code must be valid and not expired (typically 5-10 min expiry)

    Example:
        POST /api/authenticate
        Body: {"mfa_code": "123456"}
        Response: {"success": true, "message": "Authentication successful"}

    Notes:
        - After successful authentication, the auth token is stored in authenticator
        - The token persists in memory for the lifetime of the server process
        - Invalid code attempts are tracked and may trigger account lockout
    """
    global authenticator

    # Verify that MFA request was made first
    if not authenticator:
        return jsonify({'success': False, 'error': 'Must request MFA code first'}), 400

    # Extract and validate MFA code from request
    data = request.get_json()
    mfa_code = data.get('mfa_code', '').strip()

    if not mfa_code:
        return jsonify({'success': False, 'error': 'MFA code is required'}), 400

    try:
        # Step 3: Validate the MFA code
        if not authenticator.step3_validate_mfa_code(mfa_code):
            return jsonify({'success': False, 'error': 'Invalid MFA code'}), 400

        # Step 4: Register page access (analytics tracking)
        authenticator.step4_register_page_access()

        # Step 5: Navigate to Event Management page
        authenticator.step5_navigate_to_event_management()

        # Step 6: Obtain authentication token from Event Management API
        if not authenticator.step6_authenticate_event_management():
            return jsonify({'success': False, 'error': 'Failed to authenticate with Event Management'}), 400

        return jsonify({'success': True, 'message': 'Authentication successful'})

    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/get-events', methods=['POST'])
def get_events():
    """
    Get all CORE events scheduled for a specific date.

    Queries the local scheduler database to find all events of type 'Core'
    that are scheduled on the specified date. Returns event details including
    the 6-digit event number needed for EDR report retrieval.

    Request Body (JSON):
        {
            'date': str  # Date in YYYY-MM-DD format (e.g., "2024-01-15")
        }

    Returns:
        JSON response with structure:
        {
            'success': bool,
            'count': int,  # Number of events found
            'events': [
                {
                    'id': int,
                    'project_name': str,
                    'event_number': str,  # 6-digit event ID
                    'store_name': str,
                    'scheduled_datetime': str  # ISO 8601 format
                },
                ...
            ],
            'error': str (on failure)
        }

    Status Codes:
        200: Success (may return 0 events)
        400: Missing or invalid date parameter
        500: Database or server error

    Example:
        POST /api/get-events
        Body: {"date": "2024-01-15"}
        Response: {
            "success": true,
            "count": 3,
            "events": [
                {
                    "id": 123,
                    "project_name": "456789 - Food Demo at Store",
                    "event_number": "456789",
                    "store_name": "Walmart Supercenter #1234",
                    "scheduled_datetime": "2024-01-15T10:00:00"
                }
            ]
        }

    Notes:
        - Only returns events with event_type='Core'
        - Event number is extracted from project_name using regex
        - Events without a 6-digit number in the name are excluded
        - Multiple schedules for the same event are deduplicated
    """
    # Extract and validate date from request
    data = request.get_json()
    selected_date = data.get('date')

    if not selected_date:
        return jsonify({'success': False, 'error': 'Date is required'}), 400

    try:
        # Parse the date string to datetime object
        date_obj = datetime.strptime(selected_date, '%Y-%m-%d')

        # Query events that are scheduled on this date and are CORE type
        # Join with schedules table to filter by scheduled date
        events = db.session.query(Event).join(
            Schedule, Event.project_ref_num == Schedule.event_ref_num
        ).filter(
            db.func.date(Schedule.schedule_datetime) == date_obj.date(),
            Event.event_type == 'Core'
        ).distinct().all()

        # Build response with event information
        event_list = []
        for event in events:
            # Extract 6-digit event number from project_name
            # Event names typically follow format: "123456 - Description"
            match = re.search(r'\d{6}', event.project_name)
            event_number = match.group(0) if match else None

            # Only include events with valid event numbers
            if event_number:
                # Get the schedule record for this event on the selected date
                schedule = Schedule.query.filter(
                    Schedule.event_ref_num == event.project_ref_num,
                    db.func.date(Schedule.schedule_datetime) == date_obj.date()
                ).first()

                event_list.append({
                    'id': event.id,
                    'project_name': event.project_name,
                    'event_number': event_number,
                    'store_name': event.store_name,
                    'scheduled_datetime': schedule.schedule_datetime.isoformat() if schedule else None
                })

        return jsonify({
            'success': True,
            'count': len(event_list),
            'events': event_list
        })

    except Exception as e:
        logger.error(f"Failed to get events: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/download-edrs', methods=['POST'])
def download_edrs():
    """
    Download EDR PDF reports for all CORE events on the selected date.

    Fetches EDR data from Walmart's Event Management API for each CORE event
    scheduled on the specified date, then generates PDF documents with employee
    signature sections. PDFs are saved to the temp_edrs folder.

    This is the main workflow endpoint that:
        1. Queries database for CORE events on the date
        2. For each event:
           - Extracts the 6-digit event number
           - Fetches EDR data from Walmart API
           - Looks up the assigned employee name
           - Generates a PDF with event details and signature section
        3. Returns summary of successful downloads and failures

    Request Body (JSON):
        {
            'date': str  # Date in YYYY-MM-DD format
        }

    Returns:
        JSON response with structure:
        {
            'success': bool,
            'downloaded': int,  # Count of successful downloads
            'failed': int,      # Count of failures
            'files': [          # List of successfully downloaded files
                {
                    'project_name': str,
                    'event_number': str,
                    'filename': str  # PDF filename
                },
                ...
            ],
            'errors': [         # List of failed events
                {
                    'project_name': str,
                    'event_number': str,
                    'error': str  # Error description
                },
                ...
            ],
            'error': str (on complete failure)
        }

    Status Codes:
        200: At least partial success (some PDFs may have failed)
        400: Missing or invalid date parameter
        401: Not authenticated (must call /api/authenticate first)
        404: No CORE events found for the date
        500: Unexpected server error

    Prerequisites:
        - Must be authenticated via /api/authenticate
        - Valid auth_token must be present in authenticator

    Example:
        POST /api/download-edrs
        Body: {"date": "2024-01-15"}
        Response: {
            "success": true,
            "downloaded": 2,
            "failed": 1,
            "files": [
                {
                    "project_name": "123456 - Food Demo",
                    "event_number": "123456",
                    "filename": "123456 - Food Demo.pdf"
                }
            ],
            "errors": [
                {
                    "project_name": "789012 - Beverage Demo",
                    "event_number": "789012",
                    "error": "Failed to retrieve EDR data"
                }
            ]
        }

    Notes:
        - PDFs are saved to Config.TEMP_EDR_FOLDER
        - Filename uses full project_name (sanitized for filesystem)
        - Employee name is looked up from database and included in PDF
        - Partial failures are acceptable (returns 200 with error list)
        - If ALL events fail, returns 200 with downloaded=0
    """
    global authenticator

    # Verify authentication before proceeding
    if not authenticator or not authenticator.auth_token:
        return jsonify({'success': False, 'error': 'Not authenticated. Please authenticate first.'}), 401

    # Extract and validate date from request
    data = request.get_json()
    selected_date = data.get('date')

    if not selected_date:
        return jsonify({'success': False, 'error': 'Date is required'}), 400

    try:
        # Parse the date string to datetime object
        date_obj = datetime.strptime(selected_date, '%Y-%m-%d')

        # Query CORE events scheduled on this date
        # Join with schedules table to filter by scheduled date
        events = db.session.query(Event).join(
            Schedule, Event.project_ref_num == Schedule.event_ref_num
        ).filter(
            db.func.date(Schedule.schedule_datetime) == date_obj.date(),
            Event.event_type == 'Core'
        ).distinct().all()

        # Return error if no events found
        if not events:
            return jsonify({'success': False, 'error': 'No CORE events found for this date'}), 404

        # Process each event and track successes/failures
        downloaded_files = []
        failed_events = []

        for event in events:
            # Extract 6-digit event number from project_name
            # Event names typically follow format: "123456 - Description"
            match = re.search(r'\d{6}', event.project_name)
            event_number = match.group(0) if match else None

            # Skip events without valid event numbers
            if not event_number:
                logger.warning(f"Could not extract event number from: {event.project_name}")
                failed_events.append({
                    'project_name': event.project_name,
                    'error': 'Could not extract event number'
                })
                continue

            try:
                # Look up the employee assigned to this event on the selected date
                schedule = Schedule.query.filter(
                    Schedule.event_ref_num == event.project_ref_num,
                    db.func.date(Schedule.schedule_datetime) == date_obj.date()
                ).first()

                # Get employee name for PDF signature line
                employee_name = 'N/A'
                if schedule:
                    employee = Employee.query.filter_by(id=schedule.employee_id).first()
                    employee_name = employee.name if employee else schedule.employee_id

                # Fetch EDR data from Walmart API
                logger.info(f"Downloading EDR for event {event_number}: {event.project_name}")
                edr_data = authenticator.get_edr_report(event_number)

                # Handle failed API request
                if not edr_data:
                    failed_events.append({
                        'project_name': event.project_name,
                        'event_number': event_number,
                        'error': 'Failed to retrieve EDR data'
                    })
                    continue

                # Generate PDF filename using full event name
                # Sanitize filename by removing invalid filesystem characters
                safe_filename = re.sub(r'[<>:"/\\|?*]', '_', event.project_name)
                pdf_filename = os.path.join(
                    app.config['TEMP_EDR_FOLDER'],
                    f"{safe_filename}.pdf"
                )

                # Generate PDF document with event data and employee name
                if pdf_generator.generate_pdf(edr_data, pdf_filename, employee_name):
                    downloaded_files.append({
                        'project_name': event.project_name,
                        'event_number': event_number,
                        'filename': os.path.basename(pdf_filename)
                    })
                    logger.info(f"Successfully generated PDF: {pdf_filename}")
                else:
                    failed_events.append({
                        'project_name': event.project_name,
                        'event_number': event_number,
                        'error': 'Failed to generate PDF'
                    })

            except Exception as e:
                # Log and track any unexpected errors during processing
                logger.error(f"Error processing event {event.project_name}: {str(e)}")
                failed_events.append({
                    'project_name': event.project_name,
                    'event_number': event_number,
                    'error': str(e)
                })

        return jsonify({
            'success': True,
            'downloaded': len(downloaded_files),
            'failed': len(failed_events),
            'files': downloaded_files,
            'errors': failed_events
        })

    except Exception as e:
        logger.error(f"Failed to download EDRs: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    # Run startup checks before starting the server
    with app.app_context():
        # Verify that the database file exists
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if not os.path.exists(db_path):
            logger.error("Database not found! Please ensure scheduler.db is in the instance folder.")
            logger.error(f"Expected location: {db_path}")
        else:
            logger.info("Database found successfully")
            logger.info(f"Database location: {db_path}")

    # Start Flask development server
    # Port 5001 is used to avoid conflict with main scheduler application on port 5000
    # host='0.0.0.0' allows access from other machines on the network
    app.run(debug=True, host='0.0.0.0', port=5001)
