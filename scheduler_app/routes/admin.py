"""
Admin routes blueprint
Handles admin operations, sync management, testing, and utility endpoints
"""
from flask import Blueprint, render_template, request, jsonify, current_app, abort, make_response
from scheduler_app.routes.auth import require_authentication
from datetime import datetime, timedelta, date, time
from io import BytesIO
import requests
import re
import logging

admin_bp = Blueprint('admin', __name__)


def _get_edr_credentials():
    """
    Get EDR credentials from SystemSetting with config fallback
    Returns: tuple (username, password, mfa_credential_id)
    """
    SystemSetting = current_app.config.get('SystemSetting')

    if SystemSetting:
        username = SystemSetting.get_setting('edr_username') or current_app.config.get('WALMART_EDR_USERNAME')
        password = SystemSetting.get_setting('edr_password') or current_app.config.get('WALMART_EDR_PASSWORD')
        mfa_credential_id = SystemSetting.get_setting('edr_mfa_credential_id') or current_app.config.get('WALMART_EDR_MFA_CREDENTIAL_ID')
    else:
        # Fallback to config if SystemSetting not available
        username = current_app.config.get('WALMART_EDR_USERNAME')
        password = current_app.config.get('WALMART_EDR_PASSWORD')
        mfa_credential_id = current_app.config.get('WALMART_EDR_MFA_CREDENTIAL_ID')

    return username, password, mfa_credential_id


@admin_bp.route('/api/refresh/database', methods=['POST'])
@require_authentication()
def refresh_database():
    """
    Completely refresh database with latest planning events from Crossmark API
    Clears all existing events and replaces with fresh data
    Fetches events from 1 month before to 1 month after current date
    """
    try:
        db = current_app.extensions['sqlalchemy']
        Event = current_app.config['Event']
        Schedule = current_app.config['Schedule']
        Employee = current_app.config['Employee']
        from scheduler_app.session_api_service import session_api as external_api

        current_app.logger.info("Starting complete database refresh from Crossmark API")

        # Get all planning events using the new comprehensive method
        events_data = external_api.get_all_planning_events()

        if not events_data:
            return jsonify({
                'success': False,
                'message': 'Failed to fetch events from Crossmark API'
            }), 500

        # Process and completely replace database
        # Events are in 'mplans' array, not 'records'
        records = events_data.get('mplans', [])
        total_fetched = len(records)

        # CLEAR ALL EXISTING EVENTS FIRST
        current_app.logger.info("Clearing all existing events from database")
        existing_count = Event.query.count()

        # Clear related schedules first (foreign key constraint)
        Schedule.query.delete()

        # Clear all events
        Event.query.delete()

        # Commit the deletions
        db.session.commit()
        current_app.logger.info(f"Cleared {existing_count} existing events from database")

        # Now insert all fresh events
        created_count = 0

        # Log first event structure to see all available fields
        if records:
            current_app.logger.info(f"Sample event record keys: {list(records[0].keys())}")
            current_app.logger.info(f"Sample event record: {records[0]}")

        for event_record in records:
            try:
                # Extract event data
                mplan_id = event_record.get('mPlanID')
                if not mplan_id:
                    continue

                # Create new event (all events are new since we cleared the database)
                # Map the mplans field names to Event model fields

                # Parse dates from MM/DD/YYYY format
                start_date = None
                end_date = None
                schedule_date = None

                try:
                    if event_record.get('startDate'):
                        start_date = datetime.strptime(event_record['startDate'], '%m/%d/%Y')
                except ValueError:
                    start_date = datetime.utcnow()

                try:
                    if event_record.get('endDate'):
                        end_date = datetime.strptime(event_record['endDate'], '%m/%d/%Y')
                except ValueError:
                    end_date = datetime.utcnow()

                try:
                    # Parse scheduleDate which is in format "MM/DD/YYYY HH:MM:SS AM/PM"
                    if event_record.get('scheduleDate'):
                        schedule_date = datetime.strptime(event_record['scheduleDate'], '%m/%d/%Y %I:%M:%S %p')
                except ValueError:
                    schedule_date = start_date

                # Get the condition from the event record
                condition = event_record.get('condition', 'Unstaffed')

                # Determine if event is scheduled based on new logic
                # Only Unstaffed is truly unscheduled
                is_event_scheduled = condition != 'Unstaffed'

                # Extract SalesToolURL from the event record
                # It's nested under salesTools array: salesTools[0].salesToolURL
                sales_tools_url = None
                sales_tools = event_record.get('salesTools', [])
                if sales_tools and len(sales_tools) > 0 and isinstance(sales_tools, list):
                    sales_tools_url = sales_tools[0].get('salesToolURL') if isinstance(sales_tools[0], dict) else None

                new_event = Event(
                    external_id=str(mplan_id),
                    project_name=event_record.get('name', ''),
                    project_ref_num=int(mplan_id) if str(mplan_id).isdigit() else 0,
                    location_mvid=event_record.get('storeID', ''),
                    store_name=event_record.get('storeName', ''),
                    start_datetime=start_date or datetime.utcnow(),  # Scheduling window start
                    due_datetime=end_date or datetime.utcnow(),  # Scheduling window end/due
                    is_scheduled=is_event_scheduled,
                    condition=condition,  # Store the actual condition
                    sales_tools_url=sales_tools_url,  # Store SalesToolURL
                    last_synced=datetime.utcnow(),
                    sync_status='synced'
                )
                # Detect event type based on project name
                new_event.event_type = new_event.detect_event_type()
                db.session.add(new_event)
                created_count += 1

                # Log if SalesToolURL was found for this event
                if sales_tools_url:
                    current_app.logger.info(f"Event {mplan_id} ({event_record.get('name', 'Unknown')}): Found SalesToolURL: {sales_tools_url}")
                else:
                    current_app.logger.warning(f"Event {mplan_id} ({event_record.get('name', 'Unknown')}): No SalesToolURL found in salesTools array")

                # If event has a schedule date, create a Schedule record
                if schedule_date and is_event_scheduled:
                    # Get the assigned employee from the API data
                    staffed_reps = event_record.get('staffedReps', '')
                    schedule_rep_id = event_record.get('scheduleRepID', '')

                    # Try to find the employee by name or ID
                    employee_id = None

                    if staffed_reps:
                        # Get the first staffed rep name
                        first_rep_name = staffed_reps.split(',')[0].strip()

                        # Try to find the employee by name
                        employee = Employee.query.filter_by(name=first_rep_name).first()
                        if employee:
                            employee_id = employee.id
                        else:
                            # If not found by exact name, use the schedule rep ID if available
                            if schedule_rep_id:
                                employee_id = f"US{schedule_rep_id}" if not str(schedule_rep_id).startswith('US') else str(schedule_rep_id)
                            else:
                                # Last resort - store the name and we'll need to handle it in queries
                                employee_id = first_rep_name

                    elif schedule_rep_id:
                        # Use the schedule rep ID if available
                        employee_id = f"US{schedule_rep_id}" if not str(schedule_rep_id).startswith('US') else str(schedule_rep_id)

                    if employee_id:
                        schedule = Schedule(
                            event_ref_num=int(mplan_id) if str(mplan_id).isdigit() else 0,
                            employee_id=employee_id,
                            schedule_datetime=schedule_date,
                            external_id=f"{mplan_id}_schedule",
                            last_synced=datetime.utcnow()
                        )
                        db.session.add(schedule)

            except Exception as e:
                current_app.logger.error(f"Error processing event {event_record.get('mPlanID', 'unknown')}: {str(e)}")
                continue

        # Commit all new events
        db.session.commit()

        current_app.logger.info(f"Database refresh completed: Cleared {existing_count} old events, created {created_count} new events from {total_fetched} fetched")

        # Check for Staffed events without schedule records - these need attention
        from sqlalchemy import select
        staffed_without_schedule = Event.query.filter(
            Event.condition == 'Staffed',
            ~Event.project_ref_num.in_(
                select(Schedule.event_ref_num)
            )
        ).all()

        warning_message = None
        if staffed_without_schedule:
            warning_message = f"WARNING: {len(staffed_without_schedule)} events are marked as 'Staffed' but have no schedule records. Please schedule these events or the system will not handle them properly."
            current_app.logger.warning(warning_message)

        return jsonify({
            'success': True,
            'message': f'Database completely refreshed with fresh data',
            'stats': {
                'total_fetched': total_fetched,
                'cleared': existing_count,
                'created': created_count
            },
            'warning': warning_message
        })

    except Exception as e:
        db = current_app.extensions['sqlalchemy']
        db.session.rollback()
        current_app.logger.error(f"Database refresh failed: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Database refresh failed: {str(e)}'
        }), 500

