import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, Numeric, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base

class RestaurantOrderLine(Base):
    """
    Individual items ordered. Captures frozen snapshots of prices and modifiers.
    KOT Status: PENDING_SEND, SENT_TO_KITCHEN, PREPARING, READY, SERVED, CANCELLED
    """
    __tablename__ = "restaurant_order_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("restaurant_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(UUID(as_uuid=True), ForeignKey("restaurant_menu_items.id", ondelete="SET NULL"), nullable=True)

    # Snapshots to preserve invoice integrity even if menu changes later
    item_name = Column(String(150), nullable=False)
    variant_name = Column(String(50), default="Standard", nullable=False)
    prep_station = Column(String(50), default="KITCHEN", nullable=False)

    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False) # Base variant price
    modifier_price = Column(Numeric(10, 2), default=0.00, nullable=False) # Sum of selected modifiers
    discount_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    tax_rate = Column(Numeric(5, 2), default=5.00, nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    line_total = Column(Numeric(10, 2), nullable=False) # (unit_price + modifier_price) * qty - discount + tax

    # JSON snapshot of chosen modifiers: [{"id": "...", "name": "Extra Cheese", "price": 40.0}]
    selected_modifiers = Column(JSON, default=list)
    special_instructions = Column(Text, nullable=True) # e.g. "Less spicy, no onions"

    kot_status = Column(String(30), default="PENDING_SEND", nullable=False) # PENDING_SEND, SENT_TO_KITCHEN, PREPARING, READY, SERVED, CANCELLED
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    order = relationship("RestaurantOrder", back_populates="lines")
    item = relationship("RestaurantMenuItem")
