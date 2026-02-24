from datetime import date, timedelta
from .tz import today_in_tz


def currency_usd(func):
    '''
    ensures currency formating is consistent
    '''

    def wrapper(*args, **kwargs):
        amount = func(*args, **kwargs)
        if amount is None:
            return ("%0.2f" % float(0))
        else:
            return ("%0.2f" % float(amount))
    return wrapper


def minutes_to_hours(func):
    '''
    ensures minutes are always divided into
    amount of hours and minutes cleanly
    '''

    def wrapper(*args, **kwargs):
        m = func(*args, **kwargs)
        if m is not None:
            h, m = divmod(m, 60)
        else:
             return {'hours': 0, 'minutes': 0}
        return {'hours': int(h), 'minutes': float(m)}
    return wrapper


class Timelines():

    def current_month(tz=None):
        today = today_in_tz(tz)
        start_day = today.replace(day=1) - timedelta()

        date_range = {
            'first': today.strftime("%Y-%m-%d"),
            'last': start_day.strftime("%Y-%m-%d")
                }

        return date_range

    def last_month(tz=None):
        today = today_in_tz(tz)
        last_month_last_day = today.replace(day=1) - timedelta(days=1)
        last_month_first_day = (
            today.replace(day=1)
            - timedelta(days=last_month_last_day.day)
                )

        date_range = {
            'first': last_month_first_day.strftime("%Y-%m-%d"),
            'last': last_month_last_day.strftime("%Y-%m-%d")
                }

        return date_range

    def last_3m(tz=None):
        today = today_in_tz(tz)
        past_3m = today - timedelta(weeks=12)
        past_3m_start = past_3m.replace(day=1)

        date_range = {
            'first': past_3m_start.strftime("%Y-%m-%d"),
            'last': today.strftime("%Y-%m-%d")
                }

        return date_range