@admin_bp.route('/api/refresh/status')
@require_authentication()
def refresh_status():
    """Get status of database refresh progress"""
    try:
        Event = current_app.config['Event']

        # Get total events count and last sync info
        total_events = Event.query.count()
        synced_events = Event.query.filter_by(sync_status='synced').count()
        last_sync = Event.query.filter(Event.last_synced.isnot(None)).order_by(Event.last_synced.desc()).first()

        return jsonify({
            'success': True,
            'stats': {
                'total_events': total_events,
                'synced_events': synced_events,
                'last_sync': last_sync.last_synced.isoformat() if last_sync and last_sync.last_synced else None
            }
        })
    except Exception as e:
        current_app.logger.error(f"Failed to get refresh status: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to get refresh status'
        }), 500

@admin_bp.route('/delete_event/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    """Delete an event from the database"""
    try:
        db = current_app.extensions['sqlalchemy']
        Event = current_app.config['Event']
        Schedule = current_app.config['Schedule']

        # Find the event
        event = db.session.get(Event, event_id)
        if not event:
            return jsonify({'success': False, 'message': 'Event not found'}), 404

        # Check if event is scheduled - if so, also delete the schedule
        schedules = Schedule.query.filter_by(event_ref_num=event.project_ref_num).all()
        for schedule in schedules:
            db.session.delete(schedule)

        # Delete the event
        event_name = event.project_name
        db.session.delete(event)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Event "{event_name}" has been removed successfully'
        })

    except Exception as e:
        db = current_app.extensions['sqlalchemy']
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error removing event: {str(e)}'
        }), 500

