from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from models.database import Base

class Banner(Base):
    """
    Stores images for the home screen advertisement carousel.
    """
    __tablename__ = "banners"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_url = Column(String, nullable=False)
    
    # Optional: If you want clicking the banner to open a specific link or screen
    action_url = Column(String, nullable=True) 
    
    is_active = Column(Boolean, default=True) # Allows admin to hide a banner without deleting it
    created_at = Column(DateTime, default=datetime.utcnow)
