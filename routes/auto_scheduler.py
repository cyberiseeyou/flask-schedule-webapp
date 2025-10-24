"""
Auto-scheduler routes
Handles scheduler runs, review, and approval workflow
"""
from flask import Blueprint, render_template, request, jsonify, current_app
from datetime import datetime, timedelta, date
from sqlalchemy import func

from services import SchedulingEngine
from routes.auth import require_authentication

auto_scheduler_bp = Blueprint('auto_scheduler', __name__, url_prefix='/auto-schedule')


@auto_scheduler_bp.route('/')
@require_authentication()
def index():
    """Main auto-scheduler page with scheduling progress"""
    db = current_app.extensions['sqlalchemy']
    Event = current_app.config['Event']
    SchedulerRunHistory = current_app.config['SchedulerRunHistory']

    # Get today's date
    today = date.today()
    two_weeks_from_now = today + timedelta(days=14)

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

    # Get unscheduled events within 2 weeks - ONLY Unstaffed are truly unscheduled
    unscheduled_events_2weeks = Event.query.filter(
        Event.condition == 'Unstaffed',
        Event.start_datetime >= today,
        Event.start_datetime <= two_weeks_from_now
    ).order_by(
        Event.start_datetime.asc(),
        Event.due_datetime.asc()
    ).all()

    # Calculate scheduling percentage
    scheduling_percentage = 0
    if total_events_2weeks > 0:
        scheduling_percentage = round((scheduled_events_2weeks / total_events_2weeks) * 100, 1)

    # Get last scheduler run info
    last_run = db.session.query(SchedulerRunHistory).order_by(
        SchedulerRunHistory.started_at.desc()
    ).first()

    return render_template('auto_scheduler_main.html',
                         unscheduled_events_2weeks=unscheduled_events_2weeks,
                         total_events_2weeks=total_events_2weeks,
                         scheduled_events_2weeks=scheduled_events_2weeks,
                         scheduling_percentage=scheduling_percentage,
                         last_run=last_run,
                         today=today)


