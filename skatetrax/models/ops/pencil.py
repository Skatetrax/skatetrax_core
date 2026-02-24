from sqlalchemy import func
from datetime import datetime

from ..cyberconnect2 import Session, engine

from ..t_auth import uAuthTable

from ..t_ice_time import Ice_Time
from ..t_locations import Locations, Punch_cards
from ..t_maint import uSkaterMaint
from ..t_icetype import IceType
from ..t_coaches import Coaches
from ..t_equip import uSkateConfig, uSkaterBlades, uSkaterBoots
from ..t_classes import Skate_School
from ..t_memberships import Club_Directory, Club_Members

from ..t_skaterMeta import uSkaterConfig, uSkaterRoles

session = Session()


class Coach_Data():

    def add_coaches(coaches):
        for coach in coaches:
            try:
                session.add(Coaches(**coach))
                session.commit()
            except Exception as why:
                session.rollback()
                print(why)
        session.close()


class Equipment_Data():

    def add_blades(blades):
        for blade in blades:
            try:
                session.add(uSkaterBlades(**blade))
                session.commit()
            except Exception as why:
                session.rollback()
                print(why)
        session.close()

    def add_boots(boots):
        for boot in boots:
            try:
                session.add(uSkaterBoots(**boot))
                session.commit()
            except Exception as why:
                session.rollback()
                print(why)
        session.close()

    def add_combo(configs):
        for config in configs:
            try:
                session.add(uSkateConfig(**config))
                session.commit()
            except Exception as why:
                session.rollback()
                print(why)
        session.close()

    def add_maintenance(maint_sess):
        for maint in maint_sess:
            try:
                session.add(uSkaterMaint(**maint))
                session.commit()
            except Exception as why:
                session.rollback()
                print(why)
        session.close()


class Ice_Session():

    def add_skate_time(sessions):
        for asession in sessions:
            try:
                session.add(Ice_Time(**asession))
                session.commit()
            except Exception as why:
                session.rollback()
                print(why)
        session.close()

    def add_skate_school(classes):
        for aclass in classes:
            try:
                session.add(Skate_School(**aclass))
                session.commit()
            except Exception as why:
                session.rollback()
                print(why)
        session.close()


class Location_Data():

    def add_ice_type(types):
        for ice_type in types:
            try:
                session.add(IceType(**ice_type))
                session.commit()
            except Exception as why:
                session.rollback()
                print(why)
        session.close()

    def add_ice_rink(rinks):
        for rink in rinks:
            try:
                session.add(Locations(**rink))
                session.commit()
            except Exception as why:
                session.rollback()
                print(why)
        session.close()
        
    def add_punchcard(cards):
        for card in cards:
            try:
                session.add(Punch_cards(**card))
                session.commit()
            except Exception as why:
                session.rollback()
                print(why)
        session.close()


class User_Data():

    def add_skater(skater_data):
        for data in skater_data:
            try:
                session.add(uSkaterConfig(**data))
                session.commit()
            except Exception as why:
                session.rollback()
                print(why)
        session.close()

    def add_skater_roles(role_data):
        for data in role_data:
            try:
                session.add(uSkaterRoles(**data))
                session.commit()
            except Exception as why:
                session.rollback()
                print(why)
        session.close()
        

class Club_Data():
    
    def add_club(club_data):
        for data in club_data:
            try:
                session.add(Club_Directory(**data))
                session.commit()
            except Exception as why:
                session.rollback()
                print(why)
        session.close()
        

    def add_member(member_data):
        for data in member_data:
            try:
                session.add(Club_Members(**data))
                session.commit()
            except Exception as why:
                session.rollback()
                print(why)
        session.close()
        
### Incoming Changes from Legacy

class AddSession:
    def __init__(self, db_session):
        """Store the SQLAlchemy session."""
        self.db_session = db_session

    def __call__(self, data):
        """
        Insert a new Ice_Time row.

        Args:
            data (dict): Keys must match Ice_Time columns.
        Returns:
            Ice_Time: The newly created row object.
        """
        new_row = Ice_Time(**data)

        self.db_session.add(new_row)
        self.db_session.commit()
        self.db_session.refresh(new_row)

        return new_row
