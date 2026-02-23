from sqlalchemy import func, select
from datetime import date
import calendar


from ...models.cyberconnect2 import Session
from ...utils.timeframe_generator import TIMEFRAMES
from ...utils.common import minutes_to_hours, currency_usd
from ...utils.tz import today_in_tz, utc_to_local, resolve_tz

from ..t_equip import uSkateConfig, uSkaterBlades, uSkaterBoots
from ..t_skaterMeta import uSkaterConfig
from ..t_maint import uSkaterMaint
from ..t_ice_time import Ice_Time as IceTime
from ..t_locations import Locations


class SkaterAggregates:
    """
    Aggregator for skater metrics including ice_time, coach_time,
    costs, and now group sessions.
    """
    GROUP_SESSION_IDS = ["db32094e-9b0d-42a5-b87f-cd47729b6c65"]
    COMPETITION_IDS = ["7a3b3441-04d6-4b5a-afb6-eb556022c2e7",
                       "88f87085-927d-4b77-b1c9-77d6de7c2d28"]


    def __init__(self, uSkaterUUID, session=None, tz=None):
        self.uSkaterUUID = uSkaterUUID
        self.external_session = session
        self.tz = tz


    def _get_session(self):
        return self.external_session or Session()


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


    @minutes_to_hours
    def group_time(self, timeframe=None):
        from ..t_ice_time import Ice_Time
        start, end = self._resolve_timeframe(timeframe)
        return self.aggregate(Ice_Time, "ice_time", start, end, ice_type_ids=self.GROUP_SESSION_IDS)


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
            "ice_time",               # still summing ice_time minutes
            start,
            end,
            ice_type_ids=self.GROUP_SESSION_IDS
        )


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

        data = {"months": [], "ice_time": [], "coach_time": [], "group_sessions": [], "competitions": []}

        for year, month, month_name in months:
            start = date(year, month, 1)
            end_day = calendar.monthrange(year, month)[1]
            end = date(year, month, end_day)

            ice = self.aggregate(Ice_Time, "ice_time", start, end)
            coach = self.aggregate(Ice_Time, "coach_time", start, end)
            group = self.aggregate(Ice_Time, "ice_time", start, end, ice_type_ids=self.GROUP_SESSION_IDS)

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
            data["coach_time"].append(minutes_to_hours_float(coach))
            data["group_sessions"].append(minutes_to_hours_float(group))
            data["competitions"].append(comp_flag)

        return data


class Equipment():

    def config_active(uSkaterUUID):
        config = UserMeta.skater_config_active_ice(uSkaterUUID)

        with Session() as s:
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
                .where(uSkateConfig.sConfigID == config)
                .one()
            )
        return data._asdict()


class UserMeta:
    def __init__(self, uSkaterUUID, session=None):
        self.uSkaterUUID = uSkaterUUID
        self.external_session = session

    def _get_session(self):
        return self.external_session or Session()

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
        profile = self.skater_profile()
        if not profile:
            return {}
        return {
            'date_created':  profile.date_created,
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
            'uSkaterComboIce': profile.uSkaterComboIce,
            'uSkaterComboOff': profile.uSkaterComboOff,
            'uSkaterRinkPref': profile.uSkaterRinkPref,
            'uSkaterMaintPref': profile.uSkaterMaintPref,
            'activeCoach': profile.activeCoach,
            'org_Club': profile.org_Club,
            'org_Club_Join_Date': profile.org_Club_Join_Date,
            'org_USFSA_number':profile.org_USFSA_number
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
        return self.external_session or Session()

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