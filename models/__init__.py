# coding=utf-8
import pandas as pd
from sqlalchemy import func
from models.cyberconnect2 import Session, engine

from models.t_ice_time import Ice_Time
from models.t_locations import Locations
from models.t_icetype import IceType
from models.t_coaches import Coaches
from models.t_equip import uSkateConfig, uSkaterBlades, uSkaterBoots


session = Session()


class coaches():

    def add_coaches(coaches):
        for coach in coaches:
            session.add(Coaches(**coach))
            session.commit()
        session.close()


class locations():
    '''
    Everything needed for managing rinks such as but not limited to
    adding rinks, session types, listing rinks by hours or skaters
    and more
    '''

    def add_rink(rinks):
        '''
        Adds a rink to the location table
        '''

        for rink in rinks:
            session.add(Locations(**rink))
            session.commit()
        session.close()

    def add_types(ice_types):
        '''
        Adds a session such as freestyle, public, group class, etc
        '''

        for types in ice_types:
            session.add(IceType(**types))
            session.commit()
        session.close()


class ice_cost():
    def __init__(self, uSkateUUID):
        self.uSkateUUID = uSkateUUID

    def ice_cost(self):
        '''
        Total cost of time on ice, by uSkaterUUID.
        '''

        with Session() as s:
            cost = (
                s.query(func.sum(Ice_Time.ice_cost))
                .where(Ice_Time.uSkaterUUID == self.uSkateUUID)
                .scalar()
                    )

        return cost


class ice_time():
    def __init__(self, uSkaterUUID):
        self.uSkaterUUID = uSkaterUUID

    def ice_time_in_minutes(self):
        '''
        Get all minutes for a skater, by uSkaterUUID.
        '''

        with Session() as s:
            minutes = (
                s.query(func.sum(Ice_Time.ice_time))
                .where(Ice_Time.uSkaterUUID == self.uSkaterUUID)
                .scalar()
                        )
        return minutes

    def ice_time_config_in_minutes(self, uSkaterConfig):
        '''
        Get all minutes for a specific configuration of a skater.
        Requires the uSkaterConfig as an ID to match on.
        '''

        with Session() as s:
            minutes = (
                s.query(func.sum(Ice_Time.ice_time))
                .where(Ice_Time.uSkaterUUID == self.uSkaterUUID)
                .where(Ice_Time.uSkaterConfig == uSkaterConfig)
                .scalar()
                        )
        return minutes


class insert_data():

    def add_bulk_session(ice_session):
        '''
        This should probably be moved to ice_sessions class
        '''

        with Session() as s:
            for session in ice_session:
                s.add(Ice_Time(**session))
                s.commit()
        s.close()


class ice_sessions():

    def list_all(uSkaterUUID):
        '''
        lists all ice sessions of a particular skater via uSkaterUUID
        '''

        with Session() as s:
            all_sessions = (
                s.query(Ice_Time, Locations, IceType)
                .where(Ice_Time.uSkaterUUID == uSkaterUUID)
                .join(Locations, Ice_Time.rink_id == Locations.rink_id)
                .join(IceType, Ice_Time.skate_type == IceType.id)
                .all()
                )

        return all_sessions

    def df_all(uSkaterUUID):
        '''
        Same as list_all(), but returns a pandas dataframe which
        may be the way of the future if we can pass json correctly
        Returns same data as legacy sessions table:
        date, ice session meta, coach meta, rink meta.
        '''

        df = pd.read_sql_query(
            sql=Session().query(
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
                )
            .where(Ice_Time.uSkaterUUID == uSkaterUUID)
            .join(Locations, Ice_Time.rink_id == Locations.rink_id)
            .join(IceType, Ice_Time.skate_type == IceType.id)
            .join(Coaches, Ice_Time.coach_id == Coaches.id)
            .statement, con=engine
        )

        return df


class equipment():
    '''
    Everything related to equipment ...
    '''

    class add():

        def boot(boots):
            '''
            Adds boot meta to the boots table
            '''

            with Session() as s:
                for b in boots:
                    s.add(uSkaterBoots(**b))
                    s.commit()
            s.close()

        def blade(blades):
            '''
            Adds blade meta to the blades table
            '''

            with Session() as s:
                for b in blades:
                    s.add(uSkaterBlades(**b))
                    s.commit()
            s.close()

        def sConfig(config):
            '''
            adds a config that uses the boots and blades specific IDs
            as a key to join on, determines what skate config is currently
            active for a specific uSkaterUUID
            '''

            with Session() as s:
                for c in config:
                    s.add(uSkateConfig(**c))
                    s.commit()
            s.close()

    class list():
        def all_configs(uSkaterUUID):
            '''
            returns a pandas dataframe of all skate config combos
            for a specific uSkaterUUID
            '''

            df = pd.read_sql_query(
                sql=Session()
                .query(
                    uSkateConfig.date_created,
                    uSkaterBoots.bootsModel,
                    uSkaterBoots.bootsName,
                    uSkaterBlades.bladesModel,
                    uSkaterBlades.bladesName
                )
                .where(
                    (uSkateConfig.uSkaterUUID == uSkaterUUID)
                    & (uSkaterBoots.uSkaterUUID == uSkaterUUID)
                    & (uSkaterBlades.uSkaterUUID == uSkaterUUID)
                    )
                .join(
                    uSkaterBoots,
                    uSkateConfig.uSkaterBootsID == uSkaterBoots.bootsID
                    )
                .join(
                    uSkaterBlades,
                    uSkateConfig.uSkaterBladesID == uSkaterBlades.bladesID
                    )
                .distinct()
                .statement, con=engine
            )

            return df

        def active_config(uSkaterUUID):
            '''
            returns a pandas dataframe of only the current skate
            config combo for a specific uSkaterUUID
            '''

            df = pd.read_sql_query(
                sql=Session()
                .query(
                    uSkateConfig.date_created,
                    uSkaterBoots.bootsModel,
                    uSkaterBoots.bootsName,
                    uSkaterBlades.bladesModel,
                    uSkaterBlades.bladesName
                )
                .where(
                    (uSkateConfig.uSkaterUUID == uSkaterUUID)
                    & (uSkateConfig.uConfigActive == 1)
                    & (uSkaterBoots.uSkaterUUID == uSkaterUUID)
                    & (uSkaterBlades.uSkaterUUID == uSkaterUUID)
                    )
                .join(
                    uSkaterBoots,
                    uSkateConfig.uSkaterBootsID == uSkaterBoots.bootsID
                    )
                .join(
                    uSkaterBlades,
                    uSkateConfig.uSkaterBladesID == uSkaterBlades.bladesID
                    )
                .distinct()
                .statement, con=engine
            )

            return df
