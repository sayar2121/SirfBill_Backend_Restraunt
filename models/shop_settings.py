from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from models.database import Base

class ShopSettings(Base):
    __tablename__ = "shop_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id = Column(UUID(as_uuid=True), ForeignKey("shops.id"), nullable=True) # If null, applies globally for now
    shop_name = Column(String, nullable=True)
    tagline = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    phone = Column(String, nullable=True)
    landline = Column(String, nullable=True)
    email = Column(String, nullable=True)
    gst_number = Column(String, nullable=True)
    drug_licence = Column(String, nullable=True)
    cin_number = Column(String, nullable=True)
    
    bank_name = Column(String, nullable=True)
    branch_name = Column(String, nullable=True)
    ac_holder_name = Column(String, nullable=True)
    ac_number = Column(String, nullable=True)
    ifsc_code = Column(String, nullable=True)
    upi_id = Column(String, nullable=True)
    
    terms_1 = Column(Text, nullable=True)
    terms_2 = Column(Text, nullable=True)
    terms_3 = Column(Text, nullable=True)
    
    logo_url = Column(String, nullable=True)
    qr_url = Column(String, nullable=True)
