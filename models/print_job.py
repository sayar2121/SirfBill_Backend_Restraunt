import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base

class PrintJob(Base):
    __tablename__ = "print_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id = Column(UUID(as_uuid=True), ForeignKey("shops.id", ondelete="CASCADE"), nullable=False)
    
    customer_name = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True)

    service_id = Column(UUID(as_uuid=True), ForeignKey("print_services.id", ondelete="SET NULL"), nullable=True)

    file_name = Column(String, nullable=True)
    pages = Column(Integer, default=1)
    copies = Column(Integer, default=1)
    color_type = Column(String, nullable=True)
    status = Column(String, default="PENDING")
    
    total_amount = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    shop = relationship("Shop")
    service = relationship("PrintService")
