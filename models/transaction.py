import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import UUID

from models.database import Base
from models.enums import TransactionType

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reference_number = Column(String, unique=True, index=True)
    date = Column(DateTime, nullable=False, default=datetime.now)
    description = Column(String, nullable=True)
    
    amount = Column(Float, nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    shop_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Extended Accounting Fields
    entity_name = Column(String, nullable=True) # e.g., 'John Doe' or 'Pharma Distributors'
    entity_type = Column(String, nullable=True) # e.g., 'CUSTOMER' or 'SUPPLIER'
    status = Column(String, default='PAID') # e.g., 'UNPAID', 'PARTIAL', 'PAID'
    due_date = Column(DateTime, nullable=True)

    # Foreign Keys
    category_id = Column(UUID(as_uuid=True), ForeignKey("transaction_categories.id"), nullable=True)
    from_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)
    to_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    category = relationship("TransactionCategory")
    from_account = relationship("Account", foreign_keys=[from_account_id], back_populates="transactions_from")
    to_account = relationship("Account", foreign_keys=[to_account_id], back_populates="transactions_to")
