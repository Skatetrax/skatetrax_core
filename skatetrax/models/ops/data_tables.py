import pandas as pd
from sqlalchemy import func

from ..cyberconnect2 import Session, engine

from ...utils.common import Timelines
from ...utils.tz import utc_to_local

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


session = Session()


class Equipment():

    def skate_configs(uSkaterUUID):
        '''
        Lists all boot and blade combinations defined for a skater,
        including total ice time (minutes) per config.
        '''

        df = pd.read_sql_query(
            sql=Session().query(
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

        if df.empty:
            return df

        hours_df = pd.read_sql_query(
            sql=Session().query(
                Ice_Time.uSkaterConfig.label('sConfigID'),
                func.coalesce(func.sum(Ice_Time.ice_time), 0).label('hours')
                )
            .filter(Ice_Time.uSkaterUUID == uSkaterUUID)
            .group_by(Ice_Time.uSkaterConfig)
            .statement, con=engine
        )

        df = df.merge(hours_df, on='sConfigID', how='left')
        df['hours'] = df['hours'].fillna(0).astype(int)
        df = df.drop(columns=['sConfigID'])
        df = df.sort_values('date_created', ascending=False)

        return df

    def boots(uSkaterUUID):
        '''Lists all boots for a skater with hours skated per boot.'''
        df = pd.read_sql_query(
            sql=Session().query(
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

        if df.empty:
            return df

        hours_df = pd.read_sql_query(
            sql=Session().query(
                uSkateConfig.uSkaterBootsID.label('bootsID'),
                func.coalesce(func.sum(Ice_Time.ice_time), 0).label('hours')
                )
            .join(Ice_Time, Ice_Time.uSkaterConfig == uSkateConfig.sConfigID)
            .filter(uSkateConfig.uSkaterUUID == uSkaterUUID)
            .group_by(uSkateConfig.uSkaterBootsID)
            .statement, con=engine
        )

        df = df.merge(hours_df, on='bootsID', how='left')
        df['hours'] = df['hours'].fillna(0).astype(int)
        df = df.drop(columns=['bootsID'])
        df = df.sort_values('date_created', ascending=False)

        return df

    def blades(uSkaterUUID):
        '''Lists all blades for a skater with sharpening count per blade.'''
        df = pd.read_sql_query(
            sql=Session().query(
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

        if df.empty:
            return df

        maint_df = pd.read_sql_query(
            sql=Session().query(
                uSkaterMaint.uSkaterBladesID.label('bladesID'),
                func.count(uSkaterMaint.id).label('sharpenings')
                )
            .filter(uSkaterMaint.uSkaterUUID == uSkaterUUID)
            .group_by(uSkaterMaint.uSkaterBladesID)
            .statement, con=engine
        )

        df = df.merge(maint_df, on='bladesID', how='left')
        df['sharpenings'] = df['sharpenings'].fillna(0).astype(int)
        df = df.drop(columns=['bladesID'])
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
            .outerjoin(Locations, Ice_Time.rink_id == Locations.rink_id)
            .outerjoin(IceType, Ice_Time.skate_type == IceType.ice_type_id)
            .outerjoin(Coaches, Ice_Time.coach_id == Coaches.coach_id)
            .order_by(Ice_Time.date.desc())
            .statement, con=engine
        )

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
            .outerjoin(Locations, Ice_Time.rink_id == Locations.rink_id)
            .outerjoin(IceType, Ice_Time.skate_type == IceType.ice_type_id)
            .outerjoin(Coaches, Ice_Time.coach_id == Coaches.coach_id)
            .order_by(Ice_Time.date.desc())
            .statement, con=engine
        )

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

    def active_config(uSkaterUUID):
        '''
        returns a pandas dataframe of only the current skate
        config combo for a specific uSkaterUUID
        '''

        df = pd.read_sql_query(
            sql=Session()
            .query(
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