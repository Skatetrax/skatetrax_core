import pytest
from datetime import datetime, date
from zoneinfo import ZoneInfo
from unittest.mock import patch

from skatetrax.utils.tz import (
    resolve_tz,
    utc_to_local,
    today_in_tz,
    local_date_start_as_utc_naive,
    utc_naive_range_for_inclusive_local_dates,
    intent_local_calendar_day_for_legacy_utc_midnight,
)

# run via: PYTHONPATH=. pytest tests/test_tz.py -v


class TestResolveTz:

    def test_rink_wins(self):
        assert resolve_tz("America/New_York", "America/Chicago") == "America/New_York"

    def test_user_fallback(self):
        assert resolve_tz(None, "America/Chicago") == "America/Chicago"

    def test_utc_default(self):
        assert resolve_tz(None, None) == "UTC"

    def test_rink_only(self):
        assert resolve_tz("America/Los_Angeles", None) == "America/Los_Angeles"


class TestUtcToLocal:

    def test_converts_eastern(self):
        utc_dt = datetime(2026, 1, 15, 17, 0, 0)
        result = utc_to_local(utc_dt, "America/New_York")
        assert result.hour == 12
        assert str(result.tzinfo) == "America/New_York"

    def test_none_datetime_passthrough(self):
        assert utc_to_local(None, "America/New_York") is None

    def test_none_tz_passthrough(self):
        dt = datetime(2026, 1, 15, 17, 0, 0)
        assert utc_to_local(dt, None) is dt

    def test_date_not_datetime_passthrough(self):
        d = date(2026, 1, 15)
        assert utc_to_local(d, "America/New_York") is d

    def test_dst_summer(self):
        utc_dt = datetime(2026, 7, 15, 16, 0, 0)
        result = utc_to_local(utc_dt, "America/New_York")
        assert result.hour == 12  # EDT is UTC-4


class TestLocalDateToUtcNaive:

    def test_eastern_midnight_is_utc_offset(self):
        d = date(2026, 2, 28)
        utc_naive = local_date_start_as_utc_naive(d, "America/New_York")
        assert utc_naive == datetime(2026, 2, 28, 5, 0, 0)

    def test_utc_identity(self):
        d = date(2026, 3, 1)
        assert local_date_start_as_utc_naive(d, "UTC") == datetime(2026, 3, 1, 0, 0, 0)


class TestIntentLocalDayLegacyMidnight:

    def test_eastern_utc_midnight_bumps_to_stored_utc_date(self):
        # Mar 3 00:00 UTC = Sunday PM US/Eastern → user meant Mon Mar 3
        d = intent_local_calendar_day_for_legacy_utc_midnight(
            datetime(2026, 3, 3, 0, 0, 0), "America/New_York"
        )
        assert d == date(2026, 3, 3)

    def test_utc_skater_no_bump(self):
        d = intent_local_calendar_day_for_legacy_utc_midnight(
            datetime(2026, 3, 3, 0, 0, 0), "UTC"
        )
        assert d == date(2026, 3, 3)

    def test_tokyo_same_calendar_no_bump(self):
        d = intent_local_calendar_day_for_legacy_utc_midnight(
            datetime(2026, 3, 3, 0, 0, 0), "Asia/Tokyo"
        )
        assert d == date(2026, 3, 3)


class TestUtcNaiveRangeInclusive:

    def test_february_span_new_york(self):
        lo, hi_excl = utc_naive_range_for_inclusive_local_dates(
            date(2026, 2, 1), date(2026, 2, 28), "America/New_York"
        )
        edge = datetime(2026, 3, 1, 0, 0, 0)
        assert lo <= edge < hi_excl


class TestTodayInTz:

    def test_no_tz_returns_date(self):
        result = today_in_tz(None)
        assert isinstance(result, date)

    def test_with_tz_returns_date(self):
        result = today_in_tz("America/New_York")
        assert isinstance(result, date)
        assert not isinstance(result, datetime)

    def test_returns_correct_type(self):
        result = today_in_tz("UTC")
        assert isinstance(result, date)

    def test_different_tz_still_date(self):
        result = today_in_tz("Pacific/Auckland")
        assert isinstance(result, date)
