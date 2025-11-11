"""
Schedule Verification Service

Verifies daily schedules for issues before the day starts.
Implements 8 validation rules to catch scheduling problems proactively.
"""
from datetime import datetime, timedelta, time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from collections import Counter


@dataclass
class VerificationIssue:
    """Represents a single verification issue found in the schedule"""
    severity: str  # 'critical', 'warning', 'info'
    rule_name: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'severity': self.severity,
            'rule_name': self.rule_name,
            'message': self.message,
            'details': self.details
        }


@dataclass
class VerificationResult:
    """Results of schedule verification"""
    status: str  # 'pass', 'warning', 'fail'
    issues: List[VerificationIssue] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'status': self.status,
            'issues': [issue.to_dict() for issue in self.issues],
            'summary': self.summary
        }


class ScheduleVerificationService:
    """
    Service to verify daily schedules for issues.

    Implements 8 validation rules:
    1. Juicer event verification
    2. Core events per person limit
    3. Supervisor event assignment
    4. Supervisor event time
    5. Shift balance across 4 timeslots
    6. Lead Event Specialist coverage (opening/closing)
    7. Employee work limits (availability, time-off, max 6 days/week)
    8. Event date range validation
    """

    MAX_WORK_DAYS_PER_WEEK = 6

    @classmethod
    def _get_core_timeslots(cls):
        """Get Core event time slots from database settings"""
        from app.services.event_time_settings import get_core_slots

        try:
            slots = get_core_slots()
            # Convert to HH:MM:SS format for comparison
            return [f"{slot['start'].hour:02d}:{slot['start'].minute:02d}:00" for slot in slots]
        except Exception:
            # Fallback to hard-coded defaults
            return ['09:45:00', '10:30:00', '11:00:00', '11:30:00']

    @classmethod
    def _get_supervisor_time(cls):
        """Get Supervisor event time from database settings"""
        from app.services.event_time_settings import get_supervisor_times

        try:
            times = get_supervisor_times()
            # Convert to HH:MM:SS format for comparison
            return f"{times['start'].hour:02d}:{times['start'].minute:02d}:00"
        except Exception:
            # Fallback to hard-coded default
            return '12:00:00'

    def __init__(self, db_session, models):
        """
        Initialize verification service

        Args:
            db_session: SQLAlchemy database session
            models: Dictionary of model classes
        """
        self.db = db_session
        self.Employee = models['Employee']
        self.Event = models['Event']
        self.Schedule = models['Schedule']
        self.EmployeeAvailability = models.get('EmployeeAvailability')
        self.EmployeeWeeklyAvailability = models.get('EmployeeWeeklyAvailability')
        self.EmployeeTimeOff = models['EmployeeTimeOff']
        self.EmployeeAttendance = models.get('EmployeeAttendance')

        # Load time settings from database
        self.CORE_TIMESLOTS = self._get_core_timeslots()
        self.SUPERVISOR_TIME = self._get_supervisor_time()

    def verify_schedule(self, verify_date: datetime.date) -> VerificationResult:
        """
        Run all verification rules for a specific date

        Args:
            verify_date: Date to verify (datetime.date object)

        Returns:
            VerificationResult with all issues found
        """
        issues = []

        # Run all verification rules
        issues.extend(self._check_juicer_events(verify_date))
        issues.extend(self._check_core_event_limit(verify_date))
        issues.extend(self._check_supervisor_assignments(verify_date))
        issues.extend(self._check_supervisor_times(verify_date))
        issues.extend(self._check_shift_balance(verify_date))
        issues.extend(self._check_lead_coverage(verify_date))
        issues.extend(self._check_employee_work_limits(verify_date))
        issues.extend(self._check_event_date_ranges(verify_date))

        # Determine overall status
        critical_count = sum(1 for issue in issues if issue.severity == 'critical')
        warning_count = sum(1 for issue in issues if issue.severity == 'warning')

        if critical_count > 0:
            status = 'fail'
        elif warning_count > 0:
            status = 'warning'
        else:
            status = 'pass'

        # Build summary
        summary = {
            'date': verify_date.isoformat(),
            'total_issues': len(issues),
            'critical_issues': critical_count,
            'warnings': warning_count,
            'total_events': self._count_events(verify_date),
            'total_employees': self._count_employees(verify_date)
        }

        return VerificationResult(status=status, issues=issues, summary=summary)

    def _check_juicer_events(self, verify_date: datetime.date) -> List[VerificationIssue]:
        """
        Rule 1: Verify Juicer events are assigned to qualified employees

        Juicer events require Club Supervisor or Juicer Barista
        """
        issues = []

        # Get all Juicer events scheduled for this date
        juicer_schedules = self.db.query(
            self.Schedule, self.Event, self.Employee
        ).join(
            self.Event, self.Schedule.event_ref_num == self.Event.project_ref_num
        ).join(
            self.Employee, self.Schedule.employee_id == self.Employee.id
        ).filter(
            self.db.func.date(self.Schedule.schedule_datetime) == verify_date,
            self.Event.event_type == 'Juicer'
        ).all()

        for schedule, event, employee in juicer_schedules:
            # Check if employee can work Juicer events
            if employee.job_title not in ['Club Supervisor', 'Juicer Barista']:
                issues.append(VerificationIssue(
                    severity='critical',
                    rule_name='Juicer Event Assignment',
                    message=f"Juicer event '{event.project_name}' is assigned to {employee.name} ({employee.job_title}), who is not qualified for Juicer events.",
                    details={
                        'employee_id': employee.id,
                        'employee_name': employee.name,
                        'employee_job_title': employee.job_title,
                        'event_id': event.id,
                        'event_name': event.project_name,
                        'schedule_id': schedule.id,
                        'required_titles': ['Club Supervisor', 'Juicer Barista']
                    }
                ))

        return issues

    def _check_core_event_limit(self, verify_date: datetime.date) -> List[VerificationIssue]:
        """
        Rule 2: Verify each employee has maximum 1 Core event per day
        """
        issues = []

        # Get Core event counts per employee for this date
        core_counts = self.db.query(
            self.Employee.id,
            self.Employee.name,
            self.db.func.count(self.Schedule.id).label('core_count')
        ).join(
            self.Schedule, self.Employee.id == self.Schedule.employee_id
        ).join(
            self.Event, self.Schedule.event_ref_num == self.Event.project_ref_num
        ).filter(
            self.db.func.date(self.Schedule.schedule_datetime) == verify_date,
            self.Event.event_type == 'Core'
        ).group_by(
            self.Employee.id, self.Employee.name
        ).having(
            self.db.func.count(self.Schedule.id) > 1
        ).all()

        for employee_id, employee_name, core_count in core_counts:
            issues.append(VerificationIssue(
                severity='critical',
                rule_name='Core Event Limit',
                message=f"{employee_name} has {core_count} Core events scheduled. Employees can only work 1 Core event per day.",
                details={
                    'employee_id': employee_id,
                    'employee_name': employee_name,
                    'core_event_count': core_count
                }
            ))

        return issues

    def _check_supervisor_assignments(self, verify_date: datetime.date) -> List[VerificationIssue]:
        """
        Rule 3: Verify Supervisor events are assigned to Club Supervisor or Lead Event Specialist
        """
        issues = []

        # Get all Supervisor events for this date
        supervisor_schedules = self.db.query(
            self.Schedule, self.Event, self.Employee
        ).join(
            self.Event, self.Schedule.event_ref_num == self.Event.project_ref_num
        ).join(
            self.Employee, self.Schedule.employee_id == self.Employee.id
        ).filter(
            self.db.func.date(self.Schedule.schedule_datetime) == verify_date,
            self.Event.event_type == 'Supervisor'
        ).all()

        for schedule, event, employee in supervisor_schedules:
            # Check if employee is Club Supervisor or Lead Event Specialist
            if employee.job_title not in ['Club Supervisor', 'Lead Event Specialist']:
                issues.append(VerificationIssue(
                    severity='warning',
                    rule_name='Supervisor Event Assignment',
                    message=f"Supervisor event '{event.project_name}' is assigned to {employee.name} ({employee.job_title}). Should be assigned to Club Supervisor or Lead Event Specialist.",
                    details={
                        'employee_id': employee.id,
                        'employee_name': employee.name,
                        'employee_job_title': employee.job_title,
                        'event_id': event.id,
                        'event_name': event.project_name,
                        'schedule_id': schedule.id,
                        'required_titles': ['Club Supervisor', 'Lead Event Specialist']
                    }
                ))

        return issues

    def _check_supervisor_times(self, verify_date: datetime.date) -> List[VerificationIssue]:
        """
        Rule 4: Verify all Supervisor events are scheduled at 12:00 noon
        """
        issues = []

        # Get all Supervisor events for this date
        supervisor_schedules = self.db.query(
            self.Schedule, self.Event, self.Employee
        ).join(
            self.Event, self.Schedule.event_ref_num == self.Event.project_ref_num
        ).join(
            self.Employee, self.Schedule.employee_id == self.Employee.id
        ).filter(
            self.db.func.date(self.Schedule.schedule_datetime) == verify_date,
            self.Event.event_type == 'Supervisor'
        ).all()

        for schedule, event, employee in supervisor_schedules:
            scheduled_time = schedule.schedule_datetime.time()
            expected_time = time(12, 0)  # 12:00 PM

            if scheduled_time != expected_time:
                issues.append(VerificationIssue(
                    severity='warning',
                    rule_name='Supervisor Event Time',
                    message=f"Supervisor event '{event.project_name}' for {employee.name} is scheduled at {scheduled_time.strftime('%I:%M %p')}. Should be at 12:00 PM.",
                    details={
                        'employee_id': employee.id,
                        'employee_name': employee.name,
                        'event_id': event.id,
                        'event_name': event.project_name,
                        'schedule_id': schedule.id,
                        'scheduled_time': scheduled_time.strftime('%H:%M:%S'),
                        'expected_time': '12:00:00'
                    }
                ))

        return issues

    def _check_shift_balance(self, verify_date: datetime.date) -> List[VerificationIssue]:
        """
        Rule 5: Verify Core events are balanced across 4 shifts

        Rule: No shift should have 3+ events while another shift has 0 events
        """
        issues = []

        # Get Core event counts per timeslot
        shift_counts = {}
        for timeslot in self.CORE_TIMESLOTS:
            count = self.db.query(self.Schedule).join(
                self.Event, self.Schedule.event_ref_num == self.Event.project_ref_num
            ).filter(
                self.db.func.date(self.Schedule.schedule_datetime) == verify_date,
                self.db.func.time(self.Schedule.schedule_datetime) == timeslot,
                self.Event.event_type == 'Core'
            ).count()
            shift_counts[timeslot] = count

        # Check for imbalance: any shift with 3+ events while another has 0
        max_count = max(shift_counts.values())
        min_count = min(shift_counts.values())

        if max_count >= 3 and min_count == 0:
            # Find shifts with max and min
            max_shifts = [slot for slot, count in shift_counts.items() if count == max_count]
            min_shifts = [slot for slot, count in shift_counts.items() if count == min_count]

            issues.append(VerificationIssue(
                severity='warning',
                rule_name='Shift Balance',
                message=f"Core events are imbalanced across shifts. {self._format_time(max_shifts[0])} has {max_count} events while {self._format_time(min_shifts[0])} has 0 events.",
                details={
                    'shift_counts': {self._format_time(k): v for k, v in shift_counts.items()},
                    'overloaded_shifts': [self._format_time(s) for s in max_shifts],
                    'empty_shifts': [self._format_time(s) for s in min_shifts]
                }
            ))

        return issues

    def _check_lead_coverage(self, verify_date: datetime.date) -> List[VerificationIssue]:
        """
        Rule 6: Verify opening and closing Lead Event Specialist coverage

        If more than 1 Lead Event Specialist scheduled:
        - Check if there's an opening Lead (earliest Core time)
        - Check if there's a closing Lead (latest Core time)
        - Suggest shift swaps with Event Specialists if needed
        """
        issues = []

        # Get all Lead Event Specialists with Core events on this date
        lead_schedules = self.db.query(
            self.Schedule, self.Event, self.Employee
        ).join(
            self.Event, self.Schedule.event_ref_num == self.Event.project_ref_num
        ).join(
            self.Employee, self.Schedule.employee_id == self.Employee.id
        ).filter(
            self.db.func.date(self.Schedule.schedule_datetime) == verify_date,
            self.Event.event_type == 'Core',
            self.Employee.job_title == 'Lead Event Specialist'
        ).order_by(
            self.Schedule.schedule_datetime
        ).all()

        # Only check if there are 2+ Leads scheduled
        if len(lead_schedules) < 2:
            return issues

        # Get all Core event times for the day
        all_core_times = self.db.query(
            self.Schedule.schedule_datetime
        ).join(
            self.Event, self.Schedule.event_ref_num == self.Event.project_ref_num
        ).filter(
            self.db.func.date(self.Schedule.schedule_datetime) == verify_date,
            self.Event.event_type == 'Core'
        ).order_by(
            self.Schedule.schedule_datetime
        ).all()

        if not all_core_times:
            return issues

        earliest_time = all_core_times[0][0].time()
        latest_time = all_core_times[-1][0].time()

        # Get Lead times
        lead_times = [schedule.schedule_datetime.time() for schedule, _, _ in lead_schedules]

        # Check opening Lead
        has_opening_lead = earliest_time in lead_times

        # Check closing Lead
        has_closing_lead = latest_time in lead_times

        if not has_opening_lead:
            # Find Event Specialists at opening time to suggest swap
            opening_specialists = self._find_shift_swap_candidates(
                verify_date, earliest_time, 'Lead Event Specialist'
            )

            issues.append(VerificationIssue(
                severity='warning',
                rule_name='Lead Coverage - Opening',
                message=f"No Lead Event Specialist at opening shift ({self._format_time_obj(earliest_time)}). Consider swapping a Lead's shift with an Event Specialist.",
                details={
                    'missing_shift': self._format_time_obj(earliest_time),
                    'coverage_type': 'opening',
                    'swap_suggestions': opening_specialists
                }
            ))

        if not has_closing_lead:
            # Find Event Specialists at closing time to suggest swap
            closing_specialists = self._find_shift_swap_candidates(
                verify_date, latest_time, 'Lead Event Specialist'
            )

            issues.append(VerificationIssue(
                severity='warning',
                rule_name='Lead Coverage - Closing',
                message=f"No Lead Event Specialist at closing shift ({self._format_time_obj(latest_time)}). Consider swapping a Lead's shift with an Event Specialist.",
                details={
                    'missing_shift': self._format_time_obj(latest_time),
                    'coverage_type': 'closing',
                    'swap_suggestions': closing_specialists
                }
            ))

        return issues

    def _find_shift_swap_candidates(
        self,
        verify_date: datetime.date,
        target_time: time,
        target_job_title: str
    ) -> List[Dict[str, Any]]:
        """
        Find potential shift swap candidates

        Looks for:
        1. Event Specialists at target_time (who could swap with a Lead at different time)
        2. Leads at different times (who could swap to target_time)
        """
        candidates = []

        # Get Event Specialists at target time
        specialists_at_target = self.db.query(
            self.Schedule, self.Event, self.Employee
        ).join(
            self.Event, self.Schedule.event_ref_num == self.Event.project_ref_num
        ).join(
            self.Employee, self.Schedule.employee_id == self.Employee.id
        ).filter(
            self.db.func.date(self.Schedule.schedule_datetime) == verify_date,
            self.db.func.time(self.Schedule.schedule_datetime) == target_time,
            self.Event.event_type == 'Core',
            self.Employee.job_title == 'Event Specialist'
        ).all()

        # Get Leads at different times
        leads_at_other_times = self.db.query(
            self.Schedule, self.Event, self.Employee
        ).join(
            self.Event, self.Schedule.event_ref_num == self.Event.project_ref_num
        ).join(
            self.Employee, self.Schedule.employee_id == self.Employee.id
        ).filter(
            self.db.func.date(self.Schedule.schedule_datetime) == verify_date,
            self.db.func.time(self.Schedule.schedule_datetime) != target_time,
            self.Event.event_type == 'Core',
            self.Employee.job_title == target_job_title
        ).all()

        # Build swap suggestions
        for spec_sched, spec_event, specialist in specialists_at_target:
            for lead_sched, lead_event, lead in leads_at_other_times:
                candidates.append({
                    'swap_type': 'shift_time',
                    'suggestion': f"Swap {lead.name}'s shift time ({self._format_time_obj(lead_sched.schedule_datetime.time())}) with {specialist.name}'s shift time ({self._format_time_obj(spec_sched.schedule_datetime.time())})",
                    'lead_employee': {
                        'id': lead.id,
                        'name': lead.name,
                        'current_time': self._format_time_obj(lead_sched.schedule_datetime.time()),
                        'schedule_id': lead_sched.id
                    },
                    'specialist_employee': {
                        'id': specialist.id,
                        'name': specialist.name,
                        'current_time': self._format_time_obj(spec_sched.schedule_datetime.time()),
                        'schedule_id': spec_sched.id
                    }
                })

        return candidates

    def _check_employee_work_limits(self, verify_date: datetime.date) -> List[VerificationIssue]:
        """
        Rule 7: Check employee work limits

        - Verify availability
        - Check time-off requests
        - Ensure max 6 days worked per week (Sunday-Saturday)
        """
        issues = []

        # Get all employees scheduled for this date
        scheduled_employees = self.db.query(
            self.Employee
        ).join(
            self.Schedule, self.Employee.id == self.Schedule.employee_id
        ).filter(
            self.db.func.date(self.Schedule.schedule_datetime) == verify_date
        ).distinct().all()

        for employee in scheduled_employees:
            # Check 1: Availability
            availability_issue = self._check_employee_availability(employee, verify_date)
            if availability_issue:
                issues.append(availability_issue)

            # Check 2: Time-off
            time_off_issue = self._check_employee_time_off(employee, verify_date)
            if time_off_issue:
                issues.append(time_off_issue)

            # Check 3: Max work days (6 per week, Sunday-Saturday)
            work_days_issue = self._check_employee_work_days(employee, verify_date)
            if work_days_issue:
                issues.append(work_days_issue)

        return issues

    def _check_employee_availability(
        self,
        employee,
        verify_date: datetime.date
    ) -> Optional[VerificationIssue]:
        """Check if employee is available on this date"""

        # Check specific date availability
        if self.EmployeeAvailability:
            specific_avail = self.db.query(self.EmployeeAvailability).filter(
                self.EmployeeAvailability.employee_id == employee.id,
                self.EmployeeAvailability.date == verify_date
            ).first()

            if specific_avail and not specific_avail.is_available:
                return VerificationIssue(
                    severity='warning',
                    rule_name='Employee Availability',
                    message=f"{employee.name} is marked as unavailable on {verify_date}. Reason: {specific_avail.reason or 'Not specified'}",
                    details={
                        'employee_id': employee.id,
                        'employee_name': employee.name,
                        'date': verify_date.isoformat(),
                        'reason': specific_avail.reason
                    }
                )

        # Check weekly availability
        if self.EmployeeWeeklyAvailability:
            day_of_week = verify_date.weekday()  # 0=Monday, 6=Sunday
            day_columns = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            day_column = day_columns[day_of_week]

            weekly_avail = self.db.query(self.EmployeeWeeklyAvailability).filter(
                self.EmployeeWeeklyAvailability.employee_id == employee.id
            ).first()

            if weekly_avail:
                is_available = getattr(weekly_avail, day_column)
                if not is_available:
                    return VerificationIssue(
                        severity='warning',
                        rule_name='Employee Weekly Availability',
                        message=f"{employee.name} is not available on {day_column.capitalize()}s according to their weekly availability pattern.",
                        details={
                            'employee_id': employee.id,
                            'employee_name': employee.name,
                            'day_of_week': day_column,
                            'date': verify_date.isoformat()
                        }
                    )

        return None

    def _check_employee_time_off(
        self,
        employee,
        verify_date: datetime.date
    ) -> Optional[VerificationIssue]:
        """Check if employee has time-off on this date"""

        time_off = self.db.query(self.EmployeeTimeOff).filter(
            self.EmployeeTimeOff.employee_id == employee.id,
            self.EmployeeTimeOff.start_date <= verify_date,
            self.EmployeeTimeOff.end_date >= verify_date
        ).first()

        if time_off:
            return VerificationIssue(
                severity='warning',
                rule_name='Employee Time Off',
                message=f"{employee.name} has time-off scheduled from {time_off.start_date} to {time_off.end_date}. Reason: {time_off.reason or 'Not specified'}",
                details={
                    'employee_id': employee.id,
                    'employee_name': employee.name,
                    'time_off_start': time_off.start_date.isoformat(),
                    'time_off_end': time_off.end_date.isoformat(),
                    'reason': time_off.reason
                }
            )

        return None

    def _check_employee_work_days(
        self,
        employee,
        verify_date: datetime.date
    ) -> Optional[VerificationIssue]:
        """
        Check if employee is working more than 6 days in the week

        Week definition: Sunday through Saturday containing verify_date
        """
        # Find the Sunday of the week containing verify_date
        days_since_sunday = (verify_date.weekday() + 1) % 7  # Monday=0, Sunday=6 -> 1,2,3,4,5,6,0
        week_start = verify_date - timedelta(days=days_since_sunday)
        week_end = week_start + timedelta(days=6)

        # Count distinct days worked in this week
        days_worked = self.db.query(
            self.db.func.date(self.Schedule.schedule_datetime)
        ).filter(
            self.Schedule.employee_id == employee.id,
            self.db.func.date(self.Schedule.schedule_datetime) >= week_start,
            self.db.func.date(self.Schedule.schedule_datetime) <= week_end
        ).distinct().count()

        if days_worked > self.MAX_WORK_DAYS_PER_WEEK:
            return VerificationIssue(
                severity='warning',
                rule_name='Employee Work Days Limit',
                message=f"{employee.name} is scheduled for {days_worked} days in the week of {week_start} to {week_end}. Maximum is {self.MAX_WORK_DAYS_PER_WEEK} days per week.",
                details={
                    'employee_id': employee.id,
                    'employee_name': employee.name,
                    'days_worked': days_worked,
                    'max_days': self.MAX_WORK_DAYS_PER_WEEK,
                    'week_start': week_start.isoformat(),
                    'week_end': week_end.isoformat()
                }
            )

        return None

    def _check_event_date_ranges(self, verify_date: datetime.date) -> List[VerificationIssue]:
        """
        Rule 8: Verify event date ranges

        - Check if scheduled events are within their start_datetime and due_datetime
        - Check for unscheduled events that should be done on this date
        """
        issues = []

        # Check 1: Scheduled events outside their date range
        out_of_range = self.db.query(
            self.Schedule, self.Event, self.Employee
        ).join(
            self.Event, self.Schedule.event_ref_num == self.Event.project_ref_num
        ).join(
            self.Employee, self.Schedule.employee_id == self.Employee.id
        ).filter(
            self.db.func.date(self.Schedule.schedule_datetime) == verify_date,
            self.db.or_(
                self.db.func.date(self.Schedule.schedule_datetime) < self.db.func.date(self.Event.start_datetime),
                self.db.func.date(self.Schedule.schedule_datetime) > self.db.func.date(self.Event.due_datetime)
            )
        ).all()

        for schedule, event, employee in out_of_range:
            issues.append(VerificationIssue(
                severity='critical',
                rule_name='Event Date Range',
                message=f"Event '{event.project_name}' is scheduled on {verify_date} but must be done between {event.start_datetime.date()} and {event.due_datetime.date()}.",
                details={
                    'event_id': event.id,
                    'event_name': event.project_name,
                    'schedule_id': schedule.id,
                    'employee_id': employee.id,
                    'employee_name': employee.name,
                    'scheduled_date': verify_date.isoformat(),
                    'event_start_date': event.start_datetime.date().isoformat(),
                    'event_due_date': event.due_datetime.date().isoformat()
                }
            ))

        # Check 2: Unscheduled events that should be done today
        unscheduled_today = self.db.query(self.Event).filter(
            self.Event.is_scheduled == False,
            self.db.func.date(self.Event.start_datetime) <= verify_date,
            self.db.func.date(self.Event.due_datetime) >= verify_date
        ).all()

        for event in unscheduled_today:
            issues.append(VerificationIssue(
                severity='critical',
                rule_name='Unscheduled Required Event',
                message=f"Event '{event.project_name}' (Type: {event.event_type}) is not scheduled but must be completed between {event.start_datetime.date()} and {event.due_datetime.date()}.",
                details={
                    'event_id': event.id,
                    'event_name': event.project_name,
                    'event_type': event.event_type,
                    'event_start_date': event.start_datetime.date().isoformat(),
                    'event_due_date': event.due_datetime.date().isoformat(),
                    'verify_date': verify_date.isoformat()
                }
            ))

        return issues

    # Utility methods

    def _count_events(self, verify_date: datetime.date) -> int:
        """Count total events scheduled for the date"""
        return self.db.query(self.Schedule).filter(
            self.db.func.date(self.Schedule.schedule_datetime) == verify_date
        ).count()

    def _count_employees(self, verify_date: datetime.date) -> int:
        """Count total employees scheduled for the date"""
        return self.db.query(self.Schedule.employee_id).filter(
            self.db.func.date(self.Schedule.schedule_datetime) == verify_date
        ).distinct().count()

    def _format_time(self, time_str: str) -> str:
        """Format time string (HH:MM:SS) to readable format (HH:MM AM/PM)"""
        try:
            t = datetime.strptime(time_str, '%H:%M:%S').time()
            return self._format_time_obj(t)
        except:
            return time_str

    def _format_time_obj(self, time_obj: time) -> str:
        """Format time object to readable format (HH:MM AM/PM)"""
        hour = time_obj.hour
        minute = time_obj.minute
        ampm = 'AM' if hour < 12 else 'PM'
        display_hour = hour if hour <= 12 else hour - 12
        display_hour = 12 if display_hour == 0 else display_hour
        return f"{display_hour}:{minute:02d} {ampm}"
