import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy import UUID

from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # --- ADDED FOR TENANCY & OUTLET ASSIGNMENT ---
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    outlet_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    # ---------------------------------------------
    
    role = Column(String, nullable=False)
    phone = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, index=True, nullable=True)
    password = Column(String, nullable=True)
    avatar_url = Column(String)
    saved_addresses = Column(JSONB)
    is_active = Column(Boolean, default=True)
    location = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

