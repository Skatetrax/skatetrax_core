from sqlalchemy import Column, String
from sqlalchemy.orm import mapped_column, Mapped
from uuid import uuid4, UUID as UUIDV4
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

    ice_type_id: Mapped[UUIDV4] = mapped_column(primary_key=True, default=uuid4)
    ice_type = Column(String)

    def __init__(self, ice_type_id, ice_type):
        self.ice_type_id = ice_type_id
        self.ice_type = ice_type
