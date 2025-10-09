"""
Scheduling Engine - Core Auto-Scheduler Logic
Orchestrates the automatic scheduling process
"""
from datetime import datetime, timedelta, time, date
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
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

            # Sort by priority
            events = self._sort_events_by_priority(events)

            # Phase 1: Core events (scheduled first so Juicers can bump them later)
            self._schedule_core_events(run, events)

            # Phase 2: Juicer events (PRIORITY - can bump Core events)
            self._schedule_juicer_events_only(run, events)

            # Phase 3: Other rotation-based events (Digital, Freeosk)
            self._schedule_other_rotation_events(run, events)

            # Phase 4: Supervisor events
            self._schedule_supervisor_events(run, events)

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

    def _schedule_juicer_events_only(self, run: object, events: List[object]) -> None:
        """
        Phase 2: Schedule Juicer events with PRIORITY (can bump Core events)

        Juicer events are scheduled AFTER Core events so they can bump Core events
        if the Primary Juicer is already assigned to a Core event at 9:00 AM.
        """
        juicer_events = [e for e in events if e.event_type == 'Juicer' and not e.is_scheduled]
        for event in juicer_events:
            self._schedule_juicer_event(run, event)

    def _schedule_other_rotation_events(self, run: object, events: List[object]) -> None:
        """
        Phase 3: Schedule other rotation-based events

        Handles:
        - Digitals (Digital Setup/Refresh) → Primary Lead rotation (fallback to Club Supervisor)
        - Digitals (Digital Teardown) → Secondary Lead rotation (fallback to Club Supervisor)
        - Freeosk → Primary Lead rotation
        - Other → Club Supervisor at Noon
        """
        for event in events:
            if event.is_scheduled:
                continue

            # Handle Other events - go to Club Supervisor at Noon
            if event.event_type == 'Other':
                self._schedule_other_event(run, event)

            # Handle Digitals events (detect subtype from name)
            elif event.event_type == 'Digitals':
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

    def _schedule_other_event(self, run: object, event: object) -> None:
        """
        Schedule Other events to Club Supervisor at Noon on their start date

        All events categorized as 'Other' are scheduled to the Club Supervisor
        at noon (12:00 PM) on the event's start date. Multiple events can overlap
        at the same time since time conflicts are ignored for Supervisor-level employees.
        """
        # Use event's start date for scheduling
        current_date = self._get_earliest_schedule_date(event)

        # Schedule at noon
        schedule_time = time(12, 0)
        schedule_datetime = datetime.combine(current_date.date(), schedule_time)

        # Get Club Supervisor
        club_supervisor = self.db.query(self.Employee).filter_by(
            job_title='Club Supervisor',
            is_active=True
        ).first()

        if club_supervisor:
            # Check basic availability (time off and weekly availability only)
            # Time conflicts are ignored for Club Supervisor
            target_date = schedule_datetime.date()

            # Check time off
            time_off = self.db.query(self.EmployeeTimeOff).filter(
                self.EmployeeTimeOff.employee_id == club_supervisor.id,
                self.EmployeeTimeOff.start_date <= target_date,
                self.EmployeeTimeOff.end_date >= target_date
            ).first()

            if time_off:
                self._create_failed_pending_schedule(run, event, f"Club Supervisor has time off on {target_date}")
                run.events_failed += 1
                return

            # Check weekly availability
            day_of_week = target_date.weekday()
            weekly_avail = self.db.query(self.EmployeeWeeklyAvailability).filter_by(
                employee_id=club_supervisor.id
            ).first()

            if weekly_avail:
                # Map day_of_week (0=Monday, 6=Sunday) to column name
                day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                day_column = day_names[day_of_week]
                is_available = getattr(weekly_avail, day_column)

                if not is_available:
                    self._create_failed_pending_schedule(run, event, f"Club Supervisor not available on {day_names[day_of_week].title()}")
                    run.events_failed += 1
                    return

            # Schedule the event (no time conflict checks for Club Supervisor)
            self._create_pending_schedule(run, event, club_supervisor, schedule_datetime, False, None, None)
            run.events_scheduled += 1
            current_app.logger.info(f"Scheduled Other event {event.project_ref_num} to Club Supervisor at noon")
        else:
            self._create_failed_pending_schedule(run, event, "No Club Supervisor found")
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

    def _schedule_juicer_event(self, run: object, event: object) -> None:
        """
        Schedule a Juicer event to the rotation-assigned employee

        Juicer events have PRIORITY - if the Primary Juicer is already scheduled
        to a Core event, we bump the Core event and schedule it elsewhere.

        Scheduling times:
        - JUICER-PRODUCTION-SPCLTY: 9:00 AM
        - Juicer Survey: 5:00 PM
        """
        # Determine the appropriate time for this Juicer event
        juicer_time = self._get_juicer_time(event)

        # Try each day from earliest allowed date to due date
        current_date = self._get_earliest_schedule_date(event)
        while current_date < event.due_datetime:
            employee = self.rotation_manager.get_rotation_employee(current_date, 'juicer')
            if not employee:
                current_date += timedelta(days=1)
                continue

            schedule_datetime = datetime.combine(current_date.date(), juicer_time)
            validation = self.validator.validate_assignment(event, employee, schedule_datetime)

            if validation.is_valid:
                # Juicer is available - schedule it
                self._create_pending_schedule(run, event, employee, schedule_datetime, False, None, None)
                run.events_scheduled += 1
                return
            else:
                # Juicer is NOT available - check if they have a Core event we can bump
                # Check if the conflict is a Core event scheduled to this employee
                conflicting_schedule = self.db.query(self.Schedule).filter_by(
                    employee_id=employee.id,
                    schedule_datetime=schedule_datetime
                ).first()

                conflicting_pending = None
                if not conflicting_schedule:
                    # Check pending schedules from this run
                    conflicting_pending = self.db.query(self.PendingSchedule).filter_by(
                        scheduler_run_id=run.id,
                        employee_id=employee.id,
                        schedule_datetime=schedule_datetime
                    ).first()

                # Determine if we can bump this event
                bumped_event = None
                if conflicting_schedule:
                    # Check if it's a Core event
                    bumped_event = self.db.query(self.Event).filter_by(
                        project_ref_num=conflicting_schedule.event_ref_num
                    ).first()

                    if bumped_event and bumped_event.event_type == 'Core':
                        # Remove the existing schedule
                        self.db.delete(conflicting_schedule)
                        self.db.flush()

                        # Schedule the Juicer event
                        self._create_pending_schedule(run, event, employee, schedule_datetime, False, None, None)
                        run.events_scheduled += 1

                        # Try to reschedule the bumped Core event
                        self._reschedule_bumped_core_event(run, bumped_event, schedule_datetime.date())
                        return

                elif conflicting_pending:
                    # Check if it's a Core event
                    bumped_event = self.db.query(self.Event).filter_by(
                        project_ref_num=conflicting_pending.event_ref_num
                    ).first()

                    if bumped_event and bumped_event.event_type == 'Core':
                        # Remove the pending schedule
                        self.db.delete(conflicting_pending)
                        self.db.flush()

                        # Schedule the Juicer event
                        self._create_pending_schedule(run, event, employee, schedule_datetime, False, None, None)
                        run.events_scheduled += 1

                        # Try to reschedule the bumped Core event
                        self._reschedule_bumped_core_event(run, bumped_event, schedule_datetime.date())
                        return

            current_date += timedelta(days=1)

        # Failed to schedule
        self._create_failed_pending_schedule(run, event, "No available Juicer rotation employee")
        run.events_failed += 1

    def _reschedule_bumped_core_event(self, run: object, core_event: object, original_date: date) -> None:
        """
        Try to reschedule a Core event that was bumped by a Juicer event

        Args:
            run: Current scheduler run
            core_event: The Core event that was bumped
            original_date: The date it was originally scheduled for
        """
        # Try to schedule on the same day at a different time
        for time_slot in self.CORE_TIME_SLOTS:
            schedule_datetime = datetime.combine(original_date, time_slot)

            # Try Leads first
            leads = self._get_available_leads(core_event, schedule_datetime)
            for lead in leads:
                validation = self.validator.validate_assignment(core_event, lead, schedule_datetime)
                if validation.is_valid:
                    self._create_pending_schedule(run, core_event, lead, schedule_datetime, False, None, None)
                    current_app.logger.info(
                        f"Rescheduled bumped Core event {core_event.project_ref_num} "
                        f"from 9:00 AM to {time_slot.strftime('%H:%M')}"
                    )
                    return

            # Try Event Specialists
            specialists = self._get_available_specialists(core_event, schedule_datetime)
            for specialist in specialists:
                validation = self.validator.validate_assignment(core_event, specialist, schedule_datetime)
                if validation.is_valid:
                    self._create_pending_schedule(run, core_event, specialist, schedule_datetime, False, None, None)
                    current_app.logger.info(
                        f"Rescheduled bumped Core event {core_event.project_ref_num} "
                        f"from 9:00 AM to {time_slot.strftime('%H:%M')} (Event Specialist)"
                    )
                    return

        # Could not reschedule on same day - try next days
        current_date = original_date + timedelta(days=1)
        end_date = core_event.due_datetime.date()

        while current_date < end_date:
            time_slot = self._get_next_time_slot(datetime.combine(current_date, time(0, 0)))
            schedule_datetime = datetime.combine(current_date, time_slot)

            # Try Leads
            leads = self._get_available_leads(core_event, schedule_datetime)
            for lead in leads:
                validation = self.validator.validate_assignment(core_event, lead, schedule_datetime)
                if validation.is_valid:
                    self._create_pending_schedule(run, core_event, lead, schedule_datetime, False, None, None)
                    current_app.logger.info(
                        f"Rescheduled bumped Core event {core_event.project_ref_num} "
                        f"to {schedule_datetime.strftime('%Y-%m-%d %H:%M')}"
                    )
                    return

            # Try Specialists
            specialists = self._get_available_specialists(core_event, schedule_datetime)
            for specialist in specialists:
                validation = self.validator.validate_assignment(core_event, specialist, schedule_datetime)
                if validation.is_valid:
                    self._create_pending_schedule(run, core_event, specialist, schedule_datetime, False, None, None)
                    current_app.logger.info(
                        f"Rescheduled bumped Core event {core_event.project_ref_num} "
                        f"to {schedule_datetime.strftime('%Y-%m-%d %H:%M')} (Event Specialist)"
                    )
                    return

            current_date += timedelta(days=1)

        # Failed to reschedule
        self._create_failed_pending_schedule(run, core_event, "Bumped by Juicer event - could not reschedule")
        run.events_failed += 1
        current_app.logger.warning(
            f"Failed to reschedule bumped Core event {core_event.project_ref_num}"
        )

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
        """Schedule Digital Setup/Refresh or Freeosk event to Primary Lead"""
        current_date = self._get_earliest_schedule_date(event)
        while current_date < event.due_datetime:
            # Determine time slot based on event name
            event_name_upper = event.project_name.upper()

            # Digital Setup/Refresh: 15-minute intervals starting at 9:15
            if event.event_type == 'Digitals' and ('SETUP' in event_name_upper or 'REFRESH' in event_name_upper):
                schedule_time = self._get_next_digital_time_slot(current_date)
            # Freeosk: 9:00 AM
            else:
                schedule_time = self.DEFAULT_TIMES.get('Freeosk', time(9, 0))

            schedule_datetime = datetime.combine(current_date.date(), schedule_time)

            # Try primary lead first
            employee = self.rotation_manager.get_rotation_employee(current_date, 'primary_lead')
            if employee:
                validation = self.validator.validate_assignment(event, employee, schedule_datetime)
                if validation.is_valid:
                    self._create_pending_schedule(run, event, employee, schedule_datetime, False, None, None)
                    run.events_scheduled += 1
                    return

            # Try other available leads
            available_leads = self._get_available_leads(event, schedule_datetime)
            if available_leads:
                self._create_pending_schedule(run, event, available_leads[0], schedule_datetime, False, None, None)
                run.events_scheduled += 1
                return

            # Fallback to Club Supervisor if no leads available
            club_supervisor = self.db.query(self.Employee).filter_by(
                job_title='Club Supervisor',
                is_active=True
            ).first()

            if club_supervisor:
                # Check basic availability for Club Supervisor
                validation = self.validator.validate_assignment(event, club_supervisor, schedule_datetime)
                if validation.is_valid:
                    self._create_pending_schedule(run, event, club_supervisor, schedule_datetime, False, None, None)
                    run.events_scheduled += 1
                    current_app.logger.info(
                        f"Scheduled Digital event {event.project_ref_num} to Club Supervisor (no leads available)"
                    )
                    return

            current_date += timedelta(days=1)

        self._create_failed_pending_schedule(run, event, "No available Lead or Club Supervisor for Digital event")
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
        """Schedule Digital Teardown to Secondary Lead at rotating 15-min intervals from 5 PM (fallback to Club Supervisor)"""
        current_date = self._get_earliest_schedule_date(event)
        while current_date < event.due_datetime:
            schedule_time = self._get_next_teardown_time_slot(current_date)
            schedule_datetime = datetime.combine(current_date.date(), schedule_time)

            # Try secondary lead first
            secondary_lead = self.rotation_manager.get_secondary_lead(current_date)
            if secondary_lead:
                validation = self.validator.validate_assignment(event, secondary_lead, schedule_datetime)
                if validation.is_valid:
                    self._create_pending_schedule(run, event, secondary_lead, schedule_datetime, False, None, None)
                    run.events_scheduled += 1
                    return

            # Fallback to Club Supervisor if no secondary lead available
            club_supervisor = self.db.query(self.Employee).filter_by(
                job_title='Club Supervisor',
                is_active=True
            ).first()

            if club_supervisor:
                validation = self.validator.validate_assignment(event, club_supervisor, schedule_datetime)
                if validation.is_valid:
                    self._create_pending_schedule(run, event, club_supervisor, schedule_datetime, False, None, None)
                    run.events_scheduled += 1
                    current_app.logger.info(
                        f"Scheduled Digital Teardown {event.project_ref_num} to Club Supervisor (no secondary lead available)"
                    )
                    return

            current_date += timedelta(days=1)

        self._create_failed_pending_schedule(run, event, "No available Secondary Lead or Club Supervisor")
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

    def _schedule_supervisor_events(self, run: object, events: List[object]) -> None:
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
                # Check if Core event has a pending schedule
                core_pending = self.db.query(self.PendingSchedule).filter_by(
                    event_ref_num=core_event.project_ref_num,
                    scheduler_run_id=run.id
                ).first()

                if core_pending and core_pending.schedule_datetime:
                    # Use the pending schedule datetime
                    supervisor_datetime = datetime.combine(core_pending.schedule_datetime.date(), time(12, 0))
                else:
                    self._create_failed_pending_schedule(run, supervisor_event, "Core event not yet scheduled")
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
