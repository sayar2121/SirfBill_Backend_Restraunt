import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy import UUID

from .database import Base

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # --- ADDED FOR TENANCY ---
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    # -------------------------
    
    name = Column(String, nullable=False)
    specialty_key = Column(String, nullable=False)
    experience = Column(String)
    fee = Column(Float, nullable=False)
    
    # --- ADDED: Doctor's Profile Picture ---
    image_url = Column(String, nullable=True) 
    # --------------------------------------
    
    about = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    appointments = relationship("Appointment", back_populates="doctor")
