import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Date, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy import UUID, Enum, Text

from .enums import BookingStatus

from .database import Base

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=True)
    
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    admin_notes = Column(Text, nullable=True)
    
    status = Column(Enum(BookingStatus), nullable=False, default=BookingStatus.PENDING_CONFIRMATION)
    preferred_date = Column(Date, nullable=False)
    form_details = Column(JSONB)
    prescription_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id])
    doctor = relationship("Doctor", back_populates="appointments")
    agent = relationship("User", foreign_keys=[agent_id])

