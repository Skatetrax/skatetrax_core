from sqlalchemy import func
from datetime import datetime

from ..cyberconnect2 import create_session

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

class Coach_Data():

    def add_coaches(coaches):
        with create_session() as session:
            for coach in coaches:
                try:
                    session.add(Coaches(**coach))
                    session.commit()
                except Exception as why:
                    session.rollback()
                    print(why)


class Equipment_Data():

    def add_blades(blades):
        with create_session() as session:
            for blade in blades:
                try:
                    session.add(uSkaterBlades(**blade))
                    session.commit()
                except Exception as why:
                    session.rollback()
                    print(why)

    def add_boots(boots):
        with create_session() as session:
            for boot in boots:
                try:
                    session.add(uSkaterBoots(**boot))
                    session.commit()
                except Exception as why:
                    session.rollback()
                    print(why)

    def add_combo(configs):
        with create_session() as session:
            for config in configs:
                try:
                    session.add(uSkateConfig(**config))
                    session.commit()
                except Exception as why:
                    session.rollback()
                    print(why)

    def add_maintenance(maint_sess):
        with create_session() as session:
            for maint in maint_sess:
                try:
                    session.add(uSkaterMaint(**maint))
                    session.commit()
                except Exception as why:
                    session.rollback()
                    print(why)


class Ice_Session():

    def add_skate_time(sessions):
        with create_session() as session:
            for asession in sessions:
                try:
                    session.add(Ice_Time(**asession))
                    session.commit()
                except Exception as why:
                    session.rollback()
                    print(why)

    def add_skate_school(classes):
        with create_session() as session:
            for aclass in classes:
                try:
                    session.add(Skate_School(**aclass))
                    session.commit()
                except Exception as why:
                    session.rollback()
                    print(why)


class Location_Data():

    def add_ice_type(types):
        with create_session() as session:
            for ice_type in types:
                try:
                    session.add(IceType(**ice_type))
                    session.commit()
                except Exception as why:
                    session.rollback()
                    print(why)

    def add_ice_rink(rinks):
        with create_session() as session:
            for rink in rinks:
                try:
                    session.add(Locations(**rink))
                    session.commit()
                except Exception as why:
                    session.rollback()
                    print(why)

    def add_punchcard(cards):
        with create_session() as session:
            for card in cards:
                try:
                    session.add(Punch_cards(**card))
                    session.commit()
                except Exception as why:
                    session.rollback()
                    print(why)


class User_Data():

    def add_skater(skater_data):
        with create_session() as session:
            for data in skater_data:
                try:
                    session.add(uSkaterConfig(**data))
                    session.commit()
                except Exception as why:
                    session.rollback()
                    print(why)

    def add_skater_roles(role_data):
        with create_session() as session:
            for data in role_data:
                try:
                    session.add(uSkaterRoles(**data))
                    session.commit()
                except Exception as why:
                    session.rollback()
                    print(why)


class Club_Data():

    def add_club(club_data):
        with create_session() as session:
            for data in club_data:
                try:
                    session.add(Club_Directory(**data))
                    session.commit()
                except Exception as why:
                    session.rollback()
                    print(why)

    def add_member(member_data):
        with create_session() as session:
            for data in member_data:
                try:
                    session.add(Club_Members(**data))
                    session.commit()
                except Exception as why:
                    session.rollback()
                    print(why)
        
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
