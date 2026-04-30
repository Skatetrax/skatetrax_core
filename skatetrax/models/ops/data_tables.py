import pandas as pd
from sqlalchemy import func

from ..cyberconnect2 import create_session, get_engine

from ...utils.tz import utc_to_local, today_in_tz, utc_naive_range_for_inclusive_local_dates, resolve_tz

from ..t_ice_time import Ice_Time
from ..t_locations import Locations
from ..t_icetype import IceType
from ..t_coaches import Coaches
from ..t_equip import uSkateConfig, uSkaterBlades, uSkaterBoots
from ..t_maint import uSkaterMaint


def _convert_dates(df, columns, tz):
    """Apply UTC→local conversion to datetime columns in a DataFrame."""
    if tz is None:
        return df
    for col in columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda d: utc_to_local(d, tz) if d is not None else d)
    return df


def _resolve_tz(row_tz, fallback):
    """Return row_tz when it's a real string, otherwise fallback."""
    if pd.notna(row_tz) and isinstance(row_tz, str):
        return row_tz
    return fallback


class Equipment():

    def skate_configs(uSkaterUUID, session=None):
        '''
        Lists all boot and blade combinations defined for a skater,
        including total ice time (minutes) per config.
        '''
        def _run(sess, engine):
            return pd.read_sql_query(
                sql=sess.query(
                    uSkateConfig.sConfigID,
                    uSkateConfig.date_created,
                    uSkateConfig.sActiveFlag,
                    uSkaterBoots.bootsName,
                    uSkaterBoots.bootsModel,
                    uSkaterBlades.bladesName,
                    uSkaterBlades.bladesModel,
                )
                .where(uSkateConfig.uSkaterUUID == uSkaterUUID)
                .join(uSkaterBoots, uSkateConfig.uSkaterBootsID == uSkaterBoots.bootsID)
                .join(uSkaterBlades, uSkateConfig.uSkaterBladesID == uSkaterBlades.bladesID)
                .statement, con=engine
            )

        if session is not None:
            engine = session.get_bind()
            df = _run(session, engine)
        else:
            with create_session() as sess:
                df = _run(sess, get_engine())

        if df.empty:
            return df

        def _hours(sess, engine):
            return pd.read_sql_query(
                sql=sess.query(
                    Ice_Time.uSkaterConfig.label('sConfigID'),
                    func.coalesce(func.sum(Ice_Time.ice_time), 0).label('hours')
                )
                .filter(Ice_Time.uSkaterUUID == uSkaterUUID)
                .group_by(Ice_Time.uSkaterConfig)
                .statement, con=engine
            )

        if session is not None:
            hours_df = _hours(session, session.get_bind())
        else:
            with create_session() as sess:
                hours_df = _hours(sess, get_engine())

        df = df.merge(hours_df, on='sConfigID', how='left')
        df['hours'] = df['hours'].fillna(0).astype(int)
        df = df.drop(columns=['sConfigID'])
        df = df.sort_values('date_created', ascending=False)

        return df

    def boots(uSkaterUUID, session=None):
        '''Lists all boots for a skater with hours skated per boot.'''
        def _run(sess, engine):
            return pd.read_sql_query(
                sql=sess.query(
                    uSkaterBoots.bootsID,
                    uSkaterBoots.date_created,
                    uSkaterBoots.bootsName,
                    uSkaterBoots.bootsModel,
                    uSkaterBoots.bootsSize,
                    uSkaterBoots.bootsPurchaseAmount,
                )
                .where(uSkaterBoots.uSkaterUUID == uSkaterUUID)
                .statement, con=engine
            )

        if session is not None:
            df = _run(session, session.get_bind())
        else:
            with create_session() as sess:
                df = _run(sess, get_engine())

        if df.empty:
            return df

        def _hours(sess, engine):
            return pd.read_sql_query(
                sql=sess.query(
                    uSkateConfig.uSkaterBootsID.label('bootsID'),
                    func.coalesce(func.sum(Ice_Time.ice_time), 0).label('hours')
                )
                .join(Ice_Time, Ice_Time.uSkaterConfig == uSkateConfig.sConfigID)
                .filter(uSkateConfig.uSkaterUUID == uSkaterUUID)
                .group_by(uSkateConfig.uSkaterBootsID)
                .statement, con=engine
            )

        if session is not None:
            hours_df = _hours(session, session.get_bind())
        else:
            with create_session() as sess:
                hours_df = _hours(sess, get_engine())

        df = df.merge(hours_df, on='bootsID', how='left')
        df['hours'] = df['hours'].fillna(0).astype(int)
        df = df.drop(columns=['bootsID'])
        df = df.sort_values('date_created', ascending=False)

        return df

    def blades(uSkaterUUID, session=None):
        '''Lists all blades for a skater with sharpening count per blade.'''
        def _run(sess, engine):
            return pd.read_sql_query(
                sql=sess.query(
                    uSkaterBlades.bladesID,
                    uSkaterBlades.date_created,
                    uSkaterBlades.bladesName,
                    uSkaterBlades.bladesModel,
                    uSkaterBlades.bladesSize,
                    uSkaterBlades.bladesPurchaseAmount,
                )
                .where(uSkaterBlades.uSkaterUUID == uSkaterUUID)
                .statement, con=engine
            )

        if session is not None:
            df = _run(session, session.get_bind())
        else:
            with create_session() as sess:
                df = _run(sess, get_engine())

        if df.empty:
            return df

        def _maint(sess, engine):
            return pd.read_sql_query(
                sql=sess.query(
                    uSkaterMaint.uSkaterBladesID.label('bladesID'),
                    func.count(uSkaterMaint.id).label('sharpenings')
                )
                .filter(uSkaterMaint.uSkaterUUID == uSkaterUUID)
                .group_by(uSkaterMaint.uSkaterBladesID)
                .statement, con=engine
            )

        if session is not None:
            maint_df = _maint(session, session.get_bind())
        else:
            with create_session() as sess:
                maint_df = _maint(sess, get_engine())

        df = df.merge(maint_df, on='bladesID', how='left')
        df['sharpenings'] = df['sharpenings'].fillna(0).astype(int)
        df = df.drop(columns=['bladesID'])
        df = df.sort_values('date_created', ascending=False)

        return df


