from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo


def _zoneinfo_or_utc(tz_name):
    """Resolve an IANA name; invalid or empty values fall back to UTC."""
    if not tz_name:
        return ZoneInfo("UTC")
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return ZoneInfo("UTC")


def intent_local_calendar_day_for_legacy_utc_midnight(
    stored_naive_utc: datetime, tz_name: str | None
) -> date:
    """
    Legacy rows were often saved as UTC midnight. That instant can fall on the *previous*
    local calendar evening (e.g. Americas). Infer the skating day the user meant:

    - If local calendar date < stored UTC date → intent is (local date + 1 day).
    - Otherwise (UTC user, or same calendar date in Asia) → intent is stored UTC date.

    Used by admin migration; new inserts should use local_date_start_as_utc_naive from the
    form date directly (no bump).
    """
    stored_d = stored_naive_utc.date()
    local_d = utc_to_local(stored_naive_utc, resolve_tz(None, tz_name)).date()
    if local_d < stored_d:
        return local_d + timedelta(days=1)
    return stored_d


def local_date_start_as_utc_naive(local_day: date, tz_name: str | None) -> datetime:
    """
    Convert a calendar date in the skater's (or rink's) timezone to the
    UTC instant at the start of that local day, returned as naive UTC for
    storage alongside existing naive-UTC timestamps.
    """
    z = _zoneinfo_or_utc(tz_name)
    start_local = datetime.combine(local_day, time.min, tzinfo=z)
    return start_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)


def utc_naive_range_for_inclusive_local_dates(
    start_d: date, end_d: date, tz_name: str | None
) -> tuple[datetime, datetime]:
    """
    Map an inclusive local calendar range [start_d, end_d] to half-open UTC
    [start_utc_naive, end_utc_naive) for filtering TIMESTAMP columns that
    store naive UTC.
    """
    lo = local_date_start_as_utc_naive(start_d, tz_name)
    hi_excl = local_date_start_as_utc_naive(end_d + timedelta(days=1), tz_name)
    return lo, hi_excl


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
