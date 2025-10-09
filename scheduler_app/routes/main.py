"""
Main application routes blueprint
Handles dashboard, events list, and calendar views
"""
from flask import Blueprint, render_template, request, jsonify, current_app
from routes.auth import require_authentication
from models import init_models
from datetime import datetime, date, timedelta

# Create blueprint
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@require_authentication()
def dashboard():
    """Main dashboard view with today's schedule and statistics"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']

    # Get models
    Employee = current_app.config['Employee']
    Event = current_app.config['Event']
    Schedule = current_app.config['Schedule']

    # Get today's date - always use current system date
    today = date.today()
    two_weeks_from_now = today + timedelta(days=14)

    # Get Club Supervisor name for welcome message
    supervisor = Employee.query.filter_by(job_title='Club Supervisor', is_active=True).first()
    supervisor_first_name = None
    if supervisor:
        supervisor_first_name = supervisor.name.split()[0] if supervisor.name else None

    # Get today's Core events and Juicer Production events (scheduled)
    today_core_events = db.session.query(
        Schedule, Event, Employee
    ).join(
        Event, Schedule.event_ref_num == Event.project_ref_num
    ).outerjoin(
        Employee, db.or_(
            Schedule.employee_id == Employee.id,
            Schedule.employee_id == Employee.name
        )
    ).filter(
        db.func.date(Schedule.schedule_datetime) == today,
        db.or_(
            Event.event_type == 'Core',
            db.and_(
                Event.event_type == 'Juicer',
                Event.project_name.contains('Production'),
                ~Event.project_name.contains('Survey')
            )
        )
    ).order_by(
        Schedule.schedule_datetime.asc()
    ).all()

    # Get tomorrow's Core events and Juicer Production events (scheduled)
    tomorrow = today + timedelta(days=1)
    tomorrow_core_events = db.session.query(
        Schedule, Event, Employee
    ).join(
        Event, Schedule.event_ref_num == Event.project_ref_num
    ).join(
        Employee, Schedule.employee_id == Employee.id
    ).filter(
        db.func.date(Schedule.schedule_datetime) == tomorrow,
        db.or_(
            Event.event_type == 'Core',
            db.and_(
                Event.event_type == 'Juicer',
                Event.project_name.contains('Production'),
                ~Event.project_name.contains('Survey')
            )
        )
    ).order_by(
        Schedule.schedule_datetime.asc()
    ).all()

    # Get unscheduled events within 2 weeks - ONLY Unstaffed are truly unscheduled
    unscheduled_events_2weeks = Event.query.filter(
        Event.condition == 'Unstaffed',
        Event.start_datetime >= today,
        Event.start_datetime <= two_weeks_from_now
    ).order_by(
        Event.start_datetime.asc(),
        Event.due_datetime.asc()
    ).all()

    # Calculate statistics with new logic
    # Total events within 2 weeks (from today to 2 weeks from now)
    total_events_2weeks = Event.query.filter(
        Event.start_datetime >= today,
        Event.start_datetime <= two_weeks_from_now,
        # Exclude canceled and expired
        ~Event.condition.in_(['Canceled', 'Expired'])
    ).count()

    # Scheduled events: Scheduled + Submitted conditions within date range
    scheduled_events_2weeks = Event.query.filter(
        Event.start_datetime >= today,
        Event.start_datetime <= two_weeks_from_now,
        Event.condition.in_(['Scheduled', 'Submitted'])
    ).count()

    # Calculate scheduling percentage
    scheduling_percentage = 0
    if total_events_2weeks > 0:
        scheduling_percentage = round((scheduled_events_2weeks / total_events_2weeks) * 100, 1)

    # Core event counts by time slots for today
    core_time_slots = {}
    core_times = ['9:45', '10:30', '11:00', '11:30']

    for time_slot in core_times:
        count = 0
        for schedule, event, employee in today_core_events:
            scheduled_time = schedule.schedule_datetime.strftime('%H:%M')
            if ((time_slot == '9:45' and scheduled_time == '09:45') or
                (time_slot == '10:30' and scheduled_time == '10:30') or
                (time_slot == '11:00' and scheduled_time == '11:00') or
                (time_slot == '11:30' and scheduled_time == '11:30')):
                count += 1
        core_time_slots[time_slot] = count

    # Additional statistics
    total_core_today = len(today_core_events)
    total_digitals_today = db.session.query(
        Schedule, Event
    ).join(
        Event, Schedule.event_ref_num == Event.project_ref_num
    ).filter(
        db.func.date(Schedule.schedule_datetime) == today,
        Event.event_type == 'Digitals'
    ).count()

    # Active employees count
    active_employees_count = Employee.query.filter_by(is_active=True).count()

    # Events scheduled this week
    week_start = today - timedelta(days=today.weekday())
    events_this_week = db.session.query(Schedule).filter(
        db.func.date(Schedule.schedule_datetime) >= week_start,
        db.func.date(Schedule.schedule_datetime) < week_start + timedelta(days=7)
    ).count()

    return render_template('index.html',
                         supervisor_first_name=supervisor_first_name,
                         today_core_events=today_core_events,
                         tomorrow_core_events=tomorrow_core_events,
                         unscheduled_events_2weeks=unscheduled_events_2weeks,
                         total_events_2weeks=total_events_2weeks,
                         scheduled_events_2weeks=scheduled_events_2weeks,
                         scheduling_percentage=scheduling_percentage,
                         core_time_slots=core_time_slots,
                         total_core_today=total_core_today,
                         total_digitals_today=total_digitals_today,
                         active_employees_count=active_employees_count,
                         events_this_week=events_this_week,
                         today=today,
                         today_date=today.strftime('%Y-%m-%d'),
                         tomorrow=tomorrow)


@main_bp.route('/events')
@main_bp.route('/unscheduled')  # Keep old route for compatibility
def unscheduled_events():
    """Events list view with filtering by condition and type"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    Event = current_app.config['Event']

    # Get filter parameters
    condition_filter = request.args.get('condition', 'unstaffed')  # Default to unstaffed (unscheduled)
    event_type_filter = request.args.get('event_type', '')

    # Map condition display names
    condition_display_map = {
        'unstaffed': 'Unscheduled',
        'scheduled': 'Scheduled',
        'submitted': 'Submitted',
        'paused': 'Paused',
        'reissued': 'Reissued'
    }

    # Build query based on condition
    if condition_filter == 'unstaffed':
        # Only Unstaffed events are truly unscheduled
        query = Event.query.filter_by(condition='Unstaffed')
    elif condition_filter == 'scheduled':
        # Scheduled condition events
        query = Event.query.filter_by(condition='Scheduled')
    elif condition_filter == 'submitted':
        # Submitted condition events
        query = Event.query.filter_by(condition='Submitted')
    elif condition_filter == 'paused':
        # Paused condition events
        query = Event.query.filter_by(condition='Paused')
    elif condition_filter == 'reissued':
        # Reissued condition events
        query = Event.query.filter_by(condition='Reissued')
    else:
        # Default to unstaffed
        query = Event.query.filter_by(condition='Unstaffed')

    # Apply event type filter if specified
    if event_type_filter and event_type_filter != '':
        query = query.filter_by(event_type=event_type_filter)

    # Order results
    events = query.order_by(
        Event.start_datetime.asc(),
        Event.due_datetime.asc()
    ).all()

    # Calculate priority for each event (for visual coding)
    # Also fetch schedule/employee info for scheduled events
    Schedule = current_app.config['Schedule']
    Employee = current_app.config['Employee']

    today = date.today()
    events_with_priority = []
    for event in events:
        days_remaining = (event.due_datetime.date() - today).days
        if days_remaining <= 1:
            priority = 'critical'
            priority_color = 'red'
        elif days_remaining <= 7:
            priority = 'urgent'
            priority_color = 'yellow'
        else:
            priority = 'normal'
            priority_color = 'green'

        # Add priority attributes to event object
        event.priority = priority
        event.priority_color = priority_color
        event.days_remaining = days_remaining

        # For scheduled events, fetch schedule and employee information
        if condition_filter in ['scheduled', 'submitted', 'reissued']:
            schedules = Schedule.query.filter_by(event_ref_num=event.project_ref_num).all()
            if schedules:
                # Get employee names and times for all schedules
                schedule_info = []
                for schedule in schedules:
                    employee = Employee.query.get(schedule.employee_id)
                    if employee:
                        schedule_info.append({
                            'employee_name': employee.name,
                            'schedule_datetime': schedule.schedule_datetime,
                            'schedule_time': schedule.schedule_datetime.strftime('%I:%M %p') if schedule.schedule_datetime else 'N/A'
                        })
                event.schedule_info = schedule_info
            else:
                event.schedule_info = []
        else:
            event.schedule_info = []

        events_with_priority.append(event)

    # Get all distinct event types for the filter dropdown
    event_types = db.session.query(Event.event_type).distinct().order_by(Event.event_type).all()
    event_types = [et[0] for et in event_types]

    return render_template('unscheduled.html',
                         events=events_with_priority,
                         event_types=event_types,
                         selected_event_type=event_type_filter,
                         condition=condition_filter,
                         condition_display=condition_display_map.get(condition_filter, 'Unscheduled'))


