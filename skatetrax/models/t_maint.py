from sqlalchemy import Column, String, Integer, DateTime, Float, UUID, ForeignKey
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
    m_location = Column(UUID)
    m_notes = Column(String, nullable=True)
    m_roh = Column(String, nullable=True)
    m_pref_hours = Column(Float, nullable=True)  # preferred maintenance cycle hours at the time
    uSkaterBladesID = Column(UUID, ForeignKey("uSkaterBlades.bladesID", ondelete='CASCADE'), nullable=True)
    uSkaterConfig = Column(UUID, ForeignKey("uSkateConfig.sConfigID", ondelete='CASCADE'))
    uSkaterUUID = Column(UUID, ForeignKey("uSkaterConfig.uSkaterUUID", ondelete='CASCADE'))

    def __init__(
        self,
        m_date,
        m_hours_on,
        m_cost,
        m_location,
        m_notes,
        m_roh,
        m_pref_hours,
        uSkaterBladesID,
        uSkateConfig,
        uSkaterUUID,
            ):

        self.m_date = m_date
        self.m_hours_on = m_hours_on
        self.m_cost = m_cost
        self.m_location = m_location
        self.m_notes = m_notes
        self.m_roh = m_roh
        self.m_pref_hours = m_pref_hours
        self.uSkaterBladesID = uSkaterBladesID
        self.uSkateConfig = uSkateConfig
        self.uSkaterUUID = uSkaterUUID
