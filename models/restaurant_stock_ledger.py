import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base

class RestaurantStockLedger(Base):
    """
    Append-only stock ledger:
    Tracks RECEIVED, CONSUMED_SALE, WASTED, ADJUSTED, REVERSED.
    Never overwrite balances directly; sum of signed quantities yields stock.
    """
    __tablename__ = "restaurant_stock_ledger"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ingredient_id = Column(UUID(as_uuid=True), ForeignKey("restaurant_ingredients.id", ondelete="CASCADE"), nullable=False, index=True)
    outlet_id = Column(UUID(as_uuid=True), ForeignKey("restaurant_outlets.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Positive for stock-in, Negative for consumption / wastage
    signed_quantity = Column(Numeric(12, 3), nullable=False)
    reason = Column(String(50), nullable=False) # PURCHASE_RECEIVED, ORDER_CONSUMPTION, WASTAGE, PHYSICAL_COUNT_ADJUSTMENT, REVERSAL
    source_type = Column(String(50), nullable=True) # order, purchase_bill, manual
    source_id = Column(String(100), nullable=True)

    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    ingredient = relationship("RestaurantIngredient", back_populates="ledger_entries")
    outlet = relationship("RestaurantOutlet")
    actor = relationship("User")
