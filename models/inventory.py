import uuid
from datetime import datetime
from sqlalchemy import Column, Index, String, Float, Integer, Date, DateTime, ForeignKey, Boolean
from sqlalchemy import UUID
from sqlalchemy.orm import relationship

from .database import Base

class InventoryItem(Base):
    __tablename__ = "inventory_items"
    
    __table_args__ = (
        Index('idx_inventory_shop_name', 'shop_id', 'name'),
        Index('idx_inventory_shop_sku', 'shop_id', 'sku'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    shop_id = Column(UUID(as_uuid=True), ForeignKey("shops.id", ondelete="SET NULL"), nullable=True)
    
    name = Column(String, nullable=False, index=True)
    sku = Column(String, nullable=False, index=True) # e.g., product barcode
    manufacturer = Column(String, nullable=True) # Essential for medicines
    batch_number = Column(String, nullable=True, default="N/A", server_default="N/A")
    image_url = Column(String, nullable=True)
    
    stock_quantity = Column(Integer, nullable=False, default=0)
    pack_size = Column(Integer, nullable=False, default=1, server_default='1')
    loose_stock = Column(Integer, nullable=False, default=0, server_default='0')
    buying_price = Column(Float, nullable=False, default=0.0)
    hsn_code = Column(String, nullable=True)
    unit_price = Column(Float, nullable=False)
    expiry_date = Column(Date, nullable=True)
    gst = Column(Float, nullable=True, default=0.0)
    discount = Column(Float, nullable=True, default=0.0)
    rack_id = Column(UUID(as_uuid=True), ForeignKey("racks.id", ondelete="SET NULL"), nullable=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    distributor = Column(String, nullable=True) # Old text column
    distributor_id = Column(UUID(as_uuid=True), ForeignKey("distributors.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)
    is_deleted = Column(Integer, default=0, index=True)

    shop = relationship("Shop", back_populates="inventory_items")
    distributor_rel = relationship("Distributor", back_populates="inventory_items")
