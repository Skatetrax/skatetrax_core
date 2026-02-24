from sqlalchemy import func, select
from datetime import date
from uuid import UUID as PyUUID
import calendar


from ...models.cyberconnect2 import create_session
from ...utils.timeframe_generator import TIMEFRAMES
from ...utils.common import minutes_to_hours, currency_usd
from ...utils.tz import today_in_tz, utc_to_local, resolve_tz

from ..t_equip import uSkateConfig, uSkaterBlades, uSkaterBoots
from ..t_skaterMeta import uSkaterConfig
from ..t_maint import uSkaterMaint
from ..t_ice_time import Ice_Time as IceTime
from ..t_locations import Locations
from ..t_coaches import Coaches
from ..t_memberships import Club_Directory


class SkaterAggregates:
    """
    Aggregator for skater metrics including ice_time, coach_time,
    costs, and now group sessions.
    """
    GROUP_SESSION_IDS = [PyUUID("db32094e-9b0d-42a5-b87f-cd47729b6c65")]
    COMPETITION_IDS = [PyUUID("7a3b3441-04d6-4b5a-afb6-eb556022c2e7"),
                       PyUUID("88f87085-927d-4b77-b1c9-77d6de7c2d28")]


    def __init__(self, uSkaterUUID, session=None, tz=None):
        self.uSkaterUUID = uSkaterUUID
        self.external_session = session
        self.tz = tz


    def _get_session(self):
        return self.external_session or create_session()


    def aggregate(self, model, field, start_date=None, end_date=None, ice_type_ids=None):
        """Sum field for this skater, optionally filtered by start/end dates and ice_type."""
        with self._get_session() as s:
            column = getattr(model, field)
            q = s.query(func.sum(column)).filter(model.uSkaterUUID == self.uSkaterUUID)
            if start_date and end_date:
                q = q.filter(model.date >= start_date, model.date <= end_date)
            if ice_type_ids:
                q = q.filter(model.skate_type.in_(ice_type_ids))
            result = q.scalar() or 0
        return result


    def sum_costs_by_model(self, model, cost_column="class_cost", start_date=None, end_date=None):
        """
        Generic helper to sum costs for this skater across any model
        that has a uSkaterUUID column and a cost column.
        """
        with self._get_session() as s:
            total = (
                s.query(func.coalesce(func.sum(getattr(model, cost_column)), 0))
                .filter(model.uSkaterUUID == self.uSkaterUUID)
            )
            if start_date and end_date:
                total = total.filter(model.date_start >= start_date, model.date_start <= end_date)
            return total.scalar() or 0


    # Convenience shortcuts
    @minutes_to_hours
    def skated(self, timeframe=None):
        from ..t_ice_time import Ice_Time
        start, end = self._resolve_timeframe(timeframe)
        return self.aggregate(Ice_Time, "ice_time", start, end)


    @minutes_to_hours
    def coached(self, timeframe=None):
        from ..t_ice_time import Ice_Time
        start, end = self._resolve_timeframe(timeframe)
        return self.aggregate(Ice_Time, "coach_time", start, end)


    @minutes_to_hours
    def group_time(self, timeframe=None):
        from ..t_ice_time import Ice_Time
        start, end = self._resolve_timeframe(timeframe)
        return self.aggregate(
            Ice_Time,
            "ice_time",
            start,
            end,
            ice_type_ids=self.GROUP_SESSION_IDS
        )


    @minutes_to_hours
    def practice(self, timeframe=None):
        """Independent practice: total ice time minus coached and group."""
        from ..t_ice_time import Ice_Time
        start, end = self._resolve_timeframe(timeframe)
        total = self.aggregate(Ice_Time, "ice_time", start, end)
        coached = self.aggregate(Ice_Time, "coach_time", start, end)
        group = self.aggregate(Ice_Time, "ice_time", start, end,
                               ice_type_ids=self.GROUP_SESSION_IDS)
        return max(total - coached - group, 0)


    @currency_usd
    def ice_cost(self, timeframe=None):
        from ..t_ice_time import Ice_Time
        start, end = self._resolve_timeframe(timeframe)
        return self.aggregate(Ice_Time, "ice_cost", start, end)


    @currency_usd
    def school_class_cost(self, timeframe=None):
        from ..t_classes import Skate_School
        start, end = self._resolve_timeframe(timeframe)
        return self.sum_costs_by_model(Skate_School, "class_cost", start, end)
    

    @currency_usd
    def coach_cost(self, timeframe=None):
        from ..t_ice_time import Ice_Time
        start, end = self._resolve_timeframe(timeframe)
        return self.aggregate(Ice_Time, "coach_cost", start, end)


    @currency_usd
    def equipment_cost(self):
        """Total equipment spend: boots + blades + general gear."""
        from ..t_equip import uSkaterBoots, uSkaterBlades, uSkaterEquipManifest
        with self._get_session() as s:
            boots = s.query(func.coalesce(func.sum(uSkaterBoots.bootsPurchaseAmount), 0)).filter(
                uSkaterBoots.uSkaterUUID == self.uSkaterUUID).scalar()
            blades = s.query(func.coalesce(func.sum(uSkaterBlades.bladesPurchaseAmount), 0)).filter(
                uSkaterBlades.uSkaterUUID == self.uSkaterUUID).scalar()
            gear = s.query(func.coalesce(func.sum(uSkaterEquipManifest.equip_cost), 0)).filter(
                uSkaterEquipManifest.uSkaterUUID == self.uSkaterUUID).scalar()
        return boots + blades + gear


    @currency_usd
    def membership_cost(self):
        """Total club membership fees."""
        from ..t_memberships import Club_Members
        with self._get_session() as s:
            return (
                s.query(func.coalesce(func.sum(Club_Members.membership_fee), 0))
                .filter(Club_Members.uSkaterUUID == self.uSkaterUUID)
                .scalar()
            )


    @currency_usd
    def competition_cost(self):
        """Total competition entry fees."""
        from ..t_events import Events_Competition
        with self._get_session() as s:
            return (
                s.query(func.coalesce(func.sum(Events_Competition.event_cost), 0))
                .filter(Events_Competition.uSkaterUUID == self.uSkaterUUID)
                .scalar()
            )


    @currency_usd
    def test_cost(self):
        """Total test/performance fees."""
        from ..t_tests import Event_Test
        with self._get_session() as s:
            return (
                s.query(func.coalesce(func.sum(Event_Test.test_cost), 0))
                .filter(Event_Test.uSkaterUUID == self.uSkaterUUID)
                .scalar()
            )


    def _resolve_timeframe(self, timeframe):
        if timeframe is None or timeframe == "total":
            return None, None
        fn = TIMEFRAMES.get(timeframe)
        if not fn:
            raise ValueError(f"Unknown timeframe: {timeframe}")
        dates = fn(tz=self.tz)
        if dates is None:
            return None, None
        return dates["start"], dates["end"]


    def monthly_times_json(self):
        """Return JSON for last 12 months with ice_time, coach_time, group sessions, competitions."""
        from ..t_ice_time import Ice_Time


        def minutes_to_hours_float(m):
            return m / 60.0


        today = today_in_tz(self.tz)
        months = []
        for i in range(11, -1, -1):
            year = today.year
            month = today.month - i
            if month <= 0:
                month += 12
                year -= 1
            months.append((year, month, calendar.month_name[month]))

        data = {"months": [], "ice_time": [], "practice": [], "coach_time": [], "group_sessions": [], "competitions": []}

        for year, month, month_name in months:
            start = date(year, month, 1)
            end_day = calendar.monthrange(year, month)[1]
            end = date(year, month, end_day)

            ice = self.aggregate(Ice_Time, "ice_time", start, end)
            coach = self.aggregate(Ice_Time, "coach_time", start, end)
            group = self.aggregate(Ice_Time, "ice_time", start, end, ice_type_ids=self.GROUP_SESSION_IDS)
            practice = max(ice - coach - group, 0)

            # Competition flag
            with self._get_session() as s:
                comp_count = (
                    s.query(Ice_Time)
                    .filter(Ice_Time.uSkaterUUID == self.uSkaterUUID)
                    .filter(Ice_Time.skate_type.in_(self.COMPETITION_IDS))
                    .filter(Ice_Time.date >= start, Ice_Time.date <= end)
                    .count()
                )
            comp_flag = 1 if comp_count > 0 else 0

            data["months"].append(month_name)
            data["ice_time"].append(minutes_to_hours_float(ice))
            data["practice"].append(minutes_to_hours_float(practice))
            data["coach_time"].append(minutes_to_hours_float(coach))
            data["group_sessions"].append(minutes_to_hours_float(group))
            data["competitions"].append(comp_flag)

        return data


