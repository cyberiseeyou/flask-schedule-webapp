"""
API routes blueprint
Handles all API endpoints for schedule operations, imports, exports, and AJAX calls
"""
from flask import Blueprint, request, jsonify, current_app, make_response
from routes.auth import require_authentication
from datetime import datetime, timedelta, date
import csv
import io
from io import StringIO

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/core_employees_for_trade/<date>/<int:current_schedule_id>')
def core_employees_for_trade(date, current_schedule_id):
    """Get employees with Core events on the same date for trading"""
    db = current_app.extensions['sqlalchemy']
    Schedule = current_app.config['Schedule']
    Event = current_app.config['Event']
    Employee = current_app.config['Employee']

    try:
        parsed_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    # Get other Core events scheduled on the same date (excluding current schedule)
    core_schedules = db.session.query(Schedule, Event, Employee).join(
        Event, Schedule.event_ref_num == Event.project_ref_num
    ).join(
        Employee, Schedule.employee_id == Employee.id
    ).filter(
        db.func.date(Schedule.schedule_datetime) == parsed_date,
        Event.event_type == 'Core',
        Schedule.id != current_schedule_id
    ).order_by(Schedule.schedule_datetime).all()

    employees_data = []
    for schedule, event, employee in core_schedules:
        employees_data.append({
            'schedule_id': schedule.id,
            'employee_name': employee.name,
            'employee_id': employee.id,
            'event_name': event.project_name,
            'time': schedule.schedule_datetime.strftime('%I:%M %p')
        })

    return jsonify(employees_data)


