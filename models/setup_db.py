from models import coaches, locations, insert_data, equipment
from models.cyberconnect2 import engine
from datetime import datetime, timezone
from .base import Base

# import table models to be created
# start with basic needs for functionality
from .t_ice_time import Ice_Time
from .t_icetype import IceType
from .t_locations import Locations, Punch_cards
from .t_skaterMeta import uSkaterConfig

# items for configuring skates, cost of gear
from .t_equip import uSkateConfig, uSkaterBlades, uSkaterBoots, uSkaterEquipManifest

# coaching data
from .t_coaches import Coaches

# maintenance
from .t_maint import uSkaterMaint

# memberships (USFSA)
from .t_memberships import Club_Membership

# camps, LTS, multiweek series
from .t_classes import Skate_Camp, Skate_School

# competitions, tests, etc
from .t_events import Event_Test, Events_Competition, Event_Performance

# last, import supporting tables for things like notes, videos
from .t_journal import Journal_Notes, Journal_Videos


date_created = datetime.now(timezone.utc)

if __name__ == "__main__":
    Base.metadata.create_all(engine)

    # we know that some tables need default starting data for all users
    ice_types = [
        {'type_id': 1, 'ice_type': 'Free Style (Walk On)'},
        {'type_id': 2, 'ice_type': 'Public'},
        {'type_id': 3, 'ice_type': 'Coaching Session'},
        {'type_id': 4, 'ice_type': 'Competition'},
        {'type_id': 5, 'ice_type': 'Performance'},
        {'type_id': 6, 'ice_type': 'Club Ice'},
        {'type_id': 7, 'ice_type': 'Group Class'},
        {'type_id': 8, 'ice_type': 'Free Style (Punch Card)'},
        {'type_id': 9, 'ice_type': 'Off Ice - Concrete or Asphalt'},
        {'type_id': 10, 'ice_type': 'Off Ice - Rink'}
    ]

    locations.add_types(ice_types)

    coaches.add_coaches([{'coach_Fname': '-', 'coach_Lname': '-', 'coach_rate': '0', 'uSkaterUUID': 0}])

# to create, run: python -m models.setup_db

# this script is a complete mess. PEP8 complains about the imports, which are all over the place.
# note sure how to address this, if you're reading this - I sincerely wish it was better. :)
