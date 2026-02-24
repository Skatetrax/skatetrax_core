from sqlalchemy import Column, Integer, Float, String, ForeignKey, UUID
from sqlalchemy.orm import mapped_column, Mapped

from uuid import uuid4, UUID as UUIDV4
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
    
    Future enhancement: A merge process should detect and prompt users when
    their USFSA/IJS number already exists in the system, and offer to claim it.
    That would convert the anonymous/null-linked record into a verified one,
    and update uSkaterUUID accordingly.

    Row 1 should always be a generic entry for 'no coach'.
    '''

    __tablename__ = 'coaches'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    coach_id: Mapped[UUIDV4] = mapped_column(unique=True, default=uuid4)

    coach_Fname = Column(String)
    coach_Lname = Column(String)
    coach_rate = Column(Float)

    coach_usfsa_id = Column(Integer, nullable=True)
    coach_ijs_id = Column(Integer, nullable=True)
    coach_phone = Column(Integer, nullable=True)
    coach_email = Column(String, nullable=True)
    
    uSkaterUUID = Column(UUID, nullable=True)

    def __init__(
        self,
        coach_id,
        coach_Fname,
        coach_Lname,
        coach_rate,
        coach_phone,
        coach_email,
        coach_ijs_id,
        coach_usfsa_id,
        uSkaterUUID = None
        ):
        
        self.coach_id = coach_id
        self.coach_Fname = coach_Fname
        self.coach_Lname = coach_Lname
        self.coach_rate = coach_rate
        self.uSkaterUUID = uSkaterUUID
        self.coach_usfsa_id = coach_usfsa_id
        self.coach_ijs_id = coach_ijs_id
        self.coach_email = coach_email
        self.coach_phone = coach_phone
