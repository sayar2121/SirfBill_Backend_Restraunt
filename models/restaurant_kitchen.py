import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base

class RestaurantKitchenTicket(Base):
    """
    Kitchen Order Ticket (KOT) sent to station displays/printers.
    """
    __tablename__ = "restaurant_kitchen_tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("restaurant_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    ticket_number = Column(String(50), nullable=False) # e.g. "KOT-001"
    station = Column(String(50), default="KITCHEN", nullable=False) # KITCHEN, BAR, DESSERT
    status = Column(String(30), default="PENDING", nullable=False) # PENDING, PREPARING, READY, SERVED, CANCELLED
    
    server_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    is_reprint = Column(Boolean, default=False, nullable=False)
    reprint_count = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    order = relationship("RestaurantOrder", back_populates="kitchen_tickets")
    server_user = relationship("User")
    items = relationship("RestaurantKitchenTicketItem", back_populates="ticket", cascade="all, delete-orphan")
    events = relationship("RestaurantKitchenEvent", back_populates="ticket", cascade="all, delete-orphan")


class RestaurantKitchenTicketItem(Base):
    """
    Items included in a specific KOT dispatch.
    """
    __tablename__ = "restaurant_kitchen_ticket_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("restaurant_kitchen_tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    order_line_id = Column(UUID(as_uuid=True), ForeignKey("restaurant_order_lines.id", ondelete="CASCADE"), nullable=False)

    item_name = Column(String(150), nullable=False)
    variant_name = Column(String(50), default="Standard", nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    modifiers_summary = Column(Text, nullable=True)
    special_instructions = Column(Text, nullable=True)

    status = Column(String(30), default="PENDING", nullable=False)

    ticket = relationship("RestaurantKitchenTicket", back_populates="items")
    order_line = relationship("RestaurantOrderLine")


class RestaurantKitchenEvent(Base):
    """
    Audit log of kitchen state transitions (SENT, PREPARING, READY, SERVED).
    """
    __tablename__ = "restaurant_kitchen_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("restaurant_kitchen_tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    from_status = Column(String(30), nullable=True)
    to_status = Column(String(30), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    ticket = relationship("RestaurantKitchenTicket", back_populates="events")
    actor = relationship("User")
