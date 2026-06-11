from datetime import datetime, timedelta, date
from typing import Optional
import pytz


def get_user_timezone(timezone_str: str) -> pytz.timezone:
    """Get timezone object from string."""
    try:
        return pytz.timezone(timezone_str)
    except:
        return pytz.UTC


def get_current_time_in_timezone(timezone_str: str) -> datetime:
    """Get current time in user's timezone."""
    tz = get_user_timezone(timezone_str)
    return datetime.now(tz)


def is_same_day(dt1: datetime, dt2: datetime, timezone_str: str) -> bool:
    """Check if two datetimes are on the same day in user's timezone."""
    tz = get_user_timezone(timezone_str)

    if dt1.tzinfo is None:
        dt1 = pytz.UTC.localize(dt1)
    if dt2.tzinfo is None:
        dt2 = pytz.UTC.localize(dt2)

    dt1_local = dt1.astimezone(tz)
    dt2_local = dt2.astimezone(tz)

    return dt1_local.date() == dt2_local.date()


def days_between(dt1: datetime, dt2: datetime, timezone_str: str) -> int:
    """Calculate number of days between two datetimes in user's timezone."""
    tz = get_user_timezone(timezone_str)

    if dt1.tzinfo is None:
        dt1 = pytz.UTC.localize(dt1)
    if dt2.tzinfo is None:
        dt2 = pytz.UTC.localize(dt2)

    dt1_local = dt1.astimezone(tz).date()
    dt2_local = dt2.astimezone(tz).date()

    return abs((dt2_local - dt1_local).days)


def get_week_start_end(dt: Optional[datetime] = None, timezone_str: str = "UTC") -> tuple[datetime, datetime]:
    """Get the start and end of the week for a given datetime."""
    if dt is None:
        dt = datetime.utcnow()

    tz = get_user_timezone(timezone_str)
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)

    dt_local = dt.astimezone(tz)

    # Get Monday of current week
    start = dt_local - timedelta(days=dt_local.weekday())
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)

    # Get Sunday of current week
    end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)

    return start, end


def get_date_from_datetime(dt: datetime, timezone_str: str) -> date:
    """Get date from datetime in user's timezone."""
    tz = get_user_timezone(timezone_str)

    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)

    return dt.astimezone(tz).date()
