from sqlalchemy import Column, DateTime, Integer, String, Float
from .base import Base


class Locations(Base):
    '''
    This table tracks basic rink data, used as a foreign for
    joining against rink_id on ice_time table.

    If IceMaker is running, it can also drop its data here
    '''

    __tablename__ = 'locations'
    __table_args__ = {'extend_existing': True}

    rink_id = Column(Integer, primary_key=True)
    rink_name = Column(String)
    rink_address = Column(String)
    rink_city = Column(String)
    rink_state = Column(String)
    rink_country = Column(String)
    rink_url = Column(String)
    rink_phone = Column(String)
    data_source = Column(String)
    date_created = Column(DateTime)

    def __init__(
        self,
        rink_id,
        rink_name,
        rink_address,
        rink_city,
        rink_state,
        rink_country,
        rink_url,
        rink_phone,
        data_source,
        date_created
            ):

        self.rink_id = rink_id
        self.rink_name = rink_name
        self.rink_address = rink_address
        self.rink_city = rink_city
        self.rink_state = rink_state
        self.rink_country = rink_country
        self.rink_url = rink_url
        self.rink_phone = rink_phone
        self.data_source = data_source
        self.date_created = date_created


class Punch_cards(Base):
    '''
    This table tracks punch cards if rinks have them.  In some cases, a rink
    may allow one punch for unlimited minutes or one punch may be for a set
    amount of time such as 30 minutes or an hour.

    This data is to assist in knowing how much money has been spent on
    cards/time and how many punches remain on the card.
    '''

    __tablename__ = 'punch_cards'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    date_created = Column(DateTime)
    punch_time = Column(Integer)
    punch_cost = Column(Float)
    punch_location = Column(Integer)
    uSkaterUUID = Column(Integer)

    def __init__(
        self,
        date_created,
        punch_time,
        punch_cost,
        punch_location,
        uSkaterUUID
            ):

        self.date_created = date_created
        self.punch_time = punch_time
        self.punch_cost = punch_cost
        self.punch_location = punch_location
        self.uSkaterUUID = uSkaterUUID
