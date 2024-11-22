from sqlalchemy import Column, DateTime, Integer, Float
from .cyberconnect2 import Base


class Ice_Time(Base):
    __tablename__ = 'ice_time'

    ice_time_id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    ice_time = Column(Integer)
    ice_cost = Column(Float)
    skate_type = Column(Integer)
    coach_time = Column(Integer)
    coach_id = Column(Integer)
    coach_cost = Column(Float)
    has_video = Column(Integer)
    has_notes = Column(Integer)
    rink_id = Column(Integer)
    uSkaterUUID = Column(Integer)
    uSkaterConfig = Column(Integer)
    uSkaterType = Column(Integer)

    def __init__(
        self,
        date,
        ice_time,
        ice_cost,
        skate_type,
        coach_time,
        coach_id,
        coach_cost,
        has_video,
        has_notes,
        rink_id,
        uSkaterUUID,
        uSkaterConfig,
        uSkaterType
            ):

        self.date = date
        self.ice_time = ice_time
        self.ice_cost = ice_cost
        self.skate_type = skate_type
        self.coach_time = coach_time
        self.coach_id = coach_id
        self.coach_cost = coach_cost
        self.has_video = has_video
        self.has_notes = has_notes
        self.rink_id = rink_id
        self.uSkaterUUID = uSkaterUUID
        self.uSkaterConfig = uSkaterConfig
        self.uSkaterType = uSkaterType
