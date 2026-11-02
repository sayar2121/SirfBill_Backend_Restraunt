import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base

class RestaurantIngredient(Base):
    """
    Ingredient master: e.g. Chicken (KG), Basmati Rice (KG), Cooking Oil (L), Cheese (G).
    """
    __tablename__ = "restaurant_ingredients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    outlet_id = Column(UUID(as_uuid=True), ForeignKey("restaurant_outlets.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(150), nullable=False)
    sku = Column(String(50), nullable=True, index=True)
    unit = Column(String(20), nullable=False) # KG, G, L, ML, PCS
    current_stock = Column(Numeric(12, 3), default=0.000, nullable=False)
    reorder_level = Column(Numeric(12, 3), default=5.000, nullable=False)
    cost_per_unit = Column(Numeric(10, 2), default=0.00, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    outlet = relationship("RestaurantOutlet")
    recipe_lines = relationship("RestaurantRecipeLine", back_populates="ingredient")
    ledger_entries = relationship("RestaurantStockLedger", back_populates="ingredient")
