import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, Numeric, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base

class RestaurantOutlet(Base):
    __tablename__ = "restaurant_outlets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    shop_id = Column(UUID(as_uuid=True), ForeignKey("shops.id", ondelete="SET NULL"), nullable=True, index=True)
    
    name = Column(String(150), nullable=False)
    code = Column(String(50), nullable=True, index=True)
    timezone = Column(String(50), default="Asia/Kolkata", nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    
    service_settings = Column(JSON, default=dict) # e.g. {"dine_in_enabled": True, "takeaway_enabled": True, "delivery_enabled": True, "gst_number": ""}
    is_active = Column(Boolean, default=True, nullable=False)

    # Direct relational columns for pgAdmin & SQL queries
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pin_code = Column(String(20), nullable=True)
    country = Column(String(100), default="India", nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(120), nullable=True)
    outlet_type = Column(String(100), nullable=True)
    gstin = Column(String(50), nullable=True)
    fssai = Column(String(50), nullable=True)
    invoice_prefix = Column(String(50), nullable=True)
    tax_rate = Column(Numeric(5, 2), default=5.0, nullable=True)
    opening_time = Column(String(20), nullable=True)
    closing_time = Column(String(20), nullable=True)
    weekly_closing = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    logo_url = Column(String, nullable=True)

    # Bank & Payment Settlement Details
    upi_id = Column(String(100), nullable=True)
    bank_name = Column(String(100), nullable=True)
    bank_account_no = Column(String(50), nullable=True)
    bank_ifsc = Column(String(30), nullable=True)
    bank_branch = Column(String(100), nullable=True)
    bank_account_name = Column(String(150), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    shop = relationship("Shop")
    categories = relationship("RestaurantMenuCategory", back_populates="outlet", cascade="all, delete-orphan")
    items = relationship("RestaurantMenuItem", back_populates="outlet", cascade="all, delete-orphan")
    tables = relationship("RestaurantTable", back_populates="outlet", cascade="all, delete-orphan")
    orders = relationship("RestaurantOrder", back_populates="outlet")
    shifts = relationship("RestaurantShift", back_populates="outlet")