class Sessions_Tables():

    def ice_type(session=None):
        '''
        Returns contents of ice_type (lookup) table
        '''
        if session is not None:
            df = pd.read_sql_query(
                sql=session.query(IceType).statement, con=session.get_bind()
            )
        else:
            with create_session() as sess:
                df = pd.read_sql_query(
                    sql=sess.query(IceType).statement, con=get_engine()
                )
        return df
        
        
    def ice_time(uSkaterUUID, tz=None, session=None):
        '''
        lists all ice sessions of a particular skater via uSkaterUUID
        Returns a pandas dataframe containing joined data of:
        date, ice session meta, coach meta, rink meta.

        If tz is provided, session dates are converted from UTC to that
        IANA timezone. When omitted, dates are returned as stored (UTC).
        '''
        def _run(sess, engine):
            return pd.read_sql_query(
                sql=sess.query(
                    Ice_Time.date,
                    Ice_Time.ice_time,
                    Ice_Time.ice_cost,
                    IceType.ice_type,
                    Ice_Time.coach_time,
                    Coaches.coach_Fname,
                    Coaches.coach_Lname,
                    Ice_Time.coach_cost,
                    Locations.rink_name,
                    Locations.rink_city,
                    Locations.rink_state,
                    Locations.rink_tz,
                )
                .where(Ice_Time.uSkaterUUID == uSkaterUUID)
                .outerjoin(Locations, Ice_Time.rink_id == Locations.rink_id)
                .outerjoin(IceType, Ice_Time.skate_type == IceType.ice_type_id)
                .outerjoin(Coaches, Ice_Time.coach_id == Coaches.coach_id)
                .order_by(Ice_Time.date.desc())
                .statement, con=engine
            )

        if session is not None:
            df = _run(session, session.get_bind())
        else:
            with create_session() as sess:
                df = _run(sess, get_engine())

        df['coach'] = df['coach_Fname'].fillna('') + ' ' + df['coach_Lname'].fillna('')
        df = df.drop(columns=['coach_Fname', 'coach_Lname'])

        if not df.empty and (tz or 'rink_tz' in df.columns):
            df['date'] = df.apply(
                lambda row: utc_to_local(row['date'], _resolve_tz(row.get('rink_tz'), tz))
                    if _resolve_tz(row.get('rink_tz'), tz) else row['date'],
                axis=1
            )
        df = df.drop(columns=['rink_tz'], errors='ignore')

        return df

    def ice_time_current_month(uSkaterUUID, tz=None, session=None):
        '''
        lists all ice sessions of a particular skater via uSkaterUUID
        for the current month (interpreted in tz, or UTC when tz is omitted).
        Returns a pandas dataframe containing joined data of:
        date, ice session meta, coach meta, rink meta.
        '''
        today = today_in_tz(tz)
        month_start = today.replace(day=1)
        lo, hi_excl = utc_naive_range_for_inclusive_local_dates(
            month_start, today, resolve_tz(None, tz)
        )

        def _run(sess, engine):
            return pd.read_sql_query(
                sql=sess.query(
                    Ice_Time.date,
                    Ice_Time.ice_time,
                    Ice_Time.ice_cost,
                    IceType.ice_type,
                    Ice_Time.coach_time,
                    Coaches.coach_Fname,
                    Coaches.coach_Lname,
                    Ice_Time.coach_cost,
                    Locations.rink_name,
                    Locations.rink_city,
                    Locations.rink_state,
                    Locations.rink_tz,
                )
                .where(Ice_Time.uSkaterUUID == uSkaterUUID)
                .filter(Ice_Time.date >= lo)
                .filter(Ice_Time.date < hi_excl)
                .outerjoin(Locations, Ice_Time.rink_id == Locations.rink_id)
                .outerjoin(IceType, Ice_Time.skate_type == IceType.ice_type_id)
                .outerjoin(Coaches, Ice_Time.coach_id == Coaches.coach_id)
                .order_by(Ice_Time.date.desc())
                .statement, con=engine
            )

        if session is not None:
            df = _run(session, session.get_bind())
        else:
            with create_session() as sess:
                df = _run(sess, get_engine())

        df['coach'] = df['coach_Fname'].fillna('') + ' ' + df['coach_Lname'].fillna('')
        df = df.drop(columns=['coach_Fname', 'coach_Lname'])

        if not df.empty and (tz or 'rink_tz' in df.columns):
            df['date'] = df.apply(
                lambda row: utc_to_local(row['date'], _resolve_tz(row.get('rink_tz'), tz))
                    if _resolve_tz(row.get('rink_tz'), tz) else row['date'],
                axis=1
            )
        df = df.drop(columns=['rink_tz'], errors='ignore')

        return df

    def active_config(uSkaterUUID, session=None):
        '''
        returns a pandas dataframe of only the current skate
        config combo for a specific uSkaterUUID
        '''
        def _run(sess, engine):
            return pd.read_sql_query(
                sql=sess.query(
                    uSkateConfig.date_created,
                    uSkaterBoots.bootsName,
                    uSkaterBoots.bootsModel,
                    uSkaterBlades.bladesName,
                    uSkaterBlades.bladesModel
                )
                .where(
                    (uSkateConfig.uSkaterUUID == uSkaterUUID)
                    & (uSkateConfig.sActiveFlag == 1)
                )
                .join(uSkaterBoots, uSkateConfig.uSkaterBootsID == uSkaterBoots.bootsID)
                .join(uSkaterBlades, uSkateConfig.uSkaterBladesID == uSkaterBlades.bladesID)
                .statement, con=engine
            )

        if session is not None:
            df = _run(session, session.get_bind())
        else:
            with create_session() as sess:
                df = _run(sess, get_engine())
        return df


