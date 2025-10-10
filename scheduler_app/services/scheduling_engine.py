"""
Scheduling Engine - Core Auto-Scheduler Logic
Orchestrates the automatic scheduling process
"""
from datetime import datetime, timedelta, time, date
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from flask import current_app

from services.rotation_manager import RotationManager
from services.constraint_validator import ConstraintValidator
from services.conflict_resolver import ConflictResolver
from services.validation_types import SchedulingDecision


class SchedulingEngine:
    """
    Core auto-scheduler orchestrator

    Process:
    1. Filter events within 3-week window
    2. Sort by priority (due date, event type)
    3. Phase 1: Schedule rotation-based events (Juicer, Digital)
    4. Phase 2: Schedule Core events (Leads first, then Specialists)
    5. Phase 3: Auto-pair Supervisor events with Core events
    6. Generate PendingSchedule records for user approval
    """

    # Event scheduling window in days
    SCHEDULING_WINDOW_DAYS = 3  # 3 days ahead

    # Event type priority order (lower = higher priority)
    EVENT_TYPE_PRIORITY = {
        'Juicer': 1,
        'Digital Setup': 2,
        'Digital Refresh': 3,
        'Freeosk': 4,
        'Digital Teardown': 5,
        'Core': 6,
        'Supervisor': 7,
        'Digitals': 8,
        'Other': 9
    }

    # Default scheduling times by event type
    DEFAULT_TIMES = {
        'Juicer Production': time(9, 0),     # 9 AM - JUICER-PRODUCTION-SPCLTY
        'Juicer Survey': time(17, 0),        # 5 PM - Juicer Survey
        'Juicer': time(9, 0),                # 9 AM - Default for other Juicer events
        'Digital Setup': time(9, 15),        # 9:15 AM (first slot)
        'Digital Refresh': time(9, 15),      # 9:15 AM (first slot)
        'Freeosk': time(9, 0),               # 9 AM
        'Digital Teardown': time(17, 0),     # 5 PM (first slot)
        'Core': time(9, 45),                 # 9:45 AM (for Primary Leads)
        'Supervisor': time(12, 0),           # Noon
        'Other': time(10, 0)
    }

    # Time slots for Core events (rotating)
    CORE_TIME_SLOTS = [
        time(9, 45),   # Primary Lead slot
        time(10, 30),
        time(11, 0),
        time(11, 30)
    ]

    # Time slots for Digital Setup/Refresh (15 min intervals starting at 9:15)
    DIGITAL_TIME_SLOTS = [
        time(9, 15),
        time(9, 30),
        time(9, 45),
        time(10, 0),
        time(10, 15),
        time(10, 30),
        time(10, 45),
        time(11, 0),
        time(11, 15),
        time(11, 30),
        time(11, 45),
        time(12, 0),
    ]

    # Time slots for Digital Teardown (15 min intervals starting at 5:00 PM)
    TEARDOWN_TIME_SLOTS = [
        time(17, 0),   # 5:00 PM
        time(17, 15),
        time(17, 30),
        time(17, 45),
        time(18, 0),   # 6:00 PM
        time(18, 15),
        time(18, 30),
        time(18, 45),
    ]

    def __init__(self, db_session: Session, models: dict):
        """
        Initialize SchedulingEngine

        Args:
            db_session: SQLAlchemy database session
            models: Dictionary of model classes from app.config
        """
        self.db = db_session
        self.models = models

        self.Event = models['Event']
        self.Schedule = models['Schedule']
        self.Employee = models['Employee']
        self.SchedulerRunHistory = models['SchedulerRunHistory']
        self.PendingSchedule = models['PendingSchedule']
        self.EmployeeTimeOff = models['EmployeeTimeOff']
        self.EmployeeWeeklyAvailability = models['EmployeeWeeklyAvailability']

        # Initialize service dependencies
        self.rotation_manager = RotationManager(db_session, models)
        self.validator = ConstraintValidator(db_session, models)
        self.conflict_resolver = ConflictResolver(db_session, models)

        # Track time slot rotation per day
        self.daily_time_slot_index = {}  # {date_str: slot_index} for Core events
        self.digital_time_slot_index = {}  # {date_str: slot_index} for Digital Setup/Refresh
        self.teardown_time_slot_index = {}  # {date_str: slot_index} for Digital Teardown

    def run_auto_scheduler(self, run_type: str = 'manual') -> object:
        """
        Main entry point for auto-scheduler

        Scheduling Waves:
        Wave 1: Juicer events → Juicer Baristas (rotation-based, try next day if time off)
        Wave 2: Core events → 3 Subwaves:
                2.1: Lead Event Specialists (priority - fill their available days first)
                2.2: Juicer Baristas (when not juicing that day)
                2.3: Event Specialists
        Wave 3: Supervisor events → Club Supervisor
        Wave 4: Freeosk & Digitals → Primary Lead → Other Leads → Club Supervisor
        Wave 5: Other events → Club Supervisor → ANY Lead Event Specialist

        Args:
            run_type: 'automatic' or 'manual'

        Returns:
            SchedulerRunHistory object
        """
        # Create run history record
        run = self.SchedulerRunHistory(
            run_type=run_type,
            started_at=datetime.utcnow(),
            status='running'
        )
        self.db.add(run)
        self.db.flush()

        # Set current run ID in validator to check pending schedules
        self.validator.set_current_run(run.id)

        try:
            # Get events to schedule
            events = self._get_unscheduled_events()
            run.total_events_processed = len(events)

            # Sort by priority (due date first, then event type)
            events = self._sort_events_by_priority(events)

            # Wave 1: Juicer events (highest priority - scheduled first)
            self._schedule_juicer_events_wave1(run, events)

            # Wave 2: Core events (3 subwaves: Leads → Juicers → Specialists)
            self._schedule_core_events_wave2(run, events)

            # Wave 3: Supervisor events
            self._schedule_supervisor_events_wave3(run, events)

            # Wave 4: Freeosk and Digital events
            self._schedule_freeosk_digital_events_wave4(run, events)

            # Wave 5: Other events
            self._schedule_other_events_wave5(run, events)

            # Mark run as completed
            run.completed_at = datetime.utcnow()
            run.status = 'completed'
            self.db.commit()

            return run

        except Exception as e:
            run.status = 'failed'
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            self.db.commit()
            raise

    def _get_unscheduled_events(self) -> List[object]:
        """
        Get ALL unscheduled/unstaffed events

        Returns all unscheduled events regardless of start date.
        The scheduling logic will ensure the earliest assignment date is 3 days from today.

        Returns:
            List of Event objects that are unscheduled/unstaffed
        """
        events = self.db.query(self.Event).filter(
            and_(
                self.Event.is_scheduled == False,  # Only unscheduled events
                self.Event.condition == 'Unstaffed'  # Only unstaffed events
            )
        ).all()

        return events

    def _sort_events_by_priority(self, events: List[object]) -> List[object]:
        """
        Sort events by priority (due date first, then event type)

        Args:
            events: List of Event objects

        Returns:
            Sorted list of Event objects
        """
        def priority_key(event):
            # Primary sort: due date (earlier = higher priority)
            days_until_due = (event.due_datetime - datetime.now()).days

            # Secondary sort: event type priority
            type_priority = self.EVENT_TYPE_PRIORITY.get(event.event_type, 99)

            return (days_until_due, type_priority)

        return sorted(events, key=priority_key)

    def _get_earliest_schedule_date(self, event: object) -> datetime:
        """
        Get the earliest date this event can be scheduled

        The earliest date is the later of:
        1. Event's start_datetime
        2. Today + SCHEDULING_WINDOW_DAYS (3 days from today)

        This ensures the auto-scheduler doesn't schedule events within the 3-day buffer.

        Args:
            event: Event object

        Returns:
            datetime: Earliest date this event can be scheduled
        """
        today = datetime.now().date()
        earliest_allowed = today + timedelta(days=self.SCHEDULING_WINDOW_DAYS)
        earliest_allowed_datetime = datetime.combine(earliest_allowed, time(0, 0))

        # Return the later of the two dates
        if event.start_datetime >= earliest_allowed_datetime:
            return event.start_datetime
        else:
            return earliest_allowed_datetime

    def _schedule_juicer_events_wave1(self, run: object, events: List[object]) -> None:
        """
        Wave 1: Schedule Juicer events to Juicer Baristas (rotation-based)

        Logic:
        - Assign to rotation Juicer for the event's start date
        - If rotation Juicer has time off, try next day
        - Continue trying next days until due date or Juicer available
        - Respects Juicer availability constraints
        """
        juicer_events = [e for e in events if e.event_type == 'Juicer' and not e.is_scheduled]
        for event in juicer_events:
            self._schedule_juicer_event_wave1(run, event)

    def _schedule_freeosk_digital_events_wave4(self, run: object, events: List[object]) -> None:
        """
        Wave 4: Schedule Freeosk and Digital events

        Priority: Primary Lead → Other Leads → Club Supervisor
        """
        for event in events:
            if event.is_scheduled:
                continue

            # Handle Digitals events (detect subtype from name)
            if event.event_type == 'Digitals':
                event_name_upper = event.project_name.upper()

                # Digital Teardown goes to Secondary Lead (with Club Supervisor fallback)
                if 'TEARDOWN' in event_name_upper:
                    self._schedule_secondary_lead_event(run, event)
                # Digital Setup/Refresh goes to Primary Lead (with Club Supervisor fallback)
                elif 'SETUP' in event_name_upper or 'REFRESH' in event_name_upper:
                    self._schedule_primary_lead_event(run, event)
                else:
                    # Unknown Digital subtype - try Primary Lead as default
                    self._schedule_primary_lead_event(run, event)

            # Handle Freeosk events
            elif event.event_type == 'Freeosk':
                self._schedule_primary_lead_event(run, event)

    def _schedule_other_events_wave5(self, run: object, events: List[object]) -> None:
        """
        Wave 5: Schedule Other events

        Priority: Club Supervisor first → ANY Lead Event Specialist fallback
        """
        for event in events:
            if event.is_scheduled:
                continue

            if event.event_type == 'Other':
                self._schedule_other_event_wave5(run, event)

    def _schedule_other_event_wave5(self, run: object, event: object) -> None:
        """
        Wave 5: Schedule Other events

        Priority: Club Supervisor (at noon) → ANY Lead Event Specialist fallback
        """
        # Use event's start date for scheduling
        current_date = self._get_earliest_schedule_date(event)

        # Schedule at noon
        schedule_time = time(12, 0)
        schedule_datetime = datetime.combine(current_date.date(), schedule_time)
        target_date = schedule_datetime.date()
        day_of_week = target_date.weekday()
        day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        day_column = day_names[day_of_week]

        # Try Club Supervisor first
        club_supervisor = self.db.query(self.Employee).filter_by(
            job_title='Club Supervisor',
            is_active=True
        ).first()

        if club_supervisor:
            # Check basic availability (time off and weekly availability only)
            # Time conflicts are ignored for Club Supervisor

            # Check time off
            time_off = self.db.query(self.EmployeeTimeOff).filter(
                self.EmployeeTimeOff.employee_id == club_supervisor.id,
                self.EmployeeTimeOff.start_date <= target_date,
                self.EmployeeTimeOff.end_date >= target_date
            ).first()

            if not time_off:
                # Check weekly availability
                weekly_avail = self.db.query(self.EmployeeWeeklyAvailability).filter_by(
                    employee_id=club_supervisor.id
                ).first()

                is_available = True
                if weekly_avail:
                    is_available = getattr(weekly_avail, day_column, True)

                if is_available:
                    # Schedule to Club Supervisor (no time conflict checks)
                    self._create_pending_schedule(run, event, club_supervisor, schedule_datetime, False, None, None)
                    run.events_scheduled += 1
                    current_app.logger.info(f"Wave 5: Scheduled Other event {event.project_ref_num} to Club Supervisor")
                    return

        # Fallback to ANY Lead Event Specialist if Club Supervisor unavailable
        leads = self.db.query(self.Employee).filter(
            self.Employee.job_title == 'Lead Event Specialist',
            self.Employee.is_active == True
        ).all()

        for lead in leads:
            # Check time off
            time_off = self.db.query(self.EmployeeTimeOff).filter(
                self.EmployeeTimeOff.employee_id == lead.id,
                self.EmployeeTimeOff.start_date <= target_date,
                self.EmployeeTimeOff.end_date >= target_date
            ).first()

            if not time_off:
                # Check weekly availability
                weekly_avail = self.db.query(self.EmployeeWeeklyAvailability).filter_by(
                    employee_id=lead.id
                ).first()

                is_available = True
                if weekly_avail:
                    is_available = getattr(weekly_avail, day_column, True)

                if is_available:
                    # Schedule to this Lead (no time conflict checks for Other events)
                    self._create_pending_schedule(run, event, lead, schedule_datetime, False, None, None)
                    run.events_scheduled += 1
                    current_app.logger.info(f"Wave 5: Scheduled Other event {event.project_ref_num} to Lead Event Specialist {lead.name}")
                    return

        # Failed to schedule
        self._create_failed_pending_schedule(run, event, "No Club Supervisor or Lead Event Specialist available")
        run.events_failed += 1

    def _get_juicer_time(self, event: object) -> time:
        """
        Determine the scheduling time for a Juicer event based on its name

        Returns:
            - 9:00 AM for JUICER-PRODUCTION-SPCLTY events
            - 5:00 PM for Juicer Survey events
            - 9:00 AM for other Juicer events (default)
        """
        event_name_upper = event.project_name.upper()

        if 'JUICER-PRODUCTION' in event_name_upper or 'PRODUCTION-SPCLTY' in event_name_upper:
            return self.DEFAULT_TIMES['Juicer Production']
        elif 'JUICER SURVEY' in event_name_upper or 'SURVEY' in event_name_upper:
            return self.DEFAULT_TIMES['Juicer Survey']
        else:
            return self.DEFAULT_TIMES['Juicer']

    def _schedule_juicer_event_wave1(self, run: object, event: object) -> None:
        """
        Wave 1: Schedule a Juicer event to the rotation-assigned Juicer Barista

        Logic:
        - Try rotation Juicer for event start date
        - If Juicer has time off or unavailable, try next day
        - Continue until due date
        - No bumping needed since Juicers are Wave 1 (first)

        Scheduling times:
        - JUICER-PRODUCTION-SPCLTY: 9:00 AM
        - Juicer Survey: 5:00 PM
        - Other Juicer events: 9:00 AM
        """
        # Determine the appropriate time for this Juicer event
        juicer_time = self._get_juicer_time(event)

        # Try each day from earliest allowed date to due date
        current_date = self._get_earliest_schedule_date(event)
        while current_date < event.due_datetime:
            employee = self.rotation_manager.get_rotation_employee(current_date, 'juicer')
            if not employee:
                # No Juicer assigned for this day in rotation
                current_date += timedelta(days=1)
                continue

            schedule_datetime = datetime.combine(current_date.date(), juicer_time)
            validation = self.validator.validate_assignment(event, employee, schedule_datetime)

            if validation.is_valid:
                # Juicer is available - schedule it
                self._create_pending_schedule(run, event, employee, schedule_datetime, False, None, None)
                run.events_scheduled += 1
                current_app.logger.info(
                    f"Wave 1: Scheduled Juicer event {event.project_ref_num} to {employee.name} on {current_date.date()}"
                )
                return

            # Juicer not available (time off, already scheduled, etc.) - try next day
            current_date += timedelta(days=1)

        # Failed to schedule
        self._create_failed_pending_schedule(run, event, "No available Juicer rotation employee before due date")
        run.events_failed += 1

    def _schedule_core_events_wave2(self, run: object, events: List[object]) -> None:
        """
        Wave 2: Schedule Core events in 3 subwaves

        Subwave 2.1: Lead Event Specialists (highest priority)
                    - Fill their available days first, even if event could start earlier
                    - If Lead has available day with no events, prioritize assigning to them
        Subwave 2.2: Juicer Baristas (when not juicing that day)
        Subwave 2.3: Event Specialists

        Time slots rotate: 9:45 AM, 10:30 AM, 11:00 AM, 11:30 AM
        """
        core_events = [e for e in events if e.event_type == 'Core' and not e.is_scheduled]

        # Subwave 2.1: Prioritize Lead Event Specialists
        for event in core_events:
            if event.is_scheduled:
                continue
            if self._try_schedule_core_to_lead(run, event):
                event.is_scheduled = True  # Mark to skip in later subwaves

        # Subwave 2.2: Try Juicer Baristas (when not juicing)
        for event in core_events:
            if event.is_scheduled:
                continue
            if self._try_schedule_core_to_juicer(run, event):
                event.is_scheduled = True  # Mark to skip in later subwaves

        # Subwave 2.3: Try Event Specialists
        for event in core_events:
            if event.is_scheduled:
                continue
            self._try_schedule_core_to_specialist(run, event)

    def _try_schedule_core_to_lead(self, run: object, event: object) -> bool:
        """
        Subwave 2.1: Try to schedule Core event to a Lead Event Specialist

        Priority logic: Leads get events on their available days even if event could start earlier.
        This ensures Leads' schedules are filled first.
        """
        # Get all Lead Event Specialists
        leads = self.db.query(self.Employee).filter(
            self.Employee.job_title == 'Lead Event Specialist',
            self.Employee.is_active == True
        ).all()

        current_date = self._get_earliest_schedule_date(event)
        while current_date < event.due_datetime:
            time_slot = self._get_next_time_slot(current_date)
            schedule_datetime = datetime.combine(current_date.date(), time_slot)

            for lead in leads:
                validation = self.validator.validate_assignment(event, lead, schedule_datetime)
                if validation.is_valid:
                    self._create_pending_schedule(run, event, lead, schedule_datetime, False, None, None)
                    run.events_scheduled += 1
                    current_app.logger.info(
                        f"Wave 2.1: Scheduled Core event {event.project_ref_num} to Lead {lead.name}"
                    )
                    return True

            current_date += timedelta(days=1)

        return False

    def _try_schedule_core_to_juicer(self, run: object, event: object) -> bool:
        """
        Subwave 2.2: Try to schedule Core event to a Juicer Barista (when not juicing)
        """
        # Get all Juicer Baristas
        juicers = self.db.query(self.Employee).filter(
            self.Employee.job_title == 'Juicer Barista',
            self.Employee.is_active == True
        ).all()

        current_date = self._get_earliest_schedule_date(event)
        while current_date < event.due_datetime:
            time_slot = self._get_next_time_slot(current_date)
            schedule_datetime = datetime.combine(current_date.date(), time_slot)

            for juicer in juicers:
                # Check if this Juicer has a Juicer event scheduled for this day
                juicer_event_today = self.db.query(self.PendingSchedule).join(
                    self.Event, self.PendingSchedule.event_ref_num == self.Event.project_ref_num
                ).filter(
                    self.PendingSchedule.scheduler_run_id == run.id,
                    self.PendingSchedule.employee_id == juicer.id,
                    func.date(self.PendingSchedule.schedule_datetime) == schedule_datetime.date(),
                    self.Event.event_type == 'Juicer'
                ).first()

                # Only schedule if Juicer is NOT juicing this day
                if not juicer_event_today:
                    validation = self.validator.validate_assignment(event, juicer, schedule_datetime)
                    if validation.is_valid:
                        self._create_pending_schedule(run, event, juicer, schedule_datetime, False, None, None)
                        run.events_scheduled += 1
                        current_app.logger.info(
                            f"Wave 2.2: Scheduled Core event {event.project_ref_num} to Juicer {juicer.name}"
                        )
                        return True

            current_date += timedelta(days=1)

        return False

    def _try_schedule_core_to_specialist(self, run: object, event: object) -> None:
        """
        Subwave 2.3: Try to schedule Core event to an Event Specialist
        """
        # Get all Event Specialists
        specialists = self.db.query(self.Employee).filter(
            self.Employee.job_title == 'Event Specialist',
            self.Employee.is_active == True
        ).all()

        current_date = self._get_earliest_schedule_date(event)
        while current_date < event.due_datetime:
            time_slot = self._get_next_time_slot(current_date)
            schedule_datetime = datetime.combine(current_date.date(), time_slot)

            for specialist in specialists:
                validation = self.validator.validate_assignment(event, specialist, schedule_datetime)
                if validation.is_valid:
                    self._create_pending_schedule(run, event, specialist, schedule_datetime, False, None, None)
                    run.events_scheduled += 1
                    current_app.logger.info(
                        f"Wave 2.3: Scheduled Core event {event.project_ref_num} to Specialist {specialist.name}"
                    )
                    return

            current_date += timedelta(days=1)

        # Failed to schedule
        self._create_failed_pending_schedule(run, event, "No available employees before due date")
        run.events_failed += 1

    def _get_next_digital_time_slot(self, date_obj: datetime) -> time:
        """Get next 15-min interval time slot for Digital Setup/Refresh"""
        date_str = date_obj.date().isoformat()
        if date_str not in self.digital_time_slot_index:
            self.digital_time_slot_index[date_str] = 0

        slot_index = self.digital_time_slot_index[date_str]
        time_slot = self.DIGITAL_TIME_SLOTS[slot_index % len(self.DIGITAL_TIME_SLOTS)]
        self.digital_time_slot_index[date_str] += 1
        return time_slot

    def _schedule_primary_lead_event(self, run: object, event: object) -> None:
        """
        Schedule Digital Setup/Refresh or Freeosk event to Primary Lead

        Wave 4 Priority: Primary Lead → Other Leads → Club Supervisor (fallback)
        IMPORTANT: Freeosk events MUST be scheduled on their start date
        """
        # Use event's start date - Freeosk/Digital events don't move to other days
        schedule_date = self._get_earliest_schedule_date(event)

        # Determine time slot based on event name
        event_name_upper = event.project_name.upper()
        if event.event_type == 'Digitals' and ('SETUP' in event_name_upper or 'REFRESH' in event_name_upper):
            schedule_time = self._get_next_digital_time_slot(schedule_date)
        else:
            schedule_time = self.DEFAULT_TIMES.get('Freeosk', time(9, 0))

        schedule_datetime = datetime.combine(schedule_date.date(), schedule_time)
        target_date = schedule_datetime.date()
        day_of_week = target_date.weekday()
        day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        day_column = day_names[day_of_week]

        # Try Primary Lead first (only check time off and weekly availability)
        primary_lead = self.rotation_manager.get_rotation_employee(schedule_date, 'primary_lead')
        if primary_lead:
            # Check time off
            time_off = self.db.query(self.EmployeeTimeOff).filter(
                self.EmployeeTimeOff.employee_id == primary_lead.id,
                self.EmployeeTimeOff.start_date <= target_date,
                self.EmployeeTimeOff.end_date >= target_date
            ).first()

            if not time_off:
                # Check weekly availability
                weekly_avail = self.db.query(self.EmployeeWeeklyAvailability).filter_by(
                    employee_id=primary_lead.id
                ).first()

                is_available = True
                if weekly_avail:
                    is_available = getattr(weekly_avail, day_column, True)

                if is_available:
                    self._create_pending_schedule(run, event, primary_lead, schedule_datetime, False, None, None)
                    run.events_scheduled += 1
                    current_app.logger.info(
                        f"Wave 4: Scheduled {event.event_type} event {event.project_ref_num} to Primary Lead {primary_lead.name}"
                    )
                    return

        # Try other Lead Event Specialists (only check time off and weekly availability)
        other_leads = self.db.query(self.Employee).filter(
            self.Employee.job_title == 'Lead Event Specialist',
            self.Employee.is_active == True
        ).all()

        for lead in other_leads:
            if primary_lead and lead.id == primary_lead.id:
                continue  # Skip primary lead (already tried)

            # Check time off
            time_off = self.db.query(self.EmployeeTimeOff).filter(
                self.EmployeeTimeOff.employee_id == lead.id,
                self.EmployeeTimeOff.start_date <= target_date,
                self.EmployeeTimeOff.end_date >= target_date
            ).first()

            if not time_off:
                # Check weekly availability
                weekly_avail = self.db.query(self.EmployeeWeeklyAvailability).filter_by(
                    employee_id=lead.id
                ).first()

                is_available = True
                if weekly_avail:
                    is_available = getattr(weekly_avail, day_column, True)

                if is_available:
                    self._create_pending_schedule(run, event, lead, schedule_datetime, False, None, None)
                    run.events_scheduled += 1
                    current_app.logger.info(
                        f"Wave 4: Scheduled {event.event_type} event {event.project_ref_num} to Lead {lead.name}"
                    )
                    return

        # Try Club Supervisor (only check time off and weekly availability, no time conflicts)
        club_supervisor = self.db.query(self.Employee).filter_by(
            job_title='Club Supervisor',
            is_active=True
        ).first()

        if club_supervisor:
            # Check time off
            time_off = self.db.query(self.EmployeeTimeOff).filter(
                self.EmployeeTimeOff.employee_id == club_supervisor.id,
                self.EmployeeTimeOff.start_date <= target_date,
                self.EmployeeTimeOff.end_date >= target_date
            ).first()

            if not time_off:
                # Check weekly availability
                weekly_avail = self.db.query(self.EmployeeWeeklyAvailability).filter_by(
                    employee_id=club_supervisor.id
                ).first()

                is_available = True
                if weekly_avail:
                    is_available = getattr(weekly_avail, day_column, True)

                if is_available:
                    self._create_pending_schedule(run, event, club_supervisor, schedule_datetime, False, None, None)
                    run.events_scheduled += 1
                    current_app.logger.info(
                        f"Wave 4: Scheduled {event.event_type} event {event.project_ref_num} to Club Supervisor (no leads available)"
                    )
                    return
                else:
                    current_app.logger.warning(
                        f"Wave 4: Club Supervisor NOT available on {day_column} for event {event.project_ref_num}"
                    )
            else:
                current_app.logger.warning(
                    f"Wave 4: Club Supervisor has time off on {target_date} for event {event.project_ref_num}"
                )

        # This should NEVER happen - log detailed info for debugging
        current_app.logger.error(
            f"Wave 4: CRITICAL - No Lead or Club Supervisor available for {event.event_type} event {event.project_ref_num} on {target_date} ({day_column})"
        )
        self._create_failed_pending_schedule(
            run,
            event,
            f"No Lead or Club Supervisor available on {day_column} - This should not happen!"
        )
        run.events_failed += 1

    def _get_next_teardown_time_slot(self, date_obj: datetime) -> time:
        """Get next 15-min interval time slot for Digital Teardown starting at 5 PM"""
        date_str = date_obj.date().isoformat()
        if date_str not in self.teardown_time_slot_index:
            self.teardown_time_slot_index[date_str] = 0

        slot_index = self.teardown_time_slot_index[date_str]
        time_slot = self.TEARDOWN_TIME_SLOTS[slot_index % len(self.TEARDOWN_TIME_SLOTS)]
        self.teardown_time_slot_index[date_str] += 1
        return time_slot

    def _schedule_secondary_lead_event(self, run: object, event: object) -> None:
        """
        Schedule Digital Teardown to Secondary Lead at rotating 15-min intervals from 5 PM

        Wave 4 Priority: Secondary Lead → Club Supervisor (fallback)
        IMPORTANT: Digital events MUST be scheduled on their start date
        """
        # Use event's start date - Digital events don't move to other days
        schedule_date = self._get_earliest_schedule_date(event)
        schedule_time = self._get_next_teardown_time_slot(schedule_date)
        schedule_datetime = datetime.combine(schedule_date.date(), schedule_time)
        target_date = schedule_datetime.date()
        day_of_week = target_date.weekday()
        day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        day_column = day_names[day_of_week]

        # Try Secondary Lead first (only check time off and weekly availability)
        secondary_lead = self.rotation_manager.get_secondary_lead(schedule_date)
        if secondary_lead:
            # Check time off
            time_off = self.db.query(self.EmployeeTimeOff).filter(
                self.EmployeeTimeOff.employee_id == secondary_lead.id,
                self.EmployeeTimeOff.start_date <= target_date,
                self.EmployeeTimeOff.end_date >= target_date
            ).first()

            if not time_off:
                # Check weekly availability
                weekly_avail = self.db.query(self.EmployeeWeeklyAvailability).filter_by(
                    employee_id=secondary_lead.id
                ).first()

                is_available = True
                if weekly_avail:
                    is_available = getattr(weekly_avail, day_column, True)

                if is_available:
                    self._create_pending_schedule(run, event, secondary_lead, schedule_datetime, False, None, None)
                    run.events_scheduled += 1
                    current_app.logger.info(
                        f"Wave 4: Scheduled Digital Teardown {event.project_ref_num} to Secondary Lead {secondary_lead.name}"
                    )
                    return

        # Try Club Supervisor (only check time off and weekly availability, no time conflicts)
        club_supervisor = self.db.query(self.Employee).filter_by(
            job_title='Club Supervisor',
            is_active=True
        ).first()

        if club_supervisor:
            # Check time off
            time_off = self.db.query(self.EmployeeTimeOff).filter(
                self.EmployeeTimeOff.employee_id == club_supervisor.id,
                self.EmployeeTimeOff.start_date <= target_date,
                self.EmployeeTimeOff.end_date >= target_date
            ).first()

            if not time_off:
                # Check weekly availability
                weekly_avail = self.db.query(self.EmployeeWeeklyAvailability).filter_by(
                    employee_id=club_supervisor.id
                ).first()

                is_available = True
                if weekly_avail:
                    is_available = getattr(weekly_avail, day_column, True)

                if is_available:
                    self._create_pending_schedule(run, event, club_supervisor, schedule_datetime, False, None, None)
                    run.events_scheduled += 1
                    current_app.logger.info(
                        f"Wave 4: Scheduled Digital Teardown {event.project_ref_num} to Club Supervisor (no secondary lead available)"
                    )
                    return
                else:
                    current_app.logger.warning(
                        f"Wave 4: Club Supervisor NOT available on {day_column} for Digital Teardown {event.project_ref_num}"
                    )
            else:
                current_app.logger.warning(
                    f"Wave 4: Club Supervisor has time off on {target_date} for Digital Teardown {event.project_ref_num}"
                )

        # This should NEVER happen - log detailed info for debugging
        current_app.logger.error(
            f"Wave 4: CRITICAL - No Secondary Lead or Club Supervisor available for Digital Teardown {event.project_ref_num} on {target_date} ({day_column})"
        )
        self._create_failed_pending_schedule(
            run,
            event,
            f"No Secondary Lead or Club Supervisor available on {day_column} - This should not happen!"
        )
        run.events_failed += 1

    def _schedule_core_events(self, run: object, events: List[object]) -> None:
        """
        Phase 2: Schedule Core events

        Priority: Lead Event Specialists first, then Event Specialists
        """
        core_events = [e for e in events if e.event_type == 'Core' and not e.is_scheduled]

        for event in core_events:
            self._schedule_core_event(run, event)

    def _get_next_time_slot(self, date_obj: datetime) -> time:
        """
        Get the next available time slot for a date
        Rotates through: 9:45, 10:30, 11:00, 11:30, then back to 9:45
        """
        date_str = date_obj.date().isoformat()
        if date_str not in self.daily_time_slot_index:
            self.daily_time_slot_index[date_str] = 0

        slot_index = self.daily_time_slot_index[date_str]
        time_slot = self.CORE_TIME_SLOTS[slot_index % len(self.CORE_TIME_SLOTS)]

        # Increment for next event on this date
        self.daily_time_slot_index[date_str] += 1

        return time_slot

    def _schedule_core_event(self, run: object, event: object) -> None:
        """
        Schedule a single Core event

        Logic:
        - Primary Leads get 9:45 AM slot
        - Everyone else rotates through 10:30, 11:00, 11:30, then back to 9:45
        """
        current_date = self._get_earliest_schedule_date(event)
        while current_date < event.due_datetime:
            # Check if Primary Lead is available at 9:45
            primary_lead_id = self.rotation_manager.get_rotation_employee_id(current_date, 'primary_lead')
            if primary_lead_id:
                primary_lead = self.db.query(self.Employee).get(primary_lead_id)
                schedule_datetime_945 = datetime.combine(current_date.date(), time(9, 45))

                validation = self.validator.validate_assignment(event, primary_lead, schedule_datetime_945)
                if validation.is_valid:
                    # Check if Primary Lead doesn't already have an event at 9:45
                    existing = self.db.query(self.Schedule).filter(
                        self.Schedule.employee_id == primary_lead_id,
                        self.Schedule.schedule_datetime == schedule_datetime_945
                    ).first()

                    if not existing:
                        self._create_pending_schedule(run, event, primary_lead, schedule_datetime_945, False, None, None)
                        run.events_scheduled += 1
                        return

            # Primary Lead not available or already has 9:45 slot - use rotating time slots
            time_slot = self._get_next_time_slot(current_date)
            schedule_datetime = datetime.combine(current_date.date(), time_slot)

            # Try Leads first
            leads = self._get_available_leads(event, schedule_datetime)
            for lead in leads:
                validation = self.validator.validate_assignment(event, lead, schedule_datetime)
                if validation.is_valid:
                    self._create_pending_schedule(run, event, lead, schedule_datetime, False, None, None)
                    run.events_scheduled += 1
                    return

            # Try Event Specialists
            specialists = self._get_available_specialists(event, schedule_datetime)
            for specialist in specialists:
                validation = self.validator.validate_assignment(event, specialist, schedule_datetime)
                if validation.is_valid:
                    self._create_pending_schedule(run, event, specialist, schedule_datetime, False, None, None)
                    run.events_scheduled += 1
                    return

            # No one available - try conflict resolution
            swap = self._try_resolve_conflict(event, schedule_datetime)
            if swap:
                self._create_pending_schedule(run, event, None, schedule_datetime, True, swap.low_priority_event_ref, swap.reason)
                run.events_requiring_swaps += 1
                return

            current_date += timedelta(days=1)

        self._create_failed_pending_schedule(run, event, "No available employees or swap candidates")
        run.events_failed += 1

    def _extract_event_number(self, event_name: str) -> str:
        """Extract first 6 digits from event name"""
        import re
        match = re.search(r'\d{6}', event_name)
        return match.group(0) if match else None

    def _schedule_supervisor_events_wave3(self, run: object, events: List[object]) -> None:
        """
        Phase 3: Auto-pair Supervisor events with their Core events

        Links Supervisor events to Core events based on first 6 digits of event name.
        Supervisor events scheduled to:
        1. Club Supervisor at Noon (priority #1, can have unlimited overlaps)
        2. Primary Lead Event Specialist (if Club Supervisor unavailable that day)

        Note: Time conflicts are IGNORED for Supervisor events - multiple can be at noon
        """
        supervisor_events = [e for e in events if e.event_type == 'Supervisor' and not e.is_scheduled]

        for supervisor_event in supervisor_events:
            # Extract event number from Supervisor event name
            supervisor_event_number = self._extract_event_number(supervisor_event.project_name)

            if not supervisor_event_number:
                self._create_failed_pending_schedule(run, supervisor_event, "Cannot extract event number from event name")
                run.events_failed += 1
                continue

            # Find Core event with matching event number
            core_event = None
            core_events = self.db.query(self.Event).filter_by(event_type='Core').all()
            for ce in core_events:
                ce_number = self._extract_event_number(ce.project_name)
                if ce_number == supervisor_event_number:
                    core_event = ce
                    break

            if not core_event:
                self._create_failed_pending_schedule(run, supervisor_event, f"No Core event found with event number {supervisor_event_number}")
                run.events_failed += 1
                continue

            # Get Core event's scheduled date
            core_schedule = self.db.query(self.Schedule).filter_by(
                event_ref_num=core_event.project_ref_num
            ).first()

            if not core_schedule:
                # Check if Core event has a pending schedule (from Wave 2)
                core_pending = self.db.query(self.PendingSchedule).filter_by(
                    event_ref_num=core_event.project_ref_num,
                    scheduler_run_id=run.id
                ).first()

                if core_pending and core_pending.schedule_datetime:
                    # Core event was successfully scheduled in Wave 2 - use that date
                    supervisor_datetime = datetime.combine(core_pending.schedule_datetime.date(), time(12, 0))
                elif core_pending and core_pending.failure_reason:
                    # Core event FAILED to schedule - Supervisor event cannot be scheduled
                    self._create_failed_pending_schedule(
                        run,
                        supervisor_event,
                        f"Core event failed to schedule: {core_pending.failure_reason}"
                    )
                    run.events_failed += 1
                    continue
                else:
                    # This shouldn't happen with wave system, but handle gracefully
                    self._create_failed_pending_schedule(run, supervisor_event, "Core event could not be scheduled")
                    run.events_failed += 1
                    continue
            else:
                # Use the existing schedule
                supervisor_datetime = datetime.combine(core_schedule.schedule_datetime.date(), time(12, 0))

            # Get the target date for availability checks
            target_date = supervisor_datetime.date()

            # Try Club Supervisor first (ignore time conflicts, only check day availability)
            club_supervisor = self.db.query(self.Employee).filter_by(
                job_title='Club Supervisor',
                is_active=True
            ).first()

            if club_supervisor:
                # Only check time-off and weekly availability, NOT schedule conflicts
                from services.validation_types import ValidationResult
                day_available = True

                # Check time off
                time_off = self.db.query(self.EmployeeTimeOff).filter(
                    self.EmployeeTimeOff.employee_id == club_supervisor.id,
                    self.EmployeeTimeOff.start_date <= target_date,
                    self.EmployeeTimeOff.end_date >= target_date
                ).first()

                if time_off:
                    day_available = False

                # Check weekly availability
                if day_available:
                    day_of_week = supervisor_datetime.weekday()  # 0=Monday, 6=Sunday
                    day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                    day_column = day_names[day_of_week]

                    weekly_avail = self.db.query(self.EmployeeWeeklyAvailability).filter_by(
                        employee_id=club_supervisor.id
                    ).first()

                    if weekly_avail:
                        is_available = getattr(weekly_avail, day_column, True)
                        if not is_available:
                            day_available = False

                if day_available:
                    self._create_pending_schedule(run, supervisor_event, club_supervisor, supervisor_datetime, False, None, None)
                    run.events_scheduled += 1
                    continue

            # Fall back to Primary Lead Event Specialist (from rotation)
            primary_lead_id = self.rotation_manager.get_rotation_employee_id(supervisor_datetime, 'primary_lead')
            if primary_lead_id:
                primary_lead = self.db.query(self.Employee).get(primary_lead_id)
                if primary_lead:
                    # Check day availability (same as above)
                    day_available = True

                    # Check time off
                    time_off = self.db.query(self.EmployeeTimeOff).filter(
                        self.EmployeeTimeOff.employee_id == primary_lead.id,
                        self.EmployeeTimeOff.start_date <= target_date,
                        self.EmployeeTimeOff.end_date >= target_date
                    ).first()

                    if time_off:
                        day_available = False

                    # Check weekly availability
                    if day_available:
                        day_of_week = supervisor_datetime.weekday()
                        day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                        day_column = day_names[day_of_week]

                        weekly_avail = self.db.query(self.EmployeeWeeklyAvailability).filter_by(
                            employee_id=primary_lead.id
                        ).first()

                        if weekly_avail:
                            is_available = getattr(weekly_avail, day_column, True)
                            if not is_available:
                                day_available = False

                    if day_available:
                        self._create_pending_schedule(run, supervisor_event, primary_lead, supervisor_datetime, False, None, None)
                        run.events_scheduled += 1
                        continue

            self._create_failed_pending_schedule(run, supervisor_event, "Club Supervisor and Primary Lead unavailable")
            run.events_failed += 1

    def _get_available_leads(self, event: object, schedule_datetime: datetime) -> List[object]:
        """
        Get available Lead Event Specialists for an event

        Note: Club Supervisor is excluded from Core events but can do other event types
        """
        # For Core events, only get Lead Event Specialists (exclude Club Supervisor)
        if event.event_type == 'Core':
            leads = self.db.query(self.Employee).filter(
                self.Employee.job_title == 'Lead Event Specialist',
                self.Employee.is_active == True
            ).all()
        else:
            # For other event types, include Club Supervisor
            leads = self.db.query(self.Employee).filter(
                self.Employee.job_title.in_(['Lead Event Specialist', 'Club Supervisor']),
                self.Employee.is_active == True
            ).all()

        available = []
        for lead in leads:
            validation = self.validator.validate_assignment(event, lead, schedule_datetime)
            if validation.is_valid:
                available.append(lead)

        return available

    def _get_available_specialists(self, event: object, schedule_datetime: datetime) -> List[object]:
        """Get available Event Specialists for an event"""
        specialists = self.db.query(self.Employee).filter_by(
            job_title='Event Specialist'
        ).all()

        available = []
        for specialist in specialists:
            validation = self.validator.validate_assignment(event, specialist, schedule_datetime)
            if validation.is_valid:
                available.append(specialist)

        return available

    def _try_resolve_conflict(self, event: object, schedule_datetime: datetime) -> Optional[object]:
        """
        Try to resolve a scheduling conflict by finding an event to bump

        Args:
            event: Event to schedule
            schedule_datetime: Desired datetime

        Returns:
            SwapProposal or None
        """
        # Find potential employees
        all_employees = self._get_available_leads(event, schedule_datetime)
        all_employees.extend(self._get_available_specialists(event, schedule_datetime))

        for employee in all_employees:
            swap = self.conflict_resolver.resolve_conflict(event, schedule_datetime, employee.id)
            if swap:
                return swap

        return None

    def _create_pending_schedule(self, run: object, event: object, employee: Optional[object],
                                 schedule_datetime: datetime, is_swap: bool,
                                 bumped_event_ref: Optional[int], swap_reason: Optional[str]) -> None:
        """Create a PendingSchedule record"""
        pending = self.PendingSchedule(
            scheduler_run_id=run.id,
            event_ref_num=event.project_ref_num,
            employee_id=employee.id if employee else None,
            schedule_datetime=schedule_datetime,
            schedule_time=schedule_datetime.time(),
            status='proposed',
            is_swap=is_swap,
            bumped_event_ref_num=bumped_event_ref,
            swap_reason=swap_reason
        )
        self.db.add(pending)
        self.db.flush()

    def _create_failed_pending_schedule(self, run: object, event: object, failure_reason: str) -> None:
        """Create a PendingSchedule record for a failed scheduling attempt"""
        pending = self.PendingSchedule(
            scheduler_run_id=run.id,
            event_ref_num=event.project_ref_num,
            employee_id=None,
            schedule_datetime=None,
            schedule_time=None,
            status='proposed',
            failure_reason=failure_reason
        )
        self.db.add(pending)
        self.db.flush()
