import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy import UUID
from sqlalchemy.orm import relationship

from .database import Base

class Shop(Base):
    __tablename__ = "shops"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=True, index=True) # Organization ID
    
    name = Column(String, nullable=False)
    code = Column(String, unique=True, index=True)
    address = Column(String, nullable=False)
    city = Column(String)
    contact_number = Column(String)
    status = Column(String, default="Active")
    is_primary = Column(Boolean, default=False)
    account_holder_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    inventory_items = relationship("InventoryItem", back_populates="shop")
    bills = relationship("ShopBill", back_populates="shop")
