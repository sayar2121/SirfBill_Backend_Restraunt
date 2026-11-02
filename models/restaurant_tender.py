import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base

class RestaurantTender(Base):
    """
    Settlement payments for orders. Supports split tenders (e.g. part Cash, part UPI).
    """
    __tablename__ = "restaurant_tenders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("restaurant_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    method = Column(String(30), nullable=False) # CASH, UPI, CARD, COMPLIMENTARY, DUE
    amount = Column(Numeric(10, 2), nullable=False)
    reference = Column(String(100), nullable=True) # Transaction ID / UPI ref / Card last 4 digits
    status = Column(String(30), default="COMPLETED", nullable=False) # COMPLETED, REFUNDED, FAILED
    
    cashier_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    idempotency_key = Column(String(100), unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    order = relationship("RestaurantOrder", back_populates="tenders")
    cashier = relationship("User")
    refunds = relationship("RestaurantRefund", back_populates="tender", cascade="all, delete-orphan")


class RestaurantRefund(Base):
    """
    Refund or reversal linked to a tender/order.
    """
    __tablename__ = "restaurant_refunds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tender_id = Column(UUID(as_uuid=True), ForeignKey("restaurant_tenders.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("restaurant_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    
    amount = Column(Numeric(10, 2), nullable=False)
    reason = Column(Text, nullable=False)
    authorized_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True) # Manager role required
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tender = relationship("RestaurantTender", back_populates="refunds")
    order = relationship("RestaurantOrder")
    manager = relationship("User", foreign_keys=[authorized_by])
