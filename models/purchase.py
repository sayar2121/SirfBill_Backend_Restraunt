import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Date
from sqlalchemy import UUID
from sqlalchemy.orm import relationship

from .database import Base

class PurchaseBill(Base):
    __tablename__ = "purchase_bills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    shop_id = Column(UUID(as_uuid=True), ForeignKey("shops.id", ondelete="SET NULL"), nullable=True)
    distributor_id = Column(UUID(as_uuid=True), ForeignKey("distributors.id", ondelete="SET NULL"), nullable=True)
    
    invoice_no = Column(String, nullable=True) # Distributor's invoice number
    bill_date = Column(Date, nullable=False, default=datetime.now().date)
    

    total_amount = Column(Float, nullable=False)
    subtotal = Column(Float, default=0.0)
    total_discount = Column(Float, default=0.0)
    total_gst = Column(Float, default=0.0)
    amount_paid = Column(Float, default=0.0)

    payment_status = Column(String, default="PENDING") # PENDING, PARTIAL, PAID
    payment_method = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)

    shop = relationship("Shop")
    distributor = relationship("Distributor", back_populates="purchase_bills")
    items = relationship("PurchaseBillItem", back_populates="bill", cascade="all, delete-orphan")


class PurchaseBillItem(Base):
    __tablename__ = "purchase_bill_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("purchase_bills.id", ondelete="CASCADE"), nullable=False)
    inventory_item_id = Column(UUID(as_uuid=True), ForeignKey("inventory_items.id", ondelete="SET NULL"), nullable=True)
    
    quantity = Column(Integer, nullable=False) # Number of packs
    free_quantity = Column(Integer, default=0) # Free bonus packs
    unit_price = Column(Float, nullable=False) # Purchase price per pack
    batch_number = Column(String, nullable=True, default="N/A", server_default="N/A")
    expiry_date = Column(Date, nullable=True)
    discount = Column(Float, default=0.0)
    gst = Column(Float, default=0.0)
    
    bill = relationship("PurchaseBill", back_populates="items")
