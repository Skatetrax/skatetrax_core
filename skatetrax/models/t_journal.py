from sqlalchemy import Column, String, Integer, DateTime, UUID, ForeignKey
from .base import Base


class Journal_Notes(Base):
    '''
    This table is for session notes.
    '''

    __tablename__ = 'j_notes'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    notes_date = Column(DateTime)
    notes = Column(String)
    uSkaterUUID = Column(UUID, ForeignKey("uSkaterConfig.uSkaterUUID", ondelete='CASCADE'))

    def __init__(self, notes_date, notes, uSkaterUUID):
        self.notes_date = notes_date
        self.notes = notes
        self.uSkaterUUID = uSkaterUUID


class Journal_Videos(Base):
    '''
    This table is for storing info about where to find video for a session.
    There is no download here, only storage of links, name, platform, etc
    '''

    __tablename__ = 'j_videos'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    video_date = Column(DateTime)
    video_url = Column(String)
    video_platform = Column(String, nullable=True)
    video_type = Column(String, nullable=True)
    video_name = Column(String, nullable=True)
    uSkaterUUID = Column(UUID, ForeignKey("uSkaterConfig.uSkaterUUID", ondelete='CASCADE'))

    def __init__(
        self,
        video_date,
        video_url,
        video_platform,
        video_type,
        video_name,
        uSkaterUUID
            ):

        self.video_date = video_date
        self.video_url = video_url
        self.video_platform = video_platform
        self.video_type = video_type
        self.video_name = video_name
        self.uSkaterUUID = uSkaterUUID