@auto_scheduler_bp.route('/run', methods=['POST'])
def run_scheduler():
    """Manually trigger auto-scheduler run"""
    db = current_app.extensions['sqlalchemy']
    models = {k: current_app.config[k] for k in [
        'Employee', 'Event', 'Schedule', 'SchedulerRunHistory',
        'PendingSchedule', 'RotationAssignment', 'ScheduleException',
        'EmployeeTimeOff', 'EmployeeAvailability', 'EmployeeWeeklyAvailability'
    ]}

    engine = SchedulingEngine(db.session, models)

    try:
        run = engine.run_auto_scheduler(run_type='manual')

        return jsonify({
            'success': True,
            'run_id': run.id,
            'message': 'Scheduler run completed',
            'stats': {
                'total_events_processed': run.total_events_processed,
                'events_scheduled': run.events_scheduled,
                'events_requiring_swaps': run.events_requiring_swaps,
                'events_failed': run.events_failed
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auto_scheduler_bp.route('/status/<int:run_id>', methods=['GET'])
def get_run_status(run_id):
    """Get status of a scheduler run"""
    SchedulerRunHistory = current_app.config['SchedulerRunHistory']
    db = current_app.extensions['sqlalchemy']

    run = db.session.query(SchedulerRunHistory).get(run_id)

    if not run:
        return jsonify({'success': False, 'error': 'Run not found'}), 404

    return jsonify({
        'run_id': run.id,
        'status': run.status,
        'started_at': run.started_at.isoformat(),
        'completed_at': run.completed_at.isoformat() if run.completed_at else None,
        'total_events_processed': run.total_events_processed,
        'events_scheduled': run.events_scheduled,
        'events_requiring_swaps': run.events_requiring_swaps,
        'events_failed': run.events_failed,
        'error_message': run.error_message
    })


@auto_scheduler_bp.route('/review')
def review():
    """Render proposal review page"""
    db = current_app.extensions['sqlalchemy']
    SchedulerRunHistory = current_app.config['SchedulerRunHistory']

    # Get latest unapproved run
    latest_run = db.session.query(SchedulerRunHistory).filter(
        SchedulerRunHistory.approved_at.is_(None),
        SchedulerRunHistory.status == 'completed'
    ).order_by(SchedulerRunHistory.started_at.desc()).first()

    if not latest_run:
        return render_template('auto_schedule_review.html',
                             run=None,
                             message="No pending schedule proposals to review")

    return render_template('auto_schedule_review.html', run=latest_run)


@auto_scheduler_bp.route('/api/pending', methods=['GET'])
def get_pending_schedules():
    """Get pending schedule data for review (AJAX)"""
    db = current_app.extensions['sqlalchemy']
    SchedulerRunHistory = current_app.config['SchedulerRunHistory']
    PendingSchedule = current_app.config['PendingSchedule']
    Event = current_app.config['Event']
    Employee = current_app.config['Employee']

    run_id = request.args.get('run_id', type=int)

    if run_id:
        run = db.session.query(SchedulerRunHistory).get(run_id)
    else:
        # Get latest unapproved run
        run = db.session.query(SchedulerRunHistory).filter(
            SchedulerRunHistory.approved_at.is_(None),
            SchedulerRunHistory.status == 'completed'
        ).order_by(SchedulerRunHistory.started_at.desc()).first()

    if not run:
        return jsonify({'success': False, 'error': 'No pending run found'}), 404

    # Get all pending schedules for this run
    pending = db.session.query(PendingSchedule).filter_by(scheduler_run_id=run.id).all()

    # Categorize schedules
    newly_scheduled = []
    swaps = []
    failed = []
    daily_preview = {}

    for ps in pending:
        event = db.session.query(Event).filter_by(project_ref_num=ps.event_ref_num).first()
        employee = db.session.query(Employee).get(ps.employee_id) if ps.employee_id else None

        ps_data = {
            'id': ps.id,
            'event_ref_num': ps.event_ref_num,
            'event_name': event.project_name if event else 'Unknown',
            'event_type': event.event_type if event else 'Unknown',
            'employee_id': ps.employee_id,
            'employee_name': employee.name if employee else 'Unassigned',
            'schedule_datetime': ps.schedule_datetime.isoformat() if ps.schedule_datetime else None,
            'schedule_date': ps.schedule_datetime.date().isoformat() if ps.schedule_datetime else None,
            'schedule_time': ps.schedule_time.strftime('%H:%M') if ps.schedule_time else None,
            'is_swap': ps.is_swap,
            'swap_reason': ps.swap_reason,
            'failure_reason': ps.failure_reason
        }

        if ps.failure_reason:
            failed.append(ps_data)
        elif ps.is_swap:
            # Get bumped event details
            if ps.bumped_event_ref_num:
                bumped_event = db.session.query(Event).filter_by(project_ref_num=ps.bumped_event_ref_num).first()
                ps_data['bumped_event_name'] = bumped_event.project_name if bumped_event else 'Unknown'
            swaps.append(ps_data)
        else:
            newly_scheduled.append(ps_data)

        # Add to daily preview
        if ps.schedule_datetime:
            date_key = ps.schedule_datetime.date().isoformat()
            if date_key not in daily_preview:
                daily_preview[date_key] = []
            daily_preview[date_key].append(ps_data)

    return jsonify({
        'run_id': run.id,
        'newly_scheduled': newly_scheduled,
        'swaps': swaps,
        'failed': failed,
        'daily_preview': daily_preview,
        'stats': {
            'total_events_processed': run.total_events_processed,
            'events_scheduled': run.events_scheduled,
            'events_requiring_swaps': run.events_requiring_swaps,
            'events_failed': run.events_failed
        }
    })


@auto_scheduler_bp.route('/api/pending/<int:pending_id>', methods=['PUT'])
def edit_pending_schedule(pending_id):
    """Edit a pending schedule before approval"""
    db = current_app.extensions['sqlalchemy']
    PendingSchedule = current_app.config['PendingSchedule']
    Employee = current_app.config['Employee']

    pending = db.session.query(PendingSchedule).get(pending_id)
    if not pending:
        return jsonify({'success': False, 'error': 'Pending schedule not found'}), 404

    data = request.get_json()

    # Update employee if provided
    if 'employee_id' in data:
        employee = db.session.query(Employee).get(data['employee_id'])
        if not employee:
            return jsonify({'success': False, 'error': 'Employee not found'}), 400
        pending.employee_id = data['employee_id']

    # Update datetime if provided
    if 'schedule_datetime' in data:
        try:
            pending.schedule_datetime = datetime.fromisoformat(data['schedule_datetime'])
            pending.schedule_time = pending.schedule_datetime.time()
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid datetime format'}), 400

    pending.status = 'user_edited'
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Pending schedule updated',
        'updated_schedule': {
            'id': pending.id,
            'employee_id': pending.employee_id,
            'schedule_datetime': pending.schedule_datetime.isoformat() if pending.schedule_datetime else None
        }
    })


@auto_scheduler_bp.route('/approve', methods=['POST'])
def approve_schedule():
    """Approve proposed schedule and submit to Crossmark API"""
    from session_api_service import session_api as external_api

    db = current_app.extensions['sqlalchemy']

    models_needed = ['SchedulerRunHistory', 'PendingSchedule', 'Event',
                     'Schedule', 'Employee']
    models = {k: current_app.config[k] for k in models_needed}

    data = request.get_json()
    run_id = data.get('run_id')

    if not run_id:
        return jsonify({'success': False, 'error': 'No run_id provided'}), 400

    run = db.session.query(models['SchedulerRunHistory']).get(run_id)
    if not run:
        return jsonify({'success': False, 'error': 'Run not found'}), 404

    # Get all non-failed pending schedules
    pending_schedules = db.session.query(models['PendingSchedule']).filter(
        models['PendingSchedule'].scheduler_run_id == run_id,
        models['PendingSchedule'].failure_reason.is_(None)
    ).all()

    current_app.logger.info(f"Found {len(pending_schedules)} pending schedules to approve for run {run_id}")

    api_submitted = 0
    api_failed = 0
    failed_details = []

    try:
        for pending in pending_schedules:
            if not pending.employee_id or not pending.schedule_datetime:
                continue

            # Get event and employee details
            event = db.session.query(models['Event']).filter_by(
                project_ref_num=pending.event_ref_num
            ).first()

            employee = db.session.query(models['Employee']).filter_by(
                id=pending.employee_id
            ).first()

            if not event or not employee:
                current_app.logger.warning(f"Missing data: event={event}, employee={employee} for pending {pending.id}")
                failed_details.append({
                    'event_ref_num': pending.event_ref_num,
                    'employee_id': pending.employee_id,
                    'reason': 'Event or employee not found'
                })
                pending.status = 'api_failed'
                pending.api_error_details = 'Event or employee not found in database'
                api_failed += 1
                continue

            # Calculate end datetime (start + estimated_time)
            start_datetime = pending.schedule_datetime
            # Use event's estimated_time, or fall back to the event type's default duration
            estimated_minutes = event.estimated_time or event.get_default_duration(event.event_type)
            end_datetime = start_datetime + timedelta(minutes=estimated_minutes)

            # CRITICAL VALIDATION: Ensure schedule is within event period
            # This prevents scheduling events outside their valid start/due date window
            if not (event.start_datetime <= start_datetime <= event.due_datetime):
                error_msg = (
                    f"Schedule datetime {start_datetime.strftime('%Y-%m-%d %H:%M')} is outside "
                    f"event period ({event.start_datetime.strftime('%Y-%m-%d')} to "
                    f"{event.due_datetime.strftime('%Y-%m-%d')})"
                )
                current_app.logger.error(
                    f"Validation failed for event {event.project_ref_num} ({event.project_name}): {error_msg}"
                )
                failed_details.append({
                    'event_ref_num': pending.event_ref_num,
                    'event_name': event.project_name,
                    'employee_name': employee.name,
                    'scheduled_time': start_datetime.isoformat(),
                    'event_period': f"{event.start_datetime.date()} to {event.due_datetime.date()}",
                    'reason': error_msg
                })
                pending.status = 'validation_failed'
                pending.api_error_details = error_msg
                api_failed += 1
                continue

            # Prepare data for Crossmark API
            # IMPORTANT: Use external_id (numeric API ID), NOT employee.id (US###### format)
            rep_id = str(employee.external_id) if employee.external_id else None

            mplan_id = str(event.external_id) if event.external_id else None
            location_id = str(event.location_mvid) if event.location_mvid else None

            current_app.logger.info(
                f"API field check for {event.project_name}: "
                f"rep_id={rep_id} (from {employee.id}), "
                f"mplan_id={mplan_id}, "
                f"location_id={location_id}"
            )

            # Validate required API fields
            if not rep_id:
                failed_details.append({
                    'event_ref_num': pending.event_ref_num,
                    'event_name': event.project_name,
                    'employee_name': employee.name,
                    'reason': f'Missing external_id for employee {employee.name} ({employee.id})'
                })
                pending.status = 'api_failed'
                pending.api_error_details = 'Missing employee external_id'
                api_failed += 1
                continue

            if not mplan_id:
                failed_details.append({
                    'event_ref_num': pending.event_ref_num,
                    'event_name': event.project_name,
                    'reason': 'Missing external_id for event'
                })
                pending.status = 'api_failed'
                pending.api_error_details = 'Missing event external_id'
                api_failed += 1
                continue

            if not location_id:
                failed_details.append({
                    'event_ref_num': pending.event_ref_num,
                    'event_name': event.project_name,
                    'reason': 'Missing location_mvid for event'
                })
                pending.status = 'api_failed'
                pending.api_error_details = 'Missing location_mvid'
                api_failed += 1
                continue

            # Submit to Crossmark API
            try:
                current_app.logger.info(
                    f"Submitting to Crossmark API: "
                    f"rep_id={rep_id}, mplan_id={mplan_id}, location_id={location_id}, "
                    f"start={start_datetime.isoformat()}, end={end_datetime.isoformat()}, "
                    f"event={event.project_name}, employee={employee.name}"
                )

                api_result = external_api.schedule_mplan_event(
                    rep_id=rep_id,
                    mplan_id=mplan_id,
                    location_id=location_id,
                    start_datetime=start_datetime,
                    end_datetime=end_datetime,
                    planning_override=True
                )

                if api_result.get('success'):
                    # Extract the scheduled event ID from the API response
                    # First try the direct field, then fall back to response_data
                    scheduled_event_id = api_result.get('schedule_event_id')

                    if not scheduled_event_id:
                        response_data = api_result.get('response_data', {})
                        if response_data:
                            scheduled_event_id = (
                                response_data.get('scheduleEventID') or
                                response_data.get('id') or
                                response_data.get('scheduledEventId') or
                                response_data.get('ID')
                            )

                    current_app.logger.info(f"Extracted scheduled_event_id: {scheduled_event_id}")

                    # API submission successful - create local schedule record
                    schedule = models['Schedule'](
                        event_ref_num=pending.event_ref_num,
                        employee_id=pending.employee_id,
                        schedule_datetime=pending.schedule_datetime,
                        external_id=str(scheduled_event_id) if scheduled_event_id else None,
                        last_synced=datetime.utcnow(),
                        sync_status='synced'
                    )
                    db.session.add(schedule)

                    # Mark event as scheduled
                    event.is_scheduled = True
                    event.condition = 'Scheduled'
                    event.sync_status = 'synced'
                    event.last_synced = datetime.utcnow()

                    # Update pending schedule status
                    pending.status = 'api_submitted'
                    pending.api_submitted_at = datetime.utcnow()
                    api_submitted += 1

                    current_app.logger.info(
                        f"Successfully scheduled event {event.project_ref_num} ({event.project_name}) "
                        f"to {employee.name} at {start_datetime}"
                    )

                    # AUTO-SCHEDULE SUPERVISOR EVENT if this is a Core event
                    if event.event_type == 'Core':
                        from routes.scheduling import auto_schedule_supervisor_event
                        scheduled_date = start_datetime.date()
                        supervisor_scheduled, supervisor_event_name = auto_schedule_supervisor_event(
                            db, models['Event'], models['Schedule'], models['Employee'],
                            event.project_ref_num,
                            scheduled_date,
                            pending.employee_id
                        )
                        if supervisor_scheduled:
                            current_app.logger.info(
                                f"Auto-scheduled supervisor event: {supervisor_event_name}"
                            )
                else:
                    # API submission failed
                    error_message = api_result.get('message', 'Unknown API error')
                    failed_details.append({
                        'event_ref_num': pending.event_ref_num,
                        'event_name': event.project_name,
                        'employee_name': employee.name,
                        'reason': error_message
                    })
                    pending.status = 'api_failed'
                    pending.api_error_details = error_message
                    api_failed += 1

                    current_app.logger.warning(
                        f"Failed to schedule event {event.project_ref_num} to Crossmark API: {error_message}"
                    )

            except Exception as api_error:
                # API call exception
                error_message = f"API exception: {str(api_error)}"
                failed_details.append({
                    'event_ref_num': pending.event_ref_num,
                    'event_name': event.project_name,
                    'employee_name': employee.name,
                    'reason': error_message
                })
                pending.status = 'api_failed'
                pending.api_error_details = error_message
                api_failed += 1

                current_app.logger.error(
                    f"Exception scheduling event {event.project_ref_num}: {str(api_error)}",
                    exc_info=True
                )

        # Mark run as approved
        run.approved_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Schedule approved: {api_submitted} submitted, {api_failed} failed',
            'api_submitted': api_submitted,
            'api_failed': api_failed,
            'failed_events': failed_details
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to approve schedule: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to approve schedule: {str(e)}'
        }), 500
