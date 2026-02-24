from sqlalchemy import Column, Float, Integer, DateTime, String, ForeignKey, UUID
from sqlalchemy.orm import mapped_column, Mapped
from uuid import uuid4, UUID as UUIDV4
from .base import Base


class Event_Test(Base):
    '''
    This table is used to describe a skater's test entries, the Who, What, Where, Results
    for a test.  
    '''

    __tablename__ = 'e_tests'
    __table_args__ = {'extend_existing': True}

    id: Mapped[UUIDV4] = mapped_column(primary_key=True, default=uuid4)

    test_cost = Column(Float)
    test_label = Column(String)
    test_level = Column(String)
    test_type =  Column(UUID, ForeignKey("e_competition_types.id", ondelete='CASCADE'))
    test_results = Column(String)

    test_date = Column(DateTime)
    test_location = Column(UUID, ForeignKey("locations.rink_id", ondelete='CASCADE'))
    
    uSkaterUUID = Column(UUID, ForeignKey("uSkaterConfig.uSkaterUUID", ondelete='CASCADE'))
    uSkaterConfig = Column(UUID, ForeignKey("uSkateConfig.sConfigID", ondelete='CASCADE'))


    def __init__(
        self,
        test_date,
        test_type,
        test_cost,
        test_label,
        test_level,
        test_location,
        test_results,
        uSkaterConfig,
        uSkaterUUID,
            ):

        self.test_date = test_date
        self.test_type = test_type
        self.test_cost = test_cost
        self.test_label = test_label
        self.test_level = test_level
        self.test_location = test_location
        self.test_results = test_results
        self.uSkaterConfig = uSkaterConfig
        self.uSkaterUUID = uSkaterUUID


    def __repr__(self):
        return f"<Event(label={self.test_label}, date={self.test_date}, level={self.test_level})>"
