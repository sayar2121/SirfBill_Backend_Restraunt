import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy import UUID

from models.database import Base
from models.enums import TransactionType

class TransactionCategory(Base):
    __tablename__ = "transaction_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
