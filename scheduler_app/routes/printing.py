"""
Printing Routes Blueprint
=========================

Handles all printing and download operations for:
- Daily Schedules
- Weekly Schedules
- Employee Schedules
- Event Instructions (salesToolUrls)
- EDRs (Event Detail Reports)
- Daily Item Lists
- Complete Daily Paperwork

Author: Schedule Management System
"""

from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from datetime import datetime, timedelta, date
from routes.auth import require_authentication, get_current_user
import os
import logging
import requests
import re
from PyPDF2 import PdfWriter, PdfReader
from io import BytesIO

# Initialize logger FIRST before any code that might use it
logger = logging.getLogger(__name__)

# Import EDR components
try:
    from edr import EDRReportGenerator, EDRPDFGenerator, DailyItemsListPDFGenerator
    edr_available = True
except ImportError as e:
    logger.warning(f"Could not import EDR modules: {e}")
    edr_available = False
    EDRReportGenerator = None
    EDRPDFGenerator = None
    DailyItemsListPDFGenerator = None

# Import constants
try:
    from constants import WALMART_WEEKS
except ImportError:
    logger.warning("Could not import WALMART_WEEKS mapping")
    WALMART_WEEKS = []

printing_bp = Blueprint('printing', __name__, url_prefix='/printing')

# Global authenticator and generator instances
edr_authenticator = EDRReportGenerator() if edr_available else None
edr_pdf_generator = EDRPDFGenerator() if edr_available else None
daily_items_pdf_generator = DailyItemsListPDFGenerator() if edr_available else None


def get_walmart_week(target_date):
    """
    Get the Walmart week number for a given date.

    Args:
        target_date: date object

    Returns:
        str: Walmart week number (e.g., "Week 36") or None
    """
    for week in WALMART_WEEKS:
        start = datetime.fromisoformat(week['start_date'].replace('Z', '+00:00')).date()
        end = datetime.fromisoformat(week['end_date'].replace('Z', '+00:00')).date()

        if start <= target_date <= end:
            return week['WMWeek']

    return None


@printing_bp.route('/')
@require_authentication()
def printing_home():
    """
    Main printing page with all printing options.
    """
    return render_template('printing.html')


@printing_bp.route('/employees', methods=['GET'])
@require_authentication()
def get_employees():
    """
    Get list of all employees for dropdown.
    """
    try:
        db = current_app.extensions['sqlalchemy']
        Employee = current_app.config['Employee']

        employees = db.session.query(Employee).filter(
            Employee.is_active == True
        ).order_by(Employee.name).all()

        return jsonify({
            'success': True,
            'employees': [{'id': emp.id, 'name': emp.name} for emp in employees]
        })

    except Exception as e:
        logger.error(f"Error getting employees: {str(e)}")
        return jsonify({'error': str(e)}), 500


@printing_bp.route('/daily-schedule', methods=['GET'])
@require_authentication()
def get_daily_schedule():
    """
    Get daily schedule data for a specific date.
    Same as dashboard's print_schedule_by_date route.

    Query Parameters:
        date: Date in YYYY-MM-DD format

    Returns:
        JSON with schedule data
    """
    try:
        # Get date from query params
        date_str = request.args.get('date')
        if not date_str:
            return jsonify({'error': 'Date parameter is required'}), 400

        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Get models from app config
        db = current_app.extensions['sqlalchemy']
        Schedule = current_app.config['Schedule']
        Event = current_app.config['Event']
        Employee = current_app.config['Employee']

        # Get Core and Juicer Production events for the specific day
        # (same logic as dashboard)
        scheduled_events = db.session.query(Schedule, Event, Employee).join(
            Event, Schedule.event_ref_num == Event.project_ref_num
        ).join(
            Employee, Schedule.employee_id == Employee.id
        ).filter(
            db.func.date(Schedule.schedule_datetime) == target_date,
            db.or_(
                Event.event_type == 'Core',
                db.and_(
                    Event.event_type == 'Juicer',
                    Event.project_name.contains('Production'),
                    ~Event.project_name.contains('Survey')
                )
            )
        ).order_by(Schedule.schedule_datetime).all()

        # Build schedule data
        events_data = []
        for schedule, event, employee in scheduled_events:
            events_data.append({
                'employee_name': employee.name,
                'time': schedule.schedule_datetime.strftime('%I:%M %p'),
                'event_name': event.project_name,
                'event_type': event.event_type,
                'minutes': schedule.schedule_datetime.hour * 60 + schedule.schedule_datetime.minute
            })

        return jsonify({
            'success': True,
            'date': target_date.strftime('%Y-%m-%d'),
            'formatted_date': target_date.strftime('%A, %B %d, %Y'),
            'events': events_data
        })

    except Exception as e:
        logger.error(f"Error getting daily schedule: {str(e)}")
        return jsonify({'error': str(e)}), 500


