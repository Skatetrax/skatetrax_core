import pandas as pd
from ..cyberconnect2 import Session, engine

from ...utils.common import Timelines
from ...utils.tz import utc_to_local

from ..t_ice_time import Ice_Time
from ..t_locations import Locations
from ..t_icetype import IceType
from ..t_coaches import Coaches
from ..t_equip import uSkateConfig, uSkaterBlades, uSkaterBoots


def _convert_dates(df, columns, tz):
    """Apply UTC→local conversion to datetime columns in a DataFrame."""
    if tz is None:
        return df
    for col in columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda d: utc_to_local(d, tz) if d is not None else d)
    return df


session = Session()


class Equipment():

    def skate_configs(uSkaterUUID):
        '''
        Lists all boot and blade combinations defined for a skater
        '''

        df = pd.read_sql_query(
            sql=Session().query(
                uSkateConfig.date_created,
                uSkaterBoots.bootsName,
                uSkaterBoots.bootsModel,
                uSkaterBlades.bladesName,
                uSkaterBlades.bladesModel,
                uSkateConfig.sConfigID
                )
            .where(uSkateConfig.uSkaterUUID == uSkaterUUID)
            .join(
                uSkaterBoots,
                uSkateConfig.uSkaterBootsID == uSkaterBoots.bootsID
                  )
            .join(
                uSkaterBlades,
                uSkateConfig.uSkaterBladesID == uSkaterBlades.bladesID
                  )
            .statement, con=engine
            )

        df['hours'] = df.apply(lambda x: Sessions_Time.ice_time_config_in_minutes(uSkaterUUID, x['sConfigID']), axis=1)
        df = df.drop(columns=['sConfigID'])
        df = df.sort_values('date_created', ascending=False)

        return df


class Sessions_Tables():

    def ice_type():
        '''
        Returns contents of ice_type (lookup) table
        '''

        df = pd.read_sql_query(
            sql=Session().query(
                    IceType
                )
            .statement, con=engine
        )
    
        return df
        
        
    def ice_time(uSkaterUUID, tz=None):
        '''
        lists all ice sessions of a particular skater via uSkaterUUID
        Returns a pandas dataframe containing joined data of:
        date, ice session meta, coach meta, rink meta.

        If tz is provided, session dates are converted from UTC to that
        IANA timezone. When omitted, dates are returned as stored (UTC).
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
                Locations.rink_tz,
                )
            .where(Ice_Time.uSkaterUUID == uSkaterUUID)
            .join(Locations, Ice_Time.rink_id == Locations.rink_id)
            .join(IceType, Ice_Time.skate_type == IceType.ice_type_id)
            .join(Coaches, Ice_Time.coach_id == Coaches.uSkaterUUID)
            .statement, con=engine
        )

        df['coach'] = df['coach_Fname'].fillna('') + ' ' + df['coach_Lname'].fillna('')
        df = df.drop(columns=['coach_Fname', 'coach_Lname'])

        if tz or df.get('rink_tz') is not None:
            df['date'] = df.apply(
                lambda row: utc_to_local(row['date'], row.get('rink_tz') or tz),
                axis=1
            )
        df = df.drop(columns=['rink_tz'], errors='ignore')

        return df

    def ice_time_current_month(uSkaterUUID, tz=None):
        '''
        lists all ice sessions of a particular skater via uSkaterUUID
        for the current month.
        Returns a pandas dataframe containing joined data of:
        date, ice session meta, coach meta, rink meta.
        '''
        tl = Timelines.current_month(tz=tz)

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
                Locations.rink_tz,
                )
            .where(Ice_Time.uSkaterUUID == uSkaterUUID)
            .filter(Ice_Time.date >= tl['last'])
            .filter(Ice_Time.date <= tl['first'])
            .join(Locations, Ice_Time.rink_id == Locations.rink_id)
            .join(IceType, Ice_Time.skate_type == IceType.ice_type_id)
            .join(Coaches, Ice_Time.coach_id == Coaches.uSkaterUUID)
            .statement, con=engine
        )

        df['coach'] = df['coach_Fname'].fillna('') + ' ' + df['coach_Lname'].fillna('')
        df = df.drop(columns=['coach_Fname', 'coach_Lname'])

        if tz or df.get('rink_tz') is not None:
            df['date'] = df.apply(
                lambda row: utc_to_local(row['date'], row.get('rink_tz') or tz),
                axis=1
            )
        df = df.drop(columns=['rink_tz'], errors='ignore')

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


class Skating_Locations():

    def rinks():
        '''
        lists all ice sessions of a particular skater via uSkaterUUID
        Returns a pandas dataframe containing joined data of:
        date, ice session meta, coach meta, rink meta.
        '''

        df = pd.read_sql_query(
            sql=Session().query(
                Locations
                )
            .statement, con=engine
        )

        return df


class CoachesTable():
    # future note, we'll need a way to allow contact info to be returned
    # when skater/coach affiliation is established
    
    def list_coaches():
        '''
        Returns a dataframe consisting of the data in the coaches table
        Filters out sensitive data, for basic session use
        '''
        
        df = pd.read_sql_query(
            sql=Session().query(
                Coaches.coach_id,
                Coaches.coach_Fname,
                Coaches.coach_Lname,
                Coaches.coach_rate,
                Coaches.coach_usfsa_id,
                Coaches.coach_ijs_id
                )
            .statement, con=engine
        )
    
        return df