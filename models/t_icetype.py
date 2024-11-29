from sqlalchemy import Column, Integer, String
from .base import Base


class IceType(Base):
    '''
    This table describes the different types of ice sessions, used
    as part of foreign keys. If you want a human readable experience,
    this needs to be populated at setup.

    Used to calcuate things like how many hours or dollars have been spent
    competing vs practicing, or practicing on freestyle vs public time
    '''

    __tablename__ = 'ice_type'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    ice_type = Column(String)

    def __init__(self, type_id, ice_type):
        self.id = type_id
        self.ice_type = ice_type