@main_bp.route('/calendar')
def calendar_view():
    """Display calendar view of scheduled events"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    Schedule = current_app.config['Schedule']
    Event = current_app.config['Event']
    Employee = current_app.config['Employee']

    # Get the date from query params, default to today
    date_str = request.args.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()

    # Get all scheduled events for the selected month
    start_of_month = selected_date.replace(day=1)
    if start_of_month.month == 12:
        end_of_month = start_of_month.replace(year=start_of_month.year + 1, month=1)
    else:
        end_of_month = start_of_month.replace(month=start_of_month.month + 1)

    # Get scheduled events for the month
    scheduled_events = db.session.query(Schedule, Event, Employee).join(
        Event, Schedule.event_ref_num == Event.project_ref_num
    ).join(
        Employee, Schedule.employee_id == Employee.id
    ).filter(
        db.func.date(Schedule.schedule_datetime) >= start_of_month,
        db.func.date(Schedule.schedule_datetime) < end_of_month
    ).order_by(Schedule.schedule_datetime).all()

    # Group events by date (convert dates to strings for JSON serialization)
    events_by_date = {}
    for schedule, event, employee in scheduled_events:
        event_date = schedule.schedule_datetime.date()
        date_str = event_date.strftime('%Y-%m-%d')
        if date_str not in events_by_date:
            events_by_date[date_str] = []

        events_by_date[date_str].append({
            'id': schedule.id,
            'event_name': event.project_name,
            'event_type': event.event_type,
            'employee_name': employee.name,
            'time': schedule.schedule_datetime.strftime('%I:%M %p'),
            'store_name': event.store_name,
            'estimated_time': event.estimated_time
        })

    return render_template('calendar.html',
                         selected_date=selected_date,
                         events_by_date=events_by_date)


@main_bp.route('/calendar/day/<date>')
def calendar_day_view(date):
    """Get events for a specific day (AJAX endpoint)"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    Schedule = current_app.config['Schedule']
    Event = current_app.config['Event']
    Employee = current_app.config['Employee']

    try:
        selected_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    # Get scheduled events for the specific day
    scheduled_events = db.session.query(Schedule, Event, Employee).join(
        Event, Schedule.event_ref_num == Event.project_ref_num
    ).join(
        Employee, Schedule.employee_id == Employee.id
    ).filter(
        db.func.date(Schedule.schedule_datetime) == selected_date
    ).order_by(Schedule.schedule_datetime).all()

    events_data = []
    for schedule, event, employee in scheduled_events:
        events_data.append({
            'id': schedule.id,
            'event_name': event.project_name,
            'event_type': event.event_type,
            'employee_name': employee.name,
            'employee_id': employee.id,
            'time': schedule.schedule_datetime.strftime('%I:%M %p'),
            'datetime': schedule.schedule_datetime.isoformat(),
            'store_name': event.store_name,
            'estimated_time': event.estimated_time
        })

    return jsonify({
        'date': selected_date.strftime('%Y-%m-%d'),
        'formatted_date': selected_date.strftime('%A, %B %d, %Y'),
        'events': events_data
    })


@main_bp.route('/api/schedule/print/<date>')
@require_authentication()
def print_schedule_by_date(date):
    """Get schedule data for printing for a specific date"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    Schedule = current_app.config['Schedule']
    Event = current_app.config['Event']
    Employee = current_app.config['Employee']

    try:
        selected_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    # Get Core and Juicer Production events for the specific day
    scheduled_events = db.session.query(Schedule, Event, Employee).join(
        Event, Schedule.event_ref_num == Event.project_ref_num
    ).join(
        Employee, Schedule.employee_id == Employee.id
    ).filter(
        db.func.date(Schedule.schedule_datetime) == selected_date,
        db.or_(
            Event.event_type == 'Core',
            db.and_(
                Event.event_type == 'Juicer',
                Event.project_name.contains('Production'),
                ~Event.project_name.contains('Survey')
            )
        )
    ).order_by(Schedule.schedule_datetime).all()

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
        'date': selected_date.strftime('%Y-%m-%d'),
        'formatted_date': selected_date.strftime('%A, %B %d, %Y'),
        'events': events_data
    })
