from sqlalchemy import Column, Float, Integer, DateTime, String, ForeignKey, UUID
from sqlalchemy.orm import mapped_column, Mapped
from uuid import uuid4, UUID as UUIDV4
from .base import Base


class Club_Directory(Base):
    '''
    Lookup table for skating clubs. Each club has a UUID, a human-readable
    name, an optional home rink FK, and a base annual cost. Row 1 should
    always be a "No Club" placeholder so that org_Club on uSkaterConfig
    has a valid FK target for skaters without a club affiliation.
    '''

    __tablename__ = 'club_directory'
    __table_args__ = {'extend_existing': True}

    club_id: Mapped[UUIDV4] = mapped_column(primary_key=True, default=uuid4)
    club_name = Column(String)
    club_home_rink = Column(UUID, ForeignKey("locations.rink_id", ondelete='CASCADE'), nullable=True)
    club_cost = Column(Float)

    def __init__(
        self,
        club_id,
        club_name,
        club_home_rink,
        club_cost
            ):

        self.club_id = club_id
        self.club_name = club_name
        self.club_home_rink = club_home_rink
        self.club_cost = club_cost


class Club_Members(Base):
    '''
    Tracks each skater's club membership history. Each row represents one
    membership period: when they joined, when it expires, and what they paid.
    Skating club memberships typically expire on June 30th. Expired rows are
    kept as historical records -- active vs expired is determined by comparing
    expiration_date against today.
    '''

    __tablename__ = 'club_members'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    club_id = Column(UUID, ForeignKey("club_directory.club_id", ondelete='CASCADE'))
    uSkaterUUID = Column(UUID, ForeignKey("uSkaterConfig.uSkaterUUID", ondelete='CASCADE'))
    joined_date = Column(DateTime, nullable=True)
    expiration_date = Column(DateTime, nullable=True)
    membership_fee = Column(Float)

    def __init__(self, club_id, uSkaterUUID, joined_date, expiration_date, membership_fee):
        self.club_id = club_id
        self.uSkaterUUID = uSkaterUUID
        self.joined_date = joined_date
        self.expiration_date = expiration_date
        self.membership_fee = membership_fee

    def __repr__(self):
        return f"<Club_Member skater={self.uSkaterUUID} club={self.club_id}>"
