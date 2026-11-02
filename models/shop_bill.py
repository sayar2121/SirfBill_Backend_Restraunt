import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy import UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .database import Base

class ShopBill(Base):
    __tablename__ = "shop_bills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    shop_id = Column(UUID(as_uuid=True), ForeignKey("shops.id", ondelete="SET NULL"), nullable=True)
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True) # The customer buying
    # prescription_id = Column(UUID(as_uuid=True), nullable=True) # Bridging CRM & Pharmacy (Not needed for print shop)
    invoice_no = Column(String, nullable=True) # Custom shop invoice number
    
    # Customer Details for unregistered/walk-in patients or B2B
    customer_name = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True)
    customer_location = Column(String, nullable=True)
    customer_gstin = Column(String, nullable=True)
    
    # Financials
    subtotal = Column(Float, nullable=False, default=0.0, server_default='0.0')
    total_discount = Column(Float, nullable=False, default=0.0, server_default='0.0')
    total_gst = Column(Float, nullable=False, default=0.0, server_default='0.0')
    total_amount = Column(Float, nullable=False, server_default='0.0') # Final amount to pay
    amount_paid = Column(Float, nullable=False, default=0.0, server_default='0.0') # For partial payments
    
    payment_method = Column(String, default="CASH")
    payment_status = Column(String, default="PAID") # UNPAID, PARTIAL, PAID
    status = Column(String, default="COMPLETED")
    delivery_address = Column(JSONB, nullable=True) # Used for online orders
    created_at = Column(DateTime, default=datetime.now)

    shop = relationship("Shop", back_populates="bills")
    items = relationship("ShopBillItem", back_populates="bill")


class ShopBillItem(Base):
    __tablename__ = "shop_bill_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("shop_bills.id"), nullable=False)
    
    # Can be either a physical inventory item or a custom print job
    inventory_item_id = Column(UUID(as_uuid=True), ForeignKey("inventory_items.id"), nullable=True)
    
    # Store name of the item for receipt rendering without joins
    item_name = Column(String, nullable=True)
    
    quantity = Column(Integer, nullable=False)
    is_loose = Column(Boolean, default=False)
    
    # Financials at time of sale
    unit_price_at_sale = Column(Float, nullable=False, server_default='0.0') # Base price before discount/tax
    discount_at_sale = Column(Float, default=0.0, server_default='0.0') # Percentage or flat
    gst_at_sale = Column(Float, default=0.0, server_default='0.0') # GST percentage
    total_price = Column(Float, nullable=False, default=0.0, server_default='0.0') # Final price for this row
    
    bill = relationship("ShopBill", back_populates="items")

