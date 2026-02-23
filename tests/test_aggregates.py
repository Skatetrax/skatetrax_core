import pytest
from uuid import UUID as PyUUID
from datetime import datetime, date, timezone, timedelta
from unittest.mock import patch

from skatetrax.models.ops.data_aggregates import SkaterAggregates, uMaintenanceV4, UserMeta
from skatetrax.models.t_ice_time import Ice_Time
from skatetrax.models.t_maint import uSkaterMaint

from tests.conftest import (
    NEW_USER_UUID, NEW_CONFIG_UUID, NEW_BLADE_UUID, NEW_BOOT_UUID,
    TEST_RINK_UUID, TEST_COACH_UUID, NO_COACH_UUID, NO_CLUB_UUID,
    OFF_ICE_RINK_UUID,
    FREESTYLE_WALKON_UUID, GROUP_CLASS_UUID, PUBLIC_UUID,
)

# run via: PYTHONPATH=. pytest tests/test_aggregates.py -v


# ---------------------------------------------------------------------------
# New user: everything should be zero
# ---------------------------------------------------------------------------
class TestNewUserAllZeros:
    """A brand new user with no sessions should report zero across the board."""

    def test_skated_total_zero(self, seeded_session):
        sa = SkaterAggregates(NEW_USER_UUID, session=seeded_session)
        result = sa.skated("total")
        assert result == {'hours': 0, 'minutes': 0}

    def test_coached_total_zero(self, seeded_session):
        sa = SkaterAggregates(NEW_USER_UUID, session=seeded_session)
        result = sa.coached("total")
        assert result == {'hours': 0, 'minutes': 0}

    def test_group_time_total_zero(self, seeded_session):
        sa = SkaterAggregates(NEW_USER_UUID, session=seeded_session)
        result = sa.group_time("total")
        assert result == {'hours': 0, 'minutes': 0}

    def test_ice_cost_total_zero(self, seeded_session):
        sa = SkaterAggregates(NEW_USER_UUID, session=seeded_session)
        result = sa.ice_cost("total")
        assert result == "0.00"

    def test_coach_cost_total_zero(self, seeded_session):
        sa = SkaterAggregates(NEW_USER_UUID, session=seeded_session)
        result = sa.coach_cost("total")
        assert result == "0.00"

    def test_maint_clock_zero(self, seeded_session):
        mv = uMaintenanceV4(NEW_USER_UUID, session=seeded_session)
        clock = mv.maint_clock()
        assert clock["active_minutes"] == {'hours': 0, 'minutes': 0.0}

    def test_maint_clock_pref_21(self, seeded_session):
        mv = uMaintenanceV4(NEW_USER_UUID, session=seeded_session)
        clock = mv.maint_clock()
        assert clock["clock_minutes"] == {'hours': 21, 'minutes': 0.0}

    def test_maint_clock_remaining_full(self, seeded_session):
        mv = uMaintenanceV4(NEW_USER_UUID, session=seeded_session)
        clock = mv.maint_clock()
        assert clock["remaining_minutes"] == {'hours': 21, 'minutes': 0.0}


# ---------------------------------------------------------------------------
# Known data: seed some sessions, verify the math
# ---------------------------------------------------------------------------
def _add_session(session, date_val, ice_min, coach_min, coach_cost,
                 ice_cost=0, skate_type=FREESTYLE_WALKON_UUID,
                 coach_id=NO_COACH_UUID):
    session.add(Ice_Time(
        date=date_val,
        ice_time=ice_min, ice_cost=ice_cost,
        skate_type=skate_type,
        coach_time=coach_min, coach_id=coach_id,
        coach_cost=coach_cost,
        has_video=0, has_notes=0,
        rink_id=TEST_RINK_UUID,
        uSkaterUUID=NEW_USER_UUID,
        uSkaterConfig=NEW_CONFIG_UUID,
        uSkaterType=1,
    ))


