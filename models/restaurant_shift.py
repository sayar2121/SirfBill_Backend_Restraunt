import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base

class RestaurantShift(Base):
    """
    Cashier/Counter Shift management for till accountability.
    Tracks opening cash, counted closing cash, and cash drop variances.
    """
    __tablename__ = "restaurant_shifts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    outlet_id = Column(UUID(as_uuid=True), ForeignKey("restaurant_outlets.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    cashier_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    status = Column(String(30), default="OPEN", nullable=False) # OPEN, CLOSED
    opened_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    closed_at = Column(DateTime, nullable=True)

    opening_cash = Column(Numeric(10, 2), default=0.00, nullable=False)
    counted_cash = Column(Numeric(10, 2), nullable=True)
    expected_cash = Column(Numeric(10, 2), nullable=True)
    variance = Column(Numeric(10, 2), nullable=True) # counted_cash - expected_cash

    notes = Column(Text, nullable=True)

    outlet = relationship("RestaurantOutlet", back_populates="shifts")
    cashier = relationship("User")
    orders = relationship("RestaurantOrder", back_populates="shift")
