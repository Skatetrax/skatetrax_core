from sqlalchemy import Column, DateTime, Integer, Float, ForeignKey, UUID
from .base import Base


class Ice_Time(Base):
    __tablename__ = 'ice_time'
    __table_args__ = {'extend_existing': True}

    ice_time_id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime)
    ice_time = Column(Integer)
    ice_cost = Column(Float)
    skate_type = Column(UUID, ForeignKey("ice_type.ice_type_id", ondelete='CASCADE'))
    coach_time = Column(Integer)
    coach_id = Column(UUID, ForeignKey("coaches.coach_id", ondelete='CASCADE'))
    coach_cost = Column(Float)
    has_video = Column(Integer)
    has_notes = Column(Integer)
    rink_id = Column(UUID, ForeignKey("locations.rink_id", ondelete='CASCADE'))
    uSkaterUUID = Column(UUID, ForeignKey("uSkaterConfig.uSkaterUUID", ondelete='CASCADE'))
    uSkaterConfig = Column(UUID, ForeignKey("uSkateConfig.sConfigID", ondelete='CASCADE'))
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
