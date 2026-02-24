import pytest
from datetime import date
from unittest.mock import patch

from skatetrax.utils.timeframe_generator import (
    TIMEFRAMES,
    current_month, last_month, last_3_months,
    previous_30_days, previous_60_days, year_to_date, total,
)

# run via: PYTHONPATH=. pytest tests/test_timeframes.py -v

FAKE_TODAY = date(2026, 3, 15)


def _patch_today(fn, **kwargs):
    with patch("skatetrax.utils.timeframe_generator.today_in_tz", return_value=FAKE_TODAY):
        return fn(**kwargs)


class TestTimeframeRegistry:

    def test_all_keys_present(self):
        expected = {"total", "current_month", "last_month", "90d", "12m", "30d", "60d", "ytd"}
        assert set(TIMEFRAMES.keys()) == expected

    def test_total_returns_none(self):
        assert total() is None


class TestCurrentMonth:

    def test_start_is_first_of_month(self):
        result = _patch_today(current_month)
        assert result["start"] == date(2026, 3, 1)

    def test_end_is_today(self):
        result = _patch_today(current_month)
        assert result["end"] == FAKE_TODAY


class TestLastMonth:

    def test_february(self):
        result = _patch_today(last_month)
        assert result["start"] == date(2026, 2, 1)
        assert result["end"] == date(2026, 2, 28)

    def test_january_wraps_to_december(self):
        with patch("skatetrax.utils.timeframe_generator.today_in_tz",
                    return_value=date(2026, 1, 10)):
            result = last_month()
        assert result["start"] == date(2025, 12, 1)
        assert result["end"] == date(2025, 12, 31)


class TestLast3Months:

    def test_basic(self):
        result = _patch_today(last_3_months)
        assert result["start"] == date(2025, 12, 1)
        assert result["end"] == FAKE_TODAY

    def test_wraps_year(self):
        with patch("skatetrax.utils.timeframe_generator.today_in_tz",
                    return_value=date(2026, 2, 15)):
            result = last_3_months()
        assert result["start"] == date(2025, 11, 1)


class TestPrevious30Days:

    def test_basic(self):
        result = _patch_today(previous_30_days)
        assert result["start"] == date(2026, 2, 13)
        assert result["end"] == FAKE_TODAY


class TestPrevious60Days:

    def test_basic(self):
        result = _patch_today(previous_60_days)
        assert result["start"] == date(2026, 1, 14)
        assert result["end"] == FAKE_TODAY


class TestYearToDate:

    def test_starts_jan_1(self):
        result = _patch_today(year_to_date)
        assert result["start"] == date(2026, 1, 1)
        assert result["end"] == FAKE_TODAY
