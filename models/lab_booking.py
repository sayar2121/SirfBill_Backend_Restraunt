import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Date, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy import UUID, Enum
from .enums import BookingStatus

from .database import Base

class LabBooking(Base):
    __tablename__ = "lab_bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # --- ADDED FOR ADMIN DISPATCH & TENANCY ---
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True) # Assigned technician
    admin_notes = Column(Text, nullable=True) # Internal notes
    # ------------------------------------------
    
    # --- CHANGED: Cart & Payment fields ---
    payment_method = Column(String, nullable=False, default="COD")
    booked_items = Column(JSONB, nullable=False) 
    # --------------------------------------
    
    status = Column(Enum(BookingStatus), nullable=False, default=BookingStatus.PENDING_CONFIRMATION)
    total_amount = Column(Float, nullable=False)
    preferred_date = Column(Date, nullable=False)
    form_details = Column(JSONB)
    report_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id])
    agent = relationship("User", foreign_keys=[agent_id]) # New relationship

