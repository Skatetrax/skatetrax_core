import pytest
from datetime import datetime, date
from zoneinfo import ZoneInfo
from unittest.mock import patch

from skatetrax.utils.tz import resolve_tz, utc_to_local, today_in_tz

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
