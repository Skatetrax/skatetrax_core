from sqlalchemy import Column, String, Integer, DateTime, Float
from .base import Base


class Club_Membership(Base):
    '''
    This table tracks data regarding club memberships. Currently, the club
    name is manually entered, but there is a possiblity that it can be moved
    to the same type of setup that we're going to be doing with the
    location/icemaker project where things are ID based on another table.
    Since this is mostly used for cost tracking, this mechanism still works.
    '''

    __tablename__ = 'club_membership'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    location_id = Column(Integer)
    club_cost = Column(Float)
    club_name = Column(String)
    date_start = Column(DateTime)
    date_end = Column(DateTime)
    uSkaterUUID = Column(Integer)

    def __init__(
        self,
        location_id,
        club_cost,
        club_name,
        date_start,
        date_end,
        uSkaterUUID
            ):

        self.location_id = location_id
        self.club_cost = club_cost
        self.club_name = club_name
        self.date_start = date_start
        self.date_end = date_end
        self.uSkaterUUID = uSkaterUUID
