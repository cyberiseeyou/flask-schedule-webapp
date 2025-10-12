"""
Celery tasks for automated auditing
Scheduled background tasks for daily system health checks
"""
from celery import shared_task
from celery.utils.log import get_task_logger
from datetime import date, datetime

logger = get_task_logger(__name__)


@shared_task(name='tasks.run_daily_audit')
def run_daily_audit(target_date_str=None):
    """
    Run daily audit check

    This task runs automatically every morning at 6:00 AM (configured in Celery beat)
    and performs comprehensive system health checks.

    Args:
        target_date_str: Optional date string (YYYY-MM-DD). Defaults to today.

    Returns:
        Dict with audit results
    """
    from flask import current_app
    from services.daily_audit_checker import DailyAuditChecker

    try:
        # Parse target date
        if target_date_str:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        else:
            target_date = date.today()

        logger.info(f"Starting daily audit task for {target_date}")

        # Get database session and models
        db = current_app.extensions['sqlalchemy']
        models = current_app.config

        # Create audit checker
        checker = DailyAuditChecker(db.session, models)

        # Run audit
        audit_result = checker.run_daily_audit(target_date)

        # Send notifications if critical issues found
        if audit_result['critical_issues'] > 0:
            logger.warning(f"Critical issues found: {audit_result['critical_issues']}")
            _send_audit_notification(checker, audit_result)

        logger.info(f"Daily audit completed: {audit_result['total_issues']} issues found")

        return {
            'success': True,
            'date': audit_result['date'],
            'total_issues': audit_result['total_issues'],
            'critical_issues': audit_result['critical_issues'],
            'summary': audit_result['summary']
        }

    except Exception as e:
        logger.error(f"Daily audit task failed: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def _send_audit_notification(checker, audit_result):
    """Send audit notification based on settings"""
    try:
        from flask import current_app

        # Get notification settings
        AuditNotificationSettings = current_app.config.get('AuditNotificationSettings')
        if not AuditNotificationSettings:
            logger.warning("AuditNotificationSettings model not available")
            return

        db = current_app.extensions['sqlalchemy']
        settings = db.session.query(AuditNotificationSettings).filter_by(
            is_active=True
        ).first()

        if not settings:
            logger.info("No active notification settings found")
            return

        # Check if should notify based on issue severity
        should_notify = (
            (audit_result['critical_issues'] > 0 and settings.notify_on_critical) or
            (audit_result['warning_issues'] > 0 and settings.notify_on_warning) or
            (audit_result['info_issues'] > 0 and settings.notify_on_info)
        )

        if not should_notify:
            logger.info("Notification threshold not met")
            return

        # Get recipients
        if not settings.email_recipients:
            logger.warning("No email recipients configured")
            return

        recipients = [email.strip() for email in settings.email_recipients.split(',')]

        # Send notification
        checker.send_audit_notification(audit_result, recipients)

        # Update audit log
        AuditLog = current_app.config.get('AuditLog')
        if AuditLog:
            audit_log = db.session.query(AuditLog).filter_by(
                audit_date=datetime.strptime(audit_result['date'], '%Y-%m-%d').date()
            ).order_by(AuditLog.audit_timestamp.desc()).first()

            if audit_log:
                audit_log.notification_sent = True
                audit_log.notification_sent_at = datetime.utcnow()
                db.session.commit()

    except Exception as e:
        logger.error(f"Failed to send audit notification: {str(e)}", exc_info=True)


@shared_task(name='tasks.audit_event_import')
def audit_event_import():
    """
    Check if events were imported from MVRetail today

    This task runs after the expected import window (e.g., 8:00 AM)
    to verify new events were successfully imported.

    Returns:
        Dict with import status
    """
    from flask import current_app

    try:
        logger.info("Checking event import status")

        db = current_app.extensions['sqlalchemy']
        Event = current_app.config['Event']

        today = date.today()

        # Check for events synced today
        events_synced_today = db.session.query(Event).filter(
            db.func.date(Event.last_synced) == today
        ).count()

        # Check for events with pending sync status
        events_pending_sync = db.session.query(Event).filter(
            Event.sync_status == 'pending'
        ).count()

        # Check for events with failed sync status
        events_failed_sync = db.session.query(Event).filter(
            Event.sync_status == 'failed'
        ).count()

        logger.info(f"Import audit: {events_synced_today} synced today, "
                   f"{events_pending_sync} pending, {events_failed_sync} failed")

        return {
            'success': True,
            'date': today.isoformat(),
            'events_synced_today': events_synced_today,
            'events_pending_sync': events_pending_sync,
            'events_failed_sync': events_failed_sync
        }

    except Exception as e:
        logger.error(f"Event import audit failed: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(name='tasks.check_rotation_coverage')
def check_rotation_coverage(days_ahead=14):
    """
    Check rotation coverage for upcoming days

    Verifies that all upcoming days have Juicer and Primary Lead rotations assigned.

    Args:
        days_ahead: Number of days to check (default: 14 days / 2 weeks)

    Returns:
        Dict with coverage status
    """
    from flask import current_app
    from datetime import timedelta

    try:
        logger.info(f"Checking rotation coverage for next {days_ahead} days")

        db = current_app.extensions['sqlalchemy']
        RotationAssignment = current_app.config['RotationAssignment']

        today = date.today()
        gaps = []

        for i in range(days_ahead):
            check_date = today + timedelta(days=i)
            day_of_week = check_date.weekday()

            # Check Juicer rotation
            juicer_rotation = db.session.query(RotationAssignment).filter_by(
                day_of_week=day_of_week,
                rotation_type='juicer'
            ).first()

            if not juicer_rotation:
                gaps.append({
                    'date': check_date.isoformat(),
                    'day_name': check_date.strftime('%A'),
                    'rotation_type': 'Juicer',
                    'day_of_week': day_of_week
                })

            # Check Primary Lead rotation
            lead_rotation = db.session.query(RotationAssignment).filter_by(
                day_of_week=day_of_week,
                rotation_type='primary_lead'
            ).first()

            if not lead_rotation:
                gaps.append({
                    'date': check_date.isoformat(),
                    'day_name': check_date.strftime('%A'),
                    'rotation_type': 'Primary Lead',
                    'day_of_week': day_of_week
                })

        if gaps:
            logger.warning(f"Found {len(gaps)} rotation coverage gap(s)")
        else:
            logger.info(f"Rotation coverage complete for next {days_ahead} days")

        return {
            'success': True,
            'days_checked': days_ahead,
            'gaps_found': len(gaps),
            'gaps': gaps
        }

    except Exception as e:
        logger.error(f"Rotation coverage check failed: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(name='tasks.generate_weekly_audit_report')
def generate_weekly_audit_report():
    """
    Generate weekly audit summary report

    Runs every Monday morning to summarize the previous week's audit results.

    Returns:
        Dict with weekly summary
    """
    from flask import current_app
    from datetime import timedelta
    import json

    try:
        logger.info("Generating weekly audit report")

        db = current_app.extensions['sqlalchemy']
        AuditLog = current_app.config.get('AuditLog')

        if not AuditLog:
            logger.warning("AuditLog model not available")
            return {'success': False, 'error': 'AuditLog model not available'}

        # Get last 7 days of audit logs
        today = date.today()
        week_ago = today - timedelta(days=7)

        weekly_logs = db.session.query(AuditLog).filter(
            AuditLog.audit_date >= week_ago,
            AuditLog.audit_date < today
        ).order_by(AuditLog.audit_date.asc()).all()

        # Calculate weekly statistics
        total_issues = sum(log.total_issues for log in weekly_logs)
        total_critical = sum(log.critical_issues for log in weekly_logs)
        total_warnings = sum(log.warning_issues for log in weekly_logs)
        total_info = sum(log.info_issues for log in weekly_logs)

        # Calculate average health score (based on issue counts)
        avg_health_score = 100
        if weekly_logs:
            avg_issues_per_day = total_issues / len(weekly_logs)
            avg_health_score = max(0, 100 - (avg_issues_per_day * 5))  # Rough calculation

        # Identify recurring issues (issues that appear multiple days)
        issue_types = {}
        for log in weekly_logs:
            if log.details_json:
                try:
                    issues = json.loads(log.details_json)
                    for issue in issues:
                        issue_type = issue.get('type')
                        if issue_type:
                            if issue_type not in issue_types:
                                issue_types[issue_type] = 0
                            issue_types[issue_type] += 1
                except:
                    pass

        recurring_issues = [
            {'type': issue_type, 'occurrences': count}
            for issue_type, count in issue_types.items()
            if count >= 3  # Appeared 3+ days
        ]

        weekly_summary = {
            'success': True,
            'week_start': week_ago.isoformat(),
            'week_end': (today - timedelta(days=1)).isoformat(),
            'days_audited': len(weekly_logs),
            'total_issues': total_issues,
            'total_critical': total_critical,
            'total_warnings': total_warnings,
            'total_info': total_info,
            'avg_health_score': int(avg_health_score),
            'recurring_issues': recurring_issues
        }

        logger.info(f"Weekly audit report generated: {total_issues} total issues, "
                   f"avg health score {int(avg_health_score)}")

        # TODO: Send weekly report email to management
        # _send_weekly_report_email(weekly_summary)

        return weekly_summary

    except Exception as e:
        logger.error(f"Weekly audit report failed: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }
