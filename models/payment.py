import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy import UUID

from models.database import Base

class Payment(Base):
    """
    A universal ledger for all transactions (Labs, Medicines, Consultations).
    """
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # --- ADDED FOR TENANCY ---
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    # -------------------------
    
    amount = Column(Float, nullable=False)
    status = Column(String, default="PENDING") # PENDING, SUCCESS, FAILED
    
    # What are they paying for? 
    # e.g., module_type = "LAB_BOOKING", module_id = <LabBooking UUID>
    module_type = Column(String, nullable=False)
    module_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Razorpay Specifics
    razorpay_order_id = Column(String, nullable=True)
    razorpay_payment_id = Column(String, nullable=True)
    razorpay_signature = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