class TestKnownSessionData:

    def test_total_ice_time(self, seeded_session):
        _add_session(seeded_session, datetime(2026, 1, 10), 60, 30, 35)
        _add_session(seeded_session, datetime(2026, 1, 12), 45, 0, 0)
        seeded_session.flush()

        sa = SkaterAggregates(NEW_USER_UUID, session=seeded_session)
        result = sa.skated("total")
        assert result == {'hours': 1, 'minutes': 45.0}

    def test_coached_time(self, seeded_session):
        _add_session(seeded_session, datetime(2026, 1, 10), 60, 30, 35)
        _add_session(seeded_session, datetime(2026, 1, 12), 45, 0, 0)
        seeded_session.flush()

        sa = SkaterAggregates(NEW_USER_UUID, session=seeded_session)
        result = sa.coached("total")
        assert result == {'hours': 0, 'minutes': 30.0}

    def test_independent_is_total_minus_coached(self, seeded_session):
        _add_session(seeded_session, datetime(2026, 1, 10), 60, 30, 35)
        _add_session(seeded_session, datetime(2026, 1, 12), 120, 30, 35)
        seeded_session.flush()

        sa = SkaterAggregates(NEW_USER_UUID, session=seeded_session)
        total_min = sa.aggregate(Ice_Time, "ice_time")
        coached_min = sa.aggregate(Ice_Time, "coach_time")
        independent = total_min - coached_min
        assert total_min == 180
        assert coached_min == 60
        assert independent == 120

    def test_group_time_separated(self, seeded_session):
        _add_session(seeded_session, datetime(2026, 1, 10), 60, 0, 0,
                     skate_type=GROUP_CLASS_UUID)
        _add_session(seeded_session, datetime(2026, 1, 12), 45, 0, 0,
                     skate_type=FREESTYLE_WALKON_UUID)
        seeded_session.flush()

        sa = SkaterAggregates(NEW_USER_UUID, session=seeded_session)
        group = sa.group_time("total")
        assert group == {'hours': 1, 'minutes': 0.0}

    def test_practice_excludes_coached_and_group(self, seeded_session):
        _add_session(seeded_session, datetime(2026, 1, 10), 45, 30, 42,
                     skate_type=FREESTYLE_WALKON_UUID)
        _add_session(seeded_session, datetime(2026, 1, 12), 45, 30, 42,
                     skate_type=FREESTYLE_WALKON_UUID)
        _add_session(seeded_session, datetime(2026, 1, 14), 60, 0, 0,
                     skate_type=GROUP_CLASS_UUID)
        seeded_session.flush()

        sa = SkaterAggregates(NEW_USER_UUID, session=seeded_session)
        # total=150, coached=60, group=60 → practice=30
        result = sa.practice("total")
        assert result == {'hours': 0, 'minutes': 30.0}

    def test_practice_zero_when_all_coached(self, seeded_session):
        _add_session(seeded_session, datetime(2026, 1, 10), 60, 60, 42)
        seeded_session.flush()

        sa = SkaterAggregates(NEW_USER_UUID, session=seeded_session)
        result = sa.practice("total")
        assert result == {'hours': 0, 'minutes': 0.0}

    def test_ice_cost_sums(self, seeded_session):
        _add_session(seeded_session, datetime(2026, 1, 10), 60, 0, 0, ice_cost=12.50)
        _add_session(seeded_session, datetime(2026, 1, 12), 45, 0, 0, ice_cost=8.00)
        seeded_session.flush()

        sa = SkaterAggregates(NEW_USER_UUID, session=seeded_session)
        assert sa.ice_cost("total") == "20.50"

    def test_coach_cost_sums(self, seeded_session):
        _add_session(seeded_session, datetime(2026, 1, 10), 60, 30, 35)
        _add_session(seeded_session, datetime(2026, 1, 12), 60, 30, 42)
        seeded_session.flush()

        sa = SkaterAggregates(NEW_USER_UUID, session=seeded_session)
        assert sa.coach_cost("total") == "77.00"


