import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy import UUID

from models.database import Base
from models.enums import AccountType

class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    account_type = Column(Enum(AccountType), nullable=False)
    balance = Column(Float, default=0.0)
    
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    shop_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    transactions_from = relationship("Transaction", back_populates="from_account", foreign_keys="[Transaction.from_account_id]")
    transactions_to = relationship("Transaction", back_populates="to_account", foreign_keys="[Transaction.to_account_id]")
