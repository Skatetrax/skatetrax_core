from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID

from datetime import datetime, timezone
from .base import Base

from uuid import uuid4

class uAuthTable(Base):
    __tablename__ = 'uAuthTable'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    
    # Username, Pass, Contact
    aLogin = Column(String(80), unique=True, nullable=False)
    aPasswordHash = Column(Text, nullable=False)
    aEmail = Column(String(120), unique=True, nullable=False)
    phone_number = Column(String(20), unique=True, nullable=True)

    uSkaterUUID = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    
    
    # Basic Logging
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def set_password(self, password):
        self.aPasswordHash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.aPasswordHash, password)

    def __repr__(self):
        return f"<User(username='{self.aLogin}', email='{self.aEmail}')>"