@api_bp.route('/available_employees_for_change/<date>/<event_type>')
def available_employees_for_change(date, event_type):
    """Get available employees for changing event assignment with proper role-based filtering"""
    db = current_app.extensions['sqlalchemy']
    Schedule = current_app.config['Schedule']
    Event = current_app.config['Event']
    Employee = current_app.config['Employee']
    EmployeeAvailability = current_app.config['EmployeeAvailability']
    EmployeeTimeOff = current_app.config['EmployeeTimeOff']
    EmployeeWeeklyAvailability = current_app.config['EmployeeWeeklyAvailability']

    try:
        parsed_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    # Get optional parameters for current employee (for reschedule)
    from flask import request
    current_employee_id = request.args.get('current_employee_id', type=str)
    current_date_str = request.args.get('current_date', type=str)
    current_date = None
    if current_date_str:
        try:
            current_date = datetime.strptime(current_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    # Get all active employees
    all_employees = Employee.query.filter_by(is_active=True).all()

    # For Core events, get employees already scheduled for Core events that day
    if event_type == 'Core':
        core_scheduled_employees = db.session.query(Schedule.employee_id).join(
            Event, Schedule.event_ref_num == Event.project_ref_num
        ).filter(
            db.func.date(Schedule.schedule_datetime) == parsed_date,
            Event.event_type == 'Core'
        ).all()
        core_scheduled_employee_ids = {emp[0] for emp in core_scheduled_employees}
    else:
        core_scheduled_employee_ids = set()

    # Get employees marked as unavailable on the specified date
    unavailable_employees = db.session.query(EmployeeAvailability.employee_id).filter(
        EmployeeAvailability.date == parsed_date,
        EmployeeAvailability.is_available == False
    ).all()
    unavailable_employee_ids = {emp[0] for emp in unavailable_employees}

    # Get employees who have time off on the specified date
    time_off_employees = db.session.query(EmployeeTimeOff.employee_id).filter(
        EmployeeTimeOff.start_date <= parsed_date,
        EmployeeTimeOff.end_date >= parsed_date
    ).all()
    time_off_employee_ids = {emp[0] for emp in time_off_employees}

    # Get day of week for weekly availability check
    day_of_week = parsed_date.weekday()
    day_columns = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    day_column = day_columns[day_of_week]

    weekly_availability_query = db.session.query(
        EmployeeWeeklyAvailability.employee_id,
        getattr(EmployeeWeeklyAvailability, day_column).label('is_available_weekly')
    ).all()

    weekly_unavailable_ids = {
        emp[0] for emp in weekly_availability_query
        if not emp[1]
    }

    # Filter available employees
    available_employees_list = []
    for emp in all_employees:
        # Special exception for current employee when rescheduling
        is_current_employee = (current_employee_id and emp.id == current_employee_id)
        is_same_day = (current_date and current_date == parsed_date)

        # Allow current employee if it's the same day OR a day they're not scheduled
        allow_current_employee = False
        if is_current_employee:
            if is_same_day:
                # Same day - always allow
                allow_current_employee = True
            else:
                # Different day - only allow if they're not scheduled for a Core event on the new date
                allow_current_employee = (emp.id not in core_scheduled_employee_ids)

        # Normal availability checks (skip for allowed current employee on same day)
        if not (is_current_employee and is_same_day):
            if (emp.id in core_scheduled_employee_ids or
                emp.id in unavailable_employee_ids or
                emp.id in time_off_employee_ids or
                emp.id in weekly_unavailable_ids):
                # Skip unless this is the current employee being allowed
                if not allow_current_employee:
                    continue

        # Role-based restrictions
        # Special handling for "Other" events - only Lead Event Specialist and Club Supervisor
        if event_type == 'Other':
            if emp.job_title not in ['Lead Event Specialist', 'Club Supervisor']:
                continue
        # Check role-based restrictions for the event type
        elif not emp.can_work_event_type(event_type):
            continue

        available_employees_list.append({
            'id': emp.id,
            'name': emp.name,
            'job_title': emp.job_title
        })

    return jsonify(available_employees_list)


@api_bp.route('/validate_schedule_for_export')
def validate_schedule_for_export():
    """Validate scheduled events before export and return any errors"""
    db = current_app.extensions['sqlalchemy']
    Schedule = current_app.config['Schedule']
    Event = current_app.config['Event']
    Employee = current_app.config['Employee']

    try:
        today = date.today()

        # Query scheduled events with JOIN, filtering for current day and future
        scheduled_events = db.session.query(
            Schedule.id.label('schedule_id'),
            Event.project_name,
            Event.project_ref_num,
            Event.start_datetime,
            Event.due_datetime,
            Event.event_type,
            Employee.name.label('employee_name'),
            Schedule.schedule_datetime
        ).join(
            Schedule, Event.project_ref_num == Schedule.event_ref_num
        ).join(
            Employee, Schedule.employee_id == Employee.id
        ).filter(
            db.func.date(Schedule.schedule_datetime) >= today
        ).order_by(Schedule.schedule_datetime).all()

        # Validate each event's schedule date is within its start/due date range
        validation_errors = []

        for event in scheduled_events:
            schedule_date = event.schedule_datetime.date()
            start_date = event.start_datetime.date()
            due_date = event.due_datetime.date()

            # Check if scheduled date is within the event's valid date range
            if not (start_date <= schedule_date <= due_date):
                validation_errors.append({
                    'schedule_id': event.schedule_id,
                    'project_name': event.project_name,
                    'project_ref_num': event.project_ref_num,
                    'event_type': event.event_type,
                    'employee_name': event.employee_name,
                    'scheduled_date': schedule_date.strftime('%Y-%m-%d'),
                    'scheduled_time': event.schedule_datetime.strftime('%H:%M'),
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'due_date': due_date.strftime('%Y-%m-%d'),
                    'error_type': 'date_range_violation',
                    'error_message': f'Scheduled for {schedule_date.strftime("%m/%d/%Y")} but valid range is {start_date.strftime("%m/%d/%Y")} to {due_date.strftime("%m/%d/%Y")}'
                })

        # Format errors for the frontend
        formatted_errors = []
        for error in validation_errors:
            formatted_errors.append({
                'schedule_id': error['schedule_id'],
                'project_name': error['project_name'],
                'event_type': error['event_type'],
                'scheduled_date': error['scheduled_date'],
                'valid_start': error['start_date'],
                'valid_end': error['due_date'],
                'error': error['error_message']
            })

        return jsonify({
            'valid': len(validation_errors) == 0,
            'errors': formatted_errors,
            'total_events': len(scheduled_events),
            'valid_events': len(scheduled_events) - len(validation_errors)
        })

    except Exception as e:
        return jsonify({'error': f'Error validating schedule: {str(e)}'}), 500


@api_bp.route('/schedule/<int:schedule_id>')
def get_schedule_details(schedule_id):
    """Get details for a specific schedule"""
    db = current_app.extensions['sqlalchemy']
    Schedule = current_app.config['Schedule']
    Event = current_app.config['Event']

    try:
        schedule = db.session.get(Schedule, schedule_id)
        if not schedule:
            return jsonify({'error': 'Schedule not found'}), 404

        # Get the event details to include event type
        event = Event.query.filter_by(project_ref_num=schedule.event_ref_num).first()
        if not event:
            return jsonify({'error': 'Event not found'}), 404

        return jsonify({
            'id': schedule.id,
            'event_ref_num': schedule.event_ref_num,
            'employee_id': schedule.employee_id,
            'schedule_datetime': schedule.schedule_datetime.isoformat(),
            'event_type': event.event_type,
            'start_date': event.start_datetime.date().isoformat(),
            'due_date': event.due_datetime.date().isoformat()
        })

    except Exception as e:
        return jsonify({'error': f'Error fetching schedule: {str(e)}'}), 500


@api_bp.route('/reschedule', methods=['POST'])
def reschedule():
    """Reschedule an event - handles both JSON and FormData"""
    db = current_app.extensions['sqlalchemy']
    Schedule = current_app.config['Schedule']
    Event = current_app.config['Event']
    Employee = current_app.config['Employee']

    try:
        # Handle both JSON and FormData requests
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()

        schedule_id = data.get('schedule_id')
        new_date = data.get('new_date')
        new_time = data.get('new_time')
        new_employee_id = data.get('employee_id')

        # Get the current schedule
        schedule = db.session.get(Schedule, schedule_id)
        if not schedule:
            return jsonify({'error': 'Schedule not found'}), 404

        # Get the event to check type for validation
        event = Event.query.filter_by(project_ref_num=schedule.event_ref_num).first()
        if not event:
            return jsonify({'error': 'Event not found'}), 404

        # Parse and validate new date and time
        parsed_date = datetime.strptime(new_date, '%Y-%m-%d').date()
        parsed_time = datetime.strptime(new_time, '%H:%M').time()
        new_datetime = datetime.combine(parsed_date, parsed_time)

        # Validate date is within event range
        if not (event.start_datetime.date() <= parsed_date <= event.due_datetime.date()):
            return jsonify({'error': 'Date must be within event date range'}), 400

        # Check if new employee can work this event type
        new_employee = db.session.get(Employee, new_employee_id)
        if not new_employee or not new_employee.can_work_event_type(event.event_type):
            if event.event_type == 'Juicer':
                return jsonify({'error': 'Employee cannot work Juicer events. Only Club Supervisors and Juicer Baristas can work Juicer events.'}), 400
            elif event.event_type in ['Supervisor', 'Freeosk', 'Digitals']:
                return jsonify({'error': f'Employee cannot work {event.event_type} events. Only Club Supervisors and Lead Event Specialists can work this type of event.'}), 400
            else:
                return jsonify({'error': 'Employee cannot work this event type'}), 400

        # For Core events, check if new employee already has a Core event that day
        if event.event_type == 'Core':
            existing_core = Schedule.query.join(
                Event, Schedule.event_ref_num == Event.project_ref_num
            ).filter(
                Schedule.employee_id == new_employee_id,
                db.func.date(Schedule.schedule_datetime) == parsed_date,
                Event.event_type == 'Core',
                Schedule.id != schedule_id
            ).first()

            if existing_core:
                return jsonify({'error': 'Employee already has a Core event scheduled that day'}), 400

        # Submit to Crossmark API BEFORE updating local record
        from session_api_service import session_api as external_api

        # Calculate end datetime
        estimated_minutes = event.estimated_time or event.get_default_duration(event.event_type)
        end_datetime = new_datetime + timedelta(minutes=estimated_minutes)

        # Prepare API data
        rep_id = str(new_employee.external_id) if new_employee.external_id else None
        mplan_id = str(event.external_id) if event.external_id else None
        location_id = str(event.location_mvid) if event.location_mvid else None

        # Validate required API fields
        if not rep_id:
            return jsonify({'error': f'Missing Crossmark employee ID for {new_employee.name}'}), 400

        if not mplan_id:
            return jsonify({'error': 'Missing Crossmark event ID'}), 400

        if not location_id:
            return jsonify({'error': 'Missing Crossmark location ID'}), 400

        # Ensure session is authenticated
        try:
            if not external_api.ensure_authenticated():
                return jsonify({'error': 'Failed to authenticate with Crossmark API'}), 500
        except Exception as auth_error:
            current_app.logger.error(f"Authentication error: {str(auth_error)}")
            return jsonify({'error': 'Failed to authenticate with Crossmark API'}), 500

        # Submit to external API
        try:
            current_app.logger.info(
                f"Submitting reschedule to Crossmark API: "
                f"rep_id={rep_id}, mplan_id={mplan_id}, location_id={location_id}, "
                f"start={new_datetime.isoformat()}, end={end_datetime.isoformat()}"
            )

            api_result = external_api.schedule_mplan_event(
                rep_id=rep_id,
                mplan_id=mplan_id,
                location_id=location_id,
                start_datetime=new_datetime,
                end_datetime=end_datetime,
                planning_override=True
            )

            if not api_result.get('success'):
                error_message = api_result.get('message', 'Unknown API error')
                current_app.logger.error(f"Crossmark API error: {error_message}")
                return jsonify({'error': f'Failed to submit to Crossmark: {error_message}'}), 500

            current_app.logger.info(f"Successfully submitted reschedule to Crossmark API")

        except Exception as api_error:
            current_app.logger.error(f"API submission error: {str(api_error)}")
            return jsonify({'error': f'Failed to submit to Crossmark API: {str(api_error)}'}), 500

        # API submission successful - now update local record
        schedule.employee_id = new_employee_id
        schedule.schedule_datetime = new_datetime

        # Update event sync status
        event.sync_status = 'synced'
        event.last_synced = datetime.utcnow()

        db.session.commit()

        return jsonify({'success': True, 'message': 'Event rescheduled successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/reschedule_event', methods=['POST'])
def reschedule_event():
    """Reschedule an event to a new date, time, and/or employee"""
    db = current_app.extensions['sqlalchemy']
    Schedule = current_app.config['Schedule']
    Event = current_app.config['Event']
    Employee = current_app.config['Employee']

    try:
        data = request.get_json()
        schedule_id = data.get('schedule_id')
        new_date = data.get('date')
        new_time = data.get('time')
        new_employee_id = data.get('employee_id')

        # Get the current schedule
        schedule = db.session.get(Schedule, schedule_id)
        if not schedule:
            return jsonify({'error': 'Schedule not found'}), 404

        # Get the event to check type for validation
        event = Event.query.filter_by(project_ref_num=schedule.event_ref_num).first()
        if not event:
            return jsonify({'error': 'Event not found'}), 404

        # Parse and validate new date and time
        parsed_date = datetime.strptime(new_date, '%Y-%m-%d').date()
        parsed_time = datetime.strptime(new_time, '%H:%M').time()
        new_datetime = datetime.combine(parsed_date, parsed_time)

        # Validate date is within event range
        if not (event.start_datetime.date() <= parsed_date <= event.due_datetime.date()):
            return jsonify({'error': 'Date must be within event date range'}), 400

        # Check if new employee can work this event type
        new_employee = db.session.get(Employee, new_employee_id)
        if not new_employee or not new_employee.can_work_event_type(event.event_type):
            if event.event_type == 'Juicer':
                return jsonify({'error': 'Employee cannot work Juicer events. Only Club Supervisors and Juicer Baristas can work Juicer events.'}), 400
            elif event.event_type in ['Supervisor', 'Freeosk', 'Digitals']:
                return jsonify({'error': f'Employee cannot work {event.event_type} events. Only Club Supervisors and Lead Event Specialists can work this type of event.'}), 400
            else:
                return jsonify({'error': 'Employee cannot work this event type'}), 400

        # For Core events, check if new employee already has a Core event that day
        if event.event_type == 'Core':
            existing_core = Schedule.query.join(
                Event, Schedule.event_ref_num == Event.project_ref_num
            ).filter(
                Schedule.employee_id == new_employee_id,
                db.func.date(Schedule.schedule_datetime) == parsed_date,
                Event.event_type == 'Core',
                Schedule.id != schedule_id
            ).first()

            if existing_core:
                return jsonify({'error': 'Employee already has a Core event scheduled that day'}), 400

        # Submit to Crossmark API BEFORE updating local record
        from session_api_service import session_api as external_api

        # Calculate end datetime
        estimated_minutes = event.estimated_time or event.get_default_duration(event.event_type)
        end_datetime = new_datetime + timedelta(minutes=estimated_minutes)

        # Prepare API data
        rep_id = str(new_employee.external_id) if new_employee.external_id else None
        mplan_id = str(event.external_id) if event.external_id else None
        location_id = str(event.location_mvid) if event.location_mvid else None

        # Validate required API fields
        if not rep_id:
            return jsonify({'error': f'Missing Crossmark employee ID for {new_employee.name}'}), 400

        if not mplan_id:
            return jsonify({'error': 'Missing Crossmark event ID'}), 400

        if not location_id:
            return jsonify({'error': 'Missing Crossmark location ID'}), 400

        # Ensure session is authenticated
        try:
            if not external_api.ensure_authenticated():
                return jsonify({'error': 'Failed to authenticate with Crossmark API'}), 500
        except Exception as auth_error:
            current_app.logger.error(f"Authentication error: {str(auth_error)}")
            return jsonify({'error': 'Failed to authenticate with Crossmark API'}), 500

        # Submit to external API
        try:
            current_app.logger.info(
                f"Submitting reschedule_event to Crossmark API: "
                f"rep_id={rep_id}, mplan_id={mplan_id}, location_id={location_id}, "
                f"start={new_datetime.isoformat()}, end={end_datetime.isoformat()}"
            )

            api_result = external_api.schedule_mplan_event(
                rep_id=rep_id,
                mplan_id=mplan_id,
                location_id=location_id,
                start_datetime=new_datetime,
                end_datetime=end_datetime,
                planning_override=True
            )

            if not api_result.get('success'):
                error_message = api_result.get('message', 'Unknown API error')
                current_app.logger.error(f"Crossmark API error: {error_message}")
                return jsonify({'error': f'Failed to submit to Crossmark: {error_message}'}), 500

            current_app.logger.info(f"Successfully submitted reschedule_event to Crossmark API")

        except Exception as api_error:
            current_app.logger.error(f"API submission error: {str(api_error)}")
            return jsonify({'error': f'Failed to submit to Crossmark API: {str(api_error)}'}), 500

        # API submission successful - now update local record
        schedule.employee_id = new_employee_id
        schedule.schedule_datetime = new_datetime

        # Update event sync status
        event.sync_status = 'synced'
        event.last_synced = datetime.utcnow()

        db.session.commit()

        return jsonify({'success': True, 'message': 'Event rescheduled successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/unschedule/<int:schedule_id>', methods=['DELETE'])
def unschedule_event(schedule_id):
    """Unschedule an event - calls Crossmark API first, then deletes schedule and marks event as unscheduled"""
    db = current_app.extensions['sqlalchemy']
    Schedule = current_app.config['Schedule']
    Event = current_app.config['Event']

    try:
        # Get the schedule
        schedule = db.session.get(Schedule, schedule_id)
        if not schedule:
            return jsonify({'error': 'Schedule not found'}), 404

        # Get the related event
        event = Event.query.filter_by(project_ref_num=schedule.event_ref_num).first()
        if not event:
            return jsonify({'error': 'Related event not found'}), 404

        # Call Crossmark API BEFORE deleting local record
        if schedule.external_id:
            from session_api_service import session_api as external_api

            # Ensure session is authenticated
            try:
                if not external_api.ensure_authenticated():
                    return jsonify({'error': 'Failed to authenticate with Crossmark API'}), 500
            except Exception as auth_error:
                current_app.logger.error(f"Authentication error: {str(auth_error)}")
                return jsonify({'error': 'Failed to authenticate with Crossmark API'}), 500

            # Call API to delete/unschedule the event
            try:
                current_app.logger.info(
                    f"Submitting unschedule to Crossmark API: schedule_id={schedule.external_id}"
                )

                api_result = external_api.unschedule_mplan_event(str(schedule.external_id))

                if not api_result.get('success'):
                    error_message = api_result.get('message', 'Unknown API error')
                    current_app.logger.error(f"Crossmark API error: {error_message}")
                    return jsonify({'error': f'Failed to unschedule in Crossmark: {error_message}'}), 500

                current_app.logger.info(f"Successfully unscheduled event in Crossmark API")

            except Exception as api_error:
                current_app.logger.error(f"API submission error: {str(api_error)}")
                return jsonify({'error': f'Failed to submit to Crossmark API: {str(api_error)}'}), 500

        # API call successful (or no external_id) - now delete local record
        db.session.delete(schedule)

        # Check if this was the only schedule for the event
        remaining_schedules = Schedule.query.filter_by(event_ref_num=event.project_ref_num).count()
        if remaining_schedules == 0:
            event.is_scheduled = False

        # Update event sync status
        event.sync_status = 'synced'
        event.last_synced = datetime.utcnow()

        db.session.commit()

        return jsonify({'success': True, 'message': 'Event unscheduled successfully. Event moved back to unscheduled status.'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/trade_events', methods=['POST'])
def trade_events():
    """Trade two Core events between employees (keeping same times)"""
    db = current_app.extensions['sqlalchemy']
    Schedule = current_app.config['Schedule']
    Event = current_app.config['Event']

    try:
        data = request.get_json()
        schedule1_id = data.get('schedule_id')
        schedule2_id = data.get('trade_with_schedule_id')

        # Get both schedules
        schedule1 = db.session.get(Schedule, schedule1_id)
        schedule2 = db.session.get(Schedule, schedule2_id)

        if not schedule1 or not schedule2:
            return jsonify({'error': 'Schedule not found'}), 404

        # Verify both are Core events
        event1 = Event.query.filter_by(project_ref_num=schedule1.event_ref_num).first()
        event2 = Event.query.filter_by(project_ref_num=schedule2.event_ref_num).first()

        if not (event1.event_type == 'Core' and event2.event_type == 'Core'):
            return jsonify({'error': 'Both events must be Core events'}), 400

        # Trade the employees (keep times the same)
        from session_api_service import session_api as external_api
        from models import Employee

        original_emp1_id = schedule1.employee_id
        original_emp2_id = schedule2.employee_id
        schedule1_datetime = schedule1.schedule_datetime
        schedule2_datetime = schedule2.schedule_datetime

        # Get employee objects
        employee1 = db.session.get(Employee, original_emp1_id)
        employee2 = db.session.get(Employee, original_emp2_id)

        # Prepare API data for both events
        # Event 1 will get Employee 2
        rep_id_1 = str(employee2.external_id) if employee2.external_id else None
        mplan_id_1 = str(event1.external_id) if event1.external_id else None
        location_id_1 = str(event1.location_mvid) if event1.location_mvid else None

        # Event 2 will get Employee 1
        rep_id_2 = str(employee1.external_id) if employee1.external_id else None
        mplan_id_2 = str(event2.external_id) if event2.external_id else None
        location_id_2 = str(event2.location_mvid) if event2.location_mvid else None

        # Validate all required API fields
        if not all([rep_id_1, mplan_id_1, location_id_1, rep_id_2, mplan_id_2, location_id_2]):
            return jsonify({'error': 'Missing required Crossmark IDs for trade operation'}), 400

        # Ensure session is authenticated
        try:
            if not external_api.ensure_authenticated():
                return jsonify({'error': 'Failed to authenticate with Crossmark API'}), 500
        except Exception as auth_error:
            current_app.logger.error(f"Authentication error: {str(auth_error)}")
            return jsonify({'error': 'Failed to authenticate with Crossmark API'}), 500

        # Submit both trades to external API
        try:
            # Calculate end datetimes
            estimated_minutes_1 = event1.estimated_time or event1.get_default_duration(event1.event_type)
            end_datetime_1 = schedule1_datetime + timedelta(minutes=estimated_minutes_1)

            estimated_minutes_2 = event2.estimated_time or event2.get_default_duration(event2.event_type)
            end_datetime_2 = schedule2_datetime + timedelta(minutes=estimated_minutes_2)

            current_app.logger.info(
                f"Submitting trade to Crossmark API: "
                f"Event1({mplan_id_1}) -> Employee2({rep_id_1}), "
                f"Event2({mplan_id_2}) -> Employee1({rep_id_2})"
            )

            # Submit first trade
            api_result_1 = external_api.schedule_mplan_event(
                rep_id=rep_id_1,
                mplan_id=mplan_id_1,
                location_id=location_id_1,
                start_datetime=schedule1_datetime,
                end_datetime=end_datetime_1,
                planning_override=True
            )

            if not api_result_1.get('success'):
                error_message = api_result_1.get('message', 'Unknown API error')
                current_app.logger.error(f"Crossmark API error (trade 1): {error_message}")
                return jsonify({'error': f'Failed to submit first trade to Crossmark: {error_message}'}), 500

            # Submit second trade
            api_result_2 = external_api.schedule_mplan_event(
                rep_id=rep_id_2,
                mplan_id=mplan_id_2,
                location_id=location_id_2,
                start_datetime=schedule2_datetime,
                end_datetime=end_datetime_2,
                planning_override=True
            )

            if not api_result_2.get('success'):
                error_message = api_result_2.get('message', 'Unknown API error')
                current_app.logger.error(f"Crossmark API error (trade 2): {error_message}")
                # Note: First trade succeeded but second failed - this is a partial failure
                return jsonify({'error': f'Failed to submit second trade to Crossmark: {error_message}. First trade may have succeeded.'}), 500

            current_app.logger.info(f"Successfully submitted both trades to Crossmark API")

        except Exception as api_error:
            current_app.logger.error(f"API submission error: {str(api_error)}")
            return jsonify({'error': f'Failed to submit to Crossmark API: {str(api_error)}'}), 500

        # API submissions successful - now update local records
        schedule1.employee_id = original_emp2_id
        schedule2.employee_id = original_emp1_id

        # Update sync status for both events
        event1.sync_status = 'synced'
        event1.last_synced = datetime.utcnow()
        event2.sync_status = 'synced'
        event2.last_synced = datetime.utcnow()

        db.session.commit()

        return jsonify({'success': True, 'message': 'Events traded successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/change_employee', methods=['POST'])
def change_employee():
    """Change the employee for an event (keeping same date and time)"""
    db = current_app.extensions['sqlalchemy']
    Schedule = current_app.config['Schedule']
    Event = current_app.config['Event']
    Employee = current_app.config['Employee']

    try:
        data = request.get_json()
        schedule_id = data.get('schedule_id')
        new_employee_id = data.get('employee_id')

        # Get the schedule
        schedule = db.session.get(Schedule, schedule_id)
        if not schedule:
            return jsonify({'error': 'Schedule not found'}), 404

        # Get the event to check type for validation
        event = Event.query.filter_by(project_ref_num=schedule.event_ref_num).first()
        if not event:
            return jsonify({'error': 'Event not found'}), 404

        # Check if new employee can work this event type
        new_employee = db.session.get(Employee, new_employee_id)
        if not new_employee or not new_employee.can_work_event_type(event.event_type):
            if event.event_type == 'Juicer':
                return jsonify({'error': 'Employee cannot work Juicer events. Only Club Supervisors and Juicer Baristas can work Juicer events.'}), 400
            elif event.event_type in ['Supervisor', 'Freeosk', 'Digitals']:
                return jsonify({'error': f'Employee cannot work {event.event_type} events. Only Club Supervisors and Lead Event Specialists can work this type of event.'}), 400
            else:
                return jsonify({'error': 'Employee cannot work this event type'}), 400

        # For Core events, check if new employee already has a Core event that day
        if event.event_type == 'Core':
            event_date = schedule.schedule_datetime.date()
            existing_core = Schedule.query.join(
                Event, Schedule.event_ref_num == Event.project_ref_num
            ).filter(
                Schedule.employee_id == new_employee_id,
                db.func.date(Schedule.schedule_datetime) == event_date,
                Event.event_type == 'Core',
                Schedule.id != schedule_id
            ).first()

            if existing_core:
                return jsonify({'error': 'Employee already has a Core event scheduled that day'}), 400

        # Submit to Crossmark API BEFORE updating local record
        from session_api_service import session_api as external_api

        # Calculate end datetime
        estimated_minutes = event.estimated_time or event.get_default_duration(event.event_type)
        end_datetime = schedule.schedule_datetime + timedelta(minutes=estimated_minutes)

        # Prepare API data
        rep_id = str(new_employee.external_id) if new_employee.external_id else None
        mplan_id = str(event.external_id) if event.external_id else None
        location_id = str(event.location_mvid) if event.location_mvid else None

        # Validate required API fields
        if not rep_id:
            return jsonify({'error': f'Missing Crossmark employee ID for {new_employee.name}'}), 400

        if not mplan_id:
            return jsonify({'error': 'Missing Crossmark event ID'}), 400

        if not location_id:
            return jsonify({'error': 'Missing Crossmark location ID'}), 400

        # Ensure session is authenticated
        try:
            if not external_api.ensure_authenticated():
                return jsonify({'error': 'Failed to authenticate with Crossmark API'}), 500
        except Exception as auth_error:
            current_app.logger.error(f"Authentication error: {str(auth_error)}")
            return jsonify({'error': 'Failed to authenticate with Crossmark API'}), 500

        # Submit to external API
        try:
            current_app.logger.info(
                f"Submitting employee change to Crossmark API: "
                f"rep_id={rep_id}, mplan_id={mplan_id}, location_id={location_id}, "
                f"start={schedule.schedule_datetime.isoformat()}, end={end_datetime.isoformat()}"
            )

            api_result = external_api.schedule_mplan_event(
                rep_id=rep_id,
                mplan_id=mplan_id,
                location_id=location_id,
                start_datetime=schedule.schedule_datetime,
                end_datetime=end_datetime,
                planning_override=True
            )

            if not api_result.get('success'):
                error_message = api_result.get('message', 'Unknown API error')
                current_app.logger.error(f"Crossmark API error: {error_message}")
                return jsonify({'error': f'Failed to submit to Crossmark: {error_message}'}), 500

            current_app.logger.info(f"Successfully submitted employee change to Crossmark API")

        except Exception as api_error:
            current_app.logger.error(f"API submission error: {str(api_error)}")
            return jsonify({'error': f'Failed to submit to Crossmark API: {str(api_error)}'}), 500

        # API submission successful - now update local record
        schedule.employee_id = new_employee_id

        # Update event sync status
        event.sync_status = 'synced'
        event.last_synced = datetime.utcnow()

        db.session.commit()

        return jsonify({'success': True, 'message': 'Employee changed successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/export/schedule')
def export_schedule():
    """Export scheduled events to CalendarSchedule.csv (from today forward only)"""
    db = current_app.extensions['sqlalchemy']
    Schedule = current_app.config['Schedule']
    Event = current_app.config['Event']
    Employee = current_app.config['Employee']

    try:
        # Check if only valid events should be exported
        valid_only = request.args.get('valid_only') == 'true'

        # Get current date to filter out past events
        today = date.today()

        # Query scheduled events with JOIN, filtering for current day and future
        scheduled_events = db.session.query(
            Event.project_name,
            Event.project_ref_num,
            Event.location_mvid,
            Event.store_number,
            Event.store_name,
            Event.start_datetime,
            Event.due_datetime,
            Event.estimated_time,
            Employee.name.label('rep_name'),
            Employee.id.label('employee_id'),
            Schedule.schedule_datetime
        ).join(
            Schedule, Event.project_ref_num == Schedule.event_ref_num
        ).join(
            Employee, Schedule.employee_id == Employee.id
        ).filter(
            db.func.date(Schedule.schedule_datetime) >= today
        ).order_by(Schedule.schedule_datetime).all()

        # Validate each event's schedule date is within its start/due date range
        valid_events = []
        invalid_events = []

        for event in scheduled_events:
            schedule_date = event.schedule_datetime.date()
            start_date = event.start_datetime.date()
            due_date = event.due_datetime.date()

            # Check if scheduled date is within the event's valid date range
            if start_date <= schedule_date <= due_date:
                valid_events.append(event)
            else:
                invalid_events.append({
                    'project_name': event.project_name,
                    'project_ref_num': event.project_ref_num,
                    'scheduled_date': schedule_date,
                    'start_date': start_date,
                    'due_date': due_date,
                    'employee': event.rep_name
                })

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers in correct order
        writer.writerow([
            'Project Name', 'Project Reference Number', 'Location MVID',
            'Store Number', 'Store Name', 'Start Date/Time', 'Due Date/Time',
            'Estimated Time', 'Rep Name', 'Employee ID', 'Schedule Date/Time'
        ])

        # Add validation summary comment rows if there are invalid events (unless valid_only is true)
        if invalid_events and not valid_only:
            writer.writerow([])  # Empty row
            writer.writerow(['# VALIDATION WARNINGS - The following events were EXCLUDED due to invalid schedule dates:'])
            writer.writerow(['# Project Name', 'Project Ref', 'Scheduled Date', 'Valid Range Start', 'Valid Range End', 'Assigned Employee'])
            for invalid in invalid_events:
                writer.writerow([
                    f"# {invalid['project_name'][:50]}...",
                    f"# {invalid['project_ref_num']}",
                    f"# {invalid['scheduled_date']}",
                    f"# {invalid['start_date']}",
                    f"# {invalid['due_date']}",
                    f"# {invalid['employee']}"
                ])
            writer.writerow(['# END VALIDATION WARNINGS'])
            writer.writerow([])  # Empty row

        # Write only valid data rows
        for event in valid_events:
            writer.writerow([
                event.project_name,
                event.project_ref_num,
                event.location_mvid or '',
                event.store_number or '',
                event.store_name or '',
                event.start_datetime.strftime('%m/%d/%Y %I:%M:%S %p'),
                event.due_datetime.strftime('%m/%d/%Y %I:%M:%S %p'),
                event.estimated_time or '',
                event.rep_name,
                event.employee_id,
                event.schedule_datetime.strftime('%m/%d/%Y %I:%M:%S %p')
            ])

        # Prepare response
        output.seek(0)
        csv_data = output.getvalue()
        output.close()

        response = make_response(csv_data)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=CalendarSchedule.csv'

        return response

    except Exception as e:
        return jsonify({'error': f'Error generating export: {str(e)}'}), 500


@api_bp.route('/import/events', methods=['POST'])
def import_events():
    """Import unscheduled events from WorkBankVisits.csv file"""
    db = current_app.extensions['sqlalchemy']
    Event = current_app.config['Event']
    Employee = current_app.config['Employee']

    try:
        # Check if file is provided
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Validate file extension
        if not file.filename.lower().endswith('.csv'):
            return jsonify({'error': 'File must be a CSV file'}), 400

        # Read and parse CSV
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)

        # Validate CSV headers
        expected_headers = {
            'Project Name', 'Project Reference Number', 'Location MVID',
            'Store Number', 'Store Name', 'Start Date/Time', 'Due Date/Time',
            'Estimated Time', 'Employee ID', 'Rep Name'
        }

        csv_headers = set(csv_reader.fieldnames)
        missing_headers = expected_headers - csv_headers
        if missing_headers:
            return jsonify({'error': f'Missing required CSV headers: {", ".join(missing_headers)}'}), 400

        imported_count = 0
        employees_added = set()

        # Begin database transaction
        try:
            for row in csv_reader:
                # First, ensure employee exists
                employee_id = row['Employee ID'].strip() if row['Employee ID'] else ''
                rep_name = row['Rep Name'].strip() if row['Rep Name'] else ''

                if employee_id and rep_name and employee_id not in employees_added:
                    existing_employee = Employee.query.filter_by(id=employee_id).first()
                    if not existing_employee:
                        new_employee = Employee(id=employee_id, name=rep_name)
                        db.session.add(new_employee)
                        employees_added.add(employee_id)

                # Parse and validate event data
                project_ref_num = int(row['Project Reference Number'])

                # Check for duplicate
                existing_event = Event.query.filter_by(project_ref_num=project_ref_num).first()
                if existing_event:
                    continue  # Skip duplicates

                # Parse dates with correct format for MM/DD/YYYY HH:MM:SS AM/PM
                start_datetime = datetime.strptime(row['Start Date/Time'], '%m/%d/%Y %I:%M:%S %p')
                due_datetime = datetime.strptime(row['Due Date/Time'], '%m/%d/%Y %I:%M:%S %p')

                # Create new event
                new_event = Event(
                    project_name=row['Project Name'].strip() if row['Project Name'] else '',
                    project_ref_num=project_ref_num,
                    location_mvid=row['Location MVID'].strip() if row['Location MVID'] else None,
                    store_number=int(row['Store Number']) if row['Store Number'] else None,
                    store_name=row['Store Name'].strip() if row['Store Name'] else None,
                    start_datetime=start_datetime,
                    due_datetime=due_datetime,
                    estimated_time=int(row['Estimated Time']) if row['Estimated Time'] else None,
                    is_scheduled=False
                )

                # Auto-detect and set event type
                new_event.event_type = new_event.detect_event_type()

                # Set default duration if estimated_time is not set
                new_event.set_default_duration()

                db.session.add(new_event)
                imported_count += 1

            # Commit all changes
            db.session.commit()

            return jsonify({
                'imported_count': imported_count,
                'message': f'Successfully imported {imported_count} events'
            }), 200

        except Exception as e:
            # Rollback transaction on error
            db.session.rollback()
            return jsonify({'error': f'Database error during import: {str(e)}'}), 500

    except Exception as e:
        return jsonify({'error': f'Error processing CSV file: {str(e)}'}), 400


@api_bp.route('/import/scheduled', methods=['POST'])
def import_scheduled_events():
    """Import already scheduled events from CSV file"""
    db = current_app.extensions['sqlalchemy']
    Event = current_app.config['Event']
    Employee = current_app.config['Employee']
    Schedule = current_app.config['Schedule']
    EmployeeWeeklyAvailability = current_app.config['EmployeeWeeklyAvailability']

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file.filename.lower().endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400

    try:
        # Read CSV file
        content = file.read().decode('utf-8')
        csv_data = list(csv.DictReader(StringIO(content)))

        imported_count = 0

        try:
            for row in csv_data:
                # Parse dates
                start_datetime = datetime.strptime(row['Start Date/Time'], '%m/%d/%Y %I:%M:%S %p')
                due_datetime = datetime.strptime(row['Due Date/Time'], '%m/%d/%Y %I:%M:%S %p')
                schedule_datetime = datetime.strptime(row['Schedule Date/Time'], '%m/%d/%Y %I:%M:%S %p')

                # Get or create the event first
                project_ref_num = row['Project Reference Number'].strip() if row['Project Reference Number'] else None

                # Check if event already exists
                existing_event = Event.query.filter_by(project_ref_num=project_ref_num).first()

                if not existing_event:
                    # Create new event
                    new_event = Event(
                        project_name=row['Project Name'].strip() if row['Project Name'] else '',
                        project_ref_num=project_ref_num,
                        location_mvid=row['Location MVID'].strip() if row['Location MVID'] else None,
                        store_number=int(row['Store Number']) if row['Store Number'] else None,
                        store_name=row['Store Name'].strip() if row['Store Name'] else None,
                        start_datetime=start_datetime,
                        due_datetime=due_datetime,
                        estimated_time=int(row['Estimated Time']) if row['Estimated Time'] else None,
                        is_scheduled=True
                    )

                    # Auto-detect and set event type
                    new_event.event_type = new_event.detect_event_type()

                    # Set default duration if estimated_time is not set
                    new_event.set_default_duration()

                    db.session.add(new_event)
                    db.session.flush()  # Get the ID
                    event = new_event
                else:
                    # Update existing event to be scheduled
                    existing_event.is_scheduled = True
                    event = existing_event

                # Get or create the employee
                employee_id = row['Employee ID'].strip() if row['Employee ID'] else None
                employee_name = row['Rep Name'].strip() if row['Rep Name'] else None

                if employee_id:
                    employee = Employee.query.filter_by(id=employee_id).first()
                    if not employee:
                        # Create new employee if not exists
                        employee = Employee(
                            id=employee_id,
                            name=employee_name or f'Employee {employee_id}',
                            is_active=True,
                            is_supervisor=False,
                            job_title='Event Specialist',  # Default job title
                            adult_beverage_trained=False
                        )
                        db.session.add(employee)

                        # Add default weekly availability (available all days)
                        availability = EmployeeWeeklyAvailability(
                            employee_id=employee_id,
                            monday=True,
                            tuesday=True,
                            wednesday=True,
                            thursday=True,
                            friday=True,
                            saturday=True,
                            sunday=True
                        )
                        db.session.add(availability)

                    # Create the schedule entry
                    existing_schedule = Schedule.query.filter_by(
                        event_ref_num=event.project_ref_num,
                        employee_id=employee_id
                    ).first()

                    if not existing_schedule:
                        new_schedule = Schedule(
                            event_ref_num=event.project_ref_num,
                            employee_id=employee_id,
                            schedule_datetime=schedule_datetime
                        )
                        db.session.add(new_schedule)

                    # AUTO-SCHEDULE SUPERVISOR EVENT if this is a Core event
                    if event.event_type == 'Core' and not existing_schedule:
                        from routes.scheduling import auto_schedule_supervisor_event
                        scheduled_date = schedule_datetime.date()
                        auto_schedule_supervisor_event(
                            db, Event, Schedule, Employee,
                            event.project_ref_num,
                            scheduled_date,
                            employee_id
                        )

                imported_count += 1

            # Commit all changes
            db.session.commit()

            return jsonify({
                'imported_count': imported_count,
                'message': f'Successfully imported {imported_count} scheduled events'
            }), 200

        except Exception as e:
            # Rollback transaction on error
            db.session.rollback()
            return jsonify({'error': f'Database error during import: {str(e)}'}), 500

    except Exception as e:
        return jsonify({'error': f'Error processing CSV file: {str(e)}'}), 400
