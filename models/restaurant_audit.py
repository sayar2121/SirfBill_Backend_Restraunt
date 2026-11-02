import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base

class RestaurantAuditEvent(Base):
    """
    Audit log for critical restaurant events:
    Discount overrides, order voids, bill cancellations, KOT reprints, price overrides.
    """
    __tablename__ = "restaurant_audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    outlet_id = Column(UUID(as_uuid=True), ForeignKey("restaurant_outlets.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    action = Column(String(50), nullable=False) # VOID_ORDER, DISCOUNT_OVERRIDE, KOT_REPRINT, REFUND, PRICE_OVERRIDE
    entity_name = Column(String(50), nullable=False) # order, kot, tender, table
    entity_id = Column(String(100), nullable=False)
    reason = Column(String(255), nullable=True)

    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    outlet = relationship("RestaurantOutlet")
    actor = relationship("User")
