from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from uuid import UUID
from datetime import datetime
from models.enums import TransactionType
from .transaction_category import TransactionCategoryResponse

class TransactionBase(BaseModel):
    reference_number: Optional[str] = None
    date: datetime
    description: Optional[str] = None
    amount: float
    transaction_type: TransactionType
    category_id: Optional[UUID] = None
    from_account_id: Optional[UUID] = None
    to_account_id: Optional[UUID] = None
    tenant_id: Optional[UUID] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    reference_number: Optional[str] = None
    date: Optional[datetime] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    transaction_type: Optional[TransactionType] = None
    category_id: Optional[UUID] = None
    from_account_id: Optional[UUID] = None
    to_account_id: Optional[UUID] = None

class TransactionResponse(TransactionBase):
    id: UUID
    created_at: datetime
    
    # We can include category details for convenience
    category: Optional[TransactionCategoryResponse] = None

    model_config = ConfigDict(from_attributes=True)