class TestTimeframeFiltering:
    """Verify that timeframe boundaries correctly include/exclude sessions."""

    def test_30d_excludes_old_sessions(self, seeded_session):
        today = date.today()
        recent = datetime.combine(today - timedelta(days=10), datetime.min.time())
        old = datetime.combine(today - timedelta(days=60), datetime.min.time())

        _add_session(seeded_session, recent, 60, 0, 0)
        _add_session(seeded_session, old, 120, 0, 0)
        seeded_session.flush()

        sa = SkaterAggregates(NEW_USER_UUID, session=seeded_session)
        total_all = sa.aggregate(Ice_Time, "ice_time")
        assert total_all == 180

        result_30d = sa.skated("30d")
        assert result_30d == {'hours': 1, 'minutes': 0.0}

    def test_ytd_excludes_last_year(self, seeded_session):
        this_year = datetime(date.today().year, 2, 1)
        last_year = datetime(date.today().year - 1, 11, 1)

        _add_session(seeded_session, this_year, 90, 0, 0)
        _add_session(seeded_session, last_year, 60, 0, 0)
        seeded_session.flush()

        sa = SkaterAggregates(NEW_USER_UUID, session=seeded_session)
        result = sa.skated("ytd")
        assert result == {'hours': 1, 'minutes': 30.0}


class TestMaintClockWithData:

    def test_active_minutes_after_sharpening(self, seeded_session):
        maint_date = datetime(2026, 1, 1)
        seeded_session.add(uSkaterMaint(
            m_date=maint_date, m_hours_on=0, m_cost=20,
            m_location=TEST_RINK_UUID, m_notes=None, m_roh="7/16",
            m_pref_hours=21, uSkaterBladesID=NEW_BLADE_UUID,
            uSkateConfig=None, uSkaterUUID=NEW_USER_UUID,
        ))
        _add_session(seeded_session, datetime(2026, 1, 5), 60, 0, 0)
        _add_session(seeded_session, datetime(2026, 1, 10), 45, 0, 0)
        seeded_session.flush()

        mv = uMaintenanceV4(NEW_USER_UUID, session=seeded_session)
        clock = mv.maint_clock()
        assert clock["active_minutes"] == {'hours': 1, 'minutes': 45.0}
        assert clock["remaining_minutes"] == {'hours': 19, 'minutes': 15.0}


class TestResolveTimeframe:

    def test_unknown_raises(self, seeded_session):
        sa = SkaterAggregates(NEW_USER_UUID, session=seeded_session)
        with pytest.raises(ValueError, match="Unknown timeframe"):
            sa.skated("invalid_timeframe")

    def test_total_returns_all(self, seeded_session):
        _add_session(seeded_session, datetime(2020, 6, 1), 60, 0, 0)
        _add_session(seeded_session, datetime(2026, 1, 1), 30, 0, 0)
        seeded_session.flush()

        sa = SkaterAggregates(NEW_USER_UUID, session=seeded_session)
        result = sa.skated("total")
        assert result == {'hours': 1, 'minutes': 30.0}


# ---------------------------------------------------------------------------
# UserMeta.to_dict -- UUID resolution via joins
# ---------------------------------------------------------------------------
class TestUserMetaToDict:

    def test_returns_empty_for_unknown_user(self, seeded_session):
        from uuid import uuid4
        um = UserMeta(uuid4(), session=seeded_session)
        assert um.to_dict() == {}

    def test_resolves_rink_name(self, seeded_session):
        um = UserMeta(NEW_USER_UUID, session=seeded_session)
        result = um.to_dict()
        assert result['uSkaterRinkPref'] == "Off Ice"

    def test_resolves_coach_name(self, seeded_session):
        um = UserMeta(NEW_USER_UUID, session=seeded_session)
        result = um.to_dict()
        assert result['activeCoach'] == "- -"

    def test_resolves_club_name(self, seeded_session):
        um = UserMeta(NEW_USER_UUID, session=seeded_session)
        result = um.to_dict()
        assert result['org_Club'] == "No Club"

    def test_resolves_ice_config(self, seeded_session):
        um = UserMeta(NEW_USER_UUID, session=seeded_session)
        result = um.to_dict()
        assert result['uSkaterComboIce'] == "Generic Rental / Generic Rental"

    def test_basic_fields_present(self, seeded_session):
        um = UserMeta(NEW_USER_UUID, session=seeded_session)
        result = um.to_dict()
        assert result['uSkaterFname'] == "New"
        assert result['uSkaterLname'] == "Skater"
        assert result['uSkaterCity'] == "Testville"
        assert result['uSkaterMaintPref'] == 21
