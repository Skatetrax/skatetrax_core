from sqlalchemy import Column, String, Integer, DateTime, Float
from .base import Base


class uSkaterMaint(Base):
    '''
    This table tracks the cost and other details of maintenance of the skate.
    Things that belong here are blade sharpenings, boot punchouts or repairs,
    a change to the radius of hollow, and any other repairs or changes.
    '''

    __tablename__ = 'maintenance'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    m_date = Column(DateTime)
    m_hours_on = Column(Integer)
    m_cost = Column(Float)
    m_location = Column(Integer)
    m_notes = Column(String)
    m_roh = Column(Integer)
    uSkateConfig = Column(Integer)
    uSkaterUUID = Column(Integer)

    def __init__(
        self,
        m_date,
        m_hours_on,
        m_cost,
        m_location,
        m_notes,
        uSkateConfig,
        uSkaterUUID,
            ):

        self.m_date = m_date
        self.m_hours_on = m_hours_on
        self.m_cost = m_cost
        self.m_location = m_location
        self.m_notes = m_notes
        self.uSkateConfig = uSkateConfig
        self.uSkaterUUID = uSkaterUUID
