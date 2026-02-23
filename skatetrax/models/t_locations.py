from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, Float, UUID
from sqlalchemy.orm import mapped_column, Mapped
from uuid import uuid4, UUID as UUIDV4
from datetime import datetime, timezone
from .base import Base


class Locations(Base):
    '''
    This table tracks basic rink data, used as a foreign for
    joining against rink_id on ice_time table.

    If IceMaker is running, it can also drop its data here
    '''

    __tablename__ = 'locations'
    __table_args__ = {'extend_existing': True}

    rink_id: Mapped[UUIDV4] = mapped_column(primary_key=True, default=uuid4)
    rink_name = Column(String)
    rink_address = Column(String)
    rink_city = Column(String)
    rink_state = Column(String)
    rink_country = Column(String)
    rink_zip = Column(String, nullable=False)
    rink_url = Column(String)
    rink_phone = Column(String)
    rink_tz = Column(String, nullable=True)
    data_source = Column(String)
    date_created = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __init__(
        self,
        rink_id,
        rink_name,
        rink_address,
        rink_city,
        rink_state,
        rink_country,
        rink_zip,
        rink_url,
        rink_phone,
        rink_tz=None,
        data_source=None,
        date_created=None
            ):

        self.rink_id = rink_id
        self.rink_name = rink_name
        self.rink_address = rink_address
        self.rink_city = rink_city
        self.rink_state = rink_state
        self.rink_country = rink_country
        self.rink_zip = rink_zip
        self.rink_url = rink_url
        self.rink_phone = rink_phone
        self.rink_tz = rink_tz
        self.data_source = data_source
        self.date_created = date_created

class Punch_cards(Base):
    '''
    This table tracks punch cards if rinks have them.  In some cases, a rink
    may allow one punch for unlimited minutes or one punch may be for a set
    amount of time such as 30 minutes or an hour.

    This data is to assist in knowing how much money has been spent on
    cards/time and how many punches remain on the card. Allows cards to be based
    on skate sessions types already listed in the ice_type table and locations 
    already in the locations table.
    '''

    __tablename__ = 'punch_cards'
    __table_args__ = {'extend_existing': True}
    
    card_id: Mapped[UUIDV4] = mapped_column(primary_key=True, default=uuid4)
    card_type = Column(UUID, ForeignKey("ice_type.ice_type_id", ondelete='CASCADE'))
    card_cost = Column(Float)
    punches_total = Column(Integer)
    punch_session_minutes = Column(Integer)  # how many minutes 1 punch is worth
    purchase_date = Column(DateTime)
    expiration_date = Column(DateTime, nullable=True)
    rink_id = Column(UUID, ForeignKey("locations.rink_id", ondelete='CASCADE'))
    uSkaterUUID = Column(UUID, ForeignKey("uSkaterConfig.uSkaterUUID", ondelete='CASCADE'))
    
    def __init__(
        self,
        card_type,
        card_cost,
        punches_total,
        punch_session_minutes,
        purchase_date,
        expiration_date,
        rink_id,
        uSkaterUUID
            ):

        self.card_type = card_type
        self.punches_total = punches_total
        self.card_cost = card_cost
        self.punch_session_minutes = punch_session_minutes
        self.purchase_date = purchase_date
        self.expiration_date = expiration_date
        self.rink_id = rink_id
        self.uSkaterUUID = uSkaterUUID


class Punched_Sessions(Base):
    '''
    Connects sessions marked as punched based from ice_time and matches them to a specific card.
    '''

    __tablename__ = 'punched_sessions'
    __table_args__ = {'extend_existing': True}
    
    id: Mapped[UUIDV4] = mapped_column(primary_key=True, default=uuid4)
    punchcard_id = Column(UUID, ForeignKey("punch_cards.card_id", ondelete='CASCADE'))
    session_id = Column(Integer, ForeignKey("ice_time.ice_time_id", ondelete='CASCADE'))
    datetime_punch = Column(DateTime)
    punches_used = Column(Integer)
    notes =  Column(String, nullable=True)
    
    def __init__(
        self,
        punchcard_id,
        session_id,
        datetime_punch,
        punches_used,
        notes
        ):
        
        self.punchcard_id = punchcard_id
        self.session_id = session_id
        self.datetime_punch = datetime_punch
        self.punches_used = punches_used
        self.notes = notes