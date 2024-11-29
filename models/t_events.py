from sqlalchemy import Column, Float, Integer, DateTime
from .base import Base


class Events_Competition(Base):
    '''
    This table should describe a competition, though the legacy installation
    isn't clear about what data should be here. Use with caution.

    Likely this data is based on limited experience with USFSA regulations
    '''

    __tablename__ = 'e_competition'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    event_date = Column(DateTime)
    event_type = Column(Integer)
    event_cost = Column(Float)
    event_location = Column(Integer)
    config_id = Column(Integer)
    routine_id = Column(Integer)
    award_level = Column(Integer)
    award_points = Column(Integer)
    uSkaterUUID = Column(Integer)

    def __init__(
        self,
        event_date,
        event_type,
        event_cost,
        event_location,
        config_id,
        routine_id,
        award_level,
        award_points,
        uSkaterUUID,
            ):

        self.event_date = event_date
        self.event_type = event_type
        self.event_cost = event_cost
        self.event_location = event_location
        self.config_id = config_id
        self.routine_id = routine_id
        self.award_level = award_level
        self.award_points = award_points
        self.uSkaterUUID = uSkaterUUID


class Event_Performance(Base):
    '''
    This table should describe any kind of informal or unscanctioned
    performance. Showcases and seasonal shows are a great example of this.

    Currently based on limited USFSA data
    '''

    __tablename__ = 'e_performance'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    performance_date = Column(DateTime)
    performance_type = Column(Integer)
    performance_cost = Column(Float)
    performance_location = Column(Integer)
    config_id = Column(Integer)
    routine_id = Column(Integer)
    award_level = Column(Integer)
    award_points = Column(Integer)
    uSkaterUUID = Column(Integer)

    def __init__(
        self,
        performance_date,
        performance_type,
        performance_cost,
        performance_location,
        config_id,
        routine_id,
        award_level,
        award_points,
        uSkaterUUID,
            ):

        self.performance_date = performance_date
        self.performance_type = performance_type
        self.performance_cost = performance_cost
        self.performance_location = performance_location
        self.config_id = config_id
        self.routine_id = routine_id
        self.award_level = award_level
        self.award_points = award_points
        self.uSkaterUUID = uSkaterUUID


class Event_Test(Base):
    '''
    This table describes any testing done by a skater.
    Currently based on limited USFSA data.
    '''

    __tablename__ = 'e_test'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    test_date = Column(DateTime)
    test_type = Column(Integer)
    test_cost = Column(Float)
    test_location = Column(Integer)
    config_id = Column(Integer)
    routine_id = Column(Integer)
    award_level = Column(Integer)
    award_points = Column(Integer)
    uSkaterUUID = Column(Integer)

    def __init__(
        self,
        test_date,
        test_type,
        test_cost,
        test_location,
        config_id,
        routine_id,
        award_level,
        award_points,
        uSkaterUUID,
            ):

        self.test_date = test_date
        self.test_type = test_type
        self.test_cost = test_cost
        self.test_location = test_location
        self.config_id = config_id
        self.routine_id = routine_id
        self.award_level = award_level
        self.award_points = award_points
        self.uSkaterUUID = uSkaterUUID
