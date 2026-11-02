import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base

class RestaurantCustomer(Base):
    """
    Minimal restaurant customer profile (name, phone, dietary preferences).
    Walk-in guest info is optional.
    """
    __tablename__ = "restaurant_customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    outlet_id = Column(UUID(as_uuid=True), ForeignKey("restaurant_outlets.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(150), nullable=False)
    phone = Column(String(20), nullable=False, index=True)
    email = Column(String(100), nullable=True)
    
    loyalty_points = Column(Integer, default=0, nullable=False)
    preferences = Column(JSON, default=dict) # e.g. {"dietary": "VEG", "favorite_dish": "Paneer Butter Masala"}
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    outlet = relationship("RestaurantOutlet")
    loyalty_ledger = relationship("RestaurantLoyaltyLedger", back_populates="customer", cascade="all, delete-orphan")


class RestaurantLoyaltyLedger(Base):
    """
    Points earned, redeemed, or reversed.
    """
    __tablename__ = "restaurant_loyalty_ledger"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("restaurant_customers.id", ondelete="CASCADE"), nullable=False, index=True)
    points_delta = Column(Integer, nullable=False) # Positive for earn, Negative for redeem
    reason = Column(String(50), nullable=False) # ORDER_EARN, ORDER_REDEEM, MANUAL_ADJUSTMENT, REVERSAL
    source_order_id = Column(UUID(as_uuid=True), ForeignKey("restaurant_orders.id", ondelete="SET NULL"), nullable=True)

    idempotency_key = Column(String(100), unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    customer = relationship("RestaurantCustomer", back_populates="loyalty_ledger")
    order = relationship("RestaurantOrder")