class Skating_Locations():

    def rinks(session=None):
        '''
        lists all ice sessions of a particular skater via uSkaterUUID
        Returns a pandas dataframe containing joined data of:
        date, ice session meta, coach meta, rink meta.
        '''
        if session is not None:
            df = pd.read_sql_query(
                sql=session.query(Locations).statement, con=session.get_bind()
            )
        else:
            with create_session() as sess:
                df = pd.read_sql_query(
                    sql=sess.query(Locations).statement, con=get_engine()
                )
        return df


class CoachesTable():
    # future note, we'll need a way to allow contact info to be returned
    # when skater/coach affiliation is established

    def list_coaches(session=None):
        '''
        Returns a dataframe consisting of the data in the coaches table
        Filters out sensitive data, for basic session use
        '''
        if session is not None:
            df = pd.read_sql_query(
                sql=session.query(
                    Coaches.coach_id,
                    Coaches.coach_Fname,
                    Coaches.coach_Lname,
                    Coaches.coach_rate,
                    Coaches.coach_usfsa_id,
                    Coaches.coach_ijs_id
                ).statement, con=session.get_bind()
            )
        else:
            with create_session() as sess:
                df = pd.read_sql_query(
                    sql=sess.query(
                        Coaches.coach_id,
                        Coaches.coach_Fname,
                        Coaches.coach_Lname,
                        Coaches.coach_rate,
                        Coaches.coach_usfsa_id,
                        Coaches.coach_ijs_id
                    ).statement, con=get_engine()
                )
        return df
    
    
