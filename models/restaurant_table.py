import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base

class RestaurantTable(Base):
    """
    Restaurant dine-in tables, sections, and capacities.
    """
    __tablename__ = "restaurant_tables"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    outlet_id = Column(UUID(as_uuid=True), ForeignKey("restaurant_outlets.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    table_code = Column(String(50), nullable=False) # e.g. "T1", "T2", "ROOF-04"
    section = Column(String(50), default="Main Hall", nullable=False) # e.g. "AC Hall", "Balcony", "Rooftop"
    capacity = Column(Integer, default=4, nullable=False)
    
    # Operational status: VACANT, OCCUPIED, RESERVED, CLEANING
    status = Column(String(30), default="VACANT", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    outlet = relationship("RestaurantOutlet", back_populates="tables")
    orders = relationship("RestaurantOrder", back_populates="table")