@admin_bp.route('/api/sync/health')
def sync_health():
    """Check sync system health and API connectivity"""
    try:
        from scheduler_app.session_api_service import session_api as external_api

        health_status = external_api.health_check()
        return jsonify({
            'sync_enabled': current_app.config.get('SYNC_ENABLED', False),
            'external_api': health_status,
            'database': {'status': 'healthy', 'message': 'Database accessible'},
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'sync_enabled': current_app.config.get('SYNC_ENABLED', False),
            'external_api': {'status': 'unhealthy', 'message': str(e)},
            'database': {'status': 'healthy', 'message': 'Database accessible'},
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@admin_bp.route('/api/sync/trigger', methods=['POST'])
def trigger_sync():
    """Manually trigger a complete synchronization"""
    from error_handlers import requires_sync_enabled, api_error_handler, sync_logger
    from sync_engine import sync_engine

    # Apply decorators programmatically
    requires_sync_enabled_check = requires_sync_enabled(lambda: None)
    if hasattr(requires_sync_enabled_check, '__wrapped__'):
        # Decorator returned an error response
        return requires_sync_enabled_check

    sync_logger.sync_started('manual_full_sync', 'Triggered by user')
    result = sync_engine.sync_all()

    if result['status'] == 'success':
        sync_logger.sync_completed('manual_full_sync', result)
    else:
        sync_logger.sync_warning('manual_full_sync', f"Sync completed with status: {result['status']}")

    status_code = 200 if result['status'] == 'success' else 207 if result['status'] == 'partial' else 500
    return jsonify(result), status_code

@admin_bp.route('/api/sync/status')
def sync_status():
    """Get synchronization status overview"""
    try:
        db = current_app.extensions['sqlalchemy']
        Employee = current_app.config['Employee']
        Event = current_app.config['Event']
        Schedule = current_app.config['Schedule']

        # Get sync statistics
        pending_employees = Employee.query.filter_by(sync_status='pending').count()
        failed_employees = Employee.query.filter_by(sync_status='failed').count()
        synced_employees = Employee.query.filter_by(sync_status='synced').count()

        pending_events = Event.query.filter_by(sync_status='pending').count()
        failed_events = Event.query.filter_by(sync_status='failed').count()
        synced_events = Event.query.filter_by(sync_status='synced').count()

        pending_schedules = Schedule.query.filter_by(sync_status='pending').count()
        failed_schedules = Schedule.query.filter_by(sync_status='failed').count()
        synced_schedules = Schedule.query.filter_by(sync_status='synced').count()

        # Get last sync timestamps
        last_employee_sync = db.session.query(Employee.last_synced).filter(
            Employee.last_synced.isnot(None)).order_by(Employee.last_synced.desc()).first()
        last_event_sync = db.session.query(Event.last_synced).filter(
            Event.last_synced.isnot(None)).order_by(Event.last_synced.desc()).first()
        last_schedule_sync = db.session.query(Schedule.last_synced).filter(
            Schedule.last_synced.isnot(None)).order_by(Schedule.last_synced.desc()).first()

        return jsonify({
            'sync_enabled': current_app.config.get('SYNC_ENABLED', False),
            'employees': {
                'pending': pending_employees,
                'failed': failed_employees,
                'synced': synced_employees,
                'last_sync': last_employee_sync[0].isoformat() if last_employee_sync and last_employee_sync[0] else None
            },
            'events': {
                'pending': pending_events,
                'failed': failed_events,
                'synced': synced_events,
                'last_sync': last_event_sync[0].isoformat() if last_event_sync and last_event_sync[0] else None
            },
            'schedules': {
                'pending': pending_schedules,
                'failed': failed_schedules,
                'synced': synced_schedules,
                'last_sync': last_schedule_sync[0].isoformat() if last_schedule_sync and last_schedule_sync[0] else None
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        current_app.logger.error(f"Error getting sync status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/webhook/schedule_update', methods=['POST'])
def webhook_schedule_update():
    """Receive webhook notifications from external API"""
    try:
        db = current_app.extensions['sqlalchemy']
        Schedule = current_app.config['Schedule']
        from sync_engine import sync_engine

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        webhook_type = data.get('type', '')
        payload = data.get('data', {})

        logging.info(f"Received webhook: {webhook_type}")

        if webhook_type == 'schedule.created':
            # Handle new schedule from external system
            result = sync_engine._create_local_schedule_from_external(payload)
        elif webhook_type == 'schedule.updated':
            # Handle schedule update from external system
            schedule = Schedule.query.filter_by(external_id=payload.get('id')).first()
            if schedule:
                result = sync_engine._update_local_schedule(schedule, payload)
        elif webhook_type == 'schedule.deleted':
            # Handle schedule deletion from external system
            schedule = Schedule.query.filter_by(external_id=payload.get('id')).first()
            if schedule:
                db.session.delete(schedule)
                db.session.commit()
                result = True
        else:
            logging.warning(f"Unknown webhook type: {webhook_type}")
            return jsonify({'message': f'Unknown webhook type: {webhook_type}'}), 400

        return jsonify({
            'status': 'processed' if result else 'failed',
            'webhook_type': webhook_type,
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        logging.error(f"Webhook processing failed: {str(e)}")
        return jsonify({
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@admin_bp.route('/sync/admin')
def sync_admin():
    """Sync administration interface"""
    return render_template('sync_admin.html', config=current_app.config)

@admin_bp.route('/api/universal_search')
def universal_search():
    """Universal search endpoint for events, employees, and schedules"""
    db = current_app.extensions['sqlalchemy']
    Event = current_app.config['Event']
    Employee = current_app.config['Employee']
    Schedule = current_app.config['Schedule']

    query = request.args.get('q', '').strip()
    context = request.args.get('context', 'all')  # all, scheduling, tracking, reporting
    filters = request.args.getlist('filters')  # Additional filters

    if not query:
        return jsonify({
            'results': [],
            'total': 0,
            'query': query,
            'context': context
        })

    results = {
        'events': [],
        'employees': [],
        'schedules': [],
        'total': 0
    }

    # Search Events
    if context in ['all', 'scheduling', 'tracking']:
        # Search by event name, project ref number, store name, or location
        event_query = Event.query.filter(
            db.or_(
                Event.project_name.ilike(f'%{query}%'),
                Event.project_ref_num == query if query.isdigit() else False,
                Event.store_name.ilike(f'%{query}%') if Event.store_name else False,
                Event.location_mvid.ilike(f'%{query}%') if Event.location_mvid else False
            )
        )

        # Apply context-specific filters
        if context == 'scheduling':
            event_query = event_query.filter_by(is_scheduled=False)

        # Apply additional filters
        if 'event_type' in [f.split(':')[0] for f in filters]:
            event_type = next(f.split(':')[1] for f in filters if f.startswith('event_type:'))
            event_query = event_query.filter_by(event_type=event_type)

        if 'status' in [f.split(':')[0] for f in filters]:
            status = next(f.split(':')[1] for f in filters if f.startswith('status:'))
            if status == 'scheduled':
                event_query = event_query.filter_by(is_scheduled=True)
            elif status == 'unscheduled':
                event_query = event_query.filter_by(is_scheduled=False)

        events = event_query.order_by(Event.start_datetime.asc()).limit(20).all()

        for event in events:
            # Calculate priority (days until deadline)
            days_remaining = (event.due_datetime.date() - datetime.now().date()).days
            if days_remaining <= 1:
                priority = 'critical'
                priority_color = 'red'
            elif days_remaining <= 7:
                priority = 'urgent'
                priority_color = 'yellow'
            else:
                priority = 'normal'
                priority_color = 'green'

            results['events'].append({
                'id': event.id,
                'project_ref_num': event.project_ref_num,
                'project_name': event.project_name,
                'store_name': event.store_name,
                'location_mvid': event.location_mvid,
                'start_datetime': event.start_datetime.isoformat(),
                'due_datetime': event.due_datetime.isoformat(),
                'event_type': event.event_type,
                'is_scheduled': event.is_scheduled,
                'priority': priority,
                'priority_color': priority_color,
                'days_remaining': days_remaining
            })

    # Search Employees
    if context in ['all', 'scheduling']:
        employee_query = Employee.query.filter(
            db.and_(
                Employee.is_active == True,
                db.or_(
                    Employee.name.ilike(f'%{query}%'),
                    Employee.id.ilike(f'%{query}%'),
                    Employee.email.ilike(f'%{query}%') if Employee.email else False
                )
            )
        )

        employees = employee_query.limit(20).all()

        for emp in employees:
            results['employees'].append({
                'id': emp.id,
                'name': emp.name,
                'email': emp.email,
                'job_title': emp.job_title,
                'is_supervisor': emp.is_supervisor
            })

    # Search Schedules (when tracking specific assignments)
    if context in ['all', 'tracking']:
        try:
            # Try searching by project ref number or employee ID
            schedule_query = db.session.query(Schedule, Event, Employee).join(
                Event, Schedule.event_ref_num == Event.project_ref_num
            ).join(
                Employee, Schedule.employee_id == Employee.id
            ).filter(
                db.or_(
                    Event.project_name.ilike(f'%{query}%'),
                    Event.project_ref_num == query if query.isdigit() else False,
                    Employee.name.ilike(f'%{query}%'),
                    Employee.id.ilike(f'%{query}%')
                )
            )

            schedules = schedule_query.limit(20).all()

            for schedule, event, employee in schedules:
                results['schedules'].append({
                    'id': schedule.id,
                    'event_ref_num': event.project_ref_num,
                    'event_name': event.project_name,
                    'employee_id': employee.id,
                    'employee_name': employee.name,
                    'schedule_datetime': schedule.schedule_datetime.isoformat(),
                    'event_type': event.event_type
                })
        except Exception as e:
            current_app.logger.warning(f"Error searching schedules: {e}")

    results['total'] = len(results['events']) + len(results['employees']) + len(results['schedules'])
    results['query'] = query
    results['context'] = context

    return jsonify(results)

@admin_bp.route('/api/test')
def api_tester():
    """API testing and request capture tool"""
    return render_template('api_tester.html')

@admin_bp.route('/api/test/login', methods=['POST'])
def test_login():
    """Test login endpoint for capturing session data"""
    try:
        data = request.get_json()
        login_url = data.get('login_url')
        username = data.get('username')
        password = data.get('password')

        if not all([login_url, username, password]):
            return jsonify({'success': False, 'error': 'Missing required fields'})

        # Create a test session
        test_session = requests.Session()

        # First get the login page
        login_page = test_session.get(login_url, timeout=30)

        # Prepare login data
        login_data = {
            'username': username,
            'password': password
        }

        # Attempt login
        login_response = test_session.post(login_url, data=login_data, timeout=30, allow_redirects=True)

        # Extract session information
        session_id = test_session.cookies.get('PHPSESSID')

        return jsonify({
            'success': True,
            'status_code': login_response.status_code,
            'session_id': session_id,
            'cookies': dict(test_session.cookies),
            'final_url': login_response.url,
            'headers': dict(login_response.headers),
            'response_preview': login_response.text[:500] if len(login_response.text) > 500 else login_response.text
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/test/request', methods=['POST'])
def test_request():
    """Test generic API requests with session"""
    try:
        data = request.get_json()
        method = data.get('method', 'GET')
        url = data.get('endpoint_url')
        headers = data.get('headers', {})
        request_data = data.get('data')
        session_id = data.get('session_id')

        if not url:
            return jsonify({'success': False, 'error': 'URL is required'})

        # Create test session
        test_session = requests.Session()

        # Set session cookie if provided
        if session_id:
            test_session.cookies.set('PHPSESSID', session_id)

        # Set headers
        if headers:
            test_session.headers.update(headers)

        # Prepare request data
        request_kwargs = {'timeout': 30}
        if request_data:
            if headers.get('Content-Type') == 'application/json':
                request_kwargs['json'] = request_data
            else:
                request_kwargs['data'] = request_data

        # Make request
        response = test_session.request(method, url, **request_kwargs)

        return jsonify({
            'success': True,
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'cookies': dict(test_session.cookies),
            'response_preview': response.text[:1000] if len(response.text) > 1000 else response.text,
            'content_type': response.headers.get('Content-Type', 'unknown')
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def extract_event_number(project_name):
    """Extract the first 6 digits from a Core event's project name"""
    if not project_name:
        return None

    # Look for 6-digit numbers at the start of the project name
    match = re.match(r'^(\d{6})', project_name)
    if match:
        return match.group(1)

    # If no match at start, look for any 6-digit sequence
    match = re.search(r'\d{6}', project_name)
    if match:
        return match.group(0)

    return None

def generate_edr_documents(event_numbers, credentials=None):
    """Generate EDR documents using the product-connections-implementation"""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter

    # Import EDR reporting functionality
    try:
        from product_connections_implementation.edr_printer import EDRReportGenerator
        edr_available = True
    except ImportError:
        edr_available = False
        EDRReportGenerator = None

    if not event_numbers:
        return None

    if not edr_available:
        current_app.logger.error("EDR report generator is not available - product-connections-implementation not installed")
        return None

    try:
        event_numbers_str = ', '.join(event_numbers)
        current_app.logger.info(f"Generating EDR reports for event numbers: {event_numbers_str}")

        # Initialize the EDR report generator
        generator = EDRReportGenerator()

        # Set credentials if provided, otherwise it will prompt interactively
        if credentials and credentials.get('username') and credentials.get('password'):
            generator.set_credentials(credentials['username'], credentials['password'])

        # Authenticate with Retail Link
        if not generator.authenticate():
            current_app.logger.error("Failed to authenticate with Retail Link for EDR generation")
            return None

        pdf_files = []

        # Generate EDR report for each event number
        for event_id in event_numbers:
            try:
                current_app.logger.info(f"Generating EDR report for event ID: {event_id}")

                # Get EDR data for this event
                edr_data = generator.get_edr_report(event_id)

                if not edr_data:
                    current_app.logger.warning(f"No EDR data found for event ID: {event_id}")
                    continue

                # Generate HTML report
                html_content = generator.generate_html_report(edr_data)

                if html_content:
                    # Convert HTML to PDF (you might want to use a library like WeasyPrint for this)
                    # For now, we'll create a simple PDF with the event ID as placeholder
                    pdf_buffer = BytesIO()
                    pdf_canvas = canvas.Canvas(pdf_buffer, pagesize=letter)
                    pdf_canvas.setFont("Helvetica-Bold", 16)
                    pdf_canvas.drawString(50, 750, f"EDR Report - Event {event_id}")
                    pdf_canvas.setFont("Helvetica", 12)
                    pdf_canvas.drawString(50, 720, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                    # Add some basic EDR data if available
                    y_position = 680
                    if isinstance(edr_data, dict):
                        for key, value in list(edr_data.items())[:10]:  # Show first 10 items
                            pdf_canvas.drawString(50, y_position, f"{key}: {str(value)[:60]}")
                            y_position -= 20

                    pdf_canvas.save()
                    pdf_buffer.seek(0)

                    pdf_files.append({
                        'name': f"EDR_Event_{event_id}.pdf",
                        'content': pdf_buffer.getvalue()
                    })

                    current_app.logger.info(f"Successfully generated EDR report for event ID: {event_id}")
                else:
                    current_app.logger.warning(f"Failed to generate HTML report for event ID: {event_id}")

            except Exception as e:
                current_app.logger.error(f"Error generating EDR report for event ID {event_id}: {str(e)}")
                continue

        if pdf_files:
            current_app.logger.info(f"Successfully generated {len(pdf_files)} EDR PDF(s)")
            return pdf_files
        else:
            current_app.logger.error("No EDR PDF files were generated")
            return None

    except Exception as e:
        current_app.logger.error(f"Error in EDR document generation: {str(e)}")
        return None

@admin_bp.route('/api/edr/request_code', methods=['POST'])
@require_authentication()
def edr_request_code():
    """
    Request MFA code to be sent to phone
    This must be called BEFORE showing the MFA popup
    """
    try:
        from scheduler_app.services.edr_generator import EDRGenerator
        from flask import session as flask_session

        # Clear any existing EDR session data
        if 'edr_temp_cookies' in flask_session:
            del flask_session['edr_temp_cookies']
        if 'edr_session_cookies' in flask_session:
            del flask_session['edr_session_cookies']
        if 'edr_auth_token' in flask_session:
            del flask_session['edr_auth_token']

        # Create EDR generator with credentials from settings (with config fallback)
        username, password, mfa_credential_id = _get_edr_credentials()
        edr_gen = EDRGenerator(
            username=username,
            password=password,
            mfa_credential_id=mfa_credential_id
        )

        # Request MFA code (steps 1 & 2: submit password, request code)
        if edr_gen.request_mfa_code():
            # Instead of storing ALL cookies (too large for session),
            # we'll just mark that MFA was requested
            # The user will need to re-authenticate from scratch with the MFA code
            flask_session['edr_mfa_requested'] = True
            flask_session['edr_mfa_timestamp'] = datetime.utcnow().isoformat()

            current_app.logger.info("MFA code requested successfully")
            return jsonify({'success': True, 'message': 'MFA code sent to your phone'})
        else:
            return jsonify({'success': False, 'message': 'Failed to request MFA code'}), 500

    except Exception as e:
        current_app.logger.error(f"MFA code request error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/edr/authenticate', methods=['POST'])
@require_authentication()
def edr_authenticate():
    """
    Authenticate with Walmart Retail Link using MFA code
    Does a complete authentication flow from scratch with the MFA code
    """
    try:
        from scheduler_app.services.edr_generator import EDRGenerator
        from flask import session as flask_session

        data = request.get_json()
        mfa_code = data.get('mfa_code')

        if not mfa_code:
            return jsonify({'success': False, 'message': 'MFA code is required'}), 400

        # Check that MFA was requested
        if not flask_session.get('edr_mfa_requested'):
            return jsonify({'success': False, 'message': 'Please request MFA code first'}), 400

        # Create EDR generator with credentials from settings (with config fallback)
        username, password, mfa_credential_id = _get_edr_credentials()
        edr_gen = EDRGenerator(
            username=username,
            password=password,
            mfa_credential_id=mfa_credential_id
        )

        # Do complete authentication flow with MFA code
        # Step 1: Submit password (this also sets initial cookies)
        if not edr_gen._step1_submit_password():
            return jsonify({'success': False, 'message': 'Password submission failed'}), 500

        # Step 2: Note - MFA code was already sent by request_code endpoint
        # We skip step 2 since the code is already sent and valid

        # Step 3: Validate MFA code
        if not edr_gen._step3_validate_mfa_code(mfa_code):
            return jsonify({'success': False, 'message': 'Invalid MFA code'}), 401

        # Steps 4-6: Complete authentication
        edr_gen._step4_register_page_access()
        edr_gen._step5_navigate_to_event_management()

        if not edr_gen._step6_authenticate_event_management():
            return jsonify({'success': False, 'message': 'Event Management authentication failed'}), 500

        # Store auth token in session for reuse
        flask_session['edr_auth_token'] = edr_gen.auth_token

        # Store only essential cookies (avoid session size limit)
        essential_cookies = {}
        for cookie in edr_gen.session.cookies:
            # Only store auth-related cookies, skip tracking cookies
            if cookie.name in ['_auth', '_refreshAuth', 'RLSESSION', 'RETAILLINKSESSION',
                              'auth-token', 'fcnRealm', 'TS01b1e5a6', 'TS0111a950']:
                essential_cookies[cookie.name] = cookie.value

        flask_session['edr_session_cookies'] = essential_cookies

        # Clear MFA request flag
        if 'edr_mfa_requested' in flask_session:
            del flask_session['edr_mfa_requested']
        if 'edr_mfa_timestamp' in flask_session:
            del flask_session['edr_mfa_timestamp']

        current_app.logger.info(f"EDR authentication successful. Stored {len(essential_cookies)} essential cookies")
        return jsonify({'success': True, 'message': 'EDR authentication successful'})

    except Exception as e:
        current_app.logger.error(f"EDR authentication error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/print_paperwork/<paperwork_type>')
def print_paperwork(paperwork_type):
    """
    Print paperwork for Core events (today or tomorrow)
    Structure: Sales Tool PDF -> EDR -> Activity Log -> Checklist (for each event)
    paperwork_type: 'today' or 'tomorrow'
    """
    # Calculate target date from paperwork_type
    if paperwork_type == 'today':
        target_date = date.today()
    elif paperwork_type == 'tomorrow':
        target_date = date.today() + timedelta(days=1)
    else:
        return jsonify({'error': 'Invalid paperwork type. Use "today" or "tomorrow"'}), 400

    # Call refactored internal function with calculated date
    return print_paperwork_internal(paperwork_type, target_date)
def print_paperwork_internal(paperwork_type, target_date_override=None):
    """Internal function to generate paperwork PDF with optional target date override"""
    try:
        from PyPDF2 import PdfReader, PdfWriter
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from xhtml2pdf import pisa
        from scheduler_app.services.edr_generator import EDRGenerator
        import os

        db = current_app.extensions['sqlalchemy']
        Event = current_app.config['Event']
        Employee = current_app.config['Employee']
        Schedule = current_app.config['Schedule']

        # Determine target date
        if target_date_override:
            target_date = target_date_override
        elif paperwork_type == 'today':
            target_date = date.today()
        elif paperwork_type == 'tomorrow':
            target_date = date.today() + timedelta(days=1)
        else:
            target_date = date.today()

        # Query Core events for target date
        events = Event.query.filter(
            Event.event_date == target_date,
            Event.event_type == 'Core'
        ).all()

        if not events:
            return jsonify({'message': f'No Core events found for {target_date}'}), 404

        # Generate simple PDF (simplified version)
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from io import BytesIO

        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Title page
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, 750, f"Core Events Paperwork - {target_date.strftime('%B %d, %Y')}")
        
        # Event list
        y = 700
        p.setFont("Helvetica", 12)
        for event in events:
            schedules = Schedule.query.filter_by(event_id=event.id).all()
            employee_names = [Employee.query.get(s.employee_id).name for s in schedules if Employee.query.get(s.employee_id)]
            
            p.drawString(100, y, f"{event.project_name} - {', '.join(employee_names) if employee_names else 'Unassigned'}")
            y -= 20
            if y < 100:
                p.showPage()
                y = 750

        p.save()
        buffer.seek(0)

        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="Paperwork_{target_date.strftime("%Y%m%d")}.pdf"'
        
        return response

    except Exception as e:
        current_app.logger.error(f"Error generating paperwork: {str(e)}")
        return jsonify({'error': f'Failed to generate paperwork: {str(e)}'}), 500


@admin_bp.route('/api/print_event_paperwork/<int:event_id>')
@require_authentication()
def print_event_paperwork(event_id):
    """Print paperwork for a single event"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from io import BytesIO

        db = current_app.extensions['sqlalchemy']
        Event = current_app.config['Event']
        Employee = current_app.config['Employee']
        Schedule = current_app.config['Schedule']

        # Get event details
        event = Event.query.get(event_id)
        if not event:
            return jsonify({'error': f'Event {event_id} not found'}), 404

        # Get schedules for this event
        schedules = Schedule.query.filter_by(event_id=event.id).all()
        if not schedules:
            return jsonify({'error': f'Event {event_id} is not scheduled'}), 404

        # Generate simple PDF for single event
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Title
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, 750, f"Event Paperwork - {event.project_name}")
        p.setFont("Helvetica", 12)
        p.drawString(100, 730, f"Event ID: {event.id}")
        p.drawString(100, 710, f"Date: {event.event_date}")
        p.drawString(100, 690, f"Type: {event.event_type}")
        
        # Employees assigned
        y = 650
        p.setFont("Helvetica-Bold", 12)
        p.drawString(100, y, "Assigned Employees:")
        y -= 20
        
        p.setFont("Helvetica", 11)
        for schedule in schedules:
            employee = Employee.query.get(schedule.employee_id)
            if employee:
                time_str = schedule.schedule_datetime.strftime('%I:%M %p') if schedule.schedule_datetime else 'TBD'
                p.drawString(120, y, f"• {employee.name} - {time_str}")
                y -= 18
        
        p.save()
        buffer.seek(0)

        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="Event_{event_id}_Paperwork.pdf"'
        
        return response

    except Exception as e:
        current_app.logger.error(f"Error generating event paperwork: {str(e)}")
        return jsonify({'error': f'Failed to generate paperwork: {str(e)}'}), 500


@admin_bp.route('/api/auto_schedule_event/<int:event_id>', methods=['POST'])
@require_authentication()
def auto_schedule_event(event_id):
    """Auto-schedule a single event using SchedulingEngine"""
    try:
        db = current_app.extensions['sqlalchemy']
        Event = current_app.config['Event']
        SystemSetting = current_app.config.get('SystemSetting')
        SchedulerRunHistory = current_app.config['SchedulerRunHistory']
        PendingSchedule = current_app.config['PendingSchedule']

        # Get event
        event = Event.query.get(event_id)
        if not event:
            return jsonify({'error': f'Event {event_id} not found'}), 404

        # Check if already scheduled
        if event.condition in ['Scheduled', 'Submitted']:
            return jsonify({'error': f'Event {event_id} is already scheduled'}), 400

        # Initialize SchedulingEngine
        from scheduler_app.services.scheduling_engine import SchedulingEngine
        models = {k: current_app.config[k] for k in [
            'Employee', 'Event', 'Schedule', 'SchedulerRunHistory',
            'PendingSchedule', 'RotationAssignment', 'ScheduleException',
            'EmployeeTimeOff', 'EmployeeAvailability', 'EmployeeWeeklyAvailability'
        ]}
        engine = SchedulingEngine(db.session, models)

        # Create run history
        run = SchedulerRunHistory(
            run_type='single_event',
            total_events_processed=1,
            events_scheduled=0,
            events_requiring_swaps=0,
            events_failed=0
        )
        db.session.add(run)
        db.session.commit()

        # Try to schedule the event
        result = engine.schedule_single_event(event)

        if not result:
            run.events_failed = 1
            db.session.commit()
            return jsonify({'error': 'Failed to find available employee for this event'}), 500

        # Check approval setting
        require_approval = True
        if SystemSetting:
            require_approval = SystemSetting.get_setting('auto_scheduler_require_approval', True)

        if require_approval:
            # Create pending schedule
            pending = PendingSchedule(
                event_id=event.id,
                employee_id=result['employee_id'],
                scheduler_run_id=run.id,
                status='pending'
            )
            db.session.add(pending)
            run.events_scheduled = 1
            db.session.commit()

            return jsonify({
                'success': True,
                'message': f'Event scheduled for {result["employee_name"]} (pending approval)',
                'employee_name': result['employee_name'],
                'requires_approval': True
            })
        else:
            # Auto-approve and submit
            run.events_scheduled = 1
            db.session.commit()

            return jsonify({
                'success': True,
                'message': f'Event auto-scheduled for {result["employee_name"]}',
                'employee_name': result['employee_name'],
                'requires_approval': False
            })

    except Exception as e:
        current_app.logger.error(f"Error auto-scheduling event {event_id}: {str(e)}")
        return jsonify({'error': f'Scheduling failed: {str(e)}'}), 500


@admin_bp.route('/employees/analytics', methods=['GET'])
@require_authentication()
def employee_analytics():
    """Display employee scheduling analytics for the selected week"""
    from datetime import datetime, timedelta
    
    db = current_app.extensions['sqlalchemy']
    Employee = current_app.config['Employee']
    Schedule = current_app.config['Schedule']
    
    # Get week_start parameter or default to current week's Sunday
    week_start_str = request.args.get('week_start')
    if week_start_str:
        week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
    else:
        today = date.today()
        # Calculate Sunday: go back (weekday + 1) days (Monday=0, Sunday=6)
        week_start = today - timedelta(days=(today.weekday() + 1) % 7)
    
    week_end = week_start + timedelta(days=6)  # Saturday
    
    # Query employee statistics
    from sqlalchemy import func
    stats = db.session.query(
        Employee.id,
        Employee.name,
        func.count(func.distinct(func.date(Schedule.schedule_datetime))).label('days_scheduled'),
        func.count(Schedule.id).label('total_events')
    ).join(
        Schedule, Employee.id == Schedule.employee_id
    ).filter(
        func.date(Schedule.schedule_datetime) >= week_start,
        func.date(Schedule.schedule_datetime) <= week_end
    ).group_by(
        Employee.id, Employee.name
    ).order_by(
        func.count(func.distinct(func.date(Schedule.schedule_datetime))).desc()
    ).all()
    
    # Convert to list of dicts
    employee_stats = []
    for stat in stats:
        employee_stats.append({
            'employee_id': stat[0],
            'employee_name': stat[1],
            'days_scheduled': stat[2],
            'total_events': stat[3]
        })
    
    return render_template('employee_analytics.html',
                         employee_stats=employee_stats,
                         week_start=week_start.strftime('%Y-%m-%d'),
                         week_end=week_end.strftime('%Y-%m-%d'))


@admin_bp.route('/api/print_weekly_summary/<week_start_str>')
@require_authentication()
def print_weekly_summary(week_start_str):
    """Print weekly schedule summary for all employees (Core and Juicer events only)"""
    try:
        from collections import defaultdict
        from xhtml2pdf import pisa
        from io import BytesIO

        db = current_app.extensions['sqlalchemy']
        Employee = current_app.config['Employee']
        Schedule = current_app.config['Schedule']
        Event = current_app.config['Event']

        # Parse week start
        week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
        week_end = week_start + timedelta(days=6)

        # Query schedules for the week (Core and Juicer only)
        schedules = db.session.query(
            Employee.name,
            Schedule.schedule_datetime,
            Event.event_type
        ).join(
            Schedule, Employee.id == Schedule.employee_id
        ).join(
            Event, Schedule.event_id == Event.id
        ).filter(
            func.date(Schedule.schedule_datetime) >= week_start,
            func.date(Schedule.schedule_datetime) <= week_end,
            Event.event_type.in_(['Core', 'Juicer'])
        ).order_by(
            Employee.name, Schedule.schedule_datetime
        ).all()

        # Group by employee and day
        employee_schedules = defaultdict(lambda: defaultdict(list))
        for name, schedule_dt, event_type in schedules:
            day_name = schedule_dt.strftime('%A')[:3]  # Sun, Mon, Tue
            time_str = schedule_dt.strftime('%I:%M %p')
            employee_schedules[name][day_name].append(time_str)

        # Generate HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Weekly Schedule Summary</title>
            <style>
                @page {{ size: A4 landscape; margin: 0.5in; }}
                body {{ font-family: Arial, sans-serif; font-size: 10pt; }}
                .header {{ text-align: center; margin-bottom: 20px; border-bottom: 2px solid #2E4C73; padding-bottom: 10px; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th {{ background: #2E4C73; color: white; padding: 8px; text-align: left; font-size: 9pt; }}
                td {{ padding: 6px 8px; border: 1px solid #ddd; font-size: 9pt; }}
                tr:nth-child(even) {{ background: #f9f9f9; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Weekly Schedule Summary - {week_start.strftime('%B %d')} to {week_end.strftime('%B %d, %Y')}</h2>
                <p>(CORE and Juicer Events Only)</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th style="width: 20%;">Employee</th>
                        <th style="width: 11.4%;">Sun</th>
                        <th style="width: 11.4%;">Mon</th>
                        <th style="width: 11.4%;">Tue</th>
                        <th style="width: 11.4%;">Wed</th>
                        <th style="width: 11.4%;">Thu</th>
                        <th style="width: 11.4%;">Fri</th>
                        <th style="width: 11.4%;">Sat</th>
                    </tr>
                </thead>
                <tbody>
        """

        # Add employee rows
        for employee_name in sorted(employee_schedules.keys()):
            html += f"<tr><td><strong>{employee_name}</strong></td>"
            for day in ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']:
                times = employee_schedules[employee_name].get(day, [])
                html += f"<td>{'<br>'.join(times) if times else '-'}</td>"
            html += "</tr>"

        html += """
                </tbody>
            </table>
        </body>
        </html>
        """

        # Generate PDF
        output = BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=output)

        if pisa_status.err:
            return jsonify({'error': 'PDF generation failed'}), 500

        output.seek(0)

        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="Weekly_Summary_{week_start_str}.pdf"'

        return response

    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        current_app.logger.error(f"Error generating weekly summary: {str(e)}")
        return jsonify({'error': f'Failed to generate summary: {str(e)}'}), 500


@admin_bp.route('/api/print_employee_schedule/<int:employee_id>/<week_start_str>')
@require_authentication()
def print_employee_schedule(employee_id, week_start_str):
    """Print detailed weekly schedule for a single employee (all event types)"""
    try:
        from collections import defaultdict
        from xhtml2pdf import pisa
        from io import BytesIO

        db = current_app.extensions['sqlalchemy']
        Employee = current_app.config['Employee']
        Schedule = current_app.config['Schedule']
        Event = current_app.config['Event']

        # Get employee
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({'error': f'Employee {employee_id} not found'}), 404

        # Parse week start
        week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
        week_end = week_start + timedelta(days=6)

        # Query schedules for the employee
        schedules = db.session.query(
            Schedule.schedule_datetime,
            Event.project_name,
            Event.event_type
        ).join(
            Event, Schedule.event_id == Event.id
        ).filter(
            Schedule.employee_id == employee_id,
            func.date(Schedule.schedule_datetime) >= week_start,
            func.date(Schedule.schedule_datetime) <= week_end
        ).order_by(
            Schedule.schedule_datetime
        ).all()

        # Group by date
        daily_schedules = defaultdict(list)
        for schedule_dt, project_name, event_type in schedules:
            day_key = schedule_dt.date()
            daily_schedules[day_key].append({
                'time': schedule_dt.strftime('%I:%M %p'),
                'name': project_name,
                'type': event_type
            })

        # Generate HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{employee.name} - Weekly Schedule</title>
            <style>
                @page {{ size: A4 landscape; margin: 0.75in; }}
                body {{ font-family: Arial, sans-serif; }}
                .header {{ text-align: center; margin-bottom: 30px; border-bottom: 3px solid #2E4C73; padding-bottom: 15px; }}
                h1 {{ color: #2E4C73; margin: 0; font-size: 24pt; }}
                .week-range {{ color: #666; font-size: 14pt; margin-top: 10px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th {{ background: #2E4C73; color: white; padding: 12px; text-align: left; font-size: 12pt; }}
                td {{ padding: 10px 12px; border: 1px solid #ddd; font-size: 11pt; vertical-align: top; }}
                tr:nth-child(even) {{ background: #f9f9f9; }}
                .day-header {{ font-weight: bold; color: #2E4C73; font-size: 12pt; }}
                .event-time {{ color: #1B9BD8; font-weight: bold; }}
                .no-events {{ color: #999; font-style: italic; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{employee.name}</h1>
                <p class="week-range">Week of {week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th style="width: 15%;">Day</th>
                        <th style="width: 15%;">Time</th>
                        <th style="width: 70%;">Event</th>
                    </tr>
                </thead>
                <tbody>
        """

        # Add rows for each day
        current_date = week_start
        while current_date <= week_end:
            day_name = current_date.strftime('%A, %B %d')
            events = daily_schedules.get(current_date, [])

            if events:
                for idx, event in enumerate(events):
                    if idx == 0:
                        html += f"""
                        <tr>
                            <td class="day-header" rowspan="{len(events)}">{day_name}</td>
                            <td class="event-time">{event['time']}</td>
                            <td>{event['name']} <em>({event['type']})</em></td>
                        </tr>
                        """
                    else:
                        html += f"""
                        <tr>
                            <td class="event-time">{event['time']}</td>
                            <td>{event['name']} <em>({event['type']})</em></td>
                        </tr>
                        """
            else:
                html += f"""
                <tr>
                    <td class="day-header">{day_name}</td>
                    <td class="no-events" colspan="2">No events scheduled</td>
                </tr>
                """

            current_date += timedelta(days=1)

        html += """
                </tbody>
            </table>
        </body>
        </html>
        """

        # Generate PDF
        output = BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=output)

        if pisa_status.err:
            return jsonify({'error': 'PDF generation failed'}), 500

        output.seek(0)

        filename = employee.name.replace(' ', '_') + f'_Schedule_{week_start_str}.pdf'
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        current_app.logger.error(f"Error generating employee schedule: {str(e)}")
        return jsonify({'error': f'Failed to generate schedule: {str(e)}'}), 500
