import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, Numeric, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base

class RestaurantOrder(Base):
    """
    Restaurant Order Header.
    Workflow Status: DRAFT, OPEN, SENT_TO_KITCHEN, COMPLETED, CANCELLED, VOIDED
    Order Type: DINE_IN, TAKEAWAY, DELIVERY
    """
    __tablename__ = "restaurant_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    outlet_id = Column(UUID(as_uuid=True), ForeignKey("restaurant_outlets.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    order_number = Column(String(50), nullable=False, index=True) # E.g. "ORD-20261022-001"
    order_type = Column(String(30), default="DINE_IN", nullable=False) # DINE_IN, TAKEAWAY, DELIVERY
    status = Column(String(30), default="OPEN", nullable=False, index=True)

    table_id = Column(UUID(as_uuid=True), ForeignKey("restaurant_tables.id", ondelete="SET NULL"), nullable=True, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    customer_name = Column(String(150), nullable=True)
    customer_phone = Column(String(20), nullable=True)

    waiter_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    shift_id = Column(UUID(as_uuid=True), ForeignKey("restaurant_shifts.id", ondelete="SET NULL"), nullable=True)

    # Server authoritative financial calculations (Numeric)
    subtotal = Column(Numeric(10, 2), default=0.00, nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    discount_reason = Column(String(200), nullable=True)
    tax_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    rounding_adjustment = Column(Numeric(10, 2), default=0.00, nullable=False)
    grand_total = Column(Numeric(10, 2), default=0.00, nullable=False)
    paid_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    payment_method = Column(String(50), default="CASH", nullable=True) # CASH, UPI, CARD, SPLIT, DUE

    notes = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=False) # Optimistic locking concurrency check
    idempotency_key = Column(String(100), unique=True, nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    outlet = relationship("RestaurantOutlet", back_populates="orders")
    table = relationship("RestaurantTable", back_populates="orders")
    waiter = relationship("User", foreign_keys=[waiter_id])
    shift = relationship("RestaurantShift", back_populates="orders")
    lines = relationship("RestaurantOrderLine", back_populates="order", cascade="all, delete-orphan")
    kitchen_tickets = relationship("RestaurantKitchenTicket", back_populates="order", cascade="all, delete-orphan")
    tenders = relationship("RestaurantTender", back_populates="order", cascade="all, delete-orphan")
