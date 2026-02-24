from datetime import date, timedelta
from .tz import today_in_tz


def current_month(tz=None):
    today = today_in_tz(tz)
    start = today.replace(day=1)
    end = today
    return {"start": start, "end": end}

def last_month(tz=None):
    today = today_in_tz(tz)
    first_of_this_month = today.replace(day=1)
    last_month_end = first_of_this_month - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    return {"start": last_month_start, "end": last_month_end}

def last_3_months(tz=None):
    today = today_in_tz(tz)
    end = today
    start_month = today.month - 3
    start_year = today.year
    if start_month <= 0:
        start_month += 12
        start_year -= 1
    start = date(start_year, start_month, 1)
    return {"start": start, "end": end}

def last_12_months(tz=None):
    today = today_in_tz(tz)
    start = today.replace(year=today.year - 1, month=1, day=1)
    end = today
    return {"start": start, "end": end}

def previous_30_days(tz=None):
    today = today_in_tz(tz)
    start = today - timedelta(days=30)
    end = today
    return {"start": start, "end": end}

def previous_60_days(tz=None):
    today = today_in_tz(tz)
    start = today - timedelta(days=60)
    end = today
    return {"start": start, "end": end}

def year_to_date(tz=None):
    today = today_in_tz(tz)
    start = today.replace(month=1, day=1)
    end = today
    return {"start": start, "end": end}

def total(tz=None):
    return None

TIMEFRAMES = {
    "total": total,
    "current_month": current_month,
    "last_month": last_month,
    "90d": last_3_months,
    "12m": last_12_months,
    "30d": previous_30_days,
    "60d": previous_60_days,
    "ytd": year_to_date
}
