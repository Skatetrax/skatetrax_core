from datetime import datetime, date
from zoneinfo import ZoneInfo


def resolve_tz(rink_tz=None, user_tz=None):
    """Resolve display timezone using the cascade: rink → user → UTC."""
    return rink_tz or user_tz or 'UTC'


def utc_to_local(dt_utc, tz_name):
    """
    Convert a naive-UTC datetime to a timezone-aware local datetime.
    Returns the original value unchanged if either argument is None,
    or if the value is a date (not datetime).
    """
    if dt_utc is None or tz_name is None:
        return dt_utc
    if isinstance(dt_utc, date) and not isinstance(dt_utc, datetime):
        return dt_utc
    utc_aware = dt_utc.replace(tzinfo=ZoneInfo('UTC'))
    return utc_aware.astimezone(ZoneInfo(tz_name))


def today_in_tz(tz_name=None):
    """
    Get today's date in the given IANA timezone.
    Falls back to server-local date.today() when no timezone is provided.
    """
    if tz_name is None:
        return date.today()
    return datetime.now(ZoneInfo(tz_name)).date()