class Equipment():

    def config_active(uSkaterUUID):
        """Return boot/blade details for the skater's active ice config."""
        with create_session() as s:
            config_id = (
                s.query(uSkaterConfig.uSkaterComboIce)
                .filter(uSkaterConfig.uSkaterUUID == uSkaterUUID)
                .scalar()
            )
            if not config_id:
                return None

            data = (
                s.query(
                    uSkateConfig.date_created,
                    uSkaterBoots.bootsName,
                    uSkaterBoots.bootsModel,
                    uSkaterBlades.bladesName,
                    uSkaterBlades.bladesModel
                )
                .join(uSkaterBoots, uSkateConfig.uSkaterBootsID == uSkaterBoots.bootsID)
                .join(uSkaterBlades, uSkateConfig.uSkaterBladesID == uSkaterBlades.bladesID)
                .where(uSkateConfig.sConfigID == config_id)
                .first()
            )
        return data._asdict() if data else None


class UserMeta:
    def __init__(self, uSkaterUUID, session=None):
        self.uSkaterUUID = uSkaterUUID
        self.external_session = session

    def _get_session(self):
        return self.external_session or create_session()

    def skater_profile(self):
        from ..t_skaterMeta import uSkaterConfig
        with self._get_session() as s:
            stmt = select(uSkaterConfig).where(uSkaterConfig.uSkaterUUID == self.uSkaterUUID)
            return s.execute(stmt).scalar_one_or_none()

    def default_rink(self):
        profile = self.skater_profile()
        return profile.rink_id if profile else None

    def default_skate_type(self):
        profile = self.skater_profile()
        return profile.skate_type if profile else None

    def default_coach(self):
        profile = self.skater_profile()
        return profile.coach_id if profile else None

    def to_dict(self):
        with self._get_session() as s:
            row = (
                s.query(
                    uSkaterConfig,
                    Locations.rink_name,
                    Coaches.coach_Fname,
                    Coaches.coach_Lname,
                    Club_Directory.club_name,
                )
                .outerjoin(Locations, uSkaterConfig.uSkaterRinkPref == Locations.rink_id)
                .outerjoin(Coaches, uSkaterConfig.activeCoach == Coaches.coach_id)
                .outerjoin(Club_Directory, uSkaterConfig.org_Club == Club_Directory.club_id)
                .filter(uSkaterConfig.uSkaterUUID == self.uSkaterUUID)
                .first()
            )

            if not row:
                return {}

            profile = row[0]

            coach_name = None
            if row.coach_Fname or row.coach_Lname:
                coach_name = f"{row.coach_Fname or ''} {row.coach_Lname or ''}".strip()

            ice_config = None
            if profile.uSkaterComboIce:
                equip = (
                    s.query(
                        uSkaterBoots.bootsName,
                        uSkaterBoots.bootsModel,
                        uSkaterBlades.bladesName,
                        uSkaterBlades.bladesModel,
                    )
                    .select_from(uSkateConfig)
                    .join(uSkaterBoots, uSkateConfig.uSkaterBootsID == uSkaterBoots.bootsID)
                    .join(uSkaterBlades, uSkateConfig.uSkaterBladesID == uSkaterBlades.bladesID)
                    .filter(uSkateConfig.sConfigID == profile.uSkaterComboIce)
                    .first()
                )
                if equip:
                    boots = f"{equip.bootsName or ''} {equip.bootsModel or ''}".strip()
                    blades = f"{equip.bladesName or ''} {equip.bladesModel or ''}".strip()
                    parts = [p for p in (boots, blades) if p]
                    ice_config = " / ".join(parts)

        return {
            'date_created': profile.date_created,
            'uSkaterUUID': profile.uSkaterUUID,
            'uSkaterFname': profile.uSkaterFname,
            'uSkaterMname': profile.uSkaterMname,
            'uSkaterLname': profile.uSkaterLname,
            'uSkaterZip': profile.uSkaterZip,
            'uSkaterCity': profile.uSkaterCity,
            'uSkaterState': profile.uSkaterState,
            'uSkaterCountry': profile.uSkaterCountry,
            'uSkaterTZ': profile.uSkaterTZ,
            'uSkaterRoles': profile.uSkaterRoles,
            'uSkaterComboIce': ice_config,
            'uSkaterComboOff': profile.uSkaterComboOff,
            'uSkaterRinkPref': row.rink_name,
            'uSkaterMaintPref': profile.uSkaterMaintPref,
            'activeCoach': coach_name,
            'org_Club': row.club_name,
            'org_Club_Join_Date': profile.org_Club_Join_Date,
            'org_USFSA_number': profile.org_USFSA_number
        }






