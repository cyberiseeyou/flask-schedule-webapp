"""
Scheduling Constants for Flask Schedule Webapp
Centralized location for all scheduling-related magic numbers and configuration values
"""
from dataclasses import dataclass
from datetime import time
from enum import Enum


# ============================================================================
# EVENT TYPES
# ============================================================================

class EventType(str, Enum):
    """Valid event types for scheduling"""
    CORE = 'Core'
    JUICER = 'Juicer'
    SUPERVISOR = 'Supervisor'
    DIGITALS = 'Digitals'
    FREEOSK = 'Freeosk'
    OTHER = 'Other'
    DIGITAL_SETUP = 'Digital Setup'
    DIGITAL_REFRESH = 'Digital Refresh'
    DIGITAL_TEARDOWN = 'Digital Teardown'


class JobTitle(str, Enum):
    """Valid employee job titles"""
    CLUB_SUPERVISOR = 'Club Supervisor'
    LEAD_EVENT_SPECIALIST = 'Lead Event Specialist'
    JUICER_BARISTA = 'Juicer Barista'
    EVENT_SPECIALIST = 'Event Specialist'


class EventCondition(str, Enum):
    """Event condition/status values"""
    UNSTAFFED = 'Unstaffed'
    STAFFED = 'Staffed'
    SUBMITTED = 'Submitted'
    CANCELLED = 'Cancelled'


class SyncStatus(str, Enum):
    """Synchronization status for external API"""
    PENDING = 'pending'
    SYNCED = 'synced'
    FAILED = 'failed'


# ============================================================================
# SCHEDULING CONSTANTS
# ============================================================================

@dataclass(frozen=True)
class SchedulingConstants:
    """Scheduling business rules and timing constants"""

    # Scheduling windows and timing
    MIN_ADVANCE_DAYS: int = 3  # Minimum days ahead for auto-scheduling
    EVENT_OVERDUE_HOURS: int = 24  # Hours until event considered overdue
    TIME_PROXIMITY_HOURS: int = 2  # Min hours between events for same employee
    SESSION_LIFETIME_HOURS: int = 24  # Authentication session duration
    DEFAULT_EVENT_DURATION_MIN: int = 120  # Standard event duration (2 hours)

    # Auto-scheduler limits
    MAX_BUMPS_PER_EVENT: int = 3  # Prevent infinite rescheduling loops
    MAX_CORE_EVENTS_PER_DAY: int = 1  # Core events per employee per day

    # Core event time slots (9:45 AM - 11:30 AM in intervals)
    CORE_TIME_SLOTS: tuple = (
        time(9, 45),   # Primary Lead slot (first available)
        time(10, 30),  # Secondary slot
        time(11, 0),   # Tertiary slot
        time(11, 30)   # Final slot
    )

    # Digital Setup/Refresh time slots (4 slots: 9:15 AM - 10:00 AM)
    DIGITAL_TIME_SLOTS: tuple = (
        time(9, 15),
        time(9, 30),
        time(9, 45),
        time(10, 0),
    )

    # Digital Teardown time slots (15 min intervals starting at 5:00 PM)
    TEARDOWN_TIME_SLOTS: tuple = (
        time(17, 0),   # 5:00 PM
        time(17, 15),
        time(17, 30),
        time(17, 45),
        time(18, 0),   # 6:00 PM
        time(18, 15),
        time(18, 30),
        time(18, 45),
    )


# Global instance for easy access throughout the application
CONST = SchedulingConstants()


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

# Default event durations (in minutes)
DEFAULT_DURATIONS = {
    'Core': 390,        # 6.5 hours
    'Juicer': 540,      # 9 hours
    'Supervisor': 5,    # 5 minutes
    'Digitals': 15,     # 15 minutes
    'Freeosk': 15,      # 15 minutes
    'Other': 15         # 15 minutes
}
