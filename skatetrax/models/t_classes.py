from sqlalchemy import Column, String, Integer, DateTime, Float, UUID, ForeignKey
from .base import Base


class Skate_Camp(Base):
    '''
    This table tracks meta data regarding a skate camp.
    Currently mostly used for cost tracking but will
    likely evovle into something useful later.
    '''

    __tablename__ = 'classes_camp'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    location_id = Column(UUID, ForeignKey("locations.rink_id", ondelete='CASCADE'))
    camp_cost = Column(Float)
    camp_name = Column(String)
    date_start = Column(DateTime)
    date_end = Column(DateTime)
    uSkaterUUID = Column(UUID, ForeignKey("uSkaterConfig.uSkaterUUID", ondelete='CASCADE'))

    def __init__(
        self,
        location_id,
        camp_cost,
        camp_name,
        date_start,
        date_end,
        uSkaterUUID
            ):

        self.location_id = location_id
        self.camp_cost = camp_cost
        self.camp_name = camp_name
        self.date_start = date_start
        self.date_end = date_end
        self.uSkaterUUID = uSkaterUUID


class Skate_School(Base):
    '''
    This table tracks things like LearnToSkate classes and the relevant
    metadata, used mostly for cost tracking at this time
    '''

    __tablename__ = 'classes_school'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    location_id = Column(UUID, ForeignKey("locations.rink_id", ondelete='CASCADE'))
    class_cost = Column(Float)
    class_name = Column(String)
    date_start = Column(DateTime)
    date_end = Column(DateTime)
    uSkaterUUID = Column(UUID, ForeignKey("uSkaterConfig.uSkaterUUID", ondelete='CASCADE'))

    def __init__(
        self,
        location_id,
        class_cost,
        class_name,
        date_start,
        date_end,
        uSkaterUUID
            ):

        self.location_id = location_id
        self.class_cost = class_cost
        self.class_name = class_name
        self.date_start = date_start
        self.date_end = date_end
        self.uSkaterUUID = uSkaterUUID
