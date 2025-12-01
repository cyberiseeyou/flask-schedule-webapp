"""
Database compatibility utilities for cross-database support (SQLite and PostgreSQL)
"""
from sqlalchemy import func, cast, Time
from sqlalchemy.sql import expression


def extract_time(column):
    """
    Extract time portion from a datetime column in a database-agnostic way.

    SQLite uses: time(column)
    PostgreSQL uses: column::time or CAST(column AS TIME)

    This function returns a SQLAlchemy expression that works with both.

    Args:
        column: A SQLAlchemy column containing datetime data

    Returns:
        A SQLAlchemy expression that extracts the time portion
    """
    # Use CAST which works on both SQLite and PostgreSQL
    # SQLite: CAST interprets as text but comparisons still work
    # PostgreSQL: CAST properly converts to TIME type
    return cast(column, Time)


def time_equals(column, time_value):
    """
    Compare the time portion of a datetime column to a time value.

    Args:
        column: A SQLAlchemy column containing datetime data
        time_value: A time string like '09:45:00' or datetime.time object

    Returns:
        A SQLAlchemy comparison expression
    """
    return cast(column, Time) == time_value


def time_not_equals(column, time_value):
    """
    Compare the time portion of a datetime column is not equal to a time value.

    Args:
        column: A SQLAlchemy column containing datetime data
        time_value: A time string like '09:45:00' or datetime.time object

    Returns:
        A SQLAlchemy comparison expression
    """
    return cast(column, Time) != time_value
