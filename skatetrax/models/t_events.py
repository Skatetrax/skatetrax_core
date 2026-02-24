from sqlalchemy import Column, Float, Integer, DateTime, String, ForeignKey, UUID
from sqlalchemy.orm import mapped_column, Mapped
from uuid import uuid4, UUID as UUIDV4
from .base import Base


class CompetitionType(Base):
    """
    This table should hold various types of competitions. This is not to be confused with
    what competitions a skater has performed at/in.  Currently, this is a hand curated list
    unless there is ever a chance that we can scrape that data from another source.
    
    Starting options:
    Showcase - No Governing Body
    Competition - No Governing Body
    Competition - USFSA
    Competition - IJS
    """

    __tablename__ = 'e_competition_types'
    __table_args__ = {'extend_existing': True}
    
    id: Mapped[UUIDV4] = mapped_column(primary_key=True, default=uuid4)
    label = Column(String)    
    governing_body = Column(String)    

    def __init__(
        self,
        label,
        governing_body
            ):

        self.label = label
        self.governing_body = governing_body

    def __repr__(self):
        return f"<CompetitionType(name={self.label}, governing_body={self.governing_body})>"


class Events_Competition(Base):
    '''
    This table is for recording the data that describes a skater's specific performance.
    For instance, if Ashley was going to compete at Eastern Regionals, this would contain
    When and Where its happening, by who, how much it costs, what config was used.
    In the future we can include hosting club and maybe a routine identifier.
    Currently, this should join on e_competition_type table for expanded information
    '''

    __tablename__ = 'e_competition'
    __table_args__ = {'extend_existing': True}

    id: Mapped[UUIDV4] = mapped_column(primary_key=True, default=uuid4)

    event_cost = Column(Float)
    event_label = Column(String)
    event_level = Column(String)
    event_type = Column(UUID, ForeignKey("e_competition_types.id", ondelete='CASCADE'))
    event_results = Column(String)

    event_date = Column(DateTime)
    event_location = Column(UUID, ForeignKey("locations.rink_id", ondelete='CASCADE'))
    
    uSkaterUUID = Column(UUID, ForeignKey("uSkaterConfig.uSkaterUUID", ondelete='CASCADE'))
    uSkaterConfig = Column(UUID, ForeignKey("uSkateConfig.sConfigID", ondelete='CASCADE'))

    def __init__(
        self,
        event_date,
        event_type,
        event_cost,
        event_label,
        event_level,
        event_results,
        event_location,
        uSkaterConfig,
        uSkaterUUID,
            ):

        self.event_date = event_date
        self.event_type = event_type
        self.event_cost = event_cost
        self.event_label = event_label
        self.event_level = event_level
        self.event_results = event_results
        self.event_location = event_location
        self.uSkaterConfig = uSkaterConfig
        self.uSkaterUUID = uSkaterUUID


    def __repr__(self):
        return f"<Event(label={self.event_label}, date={self.event_date}, level={self.event_level})>"
