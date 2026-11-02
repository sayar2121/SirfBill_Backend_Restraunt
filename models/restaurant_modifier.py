import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base

class RestaurantModifierGroup(Base):
    """
    Modifier Group: e.g. 'Spice Level', 'Choice of Crust', 'Add-on Toppings'
    """
    __tablename__ = "restaurant_modifier_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    outlet_id = Column(UUID(as_uuid=True), ForeignKey("restaurant_outlets.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    min_selection = Column(Integer, default=0, nullable=False) # 0 means optional
    max_selection = Column(Integer, default=1, nullable=False) # 1 for single-choice, >1 for multi-choice
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    options = relationship("RestaurantModifierOption", back_populates="group", cascade="all, delete-orphan")
    item_links = relationship("RestaurantItemModifierGroup", back_populates="modifier_group", cascade="all, delete-orphan")


class RestaurantModifierOption(Base):
    """
    Individual option under a modifier group: e.g. 'Extra Cheese (+₹40)', 'Mild (+₹0)'
    """
    __tablename__ = "restaurant_modifier_options"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey("restaurant_modifier_groups.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(100), nullable=False)
    price_delta = Column(Numeric(10, 2), default=0.00, nullable=False) # Extra cost added to line item
    is_available = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    group = relationship("RestaurantModifierGroup", back_populates="options")


class RestaurantItemModifierGroup(Base):
    """
    Many-to-many relationship linking a menu item to its applicable modifier groups.
    """
    __tablename__ = "restaurant_item_modifier_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id = Column(UUID(as_uuid=True), ForeignKey("restaurant_menu_items.id", ondelete="CASCADE"), nullable=False, index=True)
    modifier_group_id = Column(UUID(as_uuid=True), ForeignKey("restaurant_modifier_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    sort_order = Column(Integer, default=0, nullable=False)

    item = relationship("RestaurantMenuItem", back_populates="modifier_links")
    modifier_group = relationship("RestaurantModifierGroup", back_populates="item_links")
