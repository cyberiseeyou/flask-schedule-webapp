"""
Event Helper Utilities
=======================

Utility functions for event processing and data extraction.

These helpers are used throughout the application to standardize event
data handling, especially for integration with external systems like
Walmart RetailLink.
"""

import re
from typing import Optional
from datetime import datetime, date


def extract_event_number(project_name):
    """
    Extract the first 6 digits from a Core event's project name.

    This event number is used as the EDR ID in Walmart's RetailLink system.

    Args:
        project_name (str): Event project name (e.g., "606034-JJSF-Super Pretzel King Size")

    Returns:
        str: 6-digit event number or None if not found

    Examples:
        >>> extract_event_number("606034-JJSF-Super Pretzel King Size")
        '606034'
        >>> extract_event_number("Invalid-Event-Name")
        None
    """
    if not project_name:
        return None

    # Look for 6-digit numbers at the start of the project name
    match = re.match(r'^(\d{6})', project_name)
    if match:
        return match.group(1)

    # If no match at start, look for any 6-digit sequence
    match = re.search(r'(\d{6})', project_name)
    if match:
        return match.group(1)

    return None


def parse_event_date(date_str: str) -> Optional[date]:
    """
    Parse event date from various string formats

    Supports multiple date formats commonly used in the system:
    - YYYY-MM-DD (ISO format)
    - MM/DD/YYYY (US format)
    - MM-DD-YYYY (US format with dashes)
    - YYYY/MM/DD (ISO with slashes)

    Args:
        date_str: Date string to parse

    Returns:
        Python date object or None if parsing failed
    """
    if not date_str:
        return None

    # Try various formats
    formats = [
        '%Y-%m-%d',      # 2025-10-05
        '%m/%d/%Y',      # 10/05/2025
        '%m-%d-%Y',      # 10-05-2025
        '%Y/%m/%d',      # 2025/10/05
        '%Y%m%d',        # 20251005
        '%m%d%Y',        # 10052025
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    return None


def format_event_date(date_obj: date, format_type: str = 'display') -> str:
    """
    Format date object for display or API

    Args:
        date_obj: Python date object
        format_type: Type of format
            - 'display': MM-DD-YYYY (e.g., "10-05-2025")
            - 'iso': YYYY-MM-DD (e.g., "2025-10-05")
            - 'api': YYYY-MM-DD (same as iso, for API calls)
            - 'filename': YYYYMMDD (e.g., "20251005")

    Returns:
        Formatted date string
    """
    if not date_obj:
        return ''

    format_map = {
        'display': '%m-%d-%Y',
        'iso': '%Y-%m-%d',
        'api': '%Y-%m-%d',
        'filename': '%Y%m%d',
    }

    fmt = format_map.get(format_type, '%Y-%m-%d')
    return date_obj.strftime(fmt)


def is_core_event(event) -> bool:
    """
    Check if event is a Core event type

    Core events require EDR (Event Detail Report) generation
    from Walmart RetailLink.

    Args:
        event: Event model instance

    Returns:
        True if Core event, False otherwise
    """
    if not event:
        return False

    return getattr(event, 'event_type', '') == 'Core'


def is_juicer_production_event(event) -> bool:
    """
    Check if event is a Juicer Production event

    Juicer Production events should be included in schedules
    but do not require EDR generation.

    Args:
        event: Event model instance

    Returns:
        True if Juicer Production event, False otherwise
    """
    if not event:
        return False

    # Check event type
    if getattr(event, 'event_type', '') != 'Juicer':
        return False

    # Check if production event (contains 'Production' in name)
    project_name = getattr(event, 'project_name', '').lower()
    if 'production' not in project_name:
        return False

    # Exclude survey events
    if 'survey' in project_name:
        return False

    return True


def should_include_in_daily_schedule(event) -> bool:
    """
    Determine if event should be included in daily schedule

    Daily schedules include Core and Juicer Production events.

    Args:
        event: Event model instance

    Returns:
        True if event should be included, False otherwise
    """
    return is_core_event(event) or is_juicer_production_event(event)


def sanitize_event_name(event_name: str) -> str:
    """
    Sanitize event name for use in filenames

    Removes or replaces characters that are invalid in filenames.

    Args:
        event_name: Original event name

    Returns:
        Sanitized event name safe for filenames
    """
    if not event_name:
        return 'Unknown_Event'

    # Replace invalid filename characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', event_name)

    # Replace multiple spaces/underscores with single underscore
    sanitized = re.sub(r'[\s_]+', '_', sanitized)

    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')

    # Limit length
    if len(sanitized) > 100:
        sanitized = sanitized[:100]

    return sanitized or 'Unknown_Event'


def validate_event_number(event_number: str) -> bool:
    """
    Validate that event number is in correct format

    Walmart event numbers must be exactly 6 digits.

    Args:
        event_number: Event number to validate

    Returns:
        True if valid, False otherwise
    """
    if not event_number:
        return False

    # Must be exactly 6 digits
    return bool(re.match(r'^\d{6}$', event_number))