class uMaintenanceV4:
    """
    Aggregator for maintenance-related metrics (sharpenings, cycles, costs).
    Provides data for both chart visualizations and maintenance detail views.
    """

    def __init__(self, uSkaterUUID, session=None, tz=None):
        self.uSkaterUUID = uSkaterUUID
        self.external_session = session
        self.tz = tz

    def _get_session(self):
        return self.external_session or create_session()

    @currency_usd
    def maint_cost(self):
        """Total maintenance cost across all sharpenings for this skater."""
        with self._get_session() as s:
            return (
                s.query(func.sum(uSkaterMaint.m_cost))
                .filter(uSkaterMaint.uSkaterUUID == self.uSkaterUUID)
                .scalar()
            )

    def maint_clock(self):
        """
        Returns a dict with maintenance cycle status for charting.

        {
            "clock_minutes": preferred sharpening cycle in minutes,
            "active_minutes": minutes since last sharpening,
            "remaining_minutes": remaining until next sharpening
        }
        """
        with self._get_session() as s:
            # Get skater’s preferred sharpening cycle (hours → minutes)
            pref_hours = (
                s.query(uSkaterConfig.uSkaterMaintPref)
                .filter(uSkaterConfig.uSkaterUUID == self.uSkaterUUID)
                .scalar()
            )
            pref_minutes = (pref_hours or 0) * 60

            # Find most recent maintenance record (sharpening event)
            last_maint_date = (
                s.query(func.max(uSkaterMaint.m_date))
                .filter(uSkaterMaint.uSkaterUUID == self.uSkaterUUID)
                .scalar()
            )

            active_minutes = 0
            if last_maint_date:
                # Sum ice_time minutes since that sharpening
                active_minutes = (
                    s.query(func.sum(IceTime.ice_time))
                    .filter(
                        IceTime.uSkaterUUID == self.uSkaterUUID,
                        IceTime.date >= last_maint_date
                    )
                    .scalar()
                    or 0
                )

        return {
            "clock_minutes": minutes_to_hours(lambda: pref_minutes or 0)(),
            "active_minutes": minutes_to_hours(lambda: active_minutes or 0)(),
            "remaining_minutes": minutes_to_hours(lambda: pref_minutes - active_minutes or 0)()
        }
    
    
    def maint_data(self):
        with self._get_session() as session:

            active_config = (
                session.query(uSkaterConfig)
                .filter(uSkaterConfig.uSkaterUUID == self.uSkaterUUID)
                .first()
            )

            skater_config = (
                session.query(uSkateConfig)
                .filter(uSkateConfig.sConfigID == active_config.uSkaterComboIce)
                .first()
            )

            blades = (
                session.query(uSkaterMaint, Locations)
                .join(Locations, uSkaterMaint.m_location == Locations.rink_id)
                .filter(uSkaterMaint.uSkaterUUID == self.uSkaterUUID)
                .filter(uSkaterMaint.uSkaterBladesID == skater_config.uSkaterBladesID)
                .all()
            )
            
        total_minutes = sum(m.m_hours_on or 0 for m, _ in blades)
        total_minutes = minutes_to_hours(lambda: total_minutes)()
        sharpen_count = len(blades)  # each row = one sharpening iteration

        history = [
            {
                "date": utc_to_local(
                    maint.m_date,
                    resolve_tz(loc.rink_tz if loc else None, self.tz)
                ).isoformat() if maint.m_date else None,
                "hours_on": minutes_to_hours(lambda: maint.m_hours_on or 0)(),
                "cost": maint.m_cost,
                "location": loc.rink_name if loc else None,
                "roh": maint.m_roh,
                "notes": maint.m_notes,
            }
            for maint, loc in blades
        ]

        return {
            "meta": {
                "total_hours": total_minutes,
                "sharpenings": sharpen_count,
            },
            "history": history,
        }

    def maint_data_all(self):
        """Sharpening history for every blade the skater owns, grouped by blade.

        Returns a list of blade dicts, each with:
          - blade_name, blade_model, is_active (bool)
          - meta: {total_hours, sharpenings}
          - history: [{date, hours_on, cost, location, roh, notes}, ...]
        Active blade is first in the list.
        """
        with self._get_session() as session:
            profile = (
                session.query(uSkaterConfig)
                .filter(uSkaterConfig.uSkaterUUID == self.uSkaterUUID)
                .first()
            )
            active_blade_id = None
            if profile and profile.uSkaterComboIce:
                combo = (
                    session.query(uSkateConfig.uSkaterBladesID)
                    .filter(uSkateConfig.sConfigID == profile.uSkaterComboIce)
                    .scalar()
                )
                active_blade_id = combo

            all_blades = (
                session.query(uSkaterBlades)
                .filter(uSkaterBlades.uSkaterUUID == self.uSkaterUUID)
                .all()
            )

            results = []
            for blade in all_blades:
                rows = (
                    session.query(uSkaterMaint, Locations)
                    .outerjoin(Locations, uSkaterMaint.m_location == Locations.rink_id)
                    .filter(uSkaterMaint.uSkaterUUID == self.uSkaterUUID)
                    .filter(uSkaterMaint.uSkaterBladesID == blade.bladesID)
                    .order_by(uSkaterMaint.m_date.desc())
                    .all()
                )

                total_min = sum(m.m_hours_on or 0 for m, _ in rows)
                history = [
                    {
                        "date": utc_to_local(
                            m.m_date,
                            resolve_tz(loc.rink_tz if loc else None, self.tz)
                        ).isoformat() if m.m_date else None,
                        "hours_on": minutes_to_hours(lambda m=m: m.m_hours_on or 0)(),
                        "cost": m.m_cost,
                        "location": loc.rink_name if loc else None,
                        "roh": m.m_roh,
                        "notes": m.m_notes,
                    }
                    for m, loc in rows
                ]

                results.append({
                    "blade_name": blade.bladesName,
                    "blade_model": blade.bladesModel,
                    "is_active": blade.bladesID == active_blade_id,
                    "meta": {
                        "total_hours": minutes_to_hours(lambda: total_min)(),
                        "sharpenings": len(rows),
                    },
                    "history": history,
                })

        results.sort(key=lambda b: (not b["is_active"], b["blade_name"] or ""))
        return results