class EventsTable():

    def list_competitions(uSkaterUUID, category=None, session=None):
        """Competition history for a skater: one row per entry with parent event context.

        Args:
            uSkaterUUID: skater identifier.
            category: optional string or list of strings to filter by
                EventType.category (e.g. "Competition", ["Showcase", "Exhibition"]).
                When None, all entries are returned regardless of category.
            session: optional external SQLAlchemy session.

        Returns a DataFrame with columns:
            event_id, event_date, entry_date, event_label, event_cost,
            hosting_club, location_name, location_city, location_state,
            event_segment, event_level, placement, field_size, status, video_url
        Ordered by event_date descending (most recent first).
        """
        from ..t_events import SkaterEvent, EventEntry, EventType, EventCost
        from ..t_memberships import Club_Directory
        from ..t_locations import Locations

        def _run(sess, engine):
            cost_sub = (
                sess.query(
                    EventCost.event_id,
                    func.coalesce(
                        func.sum(EventCost.amount * EventCost.quantity), 0
                    ).label("total_cost"),
                )
                .group_by(EventCost.event_id)
                .subquery()
            )

            q = sess.query(
                SkaterEvent.id.label("event_id"),
                SkaterEvent.event_date,
                EventEntry.entry_date,
                SkaterEvent.event_label,
                func.coalesce(cost_sub.c.total_cost, 0).label("event_cost"),
                Club_Directory.club_name.label("hosting_club"),
                Locations.rink_name.label("location_name"),
                Locations.rink_city.label("location_city"),
                Locations.rink_state.label("location_state"),
                EventEntry.event_segment,
                EventEntry.event_level,
                EventEntry.placement,
                EventEntry.field_size,
                EventEntry.status,
                EventEntry.video_url,
            ).join(EventEntry, SkaterEvent.id == EventEntry.event_id
            ).outerjoin(Club_Directory, SkaterEvent.hosting_club == Club_Directory.club_id
            ).outerjoin(Locations, SkaterEvent.event_location == Locations.rink_id
            ).outerjoin(cost_sub, SkaterEvent.id == cost_sub.c.event_id)

            if category is not None:
                cats = [category] if isinstance(category, str) else list(category)
                q = (q.outerjoin(EventType, EventEntry.event_type == EventType.id)
                       .filter(EventType.category.in_(cats)))

            q = (q.filter(SkaterEvent.uSkaterUUID == uSkaterUUID)
                   .order_by(SkaterEvent.event_date.desc()))

            return pd.read_sql_query(sql=q.statement, con=engine)

        if session is not None:
            df = _run(session, session.get_bind())
        else:
            with create_session() as sess:
                df = _run(sess, get_engine())

        return df