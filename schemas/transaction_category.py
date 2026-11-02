from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime
from models.enums import TransactionType

class TransactionCategoryBase(BaseModel):
    name: str
    transaction_type: TransactionType
    tenant_id: Optional[UUID] = None

class TransactionCategoryCreate(TransactionCategoryBase):
    pass

class TransactionCategoryUpdate(BaseModel):
    name: Optional[str] = None
    transaction_type: Optional[TransactionType] = None

class TransactionCategoryResponse(TransactionCategoryBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