@printing_bp.route('/weekly-schedule', methods=['GET'])
@require_authentication()
def get_weekly_schedule():
    """
    Get weekly schedule data for Sunday-Saturday week.

    Query Parameters:
        start_date: Start date of week in YYYY-MM-DD format (should be a Sunday)

    Returns:
        JSON with weekly schedule data
    """
    try:
        # Get date from query params
        date_str = request.args.get('start_date')
        if not date_str:
            return jsonify({'error': 'start_date parameter is required'}), 400

        start_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Adjust to Sunday if not already
        days_since_sunday = (start_date.weekday() + 1) % 7
        if days_since_sunday != 0:
            start_date = start_date - timedelta(days=days_since_sunday)

        # Calculate end date (Saturday)
        end_date = start_date + timedelta(days=6)

        # Get Walmart week number
        walmart_week = get_walmart_week(start_date)

        # Get models from app config
        db = current_app.extensions['sqlalchemy']
        Schedule = current_app.config['Schedule']
        Event = current_app.config['Event']
        Employee = current_app.config['Employee']

        # Get all events for the week (CORE and Juicer Production)
        scheduled_events = db.session.query(Schedule, Event, Employee).join(
            Event, Schedule.event_ref_num == Event.project_ref_num
        ).join(
            Employee, Schedule.employee_id == Employee.id
        ).filter(
            db.func.date(Schedule.schedule_datetime) >= start_date,
            db.func.date(Schedule.schedule_datetime) <= end_date,
            db.or_(
                Event.event_type == 'Core',
                db.and_(
                    Event.event_type == 'Juicer',
                    Event.project_name.contains('Production'),
                    ~Event.project_name.contains('Survey')
                )
            )
        ).order_by(Schedule.schedule_datetime).all()

        # Organize events by day
        days_data = []
        current_day = start_date

        for i in range(7):
            day_date = current_day + timedelta(days=i)
            day_events = []

            for schedule, event, employee in scheduled_events:
                if schedule.schedule_datetime.date() == day_date:
                    day_events.append({
                        'employee_name': employee.name,
                        'time': schedule.schedule_datetime.strftime('%I:%M %p'),
                        'event_name': event.project_name,
                        'event_type': event.event_type
                    })

            days_data.append({
                'date': day_date.strftime('%Y-%m-%d'),
                'day_of_week': day_date.strftime('%A'),
                'day_of_month': day_date.day,
                'month': day_date.strftime('%B'),
                'events': day_events
            })

        return jsonify({
            'success': True,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'formatted_range': f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}",
            'walmart_week': walmart_week,
            'days': days_data
        })

    except Exception as e:
        logger.error(f"Error getting weekly schedule: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@printing_bp.route('/employee-schedule', methods=['GET'])
@require_authentication()
def get_employee_schedule():
    """
    Get employee bi-weekly schedule (2 weeks) for a specific employee.

    Query Parameters:
        employee_id: Employee ID
        start_date: Start date of first week (will be adjusted to Sunday)
    """
    try:
        # Get parameters
        employee_id = request.args.get('employee_id')
        date_str = request.args.get('start_date')

        if not employee_id:
            return jsonify({'error': 'employee_id parameter is required'}), 400
        if not date_str:
            return jsonify({'error': 'start_date parameter is required'}), 400

        start_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Adjust to Sunday if not already
        days_since_sunday = (start_date.weekday() + 1) % 7
        if days_since_sunday != 0:
            start_date = start_date - timedelta(days=days_since_sunday)

        # Calculate end date (2 weeks = 13 days after start)
        end_date = start_date + timedelta(days=13)

        # Calculate week 2 start date
        week2_start = start_date + timedelta(days=7)

        # Get Walmart week numbers for both weeks
        walmart_week1 = get_walmart_week(start_date)
        walmart_week2 = get_walmart_week(week2_start)

        # Get models from app config
        db = current_app.extensions['sqlalchemy']
        Schedule = current_app.config['Schedule']
        Event = current_app.config['Event']
        Employee = current_app.config['Employee']

        # Get employee info
        employee = db.session.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404

        # Get all schedules for this employee for 2 weeks (CORE and Juicer Production only)
        scheduled_events = db.session.query(Schedule, Event).join(
            Event, Schedule.event_ref_num == Event.project_ref_num
        ).filter(
            Schedule.employee_id == employee_id,
            db.func.date(Schedule.schedule_datetime) >= start_date,
            db.func.date(Schedule.schedule_datetime) <= end_date,
            db.or_(
                Event.event_type == 'Core',
                db.and_(
                    Event.event_type == 'Juicer',
                    Event.project_name.contains('Production'),
                    ~Event.project_name.contains('Survey')
                )
            )
        ).order_by(Schedule.schedule_datetime).all()

        # Organize events by day for both weeks
        week1_days = []
        week2_days = []

        # Week 1 (days 0-6)
        for i in range(7):
            day_date = start_date + timedelta(days=i)
            day_events = []

            for schedule, event in scheduled_events:
                if schedule.schedule_datetime.date() == day_date:
                    day_events.append({
                        'time': schedule.schedule_datetime.strftime('%I:%M %p'),
                        'event_name': event.project_name
                    })

            week1_days.append({
                'date': day_date.strftime('%Y-%m-%d'),
                'day_of_week': day_date.strftime('%A'),
                'day_of_month': day_date.day,
                'month': day_date.strftime('%B'),
                'events': day_events,
                'is_off': len(day_events) == 0
            })

        # Week 2 (days 7-13)
        for i in range(7):
            day_date = week2_start + timedelta(days=i)
            day_events = []

            for schedule, event in scheduled_events:
                if schedule.schedule_datetime.date() == day_date:
                    day_events.append({
                        'time': schedule.schedule_datetime.strftime('%I:%M %p'),
                        'event_name': event.project_name
                    })

            week2_days.append({
                'date': day_date.strftime('%Y-%m-%d'),
                'day_of_week': day_date.strftime('%A'),
                'day_of_month': day_date.day,
                'month': day_date.strftime('%B'),
                'events': day_events,
                'is_off': len(day_events) == 0
            })

        return jsonify({
            'success': True,
            'employee_name': employee.name,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'formatted_range': f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}",
            'walmart_week1': walmart_week1,
            'walmart_week2': walmart_week2,
            'week1_days': week1_days,
            'week2_days': week2_days
        })

    except Exception as e:
        logger.error(f"Error getting employee schedule: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@printing_bp.route('/event-instructions/merge', methods=['POST'])
@require_authentication()
def merge_event_instructions():
    """
    Merge multiple instruction PDFs into a single file.

    Request Body:
        {
            "urls": ["url1", "url2", ...],
            "event_names": ["name1", "name2", ...]
        }

    Returns:
        Merged PDF file
    """
    try:
        data = request.get_json()
        urls = data.get('urls', [])
        event_names = data.get('event_names', [])

        if not urls:
            return jsonify({'error': 'No URLs provided'}), 400

        # Create PDF merger
        pdf_writer = PdfWriter()

        # Download and merge each PDF
        for idx, url in enumerate(urls):
            try:
                logger.info(f"Downloading PDF from: {url}")
                response = requests.get(url, timeout=30)
                response.raise_for_status()

                # Read PDF content
                pdf_reader = PdfReader(BytesIO(response.content))

                # Add all pages from this PDF
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)

                logger.info(f"Successfully added {len(pdf_reader.pages)} pages from {event_names[idx] if idx < len(event_names) else url}")

            except Exception as e:
                logger.error(f"Error processing PDF from {url}: {str(e)}")
                # Continue with other PDFs even if one fails

        # Write merged PDF to BytesIO
        output = BytesIO()
        pdf_writer.write(output)
        output.seek(0)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'instruction_manuals_{timestamp}.pdf'

        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=False,
            download_name=filename
        )

    except Exception as e:
        logger.error(f"Error merging PDFs: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@printing_bp.route('/event-instructions', methods=['GET'])
@require_authentication()
def get_event_instructions():
    """
    Get event instructions (salesToolUrls) for events.

    Query Parameters:
        event_id: Single event ID (6 digits) - for single event
        date: Date in YYYY-MM-DD format - for batch by date
    """
    try:
        event_id = request.args.get('event_id')
        date_str = request.args.get('date')

        db = current_app.extensions['sqlalchemy']
        Event = current_app.config['Event']

        if event_id:
            # Single event lookup - search by first 6 characters of project_name
            event = db.session.query(Event).filter(
                db.func.substr(Event.project_name, 1, 6) == event_id
            ).first()

            if not event:
                return jsonify({
                    'success': False,
                    'error': f'Event starting with "{event_id}" not found in the system'
                }), 404

            if not event.sales_tools_url or event.sales_tools_url.strip() == '':
                return jsonify({
                    'success': False,
                    'error': f'Event "{event.project_name}" does not have an instruction manual URL'
                }), 404

            return jsonify({
                'success': True,
                'event_id': event.project_ref_num,
                'event_name': event.project_name,
                'url': event.sales_tools_url
            })

        elif date_str:
            # Batch lookup - get all CORE events for the date
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            Schedule = current_app.config['Schedule']

            # Get all CORE events scheduled for this date
            events_query = db.session.query(Event).join(
                Schedule, Event.project_ref_num == Schedule.event_ref_num
            ).filter(
                db.func.date(Schedule.schedule_datetime) == target_date,
                Event.event_type == 'Core',
                Event.sales_tools_url.isnot(None),
                Event.sales_tools_url != ''
            ).distinct()

            events = events_query.all()

            if not events:
                return jsonify({
                    'success': False,
                    'error': f'No CORE events with instruction manuals found for {target_date.strftime("%B %d, %Y")}'
                }), 404

            events_data = []
            for event in events:
                events_data.append({
                    'event_id': event.project_ref_num,
                    'event_name': event.project_name,
                    'url': event.sales_tools_url
                })

            return jsonify({
                'success': True,
                'date': target_date.strftime('%Y-%m-%d'),
                'formatted_date': target_date.strftime('%A, %B %d, %Y'),
                'count': len(events_data),
                'events': events_data
            })

        else:
            return jsonify({'error': 'Either event_id or date parameter is required'}), 400

    except Exception as e:
        logger.error(f"Error getting event instructions: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@printing_bp.route('/daily-item-list', methods=['GET'])
@require_authentication()
def get_daily_item_list():
    """
    Get daily item list extracted from EDRs.

    Query Parameters:
        date: Date in YYYY-MM-DD format
    """
    # TODO: Implement daily item list
    return jsonify({'error': 'Not yet implemented'}), 501


@printing_bp.route('/complete-paperwork', methods=['POST'])
@require_authentication()
def get_complete_paperwork():
    """
    Get all paperwork for an entire day.

    Generates a consolidated PDF containing:
    1. Daily Schedule
    2. Item List
    3. For each event:
       - EDR
       - Instructions (Sales Tool)
       - Event Activity Log
       - Daily Checkoff Sheet

    Request Body:
        {
            "date": "YYYY-MM-DD"
        }

    Returns:
        Merged PDF file
    """
    global edr_authenticator

    logger.info("Complete paperwork request received")

    if not edr_available:
        logger.error("EDR modules not available - check import errors on startup")
        return jsonify({'success': False, 'error': 'EDR modules not available'}), 500

    if not edr_authenticator or not edr_authenticator.auth_token:
        logger.error("Not authenticated - auth_token missing")
        return jsonify({'success': False, 'error': 'Not authenticated. Please authenticate first.'}), 401

    try:
        # Import the DailyPaperworkGenerator
        from services.daily_paperwork_generator import DailyPaperworkGenerator

        data = request.get_json()
        date_str = data.get('date')

        if not date_str:
            return jsonify({'success': False, 'error': 'Date is required'}), 400

        # Parse date
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Get database session and models
        db = current_app.extensions['sqlalchemy']
        models_dict = {
            'Event': current_app.config['Event'],
            'Schedule': current_app.config['Schedule'],
            'Employee': current_app.config['Employee']
        }

        # Create DailyPaperworkGenerator instance
        paperwork_generator = DailyPaperworkGenerator(
            db_session=db.session,
            models_dict=models_dict,
            session_api_service=None,  # Optional authenticated session for Crossmark URLs
            edr_generator=edr_authenticator  # Pass authenticated EDR generator
        )

        # Generate complete paperwork
        logger.info(f"Generating complete paperwork for {target_date}")
        output_path = paperwork_generator.generate_complete_daily_paperwork(target_date)

        if not output_path or not os.path.exists(output_path):
            logger.error("Failed to generate complete paperwork")
            return jsonify({
                'success': False,
                'error': 'Failed to generate complete paperwork'
            }), 500

        # Read the generated PDF
        with open(output_path, 'rb') as f:
            pdf_data = f.read()

        output = BytesIO(pdf_data)
        output.seek(0)

        # Clean up temp file
        try:
            os.unlink(output_path)
            paperwork_generator.cleanup()
        except:
            pass

        # Generate filename
        filename = f'Complete_Paperwork_{target_date.strftime("%Y-%m-%d")}.pdf'

        logger.info(f"Successfully generated complete paperwork PDF ({len(pdf_data)} bytes)")

        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=False,
            download_name=filename
        )

    except Exception as e:
        logger.error(f"Failed to generate complete paperwork: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@printing_bp.route('/event-paperwork', methods=['POST'])
@require_authentication()
def get_event_paperwork():
    """
    Get complete paperwork package for a single event.

    Generates a consolidated PDF containing:
    1. EDR (Event Detail Report)
    2. Instructions (Sales Tool PDF)
    3. Event Activity Log
    4. Daily Task Checkoff Sheet

    Request Body:
        {
            "event_number": "123456"  (6-digit event number)
        }

    Returns:
        Merged PDF file
    """
    global edr_authenticator, edr_pdf_generator

    logger.info("Single event paperwork request received")

    if not edr_available:
        logger.error("EDR modules not available - check import errors on startup")
        return jsonify({'success': False, 'error': 'EDR modules not available'}), 500

    if not edr_authenticator or not edr_authenticator.auth_token:
        logger.error("Not authenticated - auth_token missing")
        return jsonify({'success': False, 'error': 'Not authenticated. Please authenticate first.'}), 401

    try:
        data = request.get_json()
        event_number = data.get('event_number', '').strip()

        if not event_number:
            return jsonify({'success': False, 'error': 'Event number is required'}), 400

        # Validate event number format (6 digits)
        if not re.match(r'^\d{6}$', event_number):
            return jsonify({'success': False, 'error': 'Event number must be exactly 6 digits'}), 400

        # Get database models
        db = current_app.extensions['sqlalchemy']
        Event = current_app.config['Event']
        Schedule = current_app.config['Schedule']
        Employee = current_app.config['Employee']

        # Find event by first 6 digits of project_name
        event = db.session.query(Event).filter(
            db.func.substr(Event.project_name, 1, 6) == event_number
        ).first()

        if not event:
            return jsonify({
                'success': False,
                'error': f'Event starting with "{event_number}" not found in the system'
            }), 404

        logger.info(f"Found event: {event.project_name}")

        # Look up employee assigned to this event (most recent schedule)
        schedule = db.session.query(Schedule).filter(
            Schedule.event_ref_num == event.project_ref_num
        ).order_by(Schedule.schedule_datetime.desc()).first()

        employee_name = 'N/A'
        if schedule:
            employee = db.session.query(Employee).filter_by(id=schedule.employee_id).first()
            employee_name = employee.name if employee else schedule.employee_id

        # List to hold all PDF paths for merging
        pdf_buffers = []
        temp_files = []

        # 1. Get EDR PDF
        logger.info(f"Fetching EDR for event {event_number}...")
        try:
            edr_data = edr_authenticator.get_edr_report(event_number)
            if edr_data:
                # Generate EDR PDF
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w+b', suffix='.pdf', delete=False) as tmp_file:
                    edr_temp_path = tmp_file.name

                if edr_pdf_generator.generate_pdf(edr_data, edr_temp_path, employee_name):
                    with open(edr_temp_path, 'rb') as f:
                        edr_buffer = BytesIO(f.read())
                        pdf_buffers.append(edr_buffer)
                    logger.info("✅ EDR PDF added")
                else:
                    logger.warning("⚠️ Failed to generate EDR PDF")

                temp_files.append(edr_temp_path)
            else:
                logger.warning("⚠️ No EDR data retrieved")
        except Exception as e:
            logger.error(f"Error fetching EDR: {str(e)}")
            # Continue without EDR - don't fail entire request

        # 2. Get Instructions PDF (Sales Tool)
        if event.sales_tools_url and event.sales_tools_url.strip():
            logger.info(f"Downloading instructions from: {event.sales_tools_url}")
            try:
                response = requests.get(event.sales_tools_url, timeout=30)
                response.raise_for_status()

                # Verify it's a PDF
                if b'%PDF' in response.content[:4]:
                    instructions_buffer = BytesIO(response.content)
                    pdf_buffers.append(instructions_buffer)
                    logger.info("✅ Instructions PDF added")
                else:
                    logger.warning("⚠️ Instructions URL did not return a valid PDF")
            except Exception as e:
                logger.error(f"Error downloading instructions: {str(e)}")
                # Continue without instructions

        # 3. Add Activity Log (static PDF)
        docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs')
        activity_log_path = os.path.join(docs_dir, 'Event Table Activity Log.pdf')

        if os.path.exists(activity_log_path):
            logger.info("Adding Activity Log...")
            try:
                with open(activity_log_path, 'rb') as f:
                    activity_log_buffer = BytesIO(f.read())
                    pdf_buffers.append(activity_log_buffer)
                logger.info("✅ Activity Log added")
            except Exception as e:
                logger.error(f"Error reading Activity Log: {str(e)}")

        # 4. Add Daily Task Checkoff (static PDF)
        checkoff_path = os.path.join(docs_dir, 'Daily Task Checkoff Sheet.pdf')

        if os.path.exists(checkoff_path):
            logger.info("Adding Daily Task Checkoff...")
            try:
                with open(checkoff_path, 'rb') as f:
                    checkoff_buffer = BytesIO(f.read())
                    pdf_buffers.append(checkoff_buffer)
                logger.info("✅ Daily Task Checkoff added")
            except Exception as e:
                logger.error(f"Error reading Daily Task Checkoff: {str(e)}")

        # Check if we have at least one PDF
        if not pdf_buffers:
            logger.error("No PDFs could be generated or found")
            return jsonify({
                'success': False,
                'error': 'Could not generate any paperwork components. Please ensure EDR authentication is valid and try again.'
            }), 500

        # Merge all PDFs
        logger.info(f"Merging {len(pdf_buffers)} PDFs...")
        pdf_writer = PdfWriter()

        for pdf_buffer in pdf_buffers:
            try:
                pdf_buffer.seek(0)
                pdf_reader = PdfReader(pdf_buffer)
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)
            except Exception as e:
                logger.error(f"Error adding PDF to merger: {str(e)}")

        # Write merged PDF to output buffer
        output = BytesIO()
        pdf_writer.write(output)
        output.seek(0)

        # Clean up temp files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except:
                pass

        # Generate filename
        safe_event_name = re.sub(r'[<>:"/\\|?*]', '_', event.project_name)
        filename = f'Event_Paperwork_{event_number}_{safe_event_name}.pdf'

        logger.info(f"✅ Successfully generated event paperwork ({output.tell()} bytes)")

        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=False,
            download_name=filename
        )

    except Exception as e:
        logger.error(f"Failed to generate event paperwork: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# EDR (Event Detail Report) Endpoints
# ========================================

@printing_bp.route('/edr/request-mfa', methods=['POST'])
@require_authentication()
def edr_request_mfa():
    """
    Request MFA code for Walmart authentication.
    Uses the simple global authenticator approach from edr_downloader.
    """
    global edr_authenticator

    logger.info("EDR MFA request received")

    if not edr_available:
        logger.error("EDR modules not available - check import errors on startup")
        return jsonify({'success': False, 'error': 'EDR modules not available'}), 500

    try:
        # Get Walmart credentials from app config
        username = current_app.config.get('WALMART_EDR_USERNAME')
        password = current_app.config.get('WALMART_EDR_PASSWORD')
        mfa_credential_id = current_app.config.get('WALMART_EDR_MFA_CREDENTIAL_ID')

        if not all([username, password, mfa_credential_id]):
            return jsonify({
                'success': False,
                'error': 'Walmart credentials not configured in settings'
            }), 400

        # Create new EDRReportGenerator instance (NOT EDRAuthenticator)
        edr_authenticator = EDRReportGenerator()
        edr_authenticator.username = username
        edr_authenticator.password = password
        edr_authenticator.mfa_credential_id = mfa_credential_id

        # Step 1: Submit password
        if not edr_authenticator.step1_submit_password():
            return jsonify({'success': False, 'error': 'Failed to submit password'}), 400

        # Step 2: Request MFA code
        if not edr_authenticator.step2_request_mfa_code():
            return jsonify({'success': False, 'error': 'Failed to request MFA code'}), 400

        return jsonify({'success': True, 'message': 'MFA code sent to your phone'})

    except Exception as e:
        logger.error(f"MFA request failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@printing_bp.route('/edr/authenticate', methods=['POST'])
@require_authentication()
def edr_authenticate():
    """
    Complete Walmart authentication with MFA code.
    """
    global edr_authenticator

    logger.info("EDR authentication request received")

    if not edr_available:
        logger.error("EDR modules not available - check import errors on startup")
        return jsonify({'success': False, 'error': 'EDR modules not available'}), 500

    if not edr_authenticator:
        logger.error("No authenticator instance - MFA code must be requested first")
        return jsonify({'success': False, 'error': 'Must request MFA code first'}), 400

    try:
        data = request.get_json()
        mfa_code = data.get('mfa_code', '').strip()

        if not mfa_code:
            return jsonify({'success': False, 'error': 'MFA code is required'}), 400

        # Step 3: Validate MFA code
        if not edr_authenticator.step3_validate_mfa_code(mfa_code):
            return jsonify({'success': False, 'error': 'Invalid MFA code'}), 400

        # Step 4: Register page access
        edr_authenticator.step4_register_page_access()

        # Step 5: Navigate to Event Management
        edr_authenticator.step5_navigate_to_event_management()

        # Step 6: Authenticate with Event Management API
        if not edr_authenticator.step6_authenticate_event_management():
            return jsonify({'success': False, 'error': 'Failed to authenticate with Event Management'}), 400

        return jsonify({'success': True, 'message': 'Authentication successful'})

    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@printing_bp.route('/edr/batch-download', methods=['POST'])
@require_authentication()
def edr_batch_download():
    """
    Download and merge EDR PDFs for all CORE events on the selected date.
    Returns a merged PDF ready for printing.
    """
    global edr_authenticator, edr_pdf_generator

    logger.info("EDR batch download request received")

    if not edr_available:
        logger.error("EDR modules not available - check import errors on startup")
        return jsonify({'success': False, 'error': 'EDR modules not available'}), 500

    if not edr_authenticator or not edr_authenticator.auth_token:
        logger.error("Not authenticated - auth_token missing")
        return jsonify({'success': False, 'error': 'Not authenticated. Please authenticate first.'}), 401

    try:
        data = request.get_json()
        date_str = data.get('date')

        if not date_str:
            return jsonify({'success': False, 'error': 'Date is required'}), 400

        # Parse date
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Get database models
        db = current_app.extensions['sqlalchemy']
        Event = current_app.config['Event']
        Schedule = current_app.config['Schedule']
        Employee = current_app.config['Employee']

        # Query CORE events scheduled on this date
        events = db.session.query(Event).join(
            Schedule, Event.project_ref_num == Schedule.event_ref_num
        ).filter(
            db.func.date(Schedule.schedule_datetime) == target_date,
            Event.event_type == 'Core'
        ).distinct().all()

        if not events:
            logger.warning(f'No CORE events found for {target_date}')
            return jsonify({
                'success': False,
                'error': f'No CORE events found for {target_date.strftime("%B %d, %Y")}'
            }), 404

        logger.info(f'Found {len(events)} CORE events for {target_date}')

        # Process each event and generate PDFs
        pdf_files = []
        failed_events = []

        for event in events:
            # Extract 6-digit event number from project_name
            match = re.search(r'\d{6}', event.project_name)
            event_number = match.group(0) if match else None

            if not event_number:
                logger.warning(f"Could not extract event number from: {event.project_name}")
                failed_events.append({
                    'project_name': event.project_name,
                    'error': 'Could not extract event number'
                })
                continue

            try:
                # Look up employee assigned to this event
                schedule = db.session.query(Schedule).filter(
                    Schedule.event_ref_num == event.project_ref_num,
                    db.func.date(Schedule.schedule_datetime) == target_date
                ).first()

                employee_name = 'N/A'
                if schedule:
                    employee = db.session.query(Employee).filter_by(id=schedule.employee_id).first()
                    employee_name = employee.name if employee else schedule.employee_id

                # Fetch EDR data from Walmart API
                logger.info(f"Downloading EDR for event {event_number}: {event.project_name}")
                edr_data = edr_authenticator.get_edr_report(event_number)

                if not edr_data:
                    failed_events.append({
                        'project_name': event.project_name,
                        'event_number': event_number,
                        'error': 'Failed to retrieve EDR data'
                    })
                    continue

                # Generate PDF in memory
                pdf_buffer = BytesIO()
                safe_filename = re.sub(r'[<>:"/\\|?*]', '_', event.project_name) + '.pdf'

                # Use temp file for PDF generation (ReportLab needs a filename)
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w+b', suffix='.pdf', delete=False) as tmp_file:
                    temp_path = tmp_file.name

                try:
                    if edr_pdf_generator.generate_pdf(edr_data, temp_path, employee_name):
                        # Read the generated PDF
                        with open(temp_path, 'rb') as f:
                            pdf_buffer.write(f.read())
                        pdf_buffer.seek(0)
                        pdf_files.append({
                            'name': event.project_name,
                            'buffer': pdf_buffer
                        })
                        logger.info(f"Successfully generated PDF for {event.project_name}")
                    else:
                        failed_events.append({
                            'project_name': event.project_name,
                            'event_number': event_number,
                            'error': 'Failed to generate PDF'
                        })
                finally:
                    # Clean up temp file
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)

            except Exception as e:
                logger.error(f"Error processing event {event.project_name}: {str(e)}")
                failed_events.append({
                    'project_name': event.project_name,
                    'event_number': event_number,
                    'error': str(e)
                })

        # Merge all PDFs
        if not pdf_files:
            logger.error(f'No EDR PDFs were successfully generated. Failed events: {len(failed_events)}')
            for failure in failed_events:
                logger.error(f"  - {failure.get('project_name', 'Unknown')}: {failure.get('error', 'Unknown error')}")
            return jsonify({
                'success': False,
                'error': 'No EDR PDFs were successfully generated',
                'failed': failed_events
            }), 500

        logger.info(f'Successfully generated {len(pdf_files)} EDR PDFs, merging...')

        # Create merged PDF
        pdf_writer = PdfWriter()

        for pdf_file in pdf_files:
            try:
                pdf_reader = PdfReader(pdf_file['buffer'])
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)
            except Exception as e:
                logger.error(f"Error adding PDF {pdf_file['name']}: {str(e)}")

        # Write merged PDF to output buffer
        output = BytesIO()
        pdf_writer.write(output)
        output.seek(0)

        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f'EDRs_{target_date.strftime("%Y-%m-%d")}_{timestamp}.pdf'

        logger.info(f"Successfully merged {len(pdf_files)} EDR PDFs into {output.tell()} bytes, {len(failed_events)} failed")

        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=False,
            download_name=filename
        )

    except Exception as e:
        logger.error(f"Failed to download EDRs: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@printing_bp.route('/edr/daily-items-list', methods=['POST'])
@require_authentication()
def edr_daily_items_list():
    """
    Generate a consolidated daily items list from all CORE events on the selected date.
    Returns a single PDF with all unique items.
    """
    global edr_authenticator, daily_items_pdf_generator

    logger.info("Daily items list request received")

    if not edr_available:
        logger.error("EDR modules not available - check import errors on startup")
        return jsonify({'success': False, 'error': 'EDR modules not available'}), 500

    if not edr_authenticator or not edr_authenticator.auth_token:
        logger.error("Not authenticated - auth_token missing")
        return jsonify({'success': False, 'error': 'Not authenticated. Please authenticate first.'}), 401

    try:
        data = request.get_json()
        date_str = data.get('date')

        if not date_str:
            return jsonify({'success': False, 'error': 'Date is required'}), 400

        # Parse date
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        date_display = target_date.strftime('%B %d, %Y')

        # Get database models
        db = current_app.extensions['sqlalchemy']
        Event = current_app.config['Event']
        Schedule = current_app.config['Schedule']

        # Query CORE events scheduled on this date
        events = db.session.query(Event).join(
            Schedule, Event.project_ref_num == Schedule.event_ref_num
        ).filter(
            db.func.date(Schedule.schedule_datetime) == target_date,
            Event.event_type == 'Core'
        ).distinct().all()

        if not events:
            logger.warning(f'No CORE events found for {target_date}')
            return jsonify({
                'success': False,
                'error': f'No CORE events found for {date_display}'
            }), 404

        logger.info(f'Found {len(events)} CORE events for {target_date}')

        # Collect EDR data for all events
        edr_data_list = []
        failed_events = []

        for event in events:
            # Extract 6-digit event number from project_name
            match = re.search(r'\d{6}', event.project_name)
            event_number = match.group(0) if match else None

            if not event_number:
                logger.warning(f"Could not extract event number from: {event.project_name}")
                failed_events.append({
                    'project_name': event.project_name,
                    'error': 'Could not extract event number'
                })
                continue

            try:
                # Fetch EDR data from Walmart API
                logger.info(f"Fetching EDR data for event {event_number}: {event.project_name}")
                edr_data = edr_authenticator.get_edr_report(event_number)

                if edr_data:
                    edr_data_list.append(edr_data)
                    logger.info(f"Successfully fetched EDR data for event {event_number}")
                else:
                    failed_events.append({
                        'project_name': event.project_name,
                        'event_number': event_number,
                        'error': 'Failed to retrieve EDR data'
                    })

            except Exception as e:
                logger.error(f"Error fetching EDR data for event {event.project_name}: {str(e)}")
                failed_events.append({
                    'project_name': event.project_name,
                    'event_number': event_number,
                    'error': str(e)
                })

        if not edr_data_list:
            logger.error(f'No EDR data retrieved. Failed events: {len(failed_events)}')
            return jsonify({
                'success': False,
                'error': 'No EDR data could be retrieved',
                'failed': failed_events
            }), 500

        logger.info(f'Successfully retrieved {len(edr_data_list)} EDR reports')

        # Generate daily items list PDF in memory
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w+b', suffix='.pdf', delete=False) as tmp_file:
            temp_path = tmp_file.name

        try:
            if daily_items_pdf_generator.generate_daily_items_pdf(edr_data_list, temp_path, date_display):
                # Read the generated PDF
                with open(temp_path, 'rb') as f:
                    pdf_data = f.read()

                output = BytesIO(pdf_data)
                output.seek(0)

                # Generate filename
                filename = f'Daily_Items_List_{target_date.strftime("%Y-%m-%d")}.pdf'

                logger.info(f"Successfully generated daily items list PDF ({len(pdf_data)} bytes), {len(failed_events)} events failed")

                return send_file(
                    output,
                    mimetype='application/pdf',
                    as_attachment=False,
                    download_name=filename
                )
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to generate daily items list PDF'
                }), 500

        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        logger.error(f"Failed to generate daily items list: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