@auto_scheduler_bp.route('/reject', methods=['POST'])
def reject_schedule():
    """Reject/discard ALL pending schedule proposals"""
    db = current_app.extensions['sqlalchemy']
    SchedulerRunHistory = current_app.config['SchedulerRunHistory']
    PendingSchedule = current_app.config['PendingSchedule']

    data = request.get_json() or {}
    reject_all = data.get('reject_all', True)  # Default to rejecting all

    try:
        if reject_all:
            # Get all pending runs (completed but not approved)
            pending_runs = db.session.query(SchedulerRunHistory).filter(
                SchedulerRunHistory.approved_at.is_(None),
                SchedulerRunHistory.status == 'completed'
            ).all()

            if not pending_runs:
                return jsonify({
                    'success': True,
                    'message': 'No pending proposals to reject'
                })

            # Delete all pending schedules for all pending runs
            for run in pending_runs:
                db.session.query(PendingSchedule).filter_by(
                    scheduler_run_id=run.id
                ).delete()

                # Mark run as rejected
                run.status = 'rejected'
                if not run.completed_at:
                    run.completed_at = datetime.utcnow()

            db.session.commit()

            return jsonify({
                'success': True,
                'message': f'{len(pending_runs)} schedule proposal(s) rejected and discarded'
            })
        else:
            # Reject specific run only
            run_id = data.get('run_id')
            if not run_id:
                return jsonify({'success': False, 'error': 'No run_id provided'}), 400

            run = db.session.query(SchedulerRunHistory).get(run_id)
            if not run:
                return jsonify({'success': False, 'error': 'Run not found'}), 404

            # Delete all pending schedules for this run
            db.session.query(PendingSchedule).filter_by(
                scheduler_run_id=run_id
            ).delete()

            # Mark run as rejected
            run.status = 'rejected'
            if not run.completed_at:
                run.completed_at = datetime.utcnow()

            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Schedule proposal rejected and discarded'
            })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to reject schedule: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to reject schedule: {str(e)}'
        }), 500


@auto_scheduler_bp.route('/api/dashboard-status', methods=['GET'])
def dashboard_status():
    """Check if there are pending scheduler runs for dashboard notification"""
    db = current_app.extensions['sqlalchemy']
    SchedulerRunHistory = current_app.config['SchedulerRunHistory']

    # Count runs that are completed but not approved and not rejected
    pending_count = db.session.query(func.count(SchedulerRunHistory.id)).filter(
        SchedulerRunHistory.approved_at.is_(None),
        SchedulerRunHistory.status == 'completed'
    ).scalar()

    return jsonify({
        'has_pending': pending_count > 0,
        'pending_count': pending_count
    })
