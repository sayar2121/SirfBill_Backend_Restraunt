import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy import UUID

from .database import Base

class Story(Base):
    __tablename__ = "stories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    media_type = Column(String, nullable=False)
    media_url = Column(String, nullable=False)
    caption = Column(String)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
