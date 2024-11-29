from sqlalchemy import Column, Integer, Float, String
from .base import Base


class Coaches(Base):
    '''
    This table describes basic coach data, such as name and rate.
    Its worth mentioning that this table complicates other areas because
    it defines what coaches can be used to track time, but we also want
    to define coaches in the uSkaterConfig table.  This table may either
    be dropped in the future or we may need some logic to account for using
    this table when a skater wants to track coach time with a coach that isnt
    a skatetrax user.  Currently, this logic doesn't exist.

    A coach with a uSkaterUUID of NULL should indicate that the coach isnt
    a skatetrax user yet.

    Row 1 should always be a generic entry for 'no coach'.
    '''

    __tablename__ = 'coaches'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    coach_Fname = Column(String)
    coach_Lname = Column(String)
    coach_rate = Column(Float)
    uSkaterUUID = Column(Integer)

    def __init__(self, coach_Fname, coach_Lname, coach_rate, uSkaterUUID):
        self.coach_Fname = coach_Fname
        self.coach_Lname = coach_Lname
        self.coach_rate = coach_rate
        self.uSkaterUUID = uSkaterUUID
